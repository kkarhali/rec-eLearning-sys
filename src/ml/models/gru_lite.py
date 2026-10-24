"""GRU-lite in numpy (D-12, D-35; draft §4.6). Hand-written forward/backward, Adam, truncated BPTT.

Architecture (one layer, d_e = d_h = 64):
    e_ℓ = mean_{i ∈ S_ℓ} E_i                       (catalogue items of the day basket; empty days are not steps)
    z = σ(e W_z + h U_z + b_z),  r = σ(e W_r + h U_r + b_r)
    h̃ = tanh(e W_h + (r ⊙ h) U_h + b_h),  h' = (1 − z) ⊙ h + z ⊙ h̃
    o = h' V + c   (logits over the presentation catalogue)
Row-vector convention: W_* is d_e×d_h, U_* is d_h×d_h, V is d_h×|I|.

Loss: multi-label cross-entropy with normalised target y = 1[j ∈ S^tgt]/|S^tgt|, target = `next`
(S_{ℓ+1}) or `next-new` (S_{ℓ+1} \\ ∪_{j≤ℓ} S_j); empty targets and padded steps are masked; the loss
is normalised by the number of valid target steps of the batch window; + λ Σ‖M‖² (λ = 1e−5) over all
matrices (E, W_*, U_*, V), not the biases.
Optimiser: Adam (0.9, 0.999, 1e−8, bias correction), global-norm clipping at 5, batch 128 sequences
shuffled by the seed each epoch, truncated BPTT with T = 20 (state carried between windows without
gradient), right padding with mask (padded steps keep h). Early stopping: ≤ 30 epochs, NDCG@10 (task A)
on validation after each epoch, patience 3, best epoch kept. Test phase: refit with the chosen number of
epochs and the same seed. Inference: full history from h₀ = 0, score = logits. No temporal features.
Init: Glorot-uniform for E, W_*, V; orthogonal (QR with sign fix) for U_*; zero biases.
"""
from __future__ import annotations

import numpy as np

from .base import Recommender, grid
from .baskets import day_keys

MATS = ("E", "Wz", "Wr", "Wh", "Uz", "Ur", "Uh", "V")
BIASES = ("bz", "br", "bh", "c")
L2 = 1e-5
CLIP = 5.0
BATCH = 128
T_BPTT = 20
MAX_EPOCHS = 30
PATIENCE = 3


def _sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


def init_params(n_items: int, de: int = 64, dh: int = 64, seed: int = 0, dtype=np.float32) -> dict:
    rng = np.random.default_rng(seed)

    def glorot(a, b):
        lim = np.sqrt(6.0 / (a + b))
        return rng.uniform(-lim, lim, (a, b))

    def orth(n):
        q, r = np.linalg.qr(rng.normal(size=(n, n)))
        return q * np.sign(np.diag(r))[None, :]

    p = {"E": glorot(n_items, de), "Wz": glorot(de, dh), "Wr": glorot(de, dh), "Wh": glorot(de, dh),
         "Uz": orth(dh), "Ur": orth(dh), "Uh": orth(dh), "V": glorot(dh, n_items),
         "bz": np.zeros(dh), "br": np.zeros(dh), "bh": np.zeros(dh), "c": np.zeros(n_items)}
    return {k: v.astype(dtype) for k, v in p.items()}


# --------------------------------------------------------------------------------------------
# forward / backward on one window
# --------------------------------------------------------------------------------------------
def window_loss_grad(p: dict, A: np.ndarray, Y: np.ndarray, m: np.ndarray, tm: np.ndarray, h0: np.ndarray,
                     l2: float = L2, n_norm: float | None = None, need_grad: bool = True):
    """Loss and gradients for one window.

    A: (T,B,I) normalised input baskets; Y: (T,B,I) normalised targets; m: (T,B) valid input step;
    tm: (T,B) valid target step; h0: (B,dh) initial state (no gradient flows into it).
    Returns (loss, grads, h_T).
    """
    T, B, _ = A.shape
    n = float(tm.sum()) if n_norm is None else n_norm
    n = max(n, 1.0)
    hs = [h0]
    cache = []
    loss = 0.0
    h = h0
    dO = []
    for t in range(T):
        e = A[t] @ p["E"]
        z = _sigmoid(e @ p["Wz"] + h @ p["Uz"] + p["bz"])
        r = _sigmoid(e @ p["Wr"] + h @ p["Ur"] + p["br"])
        rh = r * h
        hh = np.tanh(e @ p["Wh"] + rh @ p["Uh"] + p["bh"])
        hn = (1.0 - z) * h + z * hh
        mt = m[t][:, None]
        h_new = mt * hn + (1.0 - mt) * h
        o = h_new @ p["V"] + p["c"]
        o = o - o.max(axis=1, keepdims=True)
        lse = np.log(np.exp(o).sum(axis=1, keepdims=True))
        logp = o - lse
        w = tm[t][:, None]
        loss -= float((w * Y[t] * logp).sum()) / n
        if need_grad:
            prob = np.exp(logp)
            dO.append(w * (prob - Y[t]) / n)          # Σ_j y_j = 1 on valid target steps
            cache.append((e, z, r, rh, hh, h, mt))
        h = h_new
        hs.append(h)
    loss += l2 * sum(float((p[k] ** 2).sum()) for k in MATS)
    if not need_grad:
        return loss, None, h
    g = {k: np.zeros_like(v) for k, v in p.items()}
    dh_next = np.zeros_like(h0)
    for t in range(T - 1, -1, -1):
        e, z, r, rh, hh, hprev, mt = cache[t]
        h_t = hs[t + 1]
        g["V"] += h_t.T @ dO[t]
        g["c"] += dO[t].sum(axis=0)
        dh = dO[t] @ p["V"].T + dh_next
        dhn = dh * mt
        dprev = dh * (1.0 - mt) + dhn * (1.0 - z)
        dhh = dhn * z
        dz = dhn * (hh - hprev)
        dah = dhh * (1.0 - hh * hh)
        g["Wh"] += e.T @ dah
        g["Uh"] += rh.T @ dah
        g["bh"] += dah.sum(axis=0)
        drh = dah @ p["Uh"].T
        dr = drh * hprev
        dprev += drh * r
        daz = dz * z * (1.0 - z)
        dar = dr * r * (1.0 - r)
        g["Wz"] += e.T @ daz
        g["Uz"] += hprev.T @ daz
        g["bz"] += daz.sum(axis=0)
        g["Wr"] += e.T @ dar
        g["Ur"] += hprev.T @ dar
        g["br"] += dar.sum(axis=0)
        dprev += daz @ p["Uz"].T + dar @ p["Ur"].T
        de = dah @ p["Wh"].T + daz @ p["Wz"].T + dar @ p["Wr"].T
        g["E"] += A[t].T @ de
        dh_next = dprev
    for k in MATS:
        g[k] += 2.0 * l2 * p[k]
    return loss, g, h


def forward_states(p: dict, A: np.ndarray, m: np.ndarray, h0: np.ndarray | None = None) -> np.ndarray:
    """Final state after running all steps (padded steps keep h)."""
    T, B, _ = A.shape
    h = np.zeros((B, p["Uz"].shape[0]), dtype=p["E"].dtype) if h0 is None else h0
    for t in range(T):
        e = A[t] @ p["E"]
        z = _sigmoid(e @ p["Wz"] + h @ p["Uz"] + p["bz"])
        r = _sigmoid(e @ p["Wr"] + h @ p["Ur"] + p["br"])
        hh = np.tanh(e @ p["Wh"] + (r * h) @ p["Uh"] + p["bh"])
        mt = m[t][:, None]
        h = mt * ((1.0 - z) * h + z * hh) + (1.0 - mt) * h
    return h


class Adam:
    def __init__(self, params: dict, lr: float, b1=0.9, b2=0.999, eps=1e-8, clip=CLIP):
        self.lr, self.b1, self.b2, self.eps, self.clip = lr, b1, b2, eps, clip
        self.m = {k: np.zeros_like(v) for k, v in params.items()}
        self.v = {k: np.zeros_like(v) for k, v in params.items()}
        self.t = 0

    def step(self, params: dict, grads: dict) -> float:
        norm = float(np.sqrt(sum(float((g.astype(np.float64) ** 2).sum()) for g in grads.values())))
        scale = self.clip / norm if (self.clip and norm > self.clip) else 1.0
        self.t += 1
        bc1 = 1 - self.b1 ** self.t
        bc2 = 1 - self.b2 ** self.t
        for k in params:
            g = grads[k] * scale
            self.m[k] = self.b1 * self.m[k] + (1 - self.b1) * g
            self.v[k] = self.b2 * self.v[k] + (1 - self.b2) * g * g
            params[k] -= (self.lr * (self.m[k] / bc1) / (np.sqrt(self.v[k] / bc2) + self.eps)).astype(params[k].dtype)
        return norm


# --------------------------------------------------------------------------------------------
# sequences of day baskets
# --------------------------------------------------------------------------------------------
class Sequences:
    """Per-learner sequences of catalogue day baskets (CSR over baskets)."""

    def __init__(self, user_of_basket, basket_items_ptr, basket_items, n_users, n_items):
        self.n_items = n_items
        self.n_users = n_users
        self.b_ptr = basket_items_ptr          # basket → items
        self.b_items = basket_items
        order = np.argsort(user_of_basket, kind="stable")
        self.u_baskets = order                 # baskets grouped by user, chronological inside
        self.u_ptr = np.searchsorted(user_of_basket[order], np.arange(n_users + 1))

    @classmethod
    def from_train(cls, train):
        bu, bd, inv = day_keys(train)              # baskets sorted by (u, d)
        order = np.argsort(inv, kind="stable")
        items = train.ev_i[order].astype(np.int64)
        ptr = np.searchsorted(inv[order], np.arange(len(bu) + 1))
        return cls(bu, ptr, items, train.n_users, train.n_items)

    @classmethod
    def from_lists(cls, seqs: list[list[list[int]]], n_items: int):
        ub, items, ptr = [], [], [0]
        for u, s in enumerate(seqs):
            for basket in s:
                ub.append(u)
                items.extend(sorted(set(basket)))
                ptr.append(len(items))
        return cls(np.array(ub, dtype=np.int64), np.array(ptr), np.array(items, dtype=np.int64), len(seqs), n_items)

    def length(self, u) -> int:
        return int(self.u_ptr[u + 1] - self.u_ptr[u])

    def baskets(self, u):
        return self.u_baskets[self.u_ptr[u]:self.u_ptr[u + 1]]

    def items_of(self, b):
        return self.b_items[self.b_ptr[b]:self.b_ptr[b + 1]]

    def _flat(self, kind: str):
        """Cache flat (user-ptr, step, item, weight) arrays for 'in_train', 'in_infer', 'next', 'next-new'."""
        if not hasattr(self, "_cache"):
            self._cache = {}
        if kind in self._cache:
            return self._cache[kind]
        S, I, W, ptr = [], [], [], [0]
        for u in range(self.n_users):
            bs = self.baskets(u)
            n = len(bs)
            if kind == "in_infer":
                steps = range(n)
            elif kind == "in_train":
                steps = range(n - 1)
            else:
                steps = range(n - 1)
            seen = set()
            len_before = len(S)
            for s in steps:
                if kind in ("in_infer", "in_train"):
                    it = self.items_of(bs[s])
                else:
                    seen.update(self.items_of(bs[s]).tolist())
                    it = self.items_of(bs[s + 1])
                    if kind == "next-new":
                        it = np.array([i for i in it.tolist() if i not in seen], dtype=np.int64)
                if len(it):
                    S.append(np.full(len(it), s))
                    I.append(it)
                    W.append(np.full(len(it), 1.0 / len(it)))
            ptr.append(ptr[-1] + sum(len(x) for x in S[len_before:]))
        cat = (lambda xs, dt: np.concatenate(xs).astype(dt) if xs else np.zeros(0, dt))
        res = (np.array(ptr, dtype=np.int64), cat(S, np.int64), cat(I, np.int64), cat(W, np.float64))
        self._cache[kind] = res
        return res

    def dense_batch(self, users, target: str = "next", inputs_only: bool = False, dtype=np.float32):
        """Return A (L,B,I), Y (L,B,I), m (L,B), tm (L,B) for the given users.

        Training layout: inputs S_1..S_{n−1}, targets S_2..S_n (inputs_only=False);
        inference layout: inputs S_1..S_n (inputs_only=True).
        """
        users = np.asarray(users)
        B, I = len(users), self.n_items
        lens = np.array([self.length(u) - (0 if inputs_only else 1) for u in users])
        L = max(int(lens.max()) if B else 1, 1)
        A = np.zeros((L, B, I), dtype=dtype)
        m = (np.arange(L)[:, None] < lens[None, :]).astype(dtype)
        ptr, st, it, w = self._flat("in_infer" if inputs_only else "in_train")
        idx = [np.arange(ptr[u], ptr[u + 1]) for u in users]
        kk = np.concatenate([np.full(len(x), k) for k, x in enumerate(idx)]) if B else np.zeros(0, int)
        idx = np.concatenate(idx) if B else np.zeros(0, int)
        A[st[idx], kk, it[idx]] = w[idx]
        if inputs_only:
            return A, None, m, np.zeros_like(m)
        Y = np.zeros((L, B, I), dtype=dtype)
        tm = np.zeros((L, B), dtype=dtype)
        ptr, st, it, w = self._flat(target)
        idx = [np.arange(ptr[u], ptr[u + 1]) for u in users]
        kk = np.concatenate([np.full(len(x), k) for k, x in enumerate(idx)])
        idx = np.concatenate(idx)
        Y[st[idx], kk, it[idx]] = w[idx]
        tm[st[idx], kk] = 1.0
        return A, Y, m, tm


def train_epoch(p: dict, opt: Adam, seqs: Sequences, users: np.ndarray, target: str, rng,
                batch: int = BATCH, T: int = T_BPTT, l2: float = L2) -> float:
    users = users[rng.permutation(len(users))]
    tot, cnt = 0.0, 0
    dh = p["Uz"].shape[0]
    for s in range(0, len(users), batch):
        bu = users[s:s + batch]
        A, Y, m, tm = seqs.dense_batch(bu, target)
        h = np.zeros((len(bu), dh), dtype=p["E"].dtype)
        for w0 in range(0, A.shape[0], T):
            sl = slice(w0, w0 + T)
            if tm[sl].sum() == 0:
                h = forward_states(p, A[sl], m[sl], h)
                continue
            loss, g, h = window_loss_grad(p, A[sl], Y[sl], m[sl], tm[sl], h, l2=l2)
            opt.step(p, g)
            tot += loss
            cnt += 1
    return tot / max(cnt, 1)


def infer_logits(p: dict, seqs: Sequences, chunk: int = 512) -> np.ndarray:
    out = np.zeros((seqs.n_users, seqs.n_items), dtype=np.float64)
    users = np.arange(seqs.n_users)
    for s in range(0, len(users), chunk):
        bu = users[s:s + chunk]
        A, _, m, _ = seqs.dense_batch(bu, inputs_only=True)
        h = forward_states(p, A, m)
        out[bu] = (h @ p["V"] + p["c"]).astype(np.float64)
    return out


class GRULite(Recommender):
    """B-GRU (H3 candidate, hybrid component (4)). Params: lr, target, epochs (test phase), dh."""

    name = "GRU_lite"
    stochastic = True

    def _fit(self, train):
        prm = self.params
        self.seqs = Sequences.from_train(train)
        rng = np.random.default_rng(self.seed)
        self.p = init_params(train.n_items, prm.get("de", 64), prm.get("dh", 64), seed=self.seed)
        opt = Adam(self.p, float(prm.get("lr", 3e-3)))
        users = np.array([u for u in range(train.n_users) if self.seqs.length(u) >= 2])
        self.history = []
        val_fn = prm.get("val_fn")                # callable(scores) -> NDCG@10 on validation (tune phase)
        epochs = int(prm.get("epochs", MAX_EPOCHS))
        best, best_ep, best_p, bad = -np.inf, 0, None, 0
        for ep in range(1, epochs + 1):
            loss = train_epoch(self.p, opt, self.seqs, users, prm.get("target", "next"), rng)
            rec = {"epoch": ep, "train_loss": loss}
            if val_fn is not None:
                v = val_fn(infer_logits(self.p, self.seqs))
                rec["val_ndcg10"] = v
                if v > best:
                    best, best_ep, best_p, bad = v, ep, {k: x.copy() for k, x in self.p.items()}, 0
                else:
                    bad += 1
            self.history.append(rec)
            if val_fn is not None and bad >= PATIENCE:
                break
        if val_fn is not None and best_p is not None:
            self.p = best_p
            self.best_epoch, self.best_val = best_ep, best
        else:
            self.best_epoch, self.best_val = epochs, np.nan

    def _score(self):
        return infer_logits(self.p, self.seqs)

    @classmethod
    def param_space(cls):
        return grid(lr=[1e-3, 3e-3, 1e-2], target=["next", "next-new"])

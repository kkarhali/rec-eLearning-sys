"""POST-HOC model: GRU-lite with the recent peer popularity as an extra input (equal-information H3 control).

Session 2, م-ع-4 item 4 / م-ك-5 item 3. NOT part of the frozen protocol; src/ml/models/gru_lite.py is imported and
never edited. Everything of GRU-lite is kept (architecture, loss, Adam, clipping, batch 128, truncated BPTT T = 20,
early stopping, Glorot/orthogonal init of the GRU-lite parameters with the same seed) and two channels are added:

  input   e_ℓ = mean_{i ∈ S_ℓ} E_i + q_ℓ P             P: |I|×d_e (Glorot, own RNG stream), L2 like the matrices
  output  o_ℓ = h_ℓ V + c + a · log p̂_ℓ                a: scalar, initialised at 0, no L2 (like the biases)

q_ℓ is the B3 recent popularity at the prediction time of step ℓ, as a distribution over the catalogue
(q = c / Σc, with c_i = |{u : ∃ d ∈ (e − w, e], access(u, i, d)}|, exactly models.simple.recent_popularity), and
log p̂_ℓ = log((c + 1)/(Σc + |I|)). The prediction time of training step ℓ is the day before its target basket
(e = d_{ℓ+1} − 1); at inference the last step uses e = t0 (the end of the training period), so the model sees the
peer activity up to the cut exactly like B3 and SKNN do, and nothing after it. w = B3's window selected on
validation for the fold (locked baselines.csv), the same in both phases.

Zero-information mode (Q = 0, log p̂ = 0, P = 0, a = 0) is bit-for-bit GRU-lite (checked by the runner and S6).
"""
from __future__ import annotations

import numpy as np

from src.ml.models import gru_lite as G
from src.ml.models.baskets import day_keys

MATS_EQ = G.MATS + ("P",)


# --------------------------------------------------------------------------------------------
# recent popularity table over days
# --------------------------------------------------------------------------------------------
def popularity_table(train, w: int):
    """counts[e − d_min] = recent_popularity(train with t0 = e, w) for e ∈ [d_min, t0] (float64, |days|×|I|)."""
    I = train.n_items
    u = train.ev_u.astype(np.int64)
    i = train.ev_i.astype(np.int64)
    d = train.ev_d.astype(np.int64)
    d_min = int(d.min()) if len(d) else int(train.t0)
    n_days = int(train.t0) - d_min + 2
    pair = u * I + i
    o = np.lexsort((d, pair))
    pair, d, i = pair[o], d[o], i[o]
    keep = np.r_[True, (pair[1:] != pair[:-1]) | (d[1:] != d[:-1])]        # one event per (u, i, d)
    pair, d, i = pair[keep], d[keep], i[keep]
    nxt = np.r_[np.where(pair[1:] == pair[:-1], d[1:], np.iinfo(np.int64).max), np.iinfo(np.int64).max]
    end = np.minimum(d + w, nxt)                                            # active on [d, end − 1], disjoint
    diff = np.zeros((n_days + w + 1, I))
    np.add.at(diff, (d - d_min, i), 1.0)
    np.add.at(diff, (np.minimum(end - d_min, n_days + w), i), -1.0)
    counts = np.cumsum(diff, axis=0)[: n_days - 1]
    return counts, d_min


def features(counts: np.ndarray):
    tot = counts.sum(axis=1, keepdims=True)
    q = np.where(tot > 0, counts / np.maximum(tot, 1.0), 0.0)
    lp = np.log((counts + 1.0) / (tot + counts.shape[1]))
    return q, lp


# --------------------------------------------------------------------------------------------
# sequences with the prediction day of every step
# --------------------------------------------------------------------------------------------
class SequencesEq(G.Sequences):
    @classmethod
    def from_train_eq(cls, train, q_table, lp_table, d_min):
        bu, bd, inv = day_keys(train)
        order = np.argsort(inv, kind="stable")
        items = train.ev_i[order].astype(np.int64)
        ptr = np.searchsorted(inv[order], np.arange(len(bu) + 1))
        s = cls(bu, ptr, items, train.n_users, train.n_items)
        s.b_day = bd
        s.t0, s.q_table, s.lp_table, s.d_min = int(train.t0), q_table, lp_table, d_min
        return s

    def pred_days(self, users, inputs_only: bool):
        """(L, B) prediction day of every input step; −1 on padded steps."""
        rows = []
        for u in users:
            days = self.b_day[self.baskets(u)]
            e = days[1:] - 1                                  # training step s predicts basket s + 1
            if inputs_only:
                e = np.r_[e, self.t0]                         # last inference step: the cut
            rows.append(e)
        L = max(max((len(r) for r in rows), default=1), 1)
        out = np.full((L, len(users)), -1, dtype=np.int64)
        for k, r in enumerate(rows):
            out[:len(r), k] = r
        return out

    def peer_inputs(self, users, inputs_only: bool, L: int, dtype=np.float32):
        E = self.pred_days(users, inputs_only)[:L]
        if E.shape[0] < L:
            E = np.vstack([E, np.full((L - E.shape[0], E.shape[1]), -1, dtype=np.int64)])
        valid = E >= 0
        idx = np.clip(E - self.d_min, 0, self.q_table.shape[0] - 1)
        Q = self.q_table.astype(dtype, copy=False)[idx]
        LP = self.lp_table.astype(dtype, copy=False)[idx]
        Q[~valid] = 0.0
        LP[~valid] = 0.0
        return Q, LP


# --------------------------------------------------------------------------------------------
# forward / backward (G.window_loss_grad plus the two channels; identical when they are zero)
# --------------------------------------------------------------------------------------------
def window_loss_grad_eq(p, A, Q, LP, Y, m, tm, h0, l2=G.L2, n_norm=None, need_grad=True):
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
        e = e + Q[t] @ p["P"]
        z = G._sigmoid(e @ p["Wz"] + h @ p["Uz"] + p["bz"])
        r = G._sigmoid(e @ p["Wr"] + h @ p["Ur"] + p["br"])
        rh = r * h
        hh = np.tanh(e @ p["Wh"] + rh @ p["Uh"] + p["bh"])
        hn = (1.0 - z) * h + z * hh
        mt = m[t][:, None]
        h_new = mt * hn + (1.0 - mt) * h
        o = h_new @ p["V"] + p["c"]
        o = o + p["a"] * LP[t]
        o = o - o.max(axis=1, keepdims=True)
        lse = np.log(np.exp(o).sum(axis=1, keepdims=True))
        logp = o - lse
        w = tm[t][:, None]
        loss -= float((w * Y[t] * logp).sum()) / n
        if need_grad:
            prob = np.exp(logp)
            dO.append(w * (prob - Y[t]) / n)
            cache.append((e, z, r, rh, hh, h, mt))
        h = h_new
        hs.append(h)
    loss += l2 * sum(float((p[k] ** 2).sum()) for k in G.MATS)
    loss += l2 * float((p["P"] ** 2).sum())
    if not need_grad:
        return loss, None, h
    g = {k: np.zeros_like(v) for k, v in p.items()}
    dh_next = np.zeros_like(h0)
    for t in range(T - 1, -1, -1):
        e, z, r, rh, hh, hprev, mt = cache[t]
        h_t = hs[t + 1]
        g["V"] += h_t.T @ dO[t]
        g["c"] += dO[t].sum(axis=0)
        g["a"] += np.asarray((dO[t] * LP[t]).sum(), dtype=g["a"].dtype).reshape(g["a"].shape)
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
        g["P"] += Q[t].T @ de
        dh_next = dprev
    for k in MATS_EQ:
        g[k] += 2.0 * l2 * p[k]
    return loss, g, h


def forward_states_eq(p, A, Q, m, h0=None):
    T, B, _ = A.shape
    h = np.zeros((B, p["Uz"].shape[0]), dtype=p["E"].dtype) if h0 is None else h0
    for t in range(T):
        e = A[t] @ p["E"]
        e = e + Q[t] @ p["P"]
        z = G._sigmoid(e @ p["Wz"] + h @ p["Uz"] + p["bz"])
        r = G._sigmoid(e @ p["Wr"] + h @ p["Ur"] + p["br"])
        hh = np.tanh(e @ p["Wh"] + (r * h) @ p["Uh"] + p["bh"])
        mt = m[t][:, None]
        h = mt * ((1.0 - z) * h + z * hh) + (1.0 - mt) * h
    return h


def init_params_eq(n_items, de=64, dh=64, seed=0, dtype=np.float32, zero_info=False):
    p = G.init_params(n_items, de, dh, seed=seed, dtype=dtype)       # same draws as GRU-lite
    if zero_info:
        p["P"] = np.zeros((n_items, de), dtype=dtype)
    else:
        rng = np.random.default_rng([seed, 7919])                    # separate stream: GRU-lite draws unchanged
        lim = np.sqrt(6.0 / (n_items + de))
        p["P"] = rng.uniform(-lim, lim, (n_items, de)).astype(dtype)
    p["a"] = np.zeros(1, dtype=dtype)
    return p


def batch_eq(seqs: SequencesEq, users, target="next", inputs_only=False, zero_info=False, dtype=np.float32):
    A, Y, m, tm = seqs.dense_batch(users, target, inputs_only=inputs_only, dtype=dtype)
    if zero_info:
        Q = np.zeros_like(A)
        LP = np.zeros_like(A)
    else:
        Q, LP = seqs.peer_inputs(users, inputs_only, A.shape[0], dtype=dtype)
    return A, Q, LP, Y, m, tm


def train_epoch_eq(p, opt, seqs, users, target, rng, zero_info=False, batch=G.BATCH, T=G.T_BPTT, l2=G.L2):
    users = users[rng.permutation(len(users))]
    tot, cnt = 0.0, 0
    dh = p["Uz"].shape[0]
    for s in range(0, len(users), batch):
        bu = users[s:s + batch]
        A, Q, LP, Y, m, tm = batch_eq(seqs, bu, target, zero_info=zero_info)
        h = np.zeros((len(bu), dh), dtype=p["E"].dtype)
        for w0 in range(0, A.shape[0], T):
            sl = slice(w0, w0 + T)
            if tm[sl].sum() == 0:
                h = forward_states_eq(p, A[sl], Q[sl], m[sl], h)
                continue
            loss, g, h = window_loss_grad_eq(p, A[sl], Q[sl], LP[sl], Y[sl], m[sl], tm[sl], h, l2=l2)
            opt.step(p, g)
            tot += loss
            cnt += 1
    return tot / max(cnt, 1)


def infer_logits_eq(p, seqs, zero_info=False, chunk=512):
    out = np.zeros((seqs.n_users, seqs.n_items), dtype=np.float64)
    users = np.arange(seqs.n_users)
    for s in range(0, len(users), chunk):
        bu = users[s:s + chunk]
        A, Q, LP, _, m, _ = batch_eq(seqs, bu, inputs_only=True, zero_info=zero_info)
        h = forward_states_eq(p, A, Q, m)
        # last valid step of every user carries the cut-day popularity (padded steps keep h)
        lens = m.sum(axis=0).astype(int)
        last = np.where(lens > 0, lens - 1, 0)
        lp_last = LP[last, np.arange(len(bu))]
        out[bu] = (h @ p["V"] + p["c"] + p["a"] * lp_last).astype(np.float64)
    return out


class GRUEq(G.GRULite):
    """GRU-lite + recent peer popularity (input P and output gain a). Params as GRU-lite plus
    ``w`` (B3 window), ``zero_info`` (bool, for the equivalence check)."""

    name = "GRU_eqinfo"
    stochastic = True

    def _fit(self, train):
        prm = self.params
        zero = bool(prm.get("zero_info", False))
        counts, d_min = popularity_table(train, int(prm.get("w", 14)))
        q, lp = features(counts)
        q, lp = q.astype(np.float32), lp.astype(np.float32)
        self.counts_t0 = counts[int(train.t0) - d_min]
        self.seqs = SequencesEq.from_train_eq(train, q, lp, d_min)
        rng = np.random.default_rng(self.seed)
        self.p = init_params_eq(train.n_items, prm.get("de", 64), prm.get("dh", 64), seed=self.seed, zero_info=zero)
        opt = G.Adam(self.p, float(prm.get("lr", 3e-3)))
        users = np.array([u for u in range(train.n_users) if self.seqs.length(u) >= 2])
        self.history = []
        val_fn = prm.get("val_fn")
        epochs = int(prm.get("epochs", G.MAX_EPOCHS))
        best, best_ep, best_p, bad = -np.inf, 0, None, 0
        for ep in range(1, epochs + 1):
            loss = train_epoch_eq(self.p, opt, self.seqs, users, prm.get("target", "next"), rng, zero_info=zero)
            rec = {"epoch": ep, "train_loss": loss, "a": float(self.p["a"][0])}
            if val_fn is not None:
                v = val_fn(infer_logits_eq(self.p, self.seqs, zero_info=zero))
                rec["val_ndcg10"] = v
                if v > best:
                    best, best_ep, best_p, bad = v, ep, {k: x.copy() for k, x in self.p.items()}, 0
                else:
                    bad += 1
            self.history.append(rec)
            if val_fn is not None and bad >= G.PATIENCE:
                break
        if val_fn is not None and best_p is not None:
            self.p = best_p
            self.best_epoch, self.best_val = best_ep, best
        else:
            self.best_epoch, self.best_val = epochs, np.nan

    def _score(self):
        return infer_logits_eq(self.p, self.seqs, zero_info=bool(self.params.get("zero_info", False)))

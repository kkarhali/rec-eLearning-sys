#!/usr/bin/env python3
"""POST-HOC (session 2, م-ع-4 item 4; م-ك-5 item 3): an equal-information H3 control, GRU-lite + recent peer popularity.

Model: scripts/posthoc/gru_eqinfo.py (GRU-lite unchanged plus the B3 recent popularity of the fold's window w as an
input at every step and as a gain on the output log-popularity; see its docstring). Budget = the LOCKED GRU-lite
budget (run_gru.run_job): the 6 settings η ∈ {1e-3, 3e-3, 1e-2} × target ∈ {next, next-new} with seed 0 and early
stopping on validation NDCG@10 (task A; ≤ 30 epochs, patience 3); first maximum wins; refit on ≤ t with the selected
epochs for seeds 0–4; task-A rows in the baselines.csv format (harness.eval_rows). w = B3's validation-selected
window of the fold (locked baselines.csv), not tuned here.

Gates before any result (as gru_sanity, adapted): S1 gradient check of every parameter including P and a
(float64, central differences, max rel. err < 1e-4); S2 overfit on 32 sequences with random peer inputs; S3 synthetic
Markov chain with an uninformative (uniform) peer input; S6 masking / truncation and the zero-information
equivalence (loss, gradients and states bit-for-bit equal to GRU-lite); S4 one real development fold (FFF_2013J,
t = 126, η = 3e-3, next-new: no NaN/Inf, last training loss ≤ 0.9 × first). S5 (seed SD) is reported.
Reproduction (stop condition): the popularity table at t0 equals models.simple.recent_popularity exactly in every
fold and phase; the model in zero-information mode, with the locked configuration and epochs, reproduces the locked
GRU-lite test NDCG@10 (seed 0) of one fold per origin in each year (≤ 1e-6).
Runtime guard: one fold is timed first; the total is extrapolated from the locked GRU-lite CPU seconds and the tool
stops if it exceeds --max-minutes (default 90).

    python3 scripts/posthoc/a11_h3_equal_info.py [--workers 4] [--max-minutes 90]
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time

from _s2 import C, check_locked_files, log_read, np, pd
import gru_eqinfo as Q
from src.ml import components as CP, data, metrics, stats
from src.ml.harness import SEEDS, config_key, eval_rows
from src.ml.models import gru_lite as G
from src.ml.models.simple import recent_popularity
from src.ml.splits import CUTS, make_fold

LABEL = "GRU_eqinfo (post-hoc, + recent peer popularity)"
_PRES: dict = {}
_W: dict = {}


# ------------------------------------------------------------------------------------------------
# sanity gates
# ------------------------------------------------------------------------------------------------
def s1_gradient_check(seed=0):
    rng = np.random.default_rng(seed)
    I, de, dh = 9, 6, 5
    p = Q.init_params_eq(I, de, dh, seed=seed + 1, dtype=np.float64)
    for b in G.BIASES:
        p[b] = rng.normal(0, 0.1, p[b].shape)
    p["a"] = np.array([0.7])
    seqs = G.Sequences.from_lists([[[0], [1, 2]], [[1], [3], [4, 5], [0]],
                                   [[2], [6], [1, 3], [0, 7], [5], [4, 8]]], I)
    A, Y, m, tm = seqs.dense_batch([0, 1, 2], "next", dtype=np.float64)
    Qm = rng.dirichlet(np.ones(I), size=A.shape[:2]) * m[..., None]
    LP = np.log(rng.dirichlet(np.ones(I), size=A.shape[:2])) * m[..., None]
    h0 = rng.normal(0, 0.5, (3, dh))
    _, g, _ = Q.window_loss_grad_eq(p, A, Qm, LP, Y, m, tm, h0, l2=G.L2)
    worst, per, eps = 0.0, {}, 1e-5
    for k in p:
        flat = p[k].ravel()
        idx = rng.choice(flat.size, min(flat.size, 20), replace=False)
        w = 0.0
        for j in idx:
            old = flat[j]
            flat[j] = old + eps
            lp = Q.window_loss_grad_eq(p, A, Qm, LP, Y, m, tm, h0, l2=G.L2, need_grad=False)[0]
            flat[j] = old - eps
            lm = Q.window_loss_grad_eq(p, A, Qm, LP, Y, m, tm, h0, l2=G.L2, need_grad=False)[0]
            flat[j] = old
            gn, ga = (lp - lm) / (2 * eps), g[k].ravel()[j]
            w = max(w, abs(ga - gn) / max(abs(ga), abs(gn), 1e-6))
        per[k] = w
        worst = max(worst, w)
    return {"max_rel_err": worst, "per_param": per, "pass": worst < 1e-4}


def s2_overfit(seed=0):
    rng = np.random.default_rng(seed)
    I, n_seq, n_bask = 50, 32, 6
    seqs_l = [[list(rng.choice(I, size=rng.integers(1, 4), replace=False)) for _ in range(n_bask)] for _ in range(n_seq)]
    used = set()
    for sq in seqs_l:
        while tuple(sorted(sq[0])) in used:
            sq[0] = list(rng.choice(I, size=rng.integers(1, 4), replace=False))
        used.add(tuple(sorted(sq[0])))
    seqs = G.Sequences.from_lists(seqs_l, I)
    A, Y, m, tm = seqs.dense_batch(np.arange(n_seq), "next", dtype=np.float32)
    Qm = (rng.dirichlet(np.ones(I), size=A.shape[:2]) * m[..., None]).astype(np.float32)
    LP = (np.log(rng.dirichlet(np.ones(I), size=A.shape[:2])) * m[..., None]).astype(np.float32)
    p = Q.init_params_eq(I, seed=seed)
    opt = G.Adam(p, 1e-2)
    h0 = np.zeros((n_seq, 64), dtype=np.float32)
    losses = []
    for _ in range(300):
        loss, g, _ = Q.window_loss_grad_eq(p, A, Qm, LP, Y, m, tm, h0, l2=0.0)
        opt.step(p, g)
        losses.append(loss)
    h, gap, hits, n = h0, 0.0, 0, 0
    for t in range(A.shape[0]):
        h_next = Q.forward_states_eq(p, A[t:t + 1], Qm[t:t + 1], m[t:t + 1], h)
        o = h_next @ p["V"] + p["c"] + p["a"] * LP[t]
        o = o - o.max(axis=1, keepdims=True)
        logp = o - np.log(np.exp(o).sum(axis=1, keepdims=True))
        for b in range(n_seq):
            if tm[t, b]:
                y = Y[t, b]
                gap += -float((y * logp[b]).sum()) + float((y[y > 0] * np.log(y[y > 0])).sum())
                hits += bool((y[np.argsort(-o[b])[:10]] > 0).any())
                n += 1
        h = h_next
    return {"mean_L_minus_H": gap / n, "train_HR@10": hits / n, "loss_first": losses[0], "loss_last": losses[-1],
            "pass": gap / n <= 0.05 and hits / n >= 0.99}


def _synthetic_eq(lists, n_items, n_days):
    """SequencesEq over synthetic lists: day = position, uniform (uninformative) peer popularity on every day."""
    s = Q.SequencesEq.from_lists(lists, n_items)
    ub = np.repeat(np.arange(s.n_users), np.diff(s.u_ptr))
    s.b_day = np.arange(len(ub)) - s.u_ptr[ub]
    s.t0, s.d_min = n_days, 0
    s.q_table = np.full((n_days + 1, n_items), 1.0 / n_items, dtype=np.float32)
    s.lp_table = np.full((n_days + 1, n_items), np.log(1.0 / n_items), dtype=np.float32)
    return s


def s3_markov(seed=0, n_states=50, n_succ=5, n_train=5000, n_test=500, length=30, epochs=8):
    from src.ml.models.markov import transition_probabilities
    rng = np.random.default_rng(seed)
    P = np.zeros((n_states, n_states))
    for a in range(n_states):
        succ = rng.choice(n_states, n_succ, replace=False)
        P[a, succ] = rng.dirichlet(np.ones(n_succ))

    def gen(n):
        out = []
        for _ in range(n):
            s = [int(rng.integers(n_states))]
            for _ in range(length - 1):
                s.append(int(rng.choice(n_states, p=P[s[-1]])))
            out.append(s)
        return out

    tr_l, te_l = gen(n_train), gen(n_test)
    seqs = _synthetic_eq([[[x] for x in s] for s in tr_l], n_states, length)
    p = Q.init_params_eq(n_states, seed=seed)
    opt = G.Adam(p, 3e-3)
    r2 = np.random.default_rng(seed)
    curve = [Q.train_epoch_eq(p, opt, seqs, np.arange(n_train), "next", r2) for _ in range(epochs)]
    N = np.zeros((n_states, n_states))
    for s in tr_l:
        np.add.at(N, (s[:-1], s[1:]), 1.0)
    Pm = transition_probabilities(N, 0.01)
    te = _synthetic_eq([[[x] for x in s] for s in te_l], n_states, length)
    A, Qm, LP, Y, m, tm = Q.batch_eq(te, np.arange(n_test), "next")
    h = np.zeros((n_test, 64), dtype=np.float32)
    disc = 1 / np.log2(np.arange(2, 12))
    tv, nd_g, nd_m = [], [], []
    for t in range(A.shape[0]):
        h = Q.forward_states_eq(p, A[t:t + 1], Qm[t:t + 1], m[t:t + 1], h)
        o = (h @ p["V"] + p["c"] + p["a"] * LP[t]).astype(np.float64)
        o -= o.max(axis=1, keepdims=True)
        pr = np.exp(o)
        pr /= pr.sum(axis=1, keepdims=True)
        cur = np.array([s[t] for s in te_l])
        nxt = np.array([s[t + 1] for s in te_l])
        tv.append(0.5 * np.abs(pr - P[cur]).sum(axis=1))
        for scores, acc in ((o, nd_g), (Pm[cur], nd_m)):
            top = np.argsort(-scores, axis=1, kind="stable")[:, :10]
            acc.append(((top == nxt[:, None]) * disc).sum(axis=1))
    tv_m, ng, nm = float(np.mean(np.concatenate(tv))), float(np.mean(np.concatenate(nd_g))), float(np.mean(np.concatenate(nd_m)))
    return {"mean_TV": tv_m, "NDCG@10_gru_eqinfo": ng, "NDCG@10_markov": nm, "train_loss_curve": curve,
            "pass": tv_m <= 0.10 and ng >= nm - 0.01}


def s6_masking_equivalence(seed=0):
    rng = np.random.default_rng(seed)
    I = 12
    lists = [[[0], [1, 2], [3]], [[4], [5], [6, 7], [8], [9]], [[10], [11, 0]]]
    seqs = G.Sequences.from_lists(lists, I)
    A, Y, m, tm = seqs.dense_batch([0, 1, 2], "next", dtype=np.float64)
    out = {}
    # (1) zero-information mode = GRU-lite, bit for bit (loss, every gradient, final state)
    p = Q.init_params_eq(I, 8, 8, seed=3, dtype=np.float64, zero_info=True)
    pb = {k: v for k, v in p.items() if k not in ("P", "a")}
    h0 = rng.normal(0, 0.3, (3, 8))
    Z = np.zeros_like(A)
    l1, g1, h1 = Q.window_loss_grad_eq(p, A, Z, Z, Y, m, tm, h0)
    l2, g2, h2 = G.window_loss_grad(pb, A, Y, m, tm, h0)
    out["zero_info_bitwise_equal"] = bool(l1 == l2 and np.array_equal(h1, h2) and all(np.array_equal(g1[k], g2[k]) for k in g2)
                                          and not g1["P"].any() and not g1["a"].any())
    # (2) padded steps keep h: each sequence alone = the same sequence inside the padded batch
    p = Q.init_params_eq(I, 8, 8, seed=4, dtype=np.float64)
    p["a"] = np.array([0.5])
    Qm = rng.dirichlet(np.ones(I), size=A.shape[:2]) * m[..., None]
    LP = np.log(rng.dirichlet(np.ones(I), size=A.shape[:2])) * m[..., None]
    hb = Q.forward_states_eq(p, A, Qm, m)
    ok = True
    for b in range(3):
        L = int(m[:, b].sum())
        hs = Q.forward_states_eq(p, A[:L, b:b + 1], Qm[:L, b:b + 1], m[:L, b:b + 1])
        ok &= bool(np.allclose(hs[0], hb[b], rtol=0, atol=1e-12))
    out["padded_steps_keep_h"] = ok
    # (3) windows with the state carried (as train_epoch, T = 2) = one pass over all steps (forward and loss)
    n = float(tm.sum())
    lf, _, hf = Q.window_loss_grad_eq(p, A, Qm, LP, Y, m, tm, np.zeros((3, 8)), l2=0.0, need_grad=False)
    la, _, ha = Q.window_loss_grad_eq(p, A[:2], Qm[:2], LP[:2], Y[:2], m[:2], tm[:2], np.zeros((3, 8)), l2=0.0,
                                      n_norm=n, need_grad=False)
    lb, _, hb2 = Q.window_loss_grad_eq(p, A[2:], Qm[2:], LP[2:], Y[2:], m[2:], tm[2:], ha, l2=0.0, n_norm=n,
                                       need_grad=False)
    hs2 = Q.forward_states_eq(p, A[2:], Qm[2:], m[2:], Q.forward_states_eq(p, A[:2], Qm[:2], m[:2]))
    out["windows_with_carried_state_equal_full"] = bool(abs(lf - (la + lb)) < 1e-12 and np.allclose(hf, hb2, atol=1e-12)
                                                        and np.allclose(hs2, hb, atol=1e-12))
    out["truncation_T_ge_length_equal"] = out["windows_with_carried_state_equal_full"]
    # (4) GRU-lite's own unit tests (masking, candidates exclude seen items)
    import os
    import unittest
    suite = unittest.defaultTestLoader.loadTestsFromName("src.ml.tests.test_gru")
    res = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, "w")).run(suite)
    out["gru_unit_tests"] = f"{res.testsRun} run, {len(res.failures) + len(res.errors)} failed"
    out["pass"] = bool(out["zero_info_bitwise_equal"] and ok and out["truncation_T_ge_length_equal"] and res.wasSuccessful())
    return out


def _val_fn(tr, tg):
    tA = tg.task("A")
    return lambda S: metrics.summarize(metrics.evaluate(S, tA[1], tA[0], tA[2], tA[3], tr.tiebreak, ks=(10,)))["NDCG@10"]  # noqa: E731


def s4_real_curve(p, w):
    tr, tg = make_fold(p, 126, "tune", "E5")
    t = time.time()
    m = Q.GRUEq(seed=0, lr=3e-3, target="next-new", w=w, val_fn=_val_fn(tr, tg)).fit(tr)
    tl = [h["train_loss"] for h in m.history]
    vl = [h["val_ndcg10"] for h in m.history]
    ok = bool(np.all(np.isfinite(tl)) and np.all(np.isfinite(vl)) and tl[-1] <= 0.9 * tl[0])
    return {"presentation": p.name, "cut": 126, "w": w, "train_loss": tl, "val_ndcg10": vl,
            "a": [h["a"] for h in m.history], "best_epoch": m.best_epoch, "seconds": time.time() - t, "pass": ok}


# ------------------------------------------------------------------------------------------------
# jobs
# ------------------------------------------------------------------------------------------------
def repro_job(args):
    """Zero-information mode with the locked configuration and epochs, seed 0, test phase: task-A NDCG@10."""
    name, cut, cfg_key = args
    cfg = CP.parse_config(cfg_key)
    tr2, tg2 = make_fold(_PRES[name], cut, "test", "E5")
    S = Q.GRUEq(seed=0, zero_info=True, w=_W[(name, cut)], **cfg).fit(tr2).score()
    r = [x for x in eval_rows(name, cut, "zero-info", "A", 0, cfg_key, np.nan, S, tg2.task("A"), tr2) if x["slice"] == "all"][0]
    return {"presentation": name, "cut": cut, "NDCG@10": r["NDCG@10"]}


def pop_check(train, w):
    counts, d_min = Q.popularity_table(train, w)
    return float(np.abs(counts[int(train.t0) - d_min] - recent_popularity(train, w)).max())


def job(args):
    name, cut = args
    t_job = time.time()
    p, w = _PRES[name], _W[(name, cut)]
    tr, tg = make_fold(p, cut, "tune", "E5")
    tr2, tg2 = make_fold(p, cut, "test", "E5")
    popdiff = max(pop_check(tr, w), pop_check(tr2, w))
    vf = _val_fn(tr, tg)
    tuning, best = [], None
    for cfg in G.GRULite.param_space():
        t = time.time()
        m = Q.GRUEq(seed=SEEDS[0], **cfg, w=w, val_fn=vf).fit(tr)
        tuning.append({"presentation": name, "cut": cut, "config": config_key(cfg), "w": w, "best_epoch": m.best_epoch,
                       "val_NDCG@10": m.best_val, "epochs_run": len(m.history), "seconds": time.time() - t,
                       "train_loss": json.dumps([round(h["train_loss"], 4) for h in m.history]),
                       "val_curve": json.dumps([round(h["val_ndcg10"], 4) for h in m.history]),
                       "a_curve": json.dumps([round(h["a"], 4) for h in m.history])})
        if best is None or m.best_val > best[0]:
            best = (m.best_val, cfg, m.best_epoch, float(m.p["a"][0]))
    val, cfg, ep, a_best = best
    key = config_key({**cfg, "epochs": ep}) + f";w={w}"
    rows = []
    for s in SEEDS:
        t = time.time()
        mm = Q.GRUEq(seed=s, **cfg, epochs=ep, w=w).fit(tr2)
        S = mm.score()
        rows += eval_rows(name, cut, LABEL, "A", s, key, val, S, tg2.task("A"), tr2, time.time() - t,
                          extra={"a_final": float(mm.p["a"][0])})
    print(f"[a11] {name} t={cut} best={key} val={val:.3f} ({time.time() - t_job:.0f}s)", flush=True)
    return rows, tuning, {"presentation": name, "cut": cut, "pop_table_max_abs_diff": popdiff,
                          "seconds": time.time() - t_job}


def load_year(year):
    names = data.DEV_PRESENTATIONS if year == "2013" else data.CONF_PRESENTATIONS
    src = C.DEV if year == "2013" else C.CONF
    _PRES.clear()
    if year == "2013":
        _PRES.update(data.load_dev_presentations(names))
    else:
        log_read("a11_h3_equal_info.py", "daily VLE events, vle, assessments, courses, registrations and studentInfo "
                 "without sensitive columns (data.load_presentation) for GRU_eqinfo fits", names)
        ev = data.load_daily_events("conf", allow_confirmatory=True)
        _PRES.update({n: data.load_presentation(n, events=ev, allow_confirmatory=True) for n in names})
    base = pd.read_csv(src / "baselines.csv")
    b3 = base[(base["model"] == "B3_RecentPop") & (base["task"] == "A") & (base["slice"] == "all")]
    _W.clear()
    _W.update({(r.presentation, int(r.cut)): int(CP.parse_config(r.config)["w"]) for r in b3.itertuples()})
    return names, src, base


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max-minutes", type=float, default=90.0)
    a = ap.parse_args(argv)
    t0 = time.time()
    checks = check_locked_files(["gru.csv", "baselines.csv"])
    # ---------- sanity gates ----------
    san = {}
    for k, fn in (("S1", s1_gradient_check), ("S2", s2_overfit), ("S3", s3_markov), ("S6", s6_masking_equivalence)):
        t = time.time()
        san[k] = fn()
        san[k]["seconds"] = time.time() - t
        print(f"[a11] sanity {k}: pass={san[k]['pass']} ({san[k]['seconds']:.0f}s)", flush=True)
    names13, _, _ = load_year("2013")
    san["S4"] = s4_real_curve(_PRES["FFF_2013J"], _W[("FFF_2013J", 126)])
    print(f"[a11] sanity S4: pass={san['S4']['pass']} ({san['S4']['seconds']:.0f}s)", flush=True)
    gates = all(san[k]["pass"] for k in ("S1", "S2", "S3", "S4", "S6"))
    san["gates_passed"] = gates
    (C.OUT / "a11_gru_eqinfo_sanity.json").write_text(json.dumps(san, indent=1, default=float))
    if not gates:
        raise SystemExit("[a11] sanity gates not passed: no result is produced")
    rows, tun, meta, per_all, st = [], [], [], [], []
    for year in ("2013", "2014"):
        names, src, base = load_year(year) if year == "2014" else (names13, C.DEV, pd.read_csv(C.DEV / "baselines.csv"))
        gru = pd.read_csv(src / "gru.csv")
        g0 = gru[(gru["model"] == "GRU_lite") & (gru["task"] == "A") & (gru["slice"] == "all") & (gru["seed"] == 0)]
        g0 = g0.set_index(["presentation", "cut"]).sort_index()
        # ---------- reproduction (stop on failure) ----------
        rep_folds = [(names[i % len(names)], c) for i, c in enumerate(sorted(CUTS))]
        with mp.get_context("fork").Pool(min(a.workers, 3)) as pool:
            rep = pd.DataFrame(pool.map(repro_job, [(n, c, g0.loc[(n, c), "config"]) for n, c in rep_folds]))
        rep = rep.set_index(["presentation", "cut"]).sort_index()
        checks.append({"year": year, **C.check(f"{year} GRU_eqinfo zero-information mode, locked config/epochs, seed 0, test "
                                               f"NDCG@10 vs {src.name}/gru.csv ({len(rep)} folds, one per origin)",
                                               rep["NDCG@10"], g0.loc[rep.index, "NDCG@10"])})
        if not checks[-1]["pass"]:
            raise SystemExit(f"[a11] reproduction failed for {year}; no new number written")
        folds = [(n, c) for c in sorted(CUTS, reverse=True) for n in names]
        if year == "2013":
            # ---------- runtime guard: one fold timed, extrapolated with the locked GRU-lite CPU seconds ----------
            lk_t = pd.read_csv(C.DEV / "gru_tuning.csv").groupby(["presentation", "cut"])["seconds"].sum()
            probe = lk_t.sort_values().index[len(lk_t) // 2]
            r0 = job(probe)
            lk_fold = lk_t[probe] + gru[(gru["model"] == "GRU_lite") & (gru["task"] == "A") & (gru["slice"] == "all")
                                        ].set_index(["presentation", "cut"]).loc[probe, "fit_score_seconds"].sum()
            ratio = r0[2]["seconds"] / lk_fold
            locked_cpu = 0.0
            for s_ in (C.DEV, C.CONF):
                gg = pd.read_csv(s_ / "gru.csv")
                locked_cpu += pd.read_csv(s_ / "gru_tuning.csv")["seconds"].sum() + \
                    gg[(gg["model"] == "GRU_lite") & (gg["task"] == "A") & (gg["slice"] == "all")]["fit_score_seconds"].sum()
            est = (time.time() - t0) / 60 + ratio * locked_cpu / a.workers / 60
            print(f"[a11] probe fold {probe}: {r0[2]['seconds']:.0f}s vs locked GRU-lite {lk_fold:.0f}s (×{ratio:.2f}); "
                  f"estimated total {est:.0f} min", flush=True)
            meta.append({"probe_fold": f"{probe[0]} t={probe[1]}", "probe_seconds": r0[2]["seconds"], "locked_seconds": lk_fold,
                         "ratio": ratio, "estimated_total_minutes": est})
            if est > a.max_minutes:
                raise SystemExit(f"[a11] estimated {est:.0f} min > {a.max_minutes} min: stopped before the main run")
            folds = [f for f in folds if f != probe]
        with mp.get_context("fork").Pool(a.workers) as pool:
            res = pool.map(job, folds, chunksize=1)
        if year == "2013":
            res = [r0] + res
        r = pd.DataFrame([x for rr, _, _ in res for x in rr])
        r.insert(0, "year", year)
        tt = pd.DataFrame([x for _, tt_, _ in res for x in tt_])
        tt.insert(0, "year", year)
        mm = pd.DataFrame([x for _, _, mm_ in res for x in [mm_]])
        okp = float(mm["pop_table_max_abs_diff"].max()) == 0.0
        checks.append({"year": year, "check": f"{year} popularity table at t0 = models.simple.recent_popularity (every fold, "
                       "both phases)", "n": len(mm), "max_abs_diff": float(mm["pop_table_max_abs_diff"].max()),
                       "tolerance": 0.0, "pass": okp})
        if not okp:
            raise SystemExit(f"[a11] popularity table differs from B3 for {year}; no new number written")
        rows.append(r), tun.append(tt)
        # ---------- pairs ----------
        ge = C.pres_means(r, LABEL)
        per = pd.DataFrame({"GRU_eqinfo": ge, "GRU_lite_locked": C.pres_means(gru, "GRU_lite"),
                            "B5_SKNN_locked": C.pres_means(base, "B5_SKNN"), "B3_RecentPop_locked": C.pres_means(base, "B3_RecentPop")})
        a42 = pd.read_csv(C.OUT / "a4_2_sknn_all_per_presentation.csv")
        per["B5_SKNN_Mall"] = a42[a42["year"] == int(year)].set_index("presentation")["B5_SKNN_Mall"]
        per.index.name = "presentation"
        pairs = [("GRU_eqinfo − B5_SKNN (locked) [equal-information H3 control]", per["GRU_eqinfo"] - per["B5_SKNN_locked"]),
                 ("GRU_eqinfo − GRU_lite (locked)", per["GRU_eqinfo"] - per["GRU_lite_locked"]),
                 ("GRU_eqinfo − B3_RecentPop (locked)", per["GRU_eqinfo"] - per["B3_RecentPop_locked"]),
                 ("GRU_eqinfo − B5_SKNN_Mall (M = None)", per["GRU_eqinfo"] - per["B5_SKNN_Mall"])]
        for label, d in pairs:
            rr = C.pair_stats(d, label, year)
            if label.startswith("GRU_eqinfo − B5_SKNN (locked)"):
                rr[0]["six_level_reading_illustrative_uncorrected_p"] = stats.verdict_bidirectional(
                    rr[0]["mean"], rr[0]["ci_lo"], rr[0]["ci_hi"], rr[0]["p_signflip_uncorrected"])
            st += rr
        gc = r[r["slice"] == "all"].groupby(["presentation", "cut"])["NDCG@10"].mean()
        sk = base[(base["model"] == "B5_SKNN") & (base["task"] == "A") & (base["slice"] == "all")].groupby(["presentation", "cut"])["NDCG@10"].mean()
        for cut, dd in (gc - sk).dropna().groupby(level="cut"):
            st.append({"comparison": "GRU_eqinfo − B5_SKNN (locked)", "year": year, "unit": f"origin t = {cut} alone (descriptive)",
                       "n_units": len(dd), "mean": float(dd.mean()), "n_pos": int((dd > 0).sum()), "status": C.POSTHOC_NOTE})
        per = per.reset_index()
        per.insert(0, "year", year)
        per_all.append(per)
        sel = r[(r["slice"] == "all") & (r["seed"] == 0)]["config"].str.replace(r"epochs=\d+;", "", regex=True).value_counts()
        print(f"[a11] {year}: GRU_eqinfo {ge.mean():.4f} | GRU-lite {per['GRU_lite_locked'].mean():.4f} | SKNN "
              f"{per['B5_SKNN_locked'].mean():.4f} | B3 {per['B3_RecentPop_locked'].mean():.4f} | configs {sel.to_dict()}", flush=True)
    s5 = rows[0][(rows[0]["presentation"] == "GGG_2013J") & (rows[0]["cut"] == 126) & (rows[0]["slice"] == "all")]["NDCG@10"]
    san["S5"] = {"presentation": "GGG_2013J", "cut": 126, "test_ndcg10": s5.tolist(), "sd": float(np.std(s5, ddof=1)),
                 "within_0.005": bool(np.std(s5, ddof=1) <= 0.005)}
    (C.OUT / "a11_gru_eqinfo_sanity.json").write_text(json.dumps(san, indent=1, default=float))
    C.write_csv(pd.DataFrame(checks), "a11_reproduction_checks.csv")
    C.write_csv(pd.concat(rows, ignore_index=True), "a11_h3_equal_info_rows.csv")
    C.write_csv(pd.concat(tun, ignore_index=True), "a11_h3_equal_info_tuning.csv")
    C.write_csv(pd.concat(per_all, ignore_index=True), "a11_h3_equal_info_per_presentation.csv")
    C.write_csv(pd.DataFrame(st), "a11_h3_equal_info.csv")
    C.write_csv(pd.DataFrame(meta), "a11_runtime.csv")
    commit, dirty = C.git_commit()
    print(f"[a11] done in {(time.time() - t0) / 60:.1f} min (commit {commit}{' dirty' if dirty else ''})", flush=True)


if __name__ == "__main__":
    main()

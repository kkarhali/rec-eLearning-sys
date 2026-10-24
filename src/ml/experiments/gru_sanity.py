"""GRU-lite sanity package (D-35, draft §4.6.5, Table 15) → results/dev2013/gru_sanity.md (+ .json).

    python3 -m src.ml.experiments.gru_sanity

Gates: S1, S2, S3, S4, S6. S5 is reported only. Speed is reported.
  S1 gradient check: float64, central differences ε = 1e−5, 3 sequences with {1, 3, 5} training steps
     padded with a mask, T ≥ longest (no truncation), random non-zero h0, biases N(0, 0.1²), L2 on,
     ≥ 20 coordinates per matrix (all if fewer); criterion max rel. err < 1e−4.
  S2 overfit: 32 sequences, 300 Adam steps, η = 1e−2, no L2; mean (L − H(y)) ≤ 0.05 nat, train HR@10 ≥ 0.99.
  S3 synthetic Markov chain on 50 items (each state has 5 successors, Dirichlet(1) weights);
     mean TV(p̂, P*) ≤ 0.10 and NDCG@10 ≥ NDCG@10(estimated Markov) − 0.01 on held-out sequences.
  S4 real development fold: no NaN/Inf, last training loss ≤ 0.9 × first, validation curve recorded.
  S5 5 seeds on one development presentation: SD of test NDCG@10 (report; ≤ 0.005 desired).
  S6 masking: padded steps keep h; truncation with T ≥ length equals the full computation; task-A
     candidates exclude seen items (unit tests in src/ml/tests/test_gru.py, re-run here).
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import json  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

from .. import data, metrics, splits  # noqa: E402
from ..models import gru_lite as G  # noqa: E402
from ..models.markov import transition_probabilities  # noqa: E402

OUT = data.RESULTS_DIR / "dev2013"


def s1_gradient_check(seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    I, de, dh = 9, 6, 5
    p = G.init_params(I, de, dh, seed=seed + 1, dtype=np.float64)
    for b in G.BIASES:
        p[b] = rng.normal(0, 0.1, p[b].shape)
    seqs = G.Sequences.from_lists([[[0], [1, 2]],
                                   [[1], [3], [4, 5], [0]],
                                   [[2], [6], [1, 3], [0, 7], [5], [4, 8]]], I)   # 1, 3, 5 training steps
    A, Y, m, tm = seqs.dense_batch([0, 1, 2], "next", dtype=np.float64)
    assert A.shape[0] == 5                                   # T = 5 ≥ longest: one window, no truncation
    h0 = rng.normal(0, 0.5, (3, dh))
    _, g, _ = G.window_loss_grad(p, A, Y, m, tm, h0, l2=G.L2)
    worst, per = 0.0, {}
    eps = 1e-5
    for k in p:
        flat = p[k].ravel()
        n = flat.size if flat.size < 20 else 20
        idx = rng.choice(flat.size, n, replace=False)
        w = 0.0
        for j in idx:
            old = flat[j]
            flat[j] = old + eps
            lp = G.window_loss_grad(p, A, Y, m, tm, h0, l2=G.L2, need_grad=False)[0]
            flat[j] = old - eps
            lm = G.window_loss_grad(p, A, Y, m, tm, h0, l2=G.L2, need_grad=False)[0]
            flat[j] = old
            gn = (lp - lm) / (2 * eps)
            ga = g[k].ravel()[j]
            w = max(w, abs(ga - gn) / max(abs(ga), abs(gn), 1e-6))
        per[k] = w
        worst = max(worst, w)
    return {"max_rel_err": worst, "per_param": per, "pass": worst < 1e-4}


def s2_overfit(seed: int = 0, unique_prefixes: bool = True) -> dict:
    """Overfit test. The batch must be memorisable: with ``unique_prefixes`` every sequence starts with a
    distinct first basket, otherwise identical inputs with different targets impose an irreducible
    (Bayes) floor on L − H(y) (first run: 4 colliding prefixes, floor ≈ 0.055 nat; see gru_sanity.md)."""
    rng = np.random.default_rng(seed)
    I, n_seq, n_bask = 50, 32, 6
    seqs_l = [[list(rng.choice(I, size=rng.integers(1, 4), replace=False)) for _ in range(n_bask)]
              for _ in range(n_seq)]
    if unique_prefixes:
        used = set()
        for sq in seqs_l:
            while tuple(sorted(sq[0])) in used:
                sq[0] = list(rng.choice(I, size=rng.integers(1, 4), replace=False))
            used.add(tuple(sorted(sq[0])))
    seqs = G.Sequences.from_lists(seqs_l, I)
    A, Y, m, tm = seqs.dense_batch(np.arange(n_seq), "next", dtype=np.float32)
    p = G.init_params(I, seed=seed)
    opt = G.Adam(p, 1e-2)
    h0 = np.zeros((n_seq, 64), dtype=np.float32)
    losses = []
    for _ in range(300):
        loss, g, _ = G.window_loss_grad(p, A, Y, m, tm, h0, l2=0.0)
        opt.step(p, g)
        losses.append(loss)
    # final evaluation
    h = h0
    gap, hits, n = 0.0, 0, 0
    for t in range(A.shape[0]):
        h_next = G.forward_states(p, A[t:t + 1], m[t:t + 1], h)
        o = h_next @ p["V"] + p["c"]
        o = o - o.max(axis=1, keepdims=True)
        logp = o - np.log(np.exp(o).sum(axis=1, keepdims=True))
        for b in range(n_seq):
            if tm[t, b]:
                y = Y[t, b]
                L = -float((y * logp[b]).sum())
                H = -float((y[y > 0] * np.log(y[y > 0])).sum())
                gap += L - H
                top = np.argsort(-o[b])[:10]
                hits += bool((y[top] > 0).any())
                n += 1
        h = h_next
    return {"mean_L_minus_H": gap / n, "train_HR@10": hits / n, "loss_first": losses[0],
            "loss_last": losses[-1], "unique_prefixes": unique_prefixes,
            "pass": gap / n <= 0.05 and hits / n >= 0.99}


def s3_markov(seed: int = 0, n_states: int = 50, n_succ: int = 5, n_train: int = 5000, n_test: int = 500,
              length: int = 30, epochs: int = 8) -> dict:
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
    seqs = G.Sequences.from_lists([[[x] for x in s] for s in tr_l], n_states)
    p = G.init_params(n_states, seed=seed)
    opt = G.Adam(p, 3e-3)
    users = np.arange(n_train)
    r2 = np.random.default_rng(seed)
    curve = [G.train_epoch(p, opt, seqs, users, "next", r2) for _ in range(epochs)]
    # held-out: states and predictions at every step
    tv, nd_g, nd_m = [], [], []
    N = np.zeros((n_states, n_states))
    for s in tr_l:
        np.add.at(N, (s[:-1], s[1:]), 1.0)
    Pm = transition_probabilities(N, 0.01)
    te = G.Sequences.from_lists([[[x] for x in s] for s in te_l], n_states)
    A, Y, m, tm = te.dense_batch(np.arange(n_test), "next", dtype=np.float32)
    h = np.zeros((n_test, 64), dtype=np.float32)
    disc = 1 / np.log2(np.arange(2, 12))
    for t in range(A.shape[0]):
        h = G.forward_states(p, A[t:t + 1], m[t:t + 1], h)
        o = (h @ p["V"] + p["c"]).astype(np.float64)
        o -= o.max(axis=1, keepdims=True)
        pr = np.exp(o)
        pr /= pr.sum(axis=1, keepdims=True)
        cur = np.array([s[t] for s in te_l])
        nxt = np.array([s[t + 1] for s in te_l])
        tv.append(0.5 * np.abs(pr - P[cur]).sum(axis=1))
        for scores, acc in ((o, nd_g), (Pm[cur], nd_m)):
            top = np.argsort(-scores, axis=1, kind="stable")[:, :10]
            hit = top == nxt[:, None]
            acc.append((hit * disc).sum(axis=1))
    tv_m = float(np.mean(np.concatenate(tv)))
    ng, nm = float(np.mean(np.concatenate(nd_g))), float(np.mean(np.concatenate(nd_m)))
    return {"mean_TV": tv_m, "NDCG@10_gru": ng, "NDCG@10_markov": nm, "train_loss_curve": curve,
            "pass": tv_m <= 0.10 and ng >= nm - 0.01}


def _val_fn(tr, tg):
    tgt, cand, un, ev = tg.task("A")
    return lambda S: metrics.summarize(metrics.evaluate(S, cand, tgt, un, ev, tr.tiebreak, ks=(10,)))["NDCG@10"]


def s4_real_curve(pres: str = "FFF_2013J", cut: int = 126, lr: float = 3e-3, target: str = "next-new") -> dict:
    p = data.load_presentation(pres)
    tr, tg = splits.make_fold(p, cut, "tune")
    t = time.time()
    m = G.GRULite(seed=0, lr=lr, target=target, val_fn=_val_fn(tr, tg)).fit(tr)
    secs = time.time() - t
    tl = [h["train_loss"] for h in m.history]
    vl = [h["val_ndcg10"] for h in m.history]
    ok = bool(np.all(np.isfinite(tl)) and np.all(np.isfinite(vl)) and tl[-1] <= 0.9 * tl[0])
    n_pos = int(m.seqs._flat("in_train")[0][-1])
    steps = sum(max(m.seqs.length(u) - 1, 0) for u in range(tr.n_users))
    return {"presentation": pres, "cut": cut, "lr": lr, "target": target, "train_loss": tl, "val_ndcg10": vl,
            "best_epoch": m.best_epoch, "seconds": secs, "epochs": len(tl),
            "positions_per_second": steps * len(tl) / secs, "basket_items_per_epoch": n_pos, "pass": ok}


def s5_seeds(pres: str = "GGG_2013J", cut: int = 126) -> dict:
    p = data.load_presentation(pres)
    tr, tg = splits.make_fold(p, cut, "tune")
    best = None
    for cfg in G.GRULite.param_space():
        m = G.GRULite(seed=0, **cfg, val_fn=_val_fn(tr, tg)).fit(tr)
        if best is None or m.best_val > best[0]:
            best = (m.best_val, cfg, m.best_epoch)
    tr2, tg2 = splits.make_fold(p, cut, "test")
    tgt, cand, un, ev = tg2.task("A")
    vals = []
    for s in range(5):
        S = G.GRULite(seed=s, **best[1], epochs=best[2]).fit(tr2).score()
        vals.append(metrics.summarize(metrics.evaluate(S, cand, tgt, un, ev, tr2.tiebreak, ks=(10,)))["NDCG@10"])
    sd = float(np.std(vals, ddof=1))
    return {"presentation": pres, "cut": cut, "config": best[1], "epochs": best[2], "test_ndcg10": vals,
            "sd": sd, "within_0.005": sd <= 0.005}


def s6_unit_tests() -> dict:
    import unittest
    suite = unittest.defaultTestLoader.loadTestsFromName("src.ml.tests.test_gru")
    res = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, "w")).run(suite)
    return {"tests_run": res.testsRun, "failures": len(res.failures) + len(res.errors),
            "pass": res.wasSuccessful()}


def main():
    t0 = time.time()
    res = {}
    res["S2_first_run_colliding_prefixes"] = s2_overfit(unique_prefixes=False)
    for name, fn in (("S1", s1_gradient_check), ("S2", s2_overfit), ("S3", s3_markov),
                     ("S4", s4_real_curve), ("S6", s6_unit_tests), ("S5", s5_seeds)):
        t = time.time()
        res[name] = fn()
        res[name]["seconds_total"] = time.time() - t
        print(f"[gru_sanity] {name}: pass={res[name].get('pass', res[name].get('within_0.005'))} "
              f"({res[name]['seconds_total']:.0f}s)", flush=True)
    gates = all(res[k]["pass"] for k in ("S1", "S2", "S3", "S4", "S6"))
    res["gates_passed"] = gates
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gru_sanity.json").write_text(json.dumps(res, indent=2, default=float))
    fmt = lambda x: f"{x:.4g}" if isinstance(x, float) else str(x)  # noqa: E731
    md = ["# حزمة صحة GRU-lite (D-35) — مولَّد بـ`python3 -m src.ml.experiments.gru_sanity`\n",
          f"**النتيجة: {'اجتاز كل البوابات (S1، S2، S3، S4، S6)' if gates else 'لم يجتز كل البوابات'}** · "
          f"الزمن {(time.time() - t0) / 60:.1f} دقيقة\n",
          "| # | المعيار | القيمة | النتيجة |", "|---|---|---|---|",
          f"| S1 | أقصى خطأ نسبي < 1e-4 | {fmt(res['S1']['max_rel_err'])} | {'✓' if res['S1']['pass'] else '✗'} |",
          f"| S2 | متوسط (L − H(y)) ≤ 0.05 nat؛ HR@10 تدريب ≥ 0.99 | {fmt(res['S2']['mean_L_minus_H'])}؛ "
          f"{fmt(res['S2']['train_HR@10'])} | {'✓' if res['S2']['pass'] else '✗'} |",
          f"| S3 | TV ≤ 0.10؛ NDCG@10 ≥ Markov − 0.01 | TV = {fmt(res['S3']['mean_TV'])}؛ GRU {fmt(res['S3']['NDCG@10_gru'])} "
          f"مقابل Markov {fmt(res['S3']['NDCG@10_markov'])} | {'✓' if res['S3']['pass'] else '✗'} |",
          f"| S4 | لا NaN/Inf، والخسارة الأخيرة ≤ 0.9 × الأولى ({res['S4']['presentation']}، t={res['S4']['cut']}) | "
          f"{fmt(res['S4']['train_loss'][0])} → {fmt(res['S4']['train_loss'][-1])} | {'✓' if res['S4']['pass'] else '✗'} |",
          f"| S5 (إبلاغ) | انحراف NDCG@10 عبر 5 بذور ≤ 0.005 ({res['S5']['presentation']}، t={res['S5']['cut']}) | "
          f"{fmt(res['S5']['sd'])} | {'ضمن الحد' if res['S5']['within_0.005'] else 'يتجاوز (يُوثَّق)'} |",
          f"| S6 | اختبارات القناع ({res['S6']['tests_run']}) | {res['S6']['failures']} إخفاق | {'✓' if res['S6']['pass'] else '✗'} |",
          "",
          "## تفاصيل",
          f"- S1 لكل معامل: " + "، ".join(f"{k} {v:.1e}" for k, v in res["S1"]["per_param"].items()),
          f"- S2 الخسارة: {fmt(res['S2']['loss_first'])} → {fmt(res['S2']['loss_last'])} بعد 300 خطوة.",
          f"- **S2، التشغيل الأول (موثَّق):** كانت بيانات الدفعة تحوي 4 تسلسلات تبدأ بسلة مطابقة لسلة تسلسل آخر "
          f"ويتبعها هدف مختلف، فيستحيل الحفظ (حد بايز غير قابل للاختزال): L − H = "
          f"{fmt(res['S2_first_run_colliding_prefixes']['mean_L_minus_H'])} (✗)، وثبتت القيمة ≈ 0.055 حتى 1200 خطوة "
          "بقص التدرج وبدونه، فليس بطء تقارب ولا خطأ تنفيذ. صُحِّح تصميم الاختبار (بادئات فريدة) قبل إعادة التشغيل، "
          "دون تغيير أي معيار أو أي جزء من النموذج.",
          f"- S3: 5000 تسلسل تدريب × 30 خطوة، 500 اختبار؛ منحنى الخسارة: "
          + "، ".join(f"{x:.3f}" for x in res["S3"]["train_loss_curve"]),
          f"- S4: η = {res['S4']['lr']}، الهدف {res['S4']['target']}؛ أفضل دورة {res['S4']['best_epoch']} من "
          f"{res['S4']['epochs']}؛ منحنى التحقق NDCG@10: " + "، ".join(f"{x:.3f}" for x in res["S4"]["val_ndcg10"]),
          f"- **السرعة:** {res['S4']['positions_per_second']:,.0f} خطوة (متعلم، يوم) في الثانية تدريباً بخيط واحد "
          f"({res['S4']['seconds']:.0f} ث لـ{res['S4']['epochs']} دورات على FFF_2013J، t=126).",
          f"- S5: الإعداد {res['S5']['config']}، {res['S5']['epochs']} دورات؛ القيم "
          + "، ".join(f"{x:.4f}" for x in res["S5"]["test_ndcg10"]),
          "- «التفوق على Random على تسلسل اصطناعي» متضمَّن في S3 (Random على 50 مورداً ≈ 0.07 في NDCG@10).",
          ]
    (OUT / "gru_sanity.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[gru_sanity] gates_passed={gates} in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()

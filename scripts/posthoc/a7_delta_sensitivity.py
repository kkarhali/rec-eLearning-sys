#!/usr/bin/env python3
"""POST-HOC (session 2, م-ك-1 item 2): the registered verdict rule re-applied at δ = 0.015 and δ = 0.025.

No interval is recomputed. The registered precedence tables (ch3 3-5-6, tables 3-14 and 3-15; stats.verdict for
H1, H2-a, H4-a with δ_AUC = δ, stats.verdict_bidirectional for H3) are applied to the locked mean, bootstrap-t
interval and Holm p of results/conf2014/verdicts.csv, and to the rows of results/conf2014/sensitivity_other.csv
that carry an interval and a p:
  * course-level bootstrap (D-31, 7 courses): Holm over the four course-level p values (the same m = 4 family
    structure; the file's p are uncorrected);
  * nominal floor (H1 pair) and the two H4-a training variants: the row's p substituted for that hypothesis's p
    in the locked family, Holm m = 4 recomputed (the other three p from verdicts.csv);
  * the per-origin rows have no interval and no p: not applicable.
The MDE80 of the D-48 text is specific to δ = 0.02 and is not recomputed; the verdict label only is reported.
The margin test p (sign-flip on Δ_p − δ, descriptive) is recomputed from the locked per_presentation.csv.
A δ scan (0.005 to 0.050, step 0.0005) gives, for each main hypothesis, the δ range over which its verdict holds.

Stop condition: at δ = 0.02 the rule must reproduce the locked verdict of every hypothesis, the recomputed Holm p
must equal p_holm, and the recomputed margin p must equal p_margin (≤ 1e-6).

Reads only locked/committed result files (no raw data, no cache): no access-log line (as defense_stats.py).

    python3 scripts/posthoc/a7_delta_sensitivity.py
"""
from __future__ import annotations

import time

from _s2 import C, check_locked_files, np, pd
from src.ml import stats

DELTAS = (0.015, 0.02, 0.025)
HYP = ["H1", "H2-a", "H3", "H4-a"]


def rule(h: str, mean: float, lo: float, hi: float, p_holm: float, delta: float) -> str:
    f = stats.verdict_bidirectional if h == "H3" else stats.verdict
    return f(mean, lo, hi, p_holm, delta)


def main():
    t0 = time.time()
    checks = check_locked_files(["verdicts.csv", "per_presentation.csv", "sensitivity_other.csv"])
    v = pd.read_csv(C.CONF / "verdicts.csv").set_index("hypothesis").loc[HYP]
    pp = pd.read_csv(C.CONF / "per_presentation.csv").set_index("presentation")
    so = pd.read_csv(C.CONF / "sensitivity_other.csv")
    # ---------- reproduction at δ = 0.02 (stop on failure) ----------
    # p is recomputed from the locked per-presentation differences (the CSV holds 6 decimals, and Holm multiplies
    # the rounding error by up to 4)
    p_ex = pd.Series({h: stats.sign_flip_test(pp[h].to_numpy()) for h in HYP})
    checks.append({"year": "2014", **C.check("sign-flip p from per_presentation.csv vs verdicts.csv p", p_ex, v["p"])})
    ph = pd.Series(stats.holm(p_ex.to_numpy()), index=v.index)
    checks.append({"year": "2014", **C.check("Holm p (m = 4) from the recomputed p vs verdicts.csv p_holm", ph, v["p_holm"])})
    pm = pd.Series({h: stats.margin_test(pp[h].to_numpy(), 0.02) for h in HYP})
    checks.append({"year": "2014", **C.check("margin p (δ = 0.02) from per_presentation.csv vs verdicts.csv p_margin",
                                             pm, v["p_margin"])})
    got = {h: rule(h, v.at[h, "mean_delta"], v.at[h, "ci_lo"], v.at[h, "ci_hi"], v.at[h, "p_holm"], 0.02) for h in HYP}
    same = all(got[h] == v.at[h, "verdict"] for h in HYP)
    print(f"[reproduction] verdicts at δ = 0.02 identical to verdicts.csv: {same} {got}", flush=True)
    checks.append({"year": "2014", "check": "verdict at δ = 0.02 = verdicts.csv (4 hypotheses)", "n": 4,
                   "max_abs_diff": 0.0 if same else float("nan"), "tolerance": 0.0, "pass": same})
    if not all(c["pass"] for c in checks if c.get("stop_condition", True)):
        raise SystemExit("[a7] reproduction failed; no new number written")
    # ---------- the rule at δ ∈ {0.015, 0.02, 0.025} ----------
    rows = []

    def add(source, analysis, h, n_units, mean, lo, hi, p, p_holm, holm_note, margin_diffs=None):
        for d in DELTAS:
            r = {"source": source, "analysis": analysis, "hypothesis": h, "n_units": n_units, "delta": d,
                 "delta_is_registered": d == 0.02, "mean": mean, "ci_lo": lo, "ci_hi": hi, "p": p, "p_holm": p_holm,
                 "holm": holm_note, "verdict": rule(h, mean, lo, hi, p_holm, d),
                 "confirmed_with_margin": bool(stats.confirmed_with_margin(lo, d)) and rule(h, mean, lo, hi, p_holm, d)
                 in ("confirmed", "superior_confirmed"),
                 "p_margin_descriptive": stats.margin_test(margin_diffs, d) if margin_diffs is not None else np.nan}
            if d == 0.02 and source.startswith("verdicts"):
                r["locked_verdict"] = v.at[h, "verdict"]
            r["verdict_differs_from_delta_0.02"] = None
            r["status"] = C.POSTHOC_NOTE.replace("p uncorrected", "re-application of the registered rule; "
                                                 "no interval recomputed")
            rows.append(r)
        ref = [x for x in rows[-len(DELTAS):] if x["delta"] == 0.02][0]["verdict"]
        for x in rows[-len(DELTAS):]:
            x["verdict_differs_from_delta_0.02"] = x["verdict"] != ref

    for h in HYP:
        add("verdicts.csv (locked; presentation level, n = 13)", "main confirmatory pair", h, int(v.at[h, "n"]),
            v.at[h, "mean_delta"], v.at[h, "ci_lo"], v.at[h, "ci_hi"], v.at[h, "p"], v.at[h, "p_holm"],
            "locked p_holm", pp[h].to_numpy())
    cl = so[so["analysis"].str.startswith("course-level")].set_index("hypothesis").loc[HYP]
    clh = pd.Series(stats.holm(cl["p"].to_numpy()), index=cl.index)
    for h in HYP:
        add("sensitivity_other.csv", "course-level bootstrap (robustness, D-31)", h, int(cl.at[h, "n_units"]),
            cl.at[h, "mean"], cl.at[h, "ci_lo"], cl.at[h, "ci_hi"], cl.at[h, "p"], float(clh[h]),
            "Holm m = 4 over the four course-level p")
    for analysis in so["analysis"].unique():
        if analysis.startswith("course-level") or analysis.startswith("origin t"):
            continue
        r = so[so["analysis"] == analysis].iloc[0]
        h = r["hypothesis"]
        fam = p_ex.copy()
        fam[h] = r["p"]
        hp = float(pd.Series(stats.holm(fam.to_numpy()), index=fam.index)[h])
        add("sensitivity_other.csv", analysis, h, int(r["n_units"]), r["mean"], r["ci_lo"], r["ci_hi"], r["p"], hp,
            f"Holm m = 4 with this p substituted for {h} (other p recomputed from per_presentation.csv)")
    out = pd.DataFrame(rows)
    na = [{"source": "sensitivity_other.csv", "analysis": a, "hypothesis": h, "verdict": "not applicable (no interval, no p)",
           "status": "descriptive per-origin mean; rule not applicable"}
          for a, h in so[so["analysis"].str.startswith("origin t")][["analysis", "hypothesis"]].itertuples(index=False)]
    out = pd.concat([out, pd.DataFrame(na)], ignore_index=True)
    # ---------- δ scan (main pairs) ----------
    scan = []
    for h in HYP:
        prev, start = None, None
        grid = np.round(np.arange(0.005, 0.0501, 0.0005), 4)
        for d in grid:
            vv = rule(h, v.at[h, "mean_delta"], v.at[h, "ci_lo"], v.at[h, "ci_hi"], v.at[h, "p_holm"], float(d))
            if vv != prev:
                if prev is not None:
                    scan.append({"hypothesis": h, "verdict": prev, "delta_from": start, "delta_to": float(d - 0.0005)})
                prev, start = vv, float(d)
        scan.append({"hypothesis": h, "verdict": prev, "delta_from": start, "delta_to": float(grid[-1])})
    scan = pd.DataFrame(scan)
    scan["status"] = "post-hoc; δ grid step 0.0005; locked mean / interval / Holm p of verdicts.csv"
    C.write_csv(pd.DataFrame(checks), "a7_reproduction_checks.csv")
    C.write_csv(out, "a7_delta_sensitivity.csv")
    C.write_csv(scan, "a7_delta_scan.csv")
    print(out[out["delta"].notna()].pivot_table(index=["analysis", "hypothesis"], columns="delta", values="verdict",
                                               aggfunc="first").to_string())
    print(scan.to_string(index=False))
    commit, dirty = C.git_commit()
    print(f"[a7] done in {time.time() - t0:.1f}s (commit {commit}{' dirty' if dirty else ''})", flush=True)


if __name__ == "__main__":
    main()

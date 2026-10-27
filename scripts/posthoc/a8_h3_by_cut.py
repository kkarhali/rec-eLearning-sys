#!/usr/bin/env python3
"""POST-HOC (session 2, م-ك-5 item 2): the differences of table هـ-2 at each origin t ∈ {70, 126, 182}.

No model is refit. Rows are read from the locked runs (results/dev2013 and results/conf2014: gru.csv for GRU-lite,
baselines.csv for B5 SKNN, M = 1000) and from results/posthoc/a4_2_sknn_all_rows.csv for SKNN(M = all).
For each origin alone, the per-presentation difference (GRU-lite seeds averaged) is analysed with the same
inference as the other post-hoc tools (_common.pair_stats: cluster bootstrap-t B = 10,000 seed 0 and the exact
sign-flip p, uncorrected; presentation level, plus the course-level resampling of table 5-8-هـ). Three pairs:
GRU-lite − SKNN (locked), GRU-lite − SKNN(M = all), SKNN(M = all) − SKNN (locked).

Stop conditions: the per-origin means of GRU-lite − SKNN (locked) on 2014 reproduce results/conf2014/per_origin.csv
(H3) and the "origin t alone" rows of sensitivity_other.csv; the per-origin means of GRU-lite − SKNN(M = all)
reproduce the "origin t alone" rows of a4_2_sknn_all.csv; averaged over origins, the pairs reproduce the H3 column
of conf2014/per_presentation.csv and a4_2_sknn_all_per_presentation.csv; the SKNN rows of the a4_2 registered-space
reproduction equal baselines.csv per fold (all ≤ 1e-6).

Reads only locked/committed result files (no raw data, no cache): no access-log line (as defense_stats.py).

    python3 scripts/posthoc/a8_h3_by_cut.py
"""
from __future__ import annotations

import time

from _s2 import C, check_locked_files, pd
from src.ml.splits import CUTS

A42 = {"reg": "B5_SKNN (registered space, reproduction)", "all": "B5_SKNN_Mall (post-hoc, M = None)"}


def fold_series(df: pd.DataFrame, model: str) -> pd.Series:
    r = df[(df["model"] == model) & (df["task"] == "A") & (df["slice"] == "all")]
    return r.groupby(["presentation", "cut"])["NDCG@10"].mean().sort_index()


def main():
    t0 = time.time()
    checks = check_locked_files(["gru.csv", "baselines.csv", "per_origin.csv", "per_presentation.csv",
                                 "sensitivity_other.csv"])
    a42 = pd.read_csv(C.OUT / "a4_2_sknn_all_rows.csv")
    a42s = pd.read_csv(C.OUT / "a4_2_sknn_all.csv")
    a42p = pd.read_csv(C.OUT / "a4_2_sknn_all_per_presentation.csv")
    st, per_rows = [], []
    for year in ("2013", "2014"):
        src = C.DEV if year == "2013" else C.CONF
        g = fold_series(pd.read_csv(src / "gru.csv"), "GRU_lite")
        s = fold_series(pd.read_csv(src / "baselines.csv"), "B5_SKNN")
        ay = a42[a42["year"] == int(year)]
        sa = fold_series(ay, A42["all"])
        sr = fold_series(ay, A42["reg"])
        checks.append({"year": year, **C.check(f"{year} a4_2 registered-space SKNN per fold vs {src.name}/baselines.csv", sr, s)})
        pairs = {"GRU_lite − B5_SKNN (locked, M = 1000)": g - s, "GRU_lite − B5_SKNN_Mall (M = None)": g - sa,
                 "B5_SKNN_Mall − B5_SKNN (locked)": sa - s}
        # ---------- reproduction ----------
        if year == "2014":
            po = pd.read_csv(C.CONF / "per_origin.csv")
            po = po[po["hypothesis"] == "H3"].set_index("cut")["mean_delta"].sort_index()
            mine = pairs["GRU_lite − B5_SKNN (locked, M = 1000)"].groupby(level="cut").mean().sort_index()
            checks.append({"year": year, **C.check("2014 GRU − SKNN per-origin mean vs conf2014/per_origin.csv (H3)", mine, po)})
            so = pd.read_csv(C.CONF / "sensitivity_other.csv")
            so = so[(so["hypothesis"] == "H3") & so["analysis"].str.startswith("origin t")]
            so = so.set_index(so["analysis"].str.extract(r"t = (\d+)")[0].astype(int).rename("cut"))["mean"].sort_index()
            checks.append({"year": year, **C.check("2014 GRU − SKNN per-origin mean vs conf2014/sensitivity_other.csv", mine, so)})
            ref = pd.read_csv(C.CONF / "per_presentation.csv").set_index("presentation")["H3"].sort_index()
            checks.append({"year": year, **C.check("2014 GRU − SKNN per presentation vs conf2014/per_presentation.csv (H3)",
                                                   C.fold_means(pairs["GRU_lite − B5_SKNN (locked, M = 1000)"].rename("d").reset_index(), "d"), ref)})
        ref = a42s[(a42s["year"] == int(year)) & a42s["unit"].str.startswith("origin t")]
        ref = ref.set_index(ref["unit"].str.extract(r"t = (\d+)")[0].astype(int).rename("cut"))["mean"].sort_index()
        mine = pairs["GRU_lite − B5_SKNN_Mall (M = None)"].groupby(level="cut").mean().sort_index()
        checks.append({"year": year, **C.check(f"{year} GRU − SKNN(M = all) per-origin mean vs a4_2_sknn_all.csv", mine, ref)})
        pp = a42p[a42p["year"] == int(year)].set_index("presentation").sort_index()
        for col, k in (("H3_locked_delta", "GRU_lite − B5_SKNN (locked, M = 1000)"), ("H3_Mall_delta", "GRU_lite − B5_SKNN_Mall (M = None)")):
            checks.append({"year": year, **C.check(f"{year} {k} per presentation vs a4_2_sknn_all_per_presentation.csv {col}",
                                                   C.fold_means(pairs[k].rename("d").reset_index(), "d"), pp[col])})
        if not all(c["pass"] for c in checks if c["year"] == year and c.get("stop_condition", True)):
            raise SystemExit(f"[a8] reproduction failed for {year}; no new number written")
        # ---------- per origin ----------
        for label, d in pairs.items():
            for cut in sorted(CUTS):
                dc = d.xs(cut, level="cut").dropna().sort_index()
                st += C.pair_stats(dc, label, year, cut=cut)
                for p, x in dc.items():
                    per_rows.append({"year": year, "comparison": label, "cut": cut, "presentation": p, "delta": x})
            st += C.pair_stats(C.fold_means(d.rename("d").reset_index(), "d"), label, year, cut="all (mean over origins)")
    out = pd.DataFrame(st)
    C.write_csv(pd.DataFrame(checks), "a8_reproduction_checks.csv")
    C.write_csv(out, "a8_h3_by_cut.csv")
    C.write_csv(pd.DataFrame(per_rows), "a8_h3_by_cut_per_presentation.csv")
    show = out[out["unit"] == "presentation"][["comparison", "year", "cut", "n_units", "mean", "ci_lo", "ci_hi",
                                               "p_signflip_uncorrected", "n_pos"]]
    print(show.to_string(index=False))
    commit, dirty = C.git_commit()
    print(f"[a8] done in {time.time() - t0:.1f}s (commit {commit}{' dirty' if dirty else ''})", flush=True)


if __name__ == "__main__":
    main()

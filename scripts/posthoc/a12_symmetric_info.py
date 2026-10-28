#!/usr/bin/env python3
"""POST-HOC (session 2, round 2: د. العمر and د. الكنج): comparisons that complete tables هـ-7 and هـ-10.

1. Symmetric information for H3: GRU-lite with the recent-popularity input (a11) against the hybrid of recent
   popularity and SKNN with the D-51 floor (a4_1), so both sides see the recent-popularity signal; plus the same
   against the nominal-grid hybrid, and recent popularity alone against the locked SKNN (the part of the a11 gain
   that is recent popularity beating the neighbours).
2. The personalisation gain with SKNN(M = all) on the nominal grid (no floor), next to the floored version of a6.

No model is refit: per-presentation means are read from results/posthoc/a11_*, a4_1_*, a6_* per-presentation files.
Inference as the other post-hoc tools (_common.pair_stats). Stop condition: the per-presentation columns shared by
the files (B3 recent popularity, locked SKNN, C7 alone) agree across files within 1e-6, and the a11 and a6 summary
rows are reproduced from the per-presentation files within 1e-6.

Reads only committed result files: no access-log line.

    python3 scripts/posthoc/a12_symmetric_info.py
"""
from __future__ import annotations

import time

import _common as C
import pandas as pd

TOL = 1e-6


def main():
    t0 = time.time()
    a11 = pd.read_csv(C.OUT / "a11_h3_equal_info_per_presentation.csv").set_index(["year", "presentation"])
    a41 = pd.read_csv(C.OUT / "a4_1_recentpop_sknn_per_presentation.csv").set_index(["year", "presentation"])
    a6 = pd.read_csv(C.OUT / "a6_personalization_mall_per_presentation.csv").set_index(["year", "presentation"])
    s11 = pd.read_csv(C.OUT / "a11_h3_equal_info.csv")
    s6 = pd.read_csv(C.OUT / "a6_personalization_mall.csv")

    checks = []
    def chk(name, a, b):
        d = float((a - b).abs().max())
        checks.append({"check": name, "max_abs_diff": round(d, 9), "tolerance": TOL, "pass": d <= TOL})
    chk("B3 per presentation: a11 = a4_1", a11["B3_RecentPop_locked"], a41["B3_RecentPop"])
    chk("locked SKNN per presentation: a11 = a4_1", a11["B5_SKNN_locked"], a41["B5_SKNN"])
    chk("B3 per presentation: a6 = a4_1", a6["B3_RecentPop_locked"], a41["B3_RecentPop"])
    for year in (2013, 2014):
        y11 = a11.loc[year]
        r = s11[(s11.comparison.str.startswith("GRU_eqinfo − B5_SKNN (locked) [")) & (s11.year == year)
                & (s11.unit == "presentation")].iloc[0]
        chk(f"{year} a11 summary mean reproduced", pd.Series([(y11.GRU_eqinfo - y11.B5_SKNN_locked).mean()]),
            pd.Series([r["mean"]]))
        y6 = a6.loc[year]
        r = s6[(s6.comparison.str.startswith("HYB_Mall − (7) alone")) & (s6.year == year)
               & (s6.unit == "presentation")].iloc[0]
        chk(f"{year} a6 floor gain mean reproduced", pd.Series([(y6.HYB_Mall - y6.C7_alone).mean()]),
            pd.Series([r["mean"]]))
    ck = pd.DataFrame(checks)
    ck.to_csv(C.OUT / "a12_reproduction_checks.csv", index=False)
    if not ck["pass"].all():
        print(ck)
        raise SystemExit("[a12] reproduction failed; no new number written")

    rows = []
    for year in (2013, 2014):
        y11, y41, y6 = a11.loc[year], a41.loc[year], a6.loc[year]
        pairs = {
            "GRU_eqinfo − HYB_B3+SKNN (floor) [both see recent popularity]": y11.GRU_eqinfo - y41["HYB_B3+SKNN"],
            "GRU_eqinfo − HYB_B3+SKNN (nominal grid)": y11.GRU_eqinfo - y41["HYB_B3+SKNN_nominal"],
            "B3_RecentPop − B5_SKNN (locked)": y41.B3_RecentPop - y41.B5_SKNN,
            "HYB_Mall nominal grid − (7) alone [personalisation gain without the floor]": y6.HYB_Mall_nominal - y6.C7_alone,
        }
        for label, d in pairs.items():
            d.index = d.index.astype(str)
            rows += C.pair_stats(d, label, str(year))
    out = pd.DataFrame(rows)
    out.to_csv(C.OUT / "a12_symmetric_info.csv", index=False)
    print(out[["comparison", "year", "unit", "mean", "ci_lo", "ci_hi", "p_signflip_uncorrected", "n_pos", "n_units"]]
          .to_string(index=False))
    print(f"[a12] done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()

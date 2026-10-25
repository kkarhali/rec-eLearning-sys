#!/usr/bin/env python3
"""Two exploratory figures for chapter 3 (D-105), from the 2013 development presentations only.

1. ``eda_long_tail``: concentration of resource popularity per presentation — resources (non-navigational, E5)
   ranked by popularity (distinct learner–resource pairs), cumulative share of pairs against the rank as a fraction
   of the catalogue; the marked point is the share of the top 20% of resources. Legend: top-20% share and Gini.
2. ``eda_activity_share``: share of clicks by activity type, click-weighted over the nine presentations; the five
   navigational types (E5) are highlighted and their total is shown.

Data: ``src.ml.data`` with the dev role only (no 2014 row is loaded). The numbers are computed exactly as
``src/ml/experiments/eda.py`` computes chapter 3's table 3-3 and the click-weighted navigation share, and the script
refuses to write anything unless they equal ``results/dev2013/eda_presentations.csv`` and ``eda_totals.csv``
(read only). Drawing reuses the SVG helpers of ``scripts/derive_conf2014_figures.py`` (RTL Arabic with LTR runs in
Unicode isolates, rendered by Chromium through scripts/svg2png.py; no matplotlib); PNG at scale 3, tagged 300 dpi.

Outputs (paths relative to the repository root): ``deliverables/06-final-thesis/figures/eda_long_tail.{svg,png,csv}``
and ``eda_activity_share.{svg,png,csv}``.

Usage:  python3 scripts/thesis/eda_figures.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.ml import data  # noqa: E402
import derive_conf2014_figures as S  # noqa: E402  (shared SVG/PNG helpers, same Arabic handling)

OUT = ROOT / "deliverables" / "06-final-thesis" / "figures"
DEV = ROOT / "results" / "dev2013"
PAL9 = ["#2b6cb0", "#d9822b", "#2f855a", "#9b2c2c", "#6b46c1", "#b7791f", "#2c7a7b", "#c53030", "#4a5568"]


# ----------------------------------------------------------------------------------------------- data
def long_tail(pres) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, summ = [], []
    for name, p in pres.items():
        ev = p.events
        tgt = ev.loc[~ev["activity_type"].astype(str).isin(data.E5)]
        pairs = tgt[["id_student", "id_site"]].drop_duplicates()
        pop = pairs.groupby("id_site").size().sort_values(ascending=False).to_numpy()   # as eda.presentation_row
        n = len(pop)
        top = max(1, int(round(0.2 * n)))
        cum = np.cumsum(pop) / pop.sum()
        rows += [{"presentation": name, "rank": r + 1, "rank_fraction": (r + 1) / n, "pairs": int(v),
                  "cumulative_share": float(c)} for r, (v, c) in enumerate(zip(pop, cum))]
        from src.ml.experiments.eda import gini
        summ.append({"presentation": name, "n_resources": n, "top20_k": top, "top20pct_items_pair_share": float(cum[top - 1]),
                     "gini_item_popularity": gini(pop)})
    return pd.DataFrame(rows), pd.DataFrame(summ)


def activity_share() -> tuple[pd.DataFrame, float]:
    ev = data.load_daily_events("dev")                       # dev role: the nine 2013 presentations only
    at = ev["activity_type"].astype(str)
    clicks = ev.groupby(at, observed=True)["clicks"].sum().sort_values(ascending=False)
    df = pd.DataFrame({"activity_type": clicks.index, "clicks": clicks.to_numpy(dtype=np.int64)})
    df["click_share"] = df["clicks"] / df["clicks"].sum()
    df["navigational_E5"] = df["activity_type"].isin(data.E5)
    assert set(ev["presentation"].astype(str).unique()) == set(data.DEV_PRESENTATIONS)
    return df, float(df.loc[df["navigational_E5"], "click_share"].sum())


def check_against_results(summ: pd.DataFrame, e5_share: float):
    ref = pd.read_csv(DEV / "eda_presentations.csv").set_index("presentation")
    s = summ.set_index("presentation")
    for col in ("top20pct_items_pair_share", "gini_item_popularity"):
        d = (s[col] - ref.loc[s.index, col]).abs().max()
        if d > 1e-6:
            raise SystemExit(f"REFUSED: {col} differs from results/dev2013/eda_presentations.csv by {d}")
    if (s["n_resources"] != ref.loc[s.index, "sites_nonnav_E5"]).any():
        raise SystemExit("REFUSED: resource counts differ from sites_nonnav_E5")
    tot = pd.read_csv(DEV / "eda_totals.csv").iloc[0]
    if abs(e5_share - tot["click_share_E5"]) > 1e-6:
        raise SystemExit(f"REFUSED: navigational click share {e5_share} ≠ eda_totals {tot['click_share_E5']}")


# ----------------------------------------------------------------------------------------------- figures
def pct(v):
    return f"{100 * v:.1f}%" if v >= 0.0005 else "< 0.1%"     # never print a non-zero share as 0.0%


def fig_long_tail(df: pd.DataFrame, summ: pd.DataFrame) -> str:
    W, H = 1250, 760
    L, R, top, bot = 120, 800, 80, H - 110
    x, y = S.scale(0, 1, L, R), S.scale(0, 1, bot, top)
    body = S.xaxis(x, 0, 1, top, bot, "رتبة المورد كنسبة من الكتالوج (الأكثر شعبية أولاً)")
    body += S.yaxis(y, 0, 1, L, R, "الحصة التراكمية من أزواج (متعلم، مورد)")
    body.append(f"<rect x='{L}' y='{top}' width='{R - L}' height='{bot - top}' fill='none' stroke='{S.INK}'/>"
                f"<line x1='{x(0)}' y1='{y(0)}' x2='{x(1)}' y2='{y(1)}' stroke='{S.REF}' stroke-dasharray='6 4'/>"
                f"<line x1='{x(0.2):.1f}' y1='{top}' x2='{x(0.2):.1f}' y2='{bot}' stroke='{S.REF}' stroke-width='1.5' stroke-dasharray='3 3'/>"
                + S.text(x(0.2) + 6, top + 18, "أعلى 20% من الموارد", 12, anchor="start", fill=S.REF))
    body.append(S.text(x(0.62), y(0.55) + 4, "التوزيع المتساوي", 12, fill=S.REF, rotate=-41))
    for k, r in enumerate(summ.itertuples()):
        g = df[df["presentation"] == r.presentation]
        col = PAL9[k % len(PAL9)]
        pts = [(x(0), y(0))] + [(x(a), y(b)) for a, b in zip(g["rank_fraction"], g["cumulative_share"])]
        body.append(f"<polyline fill='none' stroke='{col}' stroke-width='2.2' points='{' '.join(f'{a:.1f},{b:.1f}' for a, b in pts)}'/>")
        fx = r.top20_k / r.n_resources
        body.append(f"<circle cx='{x(fx):.1f}' cy='{y(r.top20pct_items_pair_share):.1f}' r='5' fill='{col}' stroke='white'/>")
        ly = top + 14 + 30 * k
        body.append(f"<line x1='{R + 30}' y1='{ly}' x2='{R + 60}' y2='{ly}' stroke='{col}' stroke-width='3'/>"
                    + S.text(R + 68, ly + 5, f"{r.presentation}: أعلى 20% = {pct(r.top20pct_items_pair_share)}، جيني = "
                             f"{r.gini_item_popularity:.2f}", 13, anchor="start", fill=col))
    body.append(S.text(R + 68, top + 14 + 30 * len(summ) + 14, "الموارد غير التنقلية وحدها (بعد استبعاد E5)", 12,
                       anchor="start", fill=S.REF))
    return S.svg(W, H, "تركّز شعبية الموارد في عروض التطوير 2013: الحصة التراكمية بحسب رتبة المورد", body)


AT_AR = {"resource": "مورد", "oucontent": "محتوى OU", "forumng": "منتدى", "quiz": "اختبار قصير", "subpage": "صفحة فرعية",
         "homepage": "الصفحة الرئيسية", "url": "رابط", "ouwiki": "ويكي OU", "oucollaborate": "تعاون OU",
         "externalquiz": "اختبار خارجي", "page": "صفحة", "questionnaire": "استبيان", "ouelluminate": "Elluminate",
         "glossary": "مسرد", "dualpane": "لوحة مزدوجة", "htmlactivity": "نشاط HTML", "dataplus": "dataplus",
         "sharedsubpage": "صفحة فرعية مشتركة", "folder": "مجلد", "repeatactivity": "نشاط مكرر"}


def fig_activity(df: pd.DataFrame, e5_share: float) -> str:
    n = len(df)
    W, H = 1150, 150 + 34 * n
    L, R, top, bot = 330, W - 120, 80, 80 + 34 * n
    hi = float(df["click_share"].max()) * 1.1
    x = S.scale(0, hi, L, R)
    body = S.xaxis(x, 0, hi, top - 10, bot, "حصة النقرات (مرجّحة بالنقرات على العروض التسعة)")
    body.append(f"<line x1='{x(0)}' y1='{top - 10}' x2='{x(0)}' y2='{bot}' stroke='{S.INK}'/>")
    for k, r in enumerate(df.itertuples()):
        yy = top + 17 + 34 * k
        col = PAL9[1] if r.navigational_E5 else PAL9[0]
        body.append(f"<rect x='{x(0):.1f}' y='{yy - 11}' width='{max(x(r.click_share) - x(0), 1):.1f}' height='22' fill='{col}' fill-opacity='0.85'/>"
                    + S.text(x(r.click_share) + 8, yy + 5, pct(r.click_share), 12, anchor="start")
                    + S.text(L - 12, yy + 5, f"{AT_AR.get(r.activity_type, r.activity_type)} ({r.activity_type})", 13, anchor="end"))
    lx = R - 330
    body.append(f"<rect x='{lx}' y='{top + 120}' width='18' height='18' fill='{PAL9[0]}'/>"
                + S.text(lx + 26, top + 134, "أنواع غير تنقلية (أهداف التوصية)", 13, anchor="start")
                + f"<rect x='{lx}' y='{top + 150}' width='18' height='18' fill='{PAL9[1]}'/>"
                + S.text(lx + 26, top + 164, f"أنواع تنقلية (E5): مجموعها {pct(e5_share)}", 13, anchor="start"))
    return S.svg(W, H, "حصص النقر بحسب نوع النشاط في عروض التطوير 2013", body)


# ----------------------------------------------------------------------------------------------- main
def main():
    pres = data.load_dev_presentations()
    assert set(pres) == set(data.DEV_PRESENTATIONS)
    lt, summ = long_tail(pres)
    act, e5 = activity_share()
    check_against_results(summ, e5)
    OUT.mkdir(parents=True, exist_ok=True)
    outs = {"eda_long_tail": (fig_long_tail(lt, summ), lt), "eda_activity_share": (fig_activity(act, e5), act)}
    for name, (svg_text, frame) in outs.items():
        (OUT / f"{name}.svg").write_text(svg_text, encoding="utf-8")
        frame.to_csv(OUT / f"{name}.csv", index=False, float_format="%.6f")
    summ.to_csv(OUT / "eda_long_tail_summary.csv", index=False, float_format="%.6f")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "svg2png.py"), *[str(OUT / f"{n}.svg") for n in outs],
                    "--out-dir", str(OUT), "--scale", "3", "--width", "1600"], cwd=ROOT, check=True, capture_output=True)
    for n in outs:
        S.set_dpi(OUT / f"{n}.png", 300)
    print(summ.to_string(index=False))
    print(f"navigational (E5) click share: {e5:.6f}")
    print(f"→ {OUT.relative_to(ROOT)}: " + ", ".join(f"{n}.svg/.png/.csv" for n in outs) + ", eda_long_tail_summary.csv")


if __name__ == "__main__":
    main()

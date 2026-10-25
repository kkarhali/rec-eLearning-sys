#!/usr/bin/env python3
"""Derived display copies of the seven locked E10 figures (D-95).

Reads ONLY the locked companion CSVs ``results/conf2014/figures/fig*.csv`` and ``results/conf2014/verdicts.csv``
(for the verdict labels). Nothing is recomputed, filtered or dropped: every row of every source CSV is drawn, the
zero and δ reference lines are kept where the original has them, and the axis ranges follow the original rules
(``src/ml/plots.py``), so no interval is clipped. The change is presentational only: full labels, a correctly
ordered Arabic title (RTL text with LTR runs in Unicode isolates, shaped by Chromium), size and font, and the H3
verdict label «مدحوضة للتفوق» (D-93); the other verdict labels are those of verdicts.csv. No borderline comment on
the H1 figure (D-92 is disclosed in text only).

Before drawing, the SHA-256 of every source must match its reference, otherwise the script refuses:
  * phase-1 sources (fig1, fig2, fig4, fig5, fig6, verdicts.csv): the hash recorded in ``results/conf2014/LOCK``;
  * phase-2 sources (fig3, fig7) are not covered by LOCK by design (LOCK is written at the end of phase 1, D-75 (1));
    their reference is the blob committed with the E10 results (commit 86c0885), fixed below and re-read from git.
The LOCK file itself must hash to the value recorded in ui_open.json / the meeting minutes.

Outputs in ``deliverables/06-final-thesis/figures/derived/``: ``<fig>.svg``, ``<fig>.png`` (rendered by
scripts/svg2png.py at scale 3, PNG tagged 300 dpi), ``<fig>_plotted.csv`` (the values drawn, byte-identical to the
source, checked), and ``manifest.json`` (source and output SHA-256, the script's commit). ``results/`` is not written.

Usage:  python3 scripts/derive_conf2014_figures.py
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import math
import re
import struct
import subprocess
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "results" / "conf2014"
OUT = ROOT / "deliverables" / "06-final-thesis" / "figures" / "derived"
LOCK_SHA256 = "ab1c563985703a64bc1d5371b4bdeec7a28cb11e67bcb54632d4106aae16334d"
E10_RESULTS_COMMIT = "86c0885"
PHASE2_SHA256 = {  # not in LOCK (phase 2); reference = blob committed in 86c0885
    "figures/fig3_signal_ablation.csv": "cc8e5cb6eb32fe029e02e2de68cfde745aecca919a126ac837a529c2eed39326",
    "figures/fig7_fairness.csv": "2f8d3f322abd423163c09f37dafae1bd3509d725a7ce49c343442a0b566c7e85",
}
FIGS = ["fig1_forest", "fig2_per_presentation", "fig3_signal_ablation", "fig4_models_dev_vs_target", "fig5_roc",
        "fig6_h4b", "fig7_fairness"]
DPI = 300
SCALE = 3

FONT = "font-family='DejaVu Sans, Noto Sans Arabic, Arial, sans-serif'"
INK, GRID, REF = "#222", "#e3e3e3", "#777"
PAL = ["#2b6cb0", "#d9822b", "#2f855a", "#9b2c2c"]
LRI, PDI = "⁦", "⁩"
ARABIC = re.compile(r"[؀-ۿ]")
LTR_RUN = re.compile(r"[A-Za-z0-9Δδ][A-Za-z0-9Δδ_@*.,%+\-−=≤≥<>:/^\u0304 ]*[A-Za-z0-9Δδ*%=≤≥<>\u0304]|[A-Za-z0-9Δδ]")

VERDICT_DISPLAY = {"H3": "مدحوضة للتفوق"}            # D-93; every other label as in verdicts.csv (Arabic form)
VERDICT_AR = {"confirmed": "مؤكَّدة", "inconclusive": "غير حاسمة",
              "refuted": "مدحوضة عملياً (استُبعد أثر ≥ δ)"}


# ----------------------------------------------------------------------------------------------- checks
def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_sources() -> dict:
    if sha256(CONF / "LOCK") != LOCK_SHA256:
        raise SystemExit("REFUSED: results/conf2014/LOCK does not match its recorded SHA-256")
    lock = json.loads((CONF / "LOCK").read_text())
    out = {}
    for rel in ["verdicts.csv"] + [f"figures/{f}.csv" for f in FIGS]:
        h = sha256(CONF / rel)
        if rel in lock["files"]:
            ref, src = lock["files"][rel], "LOCK"
        else:
            ref, src = PHASE2_SHA256[rel], f"commit {E10_RESULTS_COMMIT}"
            try:
                blob = subprocess.run(["git", "show", f"{E10_RESULTS_COMMIT}:results/conf2014/{rel}"], cwd=ROOT,
                                      capture_output=True, check=True).stdout
                if hashlib.sha256(blob).hexdigest() != ref:
                    raise SystemExit(f"REFUSED: committed blob of {rel} differs from the fixed reference")
            except (OSError, subprocess.CalledProcessError):
                pass                                   # git unavailable: the fixed reference still applies
        if h != ref:
            raise SystemExit(f"REFUSED: {rel} SHA-256 {h[:12]}… does not match {src} ({ref[:12]}…)")
        out[rel] = {"sha256": h, "reference": src}
    return out


# ----------------------------------------------------------------------------------------------- svg helpers
def t(s: str) -> str:
    """XML-escape; for Arabic text isolate the LTR runs so the order is right in an RTL line."""
    s = str(s)
    if ARABIC.search(s):
        s = LTR_RUN.sub(lambda m: f"{LRI}{m.group(0)}{PDI}", s)
    return html.escape(s)


def text(x, y, s, size=13, anchor="middle", weight="normal", fill=INK, rotate=None):
    rtl = bool(ARABIC.search(str(s)))
    # with direction=rtl, SVG 'start'/'end' are mirrored; keep the requested visual anchor
    a = {"start": "end", "end": "start"}.get(anchor, anchor) if rtl else anchor
    tr = f" transform='rotate({rotate} {x:.1f} {y:.1f})'" if rotate is not None else ""
    return (f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{a}' font-weight='{weight}' fill='{fill}'"
            f" direction='{'rtl' if rtl else 'ltr'}'{tr}>{t(s)}</text>")


def svg(w, h, title, body):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' {FONT}>"
            f"<rect width='100%' height='100%' fill='white'/>" + text(w / 2, 34, title, 18, weight="bold")
            + "".join(body) + "</svg>")


def scale(lo, hi, a, b):
    lo, hi = float(lo), float(hi)
    if hi - lo < 1e-12:
        hi = lo + 1.0
    return lambda v: a + (float(v) - lo) / (hi - lo) * (b - a)


def ticks(lo, hi, n=6):
    span = hi - lo
    step = 10 ** math.floor(math.log10(span / n))
    for m in (1, 2, 2.5, 5, 10):
        if span / (m * step) <= n:
            step *= m
            break
    v = math.ceil(lo / step) * step
    out = []
    while v <= hi + 1e-12:
        out.append(round(v, 10))
        v += step
    return out


def fmt(v):
    return f"{v:.3f}".rstrip("0").rstrip(".") if abs(v) >= 1e-12 else "0"


def xaxis(x, lo, hi, y0, y1, label):
    b = [f"<line x1='{x(lo):.1f}' y1='{y1}' x2='{x(hi):.1f}' y2='{y1}' stroke='{INK}'/>"]
    for v in ticks(lo, hi):
        b.append(f"<line x1='{x(v):.1f}' y1='{y0}' x2='{x(v):.1f}' y2='{y1}' stroke='{GRID}'/>"
                 f"<line x1='{x(v):.1f}' y1='{y1}' x2='{x(v):.1f}' y2='{y1 + 5}' stroke='{INK}'/>" + text(x(v), y1 + 20, fmt(v), 12))
    b.append(text((x(lo) + x(hi)) / 2, y1 + 44, label, 14))
    return b


def yaxis(y, lo, hi, x0, x1, label):
    b = [f"<line x1='{x0}' y1='{y(lo):.1f}' x2='{x0}' y2='{y(hi):.1f}' stroke='{INK}'/>"]
    for v in ticks(lo, hi):
        b.append(f"<line x1='{x0}' y1='{y(v):.1f}' x2='{x1}' y2='{y(v):.1f}' stroke='{GRID}'/>"
                 f"<line x1='{x0 - 5}' y1='{y(v):.1f}' x2='{x0}' y2='{y(v):.1f}' stroke='{INK}'/>"
                 + text(x0 - 9, y(v) + 4, fmt(v), 12, anchor="end"))
    b.append(text(x0 - 62, (y(lo) + y(hi)) / 2, label, 14, rotate=-90))
    return b


def ref_v(x, v, y0, y1, label):
    return (f"<line x1='{x(v):.1f}' y1='{y0}' x2='{x(v):.1f}' y2='{y1}' stroke='{REF}' stroke-width='1.5' stroke-dasharray='6 4'/>"
            + text(x(v), y0 - 6, label, 12, fill=REF))


# ----------------------------------------------------------------------------------------------- figures
def fig1(df, ver):
    rows = df.reset_index(drop=True)
    labels = {}
    for _, r in rows.iterrows():
        v = ver.loc[r["label"], "verdict"]
        if r["label"] not in VERDICT_DISPLAY and VERDICT_AR[v] != r["note"]:
            raise SystemExit(f"REFUSED: fig1 note for {r['label']} disagrees with verdicts.csv")
        labels[r["label"]] = VERDICT_DISPLAY.get(r["label"], VERDICT_AR[v])
    fin = np.r_[rows["mean"], rows["lo"], rows["hi"], [0.0, 0.02]].astype(float)
    fin = fin[np.isfinite(fin)]
    lo, hi = fin.min(), fin.max()
    pad = 0.1 * (hi - lo + 1e-9)
    W, H = 1100, 150 + 70 * len(rows)
    L, R, top, bot = 120, 760, 80, 80 + 70 * len(rows)
    x = scale(lo - pad, hi + pad, L, R)
    body = xaxis(x, lo - pad, hi + pad, top - 10, bot, "Δ̄ (متوسط الفرق عبر عروض 2014)")
    body += [ref_v(x, 0.0, top - 10, bot, "0"), ref_v(x, 0.02, top - 10, bot, "δ = 0.02")]
    body.append(text(R + 30 + (W - 30 - R - 30) / 2, top - 16, "الحكم", 13, weight="bold"))
    for k, r in rows.iterrows():
        y = top + 30 + 70 * k
        body.append(text(L - 14, y + 5, r["label"], 14, anchor="end", weight="bold"))
        body.append(f"<line x1='{x(r['lo']):.1f}' y1='{y}' x2='{x(r['hi']):.1f}' y2='{y}' stroke='{PAL[0]}' stroke-width='3'/>"
                    f"<line x1='{x(r['lo']):.1f}' y1='{y - 7}' x2='{x(r['lo']):.1f}' y2='{y + 7}' stroke='{PAL[0]}' stroke-width='2'/>"
                    f"<line x1='{x(r['hi']):.1f}' y1='{y - 7}' x2='{x(r['hi']):.1f}' y2='{y + 7}' stroke='{PAL[0]}' stroke-width='2'/>"
                    f"<circle cx='{x(r['mean']):.1f}' cy='{y}' r='6' fill='{PAL[0]}'/>")
        body.append(text(W - 30, y + 5, labels[r["label"]], 14, anchor="end"))
    title = "الفرضيات الأربع على عروض 2014: متوسط الفرق Δ̄ وفاصل bootstrap-t"
    return svg(W, H, title, body), {"verdict_labels_drawn": labels}


def fig2(df):
    groups = list(dict.fromkeys(df["group"]))
    vals = df["value"].astype(float).to_numpy()
    vals = vals[np.isfinite(vals)]
    lo, hi = min(vals.min(), 0.0), max(vals.max(), 0.0)
    pad = 0.05 * (hi - lo + 1e-9)
    W, H = 1100, 150 + 80 * len(groups)
    L, R, top, bot = 140, W - 50, 80, 80 + 80 * len(groups)
    x = scale(lo - pad, hi + pad, L, R)
    body = xaxis(x, lo - pad, hi + pad, top - 10, bot, "Δ_p (الفرق في كل عرض من عروض 2014)")
    body.append(ref_v(x, 0.0, top - 10, bot, "0"))
    for k, g in enumerate(groups):
        y = top + 40 + 80 * k
        body.append(text(L - 14, y + 5, g, 14, anchor="end", weight="bold"))
        for j, r in enumerate(df[df["group"] == g].itertuples()):
            if np.isfinite(r.value):
                body.append(f"<circle cx='{x(r.value):.1f}' cy='{y + (j % 3 - 1) * 9}' r='5.5' fill='{PAL[k % 4]}' "
                            f"fill-opacity='0.75' stroke='white' stroke-width='0.8'><title>{html.escape(r.item)}: "
                            f"{r.value:.6f}</title></circle>")
    return svg(W, H, "الفرق Δ_p لكل عرض من عروض 2014، بحسب الفرضية", body), {}


SERIES_AR = {"WRMF dev 2013": "WRMF — التطوير 2013", "WRMF target": "WRMF — الهدف 2014"}
CAT_AR = {"Wstar": "W*"}


def fig3(df):
    cats = list(dict.fromkeys(df["x"]))
    vals = df["y"].astype(float).to_numpy()
    lo, hi = vals.min() * 0.95, vals.max() * 1.05            # the original range rule (plots.lines)
    W, H = 1000, 560
    L, R, top, bot = 110, W - 270, 70, H - 90
    x = scale(0, max(len(cats) - 1, 1), L + 30, R - 30)
    y = scale(lo, hi, bot, top)
    body = yaxis(y, lo, hi, L, R, "NDCG@10")
    body.append(f"<line x1='{L}' y1='{bot}' x2='{R}' y2='{bot}' stroke='{INK}'/>")
    for i, c in enumerate(cats):
        body.append(text(x(i), bot + 22, CAT_AR.get(c, c), 13))
    body.append(text((L + R) / 2, bot + 50, "مستوى الإشارة", 14))
    for k, (name, g) in enumerate(df.groupby("series", sort=False)):
        pts = [(x(cats.index(c)), y(v)) for c, v in zip(g["x"], g["y"])]
        col = PAL[k % 4]
        body.append(f"<polyline fill='none' stroke='{col}' stroke-width='2.5' points='{' '.join(f'{a:.1f},{b:.1f}' for a, b in pts)}'/>")
        body += [f"<circle cx='{a:.1f}' cy='{b:.1f}' r='5' fill='{col}'/>" for a, b in pts]
        ly = top + 20 + 28 * k
        body.append(f"<line x1='{R + 20}' y1='{ly}' x2='{R + 50}' y2='{ly}' stroke='{col}' stroke-width='3'/>"
                    + text(R + 58, ly + 5, SERIES_AR.get(name, name), 13, anchor="start", fill=col))
    return svg(W, H, "استئصال الإشارة لـWRMF: NDCG@10 بحسب مستوى الإشارة", body), {"series_labels": SERIES_AR,
                                                                                     "category_labels": CAT_AR}


def fig4(df):
    vals = np.r_[df["a"], df["b"]].astype(float)
    vals = vals[np.isfinite(vals)]
    lo, hi = max(vals.min() - 0.05, 0), vals.max() + 0.05      # the original range rule (plots.dumbbell)
    W, H = 1000, 170 + 42 * len(df)
    L, R, top, bot = 190, W - 50, 90, 90 + 42 * len(df)
    x = scale(lo, hi, L, R)
    body = xaxis(x, lo, hi, top - 10, bot, "NDCG@10 (المهمة A)")
    body.append(f"<circle cx='{R - 250}' cy='60' r='6' fill='{PAL[0]}'/>" + text(R - 240, 65, "التطوير 2013", 13, anchor="start")
                + f"<circle cx='{R - 120}' cy='60' r='6' fill='{PAL[1]}'/>" + text(R - 110, 65, "الهدف 2014", 13, anchor="start"))
    for k, r in df.reset_index(drop=True).iterrows():
        yy = top + 21 + 42 * k
        body.append(text(L - 14, yy + 5, r["label"], 13, anchor="end"))
        body.append(f"<line x1='{x(r['a']):.1f}' y1='{yy}' x2='{x(r['b']):.1f}' y2='{yy}' stroke='#bbb' stroke-width='4'/>")
        for v, col in ((r["a"], PAL[0]), (r["b"], PAL[1])):
            body.append(f"<circle cx='{x(v):.1f}' cy='{yy}' r='6.5' fill='{col}'><title>{v:.6f}</title></circle>")
    return svg(W, H, "NDCG@10 للمهمة A: التطوير 2013 مقابل الهدف 2014", body), {"legend": {"a": "التطوير 2013",
                                                                                       "b": "الهدف 2014"}}


def fig5(df):
    W, H = 760, 760
    L, R, top, bot = 110, W - 40, 70, H - 100
    x, y = scale(0, 1, L, R), scale(0, 1, bot, top)
    body = xaxis(x, 0, 1, top, bot, "معدل الإيجابيات الكاذبة (FPR)") + yaxis(y, 0, 1, L, R, "معدل الإيجابيات الصحيحة (TPR)")
    body.append(f"<rect x='{L}' y='{top}' width='{R - L}' height='{bot - top}' fill='none' stroke='{INK}'/>"
                f"<line x1='{x(0)}' y1='{y(0)}' x2='{x(1)}' y2='{y(1)}' stroke='{REF}' stroke-dasharray='6 4'/>")
    for k, (name, g) in enumerate(df.groupby("curve", sort=False)):
        col = PAL[k % 4]
        pts = " ".join(f"{x(a):.2f},{y(b):.2f}" for a, b in zip(g["fpr"], g["tpr"]))   # every point of the CSV
        body.append(f"<polyline fill='none' stroke='{col}' stroke-width='2.5' points='{pts}'/>")
        ly = bot - 30 - 28 * k
        body.append(f"<line x1='{R - 150}' y1='{ly}' x2='{R - 120}' y2='{ly}' stroke='{col}' stroke-width='3'/>"
                    + text(R - 112, ly + 5, name, 14, anchor="start", fill=col))
    return svg(W, H, "منحنيات ROC لنماذج الخطر عند اليوم 56 (عروض 2014)", body), {
        "note": "legend shows model names only: the AUC is not in fig5_roc.csv and is not recomputed (h4a_auc.csv)"}


GROUP_AR = {"cold_q1": "الربع الأدنى (cold_q1)", "top_q4": "الربع الأعلى (top_q4)"}
ATTR_AR = {"gender": "الجنس", "disability": "الإعاقة", "imd_band": "شريحة IMD", "age_band": "الفئة العمرية"}


def bars(df, title, ylabel, glabel, W, rot=None):
    groups = list(dict.fromkeys(df["group"]))
    vals = np.r_[df["mean"], df["lo"], df["hi"], 0.0].astype(float)
    vals = vals[np.isfinite(vals)]
    lo, hi = min(vals.min(), 0), vals.max() * 1.1 + 1e-9         # the original range rule (plots.bars), zero kept
    H = 620 if rot else 520
    L, R, top, bot = 110, W - 40, 70, H - (200 if rot else 100)
    y = scale(lo, hi, bot, top)
    body = yaxis(y, lo, hi, L, R, ylabel)
    body.append(f"<line x1='{L}' y1='{y(0):.1f}' x2='{R}' y2='{y(0):.1f}' stroke='{INK}' stroke-width='1.5'/>")
    slot = (R - L) / len(groups)
    bw = min(70, slot * 0.6)
    for i, g in enumerate(groups):
        r = df[df["group"] == g].iloc[0]
        cx = L + slot * (i + 0.5)
        topv, base = y(max(r["mean"], 0)), y(min(r["mean"], 0))
        body.append(f"<rect x='{cx - bw / 2:.1f}' y='{topv:.1f}' width='{bw:.1f}' height='{max(base - topv, 1):.1f}' "
                    f"fill='{PAL[0]}' fill-opacity='0.85'><title>{r['mean']:.6f}</title></rect>"
                    f"<line x1='{cx:.1f}' y1='{y(r['lo']):.1f}' x2='{cx:.1f}' y2='{y(r['hi']):.1f}' stroke='{INK}' stroke-width='1.5'/>"
                    f"<line x1='{cx - 7:.1f}' y1='{y(r['lo']):.1f}' x2='{cx + 7:.1f}' y2='{y(r['lo']):.1f}' stroke='{INK}' stroke-width='1.5'/>"
                    f"<line x1='{cx - 7:.1f}' y1='{y(r['hi']):.1f}' x2='{cx + 7:.1f}' y2='{y(r['hi']):.1f}' stroke='{INK}' stroke-width='1.5'/>")
        if rot:
            body.append(text(cx + 4, bot + 16, glabel(g), 13, anchor="end", rotate=rot))
        else:
            body.append(text(cx, bot + 24, glabel(g), 14))
    return svg(W, H, title, body)


def fig6(df):
    return bars(df, "H4-ب: فرق NDCG@10 في الربع الأدنى والربع الأعلى (عروض 2014)", "Δ NDCG@10",
                lambda g: GROUP_AR.get(g, g), 760), {"group_labels": GROUP_AR}


def fig7(df):
    def lab(g):
        a, _, v = g.partition(":")
        return f"{ATTR_AR.get(a, a)}: {v}"
    return bars(df, "الإنصاف الوصفي: NDCG@10 لـHYB* بحسب المجموعات (عروض 2014)", "NDCG@10 (HYB*)", lab, 1500,
                rot=-40), {"group_labels": {g: lab(g) for g in df["group"]}}


DRAW = {"fig1_forest": fig1, "fig2_per_presentation": fig2, "fig3_signal_ablation": fig3,
        "fig4_models_dev_vs_target": fig4, "fig5_roc": fig5, "fig6_h4b": fig6, "fig7_fairness": fig7}


# ----------------------------------------------------------------------------------------------- png
def set_dpi(png: Path, dpi: int):
    """Insert/replace the pHYs chunk so the PNG carries its resolution (pixels per metre)."""
    data = png.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    ppm = int(round(dpi / 0.0254))
    phys = struct.pack(">IIB", ppm, ppm, 1)
    chunk = struct.pack(">I", 9) + b"pHYs" + phys + struct.pack(">I", zlib.crc32(b"pHYs" + phys) & 0xFFFFFFFF)
    out, i = [data[:8]], 8
    while i < len(data):
        n = struct.unpack(">I", data[i:i + 4])[0]
        typ = data[i + 4:i + 8]
        block = data[i:i + 12 + n]
        if typ != b"pHYs":
            out.append(block)
        if typ == b"IHDR":
            out.append(chunk)
        i += 12 + n
    png.write_bytes(b"".join(out))


def png_size(png: Path):
    return struct.unpack(">II", png.read_bytes()[16:24])


def git_info():
    def run(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rel = "scripts/derive_conf2014_figures.py"
    return {"head": run("rev-parse", "HEAD"), "script_last_commit": run("log", "-1", "--format=%H", "--", rel) or None,
            "script_uncommitted_changes": bool(run("status", "--porcelain", "--", rel))}


# ----------------------------------------------------------------------------------------------- main
def main():
    sources = check_sources()
    ver = pd.read_csv(CONF / "verdicts.csv").set_index("hypothesis")
    OUT.mkdir(parents=True, exist_ok=True)
    figs = {}
    for f in FIGS:
        src = CONF / "figures" / f"{f}.csv"
        raw = src.read_bytes()
        df = pd.read_csv(io.BytesIO(raw))
        content, extra = DRAW[f](df, ver) if f == "fig1_forest" else DRAW[f](df)
        (OUT / f"{f}.svg").write_text(content, encoding="utf-8")
        plotted = OUT / f"{f}_plotted.csv"
        df.to_csv(plotted, index=False, float_format="%.6f")          # the frame that was drawn, row for row
        if plotted.read_bytes() != raw:
            raise SystemExit(f"plotted values of {f} differ from the source CSV")
        figs[f] = {"source": f"results/conf2014/figures/{f}.csv", "rows_drawn": int(len(df)), **extra}
    subprocess.run([sys.executable, str(ROOT / "scripts" / "svg2png.py"), *[str(OUT / f"{f}.svg") for f in FIGS],
                    "--out-dir", str(OUT), "--scale", str(SCALE), "--width", "1600"], cwd=ROOT, check=True,
                   capture_output=True)
    for f in FIGS:
        set_dpi(OUT / f"{f}.png", DPI)
        w, h = png_size(OUT / f"{f}.png")
        figs[f].update({"png_px": [w, h], "png_dpi": DPI,
                        "outputs_sha256": {ext: sha256(OUT / f"{f}{ext}") for ext in (".svg", ".png", "_plotted.csv")}})
    manifest = {"decision": "D-95 (annex of meeting 04)", "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "lock_sha256": LOCK_SHA256, "sources": sources, "figures": figs, "script": git_info(),
                "unchanged": "no value recomputed, filtered or dropped; zero/δ lines and original axis-range rules kept"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(FIGS)} figures → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

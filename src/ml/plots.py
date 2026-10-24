"""Minimal SVG figure generator (no matplotlib): forest plots, strip plots, line charts, dumbbells, ROC curves and
grouped bars with error bars. Every figure is written with the CSV of its data. PNGs are produced afterwards with
``python3 scripts/svg2png.py <svg> --out-dir <dir>`` (Playwright/Chromium).

Text containing numbers or the symbols ≤ ≥ < > is wrapped in Unicode bidi isolates (LRI U+2066 … PDI U+2069)
so that right-to-left rendering in Chromium does not reorder it (review note m4).
"""
from __future__ import annotations

import html
from pathlib import Path

import numpy as np
import pandas as pd

LRI, PDI = "⁦", "⁩"
PALETTE = ["#2F6DB5", "#C0504D", "#4F8A3F", "#8064A2", "#D08A2C", "#4BACC6", "#7F8A9C"]
FONT = "font-family='Noto Sans Arabic, DejaVu Sans, Arial, sans-serif'"


def iso(s) -> str:
    """Escape for XML and isolate LTR runs (numbers, symbols)."""
    s = html.escape(str(s))
    return f"{LRI}{s}{PDI}" if any(ch.isdigit() or ch in "≤≥<>±−+" for ch in s) else s


def _svg(w, h, body, title):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' {FONT}>"
            f"<rect width='100%' height='100%' fill='white'/>"
            f"<text x='{w / 2}' y='22' font-size='15' text-anchor='middle' font-weight='bold'>{html.escape(title)}</text>"
            + "".join(body) + "</svg>")


def _scale(lo, hi, a, b):
    lo, hi = float(lo), float(hi)
    if hi - lo < 1e-12:
        hi = lo + 1.0
    return lambda v: a + (float(v) - lo) / (hi - lo) * (b - a)


def _finite(x, fallback):
    return x if np.isfinite(x) else fallback


def _save(path: Path, svg: str, data: pd.DataFrame):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    data.to_csv(path.with_suffix(".csv"), index=False, float_format="%.6f")
    return path


def forest(path, rows: list[dict], title: str, ref_lines=(0.0, 0.02), xlabel="Δ"):
    """rows: {label, mean, lo, hi, note}. Infinite bounds are drawn as arrows to the panel edge."""
    df = pd.DataFrame(rows)
    fin = np.r_[df["mean"].to_numpy(dtype=float), df["lo"].to_numpy(dtype=float), df["hi"].to_numpy(dtype=float), list(ref_lines)]
    fin = fin[np.isfinite(fin)]
    lo, hi = fin.min(), fin.max()
    pad = 0.1 * (hi - lo + 1e-9)
    W, H = 760, 70 + 46 * len(rows)
    x = _scale(lo - pad, hi + pad, 260, W - 150)
    body = []
    for r in ref_lines:
        body.append(f"<line x1='{x(r)}' y1='40' x2='{x(r)}' y2='{H - 30}' stroke='#999' stroke-dasharray='4 3'/>"
                    f"<text x='{x(r)}' y='{H - 14}' font-size='11' text-anchor='middle'>{iso(f'{r:g}')}</text>")
    for k, r in df.reset_index(drop=True).iterrows():
        y = 60 + 46 * k
        a, b = _finite(r["lo"], lo - pad), _finite(r["hi"], hi + pad)
        body.append(f"<text x='250' y='{y + 4}' font-size='12' text-anchor='end'>{iso(r['label'])}</text>"
                    f"<line x1='{x(a)}' y1='{y}' x2='{x(b)}' y2='{y}' stroke='{PALETTE[0]}' stroke-width='2'/>"
                    f"<circle cx='{x(r['mean'])}' cy='{y}' r='5' fill='{PALETTE[0]}'/>"
                    f"<text x='{W - 140}' y='{y + 4}' font-size='11'>{iso(r.get('note', ''))}</text>")
        if not np.isfinite(r["lo"]):
            body.append(f"<text x='{x(a) - 4}' y='{y + 4}' font-size='12' text-anchor='end'>◀</text>")
        if not np.isfinite(r["hi"]):
            body.append(f"<text x='{x(b) + 4}' y='{y + 4}' font-size='12'>▶</text>")
    body.append(f"<text x='{(260 + W - 150) / 2}' y='{H - 2}' font-size='12' text-anchor='middle'>{iso(xlabel)}</text>")
    return _save(path, _svg(W, H, body, title), df)


def strip(path, data: dict[str, dict[str, float]], title: str, ref_lines=(0.0,)):
    """data: group → {item → value} (e.g. hypothesis → {presentation → Δ_p})."""
    groups = list(data)
    vals = np.array([v for g in groups for v in data[g].values()], dtype=float)
    vals = vals[np.isfinite(vals)]
    lo, hi = min(vals.min(), min(ref_lines)), max(vals.max(), max(ref_lines))
    W, H = 760, 80 + 60 * len(groups)
    x = _scale(lo - 0.05 * (hi - lo + 1e-9), hi + 0.05 * (hi - lo + 1e-9), 200, W - 40)
    body = []
    for r in ref_lines:
        body.append(f"<line x1='{x(r)}' y1='40' x2='{x(r)}' y2='{H - 30}' stroke='#999' stroke-dasharray='4 3'/>")
    rows = []
    for k, g in enumerate(groups):
        y = 70 + 60 * k
        body.append(f"<text x='190' y='{y + 4}' font-size='12' text-anchor='end'>{iso(g)}</text>")
        for j, (item, v) in enumerate(data[g].items()):
            rows.append({"group": g, "item": item, "value": v})
            if np.isfinite(v):
                body.append(f"<circle cx='{x(v)}' cy='{y + (j % 3 - 1) * 6}' r='4' fill='{PALETTE[k % len(PALETTE)]}' "
                            f"fill-opacity='0.8'><title>{html.escape(str(item))}: {v:.4f}</title></circle>")
    return _save(path, _svg(W, H, body, title), pd.DataFrame(rows))


def lines(path, series: dict[str, dict[str, float]], title: str, ylabel="NDCG@10"):
    """series: name → {x category → y} with shared ordered categories."""
    cats = list(dict.fromkeys(c for s in series.values() for c in s))
    vals = np.array([v for s in series.values() for v in s.values()], dtype=float)
    W, H = 760, 380
    x = _scale(0, max(len(cats) - 1, 1), 90, W - 160)
    y = _scale(vals.min() * 0.95, vals.max() * 1.05, H - 50, 50)
    body = [f"<line x1='90' y1='{H - 50}' x2='{W - 160}' y2='{H - 50}' stroke='#333'/>",
            f"<text x='20' y='{H / 2}' font-size='12' transform='rotate(-90 20 {H / 2})' text-anchor='middle'>{iso(ylabel)}</text>"]
    for i, c in enumerate(cats):
        body.append(f"<text x='{x(i)}' y='{H - 30}' font-size='12' text-anchor='middle'>{iso(c)}</text>")
    rows = []
    for k, (name, s) in enumerate(series.items()):
        pts = [(x(cats.index(c)), y(v)) for c, v in s.items() if np.isfinite(v)]
        col = PALETTE[k % len(PALETTE)]
        body.append(f"<polyline fill='none' stroke='{col}' stroke-width='2' points='{' '.join(f'{a},{b}' for a, b in pts)}'/>")
        body += [f"<circle cx='{a}' cy='{b}' r='3.5' fill='{col}'/>" for a, b in pts]
        body.append(f"<text x='{W - 150}' y='{60 + 18 * k}' font-size='12' fill='{col}'>{iso(name)}</text>")
        rows += [{"series": name, "x": c, "y": v} for c, v in s.items()]
    return _save(path, _svg(W, H, body, title), pd.DataFrame(rows))


def dumbbell(path, rows: list[dict], title: str, a_label="2013", b_label="target"):
    """rows: {label, a, b}."""
    df = pd.DataFrame(rows)
    vals = np.r_[df["a"].to_numpy(dtype=float), df["b"].to_numpy(dtype=float)]
    vals = vals[np.isfinite(vals)]
    W, H = 760, 80 + 34 * len(rows)
    x = _scale(max(vals.min() - 0.05, 0), vals.max() + 0.05, 220, W - 60)
    body = [f"<text x='{W - 60}' y='42' font-size='12' text-anchor='end'>"
            f"<tspan fill='{PALETTE[0]}'>● {iso(a_label)}</tspan>  <tspan fill='{PALETTE[1]}'>● {iso(b_label)}</tspan></text>"]
    for k, r in df.reset_index(drop=True).iterrows():
        yy = 70 + 34 * k
        body.append(f"<text x='210' y='{yy + 4}' font-size='12' text-anchor='end'>{iso(r['label'])}</text>")
        if np.isfinite(r["a"]) and np.isfinite(r["b"]):
            body.append(f"<line x1='{x(r['a'])}' y1='{yy}' x2='{x(r['b'])}' y2='{yy}' stroke='#bbb' stroke-width='3'/>")
        for v, col in ((r["a"], PALETTE[0]), (r["b"], PALETTE[1])):
            if np.isfinite(v):
                body.append(f"<circle cx='{x(v)}' cy='{yy}' r='5' fill='{col}'><title>{v:.4f}</title></circle>")
    return _save(path, _svg(W, H, body, title), df)


def roc(path, curves: dict[str, tuple[np.ndarray, np.ndarray, float]], title: str):
    """curves: name → (fpr, tpr, auc)."""
    W, H = 480, 480
    x = _scale(0, 1, 60, W - 30)
    y = _scale(0, 1, H - 50, 40)
    body = [f"<rect x='60' y='40' width='{W - 90}' height='{H - 90}' fill='none' stroke='#333'/>",
            f"<line x1='{x(0)}' y1='{y(0)}' x2='{x(1)}' y2='{y(1)}' stroke='#aaa' stroke-dasharray='4 3'/>",
            f"<text x='{W / 2}' y='{H - 15}' font-size='12' text-anchor='middle'>FPR</text>",
            f"<text x='18' y='{H / 2}' font-size='12' transform='rotate(-90 18 {H / 2})' text-anchor='middle'>TPR</text>"]
    rows = []
    for k, (name, (fpr, tpr, auc)) in enumerate(curves.items()):
        col = PALETTE[k % len(PALETTE)]
        step = max(1, len(fpr) // 400)
        pts = " ".join(f"{x(a):.1f},{y(b):.1f}" for a, b in zip(fpr[::step], tpr[::step]))
        body.append(f"<polyline fill='none' stroke='{col}' stroke-width='2' points='{pts}'/>")
        body.append(f"<text x='{W - 40}' y='{H - 70 - 18 * k}' font-size='12' text-anchor='end' fill='{col}'>"
                    f"{iso(f'{name} AUC = {auc:.3f}')}</text>")
        rows += [{"curve": name, "fpr": a, "tpr": b} for a, b in zip(fpr[::step], tpr[::step])]
    return _save(path, _svg(W, H, body, title), pd.DataFrame(rows))


def roc_points(y: np.ndarray, s: np.ndarray):
    order = np.argsort(-s, kind="stable")
    ys = np.asarray(y, dtype=bool)[order]
    tp = np.r_[0, np.cumsum(ys)] / max(ys.sum(), 1)
    fp = np.r_[0, np.cumsum(~ys)] / max((~ys).sum(), 1)
    return fp, tp


def bars(path, rows: list[dict], title: str, ylabel=""):
    """rows: {group, series, mean, lo, hi} — grouped vertical bars with error bars."""
    df = pd.DataFrame(rows)
    groups = list(dict.fromkeys(df["group"]))
    series = list(dict.fromkeys(df["series"]))
    vals = np.r_[df["mean"].to_numpy(dtype=float), df["lo"].to_numpy(dtype=float), df["hi"].to_numpy(dtype=float), 0.0]
    vals = vals[np.isfinite(vals)]
    W, H = max(520, 120 + 90 * len(groups) * max(len(series), 1)), 400
    y = _scale(min(vals.min(), 0), vals.max() * 1.1 + 1e-9, H - 60, 50)
    bw = 70 / max(len(series), 1)
    body = [f"<line x1='60' y1='{y(0)}' x2='{W - 20}' y2='{y(0)}' stroke='#333'/>",
            f"<text x='18' y='{H / 2}' font-size='12' transform='rotate(-90 18 {H / 2})' text-anchor='middle'>{iso(ylabel)}</text>"]
    for gi, g in enumerate(groups):
        gx = 80 + gi * (90 * max(len(series), 1) + 20)
        body.append(f"<text x='{gx + 35 * len(series)}' y='{H - 35}' font-size='12' text-anchor='middle'>{iso(g)}</text>")
        for si, sname in enumerate(series):
            r = df[(df["group"] == g) & (df["series"] == sname)]
            if r.empty:
                continue
            r = r.iloc[0]
            col = PALETTE[si % len(PALETTE)]
            bx = gx + si * (bw + 8)
            top, base = y(max(r["mean"], 0)), y(min(r["mean"], 0))
            body.append(f"<rect x='{bx}' y='{top}' width='{bw}' height='{max(base - top, 1)}' fill='{col}' fill-opacity='0.8'/>")
            a, b = _finite(r["lo"], vals.min()), _finite(r["hi"], vals.max())
            cx = bx + bw / 2
            body.append(f"<line x1='{cx}' y1='{y(a)}' x2='{cx}' y2='{y(b)}' stroke='#222'/>"
                        f"<line x1='{cx - 5}' y1='{y(a)}' x2='{cx + 5}' y2='{y(a)}' stroke='#222'/>"
                        f"<line x1='{cx - 5}' y1='{y(b)}' x2='{cx + 5}' y2='{y(b)}' stroke='#222'/>")
    for si, sname in enumerate(series):
        body.append(f"<text x='{W - 30}' y='{50 + 18 * si}' font-size='12' text-anchor='end' fill='{PALETTE[si % len(PALETTE)]}'>{iso(sname)}</text>")
    return _save(path, _svg(W, H, body, title), df)

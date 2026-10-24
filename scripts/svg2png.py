#!/usr/bin/env python3
"""Rasterize SVG or HTML files to PNG with the preinstalled Playwright/Chromium.

No CDN access is available in this environment, so diagrams and charts are
authored as self-contained SVG (or HTML with inline CSS) and rendered here.

Usage:
  python3 scripts/svg2png.py in.svg [in2.svg ...] [--out-dir DIR] [--scale 2] [--width 1400]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def render(paths: list[Path], out_dir: Path | None, scale: float, width: int) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=scale, viewport={"width": width, "height": 900})
        for src in paths:
            dst = (out_dir or src.parent) / (src.stem + ".png")
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.suffix.lower() == ".svg":
                svg = src.read_text(encoding="utf-8")
                html = f"<!doctype html><html><body style='margin:0;background:#fff;display:inline-block'>{svg}</body></html>"
                page.set_content(html)
                el = page.query_selector("svg")
            else:
                page.goto(src.resolve().as_uri())
                page.wait_for_load_state("networkidle")
                el = page.query_selector("body")
            el.screenshot(path=str(dst))
            print(f"{src} -> {dst}")
        browser.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--width", type=int, default=1400)
    a = ap.parse_args()
    render([Path(x) for x in a.inputs], Path(a.out_dir) if a.out_dir else None, a.scale, a.width)


if __name__ == "__main__":
    main()

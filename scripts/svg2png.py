#!/usr/bin/env python3
"""Rasterize SVG or HTML files to PNG.

Thin wrapper around scripts/svg2png.js (Node Playwright + Chromium are preinstalled
globally; the Python Playwright package is not available in this environment).

Usage:
  python3 scripts/svg2png.py in.svg [in2.svg ...] [--out-dir DIR] [--scale 2] [--width 1400]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    js = Path(__file__).with_name("svg2png.js")
    sys.exit(subprocess.call(["node", str(js), *sys.argv[1:]]))

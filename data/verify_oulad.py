#!/usr/bin/env python3
"""Rebuild the original OULAD studentVle.csv from the mirror's 8 shards and verify MD5 sums.

The mirror re-exported studentVle as studentVle_0..7.csv with an unnamed index
column. The original OULAD files quote every field and use CRLF line endings;
reproducing that byte-for-byte lets us compare against the published MD5 sums
in data/oulad_md5_reference.txt (collected from an independent mirror).
"""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent / "raw" / "oulad"
REF = Path(__file__).resolve().parent / "oulad_md5_reference.txt"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rebuild_student_vle() -> Path:
    out = RAW / "studentVle.csv"
    shards = sorted(RAW.glob("studentVle_*.csv"), key=lambda p: int(p.stem.split("_")[1]))
    if not shards:
        sys.exit("no studentVle_*.csv shards found")
    frames = [pd.read_csv(s, index_col=0, dtype=str) for s in shards]
    df = pd.concat(frames, ignore_index=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        w.writerow(df.columns)
        w.writerows(df.itertuples(index=False, name=None))
    print(f"rebuilt {out.name}: {len(df):,} rows (published: 10,655,280)")
    return out


def main() -> None:
    rebuild_student_vle()
    refs: dict[str, str] = {}
    if REF.exists():
        for line in REF.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                refs[Path(parts[-1]).name] = parts[0].lower()
    ok = True
    for name in ["assessments.csv", "courses.csv", "studentAssessment.csv", "studentInfo.csv",
                 "studentRegistration.csv", "studentVle.csv", "vle.csv"]:
        p = RAW / name
        if not p.exists():
            print(f"MISSING  {name}"); ok = False; continue
        h = md5(p)
        exp = refs.get(name)
        status = "OK " if exp == h else ("??" if exp is None else "BAD")
        if status == "BAD":
            ok = False
        print(f"{status}  {name:26s} {h}  expected={exp or 'n/a'}")
    print("integrity:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

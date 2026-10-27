#!/usr/bin/env python3
"""Verify that every verbatim quote cited by the committee exists in the repository text.

Quotes are taken from the last cell of each table row in the given markdown files
(the "الاقتباس الحرفي"/"الشاهد" column) and from any «...» span inside those cells.
Usage: check_quotes.py REPO FILE.md [FILE.md ...]
"""
import re
import sys
import unicodedata
from pathlib import Path

DIAC = re.compile(r"[ً-ْـ]")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = DIAC.sub("", s)
    s = s.replace("**", "").replace("`", "").replace("\\", "")
    s = re.sub(r"[«»\"“”]", "", s)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def corpus(repo: Path) -> str:
    parts = []
    for pat in ("docs/**/*.md", "docs/**/*.txt", "deliverables/**/*.md", "results/**/*.md", "results/**/*.csv",
                "src/**/*.py", "src/**/*.md", "scripts/**/*.py", "scripts/**/*.md", "*.md"):
        for p in repo.glob(pat):
            if "docs/defense" in str(p) and (p.name.startswith(("r1-", "r2-", "r3-", "03-")) or "minutes" in p.name):
                continue   # committee files and the minutes are not evidence for themselves
            try:
                parts.append(norm(p.read_text(encoding="utf-8")))
            except Exception:
                pass
    return "\n".join(parts)


def quotes(md: str):
    evid = False          # current table's last column holds evidence quotes
    prev_table = False
    for line in md.splitlines():
        if not line.startswith("|"):
            prev_table = False
            continue
        if set(line.replace("|", "").strip()) <= set("-: "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not prev_table:                      # header row of a new table
            prev_table = True
            cols = [i for i, c in enumerate(cells) if "اقتباس" in c] or \
                [i for i, c in enumerate(cells) if any(k in c for k in ("الشاهد", "شاهد"))]
            evid = bool(cols)
            col = cols[-1] if cols else -1
            ncols = len(cells)
            continue
        if not evid or len(cells) < 3:
            continue
        # a row with an extra cell split the evidence column in two (place | quote): the quote is last
        cell = cells[-1] if len(cells) > ncols or col >= len(cells) else cells[col]
        if not re.search(r"«[^»]{8,}»", cell) and cell.startswith("`") and ": " in cell:
            cell = cell.split(": ", 1)[1]          # "`file`، section: quote" form
        inner = re.findall(r"«([^»]{8,})»", cell)
        for q in inner or [cell]:
            q = q.strip().strip(".").strip()
            if len(norm(q)) >= 12 and not q.startswith(("الاقتباس", "الشاهد")):
                yield q


def main():
    repo = Path(sys.argv[1])
    text = corpus(repo)
    bad = total = 0
    for f in sys.argv[2:]:
        for q in quotes(Path(f).read_text(encoding="utf-8")):
            total += 1
            nq = norm(q)
            # allow ellipsis-split quotes: every fragment must exist
            frags = [x.strip() for x in re.split(r"\.\.\.|…", nq) if len(x.strip()) >= 8]
            if not frags or not all(fr in text for fr in frags):
                bad += 1
                print(f"MISSING [{Path(f).name}]: {q[:140]}")
    print(f"checked={total} missing={bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

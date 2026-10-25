#!/usr/bin/env python3
"""Insert the generated tables/figures into ch5 section 5-8 and write appendix D.

Run after make_tables.py:  python3 scripts/thesis/assemble.py
Reads templates/sec58_template.md and templates/appD_template.md, and the tables in
deliverables/06-final-thesis/tables/; writes docs/working/06-thesis/ch5-implementation-results.md
(section 5-8 only, between its heading and section 5-9) and appendix-D-confirmatory-details.md.
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TPL = os.path.join(HERE, "templates")
OUT = os.path.join(ROOT, "deliverables", "06-final-thesis", "tables")
THESIS = os.path.join(ROOT, "docs", "working", "06-thesis")

figs = {}
for block in open(os.path.join(OUT, "figures.txt"), encoding="utf-8").read().split("<!--FIG:")[1:]:
    name, body = block.split("-->", 1)
    figs[name] = body.strip()

def fill(text):
    def rep(m):
        key = m.group(1)
        if key.startswith("FIG:"):
            return figs[key[4:]]
        return open(os.path.join(OUT, key + ".md"), encoding="utf-8").read().strip()
    out = re.sub(r"\{\{([^}]+)\}\}", rep, text)
    assert "{{" not in out
    return out

sec = fill(open(os.path.join(TPL, "sec58_template.md"), encoding="utf-8").read())
p = os.path.join(THESIS, "ch5-implementation-results.md")
ch = open(p, encoding="utf-8").read()
a = ch.index("## 5-8 النتائج التأكيدية على عروض 2014")
b = ch.index("## 5-9 خلاصة الفصل")
ch = ch[:a] + sec.rstrip() + "\n\n" + ch[b:]
open(p, "w", encoding="utf-8").write(ch)

app = fill(open(os.path.join(TPL, "appD_template.md"), encoding="utf-8").read())
open(os.path.join(THESIS, "appendix-D-confirmatory-details.md"), "w", encoding="utf-8").write(app)
print("ok")

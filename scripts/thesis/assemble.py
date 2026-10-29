#!/usr/bin/env python3
"""Insert the generated tables/figures into ch5 sections 5-6-3 and 5-8, the NFR-01 status cell, and write appendix D.

Run after make_tables.py:  python3 scripts/thesis/assemble.py
Reads templates/sec58_template.md, templates/appD_template.md, templates/sec563_template.md and
templates/nfr01_status_template.md, and the tables and values in deliverables/06-final-thesis/tables/; writes
docs/working/06-thesis/ch5-implementation-results.md (section 5-6-3 between its heading and section 5-7, and
section 5-8 between its heading and section 5-9), the status cell of the NFR-01 row in appendix-C-requirements.md,
and appendix-D-confirmatory-details.md. {{name}} is a table file, {{FIG:name}} a figure block, and {{v:key}} a value
from serving_bench_values.json (results/serving_bench/, item ت-5).
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TPL = os.path.join(HERE, "templates")
OUT = os.path.join(ROOT, "deliverables", "06-final-thesis", "tables")
THESIS = os.path.join(ROOT, "docs", "working", "06-thesis")

figs = {}
for block in open(os.path.join(OUT, "figures.txt"), encoding="utf-8").read().split("<!--FIG:")[1:]:
    name, body = block.split("-->", 1)
    figs[name] = body.strip()

VALS = json.load(open(os.path.join(OUT, "serving_bench_values.json"), encoding="utf-8"))

def fill(text):
    def rep(m):
        key = m.group(1)
        if key.startswith("FIG:"):
            return figs[key[4:]]
        if key.startswith("v:"):
            return str(VALS[key[2:]])
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
sec = fill(open(os.path.join(TPL, "sec563_template.md"), encoding="utf-8").read())
a = ch.index("### 5-6-3 الأداء المقاس")
b = ch.index("## 5-7 نتائج التطوير على عروض 2013")
assert a < b and ch.count("### 5-6-3 الأداء المقاس") == 1
ch = ch[:a] + sec.rstrip() + "\n\n" + ch[b:]
open(p, "w", encoding="utf-8").write(ch)

# NFR-01 status cell (appendix C, table of non-functional requirements): the last cell of its row
status = fill(open(os.path.join(TPL, "nfr01_status_template.md"), encoding="utf-8").read()).strip()
assert "|" not in status and "\n" not in status
p = os.path.join(THESIS, "appendix-C-requirements.md")
lines = open(p, encoding="utf-8").read().split("\n")
hits = [i for i, l in enumerate(lines) if l.startswith("| NFR-01 | الأداء |")]
assert len(hits) == 1, hits
cells = lines[hits[0]].split(" | ")
assert len(cells) == 6 and cells[-1].endswith(" |"), cells[:2]
cells[-1] = status + " |"
lines[hits[0]] = " | ".join(cells)
open(p, "w", encoding="utf-8").write("\n".join(lines))

app = fill(open(os.path.join(TPL, "appD_template.md"), encoding="utf-8").read())
open(os.path.join(THESIS, "appendix-D-confirmatory-details.md"), "w", encoding="utf-8").write(app)
print("ok")

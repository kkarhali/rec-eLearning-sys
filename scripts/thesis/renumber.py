#!/usr/bin/env python3
"""Renumber IEEE references by order of first appearance, and check figure/table numbering.

Default is a dry run that only reports. --apply writes the changes.

References
  * order of first appearance over: front matter, chapters 1-7, appendices A-D (references.md and
    README.md are not scanned); in appendix A the "#" column of its tables also counts as a citation;
  * rewrites every [n] and [a]-[b] in those files, in docs/working/07-presentation.json and in the
    templates of scripts/thesis/templates/ (except ch6_freeze03.md, the recorded text, which
    build_ch6.py renumbers at build time from the stored map);
  * relabels and reorders references.md, rewrites its introductory paragraph, re-sorts the rows of
    the "#" tables in appendix A;
  * stores the cumulative map original-unified-number -> thesis-number in
    deliverables/06-final-thesis/refs_renumber_map.csv.
  Mandatory checks (exit code 1 on failure): every citation has an entry, every entry is cited,
  numbers are consecutive 1..N after renumbering, every entry has authors, a quoted title, a year
  and a venue/publisher/URL.

Figures and tables
  * every caption (tables: "**جدول X-Y...**"; figures: "![الشكل X-Y: ...](...)") is numbered in order
    of appearance within its chapter, mentioned in the text before it appears, and has a source;
  * with --apply, out-of-order figure/table numbers are renumbered in all thesis files, the
    templates, make_tables.py (figure numbers) and the presentation JSON.

Usage:  python3 scripts/thesis/renumber.py [--root DIR] [--apply]
"""
import argparse, csv, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from refmap import CITE_RE, MAP_REL, apply_citations, cited_numbers, load_map

ap = argparse.ArgumentParser()
ap.add_argument("--root", default=os.path.abspath(os.path.join(HERE, "..", "..")))
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()
ROOT = args.root
TH = os.path.join(ROOT, "docs", "working", "06-thesis")
ORDER = ["00-front-matter.md", "ch1-introduction.md", "ch2-background-literature.md", "ch3-methodology.md",
         "ch4-analysis-design.md", "ch5-implementation-results.md", "ch6-discussion.md", "ch7-conclusion.md",
         "appendix-A-comparison-matrix.md", "appendix-B-numeric-examples.md", "appendix-C-requirements.md",
         "appendix-D-confirmatory-details.md"]
APPA = "appendix-A-comparison-matrix.md"
PRES = os.path.join(ROOT, "docs", "working", "07-presentation.json")
TPL = os.path.join(ROOT, "scripts", "thesis", "templates")
MAKE = os.path.join(ROOT, "scripts", "thesis", "make_tables.py")
REFS = os.path.join(TH, "references.md")
errors, warnings = [], []


def read(p):
    return open(p, encoding="utf-8").read()


def write(p, s):
    if args.apply:
        open(p, "w", encoding="utf-8").write(s)


texts = {f: read(os.path.join(TH, f)) for f in ORDER}

# ------------------------------------------------------------------ appendix A "#" tables
def hash_tables(text):
    """Yield (header_line_index, [row_line_indices]) for markdown tables whose first header cell is '#'."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if re.match(r"^\|\s*#\s*\|", lines[i]) and i + 1 < len(lines) and lines[i + 1].startswith("|-"):
            rows, j = [], i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append(j)
                j += 1
            yield i, rows
            i = j
        else:
            i += 1


def first_cell_num(line):
    m = re.match(r"^\|\s*\[?(\d{1,3})\]?\s*\|", line)
    return int(m.group(1)) if m else None


def appendix_a_numbers(text):
    lines = text.split("\n")
    out = []
    for _, rows in hash_tables(text):
        for r in rows:
            n = first_cell_num(lines[r])
            if n is not None:
                out.append(n)
    return out

# ------------------------------------------------------------------ references.md
refs_text = read(REFS)
entry_re = re.compile(r"^\[(\d{1,3})\] (.+)$", re.M)
entries = {int(m.group(1)): m.group(2) for m in entry_re.finditer(refs_text)}

# ------------------------------------------------------------------ first appearance
order, first_file = [], {}
for f in ORDER:
    t = texts[f]
    seq = cited_numbers(t)
    if f == APPA:
        # bracket citations and '#' cells, in document order
        seq = []
        lines = t.split("\n")
        hash_rows = {r for _, rows in hash_tables(t) for r in rows}
        for k, line in enumerate(lines):
            if k in hash_rows:
                n = first_cell_num(line)
                rest = line
                if n is not None:
                    seq.append(n)
                    rest = re.sub(r"^\|\s*\[?\d{1,3}\]?\s*\|", "|", line)
                seq.extend(cited_numbers(rest))
            else:
                seq.extend(cited_numbers(line))
    for n in seq:
        if n not in first_file:
            first_file[n] = f
            order.append(n)

cited = set(order)
missing_entry = sorted(cited - set(entries))
uncited = sorted(set(entries) - cited)
if missing_entry:
    errors.append(f"citations without an entry in references.md: {missing_entry}")
if uncited:
    errors.append(f"entries never cited in the thesis: {uncited}")

mapping = {old: i + 1 for i, old in enumerate(order)}
nxt = len(mapping) + 1
for old in sorted(set(entries) - cited):  # keep them, at the end, so the run can still be inspected
    mapping[old] = nxt
    nxt += 1
if sorted(mapping.values()) != list(range(1, len(mapping) + 1)):
    errors.append("new numbers are not consecutive")

# IEEE completeness
def ieee_problems(e):
    p = []
    if not re.match(r"^(?:[A-Z]\.|[A-Z][\w&.-]+[ ,])", e):
        p.append("authors")
    if not re.search(r"[\"“].+?[,.]?[\"”]", e):
        p.append("quoted title")
    if not re.search(r"\b(19|20)\d{2}\b", e):
        p.append("year")
    if not re.search(r"\*[^*]+\*|\[Online\]|Available:|https?://|Press|Publishing|Springer|Elsevier|Wiley|ACM|IEEE|MIT", e):
        p.append("venue/publisher")
    return p
for n, e in sorted(entries.items()):
    pr = ieee_problems(e)
    if pr:
        errors.append(f"IEEE entry [{n}] incomplete: missing {', '.join(pr)}")

# ------------------------------------------------------------------ figures and tables
CAP_T = re.compile(r"^\*\*جدول ([0-9ء-ي]+)-(\d+)((?:-[ء-ي]+)?)[:：]\s*(.*)\*\*\s*$")
CAP_F = re.compile(r"^!\[الشكل ([0-9ء-ي]+)-(\d+)[:：]\s*([^\]]*)\]\(([^)]+)\)")
SPAN_T = re.compile(r"(الجدول|الجدولان|الجدولين|الجداول|جدول|للجدول|بالجدول)\s+((?:[0-9ء-ي]+-\d+(?:-[ء-ي]+)?)(?:\s*(?:و|،|–|إلى)\s*[0-9ء-ي]+-\d+(?:-[ء-ي]+)?)*)")
SPAN_F = re.compile(r"(الشكل|الشكلان|الشكلين|الأشكال|للشكل|بالشكل)\s+((?:[0-9ء-ي]+-\d+)(?:\s*(?:و|،|–|إلى)\s*[0-9ء-ي]+-\d+)*)")
SOURCE_HINTS = ("المصدر", "إعداد الباحث", "مولَّد من", "مولّد من", "(مقفل)", "الطور الثاني", "أُعيد رسمه", "لقطة", "منقولة", "مقتبس", "بتصرف")

renum = {"T": {}, "F": {}}  # kind -> {old_label: new_label}
for f in ORDER:
    t = texts[f]
    lines = t.split("\n")
    seen = {"T": [], "F": []}
    for k, line in enumerate(lines):
        mt, mf = CAP_T.match(line), CAP_F.match(line)
        if not (mt or mf):
            continue
        kind = "T" if mt else "F"
        m = mt or mf
        ch, num = m.group(1), int(m.group(2))
        suffix = mt.group(3) if mt else ""
        label = f"{ch}-{num}{suffix}"
        main = f"{ch}-{num}"
        if main not in seen[kind]:
            seen[kind].append(main)
        # source
        if kind == "T":
            title = mt.group(4)
            has_src = any(h in title for h in SOURCE_HINTS)
        else:
            nxt_lines = "\n".join(lines[k:k + 4])
            has_src = any(h in nxt_lines for h in SOURCE_HINTS)
        if not has_src:
            warnings.append(f"{f}: {'جدول' if kind == 'T' else 'الشكل'} {label} has no stated source")
        # mentioned before
        before = "\n".join(lines[:k])
        span = SPAN_T if kind == "T" else SPAN_F
        found = False
        for sm in span.finditer(before):
            labels = re.findall(r"[0-9ء-ي]+-\d+(?:-[ء-ي]+)?", sm.group(2))
            if label in labels or (kind == "T" and any(l == main for l in labels)):
                found = True
                break
        if not found:
            warnings.append(f"{f}: {'جدول' if kind == 'T' else 'الشكل'} {label} is not mentioned in the text before it appears")
    # order of main numbers per chapter prefix
    for kind in ("T", "F"):
        by_ch = {}
        for main in seen[kind]:
            ch, n = main.split("-")
            by_ch.setdefault(ch, []).append(int(n))
        for ch, nums in by_ch.items():
            if nums != sorted(nums):
                expected = sorted(nums)
                for old, new in zip(nums, expected):
                    if old != new:
                        renum[kind][f"{ch}-{old}"] = f"{ch}-{new}"
                errors.append(f"{f}: {'tables' if kind == 'T' else 'figures'} of chapter {ch} out of order: {nums}")
            if nums and nums[0] != 1 and ch.isdigit():
                warnings.append(f"{f}: {'tables' if kind == 'T' else 'figures'} of chapter {ch} start at {nums[0]}")


def relabel(text, kind, mp):
    if not mp:
        return text
    span = SPAN_T if kind == "T" else SPAN_F
    def rep_span(sm):
        def rep_label(lm):
            lab = lm.group(1)
            return mp.get(lab, lab) + (lm.group(2) or "")
        inner = re.sub(r"([0-9ء-ي]+-\d+)((?:-[ء-ي]+)?)", rep_label, sm.group(2))
        return sm.group(1) + " " + inner
    return span.sub(rep_span, text)

# ------------------------------------------------------------------ report
print(f"references: {len(entries)} entries, {len(cited)} cited; first-appearance order starts {order[:12]}")
moved = sum(1 for o, n in mapping.items() if o != n)
print(f"references renumbered: {moved} of {len(mapping)} change number")
for kind in ("F", "T"):
    if renum[kind]:
        print(("figures" if kind == "F" else "tables") + " to renumber: " + ", ".join(f"{a}→{b}" for a, b in renum[kind].items()))
for w in warnings:
    print("WARN", w)
for e in errors:
    print("ERROR", e)

# ------------------------------------------------------------------ apply
if args.apply:
    def transform(s):
        s = apply_citations(s, mapping)
        s = relabel(s, "F", renum["F"])
        s = relabel(s, "T", renum["T"])
        return s
    for f in ORDER:
        s = transform(texts[f])
        if f == APPA:
            lines = s.split("\n")
            for _, rows in hash_tables(s):
                vals = [lines[r] for r in rows]
                new_vals = []
                for v in vals:
                    n = first_cell_num(v)
                    if n is not None:
                        v = re.sub(r"^(\|\s*\[?)(\d{1,3})(\]?\s*\|)", lambda m: f"{m.group(1)}{mapping[int(m.group(2))]}{m.group(3)}", v, count=1)
                    new_vals.append(v)
                new_vals.sort(key=lambda v: first_cell_num(v) if first_cell_num(v) is not None else 10**6)
                for r, v in zip(rows, new_vals):
                    lines[r] = v
            s = "\n".join(lines)
        write(os.path.join(TH, f), s)
    # references.md: relabel, reorder, rewrite intro
    head = refs_text[:refs_text.index("\n[")].split("\n")
    title = head[0]
    intro = ("تتبع القائمة نمط IEEE الرقمي، والمراجع مرقّمة بترتيب ظهورها الأول في متن الرسالة وملاحقها. "
             "ولا تتضمن القائمة إلا البيانات البيبليوغرافية المؤكَّدة، أما ملاحظات التحقق فمكانها الملحق أ (الجدول أ-4).")
    body = "\n\n".join(f"[{mapping[o]}] {entries[o]}" for o in sorted(entries, key=lambda o: mapping[o]))
    write(REFS, f"{title}\n\n{intro}\n\n{body}\n")
    # templates (not the recorded ch6 text) and make_tables.py figure numbers
    for name in os.listdir(TPL):
        if name.endswith(".md") and name != "ch6_freeze03.md":
            p = os.path.join(TPL, name)
            write(p, transform(read(p)))
    if renum["F"]:
        s = read(MAKE)
        s = re.sub(r'(\("fig\w+", ")(\d+-\d+)(")', lambda m: m.group(1) + renum["F"].get(m.group(2), m.group(2)) + m.group(3), s)
        write(MAKE, s)
    if os.path.exists(PRES):
        write(PRES, transform(read(PRES)))
    # cumulative map: original unified number -> new thesis number
    prev = load_map(ROOT)
    os.makedirs(os.path.dirname(os.path.join(ROOT, MAP_REL)), exist_ok=True)
    with open(os.path.join(ROOT, MAP_REL), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["original", "new", "first_file", "entry_start"])
        if prev is None:
            pairs = [(o, mapping[o]) for o in sorted(mapping)]
            cur_of_orig = {o: o for o in mapping}
        else:
            pairs = [(orig, mapping[cur]) for orig, cur in sorted(prev.items())]
            cur_of_orig = dict(prev)
        for orig, new in pairs:
            cur = cur_of_orig[orig]
            w.writerow([orig, new, first_file.get(cur, "(uncited)"), entries[cur][:60]])
    print("applied; map written to", MAP_REL)

sys.exit(1 if errors else 0)

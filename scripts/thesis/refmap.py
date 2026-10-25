"""Shared helpers for renumbering IEEE citations [n] and figure/table labels.

Used by renumber.py (which writes the map) and build_ch6.py (which applies the stored map to the
recorded freeze-03 text at build time, so the recorded paragraphs keep their wording and only the
citation numbers follow the thesis order).
"""
import csv, os, re

CITE_RE = re.compile(r"\[(\d{1,3})\](?:\s*[–-]\s*\[(\d{1,3})\])?")
MAP_REL = os.path.join("deliverables", "06-final-thesis", "refs_renumber_map.csv")


def render(nums):
    """Render a set of citation numbers ascending; runs of 3+ consecutive numbers become [a]–[b]."""
    nums = sorted(set(nums))
    parts, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        if j - i >= 2:
            parts.append(f"[{nums[i]}]–[{nums[j]}]")
        else:
            parts.extend(f"[{n}]" for n in nums[i:j + 1])
        i = j + 1
    return "، ".join(parts)


def apply_citations(text, mapping):
    """Replace every [n] and [a]–[b] using mapping (old -> new). Unknown numbers raise KeyError."""
    def rep(m):
        a = int(m.group(1))
        if m.group(2) is None:
            return f"[{mapping[a]}]"
        b = int(m.group(2))
        return render(mapping[x] for x in range(a, b + 1))
    return CITE_RE.sub(rep, text)


def cited_numbers(text):
    """Citation numbers in order of appearance (ranges expanded ascending)."""
    out = []
    for m in CITE_RE.finditer(text):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        out.extend(range(a, b + 1))
    return out


def load_map(root):
    """original unified number -> current thesis number, or None if no map was written yet."""
    p = os.path.join(root, MAP_REL)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return {int(r["original"]): int(r["new"]) for r in csv.DictReader(f)}

#!/usr/bin/env python3
"""دليل البروفة لعرض المناقشة: Markdown مجمَّع ثم Word عربي.

يجمع لكل شريحة: نصها كما في ملف المحتوى، ونص الإلقاء المعتمد (ملاحظات المتحدث)، وطبقة «شرح البروفة»
كاملة بما فيها «مصادر التحقق». ويضع قبل الشرائح الأقسام التمهيدية من ملف شرح البروفة، وبعدها الأقسام الختامية.

الاستعمال:
    python3 scripts/build_rehearsal_guide.py                 # → deliverables/08-defense/دليل-البروفة.docx
    python3 scripts/build_rehearsal_guide.py --md-only OUT.md
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/working/07-presentation.json"
OUT_DOCX = ROOT / "deliverables/08-defense/دليل-البروفة.docx"
SLIDE_RE = re.compile(r"^(شريحة (\d+)|شريحة احتياطية (\S+)) — (.*)$")


def split_sections(text: str):
    """يقسم ملف markdown على عناوين المستوى الثاني ويعيد (المقدمة، [(العنوان، الجسم)])."""
    parts = re.split(r"\n## ", "\n" + text)
    head = parts[0].strip("\n")
    return head, [(p.split("\n", 1)[0].strip(), p.split("\n", 1)[1] if "\n" in p else "") for p in parts[1:]]


def slide_key(title: str):
    m = SLIDE_RE.match(title)
    if not m:
        return None
    return int(m.group(2)) if m.group(2) else m.group(3)


def dedent2(block: str) -> str:
    return "\n".join(ln[2:] if ln.startswith("  ") else ln for ln in block.split("\n"))


def content_slides(content_md: Path) -> dict:
    _, secs = split_sections(content_md.read_text(encoding="utf-8"))
    out = {}
    for title, body in secs:
        key = slide_key(title)
        if key is None:
            continue
        stext = re.search(r"\*\*نص الشريحة:\*\*\n(.*?)\n- \*\*الدليل", body, re.S)
        note = re.search(r"\*\*ملاحظات المتحدث:\*\*\n(.*?)(?:\n\n---|\n\n## |\Z)", body, re.S)
        out[key] = (title, dedent2(stext.group(1)).strip() if stext else "", note.group(1).strip() if note else "")
    return out


def pandoc_lists(md: str) -> str:
    """يهيّئ القوائم لـpandoc: سطر فارغ قبل قائمة تلي فقرة، وسطر الجواب «  **ج:**» فقرة ثانية داخل بند السؤال
    (GitHub يقبل القائمة بلا سطر فارغ، وpandoc يدمجها في الفقرة السابقة)."""
    out = []
    for ln in md.split("\n"):
        prev = out[-1] if out else ""
        is_item = ln.startswith("- ")
        if is_item and prev.strip() and not (prev.startswith("- ") or prev.startswith("  ")):
            out.append("")
        if ln.startswith("  **ج:**") and prev.strip():
            out.append("")
        out.append(ln)
    return "\n".join(out)


def demote(md: str) -> str:
    """يخفض عناوين الجسم درجة واحدة كي تبقى تحت عنوان الشريحة."""
    return re.sub(r"(?m)^(#{1,5}) ", lambda m: "#" + m.group(1) + " ", md)


def build_md(content_md: Path, prep_md: Path) -> str:
    slides = content_slides(content_md)
    head, secs = split_sections(prep_md.read_text(encoding="utf-8"))
    head = re.sub(r"(?m)^# .*\n?", "", head).strip()
    before, after, prep = [], [], {}
    seen_slide = False
    for title, body in secs:
        key = slide_key(title)
        if key is not None:
            seen_slide = True
            prep[key] = body.strip()
        elif not seen_slide:
            before.append((title, body.strip()))
        else:
            after.append((title, body.strip()))
    missing = [k for k in slides if k not in prep]
    if missing:
        raise SystemExit(f"شرائح بلا شرح بروفة: {missing}")
    out = []
    if head:
        out.append(head)
    for title, body in before:
        out.append(f"# {title}\n\n{demote(body)}")
    order = sorted(k for k in slides if isinstance(k, int)) + [k for k in slides if not isinstance(k, int)]
    for key in order:
        title, stext, note = slides[key]
        out.append(
            f"# {title}\n\n## ما على الشريحة\n\n{stext}\n\n## نص الإلقاء المعتمد\n\n{note}\n\n"
            f"## شرح البروفة\n\n{demote(demote(prep[key]))}"
        )
    for title, body in after:
        out.append(f"# {title}\n\n{demote(body)}")
    return pandoc_lists("\n\n".join(out).rstrip()) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--md-only", help="اكتب Markdown المجمَّع إلى هذا المسار دون Word")
    ap.add_argument("--out", default=str(OUT_DOCX))
    a = ap.parse_args(argv)
    meta = json.loads(SPEC.read_text(encoding="utf-8"))["meta"]
    md = build_md(ROOT / meta["content_source"], ROOT / meta["prep_source"])
    if a.md_only:
        Path(a.md_only).write_text(md, encoding="utf-8")
        print(f"تم: {a.md_only}")
        return 0
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "rehearsal-guide.md"
        src.write_text(md, encoding="utf-8")
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_docx.py"), a.out, str(src),
             "--title", "دليل البروفة لعرض المناقشة",
             "--subtitle", "شرح مبسّط لكل شريحة: المفاهيم والأرقام والقرارات والصلة بالدراسة المرجعية والأسئلة المتوقعة",
             "--author", meta["author"], "--supervisor", meta["supervisor"]],
            check=True,
        )
    print(f"تم: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

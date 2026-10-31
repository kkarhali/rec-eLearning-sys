set -e
# محضر الجلسة الثالثة: ملخص المحضر ثم ملفات الجلسة بترتيبها، بعناوين مخفَّضة درجة واحدة، ثم Word.
cd "$(dirname "$0")/.."
S=docs/defense/session3
FULL="$S/minutes-full.md"
python3 - "$S" "$FULL" <<'PY'
import sys, re, pathlib
s, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
order = ["00-session.md", "01-researcher-presentation.md", "r1-alomar.md", "r1-alkanj.md", "r1-abutarab.md",
         "02-researcher-answers.md", "r2-alomar.md", "r2-alkanj.md", "r2-abutarab.md", "r2-verdict.md"]
parts = [(s / "03-minutes-summary.md").read_text(encoding="utf-8").rstrip() + "\n"]
for name in order:
    text = (s / name).read_text(encoding="utf-8")
    lines, fence = [], False
    for ln in text.splitlines():
        if ln.startswith("```"):
            fence = not fence
        if not fence and re.match(r"^#{1,5} ", ln):
            ln = "#" + ln
        lines.append(ln)
    parts.append("\n".join(lines).rstrip() + "\n")
out.write_text("\n".join(parts), encoding="utf-8")
print(f"{out}: {len(parts)} أجزاء")
PY
OUT="deliverables/08-defense/محضر-الجلسة-الثالثة.docx"
python3 scripts/build_docx.py "$OUT" "$FULL" --title "محضر الجلسة الثالثة للمناقشة التجريبية" --subtitle "نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم" --author "كنان محمد قرحالي" --supervisor "د. باسل الخطيب" | tail -1
python3 - "$OUT" <<'PY'
import sys, inspect; sys.path.insert(0, 'scripts/thesis'); sys.path.insert(0, 'scripts')
import build_thesis_docx as b
src = inspect.getsource(b.fit_tables).replace("min(tl / nbody, 60)", "min(tl / nbody, 160)")
ns = dict(vars(b)); exec(src, ns)
from docx import Document
d = Document(sys.argv[1]); ns['fit_tables'](d); d.save(sys.argv[1]); print('tables fitted')
PY

set -e
cd /home/user/rec-eLearning-sys
OUT="deliverables/08-defense/محضر-الجلسة-الثانية.docx"
python3 scripts/build_docx.py "$OUT" docs/defense/session2/minutes-full.md --title "محضر الجلسة الثانية للمناقشة التجريبية" --subtitle "نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم" --author "كنان محمد قرحالي" --supervisor "د. باسل الخطيب" | tail -1
python3 - "$OUT" <<'PY'
import sys, inspect; sys.path.insert(0, 'scripts/thesis'); sys.path.insert(0, 'scripts')
import build_thesis_docx as b
src = inspect.getsource(b.fit_tables).replace("min(tl / nbody, 60)", "min(tl / nbody, 160)")
ns = dict(vars(b)); exec(src, ns)
from docx import Document
d = Document(sys.argv[1]); ns['fit_tables'](d); d.save(sys.argv[1]); print('tables fitted')
PY

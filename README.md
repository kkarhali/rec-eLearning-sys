# نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم
**A recommendation system for e-learning based on user behavior analysis**

رسالة ماجستير في علوم الوب — الجامعة الافتراضية السورية
الطالب: كنان محمد قرحالي · المشرف: د. باسل الخطيب

## خريطة المستودع

| المسار | المحتوى |
|---|---|
| [`deliverables/`](deliverables/) | **مخرجات مراحل الدراسة (Word / PowerPoint)** مرتّبة بأرقام المراحل |
| `deliverables/00-research-plan/` | خطة البحث الأصلية |
| `deliverables/01-literature-review/` | الدراسة المرجعية (التحقق من المراجع، المقارنة، الفجوة) |
| `deliverables/02-hypotheses-algorithms/` | الفرضيات والخوارزميات وجداول المصطلحات |
| `deliverables/03-analysis-design/` | التحليل والتصميم + `diagrams/` |
| `deliverables/04-code-documentation/` | توثيق الكود البرمجي |
| `deliverables/05-user-guide/` | دليل المستخدم والواجهات |
| `deliverables/06-final-thesis/` | الأطروحة النهائية |
| `deliverables/07-presentation/` | العرض التقديمي للجنة |
| [`src/`](src/) | **الكود البرمجي**: `ml/` (المعالجة والنماذج والتقييم)، `backend/` (API)، `frontend/` (الواجهات) |
| [`data/`](data/) | سكربتات تحميل ومعالجة البيانات وعيّنات |
| [`references/`](references/) | المراجع العلمية (PDF) |
| [`docs/`](docs/) | مسوّدات العمل (`working/`)، محاضر الاجتماعات (`meetings/`)، القرارات (`decisions/`)، ميثاق الفريق (`team/`) |
| [`scripts/`](scripts/) | أدوات البناء: `build_docx.py` (Markdown ← Word RTL)، `svg2png.py` |
| `.claude/skills/` | مهارات الفريق: المشرف الأكاديمي، الزميل المراجع، البحث العميق، ui-ux-pro-max |

## كيف تُبنى وثائق Word
```bash
python3 scripts/build_docx.py deliverables/01-literature-review/الدراسة-المرجعية.docx docs/working/01-literature-review.md --title "الدراسة المرجعية"
```

## تشغيل النظام من الصفر
المتطلبات: Python 3.13 مع `numpy` و`pandas` و`starlette` و`uvicorn` و`pydantic` (النسخ المختبرة: numpy 2.5.3، pandas 3.0.5، starlette 1.7.0، uvicorn 0.54.0، pydantic 2.13.5، anyio 4.15.1؛ لا ملف requirements)، وNode 22 مع `typescript` (الأمر `tsc`) و`playwright` مثبَّتَين عمومياً (`npm root -g`) لبناء الواجهة واللقطات والفحص الحي، واتصال بـGitHub لتحميل البيانات. كل الأوامر من جذر المستودع:
```bash
bash data/download.sh                              # ≈ 45 ث: يحمّل OULAD ويتحقق (يجب أن يطبع «integrity: PASS»، 7 ملفات OK)
python3 -m unittest discover -s src/ml/tests       # 121 اختباراً، ≈ 5 ث
python3 -m src.ml.experiments.build_artifacts      # ≈ 75 ث (أول مرة تقرأ studentVle وتبني data/cache)؛ artifacts/ خارج git
bash src/frontend/build.sh                         # ≈ 4 ث → src/frontend/dist
python3 -m unittest discover -s src/backend/tests -t .   # 52 اختباراً، ≈ 110 ث على نسخة نظيفة (≈ 25–90 ث لاحقاً)
python3 -m src.backend --warm --port 8100          # http://127.0.0.1:8100 ؛ الصفحة الأولى جاهزة فوراً والتسخين الكامل ≈ 60 ث على نسخة نظيفة
CHECK_ONLY=1 NODE_PATH=$(npm root -g) node src/backend/e2e/live-screenshots.js http://127.0.0.1:8100   # فحص حي ≈ 15 ث بلا كتابة لقطات
```
التفاصيل: [`src/ml/README.md`](src/ml/README.md) و[`src/backend/README.md`](src/backend/README.md) و[`src/frontend/README.md`](src/frontend/README.md). ملاحظة: تشغيل `build_artifacts` يُلحق سطراً بـ`results/access_log.jsonl` (سجل قراءات D-47 المتتبَّع في git)، فيظهر الملف معدَّلاً بعدها وهذا متوقَّع.

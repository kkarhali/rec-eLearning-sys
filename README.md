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

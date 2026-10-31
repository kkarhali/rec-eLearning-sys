# مولّد العرض التقديمي

العرض الحالي: 22 شريحة رئيسية + شريحة احتياطية واحدة («أ») = 23 شريحة، بنسبة 16:9 وقالب عربي RTL (D-124).

- **مصدر المحتوى:** `docs/working/07-presentation/deck-content.md`. فيه نص كل شريحة، وحقل «الدليل» لكل ادعاء، وملاحظات المتحدث،
  وخريطة الادعاءات وقائمة الأرقام ومصادرها. أي تعديل يبدأ منه.
- **مصدر البناء:** `docs/working/07-presentation.json` (المسار في `meta.content_source` يشير إلى ملف المحتوى). يُنقل إليه نص الشرائح
  وملاحظاتها حرفياً، ومعه التصميم (النوع والأحجام والأعمدة وسطر المصدر). لا يُعدَّل الـpptx يدوياً.
- **طبقة شرح البروفة:** `docs/working/07-presentation/rehearsal-notes.md` (المسار في `meta.prep_source`). شرح مبسّط لكل شريحة
  (الفكرة في جملة، وجملة جسر اختيارية للجمهور، والمفاهيم ببساطة، ومعنى الأرقام، وسبب القرار، والصلة بالدراسة المرجعية، وأسئلة متوقعة
  بأجوبتها، وتنبيهات للمقدّم، ومصادر التحقق)، وقبلها القصة في دقيقتين والمسرد وخطة البروفة، وبعدها أهم الأسئلة المتوقعة.
  يُلحق المولّد شرح كل شريحة بملاحظاتها بعد نص الإلقاء وفاصل «شرح البروفة»، دون «مصادر التحقق». ويُجمع في دليل Word بالأمر
  `python3 scripts/build_rehearsal_guide.py` (→ `deliverables/08-defense/دليل-البروفة.docx`: نص الشريحة، ونص الإلقاء، والشرح كاملاً).
  قواعد كتابته في `rehearsal/00-brief.md`، ومراجعتاه وقرار المشرف المحاكى في `rehearsal/`.
- **نسخة الوب:** عرض Slides (`deliverables/07-presentation/slides-source/` ونسخة ملفاته). المرجع للإيداع هو الـpptx والـPDF في المستودع.

## إعادة البناء والتحقق

```bash
python3 scripts/build_pptx.py --check     # يبني deliverables/07-presentation/العرض-التقديمي.pptx ثم يطابقه مع deck-content.md
python3 scripts/build_pptx.py --check-only                  # يطابق الملف الموجود دون بناء
python3 scripts/build_pptx.py --spec X.json --out /tmp/x.pptx   # بناء تجريبي
```

- `--check` يتأكد أن كل سطر وكل خلية في «نص الشريحة» موجودة حرفياً في الشريحة المقابلة (بعد حذف رموز الاتجاه والمسافة غير الفاصلة
  وعلامات markdown)، وأن ملاحظات المتحدث مساوية حرفياً لملف المحتوى ثم لطبقة شرح البروفة، وأن عدد الشرائح واحد، وأن لكل شريحة شرحاً.
  ويخرج برمز 1 عند أي اختلاف.
- المتطلبات: `python-pptx 1.0.2` و`lxml` و`Pillow` فقط (لا npm ولا CDN). YAML اختياري (`pyyaml`).
- الخط Arial (لـlatin وcs)، والألوان من رموز واجهة النظام (الأساسي `#0F766E`، الكهرماني `#B45309`).
- كل فقرة تحمل `a:pPr rtl="1" algn="r"`. والأرقام والفواصل داخل جملة عربية تُكتب بين U+202A وU+202C في JSON، ويقوّيها المولّد بعلامات
  LRM فتبقى مرتبة في LibreOffice أيضاً، ويُستحسن وضع مسافة غير فاصلة داخل الفاصل كي لا ينكسر عبر السطور.
- **ملف PDF:** انسخ الـpptx، واستبدل `typeface="Arial"` بـ`typeface="DejaVu Sans"` في ملفات XML داخل النسخة، ثم
  `soffice --headless --convert-to pdf`، وانسخ الناتج إلى `deliverables/07-presentation/العرض-التقديمي.pdf`. وافحص الصفحات المعدّلة
  بـ`pdftoppm -png -r 60`. ويُحفظ في `deliverables/07-presentation/` ملفا العرض وصورة الشريحة 11 `live-03-learner-why-panel.png` فقط.

## ترقيم الشرائح الحالي

| الشريحة | العنوان | النوع |
|---|---|---|
| 1 | العنوان | `title` |
| 2–4 | خصائص الوصول في OULAD، وأثر تعريف الهدف، والسؤال البحثي | `stats`، `table`، `quote` |
| 5–6 | الأدبيات والفجوة، والمسارات المستكشفة | `cards`، `table` |
| 7–9 | المنهجية والتسجيل المسبق، والفرضيات وقاعدة الحكم، والخوارزميات | `flow`، `table`، `cards` |
| 10–11 | آلية التنفيذ، وتطبيق العرض | `flow`، `image` |
| 12–17 | الأحكام (12، من `verdicts.csv`)، وما يعنيه كل حكم، والترتيب، والحداثة، ومصدر مكسب الشخصنة (لاحق)، والمتانة | `table`، `table`، `chart`، `table`، `stats`، `table` |
| 18–20 | هل يوجد مسار أوعد؟، والقيود، والمساهمات | `table`، `two-column`، `cards` |
| 21 | الخلاصة: حصيلة المسارات | `table` |
| 22 | شكراً لكم | `qa` (`variant: closing`) |
| أ | حكم H3 وسؤال نوع النموذج (احتياطية، لاحق) | `table` |

- الشريحة 12: `source.format = "verdicts"` يقرأ `results/conf2014/verdicts.csv` ويلحق نص «غير حاسمة» من العمود `D48_text`.
  ووسم صف H3 يُستبدل بـ«مدحوضة للتفوق» (`source.verdict_override`)، الوسم المسجل للجدول السداسي.
- الأرقام داخل النصوص: رموز `{{H4-a.mean_delta|.4f}}` (من `verdicts.csv`) و`{{h4b[slice=cold_q1].mean|+.4f}}` (من أي CSV في
  `results/conf2014/`) تُستبدل عند البناء.
- مدة الإلقاء: نحو 21.3–25.6 دقيقة (ملاحظات الشرائح الرئيسية 2,558 كلمة بنحو 100–120 كلمة في الدقيقة)، كما في رأس ملف المحتوى.
- لا رموز قرارات (D-xx) على الشرائح ولا في الملاحظات، وكل رقم من الملحق هـ موسوم «لاحق».

## أنواع الشرائح (`type`)

| النوع | الحقول الرئيسية |
|---|---|
| `title` | `title`, `subtitle`, `lines` |
| `section` | `title`, `subtitle` |
| `bullets` | `items` (نص أو `{head,text}`), `callout` |
| `cards` | `items[{n,head,text}]`, `cols`, `lead`, `callout`, `theme: dark` |
| `stats` | `items[{value,label}]`, `caption` |
| `flow` | `rows[{label, steps[{head,text}]}]`, `callout` |
| `timeline` | `cuts`, `window`, `chips` |
| `two-column` | `columns[{heading,items}]` (2–3 أعمدة) |
| `image` | `image` (مسار من جذر المستودع), `crop_bottom`/`crop_top`, `caption`, `items[{head,text}]`, `alt` |
| `table` | `columns`, `rows`, `col_weights`, `caption`, أو `source{file,heading_contains,cols,max_rows}` |
| `chart` | `chart{source|categories+values, sort, highlight, title}`, `items[{value,label}]`, `caption` |
| `quote` | `text`, `by` |
| `qa` | `questions[{q,a[]}]` للاحتياطي؛ `variant: closing` لشريحة الشكر |
| `placeholder` | `panels[{head,text,slot}]`, `callout` |

حقول عامة: `notes` (ملاحظات المتحدث)، `pending` (شريط كهرماني «قيد الاستكمال»)، `badge` (شريط أخضر مزرق).

مخطط الأعمدة أصلي (قابل للتحرير في PowerPoint). عند `chart.source` تُقرأ القيم من جدول markdown في ملف النتائج (عنوان يحوي `heading_contains`، العمود `label_col` والعمود `value_col`، ويؤخذ أول رقم في الخلية)، فتُحدَّث بإعادة البناء دون نسخ يدوي.

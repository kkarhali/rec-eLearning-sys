# مولّد العرض التقديمي

العرض: 21 شريحة رئيسية + 3 شرائح احتياطية للأسئلة المتوقعة = 24 شريحة، بنسبة 16:9 وقالب عربي RTL.

## إعادة البناء

```bash
python3 scripts/build_pptx.py            # يقرأ docs/working/07-presentation.yaml إن وُجد، وإلا .json
python3 scripts/build_pptx.py --spec docs/working/07-presentation.json --out /tmp/x.pptx
```

- الناتج الافتراضي: `deliverables/07-presentation/العرض-التقديمي.pptx` (المسار في `meta.output`).
- المتطلبات: `python-pptx 1.0.2` و`lxml` و`Pillow` فقط (لا npm ولا CDN). YAML اختياري (`pyyaml`).
- المصدر الوحيد للمحتوى: `docs/working/07-presentation.json`. لا يُعدَّل الـpptx يدوياً.
- الخط Arial (لـlatin وcs)، الألوان من رموز واجهة النظام (الأساسي `#0F766E`، الكهرماني `#B45309`).
- كل فقرة تحمل `a:pPr rtl="1" algn="r"`؛ ملاحظات المتحدث لكل شريحة في الحقل `notes`.
- الفحص البصري: `soffice --headless --convert-to pdf` ثم `pdftoppm -jpeg -r 50`. لا تُترك ملفات PDF/صور في `deliverables/`.

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

## ملء شرائح النتائج (بعد التشغيل التأكيدي)

العرض الآن 23 شريحة: 20 رئيسية + 3 احتياطية (21–23). النائبة: 15 (الأحكام + صف H4-ب الاستكشافي) و16 (الأشكال) و17 (المناقشة). وتحتاج مراجعة بعد النتائج: 18 (القيود) و19 (المساهمة 4) وملاحظات 15–20.

1. **15 (أحكام الفرضيات الأربع)**: املأ خلايا `[2014]` (الفرق Δ̄، فاصل 95%، p المصحَّحة، الحكم) من `verdicts.csv`؛ عمود MDE80 مجمَّد ومملوء من `results/dev2013/mde80.md`. صياغة «غير حاسمة» في `caption` هي نص D-48 الحرفي (دون رمز القرار). احذف حقل `pending` عند الاكتمال.
2. **صف H4-ب في الشريحة 15**: استكشافي بلا حكم (`explore_rows`)؛ املأ Δ̄ والفاصل وp غير المصحَّحة فقط.
3. **16 (الأشكال)**: في كل `panels[i]` أضف `"image": "results/conf2014/<الملف>.png"` فيحلّ الشكل محل المكان النائب تلقائياً (PNG فقط؛ SVG يُحوَّل بـ`scripts/svg2png.py`).
4. **17 (المناقشة)** و**19 (المساهمة 4)**: أكمل النص من النتائج؛ وحدّث `notes` للشرائح 15–20.
5. شريحة التجميد (10): قائمة الشروط ثابتة؛ الحالة الحية تُقرأ من `results/frozen/freeze_checklist.md` لا من الشريحة.
6. لا رموز قرارات (D-xx) على الشرائح ولا في الملاحظات؛ لا أرقام من لقطات الشاشة (الشاشتان توضيحيتان).
7. أعد البناء ثم افحص بصرياً، وتأكد من خلوّ الشرائح من `[2014]`:
   `python3 scripts/build_pptx.py && python3 /root/.claude/skills/synced/*/pptx/scripts/slide_text.py deliverables/07-presentation/العرض-التقديمي.pptx | grep -n "\[2014\]"`

## مصادر الأرقام في الشرائح (كلها من الملفات، لا أرقام مختلقة)

- الشريحة 6: `results/dev2013/eda.md` (الأقسام 1 و2 و3 و5) والفصل 3 §3-2-6؛ 32,593 تسجيلاً و22 عرضاً من §3-2-2.
- الشريحة 14: `results/dev2013/summary.md` (الجدول 1 للمخطط، الجدول 5 والقسم «الهجين المجمَّد» لبطاقتي SKNN والهجين)، وصفية على 9 عروض.
- الشرائح 21–23: الفصل 3 §3-5-5 و§3-6-3 والفصل 1 §1-5؛ MDE80 ≈ 0.0525 من `summary.md` (توضيحي).
- الصور: `deliverables/03-analysis-design/diagrams/02-component-architecture.png`، و`deliverables/05-user-guide/screenshots/live-02-learner-desktop.png` (مقصوصة بـ`crop_bottom`) و`live-06-instructor-drawer-desktop.png` (المتعلم FFF_2013J-29769).

## نتائج التأكيد: كيف تُولَّد الشرائح 15 و17 و21

- الشريحة 15: `source.format = "verdicts"` يقرأ `results/conf2014/verdicts.csv` (Δ̄، الفاصل، p بعد هولم، عروض Δ>0، الحكم) ويلحق نص «غير حاسمة» من العمود `D48_text`. **استثناء مسجّل:** وسم صف H3 يُستبدل في خطوة التوليد (`source.verdict_override`) بـ«مدحوضة للتفوق» (قرار المشرف: الوسم المسجل للصف الخامس من الجدول السداسي)، مع حاشية في التعليق تذكر ما يطبعه الملف. بقية الأحكام كما في الملف.
- الأرقام داخل النصوص: رموز `{{H4-a.mean_delta|.4f}}` (من verdicts.csv) و`{{h4b[slice=cold_q1].mean|+.4f}}` (من أي CSV في results/conf2014) تُستبدل عند البناء.
- الشريحة 16: النسخة المشتقة `deliverables/06-final-thesis/figures/derived/fig1_forest.png` (أُعيد رسمها من fig1_forest.csv المقفل)؛ لا يُقصّ أي PNG مقفل. خيارا `crop_*` عامان في السكربت ولا يُستعملان هنا.
- الشريحة 21 (احتياطية): الثانوي والاستكشافي بوسم «ثانوي/استكشافي»، وفيها سطر حدّية H1.

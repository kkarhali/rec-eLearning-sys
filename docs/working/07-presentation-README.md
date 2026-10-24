# مولّد العرض التقديمي

العرض: 19 شريحة رئيسية (15–20 دقيقة) + 3 شرائح احتياطية للأسئلة المتوقعة = 22 شريحة، بنسبة 16:9 وقالب عربي RTL.

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

## ملء شرائح النتائج (الجولة التالية)

الشرائح المعلّمة `pending` مؤقتة: 14 و15 و16، وتحتاج تحديثاً: 17 (القيود، يُراجع بعد النتائج) و18 (البند 4 من المساهمات).

1. **الشريحة 14 (الفرضيات)**: في الجدول املأ عمودي `Δ̄ [فاصل 95%]` و`الحكم` لكل صف من ملف نتائج التأكيد (أحكام الجدولين 3-14 و3-15)، واحذف حقل `pending`. الخلايا التي تبدأ بـ`[` تظهر بخلفية كهرمانية؛ غيّرها إلى نص عادي فتصير بنمط الجدول العادي. يمكن بدلاً من ذلك استعمال `source` لقراءة جدول من ملف النتائج.
2. **الشريحة 15 (الاستئصال والحساسيات)**: غيّر النوع من `placeholder` إلى `chart` (بـ`chart.source` من جدول الاستئصال L0–L3) أو `table` (حساسيات)، أو أبقِ ثلاث لوحات بصور.
3. **الشريحة 16 (المناقشة)**: استبدل `[ تُكتب بعد النتائج ]` في `slot` بجملة قصيرة لكل محور، أو حوّلها إلى `cards`. أبقِ سياسة النتيجة السلبية إن لزم.
4. **الشريحة 18**: أكمل `[يُستكمل بنتائج التأكيد]` في المساهمة 4، وحدّث `notes` للشرائح 14–19 بالأرقام الفعلية.
5. أعد البناء ثم افحص بصرياً (4 شرائح على الأقل) وتأكد من خلوّ النص من `[`:
   `python3 scripts/build_pptx.py && python3 -c "from pptx import Presentation as P;[print(i) for i,s in enumerate(P('deliverables/07-presentation/العرض-التقديمي.pptx').slides,1) for sh in s.shapes if sh.has_text_frame and '[' in sh.text_frame.text]"`

## مصادر الأرقام في الشرائح (كلها من الملفات، لا أرقام مختلقة)

- الشريحة 6: `results/dev2013/eda.md` (الأقسام 1 و2 و3 و5) والفصل 3 §3-2-6؛ 32,593 تسجيلاً و22 عرضاً من §3-2-2.
- الشريحة 13: `results/dev2013/summary.md` (الجدول 1 للمخطط، الجدول 5 والقسم «الهجين المجمَّد» لبطاقتي SKNN والهجين)، وصفية على 9 عروض.
- الشرائح 20–22: الفصل 3 §3-5-5 و§3-6-3 والفصل 1 §1-5؛ MDE80 ≈ 0.0525 من `summary.md` (توضيحي).
- الصور: `deliverables/03-analysis-design/diagrams/02-component-architecture.png`، `deliverables/05-user-guide/screenshots/02-learner-desktop.png` و`04-instructor-desktop.png` (مقصوصة من الأسفل عبر `crop_bottom`).

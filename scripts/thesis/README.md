# scripts/thesis: توليد الأجزاء الآلية من الأطروحة

تولّد هذه السكربتات أجزاء الأطروحة التي لا يُكتب فيها رقم يدوياً: شكلي التحليل الاستكشافي في الفصل الثالث، والقسمين 5-6-3 (الجدول 5-6) و5-8 من الفصل الخامس، وخانة حالة NFR-01 في الملحق ج، والملحق د، والفصل السادس المبني من نصه المسجل. وكلها تقرأ `results/` قراءة فقط.

## ترتيب التشغيل (من جذر المستودع)

```bash
python3 scripts/thesis/eda_figures.py      # 0) شكلا الفصل 3 من عروض 2013 وحدها (يرفض الكتابة إن خالفت أرقامه results/dev2013/)
python3 scripts/thesis/make_tables.py     # 1) الجداول من results/conf2014/ (وresults/dev2013/ablation_signals.csv)، والجدول 5-6 وقيم الأداء من results/serving_bench/
python3 scripts/thesis/assemble.py        # 2) يدرج الجداول والأشكال في §5-8، و§5-6-3 وخانة NFR-01، ويكتب الملحق د
python3 scripts/thesis/build_ch6.py       # 3) يبني الفصل 6 من نصه المسجل عند الوسم freeze-03
python3 scripts/thesis/build_thesis_docx.py [--pdf=DIR]   # 4) ملف Word النهائي (ومعاينة PDF اختيارية)
```

`build_ch6.py --verify-tag` يتحقق أيضاً من أن `templates/ch6_freeze03.md` مطابق حرفياً لنسخة الوسم (استدعاء `git show` للقراءة فقط).

**معيار القبول:** تشغيل الخطوات 1–3 على نسخة نظيفة لا يغيّر أي ملف في `docs/working/06-thesis/` (يُتحقق بـ`git diff`).

## الملفات

| الملف | يقرأ | يكتب |
|---|---|---|
| `eda_figures.py` | بيانات التطوير 2013 عبر `src.ml.data` (دور التطوير وحده)، و`results/dev2013/eda_presentations.csv` و`eda_totals.csv` للتحقق | `deliverables/06-final-thesis/figures/eda_long_tail.*` و`eda_activity_share.*` (SVG وPNG وCSV)، ويُدرجان يدوياً في الفصل 3 (الشكلان 3-1 و3-2) |
| `make_tables.py` | `results/conf2014/*` (CSV وJSON وLOCK وsummary.md)، `results/dev2013/ablation_signals.csv`، و`results/serving_bench/` (`cold.json` و`warm.json` و`precomputed.json` من `src/backend/bench.py --out`، و`precompute.txt`) | `deliverables/06-final-thesis/tables/` (جدول `.md` لكل جدول ومنه `t-5-6.md`، و`serving_bench_values.json` لأرقام 5-6-3 وNFR-01 والفصل 6، و`figures.txt` لكتل الأشكال وتعليقاتها، و`CHECKS.txt`) |
| `assemble.py` | `templates/sec58_template.md`، `templates/appD_template.md`، `templates/sec563_template.md`، `templates/nfr01_status_template.md`، مخرجات الخطوة 1 | `docs/working/06-thesis/ch5-implementation-results.md` (ما بين عنوان 5-6-3 وعنوان 5-7، وما بين عنوان 5-8 وعنوان 5-9)، وخانة الحالة في صف NFR-01 من `appendix-C-requirements.md`، و`docs/working/06-thesis/appendix-D-confirmatory-details.md` |
| `build_ch6.py` | `templates/ch6_freeze03.md`، و`serving_bench_values.json` (أرقام فقرة «بعد النتيجة» عن القيد 16: القياس البارد دون الحساب المسبق ومعه) | `docs/working/06-thesis/ch6-discussion.md` |
| `build_thesis_docx.py` | ملفات `docs/working/06-thesis/` بترتيب الرسالة (المقدمات، والفصول 1–7، والمراجع، والملاحق أ–د)، والصور | `deliverables/06-final-thesis/الأطروحة-النهائية.docx` عبر `scripts/build_docx.py`. يضيف غلافاً عربياً، وصفحة عنوان إنكليزية مستقلة، وفاصل صفحة قبل كل عنوان من المستوى الأول، وحقول فهرس المحتويات والأشكال والجداول (يحدّثها Word عند الفتح). ويضبط أنماط التعليقات، وعروض أعمدة الجداول بحسب محتواها مع تكرار صف الرأس، واتجاه الصفحة الإنكليزية والملخص الإنكليزي. ويتوقف إن غابت أي صورة. والخيار `--pdf=DIR` يكتب معاينة PDF من نسخة تُحدَّث فهارسها بـLibreOffice، وتغيب عنها المعادلات لأن LibreOffice هنا بلا وحدة Math |
| `refmap.py` | — | دوال مشتركة لإعادة ترقيم الإحالات، يستعملها `renumber.py` و`build_ch6.py`. يطبّق `build_ch6.py` جدول المقابلة المحفوظ على النص المسجل وقت البناء، فتبقى صياغة الفقرات المسجلة كما هي وتتبع أرقام الإحالات ترقيم الرسالة |
| `renumber.py` | الفصول والملاحق و`references.md` و`docs/working/07-presentation.json` | إعادة ترقيم المراجع بترتيب الظهور، وفحص ترقيم الأشكال والجداول، و`deliverables/06-final-thesis/refs_renumber_map.csv` (لا يُشغَّل على المستودع إلا بعد اكتمال سجل التحقق من المراجع) |

## قواعد

- **لا رقم يدوي في §5-8 ولا في §5-6-3 ولا في خانة حالة NFR-01 ولا في الملحق د.** ولتعديل نصها يُعدَّل القالب في `templates/`، ثم تُعاد الخطوتان 1 و2. ولا تُعدَّل حدود NFR-01 نفسها (المتطلب في الفصل 4 والملحق ج): يقارن المولّد القياس بها، ويكتب «دون الحد» أو «تجاوز» بحسب الملف.
- **يحمل عنوان كل جدول اسم مصدره ووسم مرجعه:** «(مقفل)» إن كانت كل ملفات مصدره في `results/conf2014/LOCK`، و«(ثانوي، الطور الثاني؛ مرجعه إيداع النتائج)» إن لم تكن.
- **الفحوص المتقاطعة في `make_tables.py` توقف التشغيل عند أي اختلاف.** تُقارن:
  - متوسطات `per_presentation.csv` بجدول الأحكام.
  - استئصال WRMF بقيم الشكل 3.
  - زوج H2-أ بالأحكام.
  - AUC وNDCG@10 بـ`summary.md`.
  - بصمات ملفات قيم الأشكال المقفلة بـLOCK.
  - ملفات `results/serving_bench/`: الوسيط والأقصى بعيّنات كل صف، وتطابق العرض واليوم وn والآلة بين الملفات الثلاثة، وحال الخادم المعلنة (بلا تسخين ولا ذاكرة عناقيد في `cold`، وتسخين مكتمل في `warm` و`precomputed`، وأيام باردة محسوبة مسبقاً كلها في `precomputed` وهي نفسها في `cold`)، وأن `precompute.txt` حسب كل الأيام من ذاكرة فارغة، ومصدر أداة القياس: `bench.py` غير ملتزم عند القياس (`git_dirty_paths`) وأول commit بعده يغيّره هو `BENCH_COMMIT`، وخادم الحال الباردة أُقلع عند commit لا يختلف في `src/ml` ولا `src/backend` (يُفحص بـgit إن وُجد تاريخ المستودع، ويُسجَّل في `CHECKS.txt` أنه لم يُفحص إن لم يوجد).
- **الفصل 6:** تُبقى كل فقرة مسجلة حرفياً. والمسموح ثلاثة أشياء:
  - حذف الفروع غير المنطبقة.
  - ملء «[نتيجة 2014]».
  - فقرات مستقلة تبدأ بـ«**بعد النتيجة.**».

  ويفشل `build_ch6.py` إن ظهر في الفرق مع النص المسجل أي تغيير آخر. ولتعديل ما بعد النتيجة يُعدَّل القاموس `INSERT` في السكربت.
- **الأشكال المشتقة** يرسمها `scripts/derive_conf2014_figures.py`، وتُدرج كتلها من `figures.txt`.

## إعادة الترقيم (بعد اكتمال سجل التحقق من المراجع)

```bash
python3 scripts/thesis/renumber.py            # تشغيل جاف: تقرير وفحوص فقط (رمز الخروج 1 عند أي خطأ)
python3 scripts/thesis/renumber.py --apply    # يكتب التغييرات، ثم تُعاد الخطوات 1–3 للتحقق من أنها لا تغيّر شيئاً
```

- **ما يعيد ترقيمه:** المراجع بترتيب الظهور الأول في المقدمات والفصول 1–7 والملاحق أ–د، بما فيها عمود «#» في جداول الملحق أ، وتُرتَّب صفوف تلك الجداول بالرقم الجديد.
- **ما يحدّثه:** `references.md` (الترقيم والترتيب والفقرة التمهيدية)، والقوالب، و`docs/working/07-presentation.json`. أما النص المسجل `templates/ch6_freeze03.md` فلا يُمَس.
- **جدول المقابلة:** يكتبه تراكمياً من الترقيم الموحّد الأصلي إلى الجديد في `deliverables/06-final-thesis/refs_renumber_map.csv`.
- **الأشكال والجداول:** يفحص أنها مرقّمة بترتيب الظهور، ومُشار إليها قبل ظهورها، ولها مصدر. ويعيد ترقيم المخالف منها في الفصول والقوالب وأرقام الأشكال في `make_tables.py` والشرائح.

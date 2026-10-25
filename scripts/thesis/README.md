# scripts/thesis: توليد الأجزاء الآلية من الأطروحة

تولّد هذه السكربتات أجزاء الأطروحة التي لا يُكتب فيها رقم يدوياً: القسم 5-8 من الفصل الخامس، والملحق د، والفصل السادس المبني من نصه المسجل. وكلها تقرأ `results/` قراءة فقط.

## ترتيب التشغيل (من جذر المستودع)

```bash
python3 scripts/thesis/make_tables.py     # 1) الجداول من results/conf2014/ (وresults/dev2013/ablation_signals.csv)
python3 scripts/thesis/assemble.py        # 2) يدرج الجداول والأشكال في §5-8 ويكتب الملحق د
python3 scripts/thesis/build_ch6.py       # 3) يبني الفصل 6 من نصه المسجل عند الوسم freeze-03
```

`build_ch6.py --verify-tag` يتحقق أيضاً من أن `templates/ch6_freeze03.md` مطابق حرفياً لنسخة الوسم (استدعاء `git show` للقراءة فقط).

**معيار القبول:** تشغيل الخطوات الثلاث على نسخة نظيفة لا يغيّر أي ملف في `docs/working/06-thesis/` (يُتحقق بـ`git diff`).

## الملفات

| الملف | يقرأ | يكتب |
|---|---|---|
| `make_tables.py` | `results/conf2014/*` (CSV وJSON وLOCK وsummary.md)، `results/dev2013/ablation_signals.csv` | `deliverables/06-final-thesis/tables/` (جدول `.md` لكل جدول، و`figures.txt` لكتل الأشكال وتعليقاتها، و`CHECKS.txt`) |
| `assemble.py` | `templates/sec58_template.md`، `templates/appD_template.md`، مخرجات الخطوة 1 | `docs/working/06-thesis/ch5-implementation-results.md` (ما بين عنوان 5-8 وعنوان 5-9 وحده)، `docs/working/06-thesis/appendix-D-confirmatory-details.md` |
| `build_ch6.py` | `templates/ch6_freeze03.md` | `docs/working/06-thesis/ch6-discussion.md` |
| `renumber.py` | الفصول والملاحق و`references.md` و`docs/working/07-presentation.json` | إعادة ترقيم المراجع بترتيب الظهور، وفحص ترقيم الأشكال والجداول، و`deliverables/06-final-thesis/refs_renumber_map.csv` (لا يُشغَّل على المستودع إلا بعد اكتمال سجل التحقق من المراجع) |

## قواعد

- **لا رقم يدوي في §5-8 ولا في الملحق د.** ولتعديل نصهما يُعدَّل القالب في `templates/`، ثم تُعاد الخطوتان 1 و2.
- **يحمل عنوان كل جدول اسم مصدره ووسم مرجعه:** «(مقفل)» إن كانت كل ملفات مصدره في `results/conf2014/LOCK`، و«(ثانوي، الطور الثاني؛ مرجعه إيداع النتائج)» إن لم تكن.
- **الفحوص المتقاطعة في `make_tables.py` توقف التشغيل عند أي اختلاف.** تُقارن:
  - متوسطات `per_presentation.csv` بجدول الأحكام.
  - استئصال WRMF بقيم الشكل 3.
  - زوج H2-أ بالأحكام.
  - AUC وNDCG@10 بـ`summary.md`.
  - بصمات ملفات قيم الأشكال المقفلة بـLOCK.
- **الفصل 6:** تُبقى كل فقرة مسجلة حرفياً. والمسموح ثلاثة أشياء:
  - حذف الفروع غير المنطبقة.
  - ملء «[نتيجة 2014]».
  - فقرات مستقلة تبدأ بـ«**بعد النتيجة.**».

  ويفشل `build_ch6.py` إن ظهر في الفرق مع النص المسجل أي تغيير آخر. ولتعديل ما بعد النتيجة يُعدَّل القاموس `INSERT` في السكربت.
- **الأشكال المشتقة** يرسمها `scripts/derive_conf2014_figures.py`، وتُدرج كتلها من `figures.txt`.

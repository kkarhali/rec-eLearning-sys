# جرد `results/posthoc/`

مولَّد بـ`python3 scripts/posthoc/a9_inventory.py` (لاحق؛ م-ك-4، البند 2). يُعاد توليده بعد أي تغيير في `results/posthoc/` أو في `scripts/thesis/appendix_e.py`، لأن عمود «يعرضه الملحق» يُستخرج آلياً من شيفرة مولّد الملحق هـ وقت التشغيل: الملفات التي يقرؤها، وتسميات المقارنات التي يمررها إلى جداوله حرفياً.

- عدد الملفات: 44.
- الملفات التي يقرؤها مولّد الملحق الآن: `a4_1_recentpop_sknn.csv`, `a4_2_sknn_all.csv`, `a4_3_companion_metrics.csv`, `defense_stats.json`, `sklearn_equivalence.csv`.
- كل ما في المجلد لاحق، خارج عائلة هولم، وp فيه غير مصححة.

## الملفات

| الملف | الأداة | المحتوى | في git | يعرضه الملحق هـ؟ | أين / لماذا لا |
|---|---|---|---|---|---|
| `INVENTORY.md` | `a9_inventory.py` | هذه القائمة | لا | لا | ملف توثيق |
| `README.md` | `—` | وصف كل أداة: الأمر، والزمن، وما تعيد إنتاجه أولاً، والمخرجات | نعم | لا | ملف توثيق |
| `a10_reproduction_checks.csv` | `a10_selection_loo.py` | التحقق من الإعادة | لا | لا | ملف تحقق من الإعادة، يُذكر في README ولا يُعرض جدولاً |
| `a10_selection_loo.csv` | `a10_selection_loo.py` | اختيار الهجين بترك عرض خارجاً: التركيبة المختارة لكل عرض متروك وقيمتها عليه | لا | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a10_selection_loo_folds.csv` | `a10_selection_loo.py` | الأوزان والقيم لكل أصل في العرض المتروك | لا | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a10_selection_loo_stats.csv` | `a10_selection_loo.py` | الاستدلال على العروض والمقررات | لا | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a11_gru_eqinfo_sanity.json` | `a11_h3_equal_info.py` | حزمة الصحة S1–S6 للنموذج المعدَّل | لا | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a4_1_recentpop_sknn.csv` | `a4_1_recentpop_sknn.py` | هجين B3 + SKNN: الأزواج مع B3 ومع HYB\*، والشبكة الاسمية بلا أرضية مع B3، على العروض والمقررات | نعم | نعم | الجدول هـ-1 |
| `a4_1_recentpop_sknn_folds.csv` | `a4_1_recentpop_sknn.py` | الأوزان وقيمة التحقق والاختبار لكل (عرض، أصل)، بالأرضية وبالشبكة الاسمية | نعم | لا | بيانات تفصيلية للإعادة؛ الملحق يعرض الملخص |
| `a4_1_recentpop_sknn_per_presentation.csv` | `a4_1_recentpop_sknn.py` | NDCG@10 لكل عرض: الهجين اللاحق بالأرضية وبدونها، وB3 وB5 وHYB\* | نعم | لا | بيانات تفصيلية للإعادة؛ الملحق يعرض الملخص |
| `a4_1_reproduction_checks.csv` | `a4_1_recentpop_sknn.py` | التحقق من الإعادة | نعم | لا | ملف تحقق من الإعادة، يُذكر في README ولا يُعرض جدولاً |
| `a4_2_reproduction_checks.csv` | `a4_2_sknn_all.py` | التحقق من الإعادة | نعم | لا | ملف تحقق من الإعادة، يُذكر في README ولا يُعرض جدولاً |
| `a4_2_sknn_all.csv` | `a4_2_sknn_all.py` | GRU-lite − SKNN(M = الكل)، وSKNN(M = الكل) − SKNN المقفل، على العروض والمقررات، ومتوسط كل أصل وصفاً، وقراءة سداسية توضيحية | نعم | نعم | الجدول هـ-2 |
| `a4_2_sknn_all_per_presentation.csv` | `a4_2_sknn_all.py` | GRU-lite وSKNN المقفل وSKNN(M = الكل) لكل عرض | نعم | لا | بيانات تفصيلية للإعادة؛ الملحق يعرض الملخص |
| `a4_2_sknn_all_rows.csv` | `a4_2_sknn_all.py` | صفوف الاختبار بصيغة baselines.csv لـSKNN المعاد ولـSKNN(M = الكل) | نعم | لا | بيانات تفصيلية للإعادة؛ الملحق يعرض الملخص |
| `a4_2_sknn_all_tuning.csv` | `a4_2_sknn_all.py` | قيمة التحقق لكل إعداد جُرِّب لكل طيّة | نعم | لا | بيانات تفصيلية للإعادة؛ الملحق يعرض الملخص |
| `a4_3_companion_metrics.csv` | `a4_3_companion_metrics.py` | متوسط العروض وانحرافها لكل نموذج وسنة: NDCG وHR وMRR وP وR وCoverage وPopBias عند 10 | نعم | نعم | الجدول هـ-3 |
| `a4_3_companion_metrics_folds.csv` | `a4_3_companion_metrics.py` | المقاييس المرافقة لكل (عرض، أصل، بذرة) | نعم | لا | بيانات تفصيلية للإعادة؛ الملحق يعرض الملخص |
| `a4_3_companion_metrics_per_presentation.csv` | `a4_3_companion_metrics.py` | المقاييس المرافقة لكل عرض | نعم | لا | بيانات تفصيلية للإعادة؛ الملحق يعرض الملخص |
| `a4_3_reproduction_checks.csv` | `a4_3_companion_metrics.py` | التحقق من الإعادة | نعم | لا | ملف تحقق من الإعادة، يُذكر في README ولا يُعرض جدولاً |
| `a5_nonpersonal_weights.csv` | `a5_nonpersonal_weights.py` | أوزان الهجين غير الشخصي (1)+(6) لكل (سنة، عرض، أصل)، وقيمة التحقق والاختبار، والفرق عن B3 | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a5_nonpersonal_weights_counts.csv` | `a5_nonpersonal_weights.py` | عدد الطيّات لكل متجه أوزان | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a5_nonpersonal_weights_per_presentation.csv` | `a5_nonpersonal_weights.py` | الهجين غير الشخصي وB3 وHYB\* لكل عرض | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a5_nonpersonal_weights_summary.csv` | `a5_nonpersonal_weights.py` | ملخص لكل سنة | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a5_reproduction_checks.csv` | `a5_nonpersonal_weights.py` | التحقق من الإعادة: تفكيك D-60 وHYB\* | نعم | لا | ملف تحقق من الإعادة، يُذكر في README ولا يُعرض جدولاً |
| `a6_personalization_mall.csv` | `a6_personalization_mall.py` | مكسب الشخصنة بـSKNN(M = الكل): الأزواج على العروض والمقررات، وصفوف التفكيك المقفل للمرجع | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a6_personalization_mall_folds.csv` | `a6_personalization_mall.py` | الأوزان والقيم لكل (عرض، أصل، نموذج) | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a6_personalization_mall_per_presentation.csv` | `a6_personalization_mall.py` | كل النماذج لكل عرض | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a6_personalization_mall_weights.csv` | `a6_personalization_mall.py` | توزيع الأوزان | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a6_reproduction_checks.csv` | `a6_personalization_mall.py` | التحقق من الإعادة | نعم | لا | ملف تحقق من الإعادة، يُذكر في README ولا يُعرض جدولاً |
| `a7_delta_scan.csv` | `a7_delta_sensitivity.py` | مدى δ الذي يثبت فيه كل حكم مقفل | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a7_delta_sensitivity.csv` | `a7_delta_sensitivity.py` | الحكم بالقاعدة المسجلة عند δ ∈ {0.015، 0.02، 0.025} للأحكام المقفلة ولصفوف sensitivity_other.csv | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a7_reproduction_checks.csv` | `a7_delta_sensitivity.py` | التحقق من الإعادة | نعم | لا | ملف تحقق من الإعادة، يُذكر في README ولا يُعرض جدولاً |
| `a8_h3_by_cut.csv` | `a8_h3_by_cut.py` | فروق الجدول هـ-2 لكل أصل بفواصل على العروض والمقررات | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a8_h3_by_cut_per_presentation.csv` | `a8_h3_by_cut.py` | الفرق لكل (زوج، سنة، أصل، عرض) | نعم | لا | أُنتج في الجلسة الثانية بعد آخر توليد للملحق؛ لم يُدرج بعد |
| `a8_reproduction_checks.csv` | `a8_h3_by_cut.py` | التحقق من الإعادة | نعم | لا | ملف تحقق من الإعادة، يُذكر في README ولا يُعرض جدولاً |
| `defense_stats.json` | `defense_stats.py` | إحصاءات المناقشة الأولى: ارتباط عرضي المقرر، والتحليل على المقررات، وفواصل 98.75%، ونسبة δ، وفاصل σ وMDE80 عند طرفيه، وتغطية الفواصل بالمحاكاة | نعم | نعم | الجدول هـ-4، الجدول هـ-5، الجدول هـ-6 |
| `logs/a10_selection_loo.log` | `a10_selection_loo.py` | سجل الأوامر وأرقام التحقق الدقيقة | لا | لا | سجل تشغيل (خارج git بقاعدة *.log) |
| `logs/a11_h3_equal_info.log` | `a11_h3_equal_info.py` | سجل الأوامر وأرقام التحقق الدقيقة | لا | لا | سجل تشغيل (خارج git بقاعدة *.log) |
| `logs/a4_2_sknn_all.log` | `a4_2_sknn_all.py` | سجل الأوامر وأرقام التحقق الدقيقة | لا | لا | سجل تشغيل (خارج git بقاعدة *.log) |
| `logs/a5_nonpersonal_weights.log` | `a5_nonpersonal_weights.py` | سجل الأوامر وأرقام التحقق الدقيقة | لا | لا | سجل تشغيل (خارج git بقاعدة *.log) |
| `logs/a6_personalization_mall.log` | `a6_personalization_mall.py` | سجل الأوامر وأرقام التحقق الدقيقة | لا | لا | سجل تشغيل (خارج git بقاعدة *.log) |
| `logs/a7_delta_sensitivity.log` | `a7_delta_sensitivity.py` | سجل الأوامر وأرقام التحقق الدقيقة | لا | لا | سجل تشغيل (خارج git بقاعدة *.log) |
| `logs/a8_h3_by_cut.log` | `a8_h3_by_cut.py` | سجل الأوامر وأرقام التحقق الدقيقة | لا | لا | سجل تشغيل (خارج git بقاعدة *.log) |

## داخل الملفات التي يقرؤها الملحق: أي الصفوف تُعرض

المقارنة معروضة إذا مُرِّرت تسميتها حرفياً إلى جدول في `appendix_e.py`. وصفوف «origin t = … alone» لا تُعرض.

| الملف | المقارنة أو النموذج | معروضة؟ | الوحدات في الملف |
|---|---|---|---|
| `a4_1_recentpop_sknn.csv` | HYB_B3+SKNN − B3_RecentPop (H1 inference) | نعم | course (D-31 robustness, table 5-8-هـ)؛ presentation |
| `a4_1_recentpop_sknn.csv` | HYB_B3+SKNN nominal grid − B3_RecentPop | **لا** | course (D-31 robustness, table 5-8-هـ)؛ presentation |
| `a4_1_recentpop_sknn.csv` | HYB_B3+SKNN − HYB* (frozen) | نعم | course (D-31 robustness, table 5-8-هـ)؛ presentation |
| `a4_2_sknn_all.csv` | GRU_lite − B5_SKNN_Mall (H3 inference, M = None) | نعم | course (D-31 robustness, table 5-8-هـ)؛ presentation |
| `a4_2_sknn_all.csv` | B5_SKNN_Mall − B5_SKNN (locked, M = 1000) | نعم | course (D-31 robustness, table 5-8-هـ)؛ presentation |
| `a4_2_sknn_all.csv` | GRU_lite − B5_SKNN_Mall | **لا** | origin t = 126 alone (descriptive)؛ origin t = 182 alone (descriptive)؛ origin t = 70 alone (descriptive) |
| `a4_3_companion_metrics.csv` | model = B3_RecentPop | نعم | — |
| `a4_3_companion_metrics.csv` | model = B3_RecentPop (pipeline check) | **لا** | — |
| `a4_3_companion_metrics.csv` | model = HYB* | نعم | — |
| `a4_3_companion_metrics.csv` | model = B5_SKNN | نعم | — |
| `a4_3_companion_metrics.csv` | model = GRU_lite | نعم | — |
| `a4_3_companion_metrics.csv` | model = B7_WRMF | **لا** | — |
| `a4_3_companion_metrics.csv` | model = B2_Pop | **لا** | — |

**`defense_stats.json`:** المفاتيح `source`, `label`, `within_course_corr`, `course_level`, `bonferroni_98_75`, `delta_share`, `sigma`, `coverage_n13`. يقرأ الملحق منها: `within_course_corr`, `course_level`, `bonferroni_98_75`, `delta_share`, `sigma`, `coverage_n13`.

## ما لم يُعرض ولماذا (ملخص)

- **صفوف الشبكة الاسمية بلا أرضية في `a4_1_recentpop_sknn.csv`:** محسوبة ولا يعرضها الجدول هـ-1 إلا إذا ظهرت تسميتها أعلاه بـ«نعم».
- **متوسطات الأصول منفردة في `a4_2_sknn_all.csv`:** تعرضها الأداة a8 بفواصلها في `a8_h3_by_cut.csv`.
- **أعمدة P@10 وR@10 والانحرافات، وصفوف B2_Pop وB7_WRMF و«pipeline check»:** في `a4_3_companion_metrics.csv`، ولا يعرضها الجدول هـ-3.
- **ملفات الأدوات a5 إلى a11:** أُنتجت في الجلسة الثانية، ولم تُدرج في الملحق عند توليد هذه القائمة.
- **ملفات التحقق والصفوف التفصيلية:** للإعادة لا للعرض.
- **`sklearn_equivalence.csv`:** يقرؤه مولّد الملحق إن وُجد، وهو غير موجود الآن (لم تُشغَّل أداته).

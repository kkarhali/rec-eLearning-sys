# `src/ml/` — منصة التجارب وخطوط الأساس

حزمة Python (numpy + pandas فقط) تجعل كل رقم في الرسالة قابلاً لإعادة الإنتاج بأمر واحد من جذر المستودع.
تطبّق ADR-001 وADR-002 و**ADR-004** (تعديلات الاجتماع 02، D-23…D-40، يسود عند التعارض) حرفياً، وتأخذ الصيغ التفصيلية من `docs/working/02-hypotheses-algorithms.md` (الأقسام 3–5)؛
وعند التعارض تُقدَّم ADR (انظر «التعارضات» أدناه).

## التشغيل

```bash
# 0) البيانات (مرة واحدة): data/raw/oulad/ — انظر data/README.md
bash data/download.sh                     # أو: python3 data/verify_oulad.py

# 1) اختبارات الوحدة (≈ 3 ثوانٍ، لا تحتاج البيانات الخام)
python3 -m unittest discover -s src/ml/tests -v   # 121 اختباراً (≈ 6 ث)

# 2) الإحصاءات الوصفية + إعادة إنتاج فحص الزميل 0.2 وفحص المشرف (≈ 25 ثانية)
python3 -m src.ml.experiments.eda

# 3) خطوط الأساس B1–B10 على عروض 2013 التسعة × 3 أصول × مهمتان (انظر الزمن أدناه)
python3 -m src.ml.experiments.run_baselines
#    خيارات: --presentations FFF_2013J --cuts 70 --models B2_Pop B3_RecentPop --workers 4
#            --exclusion {E5,E4,none}  (تحليل حساسية E؛ يُكتب إلى --out مختلف)

# --- الجولة الثانية (بالترتيب؛ كلها على 2013 وحدها) ---
# 4) حزمة صحة GRU-lite (S1–S6، D-35) ثم تقييمه (H3)
python3 -m src.ml.experiments.gru_sanity          # → gru_sanity.md/json (بوابة: لا نتائج GRU بلا اجتياز)
python3 -m src.ml.experiments.run_gru             # → gru.csv, gru_tuning.csv (+ ذاكرة درجات للهجين)
# 5) استئصال عائلة الإشارة (H2-أ): WRMF وItem-kNN على L0/L1/L2/L3/W*
python3 -m src.ml.experiments.run_ablation        # → ablation_signals.csv, ablation_tuning.csv
# 6) تحليل المتعلمين (H4-أ، العناقيد، CART، الإنصاف الوصفي؛ يقرأ معرّفات 2014 وحدها وفق D-47 ويسجّل الوصول)
python3 -m src.ml.experiments.learner_analysis    # → learner_analysis.md, learner_auc.csv, learner_clusters.csv
# 7) الهجين: قاعدة القبول، التجميد، H1/H3 وصفياً، H4-ب
python3 -m src.ml.experiments.run_hybrid          # → hybrid_frozen.json, hybrid_acceptance.md, hybrid.csv, h4b.csv
# 8) MDE80 لكل فرضية من زوجها الفعلي (D-46)
python3 -m src.ml.experiments.power               # → mde80.md/json
# 9) قطع النماذج لخدمة إعادة التشغيل (D-49) → artifacts/ (≈ 0.5 MB)
python3 -m src.ml.experiments.build_artifacts

# إعادة توليد summary.md من ملفات CSV دون إعادة التشغيل
python3 -m src.ml.experiments.report results/dev2013

# --- الجولة الثالثة: التجميد (D-51…D-64) ---
# أمر واحد يعيد إنتاج كل نتائج التطوير من ذاكرة مؤقتة فارغة ويكتب repro_diff.md (ش5)
python3 -m src.ml.experiments.reproduce_dev
python3 -m src.ml.experiments.risk_final          # نماذج الخطر النهائية على التسعة → results/frozen/risk_final.json (ش4)
python3 -m src.ml.experiments.freeze_config       # results/frozen/freeze03_config.json + SHA-256 (ش6)
python3 -m src.ml.experiments.freeze_config --checklist   # results/frozen/freeze_checklist.md (ش10)
# مشغّل E10 (D-63): تشغيل جاف كامل على 2013، ثم — بعد الوسم وحده — التشغيل التأكيدي مرة واحدة
python3 -m src.ml.experiments.run_confirmatory --dry-run-dev --force   # (= --dry-run-2013) → results/dryrun2013/
python3 -m src.ml.experiments.run_confirmatory --tag freeze-03          # يرفض ما لم يكن HEAD = الوسم والشجرة نظيفة
python3 -m src.ml.experiments.run_confirmatory --tag freeze-03 --phase 2   # الطور 2 وحده: يتحقق من LOCK وHEAD = الوسم (م2)
python3 -m src.ml.experiments.run_confirmatory --tag freeze-03 --resume    # المسار الوحيد بعد تعطل بيئي (D-75)
```

**خدمة الواجهة (D-49، إعادة تشغيل):**
```python
from src.ml import serving
serving.recommend("FFF_2013J", 2548055, day=100, k=10)      # [{id_site, activity_type, score, components, explanation, model_cut, ...}]
serving.learner_profile("FFF_2013J", 2548055, day=100)      # الملامح، عنقود اليوم 56، احتمال الخطر (للمدرّس فقط)
serving.presentation_overview("FFF_2013J", day=100)         # لوحة المدرّس (median_active_days، حزم الدرجة)
serving.registrations("FFF_2013J", day=100)                 # قائمة بيضاء بلا final_result؛ الانسحاب بعد اليوم = null (D-70)
serving.warm("FFF_2013J")                                   # تسخين شبكة أسبوعية + القطوع (D-68)
```
- **الخطر (D-56، D-65):** `risk.score` درجة نسبية **غير معايَرة** من M1 (لا «احتمال»)، مع `provenance` (`lopo_2013`:
  نموذج العروض الثمانية الأخرى؛ `test_2014`: `risk_final.json` بعد فتح 2014)، و`threshold`/`threshold_source` لكل قطع
  (D-58 عند 56، وعتبة Youden مجمَّعة خارج الطيّة للعرض عند 28 و112)، و`factors` (w_j·z_j) و`top_factors`. لا تقدير قبل اليوم 28.
- **العنقود (D-68، D-70):** اختيار k-means عند اليوم t يُحفظ في الذاكرة وعلى القرص (`data/cache/serving_clusters/`) بمفتاح
  (عرض، يوم) وبصمة لعرض التدريب ولـ`hybrid_frozen.json` و`freeze03_config.json`، ولا يُخدم إلا لذلك اليوم؛ بالإعدادات نفسها (n_init والبذور وk) دون تقليص. والعنقود يُستعمل
  داخل التوصية ولا يُعرض: مفتاح الدليل `similar_learners_in_window`.
- **جدول المدرّس وملخص العناقيد** منفَّذان مرة واحدة في `src/backend/services/instructor.py` (حُذفت نسختا serving المكررتان).
- **FR-40:** `Engine(allow_confirmatory=True)` يرفض ما لم يوجد `results/conf2014/verdicts.csv` و`LOCK`.
- **نطاق التجميد (D-69):** `serving.py` و`build_artifacts.py` خارج نطاق `freeze-03` بشرط عدم تعديل وحدة مجمَّدة.

أول تحميل يقرأ `studentVle.csv` (10,655,280 صفاً، ≈ 15 ثانية)، ويجمّع الصفوف المكررة، ويحفظ ذاكرة مؤقتة
في `data/cache/` (pickle لأن pyarrow غير متاح؛ parquet تلقائياً إن توفر). الذاكرة المؤقتة متجاهَلة في git
وتُبطَل تلقائياً إذا تغيّر حجم الملفات الخام.

**عروض 2014 محجوبة برمجياً (D-09):** `data.assert_allowed()` يرفع `ConfirmatoryAccessError` لأي عرض 2014
ما لم يُمرَّر `allow_confirmatory=True` صراحةً، ولا تمرّره أي تجربة في هذه الجولة. الذاكرة المؤقتة نفسها
لا تحوي إلا صفوف 2013.


## البنية

| الملف | المحتوى | المرجع |
|---|---|---|
| `data.py` | تحميل الجداول السبعة؛ تجميع (تسجيل، مورد، يوم)؛ ربط `activity_type`/`week_from/to`؛ مجموعات الاستبعاد `E5` (الرئيسية) و`E4` (= E∖{page}) و`none` و`nav3` (تعريف الفحوص الاستكشافية فقط)؛ سلال الأيام؛ قرب التقييم a(d) وفئاته | D-04…D-07، D-09، D-21 |
| `signals.py` | العائلة المتداخلة L0 ⊂ L1 ⊂ L2(τ) ⊂ L3(τ,β)، وسيطات النقر لكل نوع من التدريب، ثقة WRMF `1+α·W` (والثنائية `1+α·1[W>0]`) | ADR-002 §3.2 |
| `splits.py` | القطع العام t ∈ {70,126,182}؛ مرحلة الضبط (≤ t−14 / (t−14,t]) والاختبار (≤ t / (t,t+14])؛ الكتالوج؛ المهمتان A وB؛ الأهداف غير القابلة للوصول؛ مفاتيح كسر التعادل | D-14، §5.1–5.3 |
| `metrics.py` | P/R/HR/NDCG/MRR@K، Coverage@K، PopBias@K، مرجع قائم على القوائم للاختبارات | §5.4 |
| `models/` | B1 Random، B2 Pop، B3 Recent-Pop (w ∈ {3,7,14,21,28})، B4 Item-kNN، B5 SKNN/V-SKNN (بلا سلال المستعلِم، D-33)، B6 Markov، B7 WRMF-ALS (f ≤ 64)، B8 Personal-repeat، B9 CBF، و**B10 EASE مرجعياً** (D-37) — واجهة موحّدة `fit(train) / score() / recommend(student, k, exclude_seen)` | D-10، §4.2 |
| `hybrid.py` | تطبيع رتبي بالرتبة الوسطى عند التعادل (D-32)، شبكة السمبلكس 1/4 (5، 15 نقطة) و1/3 (20 نقطة) ضمن ميزانية 20 والشبكة 0.1 حساسية (D-29)، ضبط الأوزان على التحقق، قاعدة القبول بالرفع على نوافذ **اختبار** 2013 وفاصل bootstrap-t، أرضية الشخصنة (D-30)، البحث الأمامي الجشع (≤ 4 مكوّنات) | D-11، ADR-004 §2.4 |
| `stats.py` | **bootstrap-t عنقودي معيَّر** على العروض (الفاصل المئيني للملحق)، قلب إشارات دقيق ثنائي الطرف (2ⁿ) أو مونت-كارلو، اختبار الهامش الوصفي، Holm (العائلة m = 4)، جداول الحكم بالأسبقية (أحادية وسداسية لـH3)، القوة وMDE80 (`confirmation_power`، `mde80`) | D-23…D-26، ADR-004 §2.1–2.2 |
| `harness.py` | حلقة الضبط ثم الاختبار لكل (عرض، أصل)؛ `eval_rows` لصفوف النتائج بالشرائح | ADR-002 §3.6.1، §3.6.9 |
| `models/gru_lite.py` | GRU-lite يدوي (أمامي/خلفي، Adam، قص عام 5، BPTT T=20 بتمرير الحالة، قناع الحشو، إيقاف مبكر، الهدف {next، next-new}) | D-35، §4.6 |
| `models/context.py` | (6) أسبقية قرب التقييم، (7) شعبية العنقود (k-means++ يُعاد عند كل t₀) | §4.3، D-39-ج |
| `learners.py` | ملامح السلوك (M0/M1/M2)، k-means++ وقاعدة k (silhouette/DBI/ARI)، Logistic L2 (نيوتن)، CART (جيني)، ROC/PR-AUC، Youden، Brier | D-13، D-27، §4.7 |
| `components.py` | ذاكرة درجات المكوّنات `data/cache/components/` وتحويل مفاتيح الإعداد ↔ قواميس | — |
| `serving.py` | خدمة إعادة التشغيل للواجهة: `recommend`، `learner_profile`، `presentation_overview`، مع `model_cut` وتفسير من المساهمة الفعلية | D-22، D-49، §4.8 |
| `experiments/gru_sanity.py`، `run_gru.py` | حزمة الصحة S1–S6 ثم تقييم GRU-lite (H3) | D-12، D-35 |
| `experiments/run_ablation.py` | استئصال L0/L1/L2/L3/W\* لـWRMF وItem-kNN (H2-أ) | §2.4، §5.11 |
| `experiments/learner_analysis.py` | H4-أ بترك عرض خارج التدريب، CART، عناقيد اليوم 56، إنصاف وصفي | D-13، D-27، D-47 |
| `experiments/run_hybrid.py` | قاعدة القبول الجشعة، الأرضية، التجميد، H1/H3 وصفياً، H4-ب | D-11، D-28، D-30 |
| `experiments/power.py` | MDE80 لكل فرضية من زوجها | D-46، D-48 |
| `experiments/build_artifacts.py` | قطع النماذج الثقيلة عند القطوع ونماذج الخطر (عتبة لكل قطع) والعناقيد لخدمة الواجهة | D-49، D-65 |
| `experiments/risk_final.py` | نماذج الخطر النهائية M0/M1/M2/CART على التسعة | D-58 |
| `experiments/freeze_config.py` | ملف الإعداد المجمَّد وبصماته، وقائمة شروط الوسم | D-62 ش6، ش10 |
| `experiments/reproduce_dev.py` | أمر واحد لكل نتائج التطوير + `repro_diff.md` | D-62 ش5 |
| `experiments/run_confirmatory.py` | مشغّل E10 بحراسه وطوريه وقفله، والتشغيل الجاف | D-63 |
| `plots.py` | أشكال SVG (غابي، نقاط لكل عرض، خطوط، dumbbell، ROC، أعمدة بفواصل) مع CSV لكل شكل | D-63 §4 |
| `experiments/eda.py` | الإحصاءات الوصفية وإعادة إنتاج الفحوص الاستكشافية | T1 |
| `experiments/run_baselines.py` | B1–B10 → `results/dev2013/` | D-10، D-14، D-37 |
| `experiments/report.py` | يبني `summary.md` من ملفات CSV فقط | — |
| `tests/` | 121 اختباراً unittest (المقاييس، التقسيم والتسرب، الإشارة، النماذج وأمثلة الوثيقة، GRU وفحص التدرج والقناع، المتعلمون، الهجين والإحصاء، الخدمة، قراءة D-47 وغاية D-76، حراس E10 والاستئناف D-75) | §4.11، §5.9، ADR-004 |

كل النماذج ترث `models.base.Recommender` (`_fit`/`_score`/`param_space`)؛ ملامح المتعلم تأخذ `TrainData.all_events`
(كل الأنواع حتى t₀) ولا تُحمَّل السمات الحساسة إلا لتحليل الإنصاف (D-21).

**الاستثناء الوحيد من حاجز 2014 (D-47، موسَّع بـD-76):** `data.confirmatory_student_ids(purpose)` تقرأ من `studentRegistration.csv` الأعمدة
`code_module, code_presentation, id_student` وحدها (`usecols`) وتعيد مجموعة معرّفات لحذف المتداخلين من تدريب مصنِّفات الخطر على 2013 وحده،
وتسجّل كل وصول في `results/access_log.jsonl` (الزمن، MD5، الأعمدة، عدد المعرّفات، commit، `purpose`)؛ اختبار وحدة يتحقق من الأعمدة
ومن بقاء الحاجز. `load_student_assessment()` يرشّح تقييمات 2013 لحظة القراءة.

## بنية النتائج (`results/dev2013/`، صغيرة ومضمَّنة في git)

| الملف | المحتوى |
|---|---|
| `baselines.csv` | صف لكل (مهمة، نموذج، عرض، أصل، بذرة، شريحة): الإعداد المختار وقيمته على التحقق (`val_NDCG@10`، لفجوة التفاؤل)، زمن التدريب، n_eval، P/R/HR/NDCG/MRR عند 5/10/20، Coverage وPopBias (للشريحة all). الشرائح (D-28): `all`، `cold_q1` (الربع الأدنى من الموارد المختلفة في التدريب بين المقيَّمين)، `top_q4`، `lt5` (< 5، وصفي) |
| `tuning.csv` | كل إعداد جُرِّب في مرحلة الضبط، زمنه، وقيمة NDCG@10 على التحقق للمهمتين |
| `timing.csv` | زمن كل نموذج لكل (عرض، أصل، مرحلة) وأقصى RSS للعملية |
| `folds.csv` | لكل (عرض، أصل): حجم الكتالوج، الكثافة، المتعلمون المقيَّمون، حصة الأهداف غير القابلة للوصول |
| `run_meta.json` | الأمر، commit (HEAD وقت التشغيل؛ يُعاد التشغيل بعد التزام الشيفرة ليطابقه)، بصمة البيانات، الإصدارات، زمن التشغيل |
| `summary.md` | جداول المتوسطات ± الانحراف (مولَّدة) |
| `eda_*.csv`، `eda.md` | مخرجات `eda.py` |
| `gru_sanity.md/json`، `gru.csv`، `gru_tuning.csv`، `gru_meta.json` | حزمة الصحة، ونتائج GRU-lite (بصيغة baselines.csv؛ و`GRU_lite_dh128` حساسية)، ومنحنيات الضبط |
| `ablation_signals.csv`، `ablation_tuning.csv` | الاستئصال لكل مستوى إشارة (عمود `variant`) |
| `learner_analysis.md`، `learner_auc.csv`، `learner_h4a_summary.csv`، `learner_clusters.csv`، `learner_fairness.csv`، `learner_meta.json` | تحليل المتعلمين |
| `hybrid_frozen.json`، `hybrid_acceptance.md`، `hybrid.csv`، `h4b.csv`، `hybrid_meta.json` | التركيبة المجمَّدة (المكوّنات والأوزان لكل زوج والإعدادات)، وتقرير القبول، والنتائج |
| `mde80.md/json` | MDE80 لكل فرضية (D-46) |
| `../access_log.jsonl` | سجل قراءات D-47 |

`artifacts/<presentation>/` (≈ 0.5 MB، **خارج git** منذ D-70؛ يُعاد بناؤه بخطوة `build_artifacts` ضمن `reproduce_dev`): `risk_{28,56,112}.json`، `clusters_56.npz`، ومجلدات القطوع لقطع WRMF/GRU
إن دخلت التركيبة المجمَّدة (لا تدخلها حالياً). تُعاد بـ`build_artifacts`. `data/cache/components/` (≈ 1.1 GB) متجاهَل.

قيمة الوحدة الإحصائية = العرض: متوسط البذور ← متوسط الأصول الثلاثة ← (متوسط ± انحراف) عبر العروض.

## زمن التشغيل (آلة الفريق: 4 أنوية، 15 GB)

| الأمر | الزمن |
|---|---|
| اختبارات الوحدة | ≈ 3 ث |
| `eda` | ≈ 25 ث (منها ≈ 15 ث للقراءة الأولى إن لم تكن الذاكرة المؤقتة موجودة) |
| `gru_sanity` | ≈ 1 دقيقة |
| `run_gru` (6 إعدادات × 27 زوجاً + 5 بذور تقرير + حساسية d_h=128) | **15.2 دقيقة** فعلية (≈ 59 دقيقة CPU) |
| `run_ablation` (2 نموذج × 5 مستويات × ≤ 20 إعداداً × 27 زوجاً) | **19.2 دقيقة** فعلية (≈ 192 دقيقة CPU) |
| `learner_analysis` | ≈ 2.5 دقيقة |
| `run_hybrid` (بناء الدرجات + القبول + H4-ب) | ≈ 2–3 دقائق (يعيد استعمال درجات GRU المخزَّنة) |
| `power`، `build_artifacts` | ≈ 1 دقيقة لكل منهما |
| **مجموع التطوير الكامل (الجولتان)** | ≈ 48 دقيقة فعلية، **≈ 4.8 ساعة CPU** (< 8 ساعات، D-34؛ لم يُستعمل سلّم التقليص) |
| `serving.recommend` | ≈ 10 ث لأول طلب لكل (عرض، يوم) (عنقدة اليوم وSKNN لكل المتعلمين)، ثم < 0.01 ث من الذاكرة لبقية المتعلمين في اليوم نفسه |
| `run_baselines` (B1–B10، 9 عروض × 3 أصول، 4 عمليات) | **434.4 ث ≈ 7.2 دقائق** فعلية (مقيس في `results/dev2013/run_meta.json`، 2026-10-25؛ وقيس 473.5 ث ≈ 7.9 د في تشغيل سابق اليوم نفسه؛ ≈ 20 دقيقة CPU؛ WRMF ≈ 15 دقيقة CPU بعشرين إعداداً أساسياً عند f ≤ 64، SKNN ≈ 3 دقائق؛ أقصى RSS ≈ 550 MB لكل عملية) — بعيد عن سقف 8 ساعات CPU (D-34)، فلم يُستعمل سلّم التقليص. الجولة الأولى (ADR-002) استغرقت 7.0 دقائق |

## الاستئناف المأذون والقراءة المحدودة (D-75، D-76) — منفَّذان

- **LOCK** يُكتب في آخر الطور 1 ويحمل SHA-256 لكل ملفات الطور 1 (ومنها الثانوي والأشكال SVG/PNG)، عدا `.lock`
  و`deviations.md` و`run_meta.json`. الطور 2 (وحده أو ضمن `all`) لا يبدأ إلا بعد `verify_lock`: كل ملف مقفل مطابق،
  وcommit القفل = HEAD، وفي التأكيدي HEAD = الوسم ووسم القفل = الوسم.
- **«الشجرة النظيفة»** تعني شجرة الكود والبيانات والنتائج: `src/` و`data/` و`results/` (عدا `results/dryrun2013/`، ناتج
  التشغيل الجاف نفسه، وهو خارج git) و`scripts/` وملفات الجذر التنفيذية؛ أما `docs/` و`deliverables/` و`.claude/` فخارج الحارس
  لأنها لا تغيّر التجربة. والحارس يستثني `results/access_log.jsonl` إن كانت نسخة الوسم بادئة حرفية له (إلحاق فقط)،
  و`results/conf2014_aborted_*`. البصمات المجمَّدة الثلاث وMD5 الملفات الخام السبعة تُقارَن بـ`freeze03_config.json`
  قبل أي عمل (م3)، ويرفض المشغّل عند أي اختلاف.
- **`--resume`** (التأكيدي فقط، بلا `--phase`): يتحقق من HEAD = الوسم والشجرة والبصمات وسجل البدء (`.lock` وسطر
  `confirmatory_full_read`). بلا LOCK: يُنقل `conf2014/` دون فتحه إلى `conf2014_aborted_<n>/` مع بيان SHA-256 في
  `conf2014_aborted_<n>.sha256.json`، ويُعاد الطور 1 كاملاً ثم الطور 2. مع LOCK مطابق: تُحذف بقايا الطور 2 غير المقفلة
  ويُعاد الطور 2 كاملاً. وأي اختلاف يوقف الأمر. يُسجَّل كل استئناف (`confirmatory_resume`) في `access_log.jsonl`
  وفي `deviations.md`، ولا يُعدّ تشغيلاً ثانياً.
- **الخلل البرمجي** (لا البيئي) يُصلح بأصغر تعديل، بمراجعة الزميل وموافقة المشرف كتابةً، ثم يُوسم `freeze-03.1`
  ويُعاد الطور 1 (D-75 (4)). لا مسار في الكود لذلك عمداً: هو قرار بشري موثَّق.
- **التشغيل الجاف** يسجّل في `run_meta.json`: `guard_rehearsal` (كل حارس، و`check_guards` بوسم يساوي HEAD)،
  و`audit_2014` (لا قراءة كاملة، وقراءات D-47 بثلاثة أعمدة فقط، ولا عرض 2014 في أي محمِّل)، و`path_checks`
  (LOCK وعدد الملفات المقفلة وSVG/PNG)، و`resume_simulation` بالحالات الثلاث على نسخة منه: انهيار قبل LOCK،
  وانهيار بعده، وتلاعب بملف مقفل (شكل ثم verdicts)، بـ`resume_prepare` نفسها. ويشغّل فرع H4-أ النهائي
  (أوزان `risk_final.json` وشجرة CART كما هي) إلى `h4a_frozen_branch.csv` (داخل العينة على 2013: تمرين مسار لا دليل؛ م1).
- **D-76:** `confirmatory_student_ids(purpose)`؛ `purpose` إلزامي من القائمة البيضاء `learner_analysis` و`risk_final`
  و`run_confirmatory` و`build_artifacts`، ويُسجَّل في كل سطر من السجل، وأي قيمة أخرى ترفع `ValueError` قبل أي قراءة.
  اختبار سلبي (`test_ids_only_filter_2013_risk_training`) يفحص شجرة الكود: لا استدعاء خارج الدوال الأربع، ولا استعمال
  في الخدمة أو التوصية أو العنقدة أو الواجهة الخلفية أو تحليل 2014، وفي `h4a` لا تمس المعرّفات إلا جدول تدريب 2013.

## القرارات التنفيذية — كلها مثبَّتة

- **D-41…D-49** (ADR-004 §4-مكرر) و**D-51…D-58** (الاجتماع 03): المقيَّم؛ الاختيار لكل مهمة والفرضيات والهجين على A؛
  Item-kNN ثنائي؛ CBF مطبَّع؛ البارد n ≤ Q1؛ σ في MDE80 من زوج كل فرضية؛ قراءة D-47 المحدودة؛ نص D-48؛ إعادة التشغيل؛
  **أرضية فعلية بوزن ≥ 1/4** (D-51، والاسمية حساسية)؛ **الفاصل المنحلّ ±∞ موسوم** (D-52)؛ خانة (4) واحدة = B5 (D-53)؛
  انحراف البذور لمتوسط التركيبة (D-54)؛ ملامح العنقدة و(6) وH4-ب (D-55)؛ خطر اللوحة M1 (D-56)؛ الهجين على B (D-57)؛ بنود
  GRU وH4-أ والخدمة ونماذج الخطر النهائية (D-58)؛ H2-ب غير منطبقة بالبناء (D-59)؛ تفكيك H1 (D-60)؛ جدول MDE80 (D-61).
- **D-65…D-70** (مراجعة وثيقة التصميم): درجة خطر نسبية؛ التحفيظ والتسخين؛ القائمة البيضاء؛ نطاق التجميد؛ artifacts خارج git.
- **ملاحظات الزميل على D-47:** N1 (كل دوال التحميل العامة ترشّح بحسب الدور، و2014 يحتاج `role="conf"` +
  `allow_confirmatory=True`؛ اختبار `test_rest_of_barrier_intact` يفشل إن عاد صف 2014 من أي دالة تحميل)، وN2 (قارئ وهمي
  بأعمدة زائدة ← `RuntimeError`)، وN3 (تسجيل `attempt` قبل القراءة و`failure` عند الفشل، وحقل `dirty`).

**ما بقي اختياراً هندسياً موثَّقاً (لا يمس رقماً مجمَّداً):** في التشغيل الجاف على 2013 تُعاد مواصفة نماذج الخطر بترك عرض
خارج التدريب وبـλ المجمَّدة (لا يمكن تقييم 2013 بنموذج دُرِّب عليها)؛ ونماذج 2014 هي `risk_final.json` نفسها.

## شروط وسم `freeze-03` (D-62)

القائمة المولَّدة مع مسارات الأدلة: `results/frozen/freeze_checklist.md` (`freeze_config --checklist`). الجدول أدناه حالها
عند كتابة هذا الملف.

| # | الشرط | الحالة | الدليل | المسؤول |
|---|---|---|---|---|
| ش1 | run_hybrid بأرضية D-51 افتراضياً + الملفات | ✓ | results/dev2013/hybrid_frozen.json (floor_rule)، hybrid_acceptance.md | مهندس ML |
| ش2 | MDE80 لـH1 بالـHYB* الجديد | ✓ | results/dev2013/mde80.md (H1 = 0.0375) | مهندس ML |
| ش3 | الهجين على B؛ M1 افتراضياً؛ وسم «منحلّ»؛ H2-ب غير منطبقة | ✓ | hybrid.csv (task B)، serving.py (risk_model="M1")، stats.cluster_bootstrap_t + اختبار، hybrid_frozen.json (H2b) | مهندس ML |
| ش4 | نماذج الخطر النهائية | ✓ | results/frozen/risk_final.json | مهندس ML |
| ش5 | reproduce_dev + repro_diff.md | ✗ | results/dev2013/repro_diff.md | مهندس ML |
| ش6 | freeze03_config.json + SHA-256 | ✓ | results/frozen/freeze03_config.json | مهندس ML |
| ش7 | run_confirmatory + تشغيل جاف كامل على 2013 | ✗ | src/ml/experiments/run_confirmatory.py، results/dryrun2013/ | مهندس ML |
| ش8 | مراجعة الزميل وتوقيعه | ✗ | docs/meetings/*peer* | الزميل الباحث |
| ش9 | تحديث الوثيقة 02 بالملحق ب وREADME | ✓ | docs/working/02-hypotheses-algorithms.md، src/ml/README.md | مصمّم الفرضيات + مهندس ML |
| ش10 | تحقق المشرف وتوقيعه ثم الوسم | ✗ | §8 من محضر الاجتماع 03؛ git tag freeze-03 | المشرف ← مهندس ML |

- **ش5:** أول تشغيل كامل (53.6 دقيقة) طابق كل الملفات عدا: (1) ترتيب سجل التركيبات في `hybrid_acceptance.md` بسبب التكرار على `set` (يتغير مع PYTHONHASHSEED) — أُصلح (`hybrid.greedy_forward`) وتحقق التطابق تحت بذرتي تجزئة؛ (2) جدول الأزمنة في `summary.md` — صار محجوباً؛ (3) بصمات `freeze03_config.json` — أُزيلت الحقول المتقلبة من الملفات المبصومة فصارت ثابتة بايتياً؛ (4) `risk_final.json` في اللقطة كان نسخة وسيطة غير مُودَعة خاطئة (AUC لـM0 = 0.567) والمعاد إنتاجه يطابق المُودَع وتحليل المتعلمين (0.712). **يلزم تشغيل كامل أخير على commit نظيف** لاعتماد «مطابق».
- **ش7:** المشغّل واختباراته جاهزة؛ **التشغيل الجاف الكامل لم يُنفَّذ بعد** (≈ 2 ساعة).

## التعارضات بين المسوّدة وADR وأخطاء الأمثلة

- **عائلة Holm:** المسوّدة §5.7 اقترحت m = 5 وADR-002 قال «الأربع»؛ **حُسم في D-23: m = 4 = {H1، H2-أ، H3، H4-أ}**. `stats.holm` عام.
- **الفاصل:** ADR-002 والمسوّدة §5.6.1 مئيني؛ **ADR-004 يستبدله بـbootstrap-t المعيَّر** (مطبَّق؛ المئيني في الملحق).
- **شبكة الأوزان:** المسوّدة §4.4.2 خطوة 0.1 (11/66/286)؛ **ADR-004: 1/4 و1/3 (≤ 20)**، و0.1 حساسية.
- **نتائج الجولة الأولى** (قبل ADR-004: B3 بـw ∈ {7,14}، WRMF بـf ≤ 128 و6 إعدادات، فاصل مئيني) محفوظة في git عند commit `2fc6698`؛ `results/dev2013/` الحالي هو تشغيل ADR-004.
- **الأمثلة العددية في الأقسام 3–5:** كلها أُعيد حسابها في الاختبارات (الجداول 7، 8، 12، 14، 19، 19-أ، أمثلة SKNN/V-SKNN/Markov/WRMF/CBF، sign-flip، Holm، HR النظري للعشوائي) **ولم يوجد فيها خطأ**؛ الملاحظة الوحيدة أن متوسط NDCG@5 في الجدول 19 = 0.4925 (مقرَّب إلى 0.49).
- **فحوص الاستكشاف:** فحص الزميل 0.2 على FFF_2013J أُعيد إنتاجه بالأرقام نفسها (`results/dev2013/eda.md` §4). الجزء الخاص بـDDD_2014B وأرقام فحص المشرف المحسوبة على العروض الـ22 لا تُعاد هنا لأن D-09 يمنع لمس 2014 قبل التجميد؛ أُعيدت على عروض 2013 وحدها.

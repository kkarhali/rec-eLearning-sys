# توثيق الكود البرمجي

**المرحلة الرابعة من رسالة الماجستير: «نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم»**

- **القارئ المستهدف:** لجنة التحكيم، وأي مطوّر يريد أن يفهم كيف بُني النظام، وكيف يُشغَّل، وكيف يُعاد إنتاج كل رقم في الرسالة.
- **حالة المستودع وقت الكتابة:** 2026-10-25، commit `2d86082` (لا فرق في `src/` عن `85a0376` الذي أُخذت عليه القياسات)، قبل الوسم `freeze-03`. كل ما يُذكر هنا من أسماء ملفات ودوال وأوامر قُرئ من الشيفرة نفسها، وشُغّلت الاختبارات والأوامر المذكورة فعلاً (الفصل 7). الأرقام المتحركة (أعداد الاختبارات والأزمنة) مؤرَّخة بالتاريخ والـcommit حيث وردت، وحين يخالف README الشيفرة يُذكر ذلك صراحة (§7.4). **تُستكمل بعد التشغيل:** نتائج الشرطين ش5 (`reproduce_dev`) وش7 (التشغيل الجاف) في §8.4.
- **المصطلحات:** تبقى بالإنكليزية كما وردت في الكود (`fit`، `recommend`، `Engine`…)، والشرح بالعربية.

# 1. نظرة عامة

## 1.1 الغرض

يبني الكود ثلاثة أشياء مترابطة فوق مجموعة بيانات OULAD (Open University Learning Analytics Dataset):

1. **منصة تجارب أوفلاين** (`src/ml/`): تحمّل السجلات، وتبني الإشارة السلوكية، وتقسّم الزمن إلى طيّات بلا تسرب، وتدرّب خطوط الأساس B1–B10 والنموذج العصبوني GRU-lite والهجين، وتحسب المقاييس والاستدلال الإحصائي، وتكتب كل النتائج في ملفات صغيرة تحت `results/`. 
2. **خدمة توصية بنمط إعادة التشغيل (Replay)** (`src/ml/serving.py` ثم `src/backend/`): تأخذ تسجيلاً ويوماً t، وتعيد ما كان سيوصى به عند ذلك اليوم مع تفسير كل توصية، من التركيبة المجمَّدة على بيانات 2013، دون أن تستعمل أي حدث بعد اليوم t.
3. **واجهة عربية RTL** (`src/frontend/`): صفحة للمتعلم (أفضل 10 توصيات وتفسيرها) ولوحة للمدرّس (الملامح والعناقيد ودرجة الخطر النسبية)، وتعمل فوق الخدمة أو بوضع محاكاة مستقل.

وحدة التوصية المورد غير التنقّلي `id_site` داخل عرض المقرر، والمتعلم هو التسجيل (D-04)، ولكل عرض نموذجه المستقل (D-05).

## 1.2 خريطة المستودع

```
rec-eLearning-sys/
  README.md
  data/
    download.sh  verify_oulad.py  oulad_md5_reference.txt
    raw/oulad/            (untracked)
    cache/                (untracked)
    repro_snapshot/       (untracked)
  src/
    ml/
      data.py  signals.py  splits.py  metrics.py  hybrid.py  stats.py
      harness.py  learners.py  components.py  serving.py  plots.py
      models/        base simple knn baskets markov wrmf ease cbf
                     context gru_lite
      experiments/   eda run_baselines gru_sanity run_gru run_ablation
                     learner_analysis run_hybrid power build_artifacts
                     report risk_final freeze_config reproduce_dev
                     run_confirmatory
      tests/         9 test files
    backend/         app.py settings.py errors.py schemas.py repository.py
                     routes/ services/ tests/ e2e/ bench.py
    frontend/        src/ styles/ mock/ screenshots/ build.sh
  results/
    dev2013/         development outputs
    frozen/          freeze03_config.json risk_final.json freeze_checklist.md
    access_log.jsonl
  artifacts/         (untracked)
  scripts/           build_docx.py lo_update_toc.py svg2png.js svg2png.py
                     build_pptx.py
  docs/  deliverables/  references/
```

| المسار | الدور |
|---|---|
| `data/raw/oulad/`، `data/cache/`، `data/repro_snapshot/` | بيانات OULAD الخام (≈ 825 MB)، والذاكرة المؤقتة (أحداث مجمَّعة ودرجات المكوّنات وعنقدة الخدمة، ≈ 1.3 GB)، ولقطة `reproduce_dev`؛ كلها خارج git |
| `src/ml/` | منصة التجارب وخدمة إعادة التشغيل `serving.py` ومولّد الأشكال `plots.py` |
| `src/backend/` | خدمة starlette: المسارات والخدمات والعقود والاختبارات وقياس الأداء ولقطات الواجهة الحية |
| `src/frontend/` | الواجهة (TypeScript وHTML وCSS) وملفات المحاكاة ولقطاتها |
| `results/dev2013/` | مخرجات التطوير النصية (CSV وJSON وMD)، ≈ 3.4 MB، في git |
| `results/frozen/` | الإعداد المجمَّد ونماذج الخطر النهائية وقائمة شروط التجميد، في git |
| `artifacts/` | معاملات القطوع (`risk_*.json` و`clusters_56.npz`)، ≈ 0.5 MB، **خارج git** (D-70) وتُعاد بـ`build_artifacts` |
| `scripts/` | أدوات البناء (الفصل 6) |
| `docs/`، `deliverables/`، `references/` | المسوّدات والقرارات والمحاضر، ومخرجات المراحل (Word وPowerPoint ولقطات الشاشة)، والمراجع العلمية |

## 1.3 الفصل بين الكود والمخرجات النصية

يفصل المستودع بوضوح بين أربعة أنواع من الملفات، ولا يخلط بينها أي أمر بناء:

| النوع | أين | يُولَّد بـ | في git؟ |
|---|---|---|---|
| **الكود** | `src/`، `scripts/`، `data/*.py\|sh` | يُكتب يدوياً | نعم |
| **مخرجات التجارب** (أرقام وجداول صغيرة) | `results/dev2013/`، `results/frozen/` | أوامر `python3 -m src.ml.experiments.*` | نعم (صغيرة) |
| **البيانات والذاكرات المؤقتة والمعاملات المبنية** | `data/raw/`، `data/cache/`، `data/repro_snapshot/`، `artifacts/` | `data/download.sh` وأول تحميل و`build_artifacts` | لا (`.gitignore`) |
| **المخرجات النصية** (مسوّدات ووثائق Word/PPTX) | `docs/working/`، `deliverables/` | `scripts/build_docx.py`، `build_pptx.py` | نعم |

قاعدة التصميم: الوثائق لا تُنشئ أرقاماً؛ الشيفرة تكتبها في `results/` وتنقلها الوثائق (مثال: `summary.md` يولّده `report.py` من ملفات CSV وحدها).

## 1.4 التقنيات والقيود ولماذا

بيئة العمل لا تسمح بتثبيت حزم جديدة (pip وnpm محجوبان). المتاح في Python هو numpy وpandas وstarlette وuvicorn وpydantic وأدوات الوثائق؛ ولا يتوفر scikit-learn ولا scipy ولا matplotlib ولا TensorFlow ولا torch ولا FastAPI. هذا قيد هندسي لا علمي، وثّقه ADR-003 انحرافاً معلناً عن خطة البحث.

| الطبقة | المستعمل (إصدارات التحقق) | ما استُعيض به ولماذا |
|---|---|---|
| تعلّم الآلة والإحصاء | Python 3.13.17، numpy 2.5.3، pandas 3.0.5 | بدل TensorFlow/Keras: GRU-lite مكتوب يدوياً مع فحص تدرج بالفروق المحدودة. بدل scikit-learn: k-means++ وLogistic وCART والمقاييس مكتوبة بـnumpy ومغطاة باختبارات وحدة على حالات معروفة الحل. بدل scipy: اختبار قلب الإشارات وbootstrap-t وHolm وتوزيع t مكتوبة يدوياً (`stats.py`) |
| الخدمة | starlette 1.7.0، uvicorn 0.54.0، pydantic 2.13.5 | بدل FastAPI: starlette مع نماذج pydantic للعقود |
| الواجهة | HTML وCSS خالص وTypeScript بمترجم `tsc` وحده (Node v22.22.0) | لا React ولا مكتبات رسوم؛ الرسوم SVG مكتوبة يدوياً؛ لا حاجة لأي `npm install` |
| التخزين | CSV وJSON وnpz وpickle | لا parquet (pyarrow غير متاح)؛ يختار `data.py` parquet تلقائياً إن توفر |
| الوثائق | pandoc، python-docx، LibreOffice، python-pptx، Playwright (Node) | تحويل Markdown إلى Word RTL وتصيير SVG |

كل خوارزمية موثّقة باختبارات تعيد حساب الأمثلة العددية المنشورة في وثيقة الفرضيات، فتحل الاختبارات محل الثقة بمكتبة جاهزة.

## 1.5 مصطلحات الوثيقة

| المصطلح | المعنى في الكود والوثيقة |
|---|---|
| **الأصل (t)** | نقطة القطع الزمنية العامة t ∈ {70، 126، 182} (`splits.CUTS`)؛ ويرد أحياناً «القطع» في الخدمة بمعنى «قطع النموذج» (`model_cut`) |
| **الطور** | `tune` (تدريب حتى t−14 وتحقق في (t−14، t]) أو `test` (تدريب حتى t واختبار في (t، t+14]) |
| **الطيّة (fold)** | الثلاثية (عرض، أصل، طور) التي يبنيها `splits.make_fold` |
| **HYB\*** | التركيبة المجمَّدة للهجين: C7 (7) مع SKNN (4) بأرضية شخصنة ≥ 1/4 (D-51) |
| **فحوص الصحة S1–S6** | فحوص GRU-lite (§3.7) |
| **تصحيح هولم (Holm)** | التصحيح التنازلي على العائلة الثابتة m = 4 |
| **عائلة الإشارة W\*** | اتحاد المستويات L1 وL2 وL3 بمعاملاتها المضبوطة على التحقق (H2-أ) |

# 2. المتطلبات والتثبيت والتشغيل من الصفر

## 2.1 المتطلبات

- Python 3.13 مع numpy وpandas (لمنصة التجارب)، وstarlette وuvicorn وpydantic (للخدمة). لا يوجد ملف `requirements.txt` (لا تثبيت ممكن في بيئة العمل)؛ **الإصدارات المعتمدة للتحقق**: Python 3.13.17 وnumpy 2.5.3 وpandas 3.0.5 وstarlette 1.7.0 وuvicorn 0.54.0 وpydantic 2.13.5 وNode v22.22.0، وهي المسجَّلة في `run_meta.json`.
- Node.js مع `typescript` عالمياً (الأمر `tsc`)، وPlaywright العالمي للقطات فقط؛ و`git` و`bash` و`curl` والاتصال بـGitHub.
- مساحة ≈ 825 MB للبيانات الخام و≈ 1.3 GB للذاكرة المؤقتة؛ وأقصى RSS ≈ 550 MB لكل عملية؛ والتشغيل الكامل مصمَّم لأربع أنوية (`--workers 4`).

## 2.2 الاستنساخ وتحميل البيانات والتحقق

```
git clone <عنوان-المستودع> rec-eLearning-sys
cd rec-eLearning-sys
bash data/download.sh          # يستنسخ مرآتين من GitHub، ثم يستدعي verify_oulad.py
python3 data/verify_oulad.py   # يعيد التحقق وحده (يطبع integrity: PASS)
```

`data/download.sh` يستنسخ مرآة `LuongAnh1/oulad-data-warehouse` لأجزاء `studentVle_*.csv` الثمانية ومرآة `reyquiroz/OULAD_CourseAware` للجداول الستة الصغيرة إلى `data/raw/oulad/`. والاستشهاد في الرسالة بالمصدر الرسمي (Kuzilek وآخرون، Scientific Data 4:170171، CC BY 4.0).

`data/verify_oulad.py` يعيد بناء `studentVle.csv` من الأجزاء الثمانية (يطبّق اقتباس كل الحقول ونهايات الأسطر CRLF لتطابق الملف الأصلي بايتاً)، ثم يقارن MD5 للملفات السبعة بـ`data/oulad_md5_reference.txt` وعدد الصفوف (10,655,280) ويخرج برمز غير صفري عند أي اختلاف. المخرج الفعلي عند التحقق:

```
rebuilt studentVle.csv: 10,655,280 rows (published: 10,655,280)
OK   assessments.csv            6126f9d435767bcc70134b46f21c2a90  expected=6126f9d4...
...
OK   studentVle.csv             b8aae6f4ffd1523319aeb56d66b17f72  expected=b8aae6f4...
OK   vle.csv                    0e7ef38c483daca42900ca426b66f8da  expected=0e7ef38c...
integrity: PASS
```

أول تحميل لـ`studentVle.csv` عبر `data.load_daily_events` يستغرق ≈ 15 ثانية، ثم يحفظ ذاكرة مؤقتة في `data/cache/daily_events_dev_<fingerprint>.pkl` (للعروض التسعة 2013 وحدها).

## 2.3 تشغيل الاختبارات

الأعداد أدناه مقيسة في 2026-10-25 على commit `85a0376` (4 أنوية):

```
python3 -m unittest discover -s src/ml/tests               # 108 اختباراً، ≈ 5 ث، بلا البيانات الخام
python3 -m unittest src.backend.tests.test_contract_no_risk src.backend.tests.test_static_errors
python3 -m unittest discover -s src/backend/tests -t .     # 52 اختباراً، ≈ 120 ث (تحتاج البيانات)
cd src/frontend && tsc --noEmit -p tsconfig.json           # فحص الأنواع (strict)
```

اختبارات الخلفية تستعمل استيراداً نسبياً (`from .asgi_client import Client`)، فلا بد من الخيار `-t .` عند استعمال `discover`. الأمر `discover -s src/backend/tests` بلا `-t .` يفشل في استيراد ثلاث وحدات بالخطأ `attempted relative import with no known parent package` (تحققنا منه: `Ran 18 tests … FAILED (errors=3)`)، فلا يُستعمل مع `-k` أيضاً. زمن الخلفية الكاملة يتراوح بين ≈ 25 و≈ 120 ثانية بحسب وجود عنقدة الخدمة المخزَّنة على القرص (§4.5).

## 2.4 إعادة إنتاج نتائج التطوير

**أمر واحد:** `reproduce_dev` (D-62 ش5) يعيد إنتاج كل نتائج التطوير من ذاكرة مؤقتة فارغة ويقارنها بلقطة ما قبل التشغيل:

```
python3 -m src.ml.experiments.reproduce_dev              # ≈ 50 دقيقة على 4 أنوية
python3 -m src.ml.experiments.reproduce_dev --diff-only  # إعادة المقارنة وحدها مع اللقطة الأخيرة
```

يحفظ الأمر نسخة من `results/dev2013/` و`results/frozen/` في `data/repro_snapshot/` ويفرغ `data/cache/`، ثم يشغّل الخطوات الاثنتي عشرة (من `eda` إلى `report`) كلاً في عملية مستقلة. بعد ذلك يقارن كل ملف بلقطته حرفياً بعد حجب الحقول المتقلبة وحدها (الأزمنة والتواريخ وhash الـcommit والذاكرة والسرعة)، ويكتب `results/dev2013/repro_diff.md` (الحالة «مطابق» أو «فروق») و`repro_meta.json` (زمن كل خطوة). **تُستكمل بعد التشغيل:** حالة `repro_diff.md` على commit نظيف (§8.4). والتسلسل اليدوي المكافئ لما في `src/ml/README.md`:

```
python3 -m unittest discover -s src/ml/tests -v
python3 -m src.ml.experiments.eda               # ≈ 25-40 ث
python3 -m src.ml.experiments.run_baselines     # ≈ 8 د (473.5 ث في run_meta.json)
python3 -m src.ml.experiments.gru_sanity        # ≈ 1 د؛ بوابة: لا نتائج GRU بلا اجتيازها
python3 -m src.ml.experiments.run_gru           # 15.2 د
python3 -m src.ml.experiments.run_ablation      # 19.2 د
python3 -m src.ml.experiments.learner_analysis  # ≈ 2.5 د
python3 -m src.ml.experiments.run_hybrid        # ≈ 2-3 د
python3 -m src.ml.experiments.power             # ≈ 1 د
python3 -m src.ml.experiments.risk_final        # نماذج الخطر النهائية
python3 -m src.ml.experiments.build_artifacts   # ≈ 1 د؛ لازمة قبل الخادم
```

المجموع ≈ 48 دقيقة فعلية و≈ 4.8 ساعة CPU (سقف D-34: 8 ساعات)، وأول `reproduce_dev` كامل استغرق 53.6 دقيقة. تتطابق المقاييس لأن كل شيء حتمي (§8)، وتتغير الأزمنة والتواريخ فقط. `run_hybrid` لا يعتمد على كاش جاهز: يبني درجات المكوّنات في `data/cache/components/` (≈ 1.1 GB) في خطوته الأولى ويعيد استعمال درجات GRU التي كتبها `run_gru`.

**أرقام مرجعية للمطابقة** (مأخوذة من `results/dev2013/`، المهمة A، الشريحة `all`، متوسط ثم متوسط الأصول، تقريب 3 منازل):

| الرقم | القيمة | المصدر |
|---|---|---|
| NDCG@10 لـB3 (Recent-Pop) | 0.541 | `summary.md` الجدول 1 |
| NDCG@10 لـB5 (SKNN) | 0.531 | `summary.md` الجدول 1 |
| NDCG@10 لـGRU-lite | 0.519 | `summary.md` الجدول 1 |
| NDCG@10 لـHYB\* على نوافذ الاختبار | 0.561 (الأرضية الاسمية 0.556) | `hybrid_meta.json` |
| H4-أ: AUC(M1) − AUC(M0) عند اليوم 56 | +0.0142 | `learner_h4a_summary.csv` |

**اختبار سريع (≈ 2 ثانية)** يتحقق من سلامة الخط بلا انتظار التشغيل الكامل:

```
python3 -m src.ml.experiments.run_baselines --presentations FFF_2013J --cuts 70 --models B2_Pop B3_RecentPop --workers 1 --out /tmp/q
```

والناتج المتوقع في `/tmp/q/baselines.csv` (المهمة A، الشريحة `all`، FFF_2013J عند القطع 70، `n_eval` = 991): NDCG@10 = 0.108476 لـB2_Pop و0.394036 لـB3_RecentPop بالإعداد `w=3`، وهي مطابقة لصفوف `results/dev2013/baselines.csv` (تحققنا منها).

الملف `experiments/risk_final.py` (نماذج الخطر النهائية، D-58) يكتب `results/frozen/risk_final.json` وينسخه إلى `artifacts/`، وهو ضمن خطوات `reproduce_dev`. وتجارب التجميد (`freeze_config` و`run_confirmatory`) في §8.4.

## 2.5 بناء الواجهة وتشغيل الخادم وفتح الصفحات

```
python3 -m src.ml.experiments.build_artifacts   # أولاً: artifacts/ خارج git (D-70)، ≈ دقيقة
bash src/frontend/build.sh                      # tsc → dist/js، ونسخ html/css/mock إلى dist/
python3 -m src.backend --warm                   # http://127.0.0.1:8000 (الواجهة + /api)
```

**قبل الخادم لا بد من `build_artifacts`** ومن وجود `data/raw/oulad/` و`data/cache/` و`hybrid_frozen.json`؛ غيابها يعطي 503 `artifacts_missing` (ما يراه من يستنسخ المستودع ويشغّل الخادم مباشرة). و`build_artifacts` يقرأ معرّفات 2014 بالاستثناء D-47 فيضيف سطراً إلى `access_log.jsonl`.

التسخين (D-68) للأيام 75 و56 و70 و112 و126 و182: ≈ 25 ثانية (قياس 2026-10-25 مع عنقدة مخزَّنة على القرص)، و≈ 61 ثانية في أول تشغيل بعد تغيّر بصمة التجميد لأن العنقدة تُعاد وتُخزَّن. بعده تُفتح الصفحات:

| الصفحة | الرابط | ملاحظة |
|---|---|---|
| الرئيسية (معالج الاختيار) | `http://127.0.0.1:8000/` | اختيار العرض والتسجيل واليوم |
| واجهة المتعلم | `/learner.html?p=FFF_2013J&r=FFF_2013J-371869&d=75` | أفضل 10 وزر «لماذا؟» |
| لوحة المدرّس | `/instructor.html?p=FFF_2013J&d=75` | تتطلب اليوم ≥ 56 (422 قبله، D-74) |
| عن النظام | `/about.html` | نص ثابت (FR-35) |

خيارات الخادم (من `--help`): `--host` و`--port` و`--no-instructor` و`--warm` و`--warm-presentation` و`--warm-days` و`--warm-weekly` و`--log-level`. من دون `dist/` يعيد الجذر 503 برسالة تدل على أمر البناء وتبقى مسارات `/api/*` تعمل. وللتجربة بلا خادم: `python3 -m http.server 8000 -d src/frontend/dist` ثم تفتح الواجهة بوضع المحاكاة تلقائياً (§5.3).

# 3. وحدة `src/ml`

## 3.1 خط المعالجة

```
 data.py            signals.py          splits.py            models/*  (fit/score/recommend)
 load + aggregate → W_ui(t0), levels → TrainData(d ≤ t0)  → score matrix U×I
 D-06 / E5 / guard   L0 ⊂ L1 ⊂ L2 ⊂ L3   Targets(t0, t0+14]     │
                                                                 ▼
 stats.py  ◄──── metrics.py ◄──── harness.py ◄──── hybrid.py (rank fusion + acceptance)
 bootstrap-t     NDCG/HR/MRR       tune → test        │
 sign-flip,Holm  Coverage/PopBias  per (pres, cut)    ▼
                                           results/dev2013/*.csv|json|md
                                           artifacts/*  →  serving.py (Engine)
```

الاتجاه واحد: لا تعتمد الطبقة الدنيا على العليا. `data` لا تعرف النماذج، والنماذج لا تعرف المقاييس، و`serving` تستورد من الجميع ولا يستوردها أي مسار تجريبي (D-69).

## 3.2 `data.py`: التحميل والتجميع والحاجز

**المسؤولية:** قراءة جداول OULAD السبعة، وتجميع الصفوف المكررة، وربط `activity_type`، وتعريف مجموعات الاستبعاد، وحجب عروض 2014.

- **الثوابت:** `DEV_PRESENTATIONS` (9 عروض 2013)، `CONF_PRESENTATIONS` (13 عرضاً 2014)، `E5` (الأنواع الخمسة المستبعدة من الهدف: homepage وsubpage وsharedsubpage وfolder وpage)، `EXCLUSION_SETS` (`E5` الرئيسية، و`E4` = E∖{page}، و`none`، و`nav3` لإعادة إنتاج فحوص المشرف والزميل فقط)، `SENSITIVE_COLUMNS` (الست سمات التي لا تدخل أي نموذج، D-21).
- **المحمِّلات:** `load_vle`، `load_assessments`، `load_courses`، `load_student_info(include_sensitive=False)`، `load_student_assessment`، `load_registrations`، كلها تقبل `role` (`dev` أو `conf` أو `all`) و`allow_confirmatory`. وترشّح الصفوف عند القراءة، فلا يمر صف 2014 إلى الذاكرة بلا إذن.
- **`load_daily_events(role, allow_confirmatory, use_cache)`:** يعيد صفاً لكل (presentation, id_student, id_site, date) بعد جمع `sum_click` للصفوف المكررة (D-06)، بأعمدة `clicks` و`n_rows` و`activity_type` و`week_from` و`week_to`. الذاكرة المؤقتة تُبطَل إذا تغير حجم `studentVle.csv` أو `vle.csv` (`raw_fingerprint()`).
- **`PresentationData`** (dataclass): `name` و`events` و`items` و`assessments` و`students` (بلا السمات الحساسة) و`registrations` و`length`. تبنيها `load_presentation(name)` وتحمّل التسعة `load_dev_presentations()`.
- **أدوات:** `target_mask` و`day_baskets` و`next_assessment_gap` (a(d)) و`proximity_bin` (فئات {0–3، 4–7، 8–14، >14} يوماً).

### الحاجز ضد 2014 والقراءة المحدودة وسجل الوصول

الحاجز (D-09) من طبقتين. **الأولى** `assert_allowed(names, allow_confirmatory=False)` ترفع `ConfirmatoryAccessError` لأي اسم من `CONF_PRESENTATIONS`، وترفع `ValueError` لاسم مجهول. تستدعيها `load_presentation` و`role_presentations` وكل محمِّل. و**الثانية** أن الذاكرة المؤقتة نفسها لا تحوي إلا صفوف 2013.

الاستثناء الوحيد (D-47) هو الدالة `confirmatory_student_ids(log_path=None, reader=None)`: تقرأ من `studentRegistration.csv` الأعمدة الثلاثة `code_module` و`code_presentation` و`id_student` وحدها بالمعامل `usecols`، فلا تواريخ تسجيل ولا انسحاب ولا أي جدول آخر، وتعيد مجموعة معرّفات طلاب لهم تسجيل في 2014، لتُحذف تسجيلاتهم من تدريب H4-أ (تفادي تسرب الشخص نفسه بين التدريب والاختبار). الدالة:

1. تكتب سجلاً بحدث `attempt` **قبل** القراءة (ملاحظة N3 من مراجعة الزميل)؛
2. ترفض صراحةً أي قارئ يعيد أعمدة زائدة وتسجّل `failure`؛
3. تكتب `success` مع الزمن وMD5 للملف والأعمدة وعدد المعرّفات و`commit` وعلم `dirty`، في `results/access_log.jsonl`.

ثلاثة اختبارات في `test_splits.py` تتحقق من الأعمدة والسجل ورفض الأعمدة الزائدة وسلامة بقية الحاجز. وفي الملف سجلات التشغيلات الفعلية لـ`learner_analysis` و`build_artifacts` (الصيغة الأقدم سطر واحد لكل قراءة، والأحدث سطران `attempt` و`success`).

## 3.3 `signals.py`: عائلة الإشارة المتداخلة

يحسب الوزن السلوكي لتسجيل u ومورد i عند نهاية التدريب t₀:

W_ui(t₀) = Σ_{d ∈ D_ui} exp(−(t₀−d)/τ) · (1 + β·log1p(c_uid / m_type(i)))

حيث m_type(i) وسيط النقرات اليومية لنوع نشاط المورد محسوباً من فترة التدريب فقط. المستويات المتداخلة: **L0** ثنائي، **L1** عدد الأيام (τ = ∞، β = 0)، **L2** أيام مع حداثة τ، **L3** أيام وحداثة وشدة مطبَّعة بالنوع β.

| العنصر | الوصف |
|---|---|
| `SignalSpec(level, tau, beta)` | dataclass مجمَّد؛ الخاصية `key` تعطي نصاً مثل `L2(tau=14)` أو `L3(tau=28,beta=1)` |
| `TAU_SPACE` | (7، 14، 28، 56، ∞)؛ و`BETA_SPACE` = (0.5، 1، 2)؛ و`ALPHA_SPACE` = (1، 2، 5، 10، 20، 40) |
| `signal_matrix(train, spec)` | مصفوفة كثيفة U×I (float64) للمستوى المطلوب من `TrainData` |

## 3.4 `splits.py`: القطع الزمني والمهمتان A وB بلا تسرب

لكل عرض ونقطة قطع t ∈ {70، 126، 182} (`CUTS`) وأفق 14 يوماً (`HORIZON`) طوران: `tune` (تدريب d ≤ t−14 وتحقق (t−14، t]) و`test` (تدريب d ≤ t واختبار (t، t+14]).

- **`TrainData`** الكائن الوحيد الذي يصل إلى النماذج، من صفوف d ≤ t₀ فقط: `users` و`items` (الكتالوج) و`item_type` والأحداث (`ev_u`، `ev_i`، `ev_d`، `ev_c`) و`seen` (قناع U×I) و`all_events` (كل الأنواع للسياق وملامح المتعلم) و`assessments` و`tiebreak`.
- **`Targets`** للتقييم وحده: `target` و`unreach` (أهداف خارج الكتالوج تُحسب إخفاقاً) و`seen`؛ و`Targets.task("A"|"B")` تعيد (الأهداف، المرشحين، غير القابلة للوصول، المقيَّمين). المهمة A (الأساسية): أهداف = موارد النافذة غير المزارة قبل t₀ ومرشحون = الكتالوج ناقص المزار؛ والمهمة B: كل موارد النافذة والمرشحون كل الكتالوج.
- **`build_train`** يبني منظر التدريب لأي يوم (وتعيد استعماله الخدمة، D-49)، و**`make_fold`** يعيد `(TrainData, Targets)`، و**`check_no_overlap`** يؤكد انفصال التدريب والنافذة.
- **كسر التعادل:** `tiebreak_keys(pres, cut, students, items)` مفاتيح حتمية بدالة splitmix64 **مطابقة لكل النماذج**، فلا يربح نموذج من ترتيب المعرّفات عند التعادل.

## 3.5 `metrics.py`: المقاييس على الكتالوج الكامل

لا سوالب معيَّنة؛ يُرتَّب كل مرشح. `evaluate(scores, cand, tgt, unreach, evaluated, tiebreak, ks=(5,10,20), pop=None)` يعيد لكل متعلم مقيَّم P/R/HR/NDCG/MRR عند كل K، ويعيد Coverage@K وPopBias@K، وتلخّصها `summarize(res, mask=None)`. تفاصيل مهمة: IDCG يحسب `|T_u|` شاملاً الأهداف غير القابلة للوصول؛ و`rank_order` يرفع خطأ عند وجود NaN على مرشح؛ و`popularity_percentile` بمتوسط الرتب عند التعادل. ونسخة مرجعية قائمة على القوائم (`list_metrics`, `coverage`) تُستعمل في الاختبارات للتحقق من النسخة المتجهية على المثال اليدوي (الجدول 19).

## 3.6 واجهة النماذج الموحدة `fit/recommend`

كل نموذج يرث `models.base.Recommender` (نمط Strategy مع Template Method):

```python
model = SomeModel(seed=0, **params).fit(train)          # train: splits.TrainData (d ≤ t0)
S = model.score()                                        # مصفوفة درجات كثيفة U×I
model.recommend(student_id, k=10, exclude_seen=True)     # قائمة id_site
```

- يطبّق الصنف المشتق `_fit` و`_score` ويعلن `param_space()` والخصائص `name` و`stochastic` و`tasks`؛ و`exclude_seen=True` هي المهمة A.
- `grid(**axes)` جداء ديكارتي للإعدادات، و`sample_space(space, budget, name)` عينة ≤ budget ببذرة مشتقة من اسم النموذج.
- السجلات `BASELINES` (B1–B10) و`COMPONENTS` (C6 وC7) يستهلكها الحزام والهجين و`Engine` بلا تعديل.

| المعرّف | الملف | الفكرة | فضاء الإعدادات |
|---|---|---|---|
| B1_Random | `simple.py` | ترتيب عشوائي (مرساة المقياس) | — |
| B2_Pop | `simple.py` | عدد المتعلمين المختلفين على المورد | — |
| B3_RecentPop | `simple.py` | شعبية آخر w يوماً | w ∈ {3، 7، 14، 21، 28} |
| B4_ItemKNN | `knn.py` | تشابه جيب التمام على أعمدة ثنائية مع انكماش | k ∈ {20، 50، 100، ∞}، shrink ∈ {0، 10، 50، 100}، الإشارة |
| B5_SKNN | `knn.py` | جيران من سلال (تسجيل، أسبوع) لمتعلمين آخرين؛ V-SKNN بوزن خطي | L ∈ {1، 3، 7}، k ∈ {50، 100، 200، 500}، M ∈ {1000، 5000، ∞}، variant |
| B6_Markov | `markov.py` | انتقال من الدرجة الأولى بين يومين نشطين متتاليين | γ ∈ {0.01، 0.1، 0.5، 1}، L ∈ {1، 3} |
| B7_WRMF | `wrmf.py` | ALS ضمني (Hu وKoren وVolinsky 2008) | f ∈ {16، 32، 64}، reg ∈ {0.01، 0.1، 1، 10}، α، الإشارة؛ نقاط تفتيش 10/15/25 |
| B8_PersonalRepeat | `simple.py` | W^{L2} الشخصي (للمهمة B فقط) | τ ∈ `TAU_SPACE` |
| B9_CBF | `cbf.py` | ملف المتعلم مقابل سمات المورد (النوع، أسبوع الاستعمال الأول، ملف القرب من التقييم) | أوزان المجموعات الثلاث ∈ {0، 0.5، 1} |
| B10_EASE | `ease.py` | صيغة مغلقة (Steck 2019)، مرجعي فقط | λ ∈ {1، 10، 50، 100، 500} |
| C6_AssessProx | `context.py` | معدل وصول المورد في أيام ذات فئة القرب نفسها من التقييم | — |
| C7_ClusterPop | `context.py` | شعبية المورد داخل عنقود المتعلم (k-means++ يُعاد عند كل t₀) | w ∈ {3، 7، 14، 21، 28} |
| GRU_lite | `gru_lite.py` | شبكة GRU يدوية (§3.7) | lr ∈ {1e-3، 3e-3، 1e-2}، target ∈ {next، next-new} |

**مطابقة مكوّنات الهجين** (وثيقتا الفرضيات والتصميم) مع أسماء الكود:

| رقم المكوّن | الاسم في الكود | ملاحظة |
|---|---|---|
| (1) | `B3_RecentPop` | Recent-Pop؛ B_np\* المرجعي في H1 |
| (2) | `B7_WRMF` | شخصي |
| (3) | `B4_ItemKNN` | شخصي |
| (4) | `B5_SKNN` (S\*)، ومرشحان: `B6_Markov` و`GRU_lite` | خانة واحدة (D-53)؛ و`B5_SKNN` هو مكوّن الأرضية في التركيبة المجمَّدة |
| (5) | `B9_CBF` | شخصي |
| (6) | `C6_AssessProx` | سياقي |
| (7) | `C7_ClusterPop` | سياقي؛ معرّفه في الواجهة `similar_pop` (D-70) |

مساعدات: `baskets.py` يوفّر `day_keys` و`recency_rank` و`last_days_query` (استعلام آخر L أيام نشطة، ثنائي أو خطي) و`week_baskets` و`consecutive_day_transitions`. وWRMF مكتوب بخطوة ALS نصفية `als_half_step` تشكّل مصفوفات المعادلات الطبيعية بضرب مصفوفات واحد لكل كتلة صفوف وتحلّها بـfloat64، وتُستعمل نفسها في «fold-in» عند الخدمة.

## 3.7 GRU-lite

**البنية** (`models/gru_lite.py`، مواصفات D-35): طبقة GRU واحدة بأبعاد d_e = d_h = 64. لكل متعلم متتالية سلال أيام نشطة؛ تمثيل السلة e = متوسط تضمينات موارد الكتالوج فيها، والأيام الفارغة ليست خطوات. البوابات: z = σ(eW_z + hU_z + b_z)، r = σ(eW_r + hU_r + b_r)، h̃ = tanh(eW_h + (r⊙h)U_h + b_h)، h′ = (1−z)⊙h + z⊙h̃، والخرج o = h′V + c (لوجيتات على الكتالوج). الاصطلاح متجه صف، ومصفوفات الأوزان `MATS = (E, Wz, Wr, Wh, Uz, Ur, Uh, V)` والانحيازات `BIASES = (bz, br, bh, c)`.

**التدريب:** خسارة انتروبيا متقاطعة متعددة الوسوم بهدف مطبَّع y = 1[j ∈ S_tgt]/\|S_tgt\| حيث الهدف `next` (السلة التالية) أو `next-new` (التالية ناقص ما زاره)، مع تقنيع الأهداف الفارغة والخطوات المحشوة وعقوبة `L2 = 1e-5` على المصفوفات لا الانحيازات؛ والمُحسِّن `Adam` بقص عام للنظيم `CLIP = 5`؛ والدفعات `BATCH = 128` مخلوطة ببذرة كل حقبة، و`T_BPTT = 20` مع تمرير الحالة بين النوافذ بلا تدرج وحشو بقناع؛ والتهيئة Glorot-uniform لـE وW_* وV ومتعامدة لـU_*؛ والإيقاف المبكر بـ`MAX_EPOCHS = 30` و`PATIENCE = 3` على NDCG@10 (المهمة A) مع الاحتفاظ بأفضل حقبة، ثم يعاد التدريب في طور الاختبار بعدد الحقب نفسه والبذرة نفسها. لا ميزات زمنية. الدوال: `init_params` و`window_loss_grad` (أمامي وخلفي يدوي) و`forward_states` و`train_epoch` و`infer_logits` والأصناف `Adam` و`Sequences` و`GRULite`.

**فحوص الصحة** (`experiments/gru_sanity.py` ← `results/dev2013/gru_sanity.md`): S1 فحص تدرج بالفروق المحدودة (ε = 1e-5، ≥ 20 إحداثية لكل مصفوفة، المعيار خطأ نسبي < 1e-4، المقيس 4.28e-6)، S2 فرط ملاءمة 32 تسلسلاً (L − H ≤ 0.05 nat؛ المقيس 0.0012 وHR@10 تدريب = 1)، S3 سلسلة ماركوف اصطناعية على 50 مورداً (TV ≤ 0.10 ومقارنة NDCG@10 بنموذج ماركوف المقدَّر)، S4 طيّة فعلية بلا NaN وبخسارة نهائية ≤ 0.9 الأولى، S5 انحراف خمس بذور (للإبلاغ فقط: 0.0118، يتجاوز الهدف 0.005 ويُوثَّق)، S6 اختبارات القناع. **البوابة:** `run_gru.py` يرفض العمل (`SystemExit`) ما لم يحمل `gru_sanity.json` الحقل `gates_passed`. وتوثّق `gru_sanity.md` أن أول تشغيل لـS2 فشل (L − H = 0.055) لأن الدفعة احتوت بادئات متطابقة بأهداف مختلفة (حد بايز غير قابل للاختزال)، فصُحّح تصميم الاختبار لا النموذج.

## 3.8 `hybrid.py`: الدمج الرتبي وقاعدة القبول

- **التطبيع:** `rank_normalize(scores, cand)` يحوّل درجات كل مكوّن إلى r̃ ∈ [0,1] داخل مرشحي المتعلم بـ**الرتبة الوسطى عند التعادل** (`mid_ranks`، D-32).
- **الدمج:** `score(u,i) = Σ w_m r̃_m` بأوزان على السمبلكس (`fuse`). `simplex_grid(m, step)`: خطوة 1/4 لمكوّنين أو ثلاثة (5 و15 نقطة) و1/3 لأربعة (20 نقطة)، والخطوة 0.1 حساسية فقط (D-29). `tune_weights` يبحث في الشبكة على التحقق بمقياس NDCG@10.
- **القبول:** `accept_component` يقبل المكوّن إذا استبعد فاصل bootstrap-t (95%) على التسعة رفعَ NDCG@10 على **نوافذ اختبار 2013** الصفر، وتجاوز الرفعُ انحراف البذور للعشوائيات. `greedy_forward` يبحث جشعاً حتى `MAX_COMPONENTS = 4` مع **أرضية الشخصنة** (D-30): إن خلت التركيبة من مكوّن شخصي أُضيف الأكبر رفعاً ووُسم `floor`.

## 3.9 `stats.py`: الاستدلال الإحصائي بـnumpy وحده

وحدة الإحصاء هي العرض (متوسط البذور ثم متوسط الأصول الثلاثة). الدوال العامة:

| الدالة | الوظيفة |
|---|---|
| `cluster_bootstrap_t(diffs, n_boot=10000, seed=0)` | الفاصل المعيَّر t* = (m_b − Δ̄)/(max(s_b,1e-12)/√n)؛ ووسم «منحلّ» وحد ±∞ عند تطابق الفروق (D-52) |
| `sign_flip_test(diffs, exact_max_n=20)` | اختبار قلب الإشارات ثنائي الطرف: إحصاء دقيق على 2ⁿ (8,192 لـn = 13)، أو مونت-كارلو فوق الحد |
| `holm(pvals)` | تصحيح Holm؛ العائلة الثابتة m = 4 = {H1، H2-أ، H3، H4-أ} (D-23) |
| `verdict(mean, lo, hi, p_holm)` | جدول الحكم الأحادي بالأسبقية: مؤكَّدة ← مدحوضة عكسياً ← مدحوضة ← غير حاسمة |
| `verdict_bidirectional(...)` | جدول H3 السداسي: تفوّق مؤكَّد، تأخّر مؤكَّد، تكافؤ، تأخّر، مدحوضة، غير حاسمة |
| `confirmation_power(mu, sigma, n=13, ...)` و`mde80(sigma, n=13, ...)` | قوة التأكيد الكاملة بالقاعدة الأحادية وHolm = 4، وأصغر أثر بقوة 80% (D-46) |

الثوابت: `DELTA = 0.02`، `ALPHA = 0.05`. والمعاملات المسجَّلة قبل التجميد لا تُغيَّر.

## 3.10 `harness.py` و`components.py`

`harness.run_job(p, cut, model_names, exclusion, seeds, tasks)` ينفّذ حلقة «اضبط ثم اختبر»: يضبط كل نموذج على التحقق (≤ `BUDGET = 20` إعداداً بمقياس `NDCG@10`، ببذرة 0)، ثم يعيد التدريب على d ≤ t ويقيّم النافذة بخمس بذور (`SEEDS`) للعشوائيات. الشرائح: `all` و`cold_q1` و`top_q4` و`lt5` (D-28)، ومعها `val_NDCG@10` لفجوة التفاؤل (D-29). نقاط تفتيش WRMF (10، 15، 25) لا تُحسب إعدادات (ADR-004 §2.4). و`eval_rows` يكتب صفوفاً بصيغة `baselines.csv` لأي مصفوفة درجات.

`components.py` ذاكرة درجات المكوّنات: `save_scores` / `load_scores` / `has_scores` تخزّن float32 لكل (عرض، قطع، مكوّن، طور، بذرة) في `data/cache/components/`، و`parse_config` يعكس `harness.config_key`، و`selected_configs` يقرأ الإعدادات المختارة للمهمة A.

## 3.11 `learners.py`: تحليل المتعلمين

- **الملامح:** `vle_features` (M1: `active_days` و`gap_sd` و`first_day` وحصص نقرات 19 نوعاً)، و`total_clicks` (M0)، و`academic_features` (M2 = M1 + الالتزام بالمواعيد ومتوسط الدرجات والمحاولات السابقة وغيرها). لا سمة حساسة (D-21).
- **التجميع:** `kmeans` (k-means++) و`silhouette_fast` و`davies_bouldin` و`adjusted_rand_index`، و`choose_k(X)` بقاعدة §4.7.2: أصغر k في أفضل اثنين لكل من silhouette وDBI مع متوسط ARI ≥ 0.8 على خمس بذور، وإلا أفضل silhouette موسوماً «غير مستقر» (`ClusterChoice.stable`).
- **التصنيف والتقييم:** `logistic_fit` (L2 بنيوتن) و`cart_fit` (جيني، عمق ≤ 4) و`roc_auc` و`average_precision` و`youden_threshold` و`brier`.

`experiments/learner_analysis.py` يشغّلها بترك عرض خارج التدريب داخل 2013 عند الأيام 56 (الأساسي) و28 و112: M0 وM1 وM2، والهدف `final_result ∈ {Fail, Withdrawn}` مقابل `{Pass, Distinction}` باستبعاد المنسحبين قبل القطع، مع حذف المتداخلين مع 2014 (D-47). عتبات Youden: M0 = 0.4744 وM1 = 0.4557 وM2 = 0.4074.

## 3.12 `serving.py`: خدمة إعادة التشغيل (D-49)

الصنف `Engine(frozen=FROZEN, artifacts=ART, presentations=None, student_assessment=None, allow_confirmatory=False, cluster_cache_dir=None)` هو **المكان الوحيد** الذي تُحسب فيه التوصية والتفسير والملف والنظرة العامة (نمط Facade). الشروط التنفيذية لـD-49:

(1) المكوّنات الثقيلة (WRMF وGRU-lite) تأخذ معاملاتها من أقرب قطع c ≤ اليوم في `artifacts/<pres>/<c>/`؛ (2) حالة المتعلم تُحسب عند يوم الطلب (fold-in لـWRMF بخطوة ALS نصفية، أو تمريرة GRU أمامية) بلا تدريب وقت الطلب؛ (3) المكوّنات الخفيفة تُحسب عند اليوم نفسه؛ (4) الأوزان من القطع c في `hybrid_frozen.json`؛ (5) قبل اليوم 70 تُستعمل الخفيفة بأوزان المنوال المعاد تطبيعها مع `note`؛ (6) كل استجابة تحمل `model_cut`؛ (7) لا رقم تقييم يُشتق من إعادة التشغيل.

المعامل `allow_confirmatory` (FR-40) لا يُقبل إلا إذا وُجد `results/conf2014/verdicts.csv` والملف `LOCK` وإلا رُفع `ConfirmatoryAccessError`؛ وبه تُفتح عروض 2014 للإعادة بعد التشغيل التأكيدي وحده. الأساليب العامة:

| الأسلوب | الوظيفة |
|---|---|
| `recommend(name, registration, day, k=10, exclude_seen=True)` | قائمة عناصر لكل منها `id_site` و`activity_type` و`score` (درجة الهجين؛ تسمّيها الخلفية `relevance`، D-70) و`components{m: rtilde, weight, contribution, raw}` و`explanation{main, secondary}` و`model_cut` و`day` و`note` و`known_learner` |
| `learner_profile(name, registration, day, risk_model="M1")` | ملامح وعنقود اليوم 56 ودرجة الخطر، للمدرّس فقط |
| `presentation_overview(name, day, risk_model="M1")` | لوحة المدرّس: المتعلمون النشطون و`median_active_days` وأكثر الموارد استعمالاً وحزم درجة الخطر |
| `cluster_choice_at(name, day)` | اختيار k-means++ عند اليوم t نفسه، مخزَّناً في الذاكرة وفي `data/cache/serving_clusters/<pres>_<day>.npz`، ولا يُخدَم إلا لذلك اليوم (D-68) |
| `warm(name, days=None)` | تسخين درجات المكوّنات (والعنقدة) على شبكة أسبوعية والقطوع؛ ويستدعيه خطّاف التسخين في الخلفية |

وعلى مستوى الوحدة دوال بالأسماء نفسها (`recommend` و`learner_profile` و`presentation_overview` و`registrations` و`warm`) تستدعي `engine()` (مثيل وحيد كسول). **ملاحظة:** نسختا `learner_table` و`cluster_summary` اللتان أُضيفتا مؤقتاً إلى `serving.py` حُذفتا؛ تنفّذهما الخلفية وحدها في `services/instructor.py`.

**مفتاح ذاكرة العنقدة** يضم (عرض، يوم) وبصمة SHA-256 لمنظر التدريب وللبصمة `frozen_fingerprint` (SHA-256 مركَّب لـ`hybrid_frozen.json` و`freeze03_config.json`)، فأي تغيير في التجميد يُبطل العنقدة المخزَّنة. والإعدادات نفسها (`n_init` والبذور وk) بلا تقليص (D-68).

التفسير يأتي من المساهمة الفعلية w_m·r̃_m: يُعرض المكوّن الأعلى مساهمة، والثاني إن تجاوزت ثلث المجموع، بقوالب `TEMPLATES` ودليل `evidence` من `_evidence` (مفتاح C7 هو `similar_learners_in_window` منذ D-70). و`lru_cache` داخل المحرك تحفظ منظر التدريب والدرجات والملامح، فالطلب الأول بلا تسخين ≈ 10 ث ثم أقل من 0.01 ث للمتعلمين الآخرين في اليوم نفسه.

الخطر: `_risk` يعيد **درجة خطر نسبية غير معايَرة** `score` (D-65) من نموذج M1 في أقرب `risk_{28,56,112}.json` ≤ اليوم (مدرَّب على العروض الثمانية الأخرى، `provenance = lopo_2013`، فلا تسرب من العرض المعروض)، مع `threshold` و`threshold_source` و`above_threshold` و`factors` (w·z) و`top_factors`، ولا تقدير قبل اليوم 28؛ ولعروض 2014 يقرأ `_risk_spec` النماذج المجمَّدة من `results/frozen/risk_final.json` (`test_2014`). و`_cluster` يسند التسجيل إلى مراكز اليوم 56 من `clusters_56.npz` ولا يعمل قبل اليوم 56.

**ما نُفِّذ ولم يُقَس في الإنتاج:** مساران في `Engine` لا تمارسهما التركيبة المجمَّدة (C7 وSKNN فقط): `_wrmf_foldin` (خطوة ALS نصفية على عوامل الموارد من `wrmf.npz`) و`_gru_forward` (تمريرة أمامية بمعاملات `gru.npz`). هما منفَّذان ويختبرهما `test_serving.py` بمحرك اصطناعي (`test_wrmf_foldin_uses_artifact_items`) لكنهما لم يُقاسا على بيانات حقيقية ولا يولَّد لهما `artifacts/<pres>/<c>/` حالياً. وهنا `model_cut` هو «تاريخ الأوزان والإعدادات» (القطع الذي أُخذت منه أوزان الهجين وإعداداته) لا تاريخ معاملات مدرَّبة، وفق §1.2 من وثيقة التصميم.

## 3.13 التجارب (`experiments/*`) ومخرجاتها

| الأمر | ما يفعله | المخرجات الرئيسية |
|---|---|---|
| `eda` | إحصاءات وصفية لـ2013 وإعادة إنتاج فحص الزميل 0.2 (FFF_2013J) | `eda.md`، `eda_presentations.csv`، `eda_windows.csv`، `eda_totals.csv`، `eda_peer_repro.csv` |
| `run_baselines` | B1–B10 على 9 عروض × 3 أصول × مهمتين (4 عمليات، `fork`) | `baselines.csv`، `tuning.csv`، `timing.csv`، `folds.csv`، `run_meta.json`، `summary.md` |
| `gru_sanity` | بوابة S1–S6 | `gru_sanity.md`، `gru_sanity.json` |
| `run_gru` | ضبط 6 إعدادات ثم 5 بذور تقرير + حساسية d_h = 128 (على AAA وEEE وGGG) | `gru.csv`، `gru_tuning.csv`، `gru_meta.json`، ودرجات مخزَّنة للهجين |
| `run_ablation` | WRMF وItem-kNN على L0/L1/L2/L3/W* (H2-أ) | `ablation_signals.csv`، `ablation_tuning.csv`، `ablation_meta.json` |
| `learner_analysis` | H4-أ والعناقيد وCART والإنصاف الوصفي | `learner_*.csv`، `learner_analysis.md`، `learner_meta.json` |
| `run_hybrid` | القبول الجشع والتجميد وH1/H3 وصفياً وH4-ب والمهمة B | `hybrid_frozen.json`، `hybrid_acceptance.md`، `hybrid.csv`، `h4b.csv`، `h1_decomposition.csv`، `hybrid_meta.json` |
| `power` | MDE80 لكل فرضية من زوجها الفعلي | `mde80.md`، `mde80.json` |
| `build_artifacts` | قطع الثقيلة لكل قطع، ونماذج الخطر والعناقيد | `artifacts/<pres>/...` |
| `risk_final` | نماذج الخطر النهائية على التسعة (D-58): M0 وM1 وM2 (Logistic L2) وCART على ملامح M2، بعد حذف المتداخلين مع 2014 (D-47)؛ λ والعمق الأدنى للورقة بأعلى متوسط AUC بترك عرض خارج التدريب | `results/frozen/risk_final.json` ونسخة في `artifacts/` |
| `freeze_config` | يجمع كل الخيارات المجمَّدة (فضاءات النماذج والتركيبة والبذور وδ وm والقطوع وE وعتبات Youden وقاعدة k وMD5 للملفات السبعة وSHA-256 للملفات المجمَّدة) | `results/frozen/freeze03_config.json`؛ و`--checklist` يولّد `freeze_checklist.md` |
| `reproduce_dev` | أمر واحد يعيد إنتاج التطوير من ذاكرة فارغة ويقارن بلقطة سابقة (§2.4) | `results/dev2013/repro_diff.md` و`repro_meta.json` |
| `run_confirmatory` | مشغّل E10 بحراسه وطوريه وقفل SHA-256، مع تشغيل جاف على 2013 (§8.4) | `results/conf2014/` أو `results/dryrun2013/` |
| `report` | يعيد توليد `summary.md` من CSV دون إعادة تشغيل (ما زال عنوانه «B1–B9» مع أن B10 موجود في الجداول) | `python3 -m src.ml.experiments.report results/dev2013` |

الوحدة `plots.py` مولّد أشكال SVG بلا matplotlib يكتب مع كل شكل ملف CSV لبياناته، وتخدم أشكال التشغيل التأكيدي المخطط.

خيارات مفيدة: `run_baselines --presentations ... --cuts ... --models ... --workers 4 --exclusion {E5,E4,none} --out DIR` (حساسية E تُكتب إلى `--out` مختلف).

### ملفات `results/dev2013/` ملفاً ملفاً

| الملف | ما يحويه |
|---|---|
| `baselines.csv` | صف لكل (مهمة، نموذج، عرض، أصل، بذرة، شريحة): الإعداد المختار `config` و`val_NDCG@10` والزمن و`n_eval` و P/R/HR/NDCG/MRR عند 5/10/20 وCoverage وPopBias (شريحة `all`) |
| `tuning.csv` | كل إعداد جُرّب في مرحلة الضبط وقيمته على التحقق للمهمتين (`val_NDCG@10_A/B`) |
| `folds.csv`، `timing.csv` | لكل (عرض، أصل): الكتالوج والكثافة والمقيَّمون وحصة غير القابل للوصول؛ والأزمنة وأقصى RSS |
| `run_meta.json` | الأمر و`git_commit` وبصمة البيانات وإصدارات python/numpy/pandas والزمن |
| `gru.csv` | نتائج GRU-lite (النموذجان `GRU_lite` و`GRU_lite_dh128`) بصيغة `baselines.csv` |
| `gru_tuning.csv` | لكل (عرض، قطع، إعداد): أفضل حقبة ومنحنيا الخسارة والتحقق |
| `gru_meta.json`، `ablation_meta.json` | زمن التشغيل وCPU وعدد العمليات (لا معاملات) |
| `ablation_signals.csv`، `ablation_tuning.csv` | الاستئصال بعمود `variant` ∈ {L0، L1، L2، L3، Wstar} |
| `learner_auc.csv`، `learner_h4a_summary.csv` | AUC لكل عرض ونموذج، وملخص H4-أ (Δ ومتوسطات وفاصل وp) |
| `learner_clusters.csv`، `learner_fairness.csv`، `learner_meta.json`، `learner_analysis.md` | العناقيد (k، الاستقرار، الأحجام، الملامح)، والإنصاف الوصفي، وλ وعتبات Youden، والتقرير |
| `hybrid_frozen.json` | **التركيبة المجمَّدة** (§9.1) |
| `hybrid_acceptance.md`، `hybrid.csv`، `hybrid_meta.json`، `h4b.csv`، `h1_decomposition.csv` | الجولات الجشعة، ونتائج الهجين لكل (عرض، قطع)، وH1/H3 وH4-ب والتفكيك (D-60) وصفياً |
| `eda*.csv`، `gru_sanity.*`، `summary.md`، `repro_diff.md`، `repro_meta.json` | الوصف، وبوابة GRU، وجداول المتوسطات، ومطابقة `reproduce_dev` |
| `mde80.md/json` | MDE80 وσ وقوة التأكيد عند δ و1.5δ و2δ لكل فرضية |
| `../access_log.jsonl` | سجل قراءات D-47 (وقراءة 2014 الكاملة في E10) |
| `../frozen/freeze03_config.json`، `risk_final.json`، `freeze_checklist.md` | الإعداد المجمَّد، ونماذج الخطر النهائية، وقائمة شروط التجميد المولَّدة |

## 3.14 `artifacts/`

المجلد **خارج git** (D-70: `.gitignore` يستثني `artifacts/`) ويجب بناؤه بـ`python3 -m src.ml.experiments.build_artifacts` (≈ دقيقة) قبل أول تشغيل للخادم. يحوي `artifacts/<presentation>/` الملفات `risk_{28,56,112}.json` (نموذجا Logistic M1 وM2 بـ`features` و`weights` و`lambda` و`youden_threshold` و`threshold_source` و`provenance = lopo_2013` و`trained_on`: العروض الثمانية الأخرى)، وعتبة اليوم 56 هي العتبة المجمَّدة في D-58، أما عند 28 و112 فعتبة Youden مجمَّعة من التنبؤات خارج الطيّة للعرض فقط (D-65)؛ و`clusters_56.npz` (المراكز `centres` ومعاملات `mu` و`sd` و`k` و`stable` و`features` و`students` و`labels`)؛ ومجلدات القطوع `70/` و`126/` و`182/` التي تحمل `wrmf.npz` و`gru.npz` إن دخل أحدهما التركيبة المجمَّدة (فارغة اليوم لأن C7 وSKNN خفيفان). ويُنسخ إلى جذر `artifacts/` الملف `risk_final.json`. الحجم الكلي ≈ 0.5 MB، وغيابها يعطي 503 `artifacts_missing`.

# 4. وحدة `src/backend`

## 4.1 المعمارية

الخلفية غلاف رفيع حول `serving.Engine`: تحلّل المدخلات، وتحوّل مخرجات المحرك إلى عقود pydantic مطابقة لملفات `src/frontend/mock/*.json`، وتوحّد الأخطاء، وتخدم `src/frontend/dist/`. **لا حساب توصية خارج `Engine`**، ولا تخزين لحالة متعلم، ولا مصادقة ولا جمع حي (D-22)، ولا أرقام تقييم. الأنماط الثلاثة المستعملة:

| النمط | أين | الدور |
|---|---|---|
| **Factory** | `create_app(settings=None, engine=None)` في `app.py` | يبني تطبيق Starlette قابلاً للتكوين، فيركّب الاختبار محركاً أو إعدادات مختلفة |
| **Facade** | `ReplayService` و`ExplanationService` و`InstructorService` فوق `Engine` | تحويل مخرجات المحرك إلى عقود الاستجابة |
| **Repository** | `Repository` في `repository.py` | الوصول إلى البيانات: فهارس أحداث العروض، وكتالوج العروض (أطوال وتقييمات وعدد التسجيلات بلا أحداث)، وbصمة git والبيانات، وفحص إتاحة العرض |

ويضاف **DTO** (نماذج `schemas.py`) و**حقن بسيط** في الحاوية `Services` التي تُمرَّر إلى المسارات بالإغلاق.

```
src/backend/
  __main__.py  app.py (create_app, Services, TimingMiddleware, FrontendFiles)
  settings.py  errors.py  schemas.py  repository.py  bench.py
  routes/    meta.py  learner.py  instructor.py  common.py
  services/  replay.py  explanation.py  instructor.py  labels.py
  tests/     asgi_client.py  test_contract_no_risk.py  test_contract_json.py
             test_static_errors.py  test_api_live.py
  e2e/       live-screenshots.js
```

كل معالج `async` يشغّل العمل المتزامن في خيط عبر `run_in_threadpool` (الدالة `routes.common.respond`)، فلا يحجب `/api/health` أثناء الحساب البارد، وقفل `RLock` واحد حول `Engine`. ومعالج الأخطاء `respond` يحوّل `ApiError` و`ValidationError` و`ConfirmatoryAccessError` (إلى 409) و`FileNotFoundError` (إلى 503) وأي استثناء آخر (إلى 500 `internal_error` مسجَّلاً) إلى الصيغة الموحدة. `TimingMiddleware` يضيف الترويستين `Server-Timing` و`X-Response-Time-ms` للقياس.

## 4.2 المسارات (11 مساراً كلها GET)

| المسار | المعاملات | ما يعيده |
|---|---|---|
| `/api/health` | — | `status` و`run_id` و`uptime_s` و`instructor_enabled` و`warm` (الحالة: `idle\|pending\|running\|done\|failed`) |
| `/api/meta` | — | الإصدار و`git_commit` و`git_dirty` و`freeze_tag` و`data_fingerprint` (MD5 لـ`oulad_md5_reference.txt`) و`data_files` و`components` (الأوزان الأولية المجمَّدة) و`cutoffs` = [70،126،182] و`risk_cutoffs` = [28،56،112] و`snapshot_grid` و`presentations` و`risk_score` |
| `/api/presentations` | — | 9 عروض 2013 `published` + عرض 2014 واحد `locked` للتمثيل (طوله وتسجيلاته 0) |
| `/api/registrations` | `presentation`، `q`، `limit≤100`، `offset`، `day` | قائمة بيضاء `registration` و`id_student` و`date_registration` و`status` (`ok\|no_history\|withdrawn` تُحسب عند `day` إن مُرّر) |
| `/api/recommendations` | `registration`، `day`، `k` 1..20، `task=A\|B` | `items[{rank,id_site,activity_type,relevance,contributions,reason,reason_secondary}]` و`components` و`context` و`provenance` (والاسم `relevance` لا `score`: D-70 (4)، فالمفتاح `score` محجوز لدرجة الخطر في مسارات المدرّس) |
| `/api/explanations/{reg}/{id_site}` | `day`، `task` | `relevance` ومكوّنات `{weight, r_tilde, contribution, evidence, sentence}`؛ 404 `item_not_in_list` لمورد خارج أفضل 20 |
| `/api/learner/{reg}/history` | `day`، `window` (28) | `daily` و`recent` (3) و`active_days` |
| `/api/instructor/overview` | `presentation`، `day` | مؤشرات وملخص الملامح ومدرج الخطر والتغطية |
| `/api/instructor/clusters` | `presentation`، `day` | k و`cluster_day` (= 56، لقطة العناقيد) و`unstable` و`unstable_reason` والجودة (`ari` يقبل null إن غاب العرض من `learner_clusters.csv`) وأحجام ووصف عربي حتمي وإسقاط PCA |
| `/api/instructor/learners` | `presentation`، `day`، `cluster`، `risk=all\|above`، `sort`، `limit≤500`، `offset` | `{items,total,limit,offset}` |
| `/api/instructor/learner/{reg}` | `day` | العنقود والخطر بعوامل w·z والملامح مقابل الوسيط وأفضل 3 توصيات و`withdrawn_day`؛ **بلا أي حقل نتيجة نهائية** (حُذف `outcome` من العقد) |

**`provenance {run_id, role, model_cut}`** موجود في كل استجابة بيانات (التوصية والتفسير وسجل النشاط والنظرة العامة والعناقيد وصفحة المتعلمين وملف المتعلم)، ويفرضه الثابت `schemas.PROVENANCE_MODELS` ويفحصه اختبار العقد (D-49 (6)). صيغة `registration` = `^[A-G]{3}_20(13|14)[BJ]-\d+$` وتُحلَّل إلى (العرض، `id_student`). والمهمة الافتراضية A (موارد جديدة) لأن التوصية إرشاد إلى ما لم يُكتشف بعد.

## 4.3 أمثلة طلب/استجابة من التشغيل الفعلي

كل ما يلي ناتج تشغيل الخادم على FFF_2013J (`--warm`) في 2026-10-25. **توصية:**

```
$ curl 'localhost:8000/api/recommendations?registration=FFF_2013J-371869&day=75&k=2'
{"registration":"FFF_2013J-371869","presentation":"FFF_2013J","id_student":371869,
 "requested_day":75,"snapshot_day":75,"task":"A","status":"ok","known_learner":true,"note":null,
 "context":{"week":11,"next_assessment":{"type":"TMA","day":96,"days_ahead":21},"active_days_to_date":93},
 "components":[{"id":"similar_pop","label":"شعبية الأنماط المشابهة (7)","weight":0.75},
               {"id":"sknn","label":"SKNN (4)","weight":0.25}],
 "items":[{"rank":1,"id_site":716344,"activity_type":"oucontent","relevance":0.9963,
           "contributions":{"similar_pop":0.75,"sknn":0.2463},
           "reason":"شائع لدى متعلمين بنمط مشابه لنمطك","reason_secondary":null}, ...],
 "provenance":{"run_id":"replay-dev2013-0e2547b627","role":"dev","model_cut":70}}
```

**التفسير** (`/api/explanations/FFF_2013J-371869/716344?day=75`): مكوّنان بـ`evidence` من نوع `count` (85 متعلماً مشابهاً في نافذة 3 أيام) أو `item` (المورد 716219 زاره المتعلم 67 يوماً). **جدول المتعلمين** (للمدرّس):

```
$ curl 'localhost:8000/api/instructor/learners?presentation=FFF_2013J&day=75&sort=-risk&limit=1'
{"items":[{"registration":"FFF_2013J-590714","cluster":{"id":0,"label":"أيام نشطة قليلة · نشاط متقطع"},
  "active_days":1,"last_access_day":-7,"on_time":"0/2",
  "risk":{"score":0.998553,"cut_day":56,"threshold":0.455716,"above_threshold":true,
          "provenance":"lopo_2013","top_factor":"حصة page"}}],"total":1872,"limit":1,"offset":0,
 "provenance":{"run_id":"replay-dev2013-0e2547b627","role":"dev","model_cut":70}}
```

الدرجة والعتبة بست منازل عشرية والتقريب للعرض فقط في الواجهة، فيكون حكم `above_threshold` واحداً في الخادم والعارض. **التفسير:** الحقل `relevance` بدل `score`، وبعد `components` الحقلان `notes` و`provenance`. قبل أول قطع (اليوم 40): `model_cut: null` و`note` يشرح الرجوع إلى المكوّنات الخفيفة («اليوم 40 قبل أول قطع (70): لا مكوّن ثقيل…»).

## 4.4 صيغة الأخطاء، و409 لعروض 2014

كل خطأ بالصيغة `{"error": {"code", "message", "details"}}` ورسالة عربية ورمز ثابت، مع `Cache-Control: no-store`:

| HTTP | الرمز | الحالة |
|---|---|---|
| 404 | `presentation_not_found`، `registration_not_found`، `item_not_in_list`، `instructor_disabled`، `not_found` | معرّف غير موجود، أو مورد خارج أفضل 20، أو تشغيل بـ`--no-instructor`، أو مسار مجهول |
| 405 | `method_not_allowed` | أي طريقة غير GET |
| 409 | `confirmatory_locked` | أي عرض 2014، على **كل** المسارات |
| 422 | `validation_error` (مع `details.errors[{field, reason, type}]`) | مدخلات غير صالحة، مثلاً `day` > 400 أو `registration` بصيغة خاطئة |
| 422 | `day_out_of_range` (`details.max_day`) | اليوم أكبر من طول العرض |
| 422 | `day_before_first_snapshot` (`details.first_day = 56`) | المدرّس قبل اليوم 56 (أول عنقدة). **قرار D-74:** يبقى 422 (لا 404 ولا استجابة جزئية) وهو سلوك موثَّق، والواجهة تنقل الشريط تلقائياً |
| 503 | `artifacts_missing` | `hybrid_frozen.json` أو مخرجات القطوع غير موجودة |

حاجز 2014 هنا بطبقتين فوق حاجز `src/ml`: `Repository.check_presentation` يرفع 409 **قبل أي قراءة** لأي اسم من `CONF_PRESENTATIONS`، ومعالج `ConfirmatoryAccessError` يحوّل الاستثناء المقابل إلى 409 أيضاً. ويعرض `/api/presentations` عرضاً مقفلاً واحداً (BBB_2014J) للتمثيل بتسجيلات وطول 0، فلا يُقرأ شيء من 2014.

## 4.5 التسخين والكاش والأداء المقاس

التسخين (`--warm`) خيط خلفي يشغّل `Services.run_warmup`: يبني قوائم العروض، ثم يستدعي الخطّاف `serving.warm(presentation, days)` (D-68) إن وُجد، ثم لأول تسجيل في العرض الافتراضي (FFF_2013J) يحسب التوصية (ولقطة المدرّس إن كان اليوم ≥ 56) لكل يوم في `--warm-days` (الافتراضي `settings.WARM_DAYS` = 75، 56، 70، 112، 126، 182)، ويدعم `--warm-weekly` شبكة أسبوعية. وأي `--host` غير 127.0.0.1 يطلق تحذيراً لغياب المصادقة (D-66: عرض توضيحي بلا أمان وصول؛ ويظهر `bind_host` و`access_notice` في `/api/meta`). فشل التسخين تحسيني ويُسجَّل `failed` في `/api/health` ولا يوقف الخدمة. الذاكرات: LRU للتوصيات (1024 قائمة من 20)، ولقطات المدرّس (6)، و`lru_cache` داخل `Engine`، وعنقدة الخدمة الدائمة. وهي ذاكرات لا مصدر حقيقة: مسحها لا يغيّر أي ناتج.

**ظروف القياس:** `python3 -m src.backend.bench` على خادم مسخَّن، 20 طلباً لكل مسار، FFF_2013J، اليوم 75، commit `85a0376`، 2026-10-25، آلة 4 أنوية (Xeon 2.10GHz، Python 3.13.17). يختلف الوسيط قليلاً عن README (مثلاً `explanations` 23.3 ms هنا مقابل 17.3 ms) لأنه قياس مستقل، ويضيف الجدول p95 المطلوب في NFR-01:

| المسار | الأول (ms) | الوسيط (ms) | p95 (ms) | الأقصى (ms) |
|---|---|---|---|---|
| health | 1.0 | 0.8 | 1.0 | 1.0 |
| meta | 2.0 | 1.6 | 1.8 | 1.9 |
| presentations | 1.6 | 1.5 | 2.0 | 5.5 |
| registrations (100) | 2.4 | 2.6 | 3.1 | 3.3 |
| recommendations | 8.3 | 6.0 | 6.7 | 8.8 |
| explanations | 32.0 | 23.3 | 31.4 | 35.6 |
| history | 8.3 | 6.1 | 11.2 | 11.3 |
| instructor/overview | 1.4 | 1.5 | 1.7 | 2.5 |
| instructor/clusters | 3.6 | 3.2 | 3.5 | 3.5 |
| instructor/learners (100) | 7.2 | 6.4 | 11.2 | 11.2 |
| instructor/learner | 2.4 | 1.9 | 2.1 | 2.1 |

كلها ≪ 200 مللي ثانية في p95 (NFR-01، ويفرضه `test_latency_after_warmup`). **زمن التسخين:** ≈ 25 ثانية (الخطّاف ≈ 14 ث، ثم الأيام الستة بين 0.6 و4.1 ث) والعنقدة مخزَّنة على القرص، و≈ 61 ثانية في أول تشغيل بعد تغيّر بصمة التجميد؛ وقياس README (≈ 36 ث، 2026-10-24) بينهما. **بلا تسخين:** أول `recommendations` ≈ 10.3 ث وأول `instructor/overview` ≈ 11 ث (README)، ويوم غير مسخَّن ≈ 10 ث. ولا يجوز تقليص `n_init` أو البذور أو k لتسريع الطلب البارد (D-68).

## 4.6 الاختبارات والعميل ASGI المدمج

`tests/asgi_client.py` عميل ASGI صغير بلا httpx: يبني `scope` ويستدعي `await app(scope, receive, send)` مباشرة ويعيد `Response(status, headers, body)` مع `.json()` و`.text`، ويغلّفه `Client.get(url)`. المجموعات الست وأعدادها في §7.1: `test_contract_no_risk` (العقد على النماذج: لا خطر ولا عنقود ولا سمات حساسة في نماذج المتعلم، وقائمة بيضاء للمدرّس، وغياب حقول أرقام التقييم و`outcome`، ووجود `provenance` في `PROVENANCE_MODELS`)، و`test_contract_json` (العقد على JSON المسلسَل فعلياً، D-70)، و`test_static_errors` (الأخطاء الموحدة و409 و`--no-instructor` والملفات الثابتة؛ بلا بيانات)، و`test_text` (صيغ العدد العربية وحذف أرقام القرارات من نصوص المستخدم؛ بلا بيانات)، و`test_labels_js` (يشغّل `labels.js` المبني بـnode ويقارن `countAr` و`fmt`؛ يُتخطّى إن غاب node أو `dist/`)، و`test_api_live` (يقارن مفاتيح كل استجابة بملف mock ويفحص المنطق والتطابق مع `Engine` والأداء؛ يُتخطّى إن غابت البيانات).

# 5. وحدة `src/frontend`

## 5.1 البنية والبناء

واجهة عربية RTL بلا أي اعتماد خارجي: TypeScript (`tsc` وحده) وHTML وCSS خالص وSVG. `tsconfig.json`: الهدف ES2020 وحدات ES2020 و`moduleResolution: bundler` ووضع `strict` مع `noUnusedLocals` و`noImplicitReturns`، والإخراج في `dist/js`. السكربت `build.sh` يحذف `dist/` ويشغّل `tsc -p tsconfig.json` وينسخ `*.html` و`styles/*.css` و`mock/*.json` إلى `dist/`. المجلد `dist/` مدرج في `.gitignore`.

```
index.html learner.html instructor.html about.html
src/   api.ts state.ts types.ts dom.ts labels.ts controls.ts
       home.ts learner.ts instructor.ts about.ts
       components/  DayScrubber RecCard WhyPanel KpiCard charts DataTable Drawer feedback Header
styles/ tokens.css base.css components.css          mock/*.json (11 ملفاً)
build.sh  tsconfig.json  screenshots.js
```

## 5.2 المكوّنات

| الملف | يصدّر | الدور |
|---|---|---|
| `labels.ts` | `typeAr`، `countAr`، `daysAr`، `learnersAr`، `itemsAr`، `fmt`، `range`، `pct`، ألوان المكوّنات والعناقيد | `countAr` يطبّق صيغة العدد العربية (1 «يوم واحد»، 2 «يومان»، 3–10 «أيام»، 11+ «يوماً»)؛ و`fmt` يكتب الأعداد بعلامة طرح حقيقية U+2212 وبلا «−0» ويعزل السالب باتجاه LTR (LRI…PDI)، و`range` يكتب «a – b» كتلة LTR واحدة |
| `dom.ts` | `h`، `s` (SVG)، `mount`، `clear`، `bdi`، `$` | مساعدات DOM صغيرة بلا إطار؛ `bdi` يعزل المعرّفات اللاتينية داخل نص RTL |
| `controls.ts` | `presentationSelect`، `makeScrubber`، `registrationPicker` | عناصر التحكم المشتركة بين الصفحات |
| `components/DayScrubber.ts` | `DayScrubber` | شريط اليوم: `input[type=range]` أصلي مع حقل رقمي وأزرار اللقطات ومواعيد التقييم |
| `components/RecCard.ts` | `RecCard`، `CompLegend` | بطاقة توصية بشارات المكوّنات وزر «لماذا؟» |
| `components/WhyPanel.ts` | `WhyPanel`، `evidenceText` | لوحة التفسير: مساهمة كل مكوّن ونص الدليل |
| `components/charts.ts` | `SvgBarChart`، `SvgHBars`، `SvgDonut`، `ClusterScatter`، `DivergingBars`، `AltTable` | رسوم SVG مع `role="img"` وجدول بيانات بديل |
| `components/DataTable.ts`، `Drawer.ts`، `KpiCard.ts`، `feedback.ts`، `Header.ts` | جدول مرتّب بلوحة المفاتيح، ودرج جانبي، وبطاقة مؤشر، وToast والهيكل والفراغ والخطأ، والترويسة | عناصر مساعدة |

## 5.3 عميل API ووضع المحاكاة

`api.ts` يصدّر الكائن `api` بدالة لكل مسار (`health`، `meta`، `presentations`، `registrations`، `recommendations`، `explanation`، `history`، `overview`، `clusters`، `learners`، `learner`)، وكلها تمر على `pick(livePath, mockFn)`. `initApi()` يكشف الوضع: يجرّب `GET /api/health` بمهلة 2.5 ث، فإن فشل أو لم يعد JSON فيه `status` اختار **المحاكاة**. وتُفرض المحاكاة بـ`?mock=1` (تُحفظ في `sessionStorage`) وتُلغى بـ`?mock=0`، وتظهر وسم «وضع المحاكاة» في الشريط العلوي. الخطأ الحي يتحول إلى `ApiError(status, code, message, details)` من جسم الخطأ الموحد.

في المحاكاة يقرأ `mockFile` ملفات `mock/*.json` عبر مسار نسبي، ويطبّق منطق الخادم الأساسي: أخطاء 404/409/422 (منها `day_before_first_snapshot` مع `first_day`، و`confirmatory_locked`)، وحل اليوم t إلى اللقطة s ≤ t، و`model_cut`، والأسبوع والتقييم القادم، والفرز والتصفية والترقيم لجدول المتعلمين. بيانات المحاكاة لعرض BBB_2013J، وتُعاد تسمية بادئة المعرّف لغيره. الأرقام فيها اصطناعية للعرض لا للتقييم (D-49). أما `types.ts` فيعكس عقود الاستجابة حقلاً بحقل، ويتحقق `test_api_live` من مطابقة مفاتيح الخادم لملفات `mock/`.

## 5.4 إدارة الحالة في URL، وRTL وإمكانية الوصول

الحالة كلها في الرابط (`state.ts`: `readState` و`writeState` و`carryQuery`): `p` العرض، `r` التسجيل، `d` اليوم، `task`، `cl` العنقود المصفّى، `f` (all|above|idle)، `sort` (مثل `-risk`). تُحذف القيم الافتراضية، فيمكن مشاركة أي منظر بنسخ الرابط. و`learner.ts` يستعمل عدّاد طلبات `seq` لتجاهل الاستجابات المتأخرة.

الواجهة **مصمَّمة** لتوافق WCAG 2.2 AA و**لم يُقَس التوافق آلياً** (لا سكربت تباين؛ NFR-22 غير منفَّذ، والتباين المذكور محسوب من رموز `tokens.css` لا مقيس): `lang="ar" dir="rtl"` وخصائص CSS المنطقية، وتباين نص ≥ 4.5:1 وحدود ≥ 3:1 بالحساب، ولا اعتماد على اللون وحده (أسماء وأشكال وإطار متقطع ونص «فوق العتبة»)، ولوحة المفاتيح كاملة (Esc يغلق «لماذا؟» والدرج ويعيد التركيز)، وأهداف لمس ≥ 44px، و`aria-live` و`aria-busy` و`aria-sort`، و`prefers-reduced-motion`، وبلا تمرير أفقي من 360px. وواجهة المتعلم بلا خطر أو عنقود (NFR-09) ولا سمات حساسة (D-21)؛ ويعرض `instructor.ts` الحقل `risk.score` بعنوان «درجة الخطر النسبية» (D-65)، و`labels.ts` معرّف المكوّن السابع `similar_pop` (D-70).

## 5.5 لقطات الشاشة وكيف تُولَّد

سكربتان بـPlaywright العالمي (`NODE_PATH=$(npm root -g)`):

- `src/frontend/screenshots.js` (بوضع المحاكاة): يخدم `dist/` على المنفذ 8765 ويلتقط ست لقطات لسطح المكتب (1440×900) والجوال (375×800)، ويفحص التمرير الأفقي وأخطاء الكونسول، ويكتب إلى `src/frontend/screenshots/mock/` (في git). يتطلب `build.sh` قبله.
- `src/backend/e2e/live-screenshots.js`: لقطات مع الخادم الحي باسم `live-*.png` في `deliverables/05-user-guide/screenshots/`، بعد `python3 -m src.backend --warm`. **قاعدة D-73:** يُختار متعلم اللقطات برمجياً من صفحة الجدول المعروضة (مفروزة بالتسجيل، أول 100 صف): الأقرب إلى وسيط درجات الفوج كله بشرط درجة دون العتبة و≥ 5 أيام نشطة، والتعادل بترتيب التسجيل؛ فإن زاد الفرق عن 0.05 يُفتح الجدول بمعامل `off` عند صفحة أقرب متعلم مؤهَّل، ويطبع السكربت معرّفه ودرجته وفرقه. و`CHECK_ONLY=1` يجري الفحوص دون كتابة لقطات.

# 6. أدوات البناء `scripts/`

| الأداة | الأمر | الوظيفة |
|---|---|---|
| `build_docx.py` | `python3 scripts/build_docx.py OUT.docx IN.md [--title ... --title-en ... --subtitle ...]` | Markdown ← Word RTL: يمرّ على pandoc بـ`-M lang=ar -M dir=rtl` وفهرس بعمق 3، ثم يعالج python-docx الخطوط (Simplified Arabic وTimes New Roman) والفقرات والجداول RTL، ويحمي الرموز المتماثلة من الانعكاس، ويضيف غلافاً وترقيم صفحات، ثم يمرّر الملف على `lo_update_toc.py` ما لم يُعطَ `--no-update-toc`. أنماط الشيفرة (`Source Code` و`Verbatim Char` و`SourceCode`) تُستثنى من RTL فتبقى LTR، ويُستعمل خط العربية للنص المركّب داخل كتل الشيفرة فتظهر التعليقات العربية مشكَّلة، ويُحاط الشيفرة المضمَّنة (المسارات والمعرّفات والخيارات) بعلامة LRM لتبقى جزيرة LTR واحدة داخل النص RTL |
| `lo_update_toc.py` | `python3 scripts/lo_update_toc.py file.docx [...]` | يفتح الملف في LibreOffice عبر UNO ويحدّث الفهارس ويحفظ docx، لأن pandoc يكتب الفهرس حقلاً فارغاً لا يملؤه إلا Word عند الفتح |
| `svg2png.js` / `svg2png.py` | `node scripts/svg2png.js in.svg [--out-dir DIR --scale 2 --width 1400]` | تصيير SVG أو HTML إلى PNG بـPlaywright (Node) وChromium؛ والنسخة `.py` غلاف يستدعي `.js` |
| `build_pptx.py` | `python3 scripts/build_pptx.py [--spec X.json --out Y.pptx]` | مولّد العرض التقديمي بـpython-pptx من مخطط `docs/working/07-presentation.json`: شرائح RTL بنسبة 16:9 وأنواع عنوان وبطاقات وإحصاءات وتدفق وجدول ومخطط وأسئلة |

أمر بناء هذا الملف نفسه:

```
python3 scripts/build_docx.py "deliverables/04-code-documentation/توثيق-الكود-البرمجي.docx" docs/working/04-code-documentation.md --title "توثيق الكود البرمجي" --title-en "Source Code Documentation" --subtitle "نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم — المرحلة الرابعة"
```

# 7. الاختبارات

## 7.1 مجموعات الاختبار ونتائجها الفعلية

كلها `unittest` من المكتبة القياسية. **الأعداد مقيسة في 2026-10-25 على commit `85a0376` (لا فرق في `src/` حتى `2d86082`)، 4 أنوية**؛ وعدّها مأخوذ من تشغيل `discover` نفسه لا من README:

| المجموعة | الملف | العدد | ما تغطيه |
|---|---|---|---|
| ML: GRU | `test_gru.py` | 7 | المثال العددي 4.4.2، فحص التدرج، القناع والتقطيع، الأهداف، قص Adam |
| ML: الهجين والإحصاء | `test_hybrid_stats.py` | 20 | الدمج الرتبي (الجدول 14)، السمبلكس، القبول والجشع والأرضية، قلب الإشارات وHolm وbootstrap-t، جداول الحكم، الهامش والقوة، الانحلال |
| ML: المتعلمون | `test_learners.py` | 10 | k-means++ ومقاييس الجودة، Logistic وجيني وAUC/AP/Youden، الملامح |
| ML: المقاييس | `test_metrics.py` | 9 | الجدول 19 يدوياً، المتجه = المرجعي، المثالي = 1، HR النظري للعشوائي، التعادل، IDCG |
| ML: النماذج | `test_models.py` | 23 | أمثلة B4–B10 وC6 وC7 العددية، وفضاءات ADR-004، وواجهة `recommend` |
| ML: الخدمة | `test_serving.py` | 13 | الخطة قبل أول قطع، عدم استعمال المستقبل، fold-in، الملف والنظرة العامة، رفض 2014 وFR-40، العنقدة المخزَّنة، الخطر |
| ML: الإشارة | `test_signals.py` | 7 | الجدول 8، تداخل المستويات، وسيط النوع من التدريب وحده، الثقة الثنائية |
| ML: التقسيم | `test_splits.py` | 14 | النوافذ والتسرب، الكتالوج، المهمتان، مفاتيح التعادل، حاجز 2014، قراءة D-47 |
| ML: التجميد | `test_confirmatory.py` | 11 | حراس `run_confirmatory` و`verify_lock`، تدقيق قراءة 2014، جدول الأحكام وH3 المتعذرة، التدريب القابل للنشر |
| **مجموع ML** | `python3 -m unittest discover -s src/ml/tests` | **114** | ناجحة، ≈ 4 ثوانٍ، بلا البيانات الخام |
| الخلفية: العقد | `test_contract_no_risk.py` | 6 | نماذج المتعلم بلا خطر ولا عنقود ولا سمات حساسة، لا `outcome`، `provenance` في `PROVENANCE_MODELS` |
| الخلفية: الأخطاء والثابت | `test_static_errors.py` | 9 | الصحة، 404، 405، 409 لـ2014 على كل المسارات، 422، `--no-instructor`، الجذر يخدم `index.html` |
| الخلفية: النصوص | `test_text.py` | 7 | صيغ العدد العربية وحذف أرقام القرارات من نصوص المستخدم (بلا بيانات) |
| الخلفية: صيغ الواجهة | `test_labels_js.py` | 2 | تشغيل `labels.js` المبني بـnode ومقارنة `countAr` و`fmt` (تُتخطّى إن غاب node أو `dist/`) |
| الخلفية: JSON المسلسَل | `test_contract_json.py` | 6 | D-70: لا مفاتيح محظورة في JSON المتعلم، التسجيلات بلا `date_unregistration` و`final_result`، تسمية دليل C7، قائمة بيضاء للمدرّس |
| الخلفية: الحي | `test_api_live.py` | 22 | العقود مقابل mock، المنطق، التطابق مع `Engine`، الأداء بعد التسخين (تحتاج البيانات) |
| **مجموع الخلفية** | `python3 -m unittest discover -s src/backend/tests -t .` | **52** | ناجحة، ≈ 24-120 ثانية (بحسب العنقدة المخزَّنة) |
| الواجهة | `tsc --noEmit -p tsconfig.json` | — | فحص أنواع strict؛ خرج 0. لا اختبارات DOM آلية |

## 7.2 المخرجات المسجَّلة وقت الكتابة

```
$ python3 -m unittest discover -s src/ml/tests
Ran 114 tests in 4.190s       OK
$ python3 -m unittest src.backend.tests.test_contract_no_risk src.backend.tests.test_static_errors
Ran 15 tests in 0.111s        OK        (السريعة، بلا بيانات)
$ python3 -m unittest discover -s src/backend/tests -t .
Ran 52 tests in 24.001s       OK
$ python3 -m unittest discover -s src/backend/tests
Ran 18 tests ... FAILED (errors=3)      (بلا -t . : خطأ استيراد نسبي)
$ cd src/frontend && npx tsc --noEmit        # exit code 0
$ python3 -m src.backend --help               # يطبع الخيارات المذكورة في §2.5
```

اختبارات `src/ml` لا تكتب في `results/access_log.jsonl` الحقيقي (تستعمل مجلداً مؤقتاً وقارئاً وهمياً).

## 7.3 ما لا تغطيه الاختبارات

لا اختبار آلي لسلوك المتصفح (DOM)؛ يُغطّى بفحص الأنواع وبلقطات Playwright. ولا اختبار لمسار 2014 الفعلي في `run_confirmatory` لأنه لم يُشغَّل بعد (تغطّي الحراس اختبارات `test_confirmatory`).

## 7.4 تناقضات رُصدت بين README والكود (حتى commit `2d86082`، 2026-10-25)

أُصلح كثير مما ورد في النسخة الأولى (عدد الاختبارات، M1 بدل M2، الأمر الواحد، `probability`، مواضع `learner_table`)، وبقي ما يلي:

| # | README / الوثيقة تقول | الكود/التشغيل يقول | الأثر |
|---|---|---|---|
| 1 | `src/ml/README.md`: `artifacts/` «≈ 0.5 MB، في git» | `.gitignore` يستثني `artifacts/` وD-70 يقول «خارج git»؛ ولا ملف منها متتبَّع | نص README قديم؛ المرجع `.gitignore` |
| 2 | `src/ml/README.md` وجدول الأزمنة: `run_baselines` «5.2 دقائق» | `results/dev2013/run_meta.json` الحالي: 473.5 ث ≈ 7.9 دقيقة (commit `d820bce`، 2026-10-24) | الرقم الأول من تشغيل الجولة الأولى؛ يُعتمد 7.9 |
| 3 | أمر `discover -s src/backend/tests` (مع `-k` أو بدونه) | يفشل بلا `-t .` (3 أخطاء استيراد) | يُستعمل `-t .` أو أسماء الوحدات الكاملة |
| 4 | `gru_meta.json` و`ablation_meta.json` مصدر للمعاملات | يحويان الزمن وعدد العمليات فقط | المعاملات من الكود ومن `gru.csv` و`ablation_tuning.csv` (§9.1) |
| 5 | README الخلفية: التسخين «≈ 36 ث» | 25 ث (عنقدة مخزَّنة) و61 ث (أول تشغيل بعد تغيّر بصمة التجميد)، قياس 2026-10-25 | يتوقف الزمن على حالة الذاكرة الدائمة |
| 6 | قائمة README الـml: ش5 وش7 «✗» | `reproduce_dev.py` و`run_confirmatory.py` موجودان، لكن نتيجتا التشغيل لم تُسجَّلا بعد | تُستكمل (§8.4) |
| 7 | `git tag -l` | فارغ؛ `/api/meta.freeze_tag` = null | الوسم `freeze-03` لم يوضع بعد (ش10) |

# 8. قابلية إعادة الإنتاج والحتمية

## 8.1 البذور

- **بذور التقرير:** `harness.SEEDS = (0,1,2,3,4)` للنماذج العشوائية (B1 وWRMF وGRU-lite وC7)؛ وبذرة **0** وحدها للضبط (D-34).
- **العشوائيات الداخلية:** B1 من `[seed, crc32("pres|cut|phase")]`؛ `sample_space` من `crc32(اسم النموذج) + 20261024`؛ تهيئة WRMF `N(0, 0.01²)`؛ خلط دفعات GRU ببذرة كل حقبة؛ bootstrap بـ`seed=0` و`n_boot=10000`. وكسر التعادل بمفاتيح splitmix64 المطابقة لكل النماذج (§3.4).
- **الخيوط:** `OPENBLAS_NUM_THREADS=1` ثابتة، فتتوازى العمليات (`fork`) بدل الخيوط ويثبت ترتيب الجمع العددي.

## 8.2 المسارات والبصمات

| ما يُثبَّت | الآلية |
|---|---|
| بيانات المصدر | MD5 للملفات السبعة في `oulad_md5_reference.txt` مقابل `verify_oulad.py`؛ وعدد صفوف `studentVle` = 10,655,280 |
| ذاكرة الأحداث | `raw_fingerprint()` (حجم الملفين الخام) يدخل اسم ملف الذاكرة المؤقتة (`85fda9abc3` وقت التشغيل) ويُبطلها عند التغيير |
| تشغيل `run_baselines` | `run_meta.json`: الأمر، `git_commit`، `data_fingerprint`، إصدارات python/numpy/pandas، الزمن |
| التركيبة المجمَّدة | `hybrid_frozen.json` بلا حقول متقلبة (بايتياً ثابت)، و`freeze03_config.json` يحمل SHA-256 لثلاثة ملفات مجمَّدة وMD5 للبيانات السبعة وcommit كتابته |
| الخدمة | `/api/meta`: `git_commit` و`git_dirty` و`data_fingerprint` (MD5 لـ`oulad_md5_reference.txt`، أي `md5:e952490724b1e808d218ea580a234c89`) و`data_files` (MD5 لكل ملف) و`frozen_at_commit` |
| قراءات 2014 | `results/access_log.jsonl`: الزمن، MD5، الأعمدة، عدد المعرّفات، commit، `dirty` |
| ملف الأحكام | `run_confirmatory` يكتب SHA-256 لـ`verdicts.csv` في `results/conf2014/LOCK` قبل بدء الطور 2 (D-63؛ منفَّذ، ولم يُشغَّل على 2014) |

بصمات SHA-256 للملفات المجمَّدة وقت الكتابة (2026-10-25)؛ هي نفسها المسجَّلة في `freeze_checklist.md`، وتتغير عند أي إعادة توليد للملف (ويصبح الجديد هو المعتمد في الشرط ش6):

```
hybrid_frozen.json    cdfb3b553a8ebc1ef555da0247b8f482708f4fdd77bc8df7f9ea80dc668a0c0e
mde80.json            607468aeab296da35fae7e047b502d52c1ee919b26cb00cf8415cb6a9b81e88a
risk_final.json       76857226775c233b67cb67057ae3bf0c70ed11ff1622ec48dcdde1ef37c2a189
freeze03_config.json  d80ad472e015da8f190fb96e0b761aa0726d435aabb940758166447d9ec4d2c4
```

بُنيت هذه الملفات بحيث تكون **بايتياً ثابتة** بين التشغيلات: أُزيلت منها الحقول المتقلبة (التواريخ وhash الـcommit) من الملفات المبصومة، ورُتِّب سجل الجشع في `hybrid_acceptance.md` (كان يتغير مع `PYTHONHASHSEED` بسبب التكرار على `set`، وأُصلح في `hybrid.greedy_forward`). ويقيّد `run_confirmatory` سلامتها بمقارنتها بالقيم المسجَّلة في `freeze03_config.json`.

## 8.3 حدود الحتمية المعلنة

القيم العددية (المقاييس والأوزان والاختيارات) حتمية لنفس الإصدارات (numpy 2.5.3 وpandas 3.0.5 وPython 3.13)؛ تختلف **الأزمنة** و`maxrss_mb` والتواريخ بين التشغيلات، وقد يغيّر تغيّر إصدار numpy آخر خانات float. لذلك اشترط التجميد `repro_diff.md` (ش5) يقارن كل رقم بالملفات الحالية حرفياً.

## 8.4 الوسم `freeze-03` وشروطه والتشغيل التأكيدي

حالة الوسم وقت الكتابة: **غير موجود** (`git tag -l` فارغ). صارت أجزاء التجميد كوداً منفَّذاً:

| الملف | ما يفعله |
|---|---|
| `freeze_config.py` | يكتب `results/frozen/freeze03_config.json` (فضاءات النماذج والتركيبة والبذور وδ وm والقطوع وE وعتبات Youden وقاعدة k وMD5 للبيانات وSHA-256 للملفات المجمَّدة)؛ و`--checklist` يولّد `freeze_checklist.md` بحالة ش1–ش10 ودليل كل شرط |
| `reproduce_dev.py` | الأمر الواحد مع `repro_diff.md` (§2.4) |
| `run_confirmatory.py` | مشغّل E10 بحراسه وطوريه وقفله والتشغيل الجاف (أدناه) |
| `risk_final.py` | `results/frozen/risk_final.json`: M0 وM1 وM2 وCART لكل قطع؛ λ = 0.001 لـM0 وM2 و0.01 لـM1، وCART بعمق 4 وحد أدنى للورقة 100؛ وعتبات Youden عند 56: 0.4744 و0.4557 و0.4074 (D-58) |

**إضافات `run_confirmatory` الأخيرة (في الكود):** `verify_lock(out, tag, dry)` قبل الطور 2 (وعند `--phase 2` وحده): يطابق SHA-256 لـ`verdicts.csv` و`verdicts.md` مع `LOCK`، ويشترط أن commit الـLOCK هو HEAD، وأن HEAD هو الوسم في الوضع التأكيدي؛ ومقارنة MD5 للملفات الخام بالقيمة المجمَّدة في `freeze03_config.json` مع تسجيلها في `log_full_read`؛ وفرع H4-أ المجمَّد في التشغيل الجاف (`h4a_frozen_branch.csv`)؛ وتسجيل `guard_rehearsal` و`audit_2014` و`path_checks` في `run_meta.json`.

**قرارات اجتماع الإشراف 06 (`meeting-06-freeze-gate.md`) وحالتها في الكود وقت الكتابة:** **D-75** (الاستئناف المأذون: LOCK في آخر الطور 1 يغطي كل نواتجه؛ استثناء `access_log.jsonl` بشرط الإلحاق فقط و`conf2014_aborted_*` من حارس الشجرة النظيفة؛ العلم `--resume` بثلاث حالات: غياب LOCK ينقل المجلد إلى `conf2014_aborted_<n>/` ويعيد الطور 1، ووجوده بتطابق البصمات يعيد الطور 2، وأي اختلاف يوقف الأمر؛ تسجيل كل استئناف في `deviations.md`؛ والخلل البرمجي يُصلح بأصغر تعديل ويُوسم `freeze-03.1`) و**D-76** (`purpose` إلزامي من قائمة بيضاء بأربع قيم في `confirmatory_student_ids`، لمواضعها الأربعة: `learner_analysis` و`risk_final` و`run_confirmatory` و`build_artifacts`، مع تسجيل لكل استدعاء واختبار سلبي) **قيد التنفيذ ولم تظهر بعد في الشيفرة** (لا `--resume` في `argparse`، و`purpose` في `data.py` نص ثابت): **تُستكمل بعد التنفيذ**. و**D-77**: رموز القرارات تبقى في الكود وREADME والوثائق التقنية وتُحذف من الواجهة والدليل (`test_text.py`).

**قائمة الشروط المولَّدة** (`results/frozen/freeze_checklist.md`، 2026-10-25): **6 من 10 مستوفاة**.

| الشرط | الحالة | الدليل |
|---|---|---|
| ش1 هجين بأرضية D-51 | ✓ | `hybrid_frozen.json` (`floor_rule`)، `hybrid_acceptance.md` |
| ش2 MDE80 لـH1 بعد D-51 | ✓ | `mde80.md` (H1 = 0.0375) |
| ش3 الهجين على B، M1، وسم «منحلّ»، H2-ب | ✓ | `hybrid.csv`، `serving.py` (`risk_model="M1"`)، `hybrid_frozen.json` (`H2b`) |
| ش4 نماذج الخطر النهائية | ✓ | `results/frozen/risk_final.json` |
| ش5 `reproduce_dev` و`repro_diff.md` | ✗ قيد التشغيل | **تُستكمل بعد التشغيل** |
| ش6 `freeze03_config.json` وSHA-256 | ✓ | `results/frozen/freeze03_config.json` |
| ش7 `run_confirmatory` وتشغيل جاف كامل على 2013 | ✗ قيد التشغيل | **تُستكمل بعد التشغيل** (`results/dryrun2013/`) |
| ش8 مراجعة الزميل وتوقيعه | ✗ خارجي | `docs/meetings/*peer*` |
| ش9 تحديث الوثيقة 02 وREADME | ✓ | الوثيقة 02، `src/ml/README.md` |
| ش10 تحقق المشرف ثم الوسم | ✗ خارجي | §8 من محضر الاجتماع 03 |

**نتائج ش5 وش7 (تُستكمل بعد التشغيل):** حالة `repro_diff.md` وزمن `reproduce_dev` الكامل على commit نظيف، ونتيجة التشغيل الجاف (`results/dryrun2013/run_meta.json` و`dryrun_vs_dev.md`). المعلوم حتى الآن (README الـml) أن أول `reproduce_dev` كامل (53.6 دقيقة) طابق كل الملفات عدا فروق شُخِّصت وأُصلحت، ويلزم تشغيل أخير نظيف لاعتماد «مطابق».

**كيف يُشغَّل E10** (D-63؛ المشغّل منفَّذ ولم يُشغَّل على 2014):

```
python3 -m src.ml.experiments.run_confirmatory --dry-run-dev --force     # تشغيل جاف على 2013 → results/dryrun2013/
python3 -m src.ml.experiments.run_confirmatory --tag freeze-03           # التشغيل التأكيدي، مرة واحدة
python3 -m src.ml.experiments.run_confirmatory --tag freeze-03 --phase 2 # إعادة الطور 2 وحده بعد LOCK
```

الحراس (`check_guards`): الوسم موجود وHEAD هو commit الوسم والشجرة نظيفة والمجلد `results/conf2014/` غير موجود، وإلا رُفع `GuardError` قبل لمس 2014. بعدها يكتب `.lock` ويسجّل قراءة 2014 الكاملة في `access_log.jsonl` ويتحقق من SHA-256 للملفات المجمَّدة (`check_integrity`)، ثم يمرّر `allow_confirmatory=True`. **الطور 1** (E10): B1–B10 وGRU-lite وزوج H2-أ وHYB\* والمهمة B وH4-أ بنماذج الخطر النهائية وH4-ب وتفكيك H1، ثم الأحكام (bootstrap-t وقلب الإشارات وHolm بـm = 4 وجدولا D-26 ونص D-48) في `verdicts.csv` المقفل بـSHA-256 في `LOCK` **قبل** الطور 2، ولا تُطبع نتيجة أثناء التشغيل. **الطور 2** (E11–E13): الاستئصال وحساسيات E والإنصاف الوصفي والسوالب المعيَّنة والأشكال. التشغيل الثاني للطور 1 يحتاج قراراً مكتوباً من المشرف، والانحراف يُسجَّل في `deviations.md`.

**التشغيل الجاف** (`--dry-run-dev`): يولّد كل المخرجات على 2013 في `results/dryrun2013/` بلا مس 2014 (`data.assert_allowed`)، ويجري `guard_rehearsal` (كل حارس على حدة، و`check_guards` بتعيين الوسم إلى HEAD)، ويعيد نماذج الخطر بترك عرض خارج التدريب، ويكتب `dryrun_vs_dev.md`. وعروض 2014 لا تُخدَم من الواجهة إلا بوجود `verdicts.csv` و`LOCK` (FR-40، D-67).

**ما يحرسه الكود اليوم:** لا يمرّر أي سكربت سوى `run_confirmatory` (بعد حراسه) المعامل `allow_confirmatory=True`؛ والخلفية لا تقرأ 2014 أبداً؛ وجميع المحمِّلات ترشّح عند القراءة (D-47 N1). وشرط D-69: `serving.py` و`build_artifacts.py` و`src/backend/` و`src/frontend/` خارج نطاق التجميد بشرط ألا تعدّل وحدة مجمَّدة، ويُفحص بـ`git diff freeze-03`.

# 9. ملحق

## 9.1 المعاملات المجمَّدة (hyperparameters)

**التركيبة المجمَّدة** (`results/dev2013/hybrid_frozen.json`):

| الحقل | القيمة |
|---|---|
| `status` | مجمَّدة على 2013 (D-11، D-30، D-51)؛ التأكيدي يعيد الضبط داخل هذا الفضاء فقط. الملف بلا حقول متقلبة |
| `components` | `C7_ClusterPop` (7)، `B5_SKNN` (4) |
| `floor_component` / `accept_only_components` | `B5_SKNN` / `C7_ClusterPop` |
| `floor_rule` | وزن مكوّن الأرضية ≥ 0.25 (أصغر نقطة موجبة في شبكة D-29)؛ تُحذف نقاط الوزن الصفري ولا تُضاف قيمة (D-51) |
| `weight_grid` / `weight_grid_points` | سمبلكس بخطوة 1/4؛ النقاط الأربع (C7، SKNN): (0، 1)، (0.25، 0.75)، (0.5، 0.5)، (0.75، 0.25) |
| `weights_by_fold` | 27 زوجاً (عرض، قطع): 21 بـ(0.75، 0.25)، و5 بـ(0.5، 0.5)، وواحد بـ(0.25، 0.75) |
| `component_configs_by_fold` | C7: `w=3` في 18 زوجاً و`w=7` في 6 و`w=14` في 3؛ SKNN: `L=1;M=1000;k=500;variant=sknn` (12)، `L=1;M=1000;k=200;variant=sknn` (8)، `L=7;M=1000;k=500;variant=vsknn` (6)، `L=7;M=1000;k=200;variant=vsknn` (1) |

**معاملات منصة التجارب** (من الكود ومن CSV؛ تنبيه: `gru_meta.json` و`ablation_meta.json` يحويان الزمن لا المعاملات):

| المجال | المعامل | القيمة |
|---|---|---|
| البروتوكول | قطوع t / الأفق / الميزانية / KS | {70، 126، 182} / 14 يوماً / ≤ 20 إعداداً / (5، 10، 20) |
| الإشارة والتجميع | τ، β، α / ks، n_init، ARI الأدنى | {7، 14، 28، 56، ∞}، {0.5، 1، 2}، {1…40} / 2..8، 10، 0.8 |
| WRMF | f / reg / نقاط التفتيش / التهيئة | {16، 32، 64} / {0.01، 0.1، 1، 10} / {10، 15، 25} (افتراضي iters = 15) / N(0, 0.01²) |
| GRU-lite | البنية | d_e = d_h = 64، طبقة واحدة |
| GRU-lite | lr / الهدف | {1e-3، 3e-3، 1e-2} / {next، next-new}؛ ستة إعدادات |
| GRU-lite | L2 / القص / الدفعة / BPTT | 1e-5 / 5 / 128 / T = 20 |
| GRU-lite | الحقب / الصبر | ≤ 30 / 3 |
| GRU-lite | المختار (27 زوجاً، المهمة A) | lr = 0.001 في 13 زوجاً و0.01 في 8 و0.003 في 6؛ والهدف `next-new` في 24 زوجاً و`next` في 3؛ والحقب المختارة بين 1 و20 (الأكثر تكراراً 2 ثم 1) |
| الهجين | حد المكوّنات / شبكة الأوزان | 4 / 1/4 (2–3 مكوّنات) و1/3 (4)، و0.1 حساسية |
| الإحصاء | δ / α / m (Holm) / δ_AUC | 0.02 / 0.05 / 4 / 0.02 |
| الإحصاء | MDE80 (H1، H2-أ، H3، H4-أ) | 0.0375، 0.045، 0.050، 0.0225 |
| الخطر | λ لكل عرض (اليوم 56) | M0: 0.001 للتسعة؛ M1: 0.01 للتسعة؛ M2: 0.001 أو 0.01 |
| الخطر | عتبات Youden | M0 = 0.4744، M1 = 0.4557، M2 = 0.4074 |

## 9.2 قاموس الحقول في الاستجابات

حقول التوصية (`/api/recommendations`)، من `schemas.RecommendationResponse` وما يرجعه الخادم:

| الحقل | المعنى |
|---|---|
| `registration` | `<presentation>-<id_student>`، مثل `FFF_2013J-371869` |
| `requested_day` / `snapshot_day` | اليوم المطلوب واليوم الذي حُسبت عنده؛ متساويان دائماً (D-49) |
| `task` | A: موارد جديدة؛ B: أي وصول بما فيه الإعادات |
| `status` / `known_learner` | `ok` أو `no_history` (ترتيب غير شخصي) أو `withdrawn` (قائمة فارغة)؛ وهل للتسجيل نشاط في الكتالوج |
| `note` | تنبيه نصي (قبل أول قطع أو بلا تاريخ) |
| `context` | `week` (اليوم÷7 + 1) و`next_assessment{type, day, days_ahead}` و`active_days_to_date` |
| `components[]` | `id` و`label` و`weight` لمكوّنات الهجين عند هذا القطع |
| `items[]` | `rank` و`id_site` و`activity_type` و`relevance` (الدرجة المدمجة Σ w_m r̃_m، وليست مقياس تقييم؛ حلّت محل `score`، D-70 (4)) و`contributions` (w_m·r̃_m) و`reason` و`reason_secondary` |
| `provenance` | `run_id` (`replay-dev2013-<commit>`) و`role` (`dev`) و`model_cut` (null قبل 70)؛ في **كل** استجابة بيانات (D-49 (6)) |

التفسير (`/api/explanations`): `relevance` و`components[]` بـ`weight` و`r_tilde` (الرتبة المطبَّعة) و`contribution` و`sentence` و`evidence` من ثلاثة أنواع: `count` (`n` و`window` و`scope` = all\|similar)، و`item` (`id_site` و`activity_type` و`days` و`last_day`)، و`assessment` (`assessment_type` و`days_ahead`). **المدرّس:** الخطر `risk.score` (درجة نسبية غير معايَرة، D-65) و`cut_day` و`threshold` بست منازل (Youden) و`above_threshold` و`provenance` (`lopo_2013`) و`top_factor` و`factors[{name, wz}]` و`label_ar` = «درجة خطر نسبية غير معايَرة»؛ و`cluster{id,label}`؛ و`profile[{name,value,median,z}]`؛ و`withdrawn_day`؛ ولا حقل نتيجة نهائية. وفي `/api/instructor/clusters`: `cluster_day` (= 56) و`unstable_reason` و`quality{silhouette, dbi, ari}` (`ari` يقبل null). وفي `/api/meta`: `schema_version` و`version` و`run_id` و`git_commit` و`git_dirty` و`freeze_tag` و`data_fingerprint` و`data_files` و`components` و`snapshot_grid` (28 إلى 266 بخطوة 14) و`cutoffs` و`risk_cutoffs` و`risk_score` (الهدف: رسوب أو انسحاب مقابل نجاح أو امتياز، `calibrated = false`) و`bind_host` و`access_notice` (D-66) و`notes`.

## 9.3 مصفوفة تتبّع مختصرة (متطلب ← وحدة ← اختبار)

| المتطلب | الوحدة والملف | الاختبار |
|---|---|---|
| FR-02 حجب 2014 (D-09) | `data.assert_allowed`، `Repository.check_presentation` | `test_splits.TestConfirmatoryGuard`، `test_static_errors.test_confirmatory_locked_409_everywhere` |
| FR-21 أفضل 10 بتفسير من المساهمة | `serving.Engine.recommend`، `ReplayService`، `ExplanationService` | `test_serving`، `test_api_live.test_explanation_contract_and_consistency` |
| FR-37 المهمتان A وB | `splits.Targets.task`، `recommend(exclude_seen)` | `test_splits.test_tasks`، `test_api_live.test_task_a_excludes_seen_task_b_may_include` |
| FR-40 فتح 2014 بعد الأحكام | `Engine(allow_confirmatory)`، `run_confirmatory` | `test_serving`، `test_confirmatory` |
| NFR-01 زمن الاستجابة | `Services.run_warmup`، `serving.warm`، ذاكرات LRU | `test_api_live.test_latency_after_warmup`، `bench.py` |
| NFR-06 بلا تخزين حالة متعلم | `Engine` (بلا كتابة) | `test_serving.test_no_future_data_used` |
| NFR-07 حتمية وإعادة إنتاج | `harness.SEEDS`، `tiebreak_keys`، `reproduce_dev` | `test_splits.test_tiebreak_deterministic_and_order_free`، `repro_diff.md` |
| NFR-09 فصل مسارات المتعلم عن الخطر | `schemas.LEARNER_MODELS` | `test_contract_no_risk`، `test_contract_json` |

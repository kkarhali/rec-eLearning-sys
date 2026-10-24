# توثيق الكود البرمجي

**المرحلة الرابعة من رسالة الماجستير: «نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم»**

- **القارئ المستهدف:** لجنة التحكيم، وأي مطوّر يريد أن يفهم كيف بُني النظام، وكيف يُشغَّل، وكيف يُعاد إنتاج كل رقم في الرسالة.
- **حالة المستودع وقت الكتابة:** 2026-10-24، قبل الوسم `freeze-03`. كل ما يُذكر هنا من أسماء ملفات ودوال وأوامر قُرئ من الشيفرة نفسها، وشُغّلت الاختبارات والأوامر المذكورة فعلاً (الفصل 7). وحين يخالف README الشيفرة يُذكر ذلك صراحة (§7.4).
- **المصطلحات:** تبقى بالإنكليزية كما وردت في الكود (`fit`، `recommend`، `Engine`…)، والشرح بالعربية.

# 1. نظرة عامة

## 1.1 الغرض

يبني الكود ثلاثة أشياء مترابطة فوق مجموعة بيانات OULAD (Open University Learning Analytics Dataset):

1. **منصة تجارب أوفلاين** (`src/ml/`): تحمّل السجلات، وتبني الإشارة السلوكية، وتقسّم الزمن إلى طيّات بلا تسرب، وتدرّب خطوط الأساس B1–B10 والنموذج العصبوني GRU-lite والهجين، وتحسب المقاييس والاستدلال الإحصائي، وتكتب كل النتائج في ملفات صغيرة تحت `results/`. الغاية أن يكون كل رقم في الرسالة قابلاً لإعادة الإنتاج من جذر المستودع.
2. **خدمة توصية بنمط إعادة التشغيل (Replay)** (`src/ml/serving.py` ثم `src/backend/`): تأخذ تسجيلاً ويوماً t، وتعيد ما كان سيوصى به عند ذلك اليوم مع تفسير كل توصية، من التركيبة المجمَّدة على بيانات 2013، دون أن تستعمل أي حدث بعد اليوم t.
3. **واجهة عربية RTL** (`src/frontend/`): صفحة للمتعلم (أفضل 10 توصيات وتفسيرها) ولوحة للمدرّس (الملامح والعناقيد ودرجة الخطر النسبية)، وتعمل فوق الخدمة أو بوضع محاكاة مستقل.

وحدة التوصية هي المورد غير التنقّلي `id_site` داخل عرض المقرر (D-04)، والمتعلم هو التسجيل (module, presentation, student)، ولكل عرض نموذجه المستقل (D-05).

## 1.2 خريطة المستودع

```
rec-eLearning-sys/
├── README.md                 خريطة المستودع وأمر بناء Word
├── data/
│   ├── download.sh           استنساخ مرايا OULAD من GitHub ثم التحقق
│   ├── verify_oulad.py       إعادة بناء studentVle.csv من 8 أجزاء + MD5 لكل ملف
│   ├── oulad_md5_reference.txt
│   ├── raw/oulad/            (خارج git) الجداول السبعة، ≈ 825 MB
│   └── cache/                (خارج git) أحداث مجمَّعة + درجات المكوّنات، ≈ 1.3 GB
├── src/
│   ├── ml/                   منصة التجارب + serving.py
│   │   ├── data.py signals.py splits.py metrics.py hybrid.py stats.py
│   │   ├── harness.py learners.py components.py serving.py plots.py
│   │   ├── models/           base, simple, knn, baskets, markov, wrmf, ease, cbf,
│   │   │                     context, gru_lite
│   │   ├── experiments/      eda, run_baselines, gru_sanity, run_gru, run_ablation,
│   │   │                     learner_analysis, run_hybrid, power, build_artifacts,
│   │   │                     risk_final, report
│   │   └── tests/            unittest (8 ملفات)
│   ├── backend/              starlette + pydantic: app, routes/, services/, schemas
│   └── frontend/             TypeScript + HTML + CSS: src/, styles/, mock/, build.sh
├── results/
│   ├── dev2013/              مخرجات التطوير النصية (CSV/JSON/MD)، ≈ 3.4 MB، في git
│   └── access_log.jsonl      سجل قراءات D-47
├── artifacts/                معاملات القطوع: risk_*.json وclusters_56.npz (≈ 0.5 MB)
├── scripts/                  build_docx.py, lo_update_toc.py, svg2png.js/.py, build_pptx.py
├── docs/                     working/ (مسوّدات)، decisions/ (ADR)، meetings/ (المحاضر)
├── deliverables/             مخرجات المراحل (Word/PowerPoint) ولقطات الشاشة
└── references/               المراجع العلمية (PDF)
```

## 1.3 الفصل بين الكود والمخرجات النصية

يفصل المستودع بوضوح بين أربعة أنواع من الملفات، ولا يخلط بينها أي أمر بناء:

| النوع | أين | يُولَّد بـ | في git؟ |
|---|---|---|---|
| **الكود** | `src/`، `scripts/`، `data/*.py\|sh` | يُكتب يدوياً | نعم |
| **مخرجات التجارب** (أرقام وجداول صغيرة) | `results/dev2013/`، `artifacts/` | أوامر `python3 -m src.ml.experiments.*` | نعم (صغيرة) |
| **البيانات والذاكرات المؤقتة** | `data/raw/`، `data/cache/` | `data/download.sh` وأول تحميل | لا (`.gitignore`) |
| **المخرجات النصية** (مسوّدات ووثائق Word/PPTX) | `docs/working/`، `deliverables/` | `scripts/build_docx.py`، `build_pptx.py` | نعم |

قاعدة التصميم: الوثائق لا تُنشئ أرقاماً؛ الشيفرة تكتبها في `results/` وتنقلها الوثائق (مثال: `summary.md` يولّده `report.py` من ملفات CSV وحدها).

## 1.4 التقنيات والقيود ولماذا

بيئة العمل لا تسمح بتثبيت حزم جديدة (pip وnpm محجوبان). المتاح في Python هو numpy وpandas وstarlette وuvicorn وpydantic وأدوات الوثائق؛ ولا يتوفر scikit-learn ولا scipy ولا matplotlib ولا TensorFlow ولا torch ولا FastAPI. هذا قيد هندسي لا علمي، وقد وثّقه ADR-003 بوصفه انحرافاً معلناً عن خطة البحث الأصلية.

| الطبقة | المستعمل (إصدارات التحقق) | ما استُعيض به ولماذا |
|---|---|---|
| تعلّم الآلة والإحصاء | Python 3.13.17، numpy 2.5.3، pandas 3.0.5 | بدل TensorFlow/Keras: GRU-lite مكتوب يدوياً مع فحص تدرج بالفروق المحدودة. بدل scikit-learn: k-means++ وLogistic وCART والمقاييس مكتوبة بـnumpy ومغطاة باختبارات وحدة على حالات معروفة الحل. بدل scipy: اختبار قلب الإشارات وbootstrap-t وHolm وتوزيع t مكتوبة يدوياً (`stats.py`) |
| الخدمة | starlette 1.7.0، uvicorn 0.54.0، pydantic 2.13.5 | بدل FastAPI: starlette مع نماذج pydantic للعقود |
| الواجهة | HTML وCSS خالص وTypeScript بمترجم `tsc` وحده (Node v22.22.0) | لا React ولا مكتبات رسوم؛ الرسوم SVG مكتوبة يدوياً؛ لا حاجة لأي `npm install` |
| التخزين | CSV وJSON وnpz وpickle | لا parquet (pyarrow غير متاح)؛ يختار `data.py` parquet تلقائياً إن توفر |
| الوثائق | pandoc، python-docx، LibreOffice، python-pptx، Playwright (Node) | تحويل Markdown إلى Word RTL وتصيير SVG |

كل خوارزمية موثّقة باختبارات تعيد حساب الأمثلة العددية المنشورة في وثيقة الفرضيات (الجداول 7 و8 و12 و14 و19 وغيرها)، فتحل الاختبارات محل الثقة بمكتبة جاهزة.

# 2. المتطلبات والتثبيت والتشغيل من الصفر

## 2.1 المتطلبات

- Python 3.13 مع numpy وpandas (لمنصة التجارب)، وstarlette وuvicorn وpydantic (للخدمة).
- Node.js مع `typescript` مثبَّتاً عالمياً (الأمر `tsc`) لبناء الواجهة؛ وPlaywright العالمي لسكربتات اللقطات فقط.
- `git` و`bash` و`curl` والاتصال بـGitHub (لتحميل البيانات).
- مساحة: ≈ 825 MB للبيانات الخام، و≈ 1.3 GB للذاكرة المؤقتة. والذاكرة العاملة: أقصى RSS مقيس ≈ 550 MB لكل عملية في `run_baselines`.
- أنوية: التشغيل الكامل مصمَّم لأربع عمليات (`--workers 4`)؛ يعمل بأقل لكنه أبطأ.

## 2.2 الاستنساخ وتحميل البيانات والتحقق

```
git clone <عنوان-المستودع> rec-eLearning-sys
cd rec-eLearning-sys
bash data/download.sh          # يستنسخ مرآتين من GitHub، ثم يستدعي verify_oulad.py
python3 data/verify_oulad.py   # يعيد التحقق وحده (يطبع integrity: PASS)
```

`data/download.sh` يستنسخ (بلا LFS) مرآة `LuongAnh1/oulad-data-warehouse` لأجزاء `studentVle_*.csv` الثمانية، ومرآة `reyquiroz/OULAD_CourseAware` للجداول الستة الصغيرة المطابقة للأصل بايتاً ببايت، ويضعها في `data/raw/oulad/`. المواقع الرسمية محجوبة في بيئة العمل، ويكون الاستشهاد في الرسالة بالمصدر الرسمي (Kuzilek وHlosta وZdrahal، Scientific Data 4:170171، الترخيص CC BY 4.0).

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

```
python3 -m unittest discover -s src/ml/tests               # 96 اختباراً، ≈ 4 ث، بلا البيانات الخام
python3 -m unittest src.backend.tests.test_contract_no_risk src.backend.tests.test_static_errors
python3 -m unittest discover -s src/backend/tests -t .     # الخلفية كاملة، ≈ 85 ث (تحتاج البيانات)
cd src/frontend && tsc --noEmit -p tsconfig.json           # فحص الأنواع (strict)
```

ملاحظة: اختبارات الخلفية تستعمل استيراداً نسبياً (`from .asgi_client import Client`)، فلا بد من الخيار `-t .` (جذر المستودع مجلداً أعلى) عند استعمال `discover`. الأمر `discover -s src/backend/tests` بلا `-t .` يفشل في استيراد `test_api_live` و`test_static_errors` بالخطأ `attempted relative import with no known parent package`، وقد تحقّقنا منه (§7.4).

## 2.4 إعادة إنتاج نتائج التطوير

الأمر المعتمد في `src/ml/README.md` ليس أمراً واحداً بعد، بل تسلسل مرتَّب من تسع خطوات، تُشغَّل كلها من جذر المستودع على عروض 2013 التسعة وحدها (حاجز D-09). الأمر الواحد `python3 -m src.ml.experiments.reproduce_dev` مطلوب في شروط التجميد (D-62 ش5) ولم يُكتب بعد (§8.4). التسلسل الحالي:

```
python3 -m unittest discover -s src/ml/tests -v
python3 -m src.ml.experiments.eda               # ≈ 25 ث
python3 -m src.ml.experiments.run_baselines     # 5.2 د (4 عمليات)
python3 -m src.ml.experiments.gru_sanity        # ≈ 1 د؛ بوابة: لا نتائج GRU بلا اجتيازها
python3 -m src.ml.experiments.run_gru           # 15.2 د
python3 -m src.ml.experiments.run_ablation      # 19.2 د
python3 -m src.ml.experiments.learner_analysis  # ≈ 2.5 د
python3 -m src.ml.experiments.run_hybrid        # ≈ 2-3 د
python3 -m src.ml.experiments.power             # ≈ 1 د
python3 -m src.ml.experiments.build_artifacts   # ≈ 1 د
```

المجموع المقيس في تشغيل الفريق: ≈ 48 دقيقة فعلية و≈ 4.8 ساعة CPU، تحت سقف 8 ساعات CPU (D-34). والأوامر تعيد كتابة ملفات `results/dev2013/` المتتبَّعة في git؛ تتطابق قيم المقاييس لأن كل شيء حتمي (§8)، وتتغير أعمدة الأزمنة والتواريخ فقط.

المخرجات الوسيطة الكبيرة (درجات المكوّنات لكل طيّة وطور وبذرة) تُخزَّن في `data/cache/components/` (≈ 1.1 GB، خارج git) وتعيد استعمالها `run_hybrid` وغيره.

الملف `experiments/risk_final.py` (نماذج الخطر النهائية، D-58) ليس ضمن تسلسل README؛ يكتب في `results/frozen/` الذي لم يُنشأ بعد، ويُستعمل في مسار التجميد (§8.4).

## 2.5 بناء الواجهة وتشغيل الخادم وفتح الصفحات

```
bash src/frontend/build.sh                 # tsc → dist/js، ونسخ html/css/mock إلى dist/
python3 -m src.backend --warm              # http://127.0.0.1:8000 (الواجهة + /api)
```

بعد التسخين (≈ 80 ثانية للأيام الستة الافتراضية) تُفتح الصفحات:

| الصفحة | الرابط | ملاحظة |
|---|---|---|
| الرئيسية (معالج الاختيار) | `http://127.0.0.1:8000/` | اختيار العرض والتسجيل واليوم |
| واجهة المتعلم | `/learner.html?p=FFF_2013J&r=FFF_2013J-371869&d=75` | أفضل 10 وزر «لماذا؟» |
| لوحة المدرّس | `/instructor.html?p=FFF_2013J&d=75` | تتطلب اليوم ≥ 56 |
| عن النظام | `/about.html` | نص ثابت (FR-35) |

خيارات الخادم (من `--help`): `--host` و`--port` و`--no-instructor` و`--warm` و`--warm-presentation` و`--warm-days` و`--warm-weekly` و`--log-level`. من دون `dist/` يعيد الجذر 503 برسالة تدل على أمر البناء وتبقى مسارات `/api/*` تعمل. وللتجربة بلا خادم: `python3 -m http.server 8000 -d src/frontend/dist` ثم تفتح الواجهة بوضع المحاكاة تلقائياً (§5.4).

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
- **أدوات:** `target_mask` (قناع الموارد القابلة للتوصية)، `day_baskets` (سلال اليوم غير المرتبة)، `next_assessment_gap` (a(d) = أقرب موعد تقييم منشور)، `proximity_bin` (فئات {0–3، 4–7، 8–14، >14} يوماً).

### الحاجز ضد 2014 والقراءة المحدودة وسجل الوصول

الحاجز (D-09) من طبقتين. **الأولى** `assert_allowed(names, allow_confirmatory=False)` ترفع `ConfirmatoryAccessError` لأي اسم من `CONF_PRESENTATIONS`، وترفع `ValueError` لاسم مجهول. تستدعيها `load_presentation` و`role_presentations` وكل محمِّل. و**الثانية** أن الذاكرة المؤقتة نفسها لا تحوي إلا صفوف 2013.

الاستثناء الوحيد (D-47) هو الدالة `confirmatory_student_ids(log_path=None, reader=None)`: تقرأ من `studentRegistration.csv` الأعمدة الثلاثة `code_module` و`code_presentation` و`id_student` وحدها بالمعامل `usecols`، فلا تواريخ تسجيل ولا انسحاب ولا أي جدول آخر، وتعيد مجموعة معرّفات طلاب لهم تسجيل في 2014، لتُحذف تسجيلاتهم من تدريب H4-أ (تفادي تسرب الشخص نفسه بين التدريب والاختبار). الدالة:

1. تكتب سجلاً بحدث `attempt` **قبل** القراءة (ملاحظة N3 من مراجعة الزميل)؛
2. ترفض صراحةً أي قارئ يعيد أعمدة زائدة وتسجّل `failure`؛
3. تكتب `success` مع الزمن وMD5 للملف والأعمدة وعدد المعرّفات و`commit` وعلم `dirty`، في `results/access_log.jsonl`.

ثلاثة اختبارات وحدة في `test_splits.py` تتحقق من الأعمدة والسجل وفشل الأعمدة الزائدة وبقاء بقية الحاجز سليماً. وفي الملف سجلات التشغيلات الفعلية لـ`learner_analysis` و`build_artifacts` (الصيغة الأقدم سطر واحد لكل قراءة، والأحدث سطران `attempt` و`success`).

## 3.3 `signals.py`: عائلة الإشارة المتداخلة

يحسب الوزن السلوكي لتسجيل u ومورد i عند نهاية التدريب t₀:

W_ui(t₀) = Σ_{d ∈ D_ui} exp(−(t₀−d)/τ) · (1 + β·log1p(c_uid / m_type(i)))

حيث m_type(i) وسيط النقرات اليومية لنوع نشاط المورد محسوباً من فترة التدريب فقط. المستويات المتداخلة: **L0** ثنائي، **L1** عدد الأيام (τ = ∞، β = 0)، **L2** أيام مع حداثة τ، **L3** أيام وحداثة وشدة مطبَّعة بالنوع β.

| العنصر | الوصف |
|---|---|
| `SignalSpec(level, tau, beta)` | dataclass مجمَّد؛ الخاصية `key` تعطي نصاً مثل `L2(tau=14)` أو `L3(tau=28,beta=1)` |
| `TAU_SPACE` | (7، 14، 28، 56، ∞)؛ و`BETA_SPACE` = (0.5، 1، 2)؛ و`ALPHA_SPACE` = (1، 2، 5، 10، 20، 40) |
| `signal_matrix(train, spec)` | مصفوفة كثيفة U×I (float64) للمستوى المطلوب من `TrainData` |
| `wrmf_preference_confidence(W, alpha, binary_confidence)` | التفضيل p = 1[W>0] والثقة c = 1 + α·W (أو 1 + α·1[W>0] للمقارن الثنائي في H2-أ) |
| `all_signal_specs()` | 21 مواصفة: L0 وL1 و4 قيم τ لـL2 و15 مزيجاً (τ, β) لـL3 |

## 3.4 `splits.py`: القطع الزمني والمهمتان A وB بلا تسرب

لكل عرض ونقطة قطع t ∈ {70، 126، 182} (`CUTS`) وأفق 14 يوماً (`HORIZON`) طوران:

| الطور | التدريب | النافذة |
|---|---|---|
| `tune` | d ≤ t−14 | تحقق (t−14، t] |
| `test` | d ≤ t | اختبار (t، t+14] |

- **`TrainData`** هو الكائن الوحيد الذي يصل إلى النماذج، ويُبنى من صفوف d ≤ t₀ فقط: `users` و`items` (الكتالوج المرتب) و`item_type` والأحداث (`ev_u`، `ev_i`، `ev_d`، `ev_c`) و`seen` (قناع U×I لما زاره المتعلم) و`all_events` (كل الأنواع حتى t₀ للسياق وملامح المتعلم) و`assessments` و`tiebreak` و`type_medians`.
- **`Targets`** كائن للتقييم وحده: `target` و`unreach` (أهداف خارج الكتالوج، وتُحسب إخفاقاً) و`seen`. والدالة `Targets.task("A"|"B")` تعيد (الأهداف، المرشحين، غير القابلة للوصول، المقيَّمين). المهمة A (الأساسية): أهداف = موارد النافذة غير المزارة قبل t₀، ومرشحون = الكتالوج ناقص المزار. والمهمة B: كل موارد النافذة والمرشحون كل الكتالوج.
- **`build_train(p, t0, cut, phase, exclusion)`** يبني منظر التدريب لأي يوم، وتعيد استعماله خدمة إعادة التشغيل لأي يوم t (D-49). و**`make_fold(p, cut, phase, exclusion)`** يعيد `(TrainData, Targets)` ويرفض نافذة تتجاوز طول العرض. و**`check_no_overlap`** يؤكد برمجياً أن التدريب والنافذة منفصلان.
- **كسر التعادل:** `tiebreak_keys(pres, cut, students, items)` يولّد مفاتيح عشوائية حتمية من مزيج (عرض، قطع، متعلم، مورد) بدالة splitmix64، **مطابقة لكل النماذج**، فلا يربح نموذج من ترتيب المعرّفات أو الشعبية عند التعادل.

## 3.5 `metrics.py`: المقاييس على الكتالوج الكامل

لا سوالب معيَّنة؛ يُرتَّب كل مرشح. `evaluate(scores, cand, tgt, unreach, evaluated, tiebreak, ks=(5,10,20), pop=None)` يعيد لكل متعلم مقيَّم P/R/HR/NDCG/MRR عند كل K، ويعيد Coverage@K وPopBias@K، وتلخّصها `summarize(res, mask=None)`. تفاصيل مهمة: IDCG يحسب `|T_u|` شاملاً الأهداف غير القابلة للوصول؛ و`rank_order` يرفع خطأ عند وجود NaN على مرشح؛ و`popularity_percentile` بمتوسط الرتب عند التعادل. ونسخة مرجعية قائمة على القوائم (`list_metrics`, `coverage`) تُستعمل في الاختبارات للتحقق من النسخة المتجهية على المثال اليدوي (الجدول 19).

## 3.6 واجهة النماذج الموحدة `fit/recommend`

كل نموذج يرث `models.base.Recommender` (نمط Strategy مع Template Method):

```python
model = SomeModel(seed=0, **params).fit(train)          # train: splits.TrainData (d ≤ t0)
S = model.score()                                        # مصفوفة درجات كثيفة U×I
model.recommend(student_id, k=10, exclude_seen=True)     # قائمة id_site
```

- يطبّق الصنف المشتق `_fit(train)` و`_score()` ويعلن `param_space()` (قائمة قواميس إعدادات) ثم الخصائص `name` و`stochastic` (إن كان يُقيَّم بخمس بذور) و`tasks`.
- `exclude_seen=True` هي المهمة A، و`False` المهمة B. والترتيب النهائي بـ`metrics.rank_order` ومفاتيح `train.tiebreak`.
- `grid(**axes)` يولّد الجداء الديكارتي للإعدادات، و`sample_space(space, budget, name)` يختار ≤ budget إعداداً بعينة عشوائية ببذرة ثابتة مشتقة من اسم النموذج.
- السجلات: `BASELINES` (B1–B10) و`COMPONENTS` (C6 وC7)، يستهلكها الحزام والهجين و`Engine` بلا تعديل.

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

مساعدات: `baskets.py` يوفّر `day_keys` و`recency_rank` و`last_days_query` (استعلام آخر L أيام نشطة، ثنائي أو خطي) و`week_baskets` و`consecutive_day_transitions`. وWRMF مكتوب بخطوة ALS نصفية `als_half_step` تشكّل مصفوفات المعادلات الطبيعية بضرب مصفوفات واحد لكل كتلة صفوف وتحلّها بـfloat64، وتُستعمل نفسها في «fold-in» عند الخدمة.

## 3.7 GRU-lite

**البنية** (`models/gru_lite.py`، مواصفات D-35): طبقة GRU واحدة بأبعاد d_e = d_h = 64. لكل متعلم متتالية سلال أيام نشطة؛ تمثيل السلة e = متوسط تضمينات موارد الكتالوج فيها، والأيام الفارغة ليست خطوات. البوابات: z = σ(eW_z + hU_z + b_z)، r = σ(eW_r + hU_r + b_r)، h̃ = tanh(eW_h + (r⊙h)U_h + b_h)، h′ = (1−z)⊙h + z⊙h̃، والخرج o = h′V + c (لوجيتات على الكتالوج). الاصطلاح متجه صف، ومصفوفات الأوزان `MATS = (E, Wz, Wr, Wh, Uz, Ur, Uh, V)` والانحيازات `BIASES = (bz, br, bh, c)`.

**التدريب:**

- الخسارة: انتروبيا متقاطعة متعددة الوسوم بهدف مطبَّع y = 1[j ∈ S_tgt]/\|S_tgt\| حيث الهدف `next` (السلة التالية) أو `next-new` (التالية ناقص ما زاره). تُقنَّع الأهداف الفارغة والخطوات المحشوة، وتُضاف عقوبة λΣ‖M‖² بـ`L2 = 1e-5` على المصفوفات لا الانحيازات.
- المُحسِّن `Adam` (0.9، 0.999، 1e-8، مع تصحيح الانحياز) بقص عام للنظيم عند `CLIP = 5`.
- الدفعات `BATCH = 128` تسلسلاً تُخلط ببذرة كل حقبة، و`T_BPTT = 20` خطوة مع تمرير الحالة بين النوافذ بلا تدرج، وحشو يميني بقناع (الخطوة المحشوة تُبقي h).
- التهيئة: Glorot-uniform لـE وW_* وV، ومتعامدة (QR مع تصحيح الإشارة) لـU_*، وانحيازات صفرية.
- الإيقاف المبكر: `MAX_EPOCHS = 30`، مقياس NDCG@10 (المهمة A) على التحقق بعد كل حقبة، صبر `PATIENCE = 3`، ويُحتفظ بأفضل حقبة. في طور الاختبار يعاد التدريب بعدد الحقب المختار نفسه والبذرة نفسها. لا ميزات زمنية.

**الدوال الأساسية:** `init_params`، و`window_loss_grad` (أمامي وخلفي يدوي لنافذة)، و`forward_states`، و`train_epoch`، و`infer_logits`، والأصناف `Adam` و`Sequences` (تحويل `TrainData` إلى متتاليات مرتبطة بالمتعلمين) و`GRULite`.

**فحوص الصحة** (`experiments/gru_sanity.py` ← `results/dev2013/gru_sanity.md`): S1 فحص تدرج بالفروق المحدودة (ε = 1e-5، ≥ 20 إحداثية لكل مصفوفة، المعيار خطأ نسبي < 1e-4، المقيس 4.28e-6)، S2 فرط ملاءمة 32 تسلسلاً (L − H ≤ 0.05 nat؛ المقيس 0.0012 وHR@10 تدريب = 1)، S3 سلسلة ماركوف اصطناعية على 50 مورداً (TV ≤ 0.10 ومقارنة NDCG@10 بنموذج ماركوف المقدَّر)، S4 طيّة فعلية بلا NaN وبخسارة نهائية ≤ 0.9 الأولى، S5 انحراف خمس بذور (للإبلاغ فقط: 0.0118، يتجاوز الهدف 0.005 ويُوثَّق)، S6 اختبارات القناع. **البوابة:** `run_gru.py` يرفض العمل (`SystemExit`) ما لم يحمل `gru_sanity.json` الحقل `gates_passed`. وتوثّق `gru_sanity.md` أن أول تشغيل لـS2 فشل (L − H = 0.055) لأن الدفعة احتوت بادئات متطابقة بأهداف مختلفة (حد بايز غير قابل للاختزال)، فصُحّح تصميم الاختبار لا النموذج.

## 3.8 `hybrid.py`: الدمج الرتبي وقاعدة القبول

- **التطبيع:** `rank_normalize(scores, cand)` يحوّل درجات كل مكوّن إلى r̃ ∈ [0,1] داخل مرشحي المتعلم بـ**الرتبة الوسطى عند التعادل** (`mid_ranks`، D-32)، ويعطي 1 إن بقي مرشح وحيد.
- **الدمج:** `score(u,i) = Σ w_m r̃_m(u,i)` بأوزان على السمبلكس (`fuse`). `simplex_grid(m, step)` يولّد الشبكة: خطوة 1/4 لمكوّنين أو ثلاثة (5 و15 نقطة) و1/3 لأربعة (20 نقطة)، والخطوة 0.1 تحليل حساسية فقط (D-29). `tune_weights` يبحث في الشبكة على نافذة التحقق بمقياس NDCG@10.
- **القبول:** `accept_component(name, lifts_per_presentation, seed_sd)` يقبل المكوّن إذا استبعد فاصل bootstrap-t (95%) على التسعة رفعَ NDCG@10 المقاس على **نوافذ اختبار 2013** الصفر، وتجاوز الرفع انحراف البذور للمكوّنات العشوائية. `greedy_forward` يبحث جشعاً من أفضل مكوّن منفرد حتى `MAX_COMPONENTS = 4`، وتطبّق **أرضية الشخصنة** (D-30): إن خلت التركيبة المقبولة من مكوّن شخصي {WRMF، Item-kNN، التسلسلي، CBF} أُضيف الأكبر رفعاً ووُسم `floor`.

## 3.9 `stats.py`: الاستدلال الإحصائي بـnumpy وحده

وحدة الإحصاء هي العرض (متوسط البذور ثم متوسط الأصول الثلاثة). الدوال العامة:

| الدالة | الوظيفة |
|---|---|
| `cluster_bootstrap_t(diffs, n_boot=10000, seed=0)` | الفاصل المعيَّر t* = (m_b − Δ̄)/(max(s_b,1e-12)/√n)؛ ووسم «منحلّ» وحد ±∞ عند تطابق الفروق (D-52) |
| `cluster_bootstrap_t_ci` / `cluster_bootstrap_ci` / `t_interval` | واجهة (mean, lo, hi)؛ الفاصل المئيني والتقليدي للملحق فقط |
| `sign_flip_test(diffs, exact_max_n=20)` | اختبار قلب الإشارات ثنائي الطرف: إحصاء دقيق على 2ⁿ (8,192 لـn = 13)، أو مونت-كارلو فوق الحد |
| `holm(pvals)` | تصحيح Holm؛ العائلة الثابتة m = 4 = {H1، H2-أ، H3، H4-أ} (D-23) |
| `margin_test`، `confirmed_with_margin` | اختبار الهامش (Δ − δ) والوسم «مؤكَّدة بهامش»، وصفيان |
| `verdict(mean, lo, hi, p_holm)` | جدول الحكم الأحادي بالأسبقية: مؤكَّدة ← مدحوضة عكسياً ← مدحوضة ← غير حاسمة |
| `verdict_bidirectional(...)` | جدول H3 السداسي: تفوّق مؤكَّد، تأخّر مؤكَّد، تكافؤ، تأخّر، مدحوضة، غير حاسمة |
| `compare(diffs)` | يجمع المتوسط والفاصلين وp في قاموس |
| `confirmation_power(mu, sigma, n=13, ...)` و`mde80(sigma, n=13, ...)` | قوة التأكيد الكاملة بالقاعدة الأحادية وHolm = 4، وأصغر أثر بقوة 80% (D-46) |
| `t_quantile` | توزيع t بالتنصيف على دالة بيتا الناقصة المنظَّمة |

الثوابت: `DELTA = 0.02`، `ALPHA = 0.05`. والمعاملات المسجَّلة قبل التجميد لا تُغيَّر.

## 3.10 `harness.py` و`components.py`

`harness.run_job(p, cut, model_names, exclusion, seeds, tasks)` ينفّذ حلقة «اضبط ثم اختبر» لعرض ونقطة قطع: يضبط كل نموذج على نافذة التحقق (≤ `BUDGET = 20` إعداداً بمقياس `NDCG@10`، ببذرة 0 للعشوائيات)، ثم يعيد التدريب على d ≤ t بالإعداد المختار ويقيّم النافذة بخمس بذور (`SEEDS = (0,1,2,3,4)`) للنماذج العشوائية. تُكتب الصفوف بالشرائح `all` و`cold_q1` (الربع الأدنى من الموارد المختلفة بين المقيَّمين) و`top_q4` و`lt5` (أقل من 5 موارد، وصفي) مع `val_NDCG@10` لحساب فجوة التفاؤل (D-29). WRMF تُعامل نقاط تفتيشه (10، 15، 25) إعداداتٍ غير محسوبة في الميزانية (ADR-004 §2.4). و`eval_rows` يكتب صفوفاً بصيغة `baselines.csv` لأي مصفوفة درجات (تستعملها تجارب GRU والاستئصال).

`components.py` ذاكرة درجات المكوّنات: `save_scores` / `load_scores` / `has_scores` تخزّن مصفوفة float32 U×I لكل (عرض، قطع، مكوّن، طور، بذرة) في `data/cache/components/<pres>_<cut>/<comp>_<phase>_s<seed>.npy`، فيعيد البحث الجشع ترتيب الدرجات دون إعادة التدريب. و`parse_config` يعكس `harness.config_key` (من النص `alpha=20;f=16;signal=L3(tau=14,beta=2)` إلى قاموس)، و`selected_configs` يقرأ الإعدادات المختارة على التحقق للمهمة A من `baselines.csv`.

## 3.11 `learners.py`: تحليل المتعلمين

- **الملامح:** `vle_features(events, students, t_c)` (M1): `active_days` و`gap_sd` و`first_day` (t_c+1 لمن لا نشاط له) وحصص نقرات 19 نوع نشاط `share_<type>`. `total_clicks` (M0). `academic_features` (M2 = M1 + نسبة الالتزام بالمواعيد `on_time_ratio` ومتوسط الدرجات `mean_score` ومؤشر `no_score` والمحاولات السابقة والساعات المدروسة ويوم التسجيل). لا تدخل السمات الحساسة أي ميزة (D-21).
- **التجميع:** `kmeans_pp_init` و`lloyd` و`kmeans(X, k, seed, n_init=10)`، ومقاييس الجودة `silhouette` و`silhouette_fast` و`davies_bouldin` و`adjusted_rand_index`، و`choose_k(X)` بقاعدة §4.7.2: أصغر k في أفضل اثنين لكل من silhouette وDBI مع متوسط ARI ≥ 0.8 على خمس بذور، وإلا فأفضل silhouette موسوماً «غير مستقر» (`ClusterChoice.stable`).
- **التصنيف:** `logistic_fit(X, y, lam)` (L2 بنيوتن، حد قاطع بلا عقوبة) و`logistic_predict`، و`cart_fit(X, y, max_depth=4, min_leaf=20)` و`cart_predict` و`cart_rules` (شجرة جيني)، و`gini`.
- **التقييم:** `roc_auc` (مان-ويتني بالرتب الوسطى) و`average_precision` و`youden_threshold` و`threshold_metrics` و`brier`.

`experiments/learner_analysis.py` يشغّلها بترك عرض واحد خارج التدريب (LOPO) داخل 2013 عند الأيام 56 (الأساسي) و28 و112: M0 (مجموع النقرات) وM1 (ملامح VLE) وM2 (+الأكاديميا)، λ من {1e-3، …، 10} بترك عرض داخلي، والهدف `final_result ∈ {Fail, Withdrawn}` مقابل `{Pass, Distinction}` باستبعاد المنسحبين قبل القطع، وتُحذف من التدريب تسجيلات الطلاب الموجودين في 2014 (D-47). عتبات Youden من التنبؤات خارج الطيّة: M0 = 0.4744 وM1 = 0.4557 وM2 = 0.4074.

## 3.12 `serving.py`: خدمة إعادة التشغيل (D-49)

الصنف `Engine(frozen=FROZEN, artifacts=ART, presentations=None, student_assessment=None, allow_confirmatory=False, cluster_cache_dir=None)` هو **المكان الوحيد** الذي تُحسب فيه التوصية والتفسير والملف والنظرة العامة (نمط Facade). الشروط التنفيذية لـD-49:

1. المكوّنات الثقيلة (WRMF وGRU-lite) تأخذ معاملاتها من أقرب قطع c ≤ اليوم في `artifacts/<pres>/<c>/` (`wrmf.npz` أو `gru.npz`).
2. حالة المتعلم تُحسب عند يوم الطلب: «fold-in» لـWRMF بخطوة ALS نصفية مغلقة، أو تمريرة GRU أمامية على التاريخ ≤ اليوم. لا تدريب وقت الطلب.
3. المكوّنات الخفيفة (Recent-Pop وSKNN وMarkov وItem-kNN وCBF وC6 وC7) تُحسب عند اليوم نفسه.
4. أوزان الهجين هي أوزان القطع c من `hybrid_frozen.json`.
5. قبل اليوم 70 لا مكوّن ثقيل: تُستعمل الخفيفة بأوزان المنوال المعاد تطبيعها ويُصرَّح بذلك في `note`.
6. كل استجابة تحمل `model_cut` (تاريخ النموذج).
7. لا رقم تقييم يُشتق من إعادة التشغيل.

المعامل `allow_confirmatory` (FR-40) لا يُقبل إلا إذا وُجد `results/conf2014/verdicts.csv` والملف `LOCK` وإلا رُفع `ConfirmatoryAccessError`؛ وبه تُفتح عروض 2014 للإعادة بعد التشغيل التأكيدي وحده. الأساليب العامة: `plan(name, day)` ← (قطع، مكوّنات، أوزان، إعدادات، ملاحظة)؛ `recommend(name, registration, day, k=10, exclude_seen=True)` يعيد قائمة عناصر لكل منها `id_site` و`activity_type` و`score` و`components{m: rtilde, weight, contribution, raw}` و`explanation{main, secondary}` و`model_cut` و`day` و`note` و`known_learner`؛ `learner_profile(name, registration, day, risk_model="M1")` (ملامح وعنقود اليوم 56 ودرجة الخطر، للمدرّس فقط)؛ `presentation_overview(name, day, risk_model="M1")`؛ وأضيفت حديثاً (§8.4 من وثيقة التصميم، D-68) `learner_table(name, day)` (جدول المدرّس المتجهي مخزَّناً لكل عرض ويوم) و`cluster_summary(name)` (k والاستقرار والأحجام ووصف عربي حتمي وإسقاط PCA بـSVD) و`registrations(name, day)` (قائمة بيضاء بلا `final_result`) و`cluster_choice_at(name, day)` (اختيار k-means++ عند اليوم t نفسه مخزَّناً في الذاكرة وفي `data/cache/serving_clusters/<pres>_<day>.npz` ببصمة SHA-256 لمنظر التدريب، ولا يُخدَم إلا لذلك اليوم) و`warm(name, days)` (تسخين درجات المكوّنات على شبكة أسبوعية والقطوع). وعلى مستوى الوحدة دوال بالأسماء نفسها تستدعي `engine()` (مثيل وحيد كسول).

التفسير يأتي من المساهمة الفعلية w_m·r̃_m: يُعرض المكوّن الأعلى مساهمة، والثاني إن تجاوزت مساهمته ثلث المجموع، بقوالب `TEMPLATES` (مثلاً «شائع لدى متعلمين بنمط مشابه لنمطك» للمكوّن C7) ودليل `evidence` من `_evidence`. ذاكرات `lru_cache` داخل المحرك تحفظ منظر التدريب (طيّة اليوم) ودرجات المكوّنات والملامح، ما يجعل الطلب الأول لـ(عرض، يوم) ≈ 10 ث (منها 9.9 ث `choose_k` في C7) ثم يتراجع الزمن إلى أقل من 0.01 ث للمتعلمين الآخرين في اليوم نفسه؛ والتخزين الدائم لاختيار العنقدة (D-68) يُلغي كلفة `choose_k` في التشغيلات اللاحقة لليوم نفسه.

الخطر: `_risk` يعيد **درجة خطر نسبية غير معايَرة** `score` (D-65) من نموذج M1 في أقرب `risk_{28,56,112}.json` ≤ اليوم (مدرَّب على العروض الثمانية الأخرى، `provenance = lopo_2013`، فلا تسرب من العرض المعروض)، مع `threshold` (Youden) و`above_threshold` و`factors` (w·z) و`top_factors`، ولا تقدير قبل اليوم 28؛ ولعروض 2014 يقرأ `_risk_spec` النماذج المجمَّدة من `results/frozen/risk_final.json` (`test_2014`). و`_cluster` يسند التسجيل إلى مراكز اليوم 56 من `clusters_56.npz` ولا يعمل قبل اليوم 56.

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
| `risk_final` | نماذج الخطر النهائية على التسعة (D-58) | `results/frozen/risk_final.json` (لم يُشغَّل بعد) |
| `report` | يعيد توليد `summary.md` من CSV دون إعادة تشغيل | `python3 -m src.ml.experiments.report results/dev2013` |

الوحدة `plots.py` (جديدة، غير متتبَّعة بعد) مولّد أشكال SVG بلا matplotlib يكتب مع كل شكل ملف CSV لبياناته، وتخدم أشكال التشغيل التأكيدي المخطط.

خيارات مفيدة: `run_baselines --presentations FFF_2013J --cuts 70 --models B2_Pop B3_RecentPop --workers 4 --exclusion {E5,E4,none} --out DIR` (حساسية E تُكتب إلى `--out` مختلف). وتقبل `run_gru` و`run_ablation` الخيارات `--presentations` و`--cuts` و`--workers`.

### ملفات `results/dev2013/` ملفاً ملفاً

| الملف | ما يحويه |
|---|---|
| `baselines.csv` | صف لكل (مهمة، نموذج، عرض، أصل، بذرة، شريحة): الإعداد المختار `config` و`val_NDCG@10` والزمن و`n_eval` و P/R/HR/NDCG/MRR عند 5/10/20 وCoverage وPopBias (شريحة `all`) |
| `tuning.csv` | كل إعداد جُرّب في مرحلة الضبط وقيمته على التحقق للمهمتين (`val_NDCG@10_A/B`) |
| `timing.csv` | زمن كل نموذج لكل (عرض، أصل، مرحلة) وأقصى RSS |
| `folds.csv` | لكل (عرض، أصل): الكتالوج والكثافة والمقيَّمون وحصة الأهداف غير القابلة للوصول |
| `run_meta.json` | الأمر و`git_commit` وبصمة البيانات وإصدارات python/numpy/pandas والزمن |
| `summary.md` | جداول المتوسط ± الانحراف (مولَّدة بـ`report.py`) |
| `eda*.csv` و`eda.md` | الإحصاءات الوصفية وإعادة إنتاج فحص الزميل |
| `gru_sanity.md/json` | نتائج بوابة الصحة |
| `gru.csv` | نتائج GRU-lite (النموذجان `GRU_lite` و`GRU_lite_dh128`) بصيغة `baselines.csv` |
| `gru_tuning.csv` | لكل (عرض، قطع، إعداد): أفضل حقبة ومنحنيا الخسارة والتحقق |
| `gru_meta.json`، `ablation_meta.json` | زمن التشغيل وCPU وعدد العمليات (لا معاملات) |
| `ablation_signals.csv`، `ablation_tuning.csv` | الاستئصال بعمود `variant` ∈ {L0، L1، L2، L3، Wstar} |
| `learner_auc.csv`، `learner_h4a_summary.csv` | AUC لكل عرض ونموذج، وملخص H4-أ (Δ ومتوسطات وفاصل وp) |
| `learner_clusters.csv`، `learner_fairness.csv`، `learner_meta.json`، `learner_analysis.md` | العناقيد (k، الاستقرار، الأحجام، الملامح)، والإنصاف الوصفي، وλ وعتبات Youden، والتقرير |
| `hybrid_frozen.json` | **التركيبة المجمَّدة** (§9.1) |
| `hybrid_acceptance.md`، `hybrid.csv`، `hybrid_meta.json` | تقرير الجولات الجشعة، ونتائج الهجين لكل (عرض، قطع)، وH1/H3/H4-ب وصفياً |
| `h4b.csv`، `h1_decomposition.csv` | H4-ب الاستكشافية (الربع الأدنى مقابل الأعلى)، وتفكيك H1 (D-60) |
| `mde80.md/json` | MDE80 وσ وقوة التأكيد عند δ و1.5δ و2δ لكل فرضية |
| `../access_log.jsonl` | سجل قراءات D-47 |

## 3.14 `artifacts/`

`artifacts/<presentation>/` يحوي `risk_{28,56,112}.json` (نموذجا Logistic M1 وM2 بـ`features` و`weights` و`lambda` و`youden_threshold` و`trained_on`: العروض الثمانية الأخرى)، و`clusters_56.npz` (المراكز `centres` ومعاملات `mu` و`sd` و`k` و`stable` و`features` و`students` و`labels`)، ومجلدات القطوع `70/` و`126/` و`182/` التي تحمل `wrmf.npz` و`gru.npz` إن دخل أحدهما التركيبة المجمَّدة. التركيبة الحالية (C7 وSKNN) لا تحوي مكوّناً ثقيلاً، فمجلدات القطوع فارغة. الحجم الكلي ≈ 0.5 MB. وتُعاد كلها بـ`build_artifacts`، وهي لازمة للخلفية: غيابها يعطي 503 `artifacts_missing`.

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
| `/api/recommendations` | `registration`، `day`، `k` 1..20، `task=A\|B` | `items[{rank,id_site,activity_type,score,contributions,reason,reason_secondary}]` و`components` و`context` و`provenance.model_cut` |
| `/api/explanations/{reg}/{id_site}` | `day`، `task` | مكوّنات `{weight, r_tilde, contribution, evidence, sentence}`؛ 404 `item_not_in_list` لمورد خارج أفضل 20 |
| `/api/learner/{reg}/history` | `day`، `window` (28) | `daily` و`recent` (3) و`active_days` |
| `/api/instructor/overview` | `presentation`، `day` | مؤشرات وملخص الملامح ومدرج الخطر والتغطية |
| `/api/instructor/clusters` | `presentation`، `day` | k والاستقرار والجودة وأحجام ووصف عربي حتمي وإسقاط PCA |
| `/api/instructor/learners` | `presentation`، `day`، `cluster`، `risk=all\|above`، `sort`، `limit≤500`، `offset` | `{items,total,limit,offset}` |
| `/api/instructor/learner/{reg}` | `day` | العنقود والخطر بعوامل w·z والملامح مقابل الوسيط وأفضل 3 توصيات و`outcome: null` دائماً |

صيغة `registration` = `^[A-G]{3}_20(13|14)[BJ]-\d+$` وتُحلَّل إلى (العرض، `id_student`). والمهمة الافتراضية A (موارد جديدة) لأن التوصية إرشاد إلى ما لم يُكتشف بعد.

## 4.3 أمثلة طلب/استجابة من التشغيل الفعلي

كل ما يلي ناتج تشغيل الخادم على FFF_2013J (`--warm`). **توصية:**

```
$ curl 'localhost:8012/api/recommendations?registration=FFF_2013J-371869&day=75&k=2'
{"registration":"FFF_2013J-371869","presentation":"FFF_2013J","id_student":371869,
 "requested_day":75,"snapshot_day":75,"task":"A","status":"ok","known_learner":true,"note":null,
 "context":{"week":11,"next_assessment":{"type":"TMA","day":96,"days_ahead":21},"active_days_to_date":93},
 "components":[{"id":"similar_pop","label":"شعبية الأنماط المشابهة (7)","weight":0.75},
               {"id":"sknn","label":"SKNN (4)","weight":0.25}],
 "items":[{"rank":1,"id_site":716344,"activity_type":"oucontent","score":0.9963,
           "contributions":{"similar_pop":0.75,"sknn":0.2463},
           "reason":"شائع لدى متعلمين بنمط مشابه لنمطك","reason_secondary":null}, ...],
 "provenance":{"run_id":"replay-dev2013-62e2651927","role":"dev","model_cut":70}}
```

**تفسير** المورد الأول نفسه (`/api/explanations/FFF_2013J-371869/716344?day=75`): مكوّنان، لكل منهما `r_tilde` و`contribution` و`evidence` من نوع `count` (85 متعلماً مشابهاً في نافذة 3 أيام، `scope: "similar"`) أو `item` (المورد 716219 من نوع forumng زاره المتعلم 67 يوماً، آخرها اليوم 75) والجملة المعروضة. **جدول متعلمين** (للمدرّس):

```
$ curl 'localhost:8012/api/instructor/learners?presentation=FFF_2013J&day=75&sort=-risk&limit=1'
{"items":[{"registration":"FFF_2013J-590714","cluster":{"id":0,"label":"أيام نشطة قليلة · نشاط متقطع"},
  "active_days":1,"last_access_day":-7,"on_time":"0/2",
  "risk":{"score":0.999,"cut_day":56,"threshold":0.456,"above_threshold":true,
          "provenance":"lopo_2013","top_factor":"حصة page"}}],"total":1872,"limit":1,"offset":0}
```

قبل أول قطع (اليوم 40): `model_cut: null` و`note` يشرح الرجوع إلى المكوّنات الخفيفة («اليوم 40 قبل أول قطع (70): لا مكوّن ثقيل…»).

## 4.4 صيغة الأخطاء، و409 لعروض 2014

كل خطأ بالصيغة `{"error": {"code", "message", "details"}}` ورسالة عربية ورمز ثابت، مع `Cache-Control: no-store`:

| HTTP | الرمز | الحالة |
|---|---|---|
| 404 | `presentation_not_found`، `registration_not_found`، `item_not_in_list`، `instructor_disabled`، `not_found` | معرّف غير موجود، أو مورد خارج أفضل 20، أو تشغيل بـ`--no-instructor`، أو مسار مجهول |
| 405 | `method_not_allowed` | أي طريقة غير GET |
| 409 | `confirmatory_locked` | أي عرض 2014، على **كل** المسارات |
| 422 | `validation_error` (مع `details.errors[{field, reason, type}]`) | مدخلات غير صالحة، مثلاً `day` > 400 أو `registration` بصيغة خاطئة |
| 422 | `day_out_of_range` (`details.max_day`) | اليوم أكبر من طول العرض |
| 422 | `day_before_first_snapshot` (`details.first_day = 56`) | المدرّس قبل اليوم 56 (أول عنقدة)؛ الواجهة تنقل الشريط تلقائياً |
| 503 | `artifacts_missing` | `hybrid_frozen.json` أو مخرجات القطوع غير موجودة |

حاجز 2014 هنا بطبقتين فوق حاجز `src/ml`: `Repository.check_presentation` يرفع 409 **قبل أي قراءة** لأي اسم من `CONF_PRESENTATIONS`، ومعالج `ConfirmatoryAccessError` يحوّل الاستثناء المقابل إلى 409 أيضاً. ويعرض `/api/presentations` عرضاً مقفلاً واحداً (BBB_2014J) للتمثيل بتسجيلات وطول 0، فلا يُقرأ شيء من 2014.

## 4.5 التسخين والكاش والأداء المقاس

التسخين (`--warm`) خيط خلفي يشغّل `Services.run_warmup`: يبني قوائم العروض، ثم لأول تسجيل في العرض الافتراضي (FFF_2013J) يحسب التوصية (ولقطة المدرّس إن كان اليوم ≥ 56)، ثم يستدعي الخطّاف `serving.warm` إن وُجد (D-68) لكل يوم في `--warm-days` (الافتراضي في `settings.WARM_DAYS` = 75، 56، 70، 112، 126، 182)، ويدعم `--warm-weekly` شبكة أسبوعية. وأي `--host` غير 127.0.0.1 يطلق تحذيراً لغياب المصادقة (D-66: عرض توضيحي بلا أمان وصول؛ ويظهر `bind_host` و`access_notice` في `/api/meta`). فشل التسخين تحسيني ويُسجَّل `failed` في `/api/health` ولا يوقف الخدمة. الذاكرات: LRU للتوصيات (1024 قائمة من 20)، ولقطات المدرّس (6)، و`lru_cache` داخل `Engine`. وهي ذاكرات لا مصدر حقيقة: مسحها لا يغيّر أي ناتج.

قياس `python3 -m src.backend.bench http://127.0.0.1:8012` (20 طلباً لكل مسار؛ FFF_2013J، اليوم 75، 4 أنوية) **بعد التسخين**:

| المسار | الأول (ms) | الوسيط (ms) | الأقصى (ms) |
|---|---|---|---|
| health | 1.4 | 1.0 | 1.8 |
| meta | 1.9 | 1.6 | 2.4 |
| presentations | 1.7 | 1.5 | 1.8 |
| registrations (100) | 2.2 | 2.4 | 3.1 |
| recommendations | 7.3 | 4.9 | 6.0 |
| explanations | 25.3 | 25.0 | 30.1 |
| history | 6.1 | 5.4 | 8.3 |
| instructor/overview | 1.4 | 1.3 | 1.7 |
| instructor/clusters | 2.2 | 2.2 | 3.7 |
| instructor/learners (100) | 8.3 | 6.0 | 6.9 |
| instructor/learner | 2.1 | 1.7 | 3.7 |

كلها ≪ 200 مللي ثانية (NFR-01، ويفرضه `test_latency_after_warmup`). أما **بلا تسخين** فالطلب الأول لـ`recommendations` ≈ 10.3 ث ولـ`instructor/overview` ≈ 11 ث (بناء لقطة اليوم: الملامح والخطر والعناقيد والتغطية لكل المتعلمين)، ثم الوسيط 4.8 و1.1 ms (قياسات README). ويوم جديد غير مسخَّن يكلّف ≈ 10 ث للأول، وعرض آخر ≈ 8.3 ث، وزمن تسخين الأيام الستة ≈ 83 ثانية (≈ 71 منها في الخطّاف `serving.warm`، D-68). ولا يجوز تقليص `n_init` أو البذور أو k لتسريع الطلب البارد (D-68).

## 4.6 الاختبارات والعميل ASGI المدمج

`tests/asgi_client.py` عميل ASGI صغير بلا httpx: يبني `scope` ويستدعي `await app(scope, receive, send)` مباشرة ويعيد `Response(status, headers, body)` مع `.json()` و`.text`، ويغلّفه `Client.get(url)`. مجموعات الاختبار: `test_contract_no_risk` (لا خطر ولا عنقود ولا سمات حساسة ولا `final_result` في نماذج المتعلم، بقائمة بيضاء للمدرّس، و`outcome` دائماً null)، و`test_contract_json` (اختبار العقد على JSON المسلسَل فعلياً، D-70)، و`test_static_errors` (الأخطاء الموحدة، 409 لـ2014، `--no-instructor`، الملفات الثابتة؛ لا تحتاج البيانات)، و`test_api_live` (يقارن مفاتيح كل استجابة بملف mock المقابل ويفحص المنطق والتطابق مع `Engine` والأداء؛ يُتخطّى إن غابت البيانات). تفاصيل الأعداد في الفصل 7.

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

الحالة كلها في الرابط (`state.ts`: `readState` و`writeState(patch, push)` و`carryQuery`): `p` العرض، `r` التسجيل، `d` اليوم، `task` (A|B)، `cl` العنقود المصفّى، `f` (all|above|idle)، `sort` (مثل `-risk`). تُحذف القيم الافتراضية من الرابط، فيمكن مشاركة أي منظر بنسخ الرابط، ويُحفظ الاختيار عبر الصفحات عن طريق `carryQuery`. الصفحات: `home.ts` معالج الاختيار، و`learner.ts` يعرض أفضل 10 مع عدّاد طلبات `seq` لتجاهل الاستجابات المتأخرة، و`instructor.ts` للمؤشرات والعناقيد والجدول والدرج.

تدقيق إمكانية الوصول (WCAG 2.2 AA) مطبَّق بالبناء: `lang="ar" dir="rtl"` وخصائص CSS المنطقية، ورموز التصميم في `tokens.css` بتباين نص ≥ 4.5:1 وحدود عناصر التحكم ≥ 3:1، ولا اعتماد على اللون وحده (أسماء نصية وأشكال مميزة للعناقيد وإطار متقطع ونص «فوق العتبة»)، ولوحة المفاتيح كاملة (شريط اليوم والجدول بالأسهم وEnter، وEsc يغلق لوحة «لماذا؟» والدرج ويعيد التركيز)، وحلقة تركيز سميكة وأهداف لمس ≥ 44px، و`aria-live` و`aria-busy` و`aria-sort`، و`prefers-reduced-motion`، وبلا تمرير أفقي من 360px. وواجهة المتعلم بلا أي حقل خطر أو عنقود (NFR-09) ولا سمات حساسة (D-21). وبعد D-65 يقرأ `types.ts` و`instructor.ts` الحقل `risk.score` ويعرضه بعنوان «درجة الخطر النسبية»، وبعد D-70 معرّف المكوّن السابع `similar_pop` (`labels.ts`).

## 5.5 لقطات الشاشة وكيف تُولَّد

سكربتان بـPlaywright العالمي (`NODE_PATH=$(npm root -g)`):

- `src/frontend/screenshots.js` (بوضع المحاكاة): يخدم `dist/` بـ`python3 -m http.server` على المنفذ 8765، ويلتقط ست لقطات لكل من سطح المكتب (1440×900) والجوال (375×800)، ويفحص التمرير الأفقي وأخطاء الكونسول، ويكتب إلى `deliverables/05-user-guide/screenshots/` (`01-home` إلى `06-learner-day-before-snapshot`). يتطلب `build.sh` قبله.
- `src/backend/e2e/live-screenshots.js`: لقطات مع الخادم الحي (بلا mock) باسم `live-*.png`، ويُشغَّل بعد `python3 -m src.backend --warm`.

# 6. أدوات البناء `scripts/`

| الأداة | الأمر | الوظيفة |
|---|---|---|
| `build_docx.py` | `python3 scripts/build_docx.py OUT.docx IN.md [--title ... --title-en ... --subtitle ...]` | Markdown ← Word RTL: يمرّ على pandoc (امتدادات pipe_tables وgrid_tables وfenced_divs وfootnotes…) بـ`-M lang=ar -M dir=rtl` وفهرس بعمق 3، ثم يعالج python-docx الخطوط (Simplified Arabic للعربي وTimes New Roman للاتيني) وأخيراً الفقرات والجداول RTL، ويحمي الرموز المتماثلة من الانعكاس، ويضيف غلافاً (العنوان والمشرف والجامعة والسنة) وترقيم صفحات ثم يمرّر الملف على `lo_update_toc.py` ما لم يُعطَ `--no-update-toc`. أنماط الشيفرة (`Source Code` و`Verbatim Char` و`SourceCode`) تُستثنى من RTL فتبقى LTR |
| `lo_update_toc.py` | `python3 scripts/lo_update_toc.py file.docx [...]` | يفتح الملف في LibreOffice عبر UNO ويحدّث الفهارس ويحفظ docx، لأن pandoc يكتب الفهرس حقلاً فارغاً لا يملؤه إلا Word عند الفتح |
| `svg2png.js` / `svg2png.py` | `node scripts/svg2png.js in.svg [--out-dir DIR --scale 2 --width 1400]` | تصيير SVG أو HTML إلى PNG بـPlaywright (Node) وChromium؛ والنسخة `.py` غلاف يستدعي `.js` |
| `build_pptx.py` | `python3 scripts/build_pptx.py [--spec X.json --out Y.pptx]` | مولّد العرض التقديمي بـpython-pptx من مخطط `docs/working/07-presentation.json`: شرائح RTL بنسبة 16:9 وأنواع عنوان وبطاقات وإحصاءات وتدفق وجدول ومخطط وأسئلة |

أمر بناء هذا الملف نفسه:

```
python3 scripts/build_docx.py "deliverables/04-code-documentation/توثيق-الكود-البرمجي.docx" docs/working/04-code-documentation.md --title "توثيق الكود البرمجي" --title-en "Source Code Documentation" --subtitle "نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم — المرحلة الرابعة"
```

# 7. الاختبارات

## 7.1 مجموعات الاختبار ونتائجها الفعلية

كلها `unittest` من المكتبة القياسية، وقد شُغّلت جميعها أثناء كتابة هذا الملف:

| المجموعة | الملف | العدد | ما تغطيه |
|---|---|---|---|
| ML: GRU | `test_gru.py` | 7 | المثال العددي 4.4.2، فحص التدرج، بقاء الحالة في الخطوات المحشوة، التقطيع بنافذة طويلة = الحساب الكامل، الأهداف، قناع المهمة A، قص Adam |
| ML: الهجين والإحصاء | `test_hybrid_stats.py` | 20 | الجدول 14 (الدمج الرتبي)، حجم السمبلكس، الرتبة الوسطى، البحث عن الأوزان، قاعدة القبول والجشع والأرضية، قلب الإشارات وHolm وbootstrap والتغطية، جداول الحكم 19-أ وH3، الهامش والقوة، حالة الانحلال، توزيع t |
| ML: المتعلمون | `test_learners.py` | 10 | k-means++ وsilhouette وDBI وARI واسترجاع عناقيد مفصولة، Logistic (مثال وفصل تام وبُعد واحد)، جيني، AUC/AP/Youden، الملامح |
| ML: المقاييس | `test_metrics.py` | 9 | الجدول 19 يدوياً، المتجه = المرجعي، المثالي = 1، HR النظري للعشوائي، التعادل، غير القابل للوصول في IDCG، مئين الشعبية |
| ML: النماذج | `test_models.py` | 23 | Item-kNN وSKNN/V-SKNN (واستبعاد سلال المستعلِم) وMarkov وWRMF (خطوة ALS واحدة، رتابة الخسارة، استرجاع رتبة منخفضة، حتمية البذرة) وEASE (شروط KKT) وفضاءات ADR-004 والنماذج البسيطة وCBF وواجهة `recommend` وC6 وC7 |
| ML: الخدمة | `test_serving.py` | 6 | الخطة قبل أول قطع، بنية التوصية وغير المزار، عدم استعمال بيانات المستقبل، fold-in، الملف والنظرة العامة، رفض 2014 |
| ML: الإشارة | `test_signals.py` | 7 | الجدول 8، تداخل المستويات، وسيط النوع من التدريب وحده، الثقة الثنائية |
| ML: التقسيم | `test_splits.py` | 14 | النوافذ، منع التسرب، الكتالوج والاستبعاد، المهمتان، غير القابل للوصول، مفاتيح التعادل، حاجز 2014، قراءة D-47 (الأعمدة والسجل والرفض) |
| **مجموع ML** | `python3 -m unittest discover -s src/ml/tests` | **96** | ناجحة، ≈ 3.8 ثانية، بلا البيانات الخام |
| الخلفية: العقد | `test_contract_no_risk.py` | 5 | نماذج المتعلم بلا خطر ولا عنقود ولا سمات حساسة، والمدرّس بلا سمات حساسة، `outcome` null، لا حقول أرقام تقييم، `model_cut` في `provenance` |
| الخلفية: الأخطاء والثابت | `test_static_errors.py` | 9 | الصحة، 404 للمسار المجهول، 405 لـPOST، 409 لـ2014 على كل المسارات، 404 لعرض مجهول، 422، `--no-instructor` وإخفاء الصفحة، الجذر يخدم `index.html` |
| الخلفية: JSON المسلسَل | `test_contract_json.py` | 4 | D-70: لا مفاتيح محظورة في JSON المتعلم، التسجيلات بلا `date_unregistration` و`final_result`، تسمية دليل C7، قائمة بيضاء للمدرّس |
| الخلفية: الحي | `test_api_live.py` | 21 | العقود مقابل mock، المنطق، التطابق مع `Engine`، الأداء بعد التسخين، إعلان «بلا أمان وصول» ودرجة الخطر في `/api/meta` (تحتاج البيانات) |
| **مجموع الخلفية** | `python3 -m unittest discover -s src/backend/tests -t .` | **39** | ناجحة، ≈ 99 ثانية (أغلبها تسخين أول يوم) |
| الواجهة | `tsc --noEmit -p tsconfig.json` | — | فحص أنواع strict؛ خرج 0 بلا أخطاء. لا اختبارات DOM آلية؛ يُتحقق بصرياً بـ`screenshots.js` وبفحص التمرير الأفقي وأخطاء الكونسول |

## 7.2 المخرجات المسجَّلة وقت الكتابة

```
$ python3 -m unittest discover -s src/ml/tests
Ran 96 tests in 4.084s        OK
$ python3 -m unittest src.backend.tests.test_contract_no_risk src.backend.tests.test_static_errors
Ran 14 tests in 0.083s        OK        (السريعة، بلا بيانات)
$ python3 -m unittest discover -s src/backend/tests -t .
Ran 39 tests in 98.706s       OK
$ cd src/frontend && npx tsc --noEmit        # exit code 0، بلا أخطاء
$ python3 -m src.backend --help               # يطبع الخيارات المذكورة في §2.5
```

الجولة الأولى لمجموعة الخلفية الكاملة (34 اختباراً في 84 ثانية) سبقت إضافة الفريق `test_contract_json.py` (4 اختبارات) واختبار إضافي في `test_api_live.py` أثناء إعداد هذه الوثيقة؛ والأعداد في الجدول أعلاه هي ما أُعيد قياسه بعدها. ومن جهة أخرى اختبارات `src/ml` لا تكتب في `results/access_log.jsonl` الحقيقي (تستعمل مجلداً مؤقتاً وقارئاً وهمياً)؛ السطور المضافة هناك أثناء الإعداد صادرة عن تشغيلات `learner_analysis`/`build_artifacts` الفعلية للفريق.

## 7.3 ما لا تغطيه الاختبارات

لا اختبار آلي لسلوك المتصفح (DOM)؛ يُغطّى بفحص الأنواع وبلقطات Playwright (التمرير الأفقي وأخطاء الكونسول). ولا اختبار لـ`run_confirmatory` لأنه لم يُكتب بعد.

## 7.4 تناقضات رُصدت بين README والكود

| # | README / الوثيقة تقول | الكود/التشغيل يقول | الأثر |
|---|---|---|---|
| 1 | `src/ml/README.md`: «92 اختباراً» (مرتين) | `discover -s src/ml/tests` يجد **96** اختباراً (7+20+10+9+23+6+7+14) | عدد قديم؛ يُحدَّث |
| 2 | README الـml (القرار 9): خطر اللوحة من M2 بمعامل `risk_model` | الافتراضي في `serving.learner_profile` و`presentation_overview` هو `"M1"` (D-56)، وكذلك في الخلفية | نص قديم قبل D-56 |
| 3 | README الـml يعرض «أمراً واحداً» لإعادة الإنتاج | لا يوجد `reproduce_dev`؛ README نفسه يسرد تسع خطوات | الأمر الواحد شرط تجميد لم ينفَّذ (D-62 ش5) |
| 4 | README الـml لا يذكر `experiments/risk_final.py` ولا `h1_decomposition.csv` ولا `results/frozen/` | الملفان موجودان (والمجلد غير موجود بعد) | ثغرة توثيق |
| 5 | `build_artifacts.py` (docstring) و§7.3 من وثيقة التصميم: `artifacts/` «git-ignored» | `.gitignore` لا يستثني `artifacts/` وملفاتها متتبَّعة في git (README الـml صحيح: «في git») | docstring قديم |
| 6 | `src/ml/__init__.py` (docstring): «B1–B9» وحزمة 0.1.0 وخريطة وحدات ناقصة | الكود فيه B10 وGRU-lite وlearners وserving | docstring قديم |
| 7 | أمر الاختبار `discover -s src/backend/tests -k test_contract -k test_static` | يفشل (خطأ استيراد نسبي في وحدتين) بلا `-t .` | يُستعمل أمر README: `-t .` أو أسماء الوحدات الكاملة |
| 8 | README الخلفية: مثال المدرّس يعرض `"probability": 0.999` و`"oof_2013"` | الاستجابة الحالية `"score": 0.999` و`"lopo_2013"` (D-65) | المثال قبل D-65؛ وعرض المكوّن C7 تغيّر من `cluster_pop` إلى `similar_pop` (D-70) |
| 8-ب | README الخلفية: دوال `learner_table` و`cluster_summary` «لم تُضَف بعد إلى `serving.py`» ونُفِّذت في الخلفية | `serving.py` فيها الآن `learner_table` و`cluster_summary` و`registrations` و`warm` أيضاً، وما زالت الخلفية تنفّذ نسختها (`services/instructor.py`) | ازدواج يلزم حسمه قبل التجميد، علماً أن `test_risk_matches_engine_m1` و`test_cluster_matches_engine` تتحققان من تطابق النتائج |
| 9 | `gru_meta.json` و`ablation_meta.json` مطلوبان مصدراً للمعاملات | يحويان الزمن وعدد العمليات فقط | المعاملات من الكود (§9) ومن `gru.csv`/`ablation_tuning.csv` |
| 10 | D-69 يفترض الوسم `freeze-03` | `git tag -l` فارغ؛ `/api/meta.freeze_tag` = null | لم يُوسم المستودع بعد |
| 11 | README الجذر يعدّد `svg2png.py` أداةَ التصيير | المنفِّذ الفعلي `svg2png.js` والـ`.py` غلاف | لا أثر |

# 8. قابلية إعادة الإنتاج والحتمية

## 8.1 البذور

- **بذور التقرير:** `harness.SEEDS = (0,1,2,3,4)` للنماذج العشوائية (B1 وWRMF وGRU-lite وC7)؛ وبذرة **0** وحدها للضبط (D-34).
- **العشوائيات الداخلية:** B1 يشتق مولّده من `[seed, crc32("pres|cut|phase")]`؛ `sample_space` من `crc32(اسم النموذج) + 20261024`؛ تهيئة WRMF `N(0, 0.01²)` من البذرة؛ خلط دفعات GRU ببذرة كل حقبة؛ bootstrap بـ`seed=0` و`n_boot=10000`؛ مونت-كارلو بـ`seed=0`.
- **كسر التعادل:** مفاتيح splitmix64 مشتقة من (عرض، قطع، متعلم، مورد) وتطابق كل النماذج.
- **الخيوط:** `OPENBLAS_NUM_THREADS=1` (و`OMP`/`MKL` في run_baselines) ثابتة في كل تجربة، فتتوازى العمليات (`fork` عبر `multiprocessing`) بدل الخيوط ويثبت ترتيب الجمع العددي.

## 8.2 المسارات والبصمات

| ما يُثبَّت | الآلية |
|---|---|
| بيانات المصدر | MD5 للملفات السبعة في `oulad_md5_reference.txt` مقابل `verify_oulad.py`؛ وعدد صفوف `studentVle` = 10,655,280 |
| ذاكرة الأحداث | `raw_fingerprint()` (حجم الملفين الخام) يدخل اسم ملف الذاكرة المؤقتة (`85fda9abc3` وقت التشغيل) ويُبطلها عند التغيير |
| تشغيل `run_baselines` | `run_meta.json`: الأمر، `git_commit`، `data_fingerprint`، إصدارات python/numpy/pandas، الزمن |
| التركيبة المجمَّدة | `hybrid_frozen.json` يحمل `git_commit_at_freeze_run` وتاريخ التوليد |
| الخدمة | `/api/meta`: `git_commit` و`git_dirty` و`data_fingerprint` (MD5 لـ`oulad_md5_reference.txt`، أي `md5:e952490724b1e808d218ea580a234c89`) و`data_files` (MD5 لكل ملف) و`frozen_at_commit` |
| قراءات 2014 | `results/access_log.jsonl`: الزمن، MD5، الأعمدة، عدد المعرّفات، commit، `dirty` |
| ملف الأحكام | SHA-256 يُكتب في `results/conf2014/LOCK` قبل بدء الطور 2 (مخطط، D-63) |

بصمات ملفات النتائج المجمَّدة وقت الكتابة (تتغير عند أي إعادة توليد، ويُسجَّل الجديد في شرط التجميد ش6):

```
SHA-256 hybrid_frozen.json  9abdf4d834311846b3e6366c466e98fb8ce2bef01edf7f3b392c16d1628c4848
SHA-256 mde80.json          607468aeab296da35fae7e047b502d52c1ee919b26cb00cf8415cb6a9b81e88a
SHA-256 learner_meta.json   84476b5dda4496dbd005eae8c4b627026c1ccff19443e8c9406f8857ec9dc78a
MD5     hybrid_frozen.json  d053cb3389de86947be97ccf6a689d4f
```

## 8.3 حدود الحتمية المعلنة

القيم العددية (المقاييس والأوزان والاختيارات) حتمية لنفس الإصدارات (numpy 2.5.3 وpandas 3.0.5 وPython 3.13)؛ تختلف **الأزمنة** و`maxrss_mb` والتواريخ بين التشغيلات، وقد يغيّر تغيّر إصدار numpy آخر خانات float. لذلك اشترط التجميد `repro_diff.md` (ش5) يقارن كل رقم بالملفات الحالية حرفياً.

## 8.4 الوسم `freeze-03` وشروطه والتشغيل التأكيدي

حالة الوسم وقت الكتابة: **غير موجود** (`git tag -l` فارغ). شروطه ش1–ش10 (محضر الاجتماع 03، D-62) وحالتها من الشيفرة:

| الشرط | الحالة في المستودع |
|---|---|
| ش1 هجين بأرضية D-51 و`hybrid_frozen.json` | موجود (`floor_rule`، `weight_grid_points`) |
| ش2 MDE80 لـH1 بعد D-51 | موجود (`mde80.json`: H1 = 0.0375) |
| ش3 الهجين على B، M1 افتراضياً، وسم «منحلّ»، H2-ب | موجود (`risk_model="M1"`، `degenerate`، `H2b`) |
| ش4 نماذج الخطر النهائية | الكود موجود (`risk_final.py`) والمخرج `results/frozen/risk_final.json` لم يُولَّد |
| ش5 أمر `reproduce_dev` و`repro_diff.md` | غير موجود |
| ش6 `results/frozen/freeze03_config.json` | غير موجود |
| ش7 `run_confirmatory.py` وتشغيل جاف على 2013 | غير موجود (`--dry-run-dev` مخطط) |
| ش8 توقيع الزميل (D-47، الحراس، `repro_diff.md`) | توقيع D-47 في `peer-signoff-D47.md` مشروط بإغلاق N1؛ والكود الحالي يرشّح الجداول عند التحميل ويكتب `attempt` قبل القراءة (N1 وN3)، وإقرار الزميل المحدَّث لم يُسجَّل بعد؛ والباقي معلَّق |
| ش9 تحديث الوثيقة 02 والـREADME | قيد التنفيذ |
| ش10 توقيع المشرف والوسم على commit نظيف | معلَّق |

**كيف يُشغَّل التشغيل التأكيدي (E10) عند اكتمال الشروط**، وفق D-63 (لم يُكتب مشغّله بعد، فهذا وصف للمواصفة لا للكود):

```
python3 -m src.ml.experiments.run_confirmatory --tag freeze-03
```

يرفض المشغّل العمل ما لم يكن HEAD هو الوسم والشجرة نظيفة والمجلد `results/conf2014/` غير موجود؛ ويكتب `.lock` عند البدء، ولا يمرّر `allow_confirmatory=True` إلا بعد هذه الفحوص، ويسجّل القراءة الكاملة لـ2014 في `access_log.jsonl`. **الطور 1** (الفرضيات الأربع H1 وH2-أ وH3 وH4-أ مع خطوط الأساس): يضبط على تحقق كل عرض داخل الفضاءات المجمَّدة ويقيّم (t، t+14] ببذرة 0 للضبط والبذور 0–4 للتقرير، ويكتب `verdicts.csv` ويحسب SHA-256 في `LOCK` **قبل** بدء **الطور 2** (الثانوي: الاستئصال، حساسيات E، الإنصاف). التشغيل الثاني يحتاج قراراً مكتوباً من المشرف، وانحراف البروتوكول يُسجَّل في `deviations.md`. وعروض 2014 لا تُخدَم من الواجهة إلا بوجود `verdicts.csv` ومطابقة قفل SHA-256 (FR-40، D-67).

ما يحرسه الكود اليوم: لا يمرّر أي سكربت في `src/` المعامل `allow_confirmatory=True` (تحقق بالبحث في المستودع)، والخلفية لا تقرأ 2014 أبداً، وجميع المحمِّلات ترشّح عند القراءة. وشرط D-69: `serving.py` و`build_artifacts.py` و`src/backend/` و`src/frontend/` خارج نطاق التجميد بشرط ألا تعدّل وحدة مجمَّدة، ويُفحص بـ`git diff freeze-03`.

# 9. ملحق

## 9.1 المعاملات المجمَّدة (hyperparameters)

**التركيبة المجمَّدة** (`results/dev2013/hybrid_frozen.json`):

| الحقل | القيمة |
|---|---|
| `status` | مجمَّدة على عروض التطوير 2013 (D-11، D-30، D-51)؛ التشغيل التأكيدي يعيد ضبط معاملات المكوّنات والأوزان على تحقق كل عرض داخل هذا الفضاء فقط |
| `components` | `C7_ClusterPop` (7)، `B5_SKNN` (4) |
| `floor_component` / `accept_only_components` | `B5_SKNN` / `C7_ClusterPop` |
| `floor_rule` | وزن مكوّن الأرضية ≥ 0.25 (أصغر نقطة موجبة في شبكة D-29)؛ تُحذف نقاط الوزن الصفري ولا تُضاف قيمة (D-51) |
| `weight_grid` / `weight_grid_points` | سمبلكس بخطوة 1/4؛ النقاط الأربع (C7، SKNN): (0، 1)، (0.25، 0.75)، (0.5، 0.5)، (0.75، 0.25) |
| `candidates` | B3 وB7 وB4 وB5 وB9 وC6 وC7 |
| `S_star` / `S_star_nonneural` / `B_np_star` | `B5_SKNN` / `B5_SKNN` / `B3_RecentPop` |
| `initial_weights_modal` | C7 = 0.75، SKNN = 0.25 |
| `weights_by_fold` | 27 زوجاً (عرض، قطع): 21 بـ(0.75، 0.25)، و5 بـ(0.5، 0.5)، وواحد بـ(0.25، 0.75) |
| `component_configs_by_fold` | C7: `w=3` في 18 زوجاً و`w=7` في 6 و`w=14` في 3؛ SKNN: `L=1;M=1000;k=500;variant=sknn` (12)، `L=1;M=1000;k=200;variant=sknn` (8)، `L=7;M=1000;k=500;variant=vsknn` (6)، `L=7;M=1000;k=200;variant=vsknn` (1) |
| `H2b` | غير منطبقة بالبناء: لا مكوّن في HYB* يقرأ W (D-59) |
| `task` / `seeds_report` | A (D-42)؛ والمهمة B بأوزان A (D-57) / [0..4] |
| `git_commit_at_freeze_run` | `86ea36f011159c16ac1ff37ec97ee0ea67a2c630` |

**معاملات منصة التجارب** (من الكود ومن CSV؛ تنبيه: `gru_meta.json` و`ablation_meta.json` يحويان الزمن لا المعاملات):

| المجال | المعامل | القيمة |
|---|---|---|
| البروتوكول | قطوع t / الأفق / الميزانية | {70، 126، 182} / 14 يوماً / ≤ 20 إعداداً لكل نموذج |
| البروتوكول | KS / مقياس الضبط / استبعاد الهدف | (5، 10، 20) / NDCG@10 / E5 |
| الإشارة | τ / β / α | {7، 14، 28، 56، ∞} / {0.5، 1، 2} / {1، 2، 5، 10، 20، 40} |
| WRMF | f / reg / نقاط التفتيش / التهيئة | {16، 32، 64} / {0.01، 0.1، 1، 10} / {10، 15، 25} (افتراضي iters = 15) / N(0, 0.01²) |
| GRU-lite | البنية | d_e = d_h = 64، طبقة واحدة |
| GRU-lite | lr / الهدف | {1e-3، 3e-3، 1e-2} / {next، next-new}؛ ستة إعدادات |
| GRU-lite | L2 / القص / الدفعة / BPTT | 1e-5 / 5 / 128 / T = 20 |
| GRU-lite | الحقب / الصبر | ≤ 30 / 3 |
| GRU-lite | المختار (27 زوجاً، المهمة A) | lr = 0.001 في 13 زوجاً و0.01 في 8 و0.003 في 6؛ والهدف `next-new` في 24 زوجاً و`next` في 3؛ والحقب المختارة بين 1 و19 (الأكثر تكراراً 2 ثم 1) |
| الهجين | حد المكوّنات / شبكة الأوزان | 4 / 1/4 (2–3 مكوّنات) و1/3 (4)، و0.1 حساسية |
| الهجين | فاصل القبول / B | bootstrap-t 95%، B = 10,000 |
| التجميع | ks / البذور / n_init / ARI الأدنى | 2..8 / 0–4 / 10 / 0.8 |
| الإحصاء | δ / α / m (Holm) / δ_AUC | 0.02 / 0.05 / 4 / 0.02 |
| الإحصاء | MDE80 (H1، H2-أ، H3، H4-أ) | 0.0375، 0.045، 0.050، 0.0225 |
| الخطر | λ لكل عرض (اليوم 56) | M0: 0.001 للتسعة؛ M1: 0.01 للتسعة؛ M2: 0.001 أو 0.01 |
| الخطر | عتبات Youden | M0 = 0.4744، M1 = 0.4557، M2 = 0.4074 |
| الخطر | قطوع الخطر / العنقدة | {28، 56، 112} / اليوم 56 |
| الخدمة | قطوع النموذج / ذاكرات | {70، 126، 182} / LRU: 1024 توصية و6 لقطات مدرّس |
| الأزمنة | run_gru / run_ablation (CPU) | 913 ث فعلية، ≈ 3530 ث CPU / 1153 ث فعلية، ≈ 11,511 ث CPU |

## 9.2 قاموس الحقول في الاستجابات

حقول التوصية (`/api/recommendations`)، مأخوذة من `schemas.RecommendationResponse` وما يرجعه الخادم:

| الحقل | النوع | المعنى |
|---|---|---|
| `registration` | str | `<presentation>-<id_student>`، مثل `FFF_2013J-371869` |
| `requested_day` / `snapshot_day` | int | اليوم المطلوب واليوم الذي حُسبت عنده التوصية؛ متساويان دائماً (D-49) |
| `task` | A\|B | A: موارد جديدة؛ B: أي وصول بما فيه الإعادات |
| `status` | enum | `ok` أو `no_history` (لا نشاط سابق: ترتيب غير شخصي) أو `withdrawn` (انسحب ≤ اليوم: قائمة فارغة) |
| `known_learner` | bool | هل للتسجيل نشاط في الكتالوج حتى اليوم |
| `note` | str\|null | تنبيه نصي (مثلاً قبل أول قطع أو بلا تاريخ) |
| `context.week` | int | رقم الأسبوع = اليوم÷7 + 1 |
| `context.next_assessment` | obj\|null | `type` و`day` و`days_ahead` |
| `context.active_days_to_date` | int | عدد أيام نشاط المتعلم حتى اليوم |
| `components[]` | list | `id` و`label` و`weight` لمكوّنات الهجين عند هذا القطع |
| `items[].rank` / `id_site` / `activity_type` | int/int/str | الترتيب ومعرّف المورد ونوعه |
| `items[].score` | float | الدرجة المدمجة Σ w_m r̃_m (ليست مقياس تقييم) |
| `items[].contributions` | dict | مساهمة كل مكوّن w_m·r̃_m |
| `items[].reason` / `reason_secondary` | str / str\|null | جملة التفسير الرئيسية والثانوية |
| `provenance.run_id` / `role` / `model_cut` | str/str/int\|null | معرّف التشغيل (`replay-dev2013-<commit>`)، الدور (`dev`)، وقطع النموذج (null قبل 70) |

حقول التفسير (`/api/explanations`): `score` و`components[]` بـ`id` و`label` و`weight` و`r_tilde` (الرتبة المطبَّعة ∈ [0,1]) و`contribution` و`sentence` و`evidence` من ثلاثة أنواع: `count` (`n` و`window` و`scope` = all\|similar)، و`item` (`id_site` و`activity_type` و`days` و`last_day`)، و`assessment` (`assessment_type` و`days_ahead`). وحقول المدرّس: الخطر `risk.score` (درجة نسبية غير معايَرة، D-65) و`cut_day` و`threshold` (Youden) و`above_threshold` و`provenance` (`lopo_2013`: نموذج مدرَّب على العروض الثمانية الأخرى) و`top_factor` و`factors[{name, wz}]` (مساهمة الميزة المعيارية في اللوغاريتم)؛ والعنقود `cluster{id,label}` (وفي `/api/instructor/clusters` الحقلان `cluster_day` = 56 و`unstable_reason` يشرحان سبب وسم «غير مستقر»)؛ و`profile[{name,value,median,z}]`؛ و`withdrawn_day`؛ و`outcome` (null دائماً). ودرجة الخطر للمدرّس فقط، ولا يظهر أي خطر أو عنقود في مسارات المتعلم (يفحصه `test_contract_no_risk` و`test_contract_json`).

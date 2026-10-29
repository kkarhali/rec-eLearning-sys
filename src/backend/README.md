# `src/backend/` — خدمة API (starlette + uvicorn + pydantic)

غلاف رفيع حول `src/ml/serving.py` (الوثيقة 03 §5 و§8): يحلّل المدخلات، ويحوّل مخرجات `Engine` إلى عقود pydantic المطابقة لملفات
`src/frontend/mock/*.json`، ويوحّد الأخطاء، ويخدم `src/frontend/dist/`. **لا حساب توصية خارج `serving.Engine`**، ولا تخزين لحالة متعلم
(D-49)، ولا مصادقة ولا جمع حي (D-22)، ولا أرقام تقييم.

## التشغيل
المتطلبات الأولى (من جذر المستودع): `bash data/download.sh` (≈ 45 ث، ينتهي بـ«integrity: PASS»)، و`tsc` من TypeScript لبناء الواجهة، و`playwright` (Node، عمومي) للفحص الحي؛ وتفاصيل الإصدارات في README الجذر.
```bash
python3 -m src.ml.experiments.build_artifacts   # أولاً (D-70: artifacts/ خارج git، تُعاد في ≈ دقيقة): نماذج الخطر والعناقيد والقطوع
bash src/frontend/build.sh                      # مرة واحدة: يبني src/frontend/dist
python3 -m src.backend                          # http://127.0.0.1:8000  (الواجهة + /api)
python3 -m src.backend --warm                   # تسخين في خيط خلفي لأيام العرض الرئيسية 75/56/70/112/126/182 (21.95 ث كاملاً بذاكرة عنقدة دائمة كاملة، منها الخطّاف 12.78 ث، `results/serving_bench/warm.json`؛ وعلى نسخة نظيفة بلا الذاكرة الدائمة `data/cache/serving_clusters` أطول، ≈ 61 ث في قياس 2026-10-25)
python3 -m src.backend --warm --warm-weekly     # + شبكة أسبوعية من اليوم 56 (≈ 10 ث لكل يوم؛ عدة دقائق)
python3 -m src.backend.precompute --jobs 4      # NFR-01: اختيار العناقيد لكل أيام FFF_2013J مسبقاً (1167 ث ≈ 19 د مرة واحدة، results/serving_bench/precompute.txt؛ --all للعروض التسعة)
python3 -m src.backend --warm --precompute-clusters   # أو في الخلفية بعد التسخين (--precompute-jobs 2)؛ التقدم في /api/health ← warm.precompute
python3 -m src.backend --no-instructor          # /api/instructor/* ⇒ 404 instructor_disabled، وصفحة المدرّس 404، وتُخفى روابطها
python3 -m src.backend --host 127.0.0.1 --port 8000 --warm-presentation BBB_2013J --warm-days 75,126
```
المتطلبات: `data/raw/oulad/` و`data/cache/` (انظر `src/ml/README.md`)، و`artifacts/` (**يجب تشغيل `python3 -m src.ml.experiments.build_artifacts` قبل أول تشغيل**) و`results/dev2013/hybrid_frozen.json`. غيابها ⇒ 503 `artifacts_missing`، و500 `internal_error` (دون تفاصيل داخلية).
يطلق `--warm` الخطّاف `serving.warm(presentation, days)` إن وُجد في `serving.py` (D-68، تحفيظ العنقدة الدائم)، وإلا يسخّن بنداءات التوصية ولقطة المدرّس نفسها. الربط الافتراضي `127.0.0.1`؛ أي مضيف آخر يطلق تحذيراً (D-66: عرض توضيحي بلا أمان وصول).
`GET /api/health` يعيد `warm.state` (`pending|running|done|failed`).

## المسارات (كلها GET؛ الأخطاء `{"error":{"code","message","details"}}` بالعربية)
| المسار | المعاملات | ملاحظات |
|---|---|---|
| `/api/health` | — | `{status, run_id, uptime_s, instructor_enabled, warm}` |
| `/api/meta` | — | الإصدار، `runtime` (إصدارات Python وnumpy وpandas وstarlette وuvicorn وpydantic وanyio المحمَّلة فعلاً، مطابقة لـ`requirements.txt`)، `git_commit` (+`git_dirty`)، `data_fingerprint` (MD5 لـ`data/oulad_md5_reference.txt`) و`data_files` (MD5 لكل ملف)، `components` (الأوزان الأولية المجمَّدة)، `cutoffs` = قطوع النموذج [70،126،182]، `risk_cutoffs` = [28،56،112]، `snapshot_grid` (نقاط التنقل السريع)، `presentations`، و`bind_host` و`access_notice` («عرض توضيحي بلا أمان وصول»، D-66)، و`risk_score` (الحقل `score`، «درجة خطر نسبية غير معايَرة»، الهدف: رسوب/انسحاب مقابل نجاح/امتياز، D-65؛ `min_day` = 28 قطع مبني، و`display_from_day` = 56 أول يوم تعرضه اللوحة) |
| `/api/presentations` | — | 9 عروض 2013 `published` (الافتراضي FFF_2013J أولاً) + عرض 2014 واحد `locked` للتمثيل (عدد تسجيلاته وطوله 0: لا يُقرأ شيء من 2014، D-09؛ وتبقى مغلقة في الواجهة بقرار D-96 بلا فتح لاحق) |
| `/api/registrations` | `presentation`، `q` (جزء من id_student)، `limit≤100`، `offset`، `day` (اختياري) | قائمة بيضاء (D-70): `registration, id_student, date_registration, status` فقط، لا `final_result` ولا `date_unregistration`. `status` بلا `day` دائماً `ok`؛ ومع `day`: `withdrawn` إن انسحب ≤ day، و`no_history` إن لا نشاط ≤ day. الترتيب: الأكثر أياماً نشطة حتى اليوم 75 أولاً |
| `/api/recommendations` | `registration`، `day`، `k` 1..20، `task=A|B` | `provenance.model_cut` دائماً (null قبل اليوم 70)، `note`، `known_learner`، `status`، `components`، `items[{rank,id_site,activity_type,relevance,contributions,reason,reason_secondary}]` |
| `/api/explanations/{reg}/{id_site}` | `day`، `task` | مكوّنات `{weight, r_tilde, contribution, evidence, sentence}` مرتبة بالمساهمة؛ الدليل `count|item|assessment`؛ 404 `item_not_in_list` خارج أفضل 20 |
| `/api/learner/{reg}/history` | `day`، `window` (28) | `daily`، `recent` (3)، `active_days` |
| `/api/instructor/overview` | `presentation`، `day` | مؤشرات، ملخص الملامح، مدرج الخطر، التغطية |
| `/api/instructor/clusters` | `presentation`، `day` | k، `cluster_day` (لقطة العناقيد = 56)، `unstable` و`unstable_reason`، الجودة (ARI = ثبات البذور لـk المختار؛ والاستقرار يشترط أيضاً أن يقع k ضمن أفضل اثنين في silhouette وDBI، فقد يكون ARI = 1 والعناقيد «غير مستقرة»)، أحجام ووصف عربي حتمي، إسقاط PCA |
| `/api/instructor/learners` | `presentation`، `day`، `cluster`، `risk=all|above`، `idle=0|1` (أو `false|true`، الافتراضي 0)، `sort=[-]risk|reg|cluster|active_days|last_access|on_time`، `limit≤500`، `offset` | `{items,total,limit,offset}`. `idle=1` يُبقي من الفوج «بلا نشاط 14 يوماً»: `last_access_day` فارغ (لا وصول ≤ t) أو `t − last_access_day ≥ 14`؛ ويُطبَّق في الخادم على الفوج كله **قبل** الفرز والترقيم، ويُجمع مع `cluster` و`risk`، فـ`total` عدد المطابقين كلهم (ب-8). إزاحة بعد آخر صف تعيد `items: []` و`total` نفسه |
| `/api/instructor/learner/{reg}` | `day` | عنقود، خطر بعوامل w·z، ملامح مقابل الوسيط، أفضل 3، `withdrawn_day`، بلا أي حقل نتيجة نهائية، و`provenance {run_id, role, model_cut}` (D-49 (6)) |

الأخطاء: 404 `presentation_not_found|registration_not_found|item_not_in_list|instructor_disabled|not_found`، 405 `method_not_allowed`،
409 `confirmatory_locked` (أي عرض 2014، على كل المسارات)، 422 `validation_error` (مع `details.errors[{field,reason}]`) و`day_out_of_range`
(`details.max_day`) و`day_before_first_snapshot` (المدرّس قبل اليوم 56، `details.first_day = 56`؛ الواجهة تنقل الشريط تلقائياً)، 503 `artifacts_missing`، و500 `internal_error` (دون تفاصيل داخلية).

```text
$ curl 'localhost:8000/api/recommendations?registration=FFF_2013J-371869&day=75&k=3'
{"registration":"FFF_2013J-371869","presentation":"FFF_2013J","id_student":371869,"requested_day":75,"snapshot_day":75,"task":"A",
 "status":"ok","known_learner":true,"note":null,"context":{"week":11,"next_assessment":{"type":"TMA","day":96,"days_ahead":21},"active_days_to_date":93},
 "components":[{"id":"similar_pop","label":"شعبية الأنماط المشابهة (7)","weight":0.75},{"id":"sknn","label":"SKNN (4)","weight":0.25}],
 "items":[{"rank":1,"id_site":716344,"activity_type":"oucontent","relevance":1.0,"contributions":{"similar_pop":0.75,"sknn":0.25},
           "reason":"شائع لدى متعلمين بنمط مشابه لنمطك","reason_secondary":null}, …],
 "provenance":{"run_id":"replay-dev2013-…","role":"dev","model_cut":70}}
$ curl 'localhost:8000/api/instructor/learners?presentation=FFF_2013J&day=75&sort=-risk&limit=1'
{"items":[{"registration":"FFF_2013J-590714","cluster":{"id":0,"label":"أيام نشطة قليلة · نشاط متقطع"},"active_days":1,"last_access_day":-7,"on_time":"0/2",
  "risk":{"score":0.999,"cut_day":56,"threshold":0.456,"above_threshold":true,"provenance":"lopo_2013","top_factor":"حصة page"}}],"total":1872,"limit":1,"offset":0}
```

## قرارات التحويل (ما يخالف الوثيقة أو يكمّلها)
- **الأولوية لملفات mock** عند التعارض: معرّفات المكوّنات قصيرة (`recent_pop, wrmf, item_knn, sknn, markov, gru, cbf, assess_prox, cluster_pop`) ومربوطة بمعرّفات serving في `services/labels.py`؛ `next_assessment.day` لا `date`؛ `Presentation`/`Page`/الأخطاء كما في `types.ts`. حقول الوثيقة الإضافية (`note`, `known_learner`, `id_student`) موجودة.
- **الحساب عند اليوم المطلوب نفسه** (D-49): `snapshot_day == requested_day`؛ الأيام الجديدة ≈10 ث للطلب الأول (اللقطات على شبكة 14 يوماً للتنقل السريع فقط). `cutoffs` في العروض = قطوع النموذج 70/126/182.
- **ما لم يُضَف بعد إلى `serving.py` (§8.4)** نُفِّذ هنا بالمعادلات نفسها: جدول المتعلمين المتجهي، `cluster_summary` (وصف حتمي من أكبر ملمحين |z|، PCA، silhouette/DBI من التعيين المخزَّن، ARI من `learner_clusters.csv`)، عوامل `w·z`، `median_active_days`. الخطر من **M1** (D-27) لا M2 الافتراضي في `serving`؛ الحقل `score` (D-65: درجة نسبية غير معايَرة لا احتمال) و`provenance = "lopo_2013"` (مدرَّب على العروض الثمانية الأخرى). يتحقق `test_risk_matches_engine_m1` و`test_cluster_matches_engine` من التطابق مع `Engine._risk/_cluster`. لا تقدير لمن سجّل بعد قطع الخطر، ولا يدخل في إحصاءات z (في الخدمتين معاً بعد ج-16، فلا يغيّر متعلم يسجّل بعد اليوم t أي درجة عند t).
- **الفوج** في لوحة المدرّس = المسجَّلون ≤ t ولم ينسحبوا ≤ t (لا مستقبل). ملخص الملامح على النشطين (≥ يوم نشط)، النسب بالمئة (الأمثلة تستعمل كسوراً مع وحدة «%»). صفوف «أول وصول» و«متوسط الدرجات» تُحذف من ملف المتعلم حين لا نشاط/درجة (قيمتا غياب بالعرف).
- **عدد المكوّنات** هو ما في التركيبة المجمَّدة فعلاً: `C7_ClusterPop` و`B5_SKNN` فقط (الأوزان تتغير مع القطع؛ SKNN بوزن 0 عند 126 و182).
- **D-70:** مفتاح دليل C7 `similar_learners_in_window` (يقبل الاسم القديم من `serving` إلى أن يُعاد تسميته هناك)، ومعرّف المكوّن `similar_pop` والوسم «شعبية الأنماط المشابهة»، و`scope: "similar"`؛ فلا كلمة cluster في أي استجابة متعلم، ويفحصه `test_contract_json.py` على JSON المسلسَل. العنقود يُستعمل داخل التوصية ولا يُعرض للمتعلم.
- **درجة التوصية** اسمها `relevance` (عناصر التوصية والتفسير) لا `score`؛ فالمفتاح `score` محجوز لدرجة الخطر في مسارات المدرّس وحدها، ويحظره اختبار العقد في كل JSON المتعلم (D-70).
- **الفصل بالعقد** (لا ضبط وصول): نماذج المتعلم بلا حقول خطر/عنقود/سمات حساسة/`final_result`؛ لا يُستدعى `learner_profile` في مساراته. `outcome` في ملف المدرّس `null` دائماً.
- `--no-instructor`: رابط المدرّس يُخفى بحقن `<style>a[href*="instructor"]{display:none}</style>` في صفحات HTML (دون تعديل الواجهة).

## البنية
```
__main__.py  app.py (create_app، Services، تسخين، TimingMiddleware، FrontendFiles)  settings.py  errors.py
schemas.py   (pydantic: استجابات + استعلامات)   repository.py (فهارس أحداث، كتالوج العروض، git، بصمة البيانات)
services/    replay.py (توصيات، سجل، عروض، LRU)  explanation.py  instructor.py  labels.py
routes/      meta.py  learner.py  instructor.py  common.py     bench.py     e2e/live-screenshots.js
tests/       asgi_client.py (عميل ASGI بلا httpx)  test_contract_no_risk.py  test_contract_json.py (D-70)  test_static_errors.py  test_api_live.py  test_bench.py (ت-5)
```
التنفيذ: كل معالج `async` يشغّل العمل في خيط (`run_in_threadpool`) فلا يحجب `/api/health` أثناء الحساب البارد؛ قفل واحد حول `Engine`.

## الأداء (آلة 4 أنوية؛ `python3 -m src.backend.bench`، 20 طلباً لكل مسار، FFF_2013J، اليوم 75)
**القياس المرجعي للرسالة (ت-5، شرط ب-2) محفوظ في `results/serving_bench/`** (ملف لكل حال: `cold.json` و`warm.json` و`precomputed.json`، و`precompute.txt`، وأوامرها وآلتها في `README.md` هناك)، ومنه يولّد `scripts/thesis/make_tables.py` الجدول 5-6 وأرقام 5-6-3 وNFR-01. والأرقام أدناه منقولة من تلك الملفات (قياس 2026-10-29، commit `6c56acf`، آلة 4 أنوية).
```bash
python3 -m src.backend.bench http://127.0.0.1:8100 --state warm --out results/serving_bench/warm.json   # JSON: الصفوف وعيّناتها + git_commit والتاريخ والمنصة والأنوية والعرض واليوم وn وحال الخادم
python3 -m src.backend.bench URL --state precomputed --out F.json --cold-day 63 --cold-overview-day 66   # أول طلب توصية/نظرة عامة في يوم بارد (يتكرر الخياران)
```
لا يكتب `--out` فوق ملف موجود (قياس واحد لكل حال)، و`--state` لازم معه. وبلا هذه الخيارات يبقى السلوك كما كان (طباعة الجدول أو `--json`).

| الحالة (الملف) | الطلب الأول | بعده (20 طلباً) |
|---|---|---|
| **بلا تسخين** (`cold.json`) — أول `recommendations`، اليوم 75 | **15,267 ms** | وسيط 9.2 ms، أقصى 42.5 ms |
| بلا تسخين — أول `instructor/overview` | 1,980 ms | وسيط 1.6 ms |
| بلا تسخين — أول طلب توصية في 11 يوماً باردة (63…203) | 15.2–19.4 ث | — |
| بلا تسخين — أول `instructor/overview` قبل أي طلب في 5 أيام باردة (66…178) | 17.0–20.3 ث | — |
| **بتسخين `--warm`** (`warm.json`، بعد اكتمال التسخين) — أول `recommendations` | **16.1 ms** | وسيط 9.9 ms، أقصى 11.6 ms |
| بتسخين — أول `instructor/overview` | 2.6 ms | وسيط 2.0 ms، أقصى 4.2 ms |
| **بعد الحساب المسبق** (`precomputed.json`) — أول طلب توصية في الأيام الباردة نفسها | 1.6–3.8 ث | — |
| بعد الحساب المسبق — أول `instructor/overview` في الأيام الباردة نفسها | 3.1–5.1 ث | — |

بعد التسخين (`warm.json`، وسيط/أقصى بـms): health 1.2/1.6، meta 1.9/3.4، presentations 2.2/4.0، registrations(100) 3.3/7.1، recommendations 9.9/11.6، explanations 27.6/31.5،
history 12.6/15.3، overview 2.0/4.2، clusters 3.6/4.4، learners(100) 11.8/14.2، learner 2.3/3.0 — كلها ≪ 200 ms (NFR-01؛ يفرض `test_latency_after_warmup` 200 ms لمسارات المتعلم وملف المتعلم و1 ث للوحة المدرّس).
**الطلب البارد (NFR-01):** `python3 -m src.backend.precompute --presentation FFF_2013J --jobs 4` يحسب اختيار العناقيد لكل أيام العرض ويحفظه في `data/cache/serving_clusters` (1167 ث لـ269 يوماً بأربع عمليات، `precompute.txt`)؛ أو `--precompute-clusters` مع الخادم. ويفرض `test_cold_day_bounded_after_cluster_precompute` 5 ث و8 ث.
زمن التسخين الكامل (`warm.json`، `server_health_at_start.warm`): 21.95 ث = خطّاف serving.warm 12.78 ث ثم الأيام الستة (75: 1.88، 56: 1.25، 70: 1.36، 112: 1.36، 126: 1.40، 182: 1.74 ث)، والذاكرة الدائمة للعناقيد كاملة (269 يوماً). وعلى نسخة نظيفة بلا تلك الذاكرة يطول بقدر اختيار العناقيد لكل يوم مسخَّن.
ذاكرات: LRU للتوصيات (1024 قائمة من 20)، ولقطات المدرّس (6)، و`lru_cache` داخل `Engine`.

## الاختبارات
```bash
python3 -m unittest discover -s src/backend/tests -t .      # 73 اختباراً، ≈ 38–45 ث بعنقدة مخزَّنة (أكثر على نسخة نظيفة: يُحسب اختيار العناقيد لأيام الاختبار)
python3 -m unittest src.backend.tests.test_contract_no_risk src.backend.tests.test_static_errors   # < 1 ث، بلا بيانات
python3 -m src.backend --warm &   # ثم التحقق الحي بمتصفح حقيقي (لا mock) ولقطات deliverables/05-user-guide/screenshots/live-*.png:
NODE_PATH=$(npm root -g) node src/backend/e2e/live-screenshots.js
```
`test_api_live` يقارن مفاتيح كل استجابة بملف mock المقابل، ويفحص المنطق (قطع النموذج حسب اليوم، المهمتان، الترتيب والترقيم والتصفية، 409/404/422، التطابق مع `Engine`، غياب الخطر والسمات الحساسة من مسارات المتعلم)، وتُتخطّى إن غابت البيانات.

- **D-49 (6):** `provenance {run_id, role, model_cut}` في كل استجابة بيانات: التوصية والتفسير وسجل النشاط والنظرة العامة والعناقيد وصفحة المتعلمين وملف المتعلم (`schemas.PROVENANCE_MODELS`، ويفحصها اختبار العقد على النماذج وعلى JSON الحي).

## تنظيف النصوص والواجهة (مراجعة دليل المستخدم)
- كل نص يصل المستخدم يمر بـ`services/labels.fix_ar`: تصحيح «بعد 57 أيام» إلى «بعد 57 يوماً» وحذف أرقام القرارات الداخلية (`(D-49 (5))` من ملاحظة `serving` وغيرها)؛ وفي الواجهة `countAr/daysAr/learnersAr/itemsAr` في `labels.ts` (1 يوم واحد، يومان، 3–10 أيام، 11+ يوماً). أرقام القرارات تبقى في تعليقات الكود وREADME فقط، ويفحصه `test_text.py` و`test_contract_json.py` والتحقق الحي.
- بطاقة «متعلمون نشطون» = الفوج الذي له يوم نشط واحد على الأقل حتى t؛ و`kpis.cohort_size` هو الفوج كله (مسجَّلون ≤ t ولم ينسحبوا ≤ t)، وهو مجموع أحجام العناقيد وعدد صفوف الجدول (1,860 من 1,872 عند اليوم 75).
- «الحساب عند اليوم t نفسه» تظهر في سياق التوصية بشرط `snapshot_day === requested_day`؛ وإلا يظهر «محسوب عند اليوم {snapshot_day}».
- `CHECK_ONLY=1 node src/backend/e2e/live-screenshots.js` يتحقق (أشرطة الملامح داخل مساراتها، خلايا الدرجة بخانتين وغير مقصوصة، لا أرقام قرارات ولا صيغ عدد خاطئة، وترتيب التركيز بـTab مع حلقة مرئية في صفحتي المتعلم والمدرّس، ورابطا التخطي إلى جدول المتعلمين والتوصيات مع عدد ضغطات Tab بعدهما، وأسماء العناصر التفاعلية في شجرة الوصول، وتباين كل نص مرسوم، والانتقال إلى الصفحة الثانية من جدول المدرّس بـEnter، وتطابق عدد «بلا نشاط 14 يوماً» مع `idle=1`، وغياب التمرير الأفقي على 1440 و375 و360؛ عرض 360 للفحص وحده بلا لقطات) دون كتابة لقطات؛ ويختار متعلماً بدرجة خطر 0.40–0.60 للقطات.

## تحديثات D-71/D-72 وربط `serving.warm`
- `ClusterQuality.ari` يقبل `null` (العرض الغائب من `results/dev2013/learner_clusters.csv`)؛ الواجهة تعرض «غير متاح» و`unstable_reason` لا يستشهد بـARI غائب (`test_text.py`). تشخيص التجميع (silhouette وDBI وARI مع مصدره) يُعرض بلا تسميات؛ وبطاقة التغطية «اتساع التوصيات عند اليوم t: X من Y مورداً» (حقل `coverage.at_10` في API لم يتغير).
- `--warm` يستدعي الآن `serving.warm(presentation, days)` ثم يسخّن توصيات ولقطات الأيام الستة. زمن التسخين قياس واحد مؤرَّخ في قسم «الأداء» أعلاه (≈ 22 ث كاملاً بذاكرة عناقيد كاملة، `results/serving_bench/warm.json`).
- اللقطات الحية (D-72): متعلم الدرج والصف = الأقرب إلى وسيط درجات الفوج من بين من هم دون العتبة ضمن الصفحة المعروضة (مرتبة بالتسجيل، بلا مرشّح)؛ يختاره `e2e/live-screenshots.js` برمجياً ويطبع معرّفه ودرجته وفرقه عن الوسيط. ويتحقق من أن أعمدة الجدول كلها ظاهرة والدرج مفتوح على سطح المكتب.
- **دقة العتبة والدرجة:** `risk.threshold` و`risk.score` تُعادان بست منازل (العتبة المجمَّدة 0.455716…، لا 0.456)، ويُترك التقريب للعرض في الواجهة؛ فحكم `above_threshold` واحد في الخادم والعارض (يفحصه `test_learners_contract_sort_page_filter`).

## قاعدة اختيار متعلم اللقطات (D-73)
مجتمع الاختيار = الصفحة التي يعرضها الجدول فعلاً (مفروزة بالتسجيل، بلا مرشّح، أول 100 صف). الشروط: درجته دون العتبة، و5 أيام نشطة فأكثر، وهو الأقرب إلى **وسيط درجات الفوج كله**، والتعادل يُكسر بترتيب التسجيل. يُقبل إن كان الفرق عن الوسيط ≤ 0.05؛ وإلا يُنتقى أقرب متعلم مؤهَّل في الفوج كله ويُفتح الجدول عند صفحته (`&off=` في عنوان الصفحة، والفرز بالتسجيل باقٍ). يفشل `e2e/live-screenshots.js` إن خالف الاختيار القاعدة.

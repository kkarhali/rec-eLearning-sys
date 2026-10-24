# `src/backend/` — خدمة API (starlette + uvicorn + pydantic)

غلاف رفيع حول `src/ml/serving.py` (الوثيقة 03 §5 و§8): يحلّل المدخلات، ويحوّل مخرجات `Engine` إلى عقود pydantic المطابقة لملفات
`src/frontend/mock/*.json`، ويوحّد الأخطاء، ويخدم `src/frontend/dist/`. **لا حساب توصية خارج `serving.Engine`**، ولا تخزين لحالة متعلم
(D-49)، ولا مصادقة ولا جمع حي (D-22)، ولا أرقام تقييم.

## التشغيل
```bash
python3 -m src.ml.experiments.build_artifacts   # أولاً (D-70: artifacts/ خارج git، تُعاد في ≈ دقيقة): نماذج الخطر والعناقيد والقطوع
bash src/frontend/build.sh                      # مرة واحدة: يبني src/frontend/dist
python3 -m src.backend                          # http://127.0.0.1:8000  (الواجهة + /api)
python3 -m src.backend --warm                   # تسخين في خيط خلفي لأيام العرض الرئيسية 75/56/70/112/126/182 (≈ 36 ث كاملاً بعد ربط serving.warm؛ 75 جاهز بعد ≈ 25 ث)
python3 -m src.backend --warm --warm-weekly     # + شبكة أسبوعية من اليوم 56 (≈ 10 ث لكل يوم؛ عدة دقائق)
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
| `/api/meta` | — | الإصدار، `git_commit` (+`git_dirty`)، `data_fingerprint` (MD5 لـ`data/oulad_md5_reference.txt`) و`data_files` (MD5 لكل ملف)، `components` (الأوزان الأولية المجمَّدة)، `cutoffs` = قطوع النموذج [70،126،182]، `risk_cutoffs` = [28،56،112]، `snapshot_grid` (نقاط التنقل السريع)، `presentations`، و`bind_host` و`access_notice` («عرض توضيحي بلا أمان وصول»، D-66)، و`risk_score` (الحقل `score`، «درجة خطر نسبية غير معايَرة»، الهدف: رسوب/انسحاب مقابل نجاح/امتياز، D-65) |
| `/api/presentations` | — | 9 عروض 2013 `published` (الافتراضي FFF_2013J أولاً) + عرض 2014 واحد `locked` للتمثيل (عدد تسجيلاته وطوله 0: لا يُقرأ شيء من 2014، D-09) |
| `/api/registrations` | `presentation`، `q` (جزء من id_student)، `limit≤100`، `offset`، `day` (اختياري) | قائمة بيضاء (D-70): `registration, id_student, date_registration, status` فقط، لا `final_result` ولا `date_unregistration`. `status` بلا `day` دائماً `ok`؛ ومع `day`: `withdrawn` إن انسحب ≤ day، و`no_history` إن لا نشاط ≤ day. الترتيب: الأكثر أياماً نشطة حتى اليوم 75 أولاً |
| `/api/recommendations` | `registration`، `day`، `k` 1..20، `task=A|B` | `provenance.model_cut` دائماً (null قبل اليوم 70)، `note`، `known_learner`، `status`، `components`، `items[{rank,id_site,activity_type,relevance,contributions,reason,reason_secondary}]` |
| `/api/explanations/{reg}/{id_site}` | `day`، `task` | مكوّنات `{weight, r_tilde, contribution, evidence, sentence}` مرتبة بالمساهمة؛ الدليل `count|item|assessment`؛ 404 `item_not_in_list` خارج أفضل 20 |
| `/api/learner/{reg}/history` | `day`، `window` (28) | `daily`، `recent` (3)، `active_days` |
| `/api/instructor/overview` | `presentation`، `day` | مؤشرات، ملخص الملامح، مدرج الخطر، التغطية |
| `/api/instructor/clusters` | `presentation`، `day` | k، `cluster_day` (لقطة العناقيد = 56)، `unstable` و`unstable_reason`، الجودة (ARI = ثبات البذور لـk المختار؛ والاستقرار يشترط أيضاً أن يقع k ضمن أفضل اثنين في silhouette وDBI، فقد يكون ARI = 1 والعناقيد «غير مستقرة»)، أحجام ووصف عربي حتمي، إسقاط PCA |
| `/api/instructor/learners` | `presentation`، `day`، `cluster`، `risk=all|above`، `sort=[-]risk|reg|cluster|active_days|last_access|on_time`، `limit≤500`، `offset` | `{items,total,limit,offset}` |
| `/api/instructor/learner/{reg}` | `day` | عنقود، خطر بعوامل w·z، ملامح مقابل الوسيط، أفضل 3، `withdrawn_day`، بلا أي حقل نتيجة نهائية |

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
- **ما لم يُضَف بعد إلى `serving.py` (§8.4)** نُفِّذ هنا بالمعادلات نفسها: جدول المتعلمين المتجهي، `cluster_summary` (وصف حتمي من أكبر ملمحين |z|، PCA، silhouette/DBI من التعيين المخزَّن، ARI من `learner_clusters.csv`)، عوامل `w·z`، `median_active_days`. الخطر من **M1** (D-27) لا M2 الافتراضي في `serving`؛ الحقل `score` (D-65: درجة نسبية غير معايَرة لا احتمال) و`provenance = "lopo_2013"` (مدرَّب على العروض الثمانية الأخرى). يتحقق `test_risk_matches_engine_m1` و`test_cluster_matches_engine` من التطابق مع `Engine._risk/_cluster`. فرق وحيد: لا تقدير لمن سجّل بعد قطع الخطر.
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
tests/       asgi_client.py (عميل ASGI بلا httpx)  test_contract_no_risk.py  test_contract_json.py (D-70)  test_static_errors.py  test_api_live.py
```
التنفيذ: كل معالج `async` يشغّل العمل في خيط (`run_in_threadpool`) فلا يحجب `/api/health` أثناء الحساب البارد؛ قفل واحد حول `Engine`.

## الأداء (آلة 4 أنوية؛ `python3 -m src.backend.bench`، 20 طلباً لكل مسار، FFF_2013J، اليوم 75)
| الحالة | الطلب الأول | بعده |
|---|---|---|
| **بلا تسخين** — أول `recommendations` | **10 307 ms** | وسيط 4.8 ms |
| بلا تسخين — أول `instructor/overview` (يبني لقطة اليوم: ملامح + خطر + عناقيد + تغطية لكل المتعلمين) | 11 081 ms | وسيط 1.1 ms |
| بلا تسخين — أول `registrations` (فهرس أحداث العرض) | 371 ms | وسيط 2.8 ms |
| **بتسخين `--warm`** (ينتهي ≈ 11.8 ث بعد الإقلاع) — أول `recommendations` | **10.5 ms** | وسيط 6.1 ms |
| بتسخين — أول `instructor/overview` | 1.4 ms | وسيط 1.4 ms |
| بتسخين الأيام الستة (D-68) — أول `recommendations` عند 56/126/182 | 7.5–8.4 ms | وسيط ≈ 5 ms |
| بتسخين — أول `instructor/learners` (100 صف) عند 56/126/182 | 8–11 ms | وسيط 6–8.6 ms |

بعد التسخين (وسيط/أقصى بـms): health 0.9/1.2، meta 1.7/2.4، presentations 1.5/2.0، registrations(100) 3.2/5.5، recommendations 6.1/9.3، explanations 17.3/19.0،
history 5.6/6.1، overview 1.4/1.9، clusters 2.2/3.3، learners(100) 6.0/6.9، learner 2.0/2.2 — كلها ≪ 300 ms (NFR-01؛ يفرضه `test_latency_after_warmup`).
زمن التسخين الكامل: ≈ 36 ث = خطّاف serving.warm ≈ 20.6 ث ثم الأيام الستة (75: 2.4، 56: 1.2، 70: 5.6، 112: 0.9، 126: 3.8، 182: 1.0 ث)؛ قياس 2026-10-24 على جهاز العمل (قبل ربط الخطّاف كان 81 ث). يوم جديد (مثلاً 90 أو 91) لا يغطيه التسخين: ≈ 9.8–10.7 ث للطلب الأول ثم ≈ 0.8–0.9 ث لبناء لقطة المدرّس ثم من الذاكرة؛ عرض آخر (BBB_2013J) ≈ 8.3 ث للأول.
ذاكرات: LRU للتوصيات (1024 قائمة من 20)، ولقطات المدرّس (6)، و`lru_cache` داخل `Engine`.

## الاختبارات
```bash
python3 -m unittest discover -s src/backend/tests -t .      # 48 اختباراً، ≈ 25–90 ث (حسب ذاكرة العنقدة الدائمة) (أغلبها تسخين أول يوم)
python3 -m unittest src.backend.tests.test_contract_no_risk src.backend.tests.test_static_errors   # < 1 ث، بلا بيانات
python3 -m src.backend --warm &   # ثم التحقق الحي بمتصفح حقيقي (لا mock) ولقطات deliverables/05-user-guide/screenshots/live-*.png:
NODE_PATH=$(npm root -g) node src/backend/e2e/live-screenshots.js
```
`test_api_live` يقارن مفاتيح كل استجابة بملف mock المقابل، ويفحص المنطق (قطع النموذج حسب اليوم، المهمتان، الترتيب والترقيم والتصفية، 409/404/422، التطابق مع `Engine`، غياب الخطر والسمات الحساسة من مسارات المتعلم)، وتُتخطّى إن غابت البيانات.

## تنظيف النصوص والواجهة (مراجعة دليل المستخدم)
- كل نص يصل المستخدم يمر بـ`services/labels.fix_ar`: تصحيح «بعد 57 أيام» إلى «بعد 57 يوماً» وحذف أرقام القرارات الداخلية (`(D-49 (5))` من ملاحظة `serving` وغيرها)؛ وفي الواجهة `countAr/daysAr/learnersAr/itemsAr` في `labels.ts` (1 يوم واحد، يومان، 3–10 أيام، 11+ يوماً). أرقام القرارات تبقى في تعليقات الكود وREADME فقط، ويفحصه `test_text.py` و`test_contract_json.py` والتحقق الحي.
- بطاقة «متعلمون نشطون» = الفوج الذي له يوم نشط واحد على الأقل حتى t؛ و`kpis.cohort_size` هو الفوج كله (مسجَّلون ≤ t ولم ينسحبوا ≤ t)، وهو مجموع أحجام العناقيد وعدد صفوف الجدول (1,860 من 1,872 عند اليوم 75).
- «الحساب عند اليوم t نفسه» تظهر في سياق التوصية بشرط `snapshot_day === requested_day`؛ وإلا يظهر «محسوب عند اليوم {snapshot_day}».
- `CHECK_ONLY=1 node src/backend/e2e/live-screenshots.js` يتحقق (أشرطة الملامح داخل مساراتها، خلايا الدرجة بخانتين وغير مقصوصة، لا أرقام قرارات ولا صيغ عدد خاطئة) دون كتابة لقطات؛ ويختار متعلماً بدرجة خطر 0.40–0.60 للقطات.

## تحديثات D-71/D-72 وربط `serving.warm`
- `ClusterQuality.ari` يقبل `null` (العرض الغائب من `results/dev2013/learner_clusters.csv`)؛ الواجهة تعرض «غير متاح» و`unstable_reason` لا يستشهد بـARI غائب (`test_text.py`). تشخيص التجميع (silhouette وDBI وARI مع مصدره) يُعرض بلا تسميات؛ وبطاقة التغطية «اتساع التوصيات عند اليوم t: X من Y مورداً» (حقل `coverage.at_10` في API لم يتغير).
- `--warm` يستدعي الآن `serving.warm(presentation, days)` ثم يسخّن توصيات ولقطات الأيام الستة. بعد وصول `serving.warm` (تحفيظ العنقدة الدائم، D-68): الخطّاف 16.0 ث ثم الأيام 75/56/70/112/126/182 بـ1.5/0.7/4.5/0.8/3.5/1.0 ث؛ المجموع **28.1 ث** (كان 81 ث).
- اللقطات الحية (D-72): متعلم الدرج والصف = الأقرب إلى وسيط درجات الفوج من بين من هم دون العتبة ضمن الصفحة المعروضة (مرتبة بالتسجيل، بلا مرشّح)؛ يختاره `e2e/live-screenshots.js` برمجياً ويطبع معرّفه ودرجته وفرقه عن الوسيط. ويتحقق من أن أعمدة الجدول كلها ظاهرة والدرج مفتوح على سطح المكتب.

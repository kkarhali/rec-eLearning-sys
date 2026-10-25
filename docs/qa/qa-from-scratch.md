# فحص QA من الصفر لمسار الكود

**التاريخ:** 2026-10-25 · **المنفِّذ:** مهندس Backend · **المنهج:** `git clone` للمستودع المحلي عند HEAD (`57479cd`، فرع `kk_auto_/amazing-planck-wzsemh`) إلى مجلد مؤقت خارج مستودع العمل، ثم اتباع README الجذر وREADME الخلفية وREADME الواجهة حرفياً كقارئ جديد، دون تعديل `src/ml/`. حُذفت النسخة بعد الفحص. الجهاز: 4 أنوية، Python 3.13، Node 22.

## الخلاصة
المسار يعمل من الصفر بلا تعديل أي كود: البيانات PASS 7/7، واختبارات ML 121/121 والخلفية 52/52 (ومنها `test_labels_js`)، والخادم والتسخين والفحص الحي LIVE OK، و`--no-instructor` يعطّل اللوحة. الفجوات المكتشفة **في التوثيق فقط** (أدناه) وأُصلحت نصياً. لا خلل يمنع التشغيل.

## الخطوات
| # | الخطوة (كما في التوثيق) | الزمن | النتيجة |
|---|---|---|---|
| 1 | `git clone` المحلي إلى scratchpad | 7 ث | نجح (HEAD `57479cd`)؛ `artifacts/` غير متتبَّعة كما يُتوقع |
| 2 | `bash data/download.sh` (تحميل من مرايا GitHub، الشبكة متاحة، لا نسخ من مستودع العمل) | 46 ث | نجح؛ «integrity: PASS» |
| 3 | `python3 data/verify_oulad.py` | 31 ث | **PASS 7/7**: سبعة أسطر OK، وإعادة بناء `studentVle.csv` = 10,655,280 صفاً |
| 4 | `python3 -m src.ml.experiments.build_artifacts` | 73 ث (منها 12.1 ث لقراءة studentVle وبناء `data/cache`) | نجح بلا مخرجات سابقة؛ ولّد `artifacts/<9 عروض>/` |
| 5 | `bash src/frontend/build.sh` ثم `tsc --noEmit -p tsconfig.json` | 4 ث + 3 ث | نجحا (TypeScript 6.0.2)؛ `dist/` كامل |
| 6 | `python3 -m unittest discover -s src/ml/tests` | 5 ث | **121/121 OK** |
| 7 | `python3 -m unittest discover -s src/backend/tests -t .` | 109 ث | **52/52 OK** (على نسخة بلا ذاكرة عنقدة دائمة) |
| 8 | `python3 -m unittest src.backend.tests.test_labels_js` | 0.1 ث | 2/2 OK |
| 9 | `python3 -m src.backend --warm --port 8100` | جاهز في ≈ 2 ث؛ التسخين الكامل 61 ث (الخطّاف `serving.warm` 47.2 ث ثم الأيام 75/56/70/112/126/182 بـ1.3/0.7/6.1/0.9/4.1/0.9 ث) | نجح؛ `warm.state = done`؛ اليوم 75 جاهز بعد ≈ 49 ث |
| 10 | `CHECK_ONLY=1 NODE_PATH=$(npm root -g) node src/backend/e2e/live-screenshots.js http://127.0.0.1:8100` | 13 ث | **LIVE OK**: قاعدة D-73 مستوفاة (`FFF_2013J-29769`، الدرجة 0.362، الفرق 0.003، offset 0)، لا أخطاء JS ولا طلبات mock، الصف المظلل = متعلم الدرج |
| 11 | `python3 -m src.backend --no-instructor --port 8101` | — | `/instructor.html` 404، `/api/instructor/overview` 404 `instructor_disabled`، `index.html` فيه قاعدة CSS تخفي الروابط، `/learner.html` 200 |
| 12 | `NODE_PATH=$(npm root -g) node screenshots.js` (لقطات mock في README الواجهة) | 11 ث | نجح؛ كتب إلى `src/frontend/screenshots/mock/` كما يقول README |

## الفجوات في التوثيق وما أُصلح (نصياً في مستودع العمل)
> **حالة التطبيق:** إصلاحات README الجذر مطبَّقة في المستودع. أما إصلاحات `src/backend/README.md` و`src/frontend/README.md` (البنود 3 و4 و6 و7 و5-جزئياً) فمحفوظة في `readme-wip/` خارج المستودع لأن `src/` ضمن حارس الشجرة النظيفة للتشغيل المجمَّد الجاري، وتُنقل بعد انتهائه.

| # | الفجوة | الأثر | الإصلاح |
|---|---|---|---|
| 1 | README الجذر خريطة مجلدات فقط: لا خطوات تشغيل، ولا متطلبات، ولا ترتيب (بيانات ← artifacts ← واجهة ← اختبارات ← خادم) | قارئ جديد يحتاج التنقيب في ثلاثة README | أُضيف قسم «تشغيل النظام من الصفر» في README الجذر بالأوامر والأزمنة المقيسة هنا |
| 2 | لا ملف متطلبات Python ولا إصدارات؛ README الجذر لا يذكر `starlette/uvicorn/pydantic` ولا Node/`tsc`/`playwright` العموميين | معرفة غير مكتوبة | سُجّلت النسخ المختبرة في README الجذر، وأُشير إليها من README الخلفية والواجهة. **مقترح (غير منفَّذ):** ملف `requirements.txt` بالنسخ نفسها |
| 3 | README الخلفية يذكر تحميل البيانات بإحالة إلى `src/ml/README` فقط، ولا يذكر `download.sh` | خطأ «البيانات غير موجودة» لمن يبدأ من الخلفية | أُضيفت فقرة متطلبات أولى في أول «التشغيل» |
| 4 | زمن التسخين الموثَّق (≈ 36 ث) يفترض ذاكرة العنقدة الدائمة `data/cache/serving_clusters` ممتلئة؛ على نسخة نظيفة 61 ث (اليوم 75 بعد ≈ 49 ث)، واختبارات الخلفية 109 ث لا «25–90» | توقع زمن خاطئ | وُثّق الزمنان (نظيفة/معبّأة) في README الخلفية والجذر |
| 5 | `build_artifacts` يُلحق سطراً بـ`results/access_log.jsonl` المتتبَّع في git | يظهر الملف معدَّلاً بعد التشغيل فيُظن أن شيئاً أُفسد | نُبّه إليه في README الجذر (سلوك D-47 المقصود) |
| 6 | README الواجهة يشغّل `python3 -m http.server 8000` وهو منفذ الخلفية الافتراضي | تعارض إن شُغّلا معاً | بُدّل إلى 8765 مع تعليل، وأُضيف سطر متطلبات `tsc`/`playwright` |
| 7 | `live-screenshots.js` لا يوثّق وسيط عنوان الخادم (`argv[2]`) في قسم التشغيل؛ و`CHECK_ONLY` مذكور فقط في قسم لاحق | استعمال المنفذ غير 8000 يتطلب قراءة الشيفرة | وُثّق الاستعمال بالوسيط وبـ`CHECK_ONLY` في README الجذر |

## ملاحظات لا تمنع التشغيل (كود، لم يُعدَّل)
- رسالة النجاح في `CHECK_ONLY` تطبع «LIVE OK -> …/screenshots» رغم أنها لا تكتب لقطات؛ التباس نصي فقط في `src/backend/e2e/live-screenshots.js`.
- ملف `data/oulad_md5_reference.txt` يذكر المسارات `data/raw/<file>` بينما الملفات في `data/raw/oulad/`؛ `verify_oulad.py` والخلفية يستعملان الأسماء فقط فلا أثر.
- لقطات mock (`src/frontend/screenshots/mock/*.png`) متتبَّعة في git وتتغير بايتياً عند كل إعادة توليد (غير حتمية)؛ فلا تُشغَّل `screenshots.js` على مستودع العمل إلا عند الحاجة.

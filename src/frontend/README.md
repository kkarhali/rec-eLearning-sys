# واجهة «موصي التعلّم» (src/frontend)

واجهة عربية RTL بلا أي اعتماد خارجي: TypeScript (`tsc` وحده) وHTML وCSS خالص وSVG. تُخدَم ملفات ثابتة من `dist/`.

## التشغيل والبناء
المتطلبات: `tsc` (TypeScript) و`playwright` للّقطات، مثبَّتان عمومياً (`npm root -g`)؛ بلا `package.json` ولا `npm install` في هذا المجلد.
```bash
cd src/frontend
./build.sh                      # tsc -> dist/js ، نسخ html/css/mock -> dist/
tsc --noEmit -p tsconfig.json   # فحص الأنواع (strict) بلا إخراج
python3 -m http.server 8765 -d dist   # ثم افتح http://127.0.0.1:8765/ (منفذ غير 8000 كي لا يتعارض مع الخلفية)  (وضع المحاكاة تلقائياً)
NODE_PATH=$(npm root -g) node screenshots.js   # لقطات وضع mock إلى src/frontend/screenshots/mock/ (لقطات الدليل الحية: src/backend/e2e/live-screenshots.js)
```
مع الـbackend: يخدم Starlette StaticFiles المجلد `src/frontend/dist` من `/`، وتُستهلك المسارات `/api/*`.
`dist/` مُدرَج في `.gitignore` (يُعاد بناؤه بـ`build.sh`).

## وضع المحاكاة (mock)
- كشف تلقائي: يفشل `GET /api/health` (أو لا يعيد JSON فيه `status`) ← تُقرأ ملفات `mock/*.json` عبر المسار النسبي `mock/…`.
- فرض: `?mock=1` (يُحفظ في sessionStorage) و`?mock=0` للإلغاء. تظهر وسم «وضع المحاكاة» في الشريط العلوي.
- `api.ts` يطبّق في المحاكاة منطق الخادم الأساسي: أخطاء 404/409/422 (`day_before_first_snapshot` مع `first_day`، `confirmatory_locked`)، الحساب عند اليوم t نفسه (`snapshot_day` = t كما في الخادم)، و`model_cut` من قطوع النموذج 70 و126 و182 (`null` قبل 70) وقطع الخطر 28 و56 و112 لدرجة المدرّس، الأسبوع والتقييم القادم، الفرز والتصفية (ومنها `idle`) والترقيم لجدول المتعلمين. بيانات المحاكاة 40 صفاً، فلا يظهر عنصر الترقيم فيها (يظهر حين `total` > 100).
- المعرّفات العشوائية: بيانات المحاكاة لعرض BBB_2013J؛ العرض FFF_2013J يُعاد استعمالها باستبدال بادئة المعرّف. عرض BBB_2014J مقفل في الواجهة (409): عروض 2014 من مجموعة التأكيد ونتائجها في الرسالة.
- الأرقام في المحاكاة وهمية (اصطناعية) للعرض فقط، لا لتقييم أي شيء (D-49).
- المحاذاة مع النموذج المجمَّد: `python3 scripts/align_mock.py` يكتب مكوّني `hybrid_frozen.json` بأوزانهما الأولية وجمل قالبيهما، وقطوع النموذج، و`snapshot_day` = t، دون تغيير أي مفتاح؛ و`--check` يفشل إن خالفت الملفات ناتجه (ويفحصه `test_mock_matches_frozen_composition`). لا تُحرَّر ملفات mock يدوياً.

## بنية الملفات
```
index.html learner.html instructor.html about.html
src/  api.ts (عميل typed + mock)  state.ts (حالة URL)  types.ts  dom.ts  labels.ts  controls.ts
      home.ts learner.ts instructor.ts about.ts
      components/ DayScrubber RecCard WhyPanel KpiCard charts(SvgBarChart, SvgHBars, SvgDonut, ClusterScatter, DivergingBars)
                  DataTable Pager Drawer feedback(Toast, Empty, Skeleton, errorBox) Header
styles/ tokens.css base.css components.css      mock/*.json      build.sh  tsconfig.json  screenshots.js
```
حالة URL: `p` العرض، `r` التسجيل، `d` اليوم، `task` (A|B)، `cl` العنقود المصفّى، `f` (all|above|idle)، `sort` (مثل `-risk`)، `off` إزاحة صفحة جدول المتعلمين (مضاعفات 100؛ يُصفَّر عند تغيير التصفية أو الفرز أو العرض). تنتقل `p` و`d` بين الصفحات عبر روابط التنقل.

## المسارات المستهلكة
`/api/health` `/api/meta` `/api/presentations` `/api/registrations` `/api/recommendations` `/api/explanations/{registration}/{id_site}` `/api/learner/{registration}/history` `/api/instructor/overview` `/api/instructor/clusters` `/api/instructor/learners` `/api/instructor/learner/{registration}`.

## قائمة تدقيق إمكانية الوصول المطبّقة (WCAG 2.2 AA)
- `lang="ar" dir="rtl"`، خصائص CSS المنطقية، `<bdi>` للمعرّفات اللاتينية، أرقام 0–9.
- تباين النص ≥ 4.5:1 عبر رموز `tokens.css` (نص التنبيه الصغير على الخلفية الكهرمانية `#92400E`)، وحدود عناصر التحكم ≥ 3:1. يفحصها آلياً `src/backend/tests/test_contrast.py` (NFR-22: كل زوج مستعمل، ويفشل إن ظهر لون غير مصنَّف)، ويفحص الاختبار الطرفي تباين كل نص مرسوم.
- لا اعتماد على اللون وحده: للمكوّنات اسم نصي، وللعناقيد شكل مختلف، وما فوق عتبة الخطر إطار داكن وخط متقطع ونص «فوق العتبة» لقارئ الشاشة.
- لوحة المفاتيح: شريط اليوم (`input[type=range]` أصلي: الأسهم/Home/End/PageUp/PageDown) وحقل رقمي وأزرار اللقطات؛ الجدول بـ↑↓ وEnter؛ ترقيم الجدول بزرين أصليين («الصفحة السابقة» في البداية و«الصفحة التالية» في النهاية، معطَّلان عند الطرفين) ويبقى التركيز على الزر بعد الانتقال؛ لوحة «لماذا؟» والدرج يُغلقان بـEsc ويعود التركيز إلى الزر/الصف. يفحص `src/backend/e2e/live-screenshots.js` ترتيب التركيز بـTab وحلقة التركيز المرئية في صفحتي المتعلم والمدرّس، والانتقال إلى الصفحة الثانية بـEnter.
- حلقة تركيز مرئية سميكة، وأهداف لمس ≥ 44px، ورابط «تخطَّ إلى المحتوى»، ورابط ثانٍ «تخطَّ إلى جدول المتعلمين» في لوحة المدرّس و«تخطَّ إلى التوصيات» في صفحة المتعلم (يعدّ الاختبار الطرفي ضغطات Tab بعدهما). ويفحص الاختبار الطرفي شجرة الوصول في Chromium: لكل عنصر تفاعلي اسم وصولي.
- `aria-live="polite"` لشريط السياق والتفسير والتنبيهات، و`aria-busy` أثناء التحميل، و`aria-sort` و`aria-pressed` و`aria-expanded`.
- كل رسم SVG بـ`role="img"` و`<title>`/`<desc>` وجدول بيانات بديل قابل للطي.
- `prefers-reduced-motion` يلغي الانتقالات والهيكل المتحرك. بلا تمرير أفقي للصفحة من 360px (الجداول تتمرر داخل حاويتها)؛ يفحصه الفحص الحي على 1440 و375 و360.
- حالات التحميل (هيكل) والفراغ والخطأ (مع إعادة المحاولة وToast).
- واجهة المتعلم بلا أي حقل خطر أو عنقود (NFR-09)، ولا تُعرض السمات الحساسة (D-21).

## ملاحظات للمعماري
1. **حقول لم تحدّدها الوثيقة (القسم 8.3)** وافترضتُها: `Presentation{id,role,status,length_days,snapshots,cutoffs,assessments[],registrations,label_ar}`؛ `Meta.snapshot_grid`؛ `Page{items,total,limit,offset}`؛ `RegistrationSummary{registration,id_student,date_registration,date_unregistration,status}`؛ `ExplanationDetail{…,components[{id,label,weight,r_tilde,contribution,evidence,sentence}],notes}` مع `evidence.type ∈ count|item|assessment`؛ `LearnerHistory{daily[{day,clicks}],recent[],active_days}`؛ `InstructorOverview{kpis,profile_summary,risk{histogram},coverage}`؛ `ClusterSet{k,quality,unstable,clusters,points}`؛ `InstructorLearnerDetail{cluster,risk{…,factors[{name,wz}]},profile,top_recs,withdrawn_day}`. الأمثلة الحرفية في `mock/` هي المرجع.
2. **`model_cut`** (D-49 «تاريخ النموذج = c») غير موجود في مثال `RecommendationResponse`؛ قرأته من `provenance.model_cut` (اختياري). إن غاب لا تُعرض الشارة.
3. معاملات `sort` في `/api/instructor/learners` غير مسمّاة في الوثيقة؛ تستعمل الواجهة `[-]risk|reg|cluster|active_days|last_access|on_time`. تصفية «بلا نشاط 14 يوماً» في الخادم بالمعامل `idle=1` (لا وصول ≤ t، أو t − آخر وصول ≥ 14) على الفوج كله قبل الترقيم، ويُعرض الجدول صفحات من 100 صف مع عنصر ترقيم «عرض a–b من N» (FR-32، ب-8؛ كانت قبله تُطبَّق في الواجهة على أول 100 صف وحدها).
4. ألوان العناقيد: لوحة مكيَّفة من Okabe–Ito بدرجات أغمق لتحقيق تباين الأشكال ≥ 3:1 (مع شكل مميّز لكل عنقود).
5. صفحة «عن النظام» مضافة (FR-35) بنص ثابت.
6. الدرج في RTL يفتح من يمين الشاشة (بداية السطر)، خلافاً للإطار السلكي حيث يظهر على اليسار.

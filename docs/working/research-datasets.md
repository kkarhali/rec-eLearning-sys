# كشّاف مجموعات البيانات: مسح وتحقق فعلي وترشيح (نظام توصية للتعليم الإلكتروني القائم على سلوك المستخدم)

- **التاريخ:** 2026-10-24
- **الكاتب:** وكيل «كشّاف مجموعات البيانات» (فريق الرسالة)
- **الحالة:** مسودة بحثية للنقاش. **لا قرار نهائي هنا**؛ القرار في اجتماع المشرف (د. باسل الخطيب).
- **مجلد العمل (scratchpad):** `/tmp/claude-0/-home-user-rec-eLearning-sys/d9fa8d7f-28c1-526d-a725-5245fbf905b7/scratchpad/data-probe/` (يُرمز له أدناه بـ `$PROBE`، حجمه الكلي ≈ 1.5 GB، لا تحميل > 2 GB فلم يُحذف شيء بسبب الحجم).

## 0. ما الذي تحقق فعلياً (خلاصة سريعة)

| المجموعة | هل تحمّلت فعلاً هنا؟ | الحالة |
|---|---|---|
| **OULAD الكاملة** (7 جداول، `studentVle` = 10,655,280 صفاً) | **نعم**، من مرآة GitHub، وتحققت بـ pandas وبـ md5 | جاهزة للاستخدام |
| **MARS** (Mandarine Academy، EN + FR) | **نعم**، من مستودعين مستقلين (نسخة EN متطابقة بايتياً) | جاهزة، مع **تحفّظ ترخيص** |
| EdNet KT3 (مستخرَج 500 مستخدماً فقط) | نعم (عينة، دون جداول المحتوى) | صالحة للتجريب فقط |
| Canvas Network Person-Course | نعم (325,199 صفاً) | بيانات مجمّعة لا سجلات |
| MOOCCube (نسخة معالجة 10-core من طرف ثالث) + MOOPer | نعم (64,763 + 135,834 تفاعلاً) | تسجيلات فقط، بلا بيانات وصفية |
| ASSISTments 2009 (skill builder) | نعم (525,534 صفاً) | موجّهة لتتبع المعرفة لا لتوصية المواد |
| ITM-Rec، قوائم دورات Coursera | نعم (صغيرة) | هامشية |
| KDD Cup 2015 | **جزئياً**: ميزات مشتقة + `object.csv` فقط، **لا `log_train.csv` الخام** | لا تصلح لسلاسل السلوك |
| MOOCCube/MOOCCubeX الخام، EdNet الكامل، Junyi، HarvardX، Moodle logs | **لا** (المضيف محجوب 403) | مستبعدة بمعيار القابلية |

---

## 1. المنهجية وقواعد الثقة

- كل رقم يخص ملفاً حمّلته مصدره **تنفيذ pandas فعلي** (أُشير إليه بـ «تحقق محلي»). الأرقام التي مصدرها ورقة/صفحة تذكر مصدرها صراحةً وتُعلَّم «ثانوي».
- الثقة: **عالية** (مصدران مستقلان أو تحقق محلي + مصدر أولي) / **متوسطة** (مصدر واحد) / **منخفضة** (ثانوي فقط أو استنتاج).
- WebFetch لم يعمل مطلقاً هنا (`getaddrinfo ENOTFOUND github.com` / `www.ncbi.nlm.nih.gov`)، فكل ما عن صفحات الويب جاء من WebSearch (ملخصات النتائج) وليس من قراءة الصفحات نفسها. لذلك صفحات Dataverse وUCI وNature لم تُقرأ بل ما ورد في مقتطفات البحث.
- الدرجات في المصفوفة (القسم 5) ذاتية 0–5 وتستند إلى الأدلة المذكورة؛ المجموعات التي لم أستطع تحميلها قُيّمت **من وثائقها فقط** (تحيّز محتمل لصالحها، وأُشير لذلك).

---

## 2. بطاقات المجموعات

### 2.1 OULAD: Open University Learning Analytics Dataset

- **المصدر الرسمي:** موقع OU Analyse (analyse.kmi.open.ac.uk / research.stem.open.ac.uk/ouanalyse) وUCI (DOI 10.24432/C5KK69 بحسب مقتطف بحث). **كلها محجوبة هنا** (انظر القسم 3).
- **الورقة المرجعية:** Kuzilek, Hlosta, Zdrahal (2017), *Open University Learning Analytics dataset*, **Scientific Data 4:170171**, DOI 10.1038/sdata.2017.171 (WebSearch + README مستودع edis8100).
- **الترخيص:** CC BY 4.0 (مقتطفا بحث: صفحة Sci Data/OU، وREADME في `HakeoungLee/edis8100-datasets`). الثقة: عالية.
- **الحجم (تحقق محلي على المرآة):** 7 وحدات دراسية (modules) × عروض (presentations 2013B/2013J/2014B/2014J) = **22 module-presentation**؛ `studentInfo` 32,593 تسجيلاً (28,785 طالباً فريداً)؛ `studentVle` **10,655,280** صفاً (26,074 طالباً، 6,268 موقع VLE مستخدماً من 6,364 في `vle.csv`)؛ `studentAssessment` 173,912؛ المدى الزمني `date` من −25 إلى 269 يوماً نسبةً لبداية العرض؛ مجموع `sum_click` = 39,605,099.
  - ملاحظة: صفحتا UCI/OU وفق مقتطف البحث تقولان «سبع وحدات»، والورقة تقول «22 دورة»؛ التحقق المحلي يحسم: 7 وحدات تُنتج 22 عرضاً.
- **الإشارات السلوكية:** نقرات يومية مجمَّعة `sum_click` لكل (طالب، مورد VLE، يوم). **لا طوابع زمنية داخل اليوم** (الدقة = اليوم). لا تقييمات صريحة؛ نتائج نهائية (`Pass/Fail/Withdrawn/Distinction`) وتسليمات التقييم ودرجاتها.
- **البنية:** `courses, assessments, vle, studentInfo, studentRegistration, studentAssessment, studentVle` (7 CSV). `vle.csv` يحوي `activity_type` (20 نوعاً: resource 2,660، subpage 1,055، oucontent 996، url 886، forumng 194، quiz 127...) و`week_from/week_to` (82.4% فارغة). بيانات ديموغرافية: gender, region, highest_education, imd_band, age_band, disability, num_of_prev_attempts, studied_credits.
- **الاستخدام في توصية التعليم:** استُخدمت للتنبؤ بالتسرب والنتائج بكثرة (ثانوي). في مراجع المستودع: المرجع #20 (`S-0109`، IJITIS 2026) يُجري «تحققاً على OULAD» ويعيد تنفيذ GRU4Rec وSASRec وLightGCN (كما يدّعي النص؛ لم أتحقق من أرقامه). الثقة: متوسطة.

### 2.2 MARS: Mandarine Academy Recommender System dataset (= ورقة PMC9932724)

- **ملاحظة:** «E-learning recommender system dataset» (PMC9932724) و«MARS» **مجموعة واحدة** (WebSearch).
- **المصدر الرسمي:** Harvard Dataverse، DOI 10.7910/DVN/BMY3UD (v2.0 بحسب README المستودع `Zaynabmnk/edu-recommender`)، وصفحة mandarine.academy/mars-dataset. **الاثنان محجوبان هنا.**
- **الورقة:** Hafsa, Wattebled, Jacques, Jourdan (2023), *E-learning recommender system dataset*, **Data in Brief 47:108942**, DOI 10.1016/j.dib.2023.108942 (WebSearch).
- **الترخيص:** **متعارض/غير محسوم.** README في `Zaynabmnk/edu-recommender` يقول «CC0 1.0» وهو مصدر ثانوي (طالب مشروع)؛ بينما مقتطف WebSearch عن صفحة Mandarine يذكر **نموذج طلب وتوقيع data sharing agreement (انتظار ≥ أسبوعين)**. لم أتمكن من قراءة قسم Terms في Dataverse. الثقة بالترخيص: **منخفضة** → يجب التحقق قبل الاعتماد (سؤال للمشرف).
- **الحجم (تحقق محلي):**
  - EN: 9,902 مستخدماً في `users`، 1,167 عنصراً، **implicit 21,908** (3,007 مستخدماً × 957 عنصراً، كثافة 0.76%)، **explicit 3,659** (822 × 776).
  - FR: 121,345 مستخدماً، 1,451 عنصراً، **implicit 253,827** (18,519 × 1,377، كثافة 1.0%)، **explicit 85,339** (9,789 × 1,350).
  - المجموع 275,735 implicit و88,998 explicit، وهو يطابق «276,000 و89,000» في ملخص الورقة (مقتطف بحث). EN وFR **مجموعتان منفصلتان تماماً** (تقاطع المستخدمين 0 والعناصر 0).
  - المدى الزمني implicit: 2016-10 إلى 2021-09 (طوابع بالثانية).
- **الإشارات السلوكية:** `implicit_ratings` = مشاهدات صفحة/فيديو (مستخدم، عنصر، `created_at`)؛ 32% (EN) و40% (FR) من الأزواج مكررة (إعادة مشاهدة)؛ `explicit_ratings` = `watch_percentage` + «rating» 1–10 مشتق منه (لذا هو ضمني عملياً).
- **البنية/البيانات الوصفية للعناصر:** `items_*`: `name`, `description` (ترجمات الفيديو، متوسط 1,950 حرفاً EN و3,021 FR، غير فارغة 86%/84%)، `Difficulty`, `Job`, `Software`, `Theme`, `type` (tutorial/use_case/webcast)، `duration`, `nb_views`, `created_at`. المستخدم: `job` فقط (غالبيته فارغ). لا ديموغرافيا ولا نتائج تعلم.
- **جلسات (تحقق محلي، فجوة خمول 30 دقيقة):** EN 6,780 جلسة (3.23 عنصر/جلسة)، FR 64,253 جلسة (3.95 عنصر/جلسة).
- **الاستخدام السابق:** مشروع UcoRecSys (بكالوريوس Córdoba، MIT للشيفرة)، ومشروع CM3070 (`Zaynabmnk`) يُبلغ HR@10 = 0.440 (لم يُحكَّم)، وCEUR-WS Vol-3268 paper9 (Hafsa et al.، توصية متعددة الأهداف). الاستخدام الأكاديمي المحكّم محدود. مجال البيانات: تدريب مهني على Microsoft 365 (وليس دورات جامعية).

### 2.3 EdNet (Riiid)

- **المصدر الرسمي:** `github.com/riiid/ednet` (README فقط، 224 KB، حمّلته). **روابط البيانات `bit.ly/ednet_kt1..4` محجوبة.**
- **الورقة:** Choi et al. (2020), *EdNet: A large-scale hierarchical dataset in education*, AIED 2020, LNCS 12164, pp. 69–73 (README edis8100 + arXiv 1912.03072 في بحث).
- **الترخيص:** **CC BY-NC 4.0** (README الرسمي، سطر 285). مقبول لأطروحة غير تجارية. الثقة: عالية.
- **الحجم (README الرسمي):** 131,441,538 تفاعلاً، 784,309 طالباً؛ KT1: 5.6 GB غير مضغوط (784,309 ملفاً)، KT3: 4.3 GB (297,915 ملفاً). 13,169 سؤالاً و1,021 محاضرة بـ293 وسماً (tags). الطوابع **مُزاحة بقيمة ثابتة** (أمنياً).
- **الإشارات:** KT3 يضيف قراءة الشروحات (explanation) ومشاهدة المحاضرات (`enter/quit` على `l`) إلى الإجابات؛ مصادر (`sprint`, `adaptive_offer`, `my_note`, `archive`...)؛ منصة mobile/web.
- **المتاح هنا فعلاً:** مستخرَج **500 مستخدماً من KT3** داخل `HakeoungLee/edis8100-datasets/ednet-kt3-500/actions.csv.gz` (تحقق محلي: **1,893,105 صفاً**، 7 أعمدة، 500 مستخدماً، 29,235 عنصراً [e: 685,268 صفاً، b: 629,582، q: 544,487 `respond`، l: 33,768 على 816 محاضرة]، من 2018-08-30 إلى 2019-11-27، وسيط 1,309 فعلاً لكل مستخدم). **جداول المحتوى (questions/lectures مع tags) غير موجودة** فيه.
- **الاستخدام السابق:** تتبع المعرفة (KT) أساساً؛ التوصية أقل (ثانوي). الثقة: متوسطة.

### 2.4 MOOCCube (ACL 2020) و MOOCCubeX (CIKM 2021)

- **المصدر:** MOOCCube: `github.com/thukg/MOOCCube` (README + LICENSE فقط؛ التحميل من `lfs.aminer.cn/misc/moocdata/data/MOOCCube.zip` أو Google Drive، **محجوبان**). MOOCCubeX: `github.com/THU-KEG/MOOCCubeX` (حمّلت المستودع: وثائق وسكربتات فقط 3.1 MB؛ البيانات على `lfs.aminer.cn`، **محجوب**).
- **الورقة:** Yu et al., ACL 2020 (MOOCCube)؛ Yu et al., CIKM 2021, pp. 4643–4652 (MOOCCubeX، من CITATION في README).
- **الترخيص:** مستودع MOOCCube: `LICENSE` = **CC0 1.0** (تحقق محلي من الملف). مستودع MOOCCubeX: `LICENSE` = **GPL-3.0** (تحقق محلي) وهو يخص المستودع ولم أجد نص ترخيص صريح للبيانات. الثقة: متوسطة لـMOOCCube، منخفضة لـMOOCCubeX.
- **الحجم:** MOOCCube (ثانوي من بحث): 706 دورات، 38,181 فيديو، 114,563 مفهوماً، 199,199 مستخدماً. MOOCCubeX (README، تحقق محلي من النص): 4,216 دورة، 230,263 فيديو، 358,265 تمريناً، 637,572 مفهوماً، **> 296 مليون سجل سلوكي لـ3,330,294 طالباً**؛ ملفات: `user-video.json` 3.0 GB، `user-problem.json` 21 GB، `video.json` 580 MB (من جدول README).
- **الإشارات:** تسلسلات مشاهدة الفيديو (سرعة، قفزات زمنية)، حل التمارين، تعليقات، تسجيل الدورات `course_order/enroll_time`، رسوم مفاهيم ومتطلبات سابقة وترجمات الفيديو (`docs/*.md`).
- **الاستخدام في التوصية:** الأقوى بين المرشحين. المرجع #22 (`S-0111`، PLOS ONE 2025) يستخدم MOOCCube بأرقام 82,536 مستخدماً / 1,303 دورة / 458,453 تفاعلاً (كثافة الندرة 99.57%)، وهي تقارب مجموعة XuetangX في المرجع #31 (`S-0609`، AAAI 2019: 1,302 / 82,535 / 458,454؛ التطابق استنتاجي، ثقة منخفضة). وكذلك `dwjds/HKER-seq` وKGAN.
- **ما تحمّل هنا:** **نسخة معالجة** من طرف ثالث فقط: `dwjds/HKER-seq/data/raw/mooccube.gz` (تحقق محلي: 64,763 صفاً `userid, course_id, timestamp`، 4,469 مستخدماً، 676 دورة، كثافة 2.14%، أطوال تسلسل 10–140 [وسيط 12] أي تصفية ≥ 10 تسجيلات، من 2013-01-01 إلى 2020-04-16) و`mooper.gz` (135,834 صفاً، 9,077 مستخدماً، 249 عنصراً، 2017-12-31 إلى 2019-12-30). ترخيص المستودع MIT (للشيفرة؛ حقوق AIRI)، **منشأ المعالجة غير موثق** → ثقة منخفضة.

### 2.5 KDD Cup 2015 (XuetangX dropout)

- **المصدر:** منافسة KDD Cup 2015 (بيانات XuetangX عبر `biendata.xyz/competition/kddcup2015/data/` بحسب Zenodo في مقتطف بحث). **محجوب هنا**؛ وفق مقتطف `cndn/kddcup-2015` البيانات غير متاحة على الموقع الرسمي بعد انتهاء المنافسة (ثانوي).
- **المرجع الأكاديمي:** لا ورقة بيانات رسمية وجدتها؛ يُستشهد بها عبر Feng et al. AAAI 2019 *Understanding dropouts in MOOCs* (ظهرت في نتائج البحث). الترخيص: **لم أجده** (❓).
- **البنية (DataDescription.txt في `AndyKANG98/Drop-MOOC-Prediction`):** `enrollment_*.csv`, `log_*.csv` (enrollment_id, time, source [server/browser]، event [7 أنواع: problem, video, access, wiki, discussion, navigate, page_close]، object)، `object.csv` (شجرة وحدات)، `date.csv`، `truth_train.csv`.
- **المتاح فعلاً هنا (تحقق محلي):** `TythonLee/kddcup-2015`: `data/object/object.csv` (**27,249 صفاً، 39 دورة**، 26,750 module_id، 15 فئة [vertical 9,823، problem 5,135، video 5,051...]، مع `children` و`start`)، و`train2.csv` (120,542 × 211 **ميزات مشتقة**) و`libfm/*`؛ و`lee14257/mooc-dropout-prediction` (ميزات عدّ أحداث مجمَّعة، 72,395 تسجيلاً). **لا يوجد `log_train.csv` الخام في أي مستودع جربته** (`TythonLee`, `yizhongw`, `cndn`, `ivanliu1989`, `hustmonk`, `ixhorse`, `AndyKANG98`, `lee14257`).
- **الاستخدام:** تنبؤ التسرب أساساً، لا توصية (ثانوي).

### 2.6 Canvas Network Open Dataset (Person-Course)

- **المصدر:** Harvard Dataverse، DOI 10.7910/DVN/1XORAL (من README edis8100؛ لم يؤكده WebSearch)، **محجوب هنا**. حجم: > 325,000 سجل في 238 دورة (Campus Technology 2016، ثانوي).
- **الترخيص:** CC BY 4.0 (README edis8100 يقول إنه تحقق من سجل Dataverse؛ ثانوي، ثقة متوسطة).
- **تحقق محلي** (`edis8100-datasets/canvas-network/person_course.csv.gz`): 325,199 × 26؛ 224,914 مستخدماً؛ 238 دورة؛ 10 تخصصات؛ **صف واحد لكل (شخص، دورة)** (وسيط دورة واحدة لكل مستخدم، الأقصى 128)؛ `nevents` متوفر لـ26.5% فقط؛ حقول استبيان (`primary_reason`, `learner_type`, `expected_hours_week`). **بيانات مجمّعة بلا سجلات أو تسلسل.**

### 2.7 ASSISTments 2009–2010 (skill builder)

- **المصدر:** موقع ASSISTments (sites.google.com/site/assistmentsdata) وIEEE DataPort (بحث؛ غير قابلة للوصول هنا). الترخيص: غير مؤكد هنا (❓).
- **تحقق محلي** (`ckyeungac/DeepKnowledgeTracing/data/skill_builder_data.csv`، ترميز ISO-8859-15): 525,534 × 30؛ 4,217 مستخدماً؛ 26,688 مسألة؛ 123 مهارة؛ 3,521 assignment؛ **لا طابع زمني** (فقط `order_id`). pykt يذكر 346,860 تفاعلاً بعد إزالة تكرار المهارات المتعددة (ثانوي).
- **الصلة:** تتبع معرفة وليس توصية مواد/ سلوك تصفح. الأقل مناسبةً.

### 2.8 Junyi Academy

- **المصدر:** Junyi Academy (تايوان)، وثائق `edudata.readthedocs.io`: سجل حل المسائل + بيانات تعريف التمارين (name, prerequisite, creation_date)؛ **استخدام تجاري ممنوع** مع وجوب الاستشهاد بـChang, Hsu, Chen (EDM 2015) (مقتطف بحث). لم أجد مستودع GitHub يحوي الملفات؛ **لم يُحمَّل**. أرقام الحجم لم أتحقق منها.

### 2.9 بيانات أخرى (مسح سريع)

| المجموعة | ما وجدته | القابلية هنا |
|---|---|---|
| **ITM-Rec** (Zheng, LAK 2023 companion) | تحقق محلي في `UcoRecSys/data/itm_dataset`: 5,230 تقييماً، 454 مستخدماً (README: 476)، 70 عنصراً (مواضيع مشاريع)، متغيرات سياق `Class/Semester/Lockdown`، تقييمات متعددة المعايير. استبيان لا سجلات. | تحمّلت (صغيرة جداً) |
| **Coursera/Udemy course lists** | `Siddharth1698/Coursera-Course-Dataset`: 891 × 7 (عنوان، جهة، تقييم، صعوبة، عدد مسجلين نصي "5.3k")؛ `ry05/couReco`: 1000 × 14 (مع skills ووصف). لا سلوك مستخدمين. Udemy: لم أجد ملف CSV على GitHub (Kaggle/Zenodo). | Coursera تحمّلت؛ Udemy لا |
| **HarvardX/MITx Person-Course (2014)** | سجل GitHub `clintonb/de_id` يحوي سكربتات إزالة التعريف فقط؛ البيانات على صفحة الإصدار الرسمي؛ شكل بيانات person-course مجمّع. | لا |
| **سجلات Moodle مفتوحة** | UNISTUDIUM 2022 (Perugia، IEEE DataPort/Zenodo 13763174)، Moodle Event Logs لجامعة Cádiz (Zenodo، CC BY 4.0 بحسب البحث)، «Learn Moodle August 2016» (research.moodle.net)، Blended CS course (Nitra، مع معرفات وIP: خصوصية!). | لا (Zenodo/DataPort محجوبان) |
| **MOOPer** | ملف معالج 135,834 تفاعلاً داخل HKER-seq (انظر 2.4). | تحمّلت (ثانوي) |
| **XuetangX (Zhang et al. AAAI 2019)** | 1,302 دورة، 82,535 مستخدماً، 458,454 تسجيلاً (المرجع #31 محلياً). لم أجد إصداراً عاماً لهذه المجموعة على GitHub. | لا |

---

## 3. سجل محاولات التحميل (حرفي قدر الإمكان)

### 3.1 قنوات الشبكة المختبَرة

| القناة | الأمر | النتيجة |
|---|---|---|
| `git clone` من github.com | `GIT_LFS_SKIP_SMUDGE=1 timeout 300 git clone --depth 1 https://github.com/<owner>/<repo>.git` | **تعمل** (≈ 30 مستودعاً) |
| أصول Releases | `curl -sS -L -o gitlfs.tgz https://github.com/git-lfs/git-lfs/releases/download/v3.4.1/git-lfs-linux-amd64-v3.4.1.tar.gz` | **تعمل**: `200 4930444` عبر `release-assets.githubusercontent.com` (حُذف الملف بعد الاختبار). لم أجد مجموعة بيانات تعليمية منشورة كـ release asset |
| Git LFS | `git lfs pull --include="ETL/staging_data/studentInfo.csv"` في `LuongAnh1/oulad-data-warehouse` | **فشل**: `batch response: access denied by the git proxy: LuongAnh1/oulad-data-warehouse is not in this session's authorized repository set, so the proxy will not inject a credential for it.` ثم `Failed to fetch some objects from '.../info/lfs'`. الملف بقي مؤشراً (132 بايت). **LFS لا يعمل إلا للمستودعات المضافة لمصادر الجلسة** (لم أُضف أي مستودع) |
| GitHub API للبحث | `gh api "search/code?q=filename:studentVle.csv"` و`search/repositories` | **403**: `This GitHub API path is not available: sessions are bound to their configured repositories` |
| WebFetch | `github.com/Pacatro/UcoRecSys`، PMC9932724 | `getaddrinfo ENOTFOUND` (غير صالح هنا) |
| `raw.githubusercontent.com` | `curl .../riiid/ednet/master/README.md` | **403** `CONNECT tunnel failed` (فقط git الوارد من github.com يعمل) |

### 3.2 المضيفون المحجوبون (جميعهم `curl: (56) CONNECT tunnel failed, response 403`، رمز HTTP يعاد 000)

- `https://schools.stem.open.ac.uk/cdn/files/anonymisedData.zip` (رابط OULAD المستخدم في سكربت `HakeoungLee/build_subsets.py`)
- `https://analyse.kmi.open.ac.uk/open_dataset`، `https://research.stem.open.ac.uk/ouanalyse/dataset/`
- `https://archive.ics.uci.edu/static/public/349/open+university+learning+analytics+dataset.zip`
- `https://www.biendata.xyz/competition/kddcup2015/data/`
- `http://moocdata.cn/data/MOOCCube`، `https://lfs.aminer.cn/misc/moocdata/data/mooccube2/entities/course.json` (+ `school.json`, `mooccubex.pdf`)
- `http://bit.ly/ednet_kt1`
- `https://zenodo.org/record/5913337`، `https://huggingface.co/datasets/mgor/EDNet/tree/main`
- `https://www.kaggle.com/datasets/anlgrbz/student-demographics-online-education-dataoulad`
- `https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/1XORAL`، `https://data.mendeley.com/datasets/`
- `https://mandarine.academy/mars-dataset/`، `https://pmc.ncbi.nlm.nih.gov/articles/PMC9932724/`، `https://www.nature.com/articles/sdata2017171`، `https://www.sciencedirect.com`

### 3.3 مستودعات استُنسخت **دون** بيانات خام قابلة للاستخدام (لا تكرروها)

| المستودع | النتيجة |
|---|---|
| `tranmink/OULAD` (مخرجات نماذج فقط؛ أما `MarkLaVenia/OULAD` فلم يُستنسخ بسبب تصادم اسم المجلد `OULAD` مع الأول)، `johnnbb/oulad-learning-dw`، `ssemerikov/oulad`، `duducolydev/analyses_oualad`, `AdonisKing2003/data_engineer_project`, `gogoladzetedo/Open_University_Analytics`, `KerensaLam/-OULA-DataSet-CaseStudy` | تحليلات/نتائج/SQL فقط، **بلا `studentVle`** (README أحدها يصرّح أنه «أكبر من حد GitHub»). ملاحظة: أول محاولة لـ`KerensaLam` فشلت بسبب خطأ في سكربتي (اسم يبدأ بـ`-` فُسّر خيارَ git)، وأُعيدت بنجاح؛ لا بيانات |
| `HE181429/oulad-student-risk-prediction` | يعلن في README أن CSV متتبَّعة بـGit LFS (`*.csv filter=lfs`)، لكن **لم تُودَع أي CSV**؛ فقط `Data/oulad_md5_reference.txt` (استُخدم للتحقق، انظر 4.1) |
| `deepaksen1996/oulad_dataset` | 6 جداول OULAD بترميز مقتبس لكن **دون `studentVle`** |
| `reyquiroz/OULAD_CourseAware` | 6 جداول خام (md5 مطابق للمرجع) **دون `studentVle`** |
| `marcosrc92/MARS-data` | **ليس مجموعة MARS التعليمية**: معايير GPU/CUDA (Rodinia traces). ترخيص CC-BY-2.5 الذي ظهر في سجل Dagstuhl لا علاقة له بـMARS التعليمية، **لا تستشهدوا به** |
| `THU-KEG/MOOCCube`، `THU-KEG/MOOCCubeX-Builder` | `fatal: could not read Username for 'https://github.com': terminal prompts disabled` (المستودعان غير موجودين بهذا الاسم). الصحيح: `thukg/MOOCCube` (README+LICENSE فقط) |
| `THU-KEG/MOOCCubeX` | وثائق وسكربتات فقط؛ البيانات على `lfs.aminer.cn` (محجوب) |
| `THU-KEG/MOOC-Radar` | `baselines-video/user2video.txt` ملف صغير (84 KB، خريطة user→video واحد لكل مستخدم تقريباً، لا يكفي) |
| `riiid/ednet` | README فقط |
| مستودعات KDD Cup 2015 (`yizhongw`, `cndn`, `ivanliu1989`, `hustmonk`, `ixhorse`, `AndyKANG98`) | شيفرة/ميزات/مراجع فقط، **لا `log_train.csv`** (`.gitignore` في AndyKANG98 يستثني `data/train` و`data/*.csv`) |

### 3.4 التحميلات الناجحة والتحقق (المسارات تحت `$PROBE`)

| المجلد | المصدر | الحجم | ما اعتُمد |
|---|---|---|---|
| `oulad-data-warehouse/raw_data/` | `LuongAnh1/oulad-data-warehouse` (HEAD `87c0d1a`، 2026-10-11) | 392 MB | OULAD كاملة: `studentVle_0..7.csv` + 6 جداول |
| `OULAD_CourseAware/data/raw/` | `reyquiroz/OULAD_CourseAware` | 126 MB (المستودع) | 6 جداول مرجعية للمقارنة |
| `UcoRecSys/data/mars_dataset/` + `itm_dataset/` | `Pacatro/UcoRecSys` (2025-09-26) | 33 MB | MARS EN+FR، ITM-Rec |
| `Zaynabmnk_edu-recommender/data/raw/` | `Zaynabmnk/edu-recommender` | 29 MB | MARS EN (نسخة مستقلة) |
| `edis8100-datasets/` | `HakeoungLee/edis8100-datasets` (2026-10-14) | 70 MB | OULAD-BBB، EdNet KT3-500، Canvas PC |
| `dwjds_HKER-seq/data/raw/` | `dwjds/HKER-seq` | 3.6 MB | MOOCCube/MOOPer معالجة |
| `kddcup-2015/data/` | `TythonLee/kddcup-2015` | 295 MB | `object.csv` + ميزات مشتقة |
| `ckyeungac_DeepKnowledgeTracing/data/` | `ckyeungac/DeepKnowledgeTracing` | 194 MB | ASSISTments 2009 |

---

## 4. نتائج التحقق (pandas) حرفياً

### 4.1 OULAD الكاملة

```
python3 -I: pd.concat([pd.read_csv(f, index_col=0) for f in sorted(glob('raw_data/studentVle_*.csv'))])
studentVle (10655280, 6) ['code_module','code_presentation','id_student','id_site','date','sum_click']
students 26074  sites 6268  modules 7  pres 4   date -25..269   sum_click 39605099   nulls 0
vle (6364, 6)  studentInfo (32593, 12)  studentRegistration (32593, 5)  studentAssessment (173912, 5)  assessments (206, 6)  courses (22, 3)
final_result: Pass 12361, Withdrawn 10156, Fail 7052, Distinction 3024        (وقت التحميل والتحليل ≈ 24 ث)
```

- **تحقق السلامة (نقطة حاسمة):** أجزاء `studentVle` في المرآة معاد تصديرها (عمود فهرس بلا اسم، 8 ملفات). أعدتُ بناء `studentVle.csv` الأصلي بحذف عمود الفهرس وتقييس كل الحقول بعلامات اقتباس وإنهاء الأسطر بـ`CRLF`، فكان **md5 = `b8aae6f4ffd1523319aeb56d66b17f72`** وهو **مطابق تماماً** للقيمة في `HE181429/.../Data/oulad_md5_reference.txt`. الجداول الستة الأخرى في المرآة **مطابقة قيمةً** لنسخة `OULAD_CourseAware` التي **md5 كل ملفاتها يطابق** نفس ملف المرجع. عدد الصفوف 10,655,280 يطابق رقم الورقة (مقتطف بحث ResearchGate).
- **حدود هذا الدليل:** ملف md5 المرجعي نفسه من مستودع طرف ثالث (لا أستطيع الوصول لقيمة OU الرسمية). تطابق 7 من 7 ملفات مع مصدرين مستقلين + العدد الرسمي يرفع الثقة إلى **عالية** بأن البيانات هي OULAD الأصلية، لكنه ليس تحققاً من الموقع الرسمي.
- **بنية مهمة للتصميم (تحقق محلي):**
  - `id_site` فريد لكل عرض (presentation): كل موقع ينتمي لعرض واحد (`groupby('id_site').size().max()==1`). **لا يوجد هوية عنصر مشتركة بين العروض.**
  - عدد أزواج (تسجيل، مورد) = 1,960,496؛ التسجيلات ذات السجلات 29,228؛ وسيط الموارد المختلفة لكل تسجيل 51 (الربع الأول 27، الربع الأخير 93، الأقصى 413)؛ وسيط الأيام النشطة 47.
  - كثافة مصفوفة (طلاب × موارد) داخل كل عرض: **11%–41%** (مثلاً DDD_2013J: 1,768 × 456 = 19.3%؛ FFF_2013J: 2,098 × 526 = 20.8%؛ EEE_2013J: 964 × 107 = 40.9%)، وبالمقارنة كثافة المصفوفة العالمية (كل التسجيلات × كل المواقع) 1.05%. أي أن التوصية ستكون **داخل المقرر** على فهارس عناصر صغيرة (100–530).
  - 2,989 طالباً من 26,074 مسجلون في أكثر من عرض.
  - 19.1% من مجموعات (طالب، مورد، يوم) فيها أكثر من صف (حتى 10)؛ و787,170 صفاً مكرراً حرفياً (نقرات مجمَّعة بعدة صفوف في اليوم نفسه، وليست أخطاء بالضرورة).
  - نقرات حسب النوع (الأكثر): oucontent 11.2M، forumng 8.0M، quiz 7.0M، homepage 6.9M، subpage 3.4M.

### 4.2 MARS (انظر الأرقام في 2.2)

```
python3 -I: pd.read_csv('implicit_ratings_en.csv') -> (21908, 3) ['item_id','user_id','created_at']; users 3007; items 957; density 0.7613%
            explicit_ratings_en.csv -> (3659, 5); users 822; items 776
            implicit_ratings_fr.csv -> (253827, 3); users 18519; items 1377; density 0.9954%
            explicit_ratings_fr.csv -> (85339, 5); users 9789; items 1350
md5sum (UcoRecSys vs Zaynabmnk) لملفات EN الأربعة: متطابقة بايتياً (e3edf39d..., 8ea0943c..., c6dbe254..., c7e734a2...)
```

- الملفات FR **موجودة في مصدر واحد فقط** (UcoRecSys) فلا مقارنة مستقلة لها. مجموعاها (275,735 implicit؛ 88,998 explicit) يتطابقان مع ملخص الورقة (≈ 276,000 و89,000).
- توزيع النشاط (implicit): EN وسيط 3 مشاهدات/مستخدم (≥ 3: 1,615 مستخدماً؛ ≥ 10: 574)، FR وسيط 3 (≥ 3: 10,856؛ ≥ 10: 4,642). ذيل طويل (الأقصى 327 EN، 2,558 FR).

### 4.3 بقية ما حُمّل (ملخص)

- **EdNet KT3-500:** انظر 2.3. `NA` فقط في `user_answer` (نتيجة طبيعية). الأعمدة: `timestamp, action_type, item_id, source, user_answer, platform, user_id`.
- **OULAD-BBB (edis8100):** `studentVle.csv.gz` 891,062 صفاً، 3,757 طالباً، 526 موقعاً (مجموعة جزئية جاهزة للتطوير السريع، CC BY 4.0).
- **Canvas / ASSISTments / ITM-Rec / HKER-seq / KDD:** انظر البطاقات.

---

## 5. المصفوفة المقارنة الموزونة

### 5.1 المعايير والأوزان (مجموعها 100) وتبريرها

| # | المعيار | الوزن | التبرير |
|---|---|---|---|
| C1 | احتواء سجلات سلوك خام تسلسلية | **20** | عنوان الرسالة وأهدافها (تحليل سلوك المستخدم، الجلسات، RNN) تتطلبها مباشرة |
| C6 | التوافق مع أهداف الخطة (توصية مواد + تصنيف/تجميع المتعلمين) | **20** | الأهداف الفرعية 1–3 في الخطة |
| C5 | بيانات وصفية للعناصر (CBF) | **15** | CBF كلمة مفتاحية في الخطة ومطلوب لمعالجة cold-start |
| C8 | استخدام سابق في بحوث التوصية (قابلية المقارنة) | **15** | يسمح بالمقارنة مع المراجع، لكنه ليس شرطاً علمياً بحد ذاته |
| C2 | الموثوقية والمصدر الأكاديمي | **10** | |
| C3 | الترخيص يسمح بالبحث | **10** | |
| C4 | الحجم المناسب لـnumpy/pandas (مثالي 10^5–10^7) | **10** | قيد البيئة، قابل للتخفيف بالعينات |
| C7 | القابلية الفعلية للتحميل هنا | **بوابة** (نجاح/فشل) لا وزن | معيار إقصائي كما طلب: «Y» محقق هنا، «Y*» عينة/نسخة معالجة، «N» غير محمّل |

الدرجة = Σ (وزن × درجة 0–5) / 5، مع 0 = غائب تماماً و5 = ممتاز. (السكربت: `/tmp/claude-0/-home-user-rec-eLearning-sys/d9fa8d7f-28c1-526d-a725-5245fbf905b7/scratchpad/tools/score.py`.)

### 5.2 النتائج (مرتبة تنازلياً)

| الترتيب | المجموعة | C1 | C2 | C3 | C4 | C5 | C6 | C8 | **الدرجة /100** | بوابة التحميل |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MOOCCube (خام) | 5 | 4 | 4 | 4 | 5 | 5 | 5 | 94 | **N** (من الوثائق فقط) |
| 2 | MOOCCubeX (خام) | 5 | 4 | 3 | 1 | 5 | 5 | 4 | 83 | **N** |
| 3 | **OULAD (كاملة)** | 4 | 5 | 5 | 5 | 2 | 4 | 4 | **80** | **Y** (تحقق كامل) |
| 4 | **MARS (EN+FR)** | 4 | 4 | 3 | 5 | 5 | 3 | 3 | **76** | **Y** (ترخيص بتحفظ) |
| 5 | EdNet KT3 (كامل) | 5 | 4 | 4 | 1 | 4 | 4 | 3 | 75 | **N** |
| 6 | EdNet KT3-500 (مستخرَج) | 5 | 3 | 4 | 5 | 1 | 3 | 3 | 68 | Y* |
| 7 | Junyi Academy | 3 | 4 | 4 | 3 | 4 | 3 | 2 | 64 | N |
| 8 | KDD Cup 2015 (سجلات خام) | 5 | 3 | 2 | 4 | 3 | 2 | 2 | 61 | **N** (ميزات مشتقة فقط) |
| 9 | ASSISTments 2009 | 3 | 4 | 3 | 5 | 3 | 2 | 2 | 59 | Y |
| 10 | MOOCCube معالجة (HKER-seq) | 2 | 3 | 4 | 3 | 1 | 3 | 4 | 55 | Y* |
| 11 | Moodle logs مفتوحة | 4 | 3 | 4 | 4 | 1 | 2 | 1 | 52 | N |
| 12 | ITM-Rec | 0 | 4 | 3 | 1 | 3 | 3 | 3 | 46 | Y |
| 13 | Canvas Network PC | 0 | 3 | 4 | 5 | 2 | 2 | 1 | 41 | Y |
| 14 | HarvardX-MITx PC | 0 | 4 | 3 | 4 | 1 | 2 | 2 | 39 | N |
| 15 | قوائم Coursera/Udemy | 0 | 1 | 1 | 0 | 4 | 1 | 2 | 26 | Y* |

**قراءة النتيجة:** المجموعتان الأعلى درجة (MOOCCube/MOOCCubeX) **مستبعدتان بالبوابة** ودرجتاهما من الوثائق فقط، فالفرق بينهما وبين الباقين قد يكون متفائلاً. **بين ما يمر البوابة فعلاً تتصدر OULAD ثم MARS**، ثم EdNet-500 كبيئة تجريب.

### 5.3 اختبار الحساسية للأوزان (نفس الدرجات)

| سيناريو الأوزان | ترتيب المارّين بالبوابة |
|---|---|
| الأساسي | OULAD 80 > MARS 76 > EdNet-500 68 > ASSISTments 59 |
| متساوية (14.3 لكلٍّ) | OULAD 82.9 > MARS 77.1 > EdNet-500 68.6 > ASSISTments 62.9 |
| تركيز على السلوك (C1=30, C6=25) | OULAD 81 > MARS 75 > EdNet-500 74 |
| تركيز على CBF (C5=30) | **MARS 80 > OULAD 74** > ASSISTments 60 |

**الخلاصة:** المركزان الأول والثاني بين القابلة للتحميل ثابتان: {OULAD, MARS}، وترتيبهما يتبدّل حسب وزن CBF. الفارق بينهما (≈ 4 نقاط) ضمن هامش الذاتية؛ **لا يُعتمد عليه وحده**.

---

## 6. أفضل خيارين (ترشيح وليس قراراً)

### الخيار أ: OULAD (الكاملة)

**المبررات:**
1. أقوى توثيق أكاديمي وترخيص واضح (CC BY 4.0) وتحقق سلامة بالـmd5 وأعداد الصفوف.
2. 10.66M سجلاً يُحمَّل بـpandas في ≈ 24 ث؛ ممتاز لأسلوب «سجلات سلوك» الذي يتطلبه العنوان.
3. يخدم **كل أهداف الخطة**: بيانات ديموغرافية ونتائج (`final_result`) وتسليمات تقييم تسمح بـ**تصنيف** (Pass/Fail/Withdrawn) و**تجميع** المتعلمين، إضافةً لتوصية الموارد داخل المقرر. هو الوحيد الذي يعطي «هدفاً تصنيفياً» جاهزاً.
4. سياق قابل للاستخدام في «Context-Aware»: أسبوع المقرر، مواعيد التقييم، نوع النشاط.

**المخاطر:**
- **دقة اليوم فقط:** لا ترتيب داخل اليوم ولا طوابع زمنية → «الجلسة» تُعرَّف باليوم/الأسبوع، ولا يُنتظر RNN بترتيب نقرات حقيقي.
- **العناصر لا تُنقل بين العروض** (`id_site` فريد لكل عرض) وبياناتها الوصفية هزيلة (`activity_type` + `week_from/to` غير متوفرة 82%) → **CBF ضعيف** (لا عناوين ولا مواضيع).
- **المصفوفة كثيفة نسبياً (11–41%) وعناصرها قليلة (100–530)**: تقييم التوصية سهل رقمياً لكنه أقل إقناعاً مقارنةً بمعايير المراجع؛ قد تكون الدرجات مرتفعة بسبب نقطة الأساس (popularity).
- لا توجد تغذية راجعة صريحة؛ التوصية «مواد» تعني موارد VLE في مقرر واحد وليس «دورات».
- الملفات من **مرآة طرف ثالث** (الموقع الرسمي محجوب)؛ يجب توثيق المرآة والتحقق (تم) وذكر المصدر الأصلي في المراجع.

**خطة معالجة أولية:**
- **الوحدات:** المستخدم = تسجيل (module, presentation, student)؛ العنصر = `id_site` ضمن العرض، بخصائص `activity_type`, وربما رتبة الأسبوع الأول للزيارة؛ استبعاد/تقليل وزن `homepage`/`subpage` (تنقلية) قابل للضبط.
- **الإشارة الضمنية:** `y_ui = log1p(Σ sum_click)` ثم ثنائية (≥ 1 أو ≥ 2 أيام مختلفة)؛ ثقة `c = 1 + α·log(1+clicks)` (نمط Hu-Koren-Volinsky) للـALS؛ عدد الأيام النشطة كإشارة أقوى من النقرات.
- **الجلسات:** `session = (تسجيل، أسبوع)` أو `(تسجيل، يوم)`؛ التسلسل = «سلات أيام» مرتبة بـ`date` (لا ترتيب داخلها) → مناسب لـSession-kNN/Markov على مستوى الأيام.
- **التقسيم:** زمني داخل كل عرض (مثلاً التدريب حتى الأسبوع k، الاختبار الأسابيع التالية) لتجنّب التسريب؛ تقييم HR@K/NDCG@K على موارد الأسابيع التالية. اختياري: التدريب على 2013 والاختبار على 2014 لنفس المقرر مع ربط العناصر بـ(`activity_type`، ترتيب الظهور) كتقريب، وهو افتراض يحتاج تبريراً.
- **التصنيف/التجميع:** ميزات لكل تسجيل في نافذة مبكرة (نقرات حسب النوع، أيام نشطة، انتظام، تاريخ التسجيل، تسليم التقييمات ودرجاتها، `num_of_prev_attempts`) → k-means/Random Forest **مكتوبَين بـnumpy** (sklearn غير متاح)؛ الهدف `final_result`.
- **البداية الباردة:** `studentInfo` (ديموغرافيا) + محتوى النشاط لطلاب بلا تاريخ.

### الخيار ب: MARS (EN وFR)

**المبررات:**
1. **الأغنى بيانات وصفية للعناصر** بين ما حُمّل (عنوان + ترجمة نصية + Difficulty/Job/Software/Theme/type/duration) → CBF حقيقي (TF-IDF) وهجين.
2. طوابع بالثانية → **جلسات حقيقية** (EN 6,780 جلسة؛ FR 64,253) وسلاسل لـMarkov/GRU/Session-kNN، وتكرار المشاهدة (32–40%) كإشارة اهتمام.
3. حجم مثالي للبيئة (EN ~22k، FR ~254k implicit؛ 88,998 explicit) وصنفان (implicit/explicit) يسمحان بمقارنة تأثير نوع الإشارة.
4. ورقة بيانات محكّمة (Data in Brief 2023) وتخصيص صريح لتوصية التعلم الإلكتروني، وملخص الحجم يطابق ما حمّلناه.

**المخاطر:**
- **الترخيص غير محسوم:** CC0 بحسب مصدر ثانوي، ونموذج طلب/اتفاقية مشاركة بحسب صفحة Mandarine؛ **الحصول من مرايا GitHub قد يكون إعادة توزيع غير مصرّح بها**. المطلوب تأكيد قسم Terms في Dataverse قبل الاستخدام.
- **تناثر شديد:** وسيط 3 مشاهدات لكل مستخدم؛ EN فقط 1,615 مستخدماً بـ≥ 3 مشاهدات (574 بـ≥ 10) → عينة صغيرة وتباين عالٍ في المقاييس.
- **لا هدف تصنيفي ولا نتائج تعلم ولا ديموغرافيا:** هدف «تصنيف/تجميع المتعلمين» لا يُبنى إلا بتعريفات اصطناعية (مثلاً وسم completion من `watch_percentage`)؛ مجال تدريب مهني (Microsoft 365) وليس تعليماً جامعياً.
- EN وFR **منفصلان**: لا دمج بينهما (لا تقاطع)، والنسخة FR مصدرها مستودع واحد فقط.
- استخدام أكاديمي محكّم سابق محدود → مقارنة أضعف بالأدبيات.

**خطة معالجة أولية:**
- **الوحدات:** المستخدم = `user_id`؛ العنصر = `item_id` (فيديو) في كتالوج اللغة؛ تحليل كل لغة مستقلاً (FR الأساسي، EN للتحقق).
- **الإشارات:** implicit = عدد المشاهدات (يشمل التكرار) مع تضعيف زمني؛ explicit = `watch_percentage` (قيم 0–100) كمقياس إتمام؛ الدمج: `c = 1 + α·views + β·watch_pct/100`.
- **الجلسات:** فجوة خمول 30 دقيقة (يمكن ضبطها)؛ تسلسل العناصر داخل الجلسة للـMarkov/GRU والتنبؤ بالعنصر التالي.
- **CBF:** TF-IDF على `name + description`، ووسوم `Theme/Software/Difficulty/Job` كمتجهات ثنائية، و`type/duration` كخصائص رقمية؛ هجين وزني يعتمد على طول تاريخ المستخدم (كما فعل مشروع Zaynabmnk).
- **التقسيم:** leave-last-out لكل مستخدم + تقسيم زمني عند تاريخ ثابت (مثلاً 2019-07-01) لقياس البداية الباردة للعناصر الجديدة؛ تصفية المستخدمين بـ≥ 3 تفاعلات.
- **التجميع:** على سلوك المشاهدة (ثيمات مفضلة، مستوى الصعوبة، نشاط زمني) وحقل `job` حيث يتوفر.

### ملاحظة عن الجمع بينهما (للنقاش فقط)
OULAD تغطي بشكل أفضل هدف **تحليل السلوك/التصنيف/التجميع** وMARS تغطي بشكل أفضل **CBF والتسلسل الحقيقي**. استخدامهما معاً (أساسية + ثانوية للتعميم) يخفف نقاط ضعف كل منهما لكنه يضاعف العمل؛ هذا قرار للمشرف.

---

## 7. أسئلة مفتوحة للمشرف

1. **وحدة التوصية:** هل «المادة التعليمية» في الخطة هي مورد داخل مقرر (OULAD/MARS) أم دورة كاملة (MOOCCube)؟ الإجابة تغيّر الاختيار جذرياً.
2. **تعدد المجموعات:** هل يكفي مجموعة واحدة أم يُطلب مجموعتان (أساسية + تحقق تعميم)؟
3. **مصدر البيانات:** هل تقبل الجامعة استخدام **مرايا GitHub** (مع الاستشهاد بالمصدر الرسمي والتحقق بـmd5) بدلاً من التحميل من المصدر الرسمي؟ ويُمكن للطالب (من شبكة غير مقيّدة) تحميل MOOCCube أو EdNet رسمياً ورفعه كـrelease في مستودع خاص (القناة `release-assets.githubusercontent.com` تعمل هنا) أو إضافة المستودع لمصادر الجلسة لتمكين Git LFS؛ هل يُستحسن ذلك مقابل التعقيد؟
4. **ترخيص MARS:** من يؤكد شروط Dataverse/اتفاقية Mandarine؟ (مطلوب قبل أي استخدام).
5. **هدف التصنيف:** هل نكتفي بتصنيف `final_result` (OULAD) كمحور «تحليل سلوك المتعلم»، أم يجب أن يرتبط التصنيف بنموذج التوصية نفسه؟
6. **بروتوكول التقييم:** هل يُقبل تقييم **غير متصل (offline)** بتقسيم زمني مع HR@K/NDCG@K/Coverage؟ وما خطوط الأساس المطلوبة (Popularity، Item-kNN، ALS، Markov، Session-kNN)؟
7. **قيد الأدوات:** الخطة تذكر TensorFlow/Keras وSklearn؛ البيئة لا تتيحهما (numpy/pandas فقط). هل يُقبل تنفيذ الشبكات (RNN) يدوياً أو استبدالها بنموذج تسلسلي بديل مبرَّر؟
8. **السياق (Context-Aware):** أي سياق مقبول؟ (OULAD: أسبوع المقرر/موعد التقييم/نوع النشاط؛ MARS: وقت اليوم/الوظيفة؛ ITM-Rec فيها سياق صريح لكنها صغيرة جداً).
9. **KDD Cup 2015:** إذا لزم استخدامها (لارتباطها بمراجع التسرب)، هل يُرجى الحصول على `log_train.csv` من الزملاء؟ لم أجده على GitHub.

---

## 8. سجل الادعاءات والمصادر (claim registry مختصر)

| الادعاء | المصدر | القوة | الثقة |
|---|---|---|---|
| OULAD: 10,655,280 صفاً في studentVle، 32,593 طالباً | تحقق محلي pandas + مقتطف بحث (ResearchGate/Sci Data) | أولي + ثانوي | **عالية** |
| OULAD تطابق md5 للملفات | محلي، مرجع md5 من `HE181429` (طرف ثالث) | ثانوي | عالية/متوسطة |
| OULAD ترخيص CC BY 4.0 | مقتطف بحث (Sci Data/OU) + README edis8100 | ثانوي ×2 | عالية |
| MARS أحجام | محلي + مقتطف بحث للملخص | أولي + ثانوي | **عالية** |
| MARS ترخيص CC0 | README مستودع `Zaynabmnk` فقط؛ يعارضه مقتطف صفحة Mandarine | ثانوي | **منخفضة (متعارض)** |
| MARS EN مطابقة بايتية بين مستودعين | `md5sum` محلي | أولي | عالية |
| EdNet الحجم والترخيص CC BY-NC 4.0 | README `riiid/ednet` المستنسخ محلياً | أولي | عالية |
| MOOCCubeX الحجم (296M سجل / 3.33M طالب) | README المستنسخ محلياً | أولي | عالية |
| MOOCCube الحجم (706 دورة...) | مقتطف بحث (ACL/IEEE DataPort) | ثانوي | متوسطة |
| MOOCCube ترخيص CC0 | `LICENSE` في `thukg/MOOCCube` محلياً | أولي (ترخيص المستودع) | متوسطة |
| KDD2015: 39 دورة، 27,249 وحدة | محلي من `object.csv` (نسخة طرف ثالث) | ثانوي | متوسطة |
| KDD2015 الخام غير متاح على GitHub | بحث في 8 مستودعات + WebSearch | أولي (عدم وجود) | متوسطة (قد يوجد مستودع لم أجده) |
| Junyi غير تجاري | مقتطف `edudata` | ثانوي | منخفضة |
| تطابق XuetangX AAAI19 مع MOOCCube في [22] | استنتاج من أرقام متقاربة | استنتاج | منخفضة |

### المصادر (روابط ظهرت في نتائج WebSearch أو مستودعات استُنسخت)

- OULAD: https://research.stem.open.ac.uk/ouanalyse/open-dataset-more/ ، https://archive.ics.uci.edu/dataset/349 ، https://pmc.ncbi.nlm.nih.gov/articles/PMC5704676
- مرايا OULAD المستخدمة: https://github.com/LuongAnh1/oulad-data-warehouse ، https://github.com/reyquiroz/OULAD_CourseAware ، https://github.com/HakeoungLee/edis8100-datasets ، https://github.com/HE181429/oulad-student-risk-prediction (مرجع md5)
- MARS: https://pmc.ncbi.nlm.nih.gov/articles/PMC9932724/ ، https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/BMY3UD ، https://mandarine.academy/mars-dataset/ ، https://github.com/Pacatro/UcoRecSys ، https://github.com/Zaynabmnk/edu-recommender ، https://ceur-ws.org/Vol-3268/paper9.pdf
- EdNet: https://github.com/riiid/ednet ، https://arxiv.org/abs/1912.03072
- MOOCCube/X: https://github.com/thukg/MOOCCube ، https://github.com/THU-KEG/MOOCCubeX ، https://github.com/dwjds/HKER-seq ، https://ieee-dataport.org/node/13679
- KDD Cup 2015: https://github.com/TythonLee/kddcup-2015 ، https://github.com/AndyKANG98/Drop-MOOC-Prediction ، https://www.r-bloggers.com/2015/06/kdd-cup-2015-the-story-of-how-i-built-hundreds-of-predictive-models-and-got-so-close-yet-so-far-away-from-1st-place/
- ASSISTments: https://github.com/ckyeungac/DeepKnowledgeTracing ، https://pykt-toolkit.readthedocs.io/en/dev/datasets.html
- Junyi: https://edudata.readthedocs.io/en/dev/build/blitz/junyi/junyi.html
- Canvas: https://campustechnology.com/articles/2016/03/02/instructure-opens-up-canvas-network-data.aspx
- Moodle/HarvardX: https://zenodo.org/records/15298539 ، https://github.com/clintonb/de_id

---

## ملخص للاجتماع

1. **ما حُمِّل فعلاً وتم التحقق منه بـpandas:** OULAD الكاملة (studentVle = 10,655,280 صفاً؛ md5 مطابق لمرجع)، وMARS (EN 21,908 + FR 253,827 implicit؛ EN متطابقة بايتياً في مستودعين).
2. **عينات صالحة للتجريب فقط:** EdNet KT3-500 (1.89M فعل، بلا بيانات وصفية)، MOOCCube/MOOPer معالجة (64,763 / 135,834 تفاعلاً)، Canvas PC (مجمّع)، ASSISTments 2009.
3. **لم يمكن تحميله:** MOOCCube/X الخام، EdNet الكامل، KDD Cup 2015 الخام (فقط ميزات مشتقة + object.csv)، Junyi، Moodle logs، HarvardX؛ المضيفون يعطون 403، وGit LFS مرفوض لمستودعات خارج مصادر الجلسة.
4. **الترتيب الموزون بين ما يمر بوابة التحميل:** OULAD 80 ثم MARS 76 (ثم EdNet-500 68). الترتيب بين الأولى والثانية يتبدل لصالح MARS لو رُفع وزن CBF؛ الفارق ضمن هامش الذاتية.
5. **خيار أ، OULAD:** الأقوى توثيقاً وترخيصاً (CC BY 4.0)، ويدعم التصنيف والتجميع (final_result) وتوصية موارد VLE.
6. **مخاطر OULAD:** دقة يومية فقط، `id_site` خاص بكل عرض، بيانات وصفية للعناصر هزيلة (CBF ضعيف)، مصفوفة كثيفة وعناصرها 100–530 داخل المقرر.
7. **خيار ب، MARS:** أغنى CBF (عناوين، ترجمات، وسوم)، جلسات حقيقية، وحجم مثالي.
8. **مخاطر MARS:** **ترخيصه غير محسوم** (CC0 بمصدر ثانوي مقابل اتفاقية مشاركة بحسب صفحة Mandarine)، وتناثر شديد (وسيط 3 مشاهدات)، ولا هدف تصنيفي ولا نتائج تعلم.
9. **الأقوى على الورق ولم يُحمَّل:** MOOCCube/X (94 و83 نقطة)؛ التحصيل يتطلب أن يحمّله الطالب رسمياً ويرفعه كـrelease خاص، أو إضافة المستودع لمصادر الجلسة.
10. **تنبيه:** `marcosrc92/MARS-data` ليس MARS التعليمية (معايير GPU)؛ لا يُستشهد بترخيصه.
11. **الأسئلة الحاسمة للمشرف:** وحدة التوصية (مورد أم دورة)، مجموعة واحدة أم اثنتان، قبول مرايا GitHub، وتأكيد ترخيص MARS.
12. **قيد منهجي:** درجات المصفوفة ذاتية 0–5، والمجموعات غير المحمّلة قُيّمت من وثائقها فقط.
13. **المحتويات المحلية:** المسارات تحت `/tmp/claude-0/-home-user-rec-eLearning-sys/d9fa8d7f-28c1-526d-a725-5245fbf905b7/scratchpad/data-probe/` (OULAD في `oulad-data-warehouse/raw_data`، MARS في `UcoRecSys/data/mars_dataset`).

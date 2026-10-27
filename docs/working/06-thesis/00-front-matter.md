# المقدمات

## صفحة العنوان (بالعربية)

**الجمهورية العربية السورية**
**الجامعة الافتراضية السورية**
**برنامج ماجستير علوم الوب**

&nbsp;

# نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم

&nbsp;

رسالة أُعدّت لنيل درجة الماجستير في علوم الوب

&nbsp;

**إعداد الطالب:** كنان محمد قرحالي

**إشراف:** د. باسل الخطيب

&nbsp;

العام 2026

---

## Title Page (English)

**Syrian Arab Republic**
**Syrian Virtual University**
**Master of Web Science Program**

&nbsp;

# A Recommendation System for E-Learning Based on User Behavior Analysis

&nbsp;

A thesis submitted in partial fulfillment of the requirements for the degree of Master of Web Science

&nbsp;

**Prepared by:** Kinan Mohammad Karhali

**Supervised by:** Dr. Basel Alkhatib

&nbsp;

2026

---

## الشكر والتقدير

أشكر الدكتور باسل الخطيب، المشرف على هذه الرسالة، على توجيهه العلمي وملاحظاته في مراحل البحث كلها. وأشكر الجامعة الافتراضية السورية وبرنامج ماجستير علوم الوب على ما أتاحاه من علم ودعم. وأشكر J. Kuzilek وM. Hlosta وZ. Zdrahal، مؤلفي مجموعة بيانات تحليلات التعلم للجامعة المفتوحة (OULAD)، على إتاحتها للباحثين بترخيص المشاع الإبداعي CC BY 4.0؛ وقد استُعملت في هذه الرسالة مع الإسناد الذي يشترطه الترخيص.

---

## الملخص

يحتاج المتعلم في بيئات التعلم الافتراضية إلى توجيه شخصي بين موارد المقرر الكثيرة، في حين تسجّل المنصة سلوكه دون أن تحوّله إلى توصيات مفيدة. غير أن الوصول إلى الموارد داخل المقرر يقوده إلى حد بعيد الجدول الدراسي والشعبية والإعادات، فلا يُعرف ما الذي يضيفه تحليل السلوك فوق ما يمليه الجدول نفسه، ولا تتضمن الأدبيات المدروسة اختباراً مضبوطاً لذلك على بيانات تعليمية عامة.

تصمّم هذه الرسالة نظام توصية قائماً على تحليل سلوك المستخدم، وتقيّمه تقييماً قابلاً لإعادة الإنتاج على مجموعة بيانات تحليلات التعلم للجامعة المفتوحة (OULAD): تسعة عروض من 2013 للتطوير، وثلاثة عشر عرضاً من 2014 للتأكيد في تشغيل واحد بعد تجميد التصميم. ومُثّل السلوك بسلال الأيام وبعائلة متداخلة من الإشارات الضمنية، وقورن نموذج هجين مدرك للسياق، جُمّد على التطوير من شعبية العنقود والجيران الأقربين على السلال، بعشرة خطوط أساس في مقدمتها الشعبية الآنية، وبشبكة متكررة خفيفة من نوع GRU، وأُرفقت بها نماذج لتجميع المتعلمين والتنبؤ المبكر بالتعثر. واعتمد التقييم تقسيماً زمنياً وترتيباً على الكتالوج الكامل ومهمة رئيسية لاكتشاف الموارد الجديدة بمقياس NDCG@10، مع فاصل bootstrap-t عنقودي وتصحيح هولم وعتبة أثر مسجلة مسبقاً قدرها 0.02. وأُتيحت النتائج عبر واجهة عربية بنمط إعادة التشغيل.

وعلى عروض التأكيد لم يتفوق الهجين السلوكي على الشعبية الآنية في اكتشاف الموارد الجديدة، والحكم غير حاسمة: لا يكشف التصميم بقوة 80% أثراً أصغر من 0.0375. ويستبعد فاصل الثقة، حين تُعامَل العروض وحدات مستقلة، أن تزيد إضافة الهجين فوق الشعبية الآنية على 0.0204 في NDCG@10، أي نحو 3.6% من مستواها، ولا يستبعد إضافة موجبة أصغر من ذلك؛ وعلى مستوى المقررات السبعة يبلغ حده الأعلى 0.043. وأُكّد أن ترجيح الإشارة السلوكية يحسّن WRMF، وحملت الحداثة معظم الأثر وصفاً، واستُبعد تفوق GRU-lite على الجيران على السلال بمقدار 0.02 فأكثر، وجاء أثر ملامح السلوك في التنبؤ بالتعثر موجباً ودالاً على مستوى العروض، وغير دال على مستوى المقررات، ودون العتبة العملية.

وتقدّم الرسالة إسهاماً منهجياً في بروتوكول تقييم مسجّل مسبقاً يمنع تسرب المستقبل، وإسهاماً تجريبياً في قياس مضبوط لما يضيفه التخصيص فوق الجدول الدراسي، وإسهاماً تقنياً في نظام قابل لإعادة الإنتاج بأدوات أساسية.

**الكلمات المفتاحية:** نظم التوصية، تحليل سلوك المستخدم، سجلات تاريخ المستخدم، التغذية الراجعة الضمنية، التصفية التعاونية، التصفية القائمة على المحتوى، التوصية المدركة للسياق، الشبكات العصبونية المتكررة، تحليلات التعلم، OULAD.

---

## Abstract

Learners in virtual learning environments need personal guidance among many course resources, while platforms record their behavior without turning it into recommendations. Yet access within a course is driven largely by the schedule, popularity and repeat visits, so it is unclear what behavior analysis adds beyond the schedule itself, and the reviewed literature lacks a controlled test of this on public educational data.

This thesis designs a behavior-based e-learning recommender and evaluates it reproducibly on the Open University Learning Analytics Dataset (OULAD): nine 2013 presentations for development and thirteen 2014 presentations for confirmation in a single run after the design is frozen. Behavior is modeled as day baskets and nested implicit signals. A context-aware hybrid, frozen on development as cluster popularity plus basket nearest neighbors, is compared with ten baselines led by recent popularity and with a lightweight GRU network, alongside learner clustering and early at-risk prediction. Evaluation uses a temporal split, full-catalog ranking and a primary new-resource task measured by NDCG@10, with clustered bootstrap-t intervals, Holm correction and a pre-registered threshold of 0.02. An Arabic learner and instructor interface serves results in replay mode.

On the confirmation presentations, the behavioral hybrid did not outperform recent popularity in discovering new resources, and the verdict is **inconclusive**: the design cannot detect, with 80% power, an effect smaller than 0.0375. Treating presentations as independent units, the confidence interval rules out a gain above 0.0204 in NDCG@10 (about 3.6% of the recent-popularity level) but not a smaller positive gain; across the seven courses its upper bound is 0.043. Behavior-signal weighting was **confirmed** to improve WRMF, with recency carrying most of the effect descriptively; an advantage of GRU-lite over basket neighbors of 0.02 or more was ruled out (**refuted for superiority**); and the effect of behavioral features on at-risk prediction was positive and significant across presentations, though not across courses, and below the practical threshold (**practically refuted**).

The thesis contributes a pre-registered, leakage-free protocol, a controlled measurement of what personalization adds beyond the schedule, and a reproducible system built with basic tools.

**Keywords:** Recommender systems, User behavior analysis, User history logs, Implicit feedback, Collaborative Filtering (CF), Content-Based Filtering (CBF), Context-Aware Recommendation, Recurrent Neural Network (RNN), Learning analytics, OULAD.

---

## فهرس المحتويات، وفهرس الجداول، وفهرس الأشكال

تُولَّد هذه الفهارس آلياً عند بناء ملف الرسالة النهائي.

---

## قائمة المختصرات

| المختصر | الصيغة الكاملة | المعنى |
|---|---|---|
| ALS | Alternating Least Squares | المربعات الصغرى المتناوبة |
| ARI | Adjusted Rand Index | مؤشر راند المعدَّل |
| AUC | Area Under the Curve | المساحة تحت المنحنى |
| BPR | Bayesian Personalized Ranking | الترتيب الشخصي البايزي |
| BPTT | Backpropagation Through Time | الانتشار العكسي عبر الزمن |
| CART | Classification and Regression Trees | شجرة التصنيف والانحدار |
| CBF | Content-Based Filtering | التصفية القائمة على المحتوى |
| CC BY | Creative Commons Attribution | ترخيص المشاع الإبداعي مع النسبة |
| CF | Collaborative Filtering | التصفية التعاونية |
| CNN | Convolutional Neural Network | الشبكة العصبونية التلافيفية |
| DBI | Davies–Bouldin Index | مؤشر ديفيز–بولدن |
| EASE | Embarrassingly Shallow Autoencoder | النموذج الخطي عنصر-إلى-عنصر بحل مغلق |
| FNR / FPR | False Negative / False Positive Rate | معدل السلب الكاذب / الإيجاب الكاذب |
| GRU | Gated Recurrent Unit | الوحدة المتكررة ذات البوابات |
| HR | Hit Rate | معدل الإصابة |
| HRL | Hierarchical Reinforcement Learning | التعلم المعزّز الهرمي |
| kNN | k-Nearest Neighbors | الجيران الأقربون |
| LMS | Learning Management System | نظام إدارة التعلم |
| LSTM / Bi-LSTM | (Bidirectional) Long Short-Term Memory | الذاكرة الطويلة القصيرة (ثنائية الاتجاه) |
| LTR | Learning-to-Rank | التعلّم بالترتيب |
| MAE / RMSE | Mean Absolute Error / Root Mean Squared Error | متوسط الخطأ المطلق / جذر متوسط مربع الخطأ |
| MAP | Mean Average Precision | متوسط الدقة المتوسطة |
| MDE80 | Minimum Detectable Effect at 80% power | الحد الأدنى للأثر القابل للكشف بقوة 80% |
| MF | Matrix Factorization | تحليل المصفوفات |
| MOOC | Massive Open Online Course | مقرر مفتوح واسع الانتشار عبر الإنترنت |
| MRR | Mean Reciprocal Rank | متوسط مقلوب الرتبة |
| NCF | Neural Collaborative Filtering | التصفية التعاونية العصبونية |
| NDCG | Normalized Discounted Cumulative Gain | الكسب التراكمي المخصوم المطبَّع |
| OULAD | Open University Learning Analytics Dataset | مجموعة بيانات تحليلات التعلم للجامعة المفتوحة |
| RBFNN | Radial Basis Function Neural Network | الشبكة العصبونية بدوال الأساس الشعاعية |
| RL | Reinforcement Learning | التعلم المعزّز |
| RNN | Recurrent Neural Network | الشبكة العصبونية المتكررة |
| ROC | Receiver Operating Characteristic | منحنى خصائص التشغيل |
| SHAP | SHapley Additive exPlanations | تفسير مساهمة الميزات بقيم شابلي |
| SKNN / V-SKNN | Session-based kNN / Vector SKNN | الجيران الأقربون على الجلسات أو السلال (والصيغة المتجهية) |
| SVD | Singular Value Decomposition | التحليل إلى القيم المنفردة |
| SVU | Syrian Virtual University | الجامعة الافتراضية السورية |
| TF-IDF | Term Frequency–Inverse Document Frequency | ترجيح المصطلحات في التمثيل النصي |
| VLE | Virtual Learning Environment | بيئة التعلم الافتراضية |
| WRMF | Weighted Regularized Matrix Factorization | تحليل المصفوفات الموزون للتغذية الضمنية |

---

## قائمة المصطلحات

| المصطلح (EN) | المصطلح (AR) | التعريف المختصر |
|---|---|---|
| Recommender system | نظام التوصية | برنامج يقدّر ملاءمة العناصر لمستخدم ويعرض عليه قائمة مرتبة منها |
| Implicit feedback | التغذية الراجعة الضمنية | تفضيل يُستنتج من أفعال المستخدم، كالزيارة والنقر، لا من تقييم صريح يقدّمه عمداً |
| Collaborative filtering | التصفية التعاونية | توصية من أنماط استهلاك مستخدمين آخرين لا من محتوى العنصر |
| Content-based filtering | التصفية القائمة على المحتوى | مطابقة سمات العنصر مع ملف المستخدم |
| Hybrid recommender | الموصي الهجين | دمج أكثر من أسلوب توصية في درجة واحدة |
| Context-aware recommendation | التوصية المدركة للسياق | توصية تستعمل ظروف لحظة التوصية، كالأسبوع وقرب التقييم، لا ذوق المستخدم وحده |
| Virtual Learning Environment | بيئة التعلم الافتراضية | منصة يصل منها المتعلم إلى مواد المقرر وأنشطته |
| Presentation | عرض المقرر | نسخة زمنية من مقرر تبدأ في شهر محدد، وهي وحدة النموذج ووحدة التحليل الإحصائي |
| Registration | التسجيل | ارتباط طالب بعرض معين، وهو «المتعلم» في هذه الرسالة |
| Activity type | نوع النشاط | تصنيف المورد في بيئة التعلم، كالاختبار القصير والمنتدى والمحتوى |
| Navigational types | الأنواع التنقلية | أنواع حاوية أو معبر تنقل تُستبعد من أهداف التوصية وتبقى ملامح سلوك |
| Catalog | الكتالوج | الموارد غير التنقلية المرشحة للتوصية عند نقطة القطع |
| Day basket | سلة اليوم | مجموعة الموارد غير المرتبة التي زارها المتعلم في يوم واحد |
| Basket-sequence | تسلسل السلال | سلسلة سلال الأيام النشطة مرتبة زمنياً، بديلاً عن الجلسات في بيانات يومية الدقة |
| Nested signal family | العائلة المتداخلة للإشارة | مستويات إشارة ضمنية كل منها حالة خاصة من الذي يليه: ثنائية ⊂ أيام ⊂ حداثة ⊂ شدة |
| Recency decay | اضمحلال الحداثة | خفض وزن الزيارة القديمة أسياً بثابت زمني τ |
| Type-normalized intensity | الشدة المطبَّعة بالنوع | وزن إضافي لنقرات اليوم نسبةً إلى وسيط نقرات نوع المورد |
| Confidence (WRMF) | الثقة | مقدار تمسك نموذج تحليل المصفوفات بخانة ملاحظة، ويساوي $1+\alpha W$ |
| Recent popularity | الشعبية الآنية | عدد المتعلمين المختلفين الذين وصلوا إلى المورد في آخر w يوماً |
| Item-based kNN | التصفية التعاونية بالعناصر | توصية موارد مشابهة لما زاره المتعلم، بتشابه مقلَّص للحالات قليلة المشتركين |
| Session/basket kNN | الجيران الأقربون على السلال | توصية مما زاره أصحاب السلال المشابهة لسلال المتعلم الأخيرة |
| Markov chain | سلسلة ماركوف | احتمال المورد في السلة التالية بشرط موارد السلة الحالية |
| Rank fusion | الدمج الرتبي | جمع رتب مطبَّعة من عدة مكوّنات بأوزان، أساس النموذج الهجين |
| Mid-rank | الرتبة الوسطى | إعطاء المتعادلين متوسط رتبهم بدل ترتيب مخترَع |
| Simplex weights | أوزان على السمبلكس | أوزان غير سالبة مجموعها 1 |
| Acceptance rule | قاعدة القبول | شرط مكتوب سلفاً لدخول مكوّن إلى النموذج الهجين |
| Personalization floor | أرضية الشخصنة | إلزام الهجين بمكوّن شخصي واحد على الأقل |
| Sanity pack | حزمة الصحة | اختبارات إلزامية بمعايير رقمية قبل الوثوق بنتائج النموذج العصبوني |
| Temporal split (rolling origins) | التقسيم الزمني (بنقاط القطع المتدحرجة) | التدريب على الماضي والاختبار على المستقبل عند عدة نقاط قطع |
| Full-catalog ranking | الترتيب على الكتالوج الكامل | ترتيب كل المرشحين لا عيّنة منهم |
| Sampled negatives | السوالب المعيَّنة | ترتيب الهدف بين عيّنة صغيرة عشوائية من العناصر، وهو بروتوكول يضخّم المقاييس |
| Task A / Task B | المهمة A / المهمة B | اكتشاف موارد جديدة لم يزرها المتعلم / أي وصول بما فيه الإعادة |
| NDCG@K | الكسب التراكمي المخصوم المطبَّع عند K | جودة الترتيب مع خصم المواضع المتأخرة، مطبَّعة بالترتيب المثالي |
| Hit rate (HR@K) | معدل الإصابة عند K | هل ظهر هدف واحد على الأقل في أول K عنصراً |
| Coverage@K | التغطية | نسبة الكتالوج التي ظهرت في قوائم التوصية |
| Cold start | البدء البارد | قِصر تاريخ المتعلم إلى حد لا يكفي للشخصنة؛ ويُدرس هنا نسبياً بالربع الأدنى من التاريخ |
| Data leakage | تسرب البيانات | استعمال معلومة لم تكن متاحة لحظة التوصية |
| Ablation | الاستئصال | حذف جزء من النموذج أو الإشارة لقياس مساهمته |
| Clustered bootstrap-t | فاصل bootstrap-t العنقودي | إعادة سحب العروض مع الإرجاع وتعيير كل متوسط بانحرافه لبناء فاصل ثقة |
| Exact sign-flip test | اختبار قلب الإشارات الدقيق | قيمة p من تعداد كل تركيبات قلب إشارات الفروق |
| Holm correction | تصحيح هولم | ضبط قيم p عند اختبار عدة فرضيات معاً |
| Pre-registration | التسجيل المسبق | تثبيت الفرضيات والعتبات وقواعد الحكم قبل رؤية النتائج |
| Practical threshold δ | عتبة الأثر العملي | أصغر فرق يُعدّ ذا قيمة عملية (0.02) |
| MDE80 | الحد الأدنى للأثر القابل للكشف | أصغر أثر حقيقي يُؤكَّد باحتمال لا يقل عن 0.8 تحت قاعدة الحكم |
| At-risk prediction | التنبؤ بالمتعلم المعرّض للخطر | التوقع المبكر للرسوب أو الانسحاب |
| Youden J | مؤشر يودن | عتبة تصنيف تعظّم مجموع الحساسية والنوعية ناقص واحد |
| Fairness analysis | تحليل الإنصاف | مقارنة أداء النظام بين مجموعات سكانية دون إدخال سماتها في النماذج |
| Replay mode | نمط إعادة التشغيل | محاكاة النظام على بيانات تاريخية عند يوم مختار دون استعمال ما بعده |

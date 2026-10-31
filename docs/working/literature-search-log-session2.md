# سجل البحث اللاحق لتدقيق الفجوة (الجدول 2-1-أ)

**الغرض:** شرط الباحث ب-1 في `docs/defense/session2/r3-verdict.md` (القسم 6): حفظ سجل البحث اللاحق في المستودع، وإحالة القسم 2-1 إليه.
**القرار:** D-127، محضر `docs/meetings/2026-10-31-decision-final-phase-b-items.md` (مشرف محاكى بأداة ذكاء اصطناعي، وليس توقيعاً).
**تاريخ هذا الملف:** 2026-10-31.

هذا الملف قسمان منفصلان، ولا يُخلط أحدهما بالآخر:

- **القسم أ: البحث الأصلي (2026-10-27).** يحفظ ما حُفظ منه فقط، وهو ما في الجدول 2-1-أ ونص القسم 2-1. **ولم تُحفظ صفحات النتائج الخام** ولا قائمة النتائج المعروضة نتيجةً نتيجة ولا قرار كل نتيجة منفردة، ولا تُستعاد، ولا يحاول هذا الملف إعادة بنائها.
- **القسم ب: إعادة تشغيل لاحقة (2026-10-31).** السلاسل الخمس عشرة نفسها بالأداة نفسها، بعد أربعة أيام. **وهي ليست البحث الأصلي**، وقد تختلف نتائجها عنه لأن فهرس المحرك وترتيبه يتغيران. وتُحفظ هنا لأنها أقرب دليل متاح على ما طلبته اللجنة («صفحات النتائج المعروضة وقرار كل نتيجة»)، وفحصاً لثبات قرارات الجدول. ولا تغيّر الجدول 2-1-أ ولا ادعاءً في الرسالة.

أرقام المراجع بين أقواس معقوفة هي أرقام قائمة الرسالة الحالية (`docs/working/06-thesis/references.md`) في تاريخ هذا الملف.

---

## القسم أ: البحث الأصلي، 2026-10-27 (ما حُفظ منه)

### أ-1 الظروف كما سُجلت في 2-1

- **التاريخ:** 2026-10-27، بعد كتابة الفصل الثاني وبعد المناقشة التجريبية الأولى.
- **الغرض:** تدقيق الفجوتين الأولى والثانية. ولم يُستعمل في انتقاء المراجع الثمانية والثلاثين المحللة.
- **الأداة:** أداة البحث في الوب المتاحة في بيئة العمل وحدها. تعرض لكل سلسلة نحو عشر نتائج مع مقتطفاتها، ولا تعرض العدد الكلي للنتائج.
- **قصر النطاق:** في السلسلتين 3 و14 على نطاقات ناشرين، وهو قصر لنتائج محرك عام، وليس بحثاً داخل ACM DL أو IEEE Xplore.
- **ما لم يُستعمل:** Google Scholar وScopus. وحجبت شبكة الجلسة Crossref وOpenAlex وSemantic Scholar وdblp وdoi.org، فتُحقّق من المعرّفات من صفحات الناشرين أو من فهارس مؤسسية ظهرت في النتائج.
- **المفحوص:** العنوان والمقتطف لكل نتيجة معروضة. وما احتاج تحققاً فُتحت له سلسلة تحقق مستقلة لا تُحسب في الجدول. وهذه السلاسل لم تُسجَّل نصوصها.
- **الأثر في المستودع:** أضيف الجدول ونصه في الـcommit `66dfc09` (2026-10-27). ثم أعاد `renumber.py` ترقيم المراجع الأربعة المدخلة: [71]→[50]، و[74]→[51]، و[73]→[52]، و[72]→[53]. وأضاف `scripts/thesis/defense2_round3_fixes.py` جملة «ولم تُحفظ صفحات النتائج الخام في المستودع…». ولم يتغير شيء آخر في الجدول.

### أ-2 معايير الإدخال والاستبعاد (منقولة من 2-1)

- **الإدخال:**
  1. عمل منشور بعد تحكيم: مجلة، أو مؤتمر، أو فصل في كتاب.
  2. يتناول مباشرة أحد هذه الموضوعات: مسح للتوصية التعليمية؛ مسح للتوصية بالجلسة أو بالسلة التالية؛ البعد الزمني في التقييم (التقسيم الزمني أو الشعبية الزمنية)؛ فصل العناصر الجديدة عن المكررة؛ التوصية على OULAD.
  3. تُتحقق بياناته ومعرّفه من صفحة الناشر أو من فهرس.
- **الاستبعاد:**
  1. المسودات غير المنشورة (arXiv)، والرسائل الجامعية، ووثائق البرمجيات، ومواقع التلخيص.
  2. المكرر، أو الموجود في القائمة.
  3. العمل الذي يؤدي دوره في الفصل مرجع مُدخل آخر.
  4. أعمال التوصية التي لا تقيس إلا بمقاييس تصنيفية.

### أ-3 السلاسل والأعداد والقرار المسجل لكل سلسلة (منقولة حرفياً من الجدول 2-1-أ)

| # | سلسلة البحث كما أُدخلت | قصر النطاق | المعروضة | المفحوصة | المُدخلة | القرار المسجل (ما وُجد) |
|---|---|---|---|---|---|---|
| 1 | survey educational recommender systems DOI | — | 10 | 10 | 1 | مراجعة منهجية للتوصية التعليمية [50]، ومسوح أضيق موضوعاً |
| 2 | e-learning recommender system learner behavior logs survey | — | 10 | 10 | 0 | مراجعات عن مصادر بيانات ملف المتعلم؛ لا تقييم بالترتيب |
| 3 | educational recommender systems survey | dl.acm.org، ieeexplore.ieee.org، link.springer.com | 10 | 10 | 0 | مسوح يؤدي [50] دورها، ومسح للتوصية التعليمية القابلة للتفسير |
| 4 | learning resource recommendation within course implicit feedback clickstream | — | 10 | 10 | 0 | تنميط بنقرات الفيديو وBPR على مقررات؛ لا استئصال للترجيح |
| 5 | educational recommender implicit feedback weighting recency decay versus binary ablation MOOC | — | 10 | 10 | 0 | لم يظهر عمل يقارن الإشارة الموزونة بالثنائية في نموذج واحد |
| 6 | learning resource recommendation repeat consumption new items popularity baseline e-learning temporal split | — | 10 | 10 | 1 | تقسيم زمني لتقييم التوصية في المقررات المغلقة [51]؛ وأعمال في إعادة الاستهلاك خارج التعليم |
| 7 | "A Task-Centric Perspective on Recommendation Systems" repeat consumption popularity reference time | — | 10 | 10 | 1 | الشعبية المحسوبة عند لحظة التفاعل [52]؛ والورقة المبحوث عنها مسودة arXiv فاستُبعدت |
| 8 | time-aware popularity baseline recommender evaluation global timeline recent popularity | — | 10 | 10 | 0 | أعمال في الخط الزمني العام وتسرب البيانات؛ [52] مكرر |
| 9 | next-basket recommendation repeat versus explore items survey | — | 10 | 10 | 0 | [18] الموجود في القائمة؛ لا مسح مخصص |
| 10 | "next basket recommendation" survey | — | 18 | 18 | 0 | تقييمات تجريبية لطرائق السلة التالية بدور [18]؛ لا مسح مخصص |
| 11 | session-based recommendation evaluation baselines empirical comparison | — | 10 | 10 | 0 | مقارنات تؤكد منافسة الجيران للطرائق العصبونية، بدور [16]، [17] |
| 12 | session-based recommender systems survey | — | 10 | 10 | 1 | مسح التوصية بالجلسة [53] |
| 13 | OULAD recommendation learning resources recommender system Open University Learning Analytics Dataset | — | 10 | 10 | 0 | أعمال على OULAD بمقاييس تصنيفية أو غير محكَّمة |
| 14 | OULAD recommender system learning resources | ieeexplore.ieee.org، dl.acm.org، link.springer.com، sciencedirect.com، mdpi.com | 10 | 10 | 0 | توصية مقررات على OULAD بمقاييس F1 وAUC؛ لا فصل للجديد عن المكرر |
| 15 | TIFU-KNN "Modeling personalized item frequency information for next-basket recommendation" educational OR MOOC OR "learning resources" | — | 10 | 10 | 0 | لم يظهر تطبيق لـTIFU-KNN في التعليم |
| | **المجموع** | | **158** | **158** | **4** | |

### أ-4 النتائج المدخلة (القرار: أُدخلت)

| السلسلة | المرجع في الرسالة |
|---|---|
| 1 | [50] M. C. Urdaneta-Ponte, A. Mendez-Zorrilla, and I. Oleagordia-Ruiz, "Recommendation systems for education: Systematic review," *Electronics*, vol. 10, no. 14, Art. no. 1611, 2021, doi: 10.3390/electronics10141611. |
| 6 | [51] C. Krauss, A. Merceron, and S. Arbanowski, "The timeliness deviation: A novel approach to evaluate educational recommender systems for closed-courses," *Proc. LAK*, 2019, pp. 195–204, doi: 10.1145/3303772.3303774. |
| 7 | [52] Y. Ji, A. Sun, J. Zhang, and C. Li, "A re-visit of the popularity baseline in recommender systems," *Proc. SIGIR*, 2020, pp. 1749–1752, doi: 10.1145/3397271.3401233. |
| 12 | [53] S. Wang, L. Cao, Y. Wang, Q. Z. Sheng, M. A. Orgun, and D. Lian, "A survey on session-based recommender systems," *ACM Computing Surveys*, vol. 54, no. 7, Art. no. 154, 2022, doi: 10.1145/3465401. |

### أ-5 قرارات الاستبعاد المسجلة

سُجّل الاستبعاد مجمَّعاً لكل سلسلة، في عمود «ما وُجد» أعلاه. والنتيجتان الوحيدتان المسمّاتان في السجل:

- **السلسلة 7:** A. Sun، «A Task-Centric Perspective on Recommendation Systems»، استُبعدت لأنها مسودة arXiv (الاستبعاد 1).
- **السلسلة 8:** [52] ظهر مرة ثانية، فاستُبعد مكرراً (الاستبعاد 2).

وما سوى ذلك لم يُسجَّل باسمه. فلا يعرف المستودع عناوين النتائج المئة والأربع والخمسين الأخرى ولا سبب استبعاد كل منها.

### أ-6 ما لم يُحفظ ولا يُستعاد

- صفحات النتائج الخام للسلاسل الخمس عشرة.
- قائمة النتائج المعروضة نتيجةً نتيجة (العنوان والرابط والمقتطف).
- قرار كل نتيجة منفردة، إلا النتيجتين في أ-5 والمدخلات الأربع.
- نصوص سلاسل التحقق المستقلة ونتائجها.

---

## القسم ب: إعادة تشغيل لاحقة، 2026-10-31 (ليست البحث الأصلي)

### ب-1 الظروف

- **التاريخ:** 2026-10-31. **المنفّذ:** الفريق، بأداة البحث في الوب في بيئة العمل (WebSearch، النمط القياسي `standard`).
- **السلاسل:** الخمس عشرة نفسها حرفياً، وبقصر النطاق نفسه في السلسلتين 3 و14 (الخيار `allowed_domains`).
- **ما تعيده الأداة:** قائمة روابط (العنوان كما يعيده المحرك، والرابط)، ومعها ملخص نصي تولّده الأداة. وهذا الملخص ليس دليلاً، فلا يُنقل هنا. وتُستعمل منه المعلومة الببليوغرافية وحدها حين لا يكفي العنوان لتعيين العمل، مع وسمها «من مقتطف الأداة، لم يُتحقق».
- **المفحوص:** العنوان والمقتطف كما في البحث الأصلي. ولم يُفتح نص كامل.
- **التحقق:** ثلاث سلاسل تحقق مستقلة (ب-4)، لا تُحسب في الأعداد.
- **رموز القرار** (من معايير أ-2):
  - **م** مُدخل في القائمة سابقاً، أو نسخة منه.
  - **س1** مسودة أو رسالة أو وثيقة برمجية أو موقع تلخيص أو صفحة غير منشورة.
  - **س2** مكرر داخل السلسلة.
  - **س3** يؤدي دوره مرجع مُدخل (يُسمّى).
  - **س4** خارج موضوعات الإدخال، أو لا يقيس بالترتيب.
  - **ف** مرشح للفحص: قد يستوفي الإدخال ويمس فجوة. يُرفع إلى الطالب والمشرف الفعلي (القرار D-127)، ولا يُضاف إلى الرسالة في هذه المرحلة.

### ب-2 النتائج وقرار كل نتيجة

**السلسلة 1** (10 نتائج)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | Recommendation systems for education: systematic review | https://deustoteka.deusto.es/items/088cf812-4201-4655-b262-057feb83c55c/full | م: [50] |
| 2 | Recommender Systems in Education: Systematic Mapping | https://dspace.mackenzie.br/handle/10899/34738 | س3: [50] (خريطة منهجية، LACLO 2021، من مقتطف الأداة) |
| 3 | Recommendation systems for education: systematic review | https://deustoteka.deusto.es/items/088cf812-4201-4655-b262-057feb83c55c | م: [50] |
| 4 | Recommendation systems for education: Systematic review | https://research.science.eus/documentos/63265424d50fae52cd317b80?lang=en | م: [50] |
| 5 | Recommender Systems in Education: Systematic Mapping | https://dspace.mackenzie.br/items/06901dcb-1d45-4355-9703-d4774c05ea64/full | س2 |
| 6 | Recommendation systems for education: Systematic review | https://research.science.eus/documentos/63265424d50fae52cd317b80 | م: [50] |
| 7 | Machine Learning and Knowledge Extraction (Jun 2023) | https://doaj.org/article/56938fd9a1e94900a881111dd72d83e8 | س3: [50] (مراجعة لتوصية المقررات، من مقتطف الأداة) |
| 8 | IDEAS home Printed from https://ideas.repec.org/a/taf/tbitxx/v35y2016i4p290-297.html | https://ideas.repec.org/a/taf/tbitxx/v35y2016i4p290-297.html | س3: [50] (مسح، Behaviour & IT 2016، من مقتطف الأداة) |
| 9 | Academic Journal | https://discovery-imamu.kwaretech.com/EdsRecord/edsbas,edsbas.18C8E4C1 | س4: لا عنوان ولا مقتطف يعيّن العمل |
| 10 | IEEE Access (Jan 2023) | https://doaj.org/article/dae6a9473274470ab5f17aecdd061f07 | س3: [50] (مراجعة أضيق، أنماط التعلم، من مقتطف الأداة) |

**السلسلة 2** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | jatit.org | https://jatit.org/volumes/Vol103No7/27Vol103No7.pdf | س3: [50] (مسح عام) |
| 2 | Recommender systems in e-learning environments: a survey of the state-of-the-art and possible extensions | https://datalearner.com:8443/academic/journal-papers/0269-2821/volumes-and-issues/320/paper-detail/2736 | س3: [50] (مسح، صفحة مجمِّع) |
| 3 | International Review of Research in Open and Distributed Learning (Mar 2024) | https://doaj.org/article/bf7e489d263742c8866e7621e04ce8b6 | س4: مصادر بيانات ملف المتعلم، لا تقييم بالترتيب |
| 4 | International Review of Research in Open and Distributed Learning | https://www.irrodl.org/index.php/irrodl/article/download/7419/6000?inline=1 | س2 |
| 5 | International Review of Research in Open and Distributed Learning | https://www.irrodl.org/index.php/irrodl/article/download/7419/6000 | س2 |
| 6 | scite.ai | https://scite.ai/reports/W8Rx6aQ | س1 |
| 7 | the research trends in recommender systems for e learning a syste | https://scholars.hkmu.edu.hk/en/publications/the-research-trends-in-recommender-systems-for-e-learning-a-syste/ | س3: [50] |
| 8 | preprints.org | https://Preprints.org/manuscript/202312.1672/v2 | س1 |
| 9 | A systematic review: machine learning based recommendation systems for e-learning | https://scholarhub.vn/publication/A-systematic-review-machine-learning-based-recommendation-systems-for-e-learning/35c24018-6f90-4901-8419-1d12eafd2c46 | س3: [50] |
| 10 | drupal.ijimai.org | https://drupal.ijimai.org/journal/node/675 | س4: لا عنوان يعيّن العمل |

**السلسلة 3** (10، مقصورة على dl.acm.org وieeexplore.ieee.org وlink.springer.com)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | A systematic literature review on educational recommender systems for teaching and learning: research trends, limitations and opportunities | https://dl.acm.org/doi/10.1007/s10639-022-11341-9 | س3: [50] |
| 2 | A Survey of Semantic Web Based Recommender Systems for E-Learning | https://link.springer.com/chapter/10.1007/978-3-031-37105-9_33 | س3: [50] (أضيق) |
| 3 | Recommender Systems for Good (RS4Good): Survey of Use Cases and a Call to Action for Research that Matters | https://arxiv.org/pdf/2411.16645 | س1 (خارج النطاق المقصور أيضاً) |
| 4 | Tutorial: Educational Recommender Systems | https://link.springer.com/chapter/10.1007/978-3-031-36336-8_7 | س4: درس تعليمي لا مسح |
| 5 | Educational recommender systems and their application in lifelong learning | https://dl.acm.org/doi/abs/10.1080/0144929X.2015.1128977 | س3: [50] |
| 6 | A Survey of Learner and Researcher Related Challenges in E-learning Recommender Systems | https://link.springer.com/chapter/10.1007/978-3-319-62743-4_11 | س3: [50] |
| 7 | Learning Outcomes, Assessment, and Evaluation in Educational Recommender Systems: A Systematic Review | https://arxiv.org/pdf/2407.09500 | س1 |
| 8 | Recommender System in eLearning: A Survey | https://link.springer.com/chapter/10.1007/978-981-15-0790-8_13 | س3: [50] |
| 9 | An Outcome-Based Educational Recommender System | https://arxiv.org/pdf/2509.18186 | س1 |
| 10 | A Survey on Explainable Course Recommendation Systems | https://link.springer.com/chapter/10.1007/978-3-031-60012-8_17 | س3: [50] (التوصية القابلة للتفسير، كما في الأصل) |

**السلسلة 4** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | TrueLearn: A Python Library for Personalised Informational Recommendations with (Implicit) Feedback | https://arxiv.org/pdf/2309.11527 | س1 |
| 2 | Modeling Balanced Explicit and Implicit Relations with Contrastive Learning for Knowledge Concept Recommendation in MOOCs | https://arxiv.org/pdf/2402.08256 | س1 |
| 3 | User Profiling in a SPOC: A method based on User Video Clickstream Analysis | https://unpaywall.org/10.3991%2FIJET.V14I01.9091 | س4: تنميط بنقرات الفيديو، لا تقييم بالترتيب |
| 4 | a learning resource recommendation algorithm based on online lear | https://pure.ecnu.edu.cn/en/publications/a-learning-resource-recommendation-algorithm-based-on-online-lear/ | س4: لا استئصال للترجيح في المقتطف |
| 5 | Using Clickstream to Understand Learning Paths and the Network Structure of Learning Resources: Using MOOC as an Example | https://library.apsce.net/index.php/ICCE/article/view/329 | س4: تحليل مسارات، لا توصية |
| 6 | paper 138 | https://v0.apsce.net/icce/icce2019/proceedings/paper_138.pdf | س2 (النص نفسه من وقائع ICCE 2019) |
| 7 | IDEAS home Printed from https://ideas.repec.org/a/igg/jhcitp/v8y2017i4p38-49.html | https://ideas.repec.org/a/igg/jhcitp/v8y2017i4p38-49.html | س4: لا عنوان يعيّن العمل |
| 8 | ethicalresearchdescription learnerparticipation | https://edge.edx.org/asset-v1:TokyoTechX+2020TT-ethics+2020Q1+type@asset+block/ethicalresearchdescription-learnerparticipation.pdf | س1 |
| 9 | ir.lib.ugm.ac.id | https://ir.lib.ugm.ac.id/id/eprint/12610/ | س4: BPR وCLiMF على مقررات، لا استئصال للترجيح (كما في الأصل) |
| 10 | Next Article in Journal | https://www.mdpi.com/2076-3417/13/19/10933/xml | س4: رسم معرفي مع ترشيح تعاوني، لا استئصال للترجيح |

**السلسلة 5** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | MOOCRep: A Unified Pre-trained Embedding of MOOC Entities | https://arxiv.org/pdf/2107.05154 | س1 |
| 2 | kuleuven.be | https://lirias.kuleuven.be/retrieve/714779 | **ف**: BPR مع زمن الانسحاب في توصية المقررات المفتوحة (ب-4) |
| 3 | Document Type : scientific-research | https://www.doi.org/10.30473/idej.2022.63928.1106 | س4: خلفية عن التغذية الضمنية، لا مقارنة |
| 4 | Papers by Iranian Distance Education | https://independent.academia.edu/IranianDistanceEducation | س1 |
| 5 | In collaboration with Payame Noor University and Iranian Electronic Learning Association | https://idej.journals.pnu.ac.ir/article_8801.html | س2 (العمل نفسه في #3) |
| 6 | ir.lib.ugm.ac.id | https://ir.lib.ugm.ac.id/id/eprint/12610/ | س4 (كما في السلسلة 4) |
| 7 | top n personalized recommendation with graph neural networks in m | https://scholars.hkmu.edu.hk/en/publications/top-n-personalized-recommendation-with-graph-neural-networks-in-m/ | س4: يذكر الحداثة دافعاً، ولا مقارنة موزونة بثنائية في المقتطف |
| 8 | Bài báo: “H-BERT4Rec: Enhancing Sequential Recommendation System on MOOCs based on Heterogeneous Information Networks” | https://www.uit.edu.vn/bai-viet/chuc-mung-sinh-vien-nguyen-hoang-long-co-bai-bao-duoc-chap-nhan-dang-tai-tap-chi-quoc-te-ieee-access-xep-hang-q1 | س1 (خبر جامعي) |
| 9 | Attentional Autoencoder for Course Recommendation in MOOC with Course Relevance | https://cs.paperswithcode.com/paper/attentional-autoencoder-for-course | س1 (موقع تلخيص) |
| 10 | www.imec-publications.be | https://www.imec-publications.be/entities/publication/dabfda95-013c-4743-9b1c-813a38316763/full | س4: لا عنوان يعيّن العمل |

**السلسلة 6** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | A Task-Centric Perspective on Recommendation Systems | https://arxiv.org/pdf/2503.21188 | س1 (كما في الأصل) |
| 2 | Recommendation system using improved neural network | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10635973 | س1 (براءة اختراع) |
| 3 | publica.fraunhofer.de | https://publica.fraunhofer.de/handle/publica/404136 | س3: [51] (تقسيم زمني لتقييم التوصية في المقررات المغلقة؛ يرجَّح أنه سجل [51] أو عمل للمجموعة نفسها، لم يُتحقق) |
| 4 | datalab-old.csd.auth.gr | https://datalab-old.csd.auth.gr/wp-content/uploads/publications/WWW2015rn.pdf | س4: إعادة الاستهلاك خارج التعليم |
| 5 | Année : 2008 | https://ceci.loria.fr/article/42 | س4: لا عنوان يعيّن العمل |
| 6 | Advances in Multimedia (Jan 2022) | https://doaj.org/article/ff02714f5eb64f2ca6ca9fc0f65cc508 | س4 بعد التحقق (ب-4): الحداثة والشعبية في ترشيح تعاوني لموارد تعليمية، بلا فصل للجديد عن المكرر في المقتطف |
| 7 | www.arxiv.org | https://www.arxiv.org/pdf/2602.19339 | س1 |
| 8 | repeat consumption www2014 slides | https://www.cs.toronto.edu/~ashton/slides/repeat-consumption-www2014-slides.pdf | س1 (شرائح) |
| 9 | E-learning material Recommender System Using Learner Interest Modeling | https://etd.aau.edu.et/items/f4bfd8af-8ef6-429a-9dea-baa8bd83ee39/full | س1 (رسالة جامعية) |
| 10 | Recommend the Most Popular Learning | https://docs.oracle.com/en/cloud/saas/talent-management/24c/faiml/recommend-the-most-popular-learning.html | س1 (وثيقة برمجية) |

**السلسلة 7** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | A Task-Centric Perspective on Recommendation Systems | https://arxiv.org/pdf/2503.21188 | س1 (كما في الأصل) |
| 2 | A Task-Centric Perspective on Recommendation Systems | https://arxiv.org/html/2503.21188v3 | س2 |
| 3 | arxiv.org | https://arxiv.org/abs/2503.21188v3 | س2 |
| 4 | arxiv.org | https://arxiv.org/abs/2005.13829 | م: [52] (نسخة arXiv) |
| 5 | arxiv.org | https://arxiv.org/abs/2503.21188v1 | س2 |
| 6 | arxiv.org | https://arxiv.org/pdf/2503.21188v2 | س2 |
| 7 | dr.ntu.edu.sg | https://dr.ntu.edu.sg/server/api/core/bitstreams/ab483e99-12a9-4491-867b-79e787971177/content | س4: لا عنوان يعيّن العمل |
| 8 | arxiv.org | https://arxiv.org/pdf/2005.13829 | م: [52] |
| 9 | A Re-visit of the Popularity Baseline in Recommender Systems | https://cs.paperswithcode.com/paper/a-re-visit-of-the-popularity-baseline-in | م: [52] |
| 10 | Our new X account is live! Follow @wizwand_team for updates | https://www.wizwand.com/paper/68fa67b01e209131cea17d2f | س1 |

**السلسلة 8** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | Take a Fresh Look at Recommender Systems from an Evaluation Standpoint | https://arxiv.org/pdf/2210.04149 | س3: [52] (الخط الزمني العام والشعبية؛ الرابط مسودة arXiv) |
| 2 | Temporal Popularity-Based Recommender Systems for e-Commerce: A | https://scitepress.org/publishedPapers/2025/142869/pdf/index.html | س3: [52] (خارج التعليم) |
| 3 | From Counter-intuitive Observations to a Fresh Look at Recommender System | https://deepai.org/publication/from-counter-intuitive-observations-to-a-fresh-look-at-recommender-system | س1 |
| 4 | arxiv.org | https://arxiv.org/abs/2210.04149v1 | س2 |
| 5 | core.ac.uk | https://core.ac.uk/works/52221208 | س4: لا عنوان يعيّن العمل |
| 6 | arxiv.org | https://arxiv.org/abs/1807.04204v2 | س1 |
| 7 | Local Popularity and Time in top-N Recommendation | https://sisinflab.poliba.it/publications/local-popularity-and-time-in-top-n-recommendation/ | س3: [52] (شعبية زمنية خارج التعليم) |
| 8 | ricerca.uniba.it | https://ricerca.uniba.it/handle/11586/401546 | س2 (العمل نفسه في #7) |
| 9 | A Re-visit of the Popularity Baseline in Recommender Systems | https://ar5iv.labs.arxiv.org/html/2005.13829 | م: [52] (مكرر كما في الأصل) |
| 10 | Local Popularity and Time in top-N Recommendation | https://sotaverified.org/papers/time-and-local-popularity-in-top-n | س1 |

**السلسلة 9** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | A Next Basket Recommendation Reality Check | https://arxiv.org/pdf/2109.14233 | م: [18] |
| 2 | Information Discovery in e-Commerce | https://arxiv.org/pdf/2410.05763 | س1 |
| 3 | A Next Basket Recommendation Reality Check | https://paperswithcode.com/paper/a-next-basket-recommendation-reality-check | م: [18] |
| 4 | Computer Science > Information Retrieval | https://web3.arxiv.org/abs/2109.14233 | م: [18] |
| 5 | We are proud to have the following paper accepted by a team of IRLab-ers by ACM Transactions on Information Systems: | https://irlab.science.uva.nl/?p=1393 | م: [18] (خبر قبول) |
| 6 | A Next Basket Recommendation Reality Check | https://deepai.org/publication/a-next-basket-recommendation-reality-check | م: [18] |
| 7 | We are proud to have the following paper accepted by a team of IRLab-ers by ACM Transactions on Information Systems: | https://irlab.science.uva.nl/2023/03/06/paper-accepted-by-acm-transactions-on-information-systems/ | م: [18] |
| 8 | A Next Basket Recommendation Reality Check | https://ar5iv.labs.arxiv.org/html/2109.14233 | م: [18] |
| 9 | Are We Really Achieving Better Beyond-Accuracy Performance | https://arxiv.org/html/2405.01143v1 | س3: [18] (الرابط مسودة arXiv) |
| 10 | [Literature Review] Are We Really Achieving Better Beyond-Accuracy Performance in Next Basket Recommendation? | https://themoonlight.io/review/are-we-really-achieving-better-beyond-accuracy-performance-in-next-basket-recommendation | س1 (موقع تلخيص) |

**السلسلة 10** (18)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | a systematical evaluation for next basket recommendation algorith | https://researchers.mq.edu.au/en/publications/a-systematical-evaluation-for-next-basket-recommendation-algorith/ | س3: [18] (تقييم تجريبي لا مسح) |
| 2 | A Systematical Evaluation for Next-Basket Recommendation Algorithms | https://deepai.org/publication/a-systematical-evaluation-for-next-basket-recommendation-algorithms | س2 |
| 3 | A Systematical Evaluation for Next-Basket Recommendation Algorithms | https://astro.paperswithcode.com/paper/a-systematical-evaluation-for-next-basket | س2 |
| 4 | References & Citations | https://export.arxiv.org/abs/2209.02892 | س2 |
| 5 | A Systematical Evaluation for Next-Basket Recommendation Algorithms | https://arxiv.org/html/2209.02892v2 | س2 |
| 6 | We gratefully acknowledge support from | https://export.arxiv.org/abs/2312.02550 | س1 |
| 7 | A Systematical Evaluation for Next-Basket Recommendation Algorithms | https://opus.lib.uts.edu.au/handle/10453/168780 | س2 |
| 8 | An empirical study of next-basket recommendations | https://astro.paperswithcode.com/paper/an-empirical-study-of-next-basket | س1 |
| 9 | export.arxiv.org | https://export.arxiv.org/pdf/2312.02550 | س2 |
| 10 | We are proud to have the following paper accepted by a team of IRLab-ers by ACM Transactions on Information Systems: | https://irlab.science.uva.nl/?p=1393 | م: [18] |
| 11 | A Next Basket Recommendation Reality Check | https://paperswithcode.com/paper/a-next-basket-recommendation-reality-check | م: [18] |
| 12 | Computer Science > Information Retrieval | https://web3.arxiv.org/abs/2109.14233 | م: [18] |
| 13 | License: arXiv.org perpetual non-exclusive license | https://arxiv.org/html/2312.02550v1 | س2 |
| 14 | Next-basket recommendation | https://PapersWithCode.com/task/next-basket-recommendation | س1 |
| 15 | web3.arxiv.org | https://web3.arxiv.org/pdf/2109.14233 | م: [18] |
| 16 | Publication Type | https://ink.library.smu.edu.sg/sis_research/7900 | س4: لا عنوان يعيّن العمل |
| 17 | This free survey is powered by QUESTIONPRO.COM | https://www.questionpro.com/a/q/mkw-gift-baskets-249048 | س4: استبيان تجاري لا صلة له |
| 18 | li 2023 next | https://irlab.science.uva.nl/wp-content/papercite-data/pdf/li-2023-next.pdf | م: [18] |

**السلسلة 11** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | Comprehensive Empirical Evaluation of Deep Learning Approaches for Session-Based Recommendation in E-Commerce | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9689569/ | س3: [16]، [17] |
| 2 | Performance Comparison of Session-based Recommendation Algorithms based on GNNs | https://physics.paperswithcode.com/paper/performance-comparison-of-session-based | س1 |
| 3 | arxiv.org | https://arxiv.org/abs/2312.16695?context=cs | س3: [16]، [17] (الرابط مسودة arXiv لورقة ECIR 2024 بحسب مقتطف الأداة) |
| 4 | Computer Science > Information Retrieval | https://web3.arxiv.org/abs/2312.16695v2 | س2 |
| 5 | Conference RecSys 2019 sessions | https://iris.unito.it/bitstream/2318/1712206/2/Conference_RecSys_2019_sessions.pdf | س3: [16]، [17] |
| 6 | Conference ECIR 2024 | https://web-ainf.aau.at/pub/jannach/files/Conference_ECIR_2024.pdf | س2 (العمل نفسه في #3) |
| 7 | catalyzex.com | https://catalyzex.com/author/Sara%20Latifi | س1 |
| 8 | web3.arxiv.org | https://web3.arxiv.org/pdf/2312.16695v2 | س2 |
| 9 | Evaluation of Session-based Recommendation Algorithms | https://cs.paperswithcode.com/paper/evaluation-of-session-based-recommendation | م: [17] |
| 10 | Session-aware Recommendation: A Surprising Quest for the State-of-the-art | https://ar5iv.labs.arxiv.org/html/2011.03424 | س3: [16]، [17] |

**السلسلة 12** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | A Survey on Session-based Recommender Systems | https://arxiv.org/pdf/1902.04864 | م: [53] |
| 2 | Graph and Sequential Neural Networks in Session-based Recommendation: A Survey | https://arxiv.org/pdf/2408.14851 | س1 |
| 3 | A Survey on Session-based Recommender Systems | https://api.deepai.org/publication/a-survey-on-session-based-recommender-systems | م: [53] |
| 4 | A Survey on Session-based Recommender Systems | https://paperswithcode.com/paper/a-survey-on-session-based-recommender-systems | م: [53] |
| 5 | A Survey on Session-based Recommender Systems | https://deepai.org/publication/a-survey-on-session-based-recommender-systems | م: [53] |
| 6 | A Survey on Session-based Recommender Systems | https://opus.lib.uts.edu.au/handle/10453/168894 | م: [53] |
| 7 | A Survey on Session-Based Recommendation | https://cse.hkust.edu.hk/pg/defenses/S26/wtanae-23-04-2026.html | س1 (ملخص امتحان دكتوراه) |
| 8 | A Survey on Session-Based Recommendation | https://cse.hkust.edu.hk/pg/defenses/F25/hsuag-06-10-2025.html | س1 |
| 9 | A Survey on Session-based Recommender Systems | https://cdnjs.deepai.org/publication/a-survey-on-session-based-recommender-systems | م: [53] |
| 10 | arxiv.org | https://arxiv.org/pdf/1902.04864v2 | م: [53] |

**السلسلة 13** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | packages.oit.ncsu.edu | https://packages.oit.ncsu.edu/cran/web/packages/ouladFormat/refman/ouladFormat.html | س1 (وثيقة برمجية) |
| 2 | erised.las.iastate.edu | https://erised.las.iastate.edu/CRAN/web/packages/ouladFormat/refman/ouladFormat.html | س1 |
| 3 | archive.linux.duke.edu | https://archive.linux.duke.edu/cran/web/packages/ouladFormat/refman/ouladFormat.html | س1 |
| 4 | cran.nics.utk.edu | https://cran.nics.utk.edu/cran/web/packages/ouladFormat/refman/ouladFormat.html | س1 |
| 5 | تحسين نظام توصية التعلم الالكتروني باستخدام التعلم العميق | https://repository.neelain.edu.sd/items/fd3bb713-2032-4ec8-8c4a-df5e8e3799c5 | س1 (رسالة جامعية؛ دقة تصنيفية بحسب مقتطف الأداة) |
| 6 | ftp.fau.de | https://ftp.fau.de/cran/web/packages/ouladFormat/refman/ouladFormat.html | س1 |
| 7 | open university learning analytics dataset | https://people.ciirc.cvut.cz/~kuziljak/publication/open_university_learning_analytics_dataset | م: [3] (ورقة البيانات) |
| 8 | pmc.ncbi.nlm.nih.gov | https://pmc.ncbi.nlm.nih.gov/articles/PMC5704676 | م: [3] |
| 9 | Open University Learning Analytics dataset | https://analyse.kmi.open.ac.uk/open-dataset | م: [3] (صفحة البيانات) |
| 10 | archive.ics.uci.edu | https://archive.ics.uci.edu/ml/datasets/Open+University+Learning+Analytics+Dataset | س1 (مستودع بيانات) |

**السلسلة 14** (9، مقصورة على ieeexplore.ieee.org وdl.acm.org وlink.springer.com وsciencedirect.com وmdpi.com)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | Unsupervised Deep Collaborative Filtering Recommender System for E-Learning Platforms | https://link.springer.com/chapter/10.1007/978-3-030-45183-7_11 | **ف** (منخفض): توصية على OULAD، ومقاييسها غير معروفة (ب-4) |
| 2 | Systematic Literature Review for the Use of AI Based Techniques in Adaptive Learning Management Systems | https://dl.acm.org/doi/fullHtml/10.1145/3593663.3593681 | س3: [50] (مراجعة؛ تذكر عملاً على OULAD بقواعد ارتباط) |
| 3 | AFEL-REC: A Recommender System for Providing Learning Resource Recommendations in Social Learning Environments | https://arxiv.org/pdf/1808.04603 | س1 (ولا يذكر OULAD) |
| 4 | Recommender Systems for Good (RS4Good): Survey of Use Cases and a Call to Action for Research that Matters | https://arxiv.org/pdf/2411.16645 | س1 |
| 5 | A recommender system of open educational resources based on the purpose of learning | https://ieeexplore.ieee.org/document/8120899/ | س4: لا يستعمل OULAD بحسب المقتطف |
| 6 | A recommender system for educational resources in specific learning contexts | https://ieeexplore.ieee.org/abstract/document/6553940/ | س4: لا يستعمل OULAD بحسب المقتطف |
| 7 | Recommender Systems in Health Professions Education: Protocol for a Scoping Review | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12411800/ | س1 (بروتوكول؛ وخارج النطاق المقصور) |
| 8 | Mobile Multimedia Recommendation in Smart Communities: A Survey | https://arxiv.org/pdf/1312.6565 | س1 |
| 9 | Review and classification of content recommenders in E-learning environment - ScienceDirect | https://www.sciencedirect.com/science/article/pii/S1319157821001427 | س3: [50] |

**السلسلة 15** (10)

| # | العنوان كما أُعيد | الرابط | القرار |
|---|---|---|---|
| 1 | [RE] Modeling Personalized Item Frequency Information for Next-basket Recommendation | https://arxiv.org/pdf/2402.17925 | س1 (إعادة إنتاج لـ[19] على سلال البقالة) |
| 2 | Explore the Personalized Resource Recommendation of Educational Learning Platforms: Deep Learning | https://www.informatica.si/index.php/informatica/article/view/5690 | س4: لا يستعمل TIFU-KNN |
| 3 | tudr.thapar.edu | https://tudr.thapar.edu/bitstreams/faaef891-ab2f-4d55-99eb-afb0fc5df2a5/download | س1 |
| 4 | arxiv.org | https://arxiv.org/abs/2402.17925?context=cs | س2 |
| 5 | Collaborative recommendation model of MOOC online learning resources based on scoring matrix | https://inderscience.com/filter.php?aid=132416 | س4: لا يستعمل TIFU-KNN |
| 6 | [RE] Modeling Personalized Item Frequency Information for Next-basket Recommendation | https://cs.paperswithcode.com/paper/re-modeling-personalized-item-frequency | س2 |
| 7 | hse.ru | https://publications.hse.ru/pubs/share/direct/840141443.pdf | س4: امتداد زمني لـTIFU-KNN على بيانات شراء بحسب مقتطف الأداة |
| 8 | recom tifuknn | https://cornac.readthedocs.io/en/latest/_modules/cornac/models/tifuknn/recom_tifuknn.html | س1 (وثيقة برمجية) |
| 9 | rdd.edu.iq | https://iasj.rdd.edu.iq/journals/uploads/2025/01/17/cd53a35b8a30103f992f436f9fb5a007.pdf | س4: لا عنوان يعيّن العمل |
| 10 | re modeling personalized item frequency | https://sotaverified.org/papers/re-modeling-personalized-item-frequency | س1 |

### ب-3 مقارنة الأعداد بالبحث الأصلي

| # | المعروضة (الأصل) | المعروضة (الإعادة) | المُدخلة (الأصل) | المُدخل أو نسخته في الإعادة | مرشح للفحص | هل يثبت قرار الأصل؟ |
|---|---|---|---|---|---|---|
| 1 | 10 | 10 | 1 | [50] | — | نعم |
| 2 | 10 | 10 | 0 | — | — | نعم |
| 3 | 10 | 10 | 0 | — | — | نعم |
| 4 | 10 | 10 | 0 | — | — | نعم |
| 5 | 10 | 10 | 0 | — | 1 | **يحتاج فحصاً** (ب-4) |
| 6 | 10 | 10 | 1 | [51] مرجَّحاً | — | نعم |
| 7 | 10 | 10 | 1 | [52] | — | نعم |
| 8 | 10 | 10 | 0 | [52] مكرر | — | نعم |
| 9 | 10 | 10 | 0 | [18] | — | نعم |
| 10 | 18 | 18 | 0 | [18] | — | نعم |
| 11 | 10 | 10 | 0 | [17] | — | نعم |
| 12 | 10 | 10 | 1 | [53] | — | نعم |
| 13 | 10 | 10 | 0 | [3] | — | نعم |
| 14 | 10 | 9 | 0 | — | 1 (منخفض) | نعم، ما لم يُظهر الفحص غير ذلك |
| 15 | 10 | 10 | 0 | — | — | نعم |
| **المجموع** | **158** | **157** | **4** | | **2** | |

### ب-4 سلاسل التحقق المستقلة (لا تُحسب في الأعداد)

1. `BPR time-to-dropout MOOC course recommendation KU Leuven`: عيّنت نتيجة السلسلة 5 (#2). بحسب مقتطف الأداة، هي عمل لمجموعة KU Leuven (Gharahighehi وVenturini وVens وزملاؤهم) بعنوان «Extending Bayesian Personalized Ranking with Survival Analysis for MOOC Recommendation» في UMAP '23. والعمل يضيف زمن الانسحاب المقدَّر بتحليل البقاء إلى BPR، ويقارنه بـBPR الذي يميز المرئي من غير المرئي وحده، في توصية مقررات على ثلاث مجموعات بيانات لمقررات مفتوحة. **لم يُتحقق** من الوعاء ولا من النص ولا من نوع المقارنة.
2. `"Unsupervised Deep Collaborative Filtering Recommender System for E-Learning Platforms" OULAD evaluation metrics`: لم تظهر مقاييس الفصل. يذكره مقتطف الأداة في وقائع SADASC 2020 (Springer)، ولم يُتحقق من ذلك.
3. `Advances in Multimedia 2022 web-based learning resources recommendation timeliness popularity collaborative filtering`: عيّنت نتيجة السلسلة 6 (#6). بحسب مقتطف الأداة، هي X. Han، «Recommendation Algorithm of Web-Based Learning Resources considering Timeliness and Popularity»، *Advances in Multimedia*، 2022، doi: 10.1155/2022/2584890، ولم يُتحقق من حل المعرّف. وهي ترشيح تعاوني يضيف الحداثة والشعبية، وتقيس الدقة والرضا على منصة تعليم مدرسية. ولا يظهر في المقتطف فصل للجديد عن المكرر ولا شعبية محسوبة عند لحظة التوصية، فلا تمس الفجوة الثانية كما صيغت (س4).

### ب-5 ما تعنيه الإعادة للرسالة

- **ثبتت قرارات ثلاث عشرة سلسلة.** ظهرت المراجع المدخلة الأربعة أو نسخها في سلاسلها، إلا [51] الذي ظهر سجل يرجَّح أنه هو. وفي السلسلة 15 لم يظهر تطبيق لـTIFU-KNN في التعليم.
- **السلسلة 5 تحتاج فحصاً.** فعمل KU Leuven (ب-4، البند 1) قد يكون أقرب ما ظهر إلى مقارنة إشارة ضمنية متدرجة بأخرى ثنائية داخل نموذج واحد في التعليم. ويمس ذلك جملة الفجوة الأولى في 2-1: «لم يظهر عمل في التعليم يقارن الإشارة الضمنية الموزونة بالثنائية داخل النموذج نفسه». لكنه يختلف عنها في ثلاثة أمور:
  - إشارته زمن انسحاب يقدّره نموذج بقاء، لا عدد أيام الوصول وحداثته وشدته.
  - مهمته توصية مقررات عبر منصة، لا موارد داخل مقرر.
  - لم يُقرأ نصه بعد.
  ولا يُعرف إن كان قد ظهر في البحث الأصلي. فإن كان قد ظهر واستُبعد، فسبب استبعاده غير مسجل.
- **القرار (D-127):** لا يتغير الجدول 2-1-أ ولا ادعاء في الرسالة في هذه المرحلة. ويُرفع العمل إلى الطالب والمشرف الفعلي ليقرآ نصه ويقررا أمرين: إدخاله مرجعاً، وتقييد جملة الفجوة الأولى. فإن قررا ذلك، أعيد `renumber.py` وسير ب-6.
- **السلسلة 14:** يُرفع فصل SADASC 2020 بأولوية منخفضة. فلا يمس جملة OULAD في 2-1 إلا إذا قاس بالترتيب وفصل الجديد عن المكرر، ولا دليل على ذلك في ما ظهر.

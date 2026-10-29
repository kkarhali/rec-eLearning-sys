# الملحق ج: جدول المتطلبات الكامل ومصفوفة التتبّع

يضم هذا الملحق المتطلبات الواحد والستين التي لخّصها الفصل الرابع (القسم 4-3)، منها ستون متطلباً نشطاً ومتطلب واحد مؤجَّل إلى عمل مستقبلي (FR-40)، بأولوياتها ومصادرها وحالتها بعد الوسم واكتمال التشغيل التأكيدي، ثم مصفوفة التتبّع الكاملة من المتطلب إلى المكوّن والملف وطريقة التحقق. ولكل متطلب في الجداول ج-1 إلى ج-3 عمود «معيار القبول»: جملة واحدة قابلة للفحص تسمّي الاختبار الآلي الذي يتحقق منها بصيغة «الملف::الاختبار»، أو الأمر أو الفحص اليدوي إن لم يكن له اختبار. واختبارات الوحدة والخدمة في `src/ml/tests/` و`src/backend/tests/`، والاختبار الطرفي بمتصفح حقيقي في `src/backend/e2e/live-screenshots.js`. ويشير عمود «المصدر» إلى القسم الذي يسوّغ المتطلب في الرسالة، أو إلى الفرضية التي يخدمها، أو إلى معيار إمكانية الوصول. وقيم عمود «الحالة»: «منفّذ»، و«جزئي»، و«مخطط» لما لم يُنفَّذ بعد، و«غير منفّذ» لمتطلب اختياري لم يتسع له الوقت، و«مؤجَّل إلى عمل مستقبلي» لمتطلب أُخرج من نطاق هذه النسخة بعد التشغيل التأكيدي. والمتطلب FR-29 محذوف ورقمه شاغر. وأُجِّل FR-40 (خدمة عروض 2014 في الواجهة) لأن فتح هذه العروض لا يضيف دليلاً، فالأرقام لا تؤخذ من الشاشات، ولأنه يقتضي بناء مخرجات عروض 2014 في الخدمة بعد التجميد (القسم 4-3-1).

**جدول ج-1: المتطلبات الوظيفية لخط التجارب (الممثل: الباحث؛ إعداد الباحث)**

| الرقم | المتطلب | الأولوية | المصدر | الحالة | معيار القبول |
|---|---|---|---|---|---|
| FR-01 | التحقق من جداول OULAD السبعة ببصمات MD5 وعدد صفوف جدول التفاعل (10,655,280) قبل أي تشغيل | لازم | التحقق من البيانات (3-2-3) | منفّذ | الأمر `bash data/download.sh` يطبع «integrity: PASS» بعد مطابقة MD5 للجداول السبعة، ويطبع عدد صفوف جدول التفاعل المعاد بناؤه (فحص بالأمر)؛ و`test_api_live.py::test_meta_contract` يتحقق من بصمة جدول التفاعل في بيانات الخدمة |
| FR-02 | حجب عروض 2014 برمجياً ما لم يُصرَّح بالتأكيد صراحة بعد وسم التجميد | لازم | الفصل بين التطوير والتأكيد (3-1، 3-5-9) | منفّذ | `test_splits.py::test_2014_refused` و`test_rest_of_barrier_intact`: كل محمّل عام يرفض أي عرض من 2014 دون تصريح صريح |
| FR-03 | تجميع الصفوف المكررة، واستبعاد الأنواع التنقلية الخمسة من الهدف مع إبقائها ملامح، وبناء سلال الأيام | لازم | المعالجة ووحدات التحليل (3-2-4، 3-2-5، 3-3-1) | منفّذ | `test_splits.py::test_catalogue_and_exclusion` و`test_exclusion_sets` و`test_tasks`: الأنواع الخمسة خارج الكتالوج والهدف، والمهمة A موارد جديدة وحدها، وكل زوج هدف إما في الكتالوج وإما معدود غير قابل للبلوغ |
| FR-04 | العائلة المتداخلة للإشارة L0 ⊂ L1 ⊂ L2 ⊂ L3 من التدريب وحده، وثقة تحليل المصفوفات ونسختها الثنائية | لازم | تمثيل السلوك (3-3-2، 3-3-3)؛ H2 | منفّذ | `test_signals.py::test_levels` و`test_nesting_special_cases` و`test_type_medians_from_training_only` و`test_binary_confidence`: المستويات متداخلة، ووسيط النوع من التدريب وحده، والثقة الثنائية لـL0 |
| FR-05 | خطوط الأساس العشرة بواجهة موحدة، وضبط حتى عشرين إعداداً لكل (عرض، نقطة قطع، مهمة)، بالفضاءات المسجلة | لازم | خطوط الأساس والضبط (3-4-1، 3-5-8)؛ H1، H2 | منفّذ | `test_models.py::test_adr004_spaces` و`test_recommend_interface`: فضاء كل نموذج مضبوط لا يتجاوز عشرين إعداداً، والواجهة الموحدة تعمل لكل خط أساس |
| FR-06 | GRU-lite بمواصفاته المسجلة وحزمة الصحة S1–S6، وتوثيق الفشل إن وقع | لازم | المكوّن التسلسلي العصبوني (3-4-4)؛ H3 | منفّذ | `test_gru.py` (سبعة اختبارات، منها `test_gradient_check` و`test_padded_steps_keep_state`) تمر، و`results/dev2013/gru_sanity.md` يعلن اجتياز البوابات |
| FR-07 | مكوّنا السياق: أسبقية قرب التقييم وشعبية العنقود، بالواجهة الموحدة نفسها | لازم | مكوّنا السياق (3-4-2)؛ H4-ب | منفّذ | `test_models.py::test_cluster_popularity_counts` و`test_assessment_proximity_bin`: عدّ شعبية العنقود في النافذة وفئة قرب التقييم مطابقان لمثالين محسوبين يدوياً |
| FR-08 | ملامح المتعلم حتى يوم القطع دون سمات حساسة (سلّم M0 وM1 وM2)، والتجميع بـk-means++ وقاعدة اختيار k | لازم | تحليل المتعلمين (3-4-5)؛ H4 | منفّذ | `test_learners.py::test_vle_features` و`test_kmeanspp_probabilities` و`test_silhouette_dbi_examples` و`test_recovers_separated_gaussians`: الملامح محسوبة حتى يوم القطع وحده، والتجميع يستعيد عناقيد مفصولة |
| FR-09 | الانحدار اللوجستي المنتظم وشجرة القرار، وعتبة يودن خارج الطيّة، والتحقق بترك عرض واحد داخل 2013، وحذف الطلاب المتداخلين | لازم | التنبؤ بالخطر (3-4-5)؛ H4-أ | منفّذ | `test_learners.py::test_logistic_example` و`test_gini_example` و`test_auc_ap_youden`، و`test_splits.py::test_ids_only_filter_2013_risk_training` لحذف الطلاب المتداخلين من التدريب وحده |
| FR-10 | الهجين: الرتبة الوسطى، وشبكة السمبلكس، وقاعدة القبول على نوافذ اختبار 2013، وأرضية الشخصنة بوزن لا يقل عن 1/4، وأربعة مكوّنات على الأكثر، والتجميد في ملف إعداد | لازم | النموذج الهجين (3-4-3)؛ H1 | منفّذ | `test_hybrid_stats.py::test_mid_rank_on_ties` و`test_simplex_grid_sizes` و`test_acceptance_rule` و`test_greedy_forward` و`test_personalisation_floor` |
| FR-11 | فاصل bootstrap-t العنقودي، واختبار قلب الإشارات الدقيق، وتصحيح هولم بأربع فرضيات، وجدولا الحكم، واختبار الهامش | لازم | الاستدلال ومعيار النجاح (3-5-5، 3-5-6) | منفّذ | `test_hybrid_stats.py::test_bootstrap_t` و`test_sign_flip_example` و`test_holm_example` و`test_verdicts_table19a` و`test_bidirectional_h3_table`: النتائج تطابق أمثلة الملحق ب |
| FR-12 | سجل الزمن والذاكرة لكل (نموذج، زوج، مرحلة)، ومقارنته بسقف ثماني ساعات معالج | لازم | ميزانية الحوسبة (3-5-8) | منفّذ (السجل في `timing.csv` وملفات بيانات التشغيل، والملخص الآلي في `results/budget_summary.md` بالسكربت `scripts/compute_budget_summary.py`) | الأمر `python3 scripts/compute_budget_summary.py --check` يطبع «identical»: الملخص في `results/budget_summary.md` مولَّد من السجلات، ويقارن كل تشغيل بسقف ثماني ساعات معالج (فحص بالأمر) |
| FR-13 | التجميد: فحص آلي لقائمة التجميد، وملف الإعداد المجمَّد، والتذكير بوسم نسخة الشيفرة | لازم | التجميد (3-5-12) | منفّذ (قائمة التجميد مولَّدة آلياً في results/frozen/freeze_checklist.md بشروطها العشرة مستوفاة، ثم وُسمت نسخة الشيفرة freeze-03) | `test_freeze_config.py` (خمسة اختبارات لتوليد قائمة التجميد) تمر، والقائمة المولَّدة `results/frozen/freeze_checklist.md` تعلم الشروط العشرة مستوفاة، ومنها شرطا المراجعتين الآليتين بدور «الزميل الباحث» والمشرف |
| FR-14 | التشغيل التأكيدي الوحيد وجدول الأحكام | لازم | التجميد والتأكيد (3-5-12) | منفّذ (تشغيل واحد بلا انحراف؛ results/conf2014/verdicts.csv وملف القفل LOCK) | `test_confirmatory.py::test_refusals` (رفض التشغيل إن وُجد مجلد المخرجات أو غاب الوسم أو تغيّرت الشجرة) و`test_lock_refusals` (رفض أي تعديل بعد ملف القفل) |
| FR-15 | تحليلات الحساسية والإنصاف وأثر البروتوكول، دون اتصال وحده | ينبغي | الحساسية والإنصاف (3-5-10، 3-5-11) | منفّذ (الطور الثاني من التشغيل التأكيدي: ملفات الحساسية والإنصاف وأثر البروتوكول في results/conf2014/) | وجود ملفات الطور الثاني في `results/conf2014/` وقراءتها في القسم 5-8 (فحص يدوي) |
| FR-16 | بناء معاملات نقاط القطع للمكوّنات الثقيلة، ونماذج الخطر، ونموذج عناقيد اليوم 56 | لازم | إعادة التشغيل (4-1-1) | منفّذ | `test_serving.py::test_wrmf_foldin_uses_artifact_items`: الخدمة تقرأ معاملات أقرب نقطة قطع ولا تدرّب عند الطلب |
| FR-17 | تفكيك الدرجة إلى مساهمات المكوّنات، والجملة الرئيسية والثانية، ودليل كل مكوّن | لازم | تفسير التوصيات (3-4-6) | منفّذ | `test_serving.py::test_recommend_structure_and_unseen` و`test_api_live.py::test_explanation_contract_and_consistency`: المساهمات تجمع إلى الدرجة، ولكل توصية جملة رئيسية |
| FR-36 | قراءة معرّفات طلاب 2014 المحدودة لترشيح تدريب H4-أ، مع سجل وصول (الزمن، وMD5، والأعمدة، والعدد، ونسخة الشيفرة) | لازم | استقلال الأفراد (3-4-5) | منفّذ | `test_splits.py::test_columns_and_log` و`test_extra_columns_rejected_and_logged` و`test_purpose_whitelist`: ثلاثة أعمدة فقط، وغرض من القائمة البيضاء، وسطر في سجل الوصول لكل قراءة |
| FR-38 | أمر واحد يعيد إنتاج نتائج التطوير والمعاملات من الصفر، مع تقرير مطابقة | لازم | قابلية الإعادة (3-6-2) | منفّذ (results/dev2013/repro_diff.md: «مطابق» على نسخة نظيفة) | الأمر `python3 -m src.ml.experiments.reproduce_dev` على نسخة نظيفة يكتب «مطابق» في `results/dev2013/repro_diff.md` (فحص بالأمر) |
| FR-39 | جدول الحد الأدنى للأثر القابل للكشف لكل فرضية قبل التجميد، والوصف المسجل الملحق بحكم «غير حاسمة» | لازم | القوة الإحصائية (3-5-7) | منفّذ | `test_hybrid_stats.py::test_margin_and_power` و`test_degenerate_label_and_verdict`، و`results/dev2013/mde80.md` مكتوب قبل الوسم |

ويعرض الجدول ج-2 المتطلبات الوظيفية لخدمة إعادة التشغيل وواجهتها البرمجية، التي يستعملها المتعلم والمدرّس والباحث.

**جدول ج-2: المتطلبات الوظيفية للخدمة والواجهة البرمجية (الممثلون: المتعلم، والمدرّس، والباحث؛ إعداد الباحث)**

| الرقم | المتطلب | الأولوية | المصدر | الحالة | معيار القبول |
|---|---|---|---|---|---|
| FR-18 | سرد العروض بدورها وحالة إتاحتها وطولها ونقاط قطعها، دون قراءة أي بيانات لعروض 2014 المقفلة | لازم | الفصل بين التطوير والتأكيد (3-5-9) | منفّذ | `test_api_live.py::test_health_and_presentations` (تسعة عروض منشورة، وعروض 2014 «مقفلة» بلا بيانات) و`test_static_errors.py::test_confirmatory_locked_409_everywhere` |
| FR-19 | سرد تسجيلات عرض مع بحث وترقيم، بقائمة بيضاء من الحقول دون سمة حساسة أو نتيجة نهائية | لازم | وحدات التحليل والأخلاقيات (3-2-4، 3-7) | منفّذ | `test_api_live.py::test_registrations_paging_and_search` و`test_contract_json.py::test_registrations_have_no_final_result_or_unregistration` |
| FR-20 | حساب كل استجابة عند اليوم المطلوب t، وإعلان اليوم وتاريخ النموذج فيها | لازم | إعادة التشغيل (4-1-1) | منفّذ | `test_serving.py::test_no_future_data_used` و`test_future_events_resources_learners_change_nothing`، و`test_contract_no_risk.py::test_every_day_dependent_response_carries_provenance_model_cut` |
| FR-21 | أفضل k توصية (افتراضياً 10، وحتى 20) لمهمة الموارد الجديدة، ومهمة أي وصول بخيار صريح، مع التفسير المضمَّن | لازم | المهام (3-5-2)؛ تفسير التوصيات (3-4-6) | منفّذ | `test_api_live.py::test_recommendation_contract` و`test_task_a_excludes_seen_task_b_may_include`، و`test_static_errors.py::test_validation_422` يرفض k = 0 وk = 21 |
| FR-22 | تفسير مفصل لكل توصية معروضة: المكوّن ووزنه ورتبته المطبَّعة ومساهمته ودليله | لازم | تفسير التوصيات (3-4-6) | منفّذ | `test_api_live.py::test_explanation_contract_and_consistency`: لكل مكوّن الوزن والرتبة المطبَّعة والمساهمة والجملة والدليل، والمساهمات تجمع إلى الدرجة |
| FR-23 | نشاط المتعلم حتى t دون خطر ولا عنقود | ينبغي | عرض الخطر (3-7) | منفّذ | `test_api_live.py::test_history_contract` و`test_learner_responses_have_no_risk_or_sensitive` |
| FR-24 | النظرة العامة للمدرّس: المتعلمون النشطون، والكتالوج عند t، ووسيط الأيام النشطة، و«اتساع التوصيات عند اليوم t»، والتقييمات القادمة، وأعلى الموارد، وفئات درجة الخطر | لازم | لوحة المدرّس (4-4-2) | منفّذ | `test_api_live.py::test_overview_contract` و`test_contract_json.py::test_kpi_cohort_consistent_with_clusters_and_table` |
| FR-25 | عناقيد اليوم 56 (العدد، والاستقرار، والأحجام، والمراكز، ووصف عربي مولَّد بقاعدة)، تُعرض عند t ≥ 56 | لازم | التجميع (3-4-5) | منفّذ | `test_api_live.py::test_clusters_contract` و`test_cluster_matches_engine`، و`test_instructor_day_before_first_snapshot` يرفض ما قبل اليوم 56 |
| FR-26 | درجة خطر نسبية غير معايَرة من الانحدار اللوجستي على ملامح سجل بيئة التعلم وحدها، عند آخر نقطة قطع معروضة من {56، 112} لا تتجاوز t (نقطة القطع 28 مبنية ولا تُعرض، لأن مسارات المدرّس ترفض ما قبل اليوم 56)، مع عتبة يودن بدقتها الكاملة ومصدر التقدير، في مسارات المدرّس وحدها | لازم | التنبؤ بالخطر وعرضه (3-4-5، 3-7) | منفّذ | `test_api_live.py::test_risk_matches_engine_m1` و`test_meta_declares_unsafe_demo_and_score`، و`test_contract_no_risk.py::test_learner_models_have_no_risk_or_sensitive_fields` |
| FR-27 | ملف متعلم للمدرّس: الملامح مقابل الوسيط، والعنقود، وعوامل الدرجة، وأفضل ثلاث توصيات | لازم | لوحة المدرّس (4-4-2) | منفّذ | `test_api_live.py::test_learner_detail_contract` |
| FR-28 | مساران لحالة الخدمة ومصدر المخرجات (نسخة الشيفرة، ومكوّنات الهجين، ونقاط القطع، وبصمة البيانات) | لازم | قابلية الإعادة (3-6-2) | منفّذ | `test_api_live.py::test_meta_contract` و`test_static_errors.py::test_health` |
| FR-29 | *(محذوف: «وضع الباحث» كان سيكشف بيانات ما بعد t)* | — | — | — | — |
| FR-30 | تصدير الجدول المعروض في لوحة المدرّس بصيغة CSV | يمكن | لوحة المدرّس (4-4-2) | غير منفّذ | — |
| FR-37 | إشعار ظاهر قبل اليوم 70 (لا مكوّن ثقيل، والأوزان مُعاد تطبيعها) وعند متعلم بلا تاريخ (ترتيب غير شخصي) | لازم | إعادة التشغيل (4-1-1) | منفّذ | `test_api_live.py::test_model_cut_by_day` (إشعار «قبل أول قطع») و`test_no_history_notice_fr37` (إشعار الترتيب غير الشخصي) |
| FR-40 | خدمة عروض 2014 في الواجهة بعد التشغيل التأكيدي. يُسجَّل الإذن في `results/conf2014/ui_open.json` بعد التحقق، ولا تُخدَم عروض 2014 في هذه النسخة | مؤجَّل | الفصل بين التطوير والتأكيد (3-5-12) | مؤجَّل إلى عمل مستقبلي (سجل الإذن مكتوب، ولا كود يقرؤه) | لا قبول في هذه النسخة؛ ويبقى `test_static_errors.py::test_confirmatory_locked_409_everywhere` ناجحاً |

ويعرض الجدول ج-3 المتطلبات الوظيفية لصفحات الواجهة نفسها.

**جدول ج-3: المتطلبات الوظيفية للواجهة (إعداد الباحث)**

| الرقم | المتطلب | الأولوية | المصدر | الحالة | معيار القبول |
|---|---|---|---|---|---|
| FR-31 | صفحة المتعلم: اختيار العرض والتسجيل واليوم، وشريط سياق بتاريخ النموذج والتقييم القادم، وعشر بطاقات بتفسير وحصص المساهمة، ولوحة «لماذا؟» | لازم | واجهة المتعلم (4-9-2) | منفّذ | الاختبار الطرفي عند 1440 و375 و360 بكسل: عشر بطاقات على الأقل، وشارة «تاريخ النموذج»، ولوحة «لماذا؟» بمكوّن واحد على الأقل |
| FR-32 | لوحة المدرّس: بطاقات المؤشرات، والعناقيد، ومدرج درجة الخطر بعتبته، وجدول قابل للفرز والتصفية، ودرج ملف المتعلم | لازم | لوحة المدرّس (4-9-2) | منفّذ | `test_api_live.py::test_learners_contract_sort_page_filter` و`test_learners_idle_filter_server_side_and_paging`، والاختبار الطرفي: الجدول والدرج والصفحة الثانية بلوحة المفاتيح وعدد الخاملين المطابق للخادم |
| FR-33 | حفظ حالة الصفحة (العرض، والتسجيل، واليوم، والتصفية) في عنوان الصفحة | ينبغي | قابلية الإعادة (NFR-04) | منفّذ | الاختبار الطرفي يفتح الصفحات بحالتها من العنوان، ويتحقق من كتابة الإزاحة فيه عند الانتقال إلى الصفحة الثانية وحذفها عند التصفية |
| FR-34 | شريط يوم يُظهر نقاط القطع الثلاث ونقاط قطع الخطر ومواعيد التقييم المنشورة | ينبغي | إعادة التشغيل (4-1-1) | منفّذ | فحص يدوي لعلامات الشريط؛ والاختبار الطرفي يتحقق من انتقال الشريط إلى اليوم 56 في لوحة المدرّس |
| FR-35 | صفحة «عن النظام»: المنهجية، والمصدر، والقيود (ومنها «بلا أمان وصول» و«درجة غير معايَرة»)، والإسناد بترخيص CC BY 4.0 | لازم | الترخيص والأمانة في العرض (3-2-3، 3-7) | منفّذ | قائمة تفحّص يدوية لمحتوى الصفحة (المنهجية، والمصدر، والقيود، والإسناد بترخيص CC BY 4.0)؛ والاختبار الطرفي يفتحها دون خطأ ودون تمرير أفقي، ويفحص شجرة الوصول وتباين النص فيها |

ويعرض الجدول ج-4 المتطلبات غير الوظيفية ومعيار التحقق من كل منها.

**جدول ج-4: المتطلبات غير الوظيفية ومعايير التحقق (إعداد الباحث)**

| الرقم | الفئة | المتطلب ومعيار القبول | الأولوية | المصدر | الحالة |
|---|---|---|---|---|---|
| NFR-01 | الأداء | في يوم مسخَّن: 200 مللي ثانية على الأكثر لمسارات المتعلم وملف المتعلم في لوحة المدرّس، وثانية واحدة على الأكثر للنظرة العامة والعناقيد وجدول المتعلمين. وفي أي يوم غير مسخَّن من عرض حُسب له اختيار العناقيد مسبقاً لكل أيامه: خمس ثوانٍ على الأكثر لأول طلب توصية، وثماني ثوانٍ على الأكثر لأول نظرة عامة للمدرّس | لازم | الواجهة (4-1) | جزئي: الحد في اليوم المسخَّن منفّذ ومقاس، وحد اليوم غير المسخَّن مستوفى للعرض الذي حُسبت عناقيده مسبقاً وحده. يفرض الحدود اختباران آليان، ويأخذ اختبار اليوم المسخَّن أدنى زمن من ثلاث محاولات بعد طلب تسخين، فلا يفحص كل طلب. والحساب المسبق منفّذ في هذه النسخة للعرض الافتراضي FFF_2013J وحده، واستغرق نحو 19 دقيقة بـ4 عمليات لأيامه البالغة 269 يوماً. وقيس بأداة القياس (طلبات HTTP) بآلة من 4 أنوية (2026-10-29؛ المصدر: `results/serving_bench/`). في اليوم المسخَّن بلغ أقصى طلب 31.5 مللي ثانية (تفسير مورد). وعلى خادم مسخَّن، أول طلب في كل يوم بارد: أول طلب توصية بين 1.6 و3.8 ثانية في 11 يوماً، وأول نظرة عامة قبل أي طلب في يومها بين 3.1 و5.1 ثانية في 5 أيام. وفي الأيام نفسها دون الحساب المسبق كان أول طلب توصية بين 15.2 و19.4 ثانية. والعروض الأخرى بلا حساب مسبق يبقى أول طلب فيها نحو هذا الزمن |
| NFR-02 | الأداء | إقلاع في حدود ثوانٍ، وذاكرة تشغيل لا تتجاوز 1.5 GB | ينبغي | آلة التشغيل | جزئي (الذاكرة لم تُلخَّص آلياً) |
| NFR-03 | الحوسبة | لا يتجاوز تشغيل التطوير الكامل والتشغيل التأكيدي ثماني ساعات معالج لكل منهما | لازم | ميزانية الحوسبة (3-5-8) | منفّذ للتطوير؛ وجزئي للتأكيدي: الحد الأعلى المحسوب (أربع عمليات × زمن الجدار) 2.4 ساعة للطور الأول و7.1 ساعة للطور الثاني، أي نحو 9.5 ساعة للتشغيل كله، فوق السقف، والسقف مسجل للتشغيل لا للطور؛ ولا قياس مباشر لزمن المعالج يثبت أن الزمن الفعلي دونه؛ والتفصيل في `results/budget_summary.md` (FR-12) |
| NFR-04 | قابلية الإعادة | بذور ثابتة، ومفاتيح تعادل حتمية، وبيانات تشغيل بنسخة الشيفرة وبصمة البيانات؛ والطلب نفسه يعطي الاستجابة نفسها | لازم | قابلية الإعادة (3-6-2) | منفّذ |
| NFR-05 | الصدق العلمي | لا رقم في الرسالة إلا من ملف نتائج يولّده الكود؛ وإعادة التشغيل لا تنتج أي رقم تقييم | لازم | قابلية الإعادة (3-6-2)؛ (4-1-1) | منفّذ |
| NFR-06 | منع التسرب | كل ما يُستعمل لطلب اليوم t محسوب من أحداث لا تتجاوز t ومعاملات نقطة قطع لا تتجاوز t؛ وتغيير حدث بعد t لا يغيّر الاستجابة | لازم | منع التسرب (3-5-9) | منفّذ |
| NFR-07 | عزل التأكيد | عروض 2014 محجوبة في طبقة خط التجارب، ولا تُخدَم من الواجهة (رمز 409 لكل عروض 2014) | لازم | الفصل بين التطوير والتأكيد (3-5-9) | منفّذ |
| NFR-08 | الخصوصية | السمات الست الحساسة والنتيجة النهائية لا تُخزَّن في المعاملات ولا تمر في أي استجابة؛ ولا محاولة لإعادة التعريف | لازم | الأخلاقيات (3-7) | منفّذ |
| NFR-09 | فصل الخطر | لا حقل خطر ولا عنقود في عقود المتعلم، وقائمة بيضاء لحقول عقود المدرّس، باختبار عقد آلي | لازم | عرض الخطر (3-7) | منفّذ |
| NFR-10 | إدارة البيانات | البيانات الخام والذاكرة المؤقتة ومخرجات البناء خارج نظام إدارة الإصدارات | لازم | الترخيص (3-2-3) | منفّذ |
| NFR-11 | القيود البيئية | لا اعتماد إلا على المكتبة القياسية وnumpy وpandas وstarlette وuvicorn وpydantic، ولا شبكات توزيع ولا حزم npm | لازم | بيئة التنفيذ (3-6-1) | منفّذ |
| NFR-12 | قابلية الاستخدام | الوصول إلى التوصيات بثلاث تفاعلات على الأكثر، وجملة تفسير غير تقنية، والمصطلح الإنكليزي عند أول ظهور | ينبغي | الواجهة (4-9) | منفّذ (قائمة تفحّص) |
| NFR-13 | العربية والاتجاه | اتجاه من اليمين إلى اليسار، وخصائص CSS المنطقية، وعزل المعرّفات اللاتينية ورموز المقارنة، وأرقام لاتينية | لازم | الواجهة (4-9-3) | منفّذ |
| NFR-14 | إمكانية الوصول | استهداف مستوى AA من WCAG 2.2 بالتحقق من بنود الجدول 4-12 | لازم | WCAG 2.2 [71] | جزئي (تُفحص آلياً بنود الجدول 4-12 القابلة للأتمتة: ترتيب التركيز وحلقته بلوحة المفاتيح، ورابطا التخطي إلى جدول المتعلمين والتوصيات، واسم وصولي لكل عنصر تفاعلي في شجرة الوصول، وتباين أزواج الألوان والنص المرسوم (NFR-22)، والعرض من 360 إلى 1440 بكسل؛ ولم يُجرَ تدقيق يدوي كامل ولا اختبار مع قارئ شاشة) |
| NFR-15 | التجاوب | عرض صحيح من 360 إلى 1440 بكسل، والجداول تتمرر داخل حاويتها | ينبغي | WCAG 1.4.10 [71] | منفّذ |
| NFR-16 | قابلية الصيانة | عقود pydantic مصدر وحيد لشكل الاستجابات، وأنواع الواجهة مطابقة لها، وفحص صارم للأنواع | ينبغي | المعمارية (4-5-2) | جزئي (المطابقة بالمقارنة مع ملفات المحاكاة) |
| NFR-17 | قابلية الاختبار | اختبارات الواجهة البرمجية بعميل داخلي، والمحرّك بمحرك اصطناعي محقون، وفحص الأنواع، واختبار طرفي بمتصفح حقيقي | لازم | بيئة التنفيذ (3-6-1) | منفّذ |
| NFR-18 | الأمانة في العرض | «درجة خطر نسبية غير معايَرة»، ووسم مصدر التقدير، وتاريخ النموذج، وتنبيه إعادة التشغيل التاريخية، ولا ادعاء بأثر تعليمي | لازم | الأخلاقيات (3-7) | منفّذ (كل تسمية ظاهرة للدرجة «درجة الخطر النسبية» أو «درجة خطر نسبية غير معايَرة»، ومنها عنوان عمود الجدول) |
| NFR-19 | المتانة | بنية أخطاء موحدة دون تتبعات استثناءات في الاستجابات، واختبار لكل رمز | ينبغي | الواجهة البرمجية (4-8) | منفّذ |
| NFR-20 | الأمان التشغيلي | الربط بالعنوان المحلي افتراضياً، وخيار يعيد «غير موجود» لمسارات المدرّس | ينبغي | حدود النظام (4-1-2) | منفّذ |
| NFR-21 | التخزين | لا يتجاوز حجم المعاملات المخزَّنة 100 MB | ينبغي | نموذج البيانات (4-7) | منفّذ (نحو 0.5 MB) |
| NFR-22 | التحقق الآلي | فحص آلي لنسب التباين لكل أزواج الألوان المستعملة | ينبغي | NFR-14 | منفّذ (اختبار يحسب نسبة WCAG لكل زوج مستعمل ويفشل دون 4.5:1 للنص و3:1 للحدود والأشكال، ويفشل إن ظهر لون غير مصنَّف؛ وفحص تباين كل نص مرسوم في الاختبار الطرفي) |

ويعرض الجدول ج-5 مصفوفة التتبّع الكاملة من كل متطلب إلى مصدره والمكوّن والملف الذي ينفّذه وطريقة التحقق منه.

**جدول ج-5: مصفوفة التتبّع الكاملة (المتطلب ← المصدر ← المكوّن والملف ← التحقق؛ إعداد الباحث)**

| المتطلب | المصدر | المكوّن · الملف | التحقق |
|---|---|---|---|
| FR-01 | 3-2-3 | data/verify_oulad.py | تشغيل قبل كل تجربة؛ البصمة في بيانات التشغيل |
| FR-02 | 3-5-9 | src/ml/data.py (حارس 2014) | test_splits.py::test_2014_refused، test_rest_of_barrier_intact |
| FR-03 | 3-2-4، 3-2-5 | src/ml/data.py | test_splits.py::test_catalogue_and_exclusion، test_exclusion_sets، test_tasks |
| FR-04 | H2 | src/ml/signals.py | test_signals.py (سبعة اختبارات، ومنها مثال الملحق ب-1) |
| FR-05 | H1، H2 | src/ml/models/، harness.py، run_baselines.py | test_models.py::test_adr004_spaces، test_recommend_interface؛ ملفات نتائج التطوير |
| FR-06 | H3 | models/gru_lite.py، gru_sanity.py، run_gru.py | test_gru.py (سبعة اختبارات)؛ تقرير حزمة الصحة gru_sanity.md |
| FR-07 | H1، H4-ب | models/context.py | test_models.py::test_cluster_popularity_counts، test_assessment_proximity_bin |
| FR-08 | H4 | src/ml/learners.py | test_learners.py::test_vle_features، test_kmeanspp_probabilities، test_silhouette_dbi_examples |
| FR-09 | H4-أ | learners.py، learner_analysis.py | test_learners.py::test_logistic_example، test_gini_example، test_auc_ap_youden؛ test_splits.py::test_ids_only_filter_2013_risk_training |
| FR-10 | H1 | hybrid.py، components.py، run_hybrid.py | test_hybrid_stats.py::test_acceptance_rule، test_greedy_forward، test_personalisation_floor؛ ملف التركيبة المجمَّدة |
| FR-11 | 3-5-5 | src/ml/stats.py | test_hybrid_stats.py::test_bootstrap_t، test_sign_flip_example، test_holm_example، test_verdicts_table19a (أمثلة الملحق ب-13 وب-14) |
| FR-12 | 3-5-8 | harness.py (سجل الزمن)؛ scripts/compute_budget_summary.py | ملفات الأزمنة؛ results/budget_summary.md والأمر نفسه بخيار --check |
| FR-13 | 3-5-12 | experiments/freeze_config.py (ومعه توليد قائمة التجميد) | ملف الإعداد المجمَّد وبصماته؛ results/frozen/freeze_checklist.md؛ test_freeze_config.py |
| FR-14 | 3-5-12 | experiments/run_confirmatory.py | test_confirmatory.py::test_refusals (ومنها رفض التشغيل الثاني)، test_lock_refusals؛ مطابقة ملف القفل |
| FR-15 | 3-5-10، 3-5-11 | learner_analysis.py؛ run_confirmatory.py (الطور الثاني) | مراجعة الجداول |
| FR-16 | 4-1-1 | experiments/build_artifacts.py | test_serving.py::test_wrmf_foldin_uses_artifact_items |
| FR-17 | 3-4-6 | src/ml/serving.py (قوالب التفسير والدليل) | test_serving.py::test_recommend_structure_and_unseen؛ test_api_live.py::test_explanation_contract_and_consistency |
| FR-18 | 3-5-9 | src/backend/routes/meta.py | test_api_live.py::test_health_and_presentations؛ test_static_errors.py::test_confirmatory_locked_409_everywhere |
| FR-19 | 3-7 | src/backend/routes/learner.py | test_api_live.py::test_registrations_paging_and_search؛ test_contract_json.py::test_registrations_have_no_final_result_or_unregistration |
| FR-20 | 4-1-1 | serving.Engine؛ routes/learner.py | test_serving.py::test_no_future_data_used، test_future_events_resources_learners_change_nothing |
| FR-21 | 3-5-2 | serving.recommend؛ routes/learner.py | test_api_live.py::test_recommendation_contract، test_task_a_excludes_seen_task_b_may_include؛ test_static_errors.py::test_validation_422 |
| FR-22 | 3-4-6 | services/explanation.py | test_api_live.py::test_explanation_contract_and_consistency |
| FR-23 | 3-7 | routes/learner.py | test_api_live.py::test_history_contract، test_learner_responses_have_no_risk_or_sensitive |
| FR-24 | 4-4-2 | services/instructor.py؛ routes/instructor.py | test_api_live.py::test_overview_contract؛ test_contract_json.py::test_kpi_cohort_consistent_with_clusters_and_table |
| FR-25 | 3-4-5 | services/instructor.py (ملخص العناقيد) | test_api_live.py::test_clusters_contract، test_cluster_matches_engine، test_instructor_day_before_first_snapshot |
| FR-26 | 3-4-5 | services/instructor.py (جدول المتعلمين) | test_api_live.py::test_risk_matches_engine_m1، test_meta_declares_unsafe_demo_and_score |
| FR-27 | 4-4-2 | serving.learner_profile؛ routes/instructor.py | test_api_live.py::test_learner_detail_contract |
| FR-28 | 3-6-2 | routes/meta.py | test_api_live.py::test_meta_contract؛ test_static_errors.py::test_health |
| FR-30 | 4-4-2 | الواجهة (غير منفّذ) | — |
| FR-31 | 4-9-2 | learner.html، learner.ts، components/ | فحص الأنواع؛ الاختبار الطرفي (البطاقات والشارة ولوحة «لماذا؟») |
| FR-32 | 4-9-2 | instructor.html، instructor.ts، Pager.ts، routes/instructor.py | فحص الأنواع؛ test_api_live.py::test_learners_contract_sort_page_filter، test_learners_idle_filter_server_side_and_paging؛ الاختبار الطرفي |
| FR-33 | NFR-04 | state.ts | الاختبار الطرفي |
| FR-34 | 4-1-1 | components/DayScrubber | الاختبار الطرفي |
| FR-35 | 3-2-3، 3-7 | about.html | قائمة تفحّص |
| FR-36 | 3-4-5 | data.confirmatory_student_ids | test_splits.py::test_columns_and_log، test_extra_columns_rejected_and_logged، test_purpose_whitelist؛ سجل الوصول |
| FR-37 | 4-1-1 | serving.Engine.plan؛ services/replay.py؛ learner.ts | test_serving.py::test_plan_before_first_cut؛ test_api_live.py::test_model_cut_by_day، test_no_history_notice_fr37 |
| FR-38 | 3-6-2 | experiments/reproduce_dev.py | تقرير المطابقة repro_diff.md («مطابق») من ذاكرة فارغة على نسخة نظيفة |
| FR-39 | 3-5-7 | experiments/power.py | جدول الحد الأدنى للأثر؛ test_hybrid_stats.py::test_margin_and_power |
| FR-40 | 3-5-12 | مؤجَّل إلى عمل مستقبلي: سجل الإذن results/conf2014/ui_open.json وحده، ولا كود يقرؤه | test_static_errors.py::test_confirmatory_locked_409_everywhere |
| NFR-01 | 4-1 | serving.Engine.precompute_clusters؛ src/backend/precompute.py؛ src/backend/bench.py | test_api_live.py::test_latency_after_warmup، test_cold_day_bounded_after_cluster_precompute؛ test_serving.py::test_precompute_clusters_fills_cache_for_every_day |
| NFR-02 | آلة التشغيل | src/backend/app.py | قياس الذاكرة (مخطط) |
| NFR-03 | 3-5-8 | harness.py؛ run_confirmatory.py؛ scripts/compute_budget_summary.py | ملفات الأزمنة؛ أزمنة الطورين وعدد العمليات في results/conf2014/run_meta.json (حد أعلى محسوب)؛ results/budget_summary.md |
| NFR-04 | 3-6-2 | بيانات التشغيل؛ مفاتيح التعادل | test_splits.py::test_tiebreak_deterministic_and_order_free؛ test_models.py::test_deterministic_given_seed_and_snapshots؛ test_api_live.py::test_recommendation_matches_engine |
| NFR-05 | 3-6-2 | ملفات النتائج ومولّد التقارير | فحوص آلية في مولّد الجداول، ومراجعة آلية بدور «الزميل الباحث» نفّذتها أداة ذكاء اصطناعي قبل كل وثيقة |
| NFR-06 | 3-5-9 | splits.py، serving.py | test_splits.py::test_no_leakage_into_models؛ test_serving.py::test_future_events_resources_learners_change_nothing، test_future_information_changes_nothing_with_risk_and_clusters |
| NFR-07 | 3-5-9 | حارس 2014 | test_splits.py::test_2014_refused؛ test_serving.py::test_2014_refused؛ test_static_errors.py::test_confirmatory_locked_409_everywhere |
| NFR-08 | 3-7 | تحميل بيانات الطلاب؛ بناء المعاملات؛ العقود | test_contract_no_risk.py::test_no_outcome_field_anywhere، test_instructor_models_have_no_sensitive_fields؛ test_contract_json.py::test_instructor_json_keys_are_whitelisted_and_not_sensitive |
| NFR-09 | 3-7 | src/backend/schemas.py | test_contract_no_risk.py::test_learner_models_have_no_risk_or_sensitive_fields؛ test_contract_json.py::test_learner_json_has_no_forbidden_key_or_value |
| NFR-10 | 3-2-3 | ملف التجاهل في نظام الإصدارات | حالة نظيفة بعد التشغيل |
| NFR-11 | 3-6-1 | الشيفرة كلها | فحص الاستيرادات؛ test_static_errors.py::test_requirements_pin_runtime_packages |
| NFR-12 | 4-9 | الواجهة | قائمة تفحّص يدوية |
| NFR-13 | 4-9-3 | styles/، components/ | لقطات الاختبار الطرفي؛ test_labels_js.py::test_negative_numbers_use_real_minus_and_isolates |
| NFR-14 | [71] | الواجهة؛ src/backend/e2e/live-screenshots.js | بنود الجدول 4-12؛ الاختبار الطرفي (التركيز، والتخطي، وشجرة الوصول، وتباين النص، والعرض 360)؛ test_contrast.py |
| NFR-15 | [71] | styles/base.css | الاختبار الطرفي: لا تمرير أفقي عند 360 و375 و1440 بكسل؛ اللقطات |
| NFR-16 | 4-5-2 | schemas.py، types.ts | مقارنة مفاتيح الاستجابات بملفات المحاكاة في اختبارات العقود الحية (test_api_live.py)؛ فحص الأنواع |
| NFR-17 | 3-6-1 | src/backend/tests/، src/ml/tests/ | مرور كل الاختبارات |
| NFR-18 | 3-7 | labels.ts، instructor.ts، about.html | test_text.py::test_risk_label_is_relative_everywhere؛ test_api_live.py::test_meta_declares_unsafe_demo_and_score |
| NFR-19 | 4-8 | src/backend/errors.py | test_static_errors.py::test_unknown_api_path_404، test_post_405، test_validation_422، test_unknown_presentation_404 |
| NFR-20 | 4-1-2 | src/backend/__main__.py | test_static_errors.py::test_instructor_disabled، test_instructor_page_hidden_when_disabled |
| NFR-21 | 4-7 | build_artifacts.py | قياس حجم المعاملات |
| NFR-22 | NFR-14 | styles/tokens.css، base.css، components.css، labels.ts | test_contrast.py (خمسة اختبارات)؛ فحص تباين النص المرسوم في الاختبار الطرفي |

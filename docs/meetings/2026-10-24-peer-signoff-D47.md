🧑‍🔬 الزميل الباحث — توقيع مراجعة تنفيذ D-47 (شرط من شروط الوسم `freeze-03`، D-62)

**التاريخ:** 2026-10-24   **المرجع:** D-47 في `thesis-context.md`، وADR-004 §4-مكرر (شروطه الخمسة)
**المفحوص:** `confirmatory_student_ids()` في `src/ml/data.py` (السطور 301–335)، والاختبار `TestConfirmatoryIdRead` في `src/ml/tests/test_splits.py`، وسجل `results/access_log.jsonl`.
**لم أعدّل الكود ولم أنفّذ git.** أُجريت تجربة طفرة (mutation) في عملية بايثون مؤقتة دون كتابة ملف.

## التوقيع
**غير موافق في الحالة الحالية، ويتحول إلى موافق بإغلاق الملاحظة N1 وحدها** (نحو سطرين في `data.py` واختبار واحد). الدالة نفسها وسجلها واختبارها سليمة؛ المانع هو أن الشرط (4) من ADR («بقية الحاجز يرفض أي قراءة أخرى لـ2014») لا يتحقق لجداول أخرى كما هو موضح في N1.

## جدول الفحوص

| # | الفحص | النتيجة | الدليل |
|---|---|---|---|
| 1 | الأعمدة المقروءة هي `code_module, code_presentation, id_student` فقط | **ناجح** | ثابت `CONFIRMATORY_ID_COLUMNS` (data.py:303) يمرّر إلى `read(path, usecols=...)` (السطر 318)، وبعد القراءة تحقق صريح `set(df.columns) != ...` فيرفع `RuntimeError`. لا `date_registration` ولا `date_unregistration` ولا `studentInfo` ولا `studentVle` ولا `studentAssessment` في الدالة. وتُعيد `set[int]` فقط (17,259 معرّفاً؛ أعدتُ العدّ مستقلاً فطابق) |
| 2 | الدالة هي الاستثناء **الوحيد** من حاجز D-09؛ لا مسار آخر يقرأ 2014 | **ناجح جزئياً (N1)** | grep على `2014|CONF_PRESENTATIONS|allow_confirmatory|studentRegistration|read_csv|date_unregistration` في `src/ml`: مسارات `studentVle` و`studentAssessment` والعرض (`load_daily_events` و`load_student_assessment` و`load_presentation`) تُحرس بـ`assert_allowed`. وواجهات `serving.py` تستدعي `assert_allowed`. **لكن** `load_student_info()` (data.py:138) و`load_registrations()` (157) دالتان عامتان **بلا حارس** وتعيدان كل الصفوف: شغّلتُهما فأعادتا **19,064 صفاً من 2014**، منها `final_result` و`date_unregistration` (والأخير هو العمود الذي يمنعه D-47 لأنه نتيجة). `load_presentation` يرشّحهما بعد القراءة الكاملة، فلا تسرب في المسارات الحالية، لكن الحاجز يقوم على حسن استعمال المنادي لا على المنع |
| 3 | السجل يُكتب عند كل قراءة بالحقول الكافية | **ناجح** | كل استدعاء يضيف سطراً: `time, file, md5, columns, n_ids, commit, purpose` (data.py:329–338). السجل الفعلي يحوي سطرين (21:10:23 و21:49:28)، المعرّفات 17,259، وMD5 `ef06e3d5…` يطابق `md5sum` للملف الحالي ولـ`data/oulad_md5_reference.txt`، وكلا الـcommit حقيقيان في المستودع (`git cat-file` = commit). الاختبارات لا تلوّث السجل (تستعمل مساراً مؤقتاً؛ بقي سطرين بعد تشغيل 85 اختباراً) |
| 4 | الاختبار يفشل لو زادت الأعمدة | **ناجح (مع ملاحظة N2)** | طفرة: أضفتُ `date_unregistration` إلى `CONFIRMATORY_ID_COLUMNS` في الذاكرة وشغّلتُ `test_columns_and_log` فسقط (خطأ `KeyError` من القارئ الوهمي). وكذلك لو غُيّرت الثابتة فإن `assertEqual(calls, [(..., ("code_module","code_presentation","id_student"), {})])` بنص حرفي يفشل |
| 5 | تشغيل الاختبار | **ناجح** | `TestConfirmatoryIdRead`: 2/2 OK؛ `test_splits`: 13/13؛ وكل وحدات `src/ml/tests` (split/learners/metrics/models/signals/hybrid_stats/serving): **85/85 OK** (تعذّر `unittest discover` لغياب `__init__.py` في `tests/`، فشغّلتُ الوحدات بالاسم؛ ولا أثر على النتيجة) |
| 6 | الاستعمال محصور في H4-أ (شرط 2 من ADR) | **ناجح** | الاستدعاء الوحيد في `experiments/learner_analysis.py:204`، لحذف المتداخلين من تدريب 2013 |
| 7 | الذكر في §3.8 وقائمة التجميد (شرط 5) | **خارج نطاق الكود، يُتحقَّق منه في الوثيقة** | سبق في جولة التحقق أن الوثيقة 02 لا تذكر D-47؛ يتأكد المصمم أن النص الحرفي أُضيف (D-62 يشترطه) |

## ملاحظات

- **N1 (إلزامية للتوقيع):** حرس `load_student_info()` و`load_registrations()`، ويكفي أن تُرشّحا عند التحميل بعروض التطوير (كما تفعل `load_student_assessment` عبر `role="dev"`)، أو أن تأخذا `allow_confirmatory` وتستدعيا `assert_allowed`. ويُضاف إلى `test_rest_of_barrier_intact` تأكيد أن `load_student_info()` و`load_registrations()` لا تعيدان صفاً من 2014 (أو ترفعان `ConfirmatoryAccessError`). وبذلك يتحقق نص ADR «وأن بقية الحاجز يرفض أي قراءة أخرى لـ2014». ويبقى استثناء `confirmatory_student_ids` وحده.
- **N2 (مستحسنة):** الاختبار يفشل عند زيادة الأعمدة لكن عرضاً (قارئ وهمي يعيد `df[list(usecols)]` فيسقط بـKeyError). أنصح بقارئ وهمي يتجاهل `usecols` ويعيد أعمدة زائدة (مثلاً `date_unregistration`) ثم `assertRaises(RuntimeError)` ليختبر التحقق الصريح في السطر 319 مباشرة.
- **N3 (مستحسنة):** تسجيل القراءة يحدث بعد نجاحها فقط؛ المحاولة الفاشلة (خطأ أعمدة) لا تترك أثراً. يُفضَّل كتابة سطر «attempt» قبل القراءة أو تسجيل الفشل. كما أن حقل `commit` هو `HEAD` ولا يلتقط شجرة عمل غير مُودَعة (dirty)؛ يُستحسن حقل `dirty: true/false`.
- **N4 (للعلم):** حساب MD5 يقرأ بايتات الملف كله (كل الأعمدة) للبصمة فقط، وهذا لا مفر منه لما يشترطه ADR (MD5)، ولا تُحلَّل أعمدة أخرى. و`load_daily_events("dev")` تقرأ `studentVle.csv` كاملاً ثم ترشّح 2013 في الذاكرة؛ وهذا قديم ولا يخص D-47، وإن أُريد حاجز أشد فقراءة بالأجزاء (`chunksize`) بترشيح مبكر.
- **ما لم أفحصه:** صحة اشتقاق `overlap` داخل `learner_analysis.py` بعد الاستدعاء (حذف تسجيلات 2013 للمعرّفات المتداخلة) فقد راجعتُ سطر الاستدعاء فقط؛ وتطابق التقرير `learner_h4a_summary` مع الحذف يُراجَع ضمن تقرير الحساسية.

## شرط التحويل إلى «موافق»
إغلاق N1 (حرس الجدولين + اختبار)، ثم إعادة تشغيل `src.ml.tests.test_splits` وإرسال commit الإصلاح؛ وأوقّع مباشرة بعدها دون إعادة فحص الدالة نفسها.


**تحديث 2026-10-25:** أُغلقت N1–N3 (108 اختباراً ناجحاً، وثلاث طفرات تُسقط الاختبار)، وأُقرّ الجزء (أ) D-47 نهائياً؛ أما ش8 كاملاً فقراري في `docs/meetings/peer-signoff-freeze03.md`: لا أوقّع حتى اكتمال التشغيل الجاف وحسم ح2 وإغلاق م1.

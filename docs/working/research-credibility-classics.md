# التحقق من مصداقية المراجع الكلاسيكية [39]–[47]

المصدر المدقَّق: `docs/working/references-bibliography.md`، قسم "مراجع كلاسيكية داعمة". الأداة: WebSearch فقط (مواقع الناشرين وdoi.org غير متاحة للجلب المباشر). التاريخ: 2026-10-24.

ملاحظة: الـDOI يُكتب هنا فقط إن ظهر في نتيجة بحث. ما لم يظهر يُعلَّم في الجدول.

| # | المرجع كما كُتب | ما وجدته (المصدر/الرابط) | مطابق؟ |
|---|---|---|---|
| 39 | Y. Hu, Y. Koren, C. Volinsky، ICDM 2008، pp. 263–272، doi 10.1109/ICDM.2008.22 | المؤلف الأول هو Yifan Hu (الحرف Y صحيح). الصفحات 263–272 والـDOI مذكوران في مراجع مقالات ومقررات: https://doi.org/10.1109/ICDM.2008.22 . مكان المؤتمر (Pisa) لم يظهر في النتائج. | ✅ مطابق (مكان المؤتمر غير مؤكَّد بالبحث) |
| 40 | S. Rendle et al.، UAI 2009، pp. 452–461 | المؤلفون والعنوان والمؤتمر مطابقون: https://www.auai.org/uai2009/papers/UAI2009_0139_48141db02b9f0b02bc7158819ebfa2c7.pdf . **تعارض في الصفحات:** BibTeX في mlanthology يعطي 452–461 (https://mlanthology.org/uai/2009/rendle2009uai-bpr/)، بينما سجل PMLR يعطي 460–469 (https://proceedings.mlr.press/r7/rendle09a.html). لم أتمكن من حسم أيهما صحيح. | ❓ الصفحات متعارضة؛ يُحسم من ملف PMLR أو وثيقة UAI الرسمية |
| 41 | B. Hidasi et al.، ICLR 2016، San Juan | المؤلفون والعنوان مطابقون: https://mlanthology.org/iclr/2016/hidasi2016iclr-session و https://arxiv.org/pdf/1511.06939 . مكان المؤتمر لم يظهر في النتائج (معروف من الذاكرة فقط). | ✅ مطابق (المكان غير مؤكَّد بالبحث) |
| 42 | D. Jannach, M. Ludewig، RecSys 2017، Como، pp. 306–310، doi 10.1145/3109859.3109872 | المؤلفون والمؤتمر والمكان مطابقون: https://web-ainf.aau.at/pub/jannach/files/RecSys2017.pdf . ملخص نتائج البحث ذكر أن سجل ACM يعطي الصفحات 306–310 والـDOI المذكور. | ✅ مطابق |
| 43 | M. Ludewig, D. Jannach، UMUAI، vol. 28, no. 4–5، pp. 331–390، 2018، doi 10.1007/s11257-018-9209-6 | المؤلفون والمجلة والسنة والمجلد مطابقة: https://arxiv.org/abs/1803.09587 و https://eldorado.tu-dortmund.de/items/caa7d2e3-7cf4-4cc1-91f3-fdf3014e6454/full . إحدى الإحالات تذكر العدد 4 فقط (لا 4–5). الصفحات 331–390 والـDOI لم يظهرا في النتائج. | ❓ لم أجد الصفحات ولا الـDOI؛ العدد (4 أم 4–5) يحتاج تحققاً |
| 44 | M. Ferrari Dacrema, P. Cremonesi, D. Jannach، RecSys 2019، Copenhagen، pp. 101–109، doi 10.1145/3298689.3347058 | المؤلفون والمؤتمر والمكان والـDOI مطابقة (الـDOI من ملخص نتائج البحث: https://doi.org/10.1145/3298689.3347058 ). الورقة على arXiv: https://arxiv.org/abs/1907.06902 . الصفحات 101–109 لم تُؤكَّد. | ✅ مطابق (الصفحات غير مؤكَّدة بالبحث) |
| 45 | K. Cho et al.، EMNLP 2014، Doha، pp. 1724–1734، doi 10.3115/v1/D14-1179 | مطابق تماماً لسجل ACL Anthology: https://aclanthology.org/D14-1179 (المؤلفون السبعة والصفحات والمكان والـDOI). | ✅ مطابق |
| 46 | J. Kuzilek, M. Hlosta, Z. Zdrahal، Sci. Data، vol. 4، Art. no. 170171، 2017، doi 10.1038/sdata.2017.171 | المؤلفون والمجلة والسنة والـDOI مطابقة: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5704676/ . المجلد 4 ورقم المقالة 170171 لم يظهرا صراحة في النتائج، لكنهما متسقان مع الـDOI. | ✅ مطابق (المجلد ورقم المقالة غير مذكورين صراحة) |
| 47 | W. Krichene, S. Rendle، KDD 2020، pp. 1748–1757، doi 10.1145/3394486.3403226 | المؤلفون والمؤتمر مطابقون (ورقة Google Research، جائزة أفضل ورقة): https://research.google/pubs/on-sampled-metrics-for-item-recommendation/ . الصفحات والـDOI لم يظهرا في النتائج. | ❓ الصفحات والـDOI غير مؤكَّدين |

## الملخص

- ✅ مطابقة: [39]، [41]، [42]، [44]، [45]، [46] (بعضها مع ملاحظات غير حاسمة موضّحة في الجدول).
- ⚠️ تحتاج تصحيحاً: لا يوجد تصحيح مؤكَّد.
- ❓ لم تُحسم: [40] (تعارض الصفحات)، [43] (الصفحات والـDOI والعدد)، [47] (الصفحات والـDOI).

## السطور البيبليوغرافية النهائية (IEEE) للمراجع ✅

[39] Y. Hu, Y. Koren, and C. Volinsky, "Collaborative filtering for implicit feedback datasets," in *Proc. 8th IEEE Int. Conf. Data Mining (ICDM)*, Pisa, Italy, 2008, pp. 263–272, doi: 10.1109/ICDM.2008.22.

[41] B. Hidasi, A. Karatzoglou, L. Baltrunas, and D. Tikk, "Session-based recommendations with recurrent neural networks," in *Proc. 4th Int. Conf. Learning Representations (ICLR)*, San Juan, Puerto Rico, 2016.

[42] D. Jannach and M. Ludewig, "When recurrent neural networks meet the neighborhood for session-based recommendation," in *Proc. 11th ACM Conf. Recommender Systems (RecSys)*, Como, Italy, 2017, pp. 306–310, doi: 10.1145/3109859.3109872.

[44] M. Ferrari Dacrema, P. Cremonesi, and D. Jannach, "Are we really making much progress? A worrying analysis of recent neural recommendation approaches," in *Proc. 13th ACM Conf. Recommender Systems (RecSys)*, Copenhagen, Denmark, 2019, pp. 101–109, doi: 10.1145/3298689.3347058.

[45] K. Cho, B. van Merriënboer, C. Gulcehre, D. Bahdanau, F. Bougares, H. Schwenk, and Y. Bengio, "Learning phrase representations using RNN encoder–decoder for statistical machine translation," in *Proc. 2014 Conf. Empirical Methods in Natural Language Processing (EMNLP)*, Doha, Qatar, 2014, pp. 1724–1734, doi: 10.3115/v1/D14-1179.

[46] J. Kuzilek, M. Hlosta, and Z. Zdrahal, "Open University Learning Analytics dataset," *Sci. Data*, vol. 4, Art. no. 170171, 2017, doi: 10.1038/sdata.2017.171.

(لم تُكتب أسطر IEEE للمراجع ❓ [40] و[43] و[47] حتى تُحسم صفحاتها.)

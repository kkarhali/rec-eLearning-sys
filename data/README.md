# بيانات الرسالة

| المجموعة | المسار المحلي | المصدر الرسمي (للاستشهاد) | الترخيص | التحقق |
|---|---|---|---|---|
| **OULAD** — Open University Learning Analytics Dataset | `data/raw/oulad/` (7 جداول؛ `studentVle.csv` يُعاد بناؤه من 8 أجزاء) | Kuzilek, Hlosta & Zdrahal, *Scientific Data* 4:170171 (2017) — https://analyse.kmi.open.ac.uk/open-dataset | CC BY 4.0 | MD5 لكل ملف مقابل `oulad_md5_reference.txt` + عدد الصفوف المنشور (10,655,280) |
| **MARS** — Mandarine Academy Recommender System dataset | `data/raw/mars/` (EN/FR: implicit, explicit, items, users) | Mandarine Academy — https://mandarine.academy/mars-dataset/ ، Harvard Dataverse doi:10.7910/DVN/BMY3UD | يُتحقَّق (انظر تقرير البيانات) | تطابق بايتي للملفات EN بين مرآتين مستقلتين |

المجلد `data/raw/` **غير مضمَّن في git** (الحجم ~400 MB). لإعادة التحميل:

```bash
bash data/download.sh      # يستنسخ المرايا من GitHub ويتحقق من MD5
```

لماذا مرايا GitHub؟ مواقع البيانات الرسمية محجوبة في بيئة العمل البحثية؛ المرايا المستخدمة موثّقة في `docs/working/research-datasets.md` مع سجل محاولات التحميل والتحقق، والاستشهاد في الرسالة يكون بالمصدر الرسمي.

## بنية OULAD المختصرة
- `studentInfo` (32,593 طالباً × 12)، `studentRegistration`، `courses` (22 عرضاً لـ7 مقررات)، `assessments` (206)، `studentAssessment` (173,912)
- `vle` (6,364 مورداً: `id_site`, `activity_type`, `week_from/to`)، `studentVle` (10,655,280 سجلاً: `id_student`, `id_site`, `date`, `sum_click`)
- ملاحظة تصميمية: `id_site` خاص بكل عرض (presentation)؛ لا هوية مورد مشتركة بين العروض.

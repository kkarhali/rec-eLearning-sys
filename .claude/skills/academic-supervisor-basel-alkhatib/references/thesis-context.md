# سياق الرسالة (يُحدَّث مع تقدّم المشروع)

## بطاقة الرسالة
- **الجامعة:** الجامعة الافتراضية السورية (SVU) — ماجستير علوم الوب (MWS)
- **المشرف:** د. باسل الخطيب — t_balkhatib@svuonline.org
- **الطالب:** كنان محمد قرحالي — kinan_198005@svuonline.org
- **العنوان (ع):** نظام توصية للتعليم الإلكتروني القائم على تحليل سلوك المستخدم
- **العنوان (E):** A recommendation system for e-learning based on user behavior analysis
- **الكلمات المفتاحية:** User information, User history logs, Content-Based Filtering (CBF), Collaborative Filtering (CF), Context-Aware Recommendation, RNN, CNN, RBFNN

## خلاصة خطة البحث (المصدر: `deliverables/00-research-plan/` و `docs/working/00-research-plan.md`)
- **المشكلة:** صعوبة اختيار المتعلم للمواد المناسبة في بيئات التعليم الإلكتروني، وضعف التوجيه الشخصي الفوري.
- **الهدف:** تصميم وتطوير نظام توصية يستند إلى تحليل سلوك المستخدم (سجلات التصفح، التفاعلات، التفضيلات) باستخدام تعلّم الآلة، مع واجهة مستخدم.
- **الأهداف الفرعية:** (1) تحليل سلوك المستخدم (2) نماذج تحليل البيانات: تصنيف/تجميع/تنبؤ (3) نموذج التوصية المدرك للسياق والتفضيلات (4) تقييم الأداء والتحسين.
- **التقانات المقترحة في الخطة:** Python، TensorFlow/Keras، Scikit-learn، Random Forest، شبكات عصبونية عميقة.
- **المراجع في الخطة:** 9 مراجع (2015–2023) تشمل: توصية الأغاني بالجلسة (RNN)، توصية دورات MOOC بـ CNN، UI-RS (CBF + D-S + RBFNN)، AMRE (تجميع خوارزميات)، نظام توصية تعلّم إلكتروني بـ Random Forest، ملفات تعريف الطلاب بسلوكهم (Jaccard)، CodERS الهجين، نظام هجين تفاعلي، نظام تعاوني هجين بملفات المستخدم.
- **المراجع في المستودع:** 38 ملف PDF في `references/` (9 مسماة + 29 بترميز S-xxxx، معظمها 2016–2026 عن توصية في التعليم الإلكتروني). النصوص المستخرجة في `docs/working/reftext/`.

## قيود بيئة العمل (مهمة جداً لأي قرار تقني)
- **لا يمكن تثبيت حزم جديدة**: pip و npm محجوبان. المتاح في Python: numpy, pandas, starlette, uvicorn, pydantic, requests, openpyxl, python-docx, python-pptx, pypdf. **غير متاح:** scikit-learn, scipy, matplotlib, tensorflow, torch, fastapi.
- **المتاح في Node (عالمي):** typescript, ts-node, docx, playwright (+Chromium), eslint, prettier, serve/http-server. لا يمكن تثبيت React أو أي حزمة npm.
- **الشبكة:** GitHub (clone) متاح؛ مواقع الناشرين (doi.org, IEEE, Springer, Semantic Scholar, Crossref)، ومستودعات البيانات (UCI, Kaggle, Zenodo, HuggingFace, موقع OULAD) **محجوبة** للتحميل المباشر. البحث عبر أداة WebSearch متاح.
- **الأدوات المتاحة للمخرجات:** pandoc، LibreOffice، pdftotext/pdftoppm، ImageMagick convert، Playwright لتصيير SVG/HTML إلى PNG.
- **الأثر:** الخوارزميات تُنفَّذ بـ numpy/pandas (CF/kNN/MF/ALS/BPR/CBF/Markov/Session-kNN كلها ممكنة؛ أي RNN يجب أن يُكتب يدوياً أو يُستبدل ببديل مبرَّر)، والبيانات يجب أن تكون قابلة للتحميل من GitHub.

## سجل القرارات (يُضاف إليه تلقائياً)
- راجع `docs/decisions/` و `docs/meetings/` — كل قرار معتمد موجود هناك مع تاريخه.

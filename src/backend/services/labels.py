"""أسماء عربية ومعرّفات المكوّنات والملامح (طبقة العرض فوق معرّفات ``serving``)."""
from __future__ import annotations

# معرّفات serving -> معرّفات الواجهة (mock/*.json و``labels.ts``: ألوان وأرقام المكوّنات (1)-(7))
COMPONENT_IDS = {
    "B3_RecentPop": "recent_pop", "B7_WRMF": "wrmf", "B4_ItemKNN": "item_knn", "B5_SKNN": "sknn",
    "B6_Markov": "markov", "GRU_lite": "gru", "B9_CBF": "cbf", "C6_AssessProx": "assess_prox",
    "C7_ClusterPop": "cluster_pop",
}
COMPONENT_LABELS = {
    "B3_RecentPop": "Recent-Pop (1)", "B7_WRMF": "WRMF (2)", "B4_ItemKNN": "Item-kNN (3)", "B5_SKNN": "SKNN (4)",
    "B6_Markov": "Markov (4)", "GRU_lite": "GRU-lite", "B9_CBF": "CBF (5)", "C6_AssessProx": "قرب التقييم (6)",
    "C7_ClusterPop": "شعبية العنقود (7)",
}


def comp_id(serving_id: str) -> str:
    return COMPONENT_IDS.get(serving_id, serving_id.lower())


def comp_label(serving_id: str) -> str:
    return COMPONENT_LABELS.get(serving_id, serving_id)


TYPES_AR = {
    "oucontent": "محتوى", "quiz": "اختبار قصير", "forumng": "منتدى", "resource": "مورد", "subpage": "صفحة فرعية",
    "homepage": "الصفحة الرئيسية", "url": "رابط", "page": "صفحة", "glossary": "مسرد", "ouwiki": "ويكي",
    "oucollaborate": "تعاون", "questionnaire": "استبيان", "dataplus": "بيانات", "folder": "مجلد",
    "dualpane": "لوحة مزدوجة", "externalquiz": "اختبار خارجي", "ouelluminate": "جلسة مباشرة",
    "repeatactivity": "نشاط متكرر", "sharedsubpage": "صفحة فرعية مشتركة",
}

_FEATURE_AR = {
    "active_days": "الأيام النشطة", "gap_sd": "انحراف الفجوات", "first_day": "يوم أول وصول",
    "date_registration": "يوم التسجيل", "total_clicks": "مجموع النقرات",
    "on_time_ratio": "الالتزام بالمواعيد", "mean_score": "متوسط الدرجات",
}


def feature_ar(name: str) -> str:
    if name.startswith("share_"):
        return "حصة " + name[6:]                 # كما في الأمثلة: «حصة quiz»
    return _FEATURE_AR.get(name, name)


# عبارات وصف العنقود بقاعدة حتمية من المركز (R-C3): (انحراف موجب، انحراف سالب)
_PHRASES = {
    "active_days": ("أيام نشطة كثيرة", "أيام نشطة قليلة"),
    "gap_sd": ("نشاط متقطع", "نشاط منتظم"),
    "first_day": ("بدء متأخر", "بدء مبكر"),
    "date_registration": ("تسجيل متأخر", "تسجيل مبكر"),
}


def phrase(feature: str, z: float) -> str:
    if feature.startswith("share_"):
        t = feature[6:]
        ar = TYPES_AR.get(t, t)
        return f"ميل إلى {ar}" if z > 0 else f"قلة {ar}"
    pos, neg = _PHRASES.get(feature, (_FEATURE_AR.get(feature, feature) + " مرتفع", _FEATURE_AR.get(feature, feature) + " منخفض"))
    return pos if z > 0 else neg

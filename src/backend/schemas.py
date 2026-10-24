"""عقود الاستجابة (pydantic) المطابقة حرفياً لملفات ``src/frontend/mock/*.json`` و``src/frontend/src/types.ts``.

الفصل بين مسارات المتعلم والمدرّس بالعقد (D-22، NFR-09): نماذج المتعلم (``LEARNER_MODELS``) لا تحوي أي حقل
خطر أو عنقود أو سمة حساسة أو ``final_result``، ويفحص ذلك ``tests/test_contract_no_risk.py`` تكرارياً.
"""
from __future__ import annotations

import re
from typing import Annotated, Generic, Literal, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator

REG_RE = re.compile(r"^([A-G]{3}_20(?:13|14)[BJ])-(\d+)$")
T = TypeVar("T")
RISK_LABEL_AR = "درجة خطر نسبية غير معايَرة"
ACCESS_NOTICE_AR = "عرض توضيحي بلا أمان وصول"


class Out(BaseModel):
    """أساس نماذج الاستجابة: NaN/Inf تُسلسَل null ولا تكسر JSON."""
    model_config = ConfigDict(ser_json_inf_nan="null")


# ------------------------------------------------------------------ عام
class ErrorDetail(Out):
    code: str
    message: str
    details: dict = {}


class ErrorBody(Out):
    error: ErrorDetail


class Health(Out):
    status: str
    run_id: str
    uptime_s: int
    instructor_enabled: bool = True
    warm: dict | None = None


class ComponentInfo(Out):
    id: str
    label: str
    weight: float


class Meta(Out):
    schema_version: int
    version: str
    run_id: str
    git_commit: str
    git_dirty: bool = False
    freeze_tag: str | None = None
    data_fingerprint: str
    data_files: dict[str, str] = {}
    components: list[ComponentInfo]
    snapshot_grid: list[int]
    cutoffs: list[int]
    risk_cutoffs: list[int]
    presentations: list[str]
    instructor_enabled: bool = True
    bind_host: str = "127.0.0.1"
    access_notice: str = ACCESS_NOTICE_AR
    risk_score: dict = {}
    frozen_at_commit: str | None = None
    notes: list[str] = []


class AssessmentInfo(Out):
    type: str
    day: int | None
    weight: float | None


class Presentation(Out):
    id: str
    role: Literal["dev", "confirm"]
    status: Literal["published", "locked"]
    length_days: int
    snapshots: list[int]
    cutoffs: list[int]
    registrations: int
    label_ar: str
    assessments: list[AssessmentInfo]


class PresentationList(RootModel[list[Presentation]]):
    pass


class RegistrationSummary(Out):
    registration: str
    id_student: int
    date_registration: int | None
    # D-70: قائمة بيضاء؛ لا date_unregistration ولا final_result ولا أي حالة مشتقة من مستقبل التسجيل.
    # status بلا day = "ok"؛ ومع day: withdrawn إن انسحب ≤ day، وno_history إن لا نشاط ≤ day.
    status: Literal["ok", "no_history", "withdrawn"]


class Page(Out, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


# ------------------------------------------------------------------ مسارات المتعلم
class NextAssessment(Out):
    type: str
    day: int
    days_ahead: int


class RecContext(Out):
    week: int
    next_assessment: NextAssessment | None
    active_days_to_date: int


class RecItem(Out):
    rank: int
    id_site: int
    activity_type: str
    relevance: float                 # درجة الهجين للتوصية (D-70: لا مفتاح score في مسارات المتعلم)
    contributions: dict[str, float]
    reason: str
    reason_secondary: str | None


class Provenance(Out):
    run_id: str
    role: str
    model_cut: int | None            # D-49: موجود دائماً؛ null قبل أول قطع (اليوم < 70)


class RecommendationResponse(Out):
    registration: str
    presentation: str
    id_student: int
    requested_day: int
    snapshot_day: int
    task: Literal["A", "B"]
    status: Literal["ok", "no_history", "withdrawn"]
    known_learner: bool
    note: str | None
    context: RecContext
    components: list[ComponentInfo]
    items: list[RecItem]
    provenance: Provenance


class CountEvidence(Out):
    type: Literal["count"] = "count"
    n: int
    window: int
    scope: Literal["all", "similar"] = "all"


class ItemEvidence(Out):
    type: Literal["item"] = "item"
    id_site: int
    activity_type: str
    days: int
    last_day: int


class AssessmentEvidence(Out):
    type: Literal["assessment"] = "assessment"
    assessment_type: str
    days_ahead: int


Evidence = Annotated[Union[CountEvidence, ItemEvidence, AssessmentEvidence], Field(discriminator="type")]


class ExplComponent(Out):
    id: str
    label: str
    weight: float
    r_tilde: float
    contribution: float
    evidence: Evidence | None
    sentence: str


class ExplanationDetail(Out):
    registration: str
    id_site: int
    activity_type: str
    task: Literal["A", "B"]
    day: int
    snapshot_day: int
    relevance: float
    components: list[ExplComponent]
    notes: list[str] = []


class HistoryEvent(Out):
    day: int
    id_site: int
    activity_type: str
    clicks: int


class DailyClicks(Out):
    day: int
    clicks: int


class LearnerHistory(Out):
    registration: str
    day: int
    window: int
    active_days: int
    daily: list[DailyClicks]
    recent: list[HistoryEvent]


# ------------------------------------------------------------------ مسارات المدرّس
class RiskRow(Out):
    score: float                    # D-65: درجة خطر نسبية غير معايَرة (ليست احتمالاً)
    cut_day: int
    threshold: float
    above_threshold: bool
    provenance: str
    top_factor: str


class RiskFactor(Out):
    name: str
    wz: float


class RiskDetail(RiskRow):
    label_ar: str = RISK_LABEL_AR
    factors: list[RiskFactor]


class ClusterRef(Out):
    id: int
    label: str


class InstructorLearnerRow(Out):
    registration: str
    cluster: ClusterRef
    active_days: int
    last_access_day: int | None
    on_time: str
    risk: RiskRow | None


class LearnersPage(Page[InstructorLearnerRow]):
    provenance: Provenance            # D-49 (6)


class Kpis(Out):
    active_learners: int              # الفوج الذي له يوم نشط واحد على الأقل حتى t
    cohort_size: int                  # الفوج: مسجَّلون ≤ t ولم ينسحبوا ≤ t (= مجموع أحجام العناقيد)
    median_active_days: float
    catalogue_size: int
    coverage_at_10: float
    share_above_threshold: float | None


class ProfileSummary(Out):
    name: str
    p25: float
    median: float
    p75: float
    unit: str


class HistBin(Out):
    lo: float
    hi: float
    count: int


class OverviewRisk(Out):
    label_ar: str = RISK_LABEL_AR
    cut_day: int
    threshold: float
    provenance: str
    histogram: list[HistBin]


class TypeShare(Out):
    activity_type: str
    catalogue_share: float
    recs_share: float


class Coverage(Out):
    at_10: float
    catalogue_size: int
    covered_items: int
    by_type: list[TypeShare]


class InstructorOverview(Out):
    presentation: str
    requested_day: int
    snapshot_day: int
    kpis: Kpis
    profile_summary: list[ProfileSummary]
    risk: OverviewRisk | None
    coverage: Coverage
    provenance: Provenance


class TopFeature(Out):
    name: str
    z: float


class ClusterInfo(Out):
    id: int
    label_ar: str
    size: int
    top_features: list[TopFeature]


class ClusterQuality(Out):
    silhouette: float
    dbi: float
    ari: float | None = None         # ثبات البذور من results/dev2013/learner_clusters.csv؛ null إن غاب العرض منه


class ClusterPoint(Out):
    x: float
    y: float
    cluster: int


class ClusterSet(Out):
    presentation: str
    requested_day: int
    snapshot_day: int
    k: int
    cluster_day: int = 56            # لقطة العناقيد: تُحسب مرة واحدة عند اليوم 56 وتُطبَّق على ما بعده
    unstable: bool
    unstable_reason: str | None = None
    quality: ClusterQuality
    clusters: list[ClusterInfo]
    points: list[ClusterPoint]
    provenance: Provenance            # D-49 (6)


class ProfileRow(Out):
    name: str
    value: float
    median: float
    z: float


class TopRec(Out):
    rank: int
    id_site: int
    activity_type: str
    reason: str


class InstructorLearnerDetail(Out):
    registration: str
    day: int
    snapshot_day: int
    cluster: ClusterRef
    risk: RiskDetail | None
    profile: list[ProfileRow]
    top_recs: list[TopRec]
    withdrawn_day: int | None
    provenance: Provenance            # D-49 (6): model_cut في كل استجابة


LEARNER_MODELS = (Health, Meta, Presentation, RegistrationSummary, RecommendationResponse, ExplanationDetail,
                  LearnerHistory)
INSTRUCTOR_MODELS = (InstructorOverview, ClusterSet, LearnersPage, InstructorLearnerRow, InstructorLearnerDetail)
# D-49 (6): كل استجابة تعتمد على اليوم t وناتج النموذج تحمل provenance.model_cut
PROVENANCE_MODELS = (RecommendationResponse, InstructorOverview, ClusterSet, LearnersPage, InstructorLearnerDetail)

# ------------------------------------------------------------------ مدخلات (استعلامات)
LEARNER_SORTS = ("risk", "reg", "cluster", "active_days", "last_access", "on_time")


class In(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


def _registration(v: str) -> str:
    if not REG_RE.match(v):
        raise ValueError("صيغة التسجيل المتوقعة: FFF_2013J-28400")
    return v


class RegistrationsIn(In):
    presentation: str = Field(pattern=r"^[A-G]{3}_20(13|14)[BJ]$")
    q: str = Field("", max_length=12)
    limit: int = Field(100, ge=1, le=100)
    offset: int = Field(0, ge=0)
    day: int | None = Field(None, ge=0, le=400)


class RecommendationsIn(In):
    registration: str
    day: int = Field(ge=0, le=400)
    k: int = Field(10, ge=1, le=20)
    task: Literal["A", "B"] = "A"

    @field_validator("registration")
    @classmethod
    def _reg(cls, v: str) -> str:
        return _registration(v)


class ExplanationIn(In):
    day: int = Field(ge=0, le=400)
    task: Literal["A", "B"] = "A"


class HistoryIn(In):
    day: int = Field(ge=0, le=400)
    window: int = Field(28, ge=1, le=120)


class OverviewIn(In):
    presentation: str = Field(pattern=r"^[A-G]{3}_20(13|14)[BJ]$")
    day: int = Field(ge=0, le=400)


class LearnersIn(OverviewIn):
    cluster: int | None = Field(None, ge=0, le=50)
    risk: Literal["all", "above"] = "all"
    sort: str = "-risk"
    limit: int = Field(100, ge=1, le=500)
    offset: int = Field(0, ge=0)

    @field_validator("sort")
    @classmethod
    def _sort(cls, v: str) -> str:
        key = v[1:] if v.startswith("-") else v
        if key not in LEARNER_SORTS:
            raise ValueError("sort يجب أن يكون أحد: " + "، ".join(LEARNER_SORTS) + " (مسبوقاً بـ- للتنازلي)")
        return v


class LearnerIn(In):
    day: int = Field(ge=0, le=400)


def parse_in(model: type[In], params: dict) -> In:
    """تحقق pydantic من معاملات الاستعلام؛ ValidationError يتحول إلى 422 في طبقة المسارات."""
    return model.model_validate(params)


def parse_registration(reg: str) -> tuple[str, int]:
    """(العرض، id_student) من ``FFF_2013J-28400``؛ الصيغة الخاطئة 422 validation_error."""
    from .errors import ApiError
    m = REG_RE.match(reg)
    if not m:
        raise ApiError(422, "validation_error", details={"errors": [
            {"field": "registration", "reason": "صيغة التسجيل المتوقعة: FFF_2013J-28400", "type": "value_error"}]})
    return m.group(1), int(m.group(2))

"""إعدادات الخلفية (قيم افتراضية قابلة للتجاوز من سطر الأوامر أو من الاختبارات)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# قطوع النموذج لخدمة التوصية (src.ml.splits.CUTS) وقطوع نموذج الخطر/العناقيد (artifacts/*/risk_<tc>.json)
MODEL_CUTS = (70, 126, 182)
RISK_CUTS = (28, 56, 112)
CLUSTER_DAY = 56
IDLE_DAYS = 14                                       # «بلا نشاط 14 يوماً»: لا وصول ≤ t، أو t − آخر وصول ≥ 14 (FR-32، ب-8)
SNAPSHOT_GRID = tuple(range(28, 267, 14))          # أيام الانتقال السريع والتسخين؛ الحساب نفسه دائماً عند اليوم المطلوب

DEFAULT_PRESENTATION = "FFF_2013J"
DEFAULT_DAY = 75
# أيام العرض الرئيسية: الافتراضي، وأول عنقدة (56)، والقطوع الثلاثة، وقطع الخطر 112 (D-68)
WARM_DAYS = (DEFAULT_DAY, 56, 70, 112, 126, 182)
LOCKED_LISTED = ("BBB_2014J",)                       # العرض المقفل الذي يُدرَج للتمثيل؛ كل عروض 2014 تعيد 409


@dataclass
class Settings:
    host: str = "127.0.0.1"
    port: int = 8000
    instructor_enabled: bool = True                  # --no-instructor يعطّله (R-C5)
    warm: bool = False                               # --warm: تسخين في خيط خلفي عند الإقلاع
    warm_presentation: str = DEFAULT_PRESENTATION
    warm_days: tuple[int, ...] = WARM_DAYS
    default_presentation: str = DEFAULT_PRESENTATION
    frontend_dist: Path = REPO_ROOT / "src" / "frontend" / "dist"
    md5_reference: Path = REPO_ROOT / "data" / "oulad_md5_reference.txt"
    frozen_path: Path | None = None                  # None: ما يستعمله serving.Engine
    rec_cache_size: int = 1024                       # ذاكرة LRU لقوائم التوصية (عرض، تسجيل، يوم، مهمة)
    snapshot_cache_size: int = 6                     # ذاكرة LRU للقطات لوحة المدرّس (عرض، يوم)
    max_day: int = 400
    log_level: str = "info"
    extra: dict = field(default_factory=dict)

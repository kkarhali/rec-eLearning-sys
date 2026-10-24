"""طبقة الوصول إلى البيانات: كل شيء يُقرأ عبر ``serving.Engine`` (المصدر الوحيد للحساب) وملفات النتائج الصغيرة.

لا تُخزَّن هنا حالة متعلم ولا توصية؛ ما يُبنى فهارس قراءة فقط (أحداث كل عرض مرتبة بالمتعلم).
عروض 2014 لا تُحمَّل أبداً (D-09): ``check_presentation`` يرفع 409 قبل أي قراءة.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import SCHEMA_VERSION, __version__
from .errors import ApiError
from .settings import REPO_ROOT, Settings

DEV = None  # يُملأ كسولاً من src.ml.data


def _data():
    from src.ml import data
    return data


@dataclass
class PIndex:
    """فهرس قراءة لعرض: أحداث مرتبة بـid_student، وتسجيلات، وأنواع الموارد."""
    name: str
    length: int
    events: pd.DataFrame
    ids: np.ndarray
    reg: pd.DataFrame            # فهرس id_student: date_registration, date_unregistration
    item_type: dict
    with_events: set
    assessments: pd.DataFrame

    def student_events(self, student: int, day: int | None = None) -> pd.DataFrame:
        lo = int(np.searchsorted(self.ids, student, "left"))
        hi = int(np.searchsorted(self.ids, student, "right"))
        ev = self.events.iloc[lo:hi]
        return ev if day is None else ev[ev["date"].to_numpy() <= day]


class Repository:
    def __init__(self, settings: Settings, engine=None):
        self.settings = settings
        self._engine = engine
        self.lock = threading.RLock()
        self._index: dict[str, PIndex] = {}
        self._catalog: dict | None = None
        self._meta_cache: dict | None = None

    # ------------------------------------------------------------ المحرّك
    @property
    def engine(self):
        if self._engine is None:
            from src.ml import serving
            self._engine = serving.engine()
        return self._engine

    @property
    def run_id(self) -> str:
        return f"replay-dev2013-{self.git()['commit'][:10]}"

    # ------------------------------------------------------------ الإتاحة
    def check_presentation(self, name: str) -> str:
        """يعيد الدور (dev). 404 لعرض غير معروف؛ 409 لعروض 2014 (D-09)."""
        d = _data()
        if name in d.CONF_PRESENTATIONS:
            raise ApiError(409, "confirmatory_locked")
        if name not in d.DEV_PRESENTATIONS:
            raise ApiError(404, "presentation_not_found", details={"presentation": name})
        return "dev"

    def require_artifacts(self) -> None:
        frozen = getattr(self.engine, "frozen", None)
        if not frozen or "components" not in frozen:
            raise ApiError(503, "artifacts_missing")

    # ------------------------------------------------------------ فهارس العروض
    def index(self, name: str) -> PIndex:
        self.check_presentation(name)
        ix = self._index.get(name)
        if ix is not None:
            return ix
        with self.lock:
            ix = self._index.get(name)
            if ix is None:
                p = self.engine.presentation(name)
                ev = p.events
                ids = ev["id_student"].to_numpy()
                if not (np.diff(ids) >= 0).all():
                    ev = ev.sort_values(["id_student", "date"], kind="stable").reset_index(drop=True)
                    ids = ev["id_student"].to_numpy()
                reg = p.registrations.set_index("id_student")[["date_registration", "date_unregistration"]]
                it = dict(zip(p.items["id_site"].astype(int), p.items["activity_type"].astype(str)))
                ix = PIndex(name, int(p.length), ev, ids, reg, it, set(np.unique(ids).tolist()), p.assessments)
                self._index[name] = ix
        return ix

    def registration_row(self, name: str, student: int) -> pd.Series:
        ix = self.index(name)
        if student not in ix.reg.index:
            raise ApiError(404, "registration_not_found", details={"registration": f"{name}-{student}"})
        return ix.reg.loc[student]

    def check_day(self, name: str, day: int) -> None:
        length = self.catalog()["presentations"][name]["length_days"]
        if day < 0 or day > length:
            raise ApiError(422, "day_out_of_range", details={"min_day": 0, "max_day": length, "day": day})

    # ------------------------------------------------------------ كتالوج العروض (بلا أحداث؛ سريع)
    def catalog(self) -> dict:
        """أطوال وتقييمات وعدد تسجيلات عروض التطوير فقط؛ تُرشَّح صفوف 2014 فور القراءة ولا تُحفظ."""
        if self._catalog is not None:
            return self._catalog
        with self.lock:
            if self._catalog is None:
                d = _data()
                dev = set(d.DEV_PRESENTATIONS)
                reg = d.load_registrations()
                reg = reg[reg["presentation"].isin(dev)]
                counts = reg.groupby("presentation").size().to_dict()
                courses = d.load_courses()
                courses = courses[courses["presentation"].isin(dev)].set_index("presentation")["module_presentation_length"]
                asm = d.load_assessments()
                asm = asm[asm["presentation"].isin(dev)]
                out = {}
                for n in d.DEV_PRESENTATIONS:
                    a = asm[asm["presentation"] == n].sort_values(["date", "assessment_type"], na_position="last")
                    out[n] = {"registrations": int(counts.get(n, 0)), "length_days": int(courses.get(n, 0)),
                              "assessments": [{"type": str(r.assessment_type),
                                               "day": None if pd.isna(r.date) else int(r.date),
                                               "weight": None if pd.isna(r.weight) else float(r.weight)}
                                              for r in a.itertuples()]}
                self._catalog = {"presentations": out}
        return self._catalog

    # ------------------------------------------------------------ بيانات التعريف
    def git(self) -> dict:
        if self._meta_cache and "git" in self._meta_cache:
            return self._meta_cache["git"]

        def run(*a):
            return subprocess.check_output(["git", *a], cwd=REPO_ROOT, stderr=subprocess.DEVNULL, timeout=5).decode().strip()
        try:
            commit = run("rev-parse", "HEAD")[:12]
        except Exception:
            commit = "unknown"
        try:
            dirty = bool(run("status", "--porcelain", "--untracked-files=no"))
        except Exception:
            dirty = False
        try:
            tag = run("describe", "--tags", "--match", "freeze*", "--abbrev=0") or None
        except Exception:
            tag = None
        g = {"commit": commit, "dirty": dirty, "freeze_tag": tag}
        self._meta_cache = {**(self._meta_cache or {}), "git": g}
        return g

    def data_fingerprint(self) -> tuple[str, dict]:
        """بصمة البيانات: MD5 لملف المرجع ``data/oulad_md5_reference.txt``، ومعه MD5 كل ملف خام."""
        path = self.settings.md5_reference
        if not path.exists():
            return "md5:unavailable", {}
        raw = path.read_bytes()
        files = {}
        for line in raw.decode("utf-8", "replace").splitlines():
            parts = line.split()
            if len(parts) == 2:
                files[Path(parts[1]).name] = parts[0]
        return "md5:" + hashlib.md5(raw).hexdigest(), files

    def frozen_commit(self) -> str | None:
        f = getattr(self.engine, "frozen", {}) or {}
        c = f.get("git_commit_at_freeze_run")
        return str(c)[:12] if c else None

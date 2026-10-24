"""واجهة (Facade) فوق ``serving.Engine``: تحويل مخرجات الخدمة إلى عقود المتعلم (D-49).

* الحساب دائماً عند اليوم المطلوب نفسه (``snapshot_day == requested_day``)، ومعاملات الثقيلة من أقرب قطع ≤ t.
* ذاكرة LRU على (عرض، تسجيل، يوم، مهمة) تحمل أفضل 20 عنصراً؛ والتسخين الحقيقي في ``lru_cache`` داخل Engine.
* مسارات المتعلم لا تُسقِط الخطر بل لا تطلبه أصلاً: لا نستدعي ``learner_profile`` هنا (D-22، NFR-09).
"""
from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..errors import ApiError
from ..repository import Repository
from ..schemas import (AssessmentInfo, ComponentInfo, DailyClicks, HistoryEvent, LearnerHistory, NextAssessment,
                       Page, Presentation, Provenance, RecContext, RecItem, RecommendationResponse,
                       RegistrationSummary)
from ..settings import DEFAULT_DAY, LOCKED_LISTED, MODEL_CUTS, SNAPSHOT_GRID, Settings
from .labels import comp_id, comp_label, fix_ar

NOTE_NO_HISTORY = "لا نشاط سابق لهذا التسجيل حتى هذا اليوم؛ الترتيب غير شخصي (الأكثر استخداماً لدى الزملاء)."


@dataclass
class RawRecs:
    status: str                  # ok | no_history | withdrawn
    plan: tuple                  # (c, comps, w, cfgs, note) من Engine.plan
    items: list                  # أفضل 20 كما تعيدها serving.recommend
    known: bool


class _LRU:
    def __init__(self, size: int):
        self.size = size
        self.d: OrderedDict = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            v = self.d.get(key)
            if v is not None:
                self.d.move_to_end(key)
            return v

    def put(self, key, value):
        with self.lock:
            self.d[key] = value
            self.d.move_to_end(key)
            while len(self.d) > self.size:
                self.d.popitem(last=False)

    def clear(self):
        with self.lock:
            self.d.clear()


def _int_or_none(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else int(x)


class ReplayService:
    def __init__(self, repo: Repository, settings: Settings):
        self.repo = repo
        self.settings = settings
        self._recs = _LRU(settings.rec_cache_size)
        self._reg_lists: dict[str, pd.DataFrame] = {}
        self._status_cache: dict = {}

    # ------------------------------------------------------------ العروض والتسجيلات
    def presentations(self) -> list[Presentation]:
        cat = self.repo.catalog()["presentations"]
        from src.ml.data import DEV_PRESENTATIONS
        order = [self.settings.default_presentation] + [n for n in DEV_PRESENTATIONS if n != self.settings.default_presentation]
        out = []
        for n in order:
            c = cat[n]
            seen, ass = set(), []
            for a in c["assessments"]:                       # حذف التكرار المتطابق (7 CMA في يوم واحد)
                k = (a["type"], a["day"], a["weight"])
                if k not in seen:
                    seen.add(k)
                    ass.append(AssessmentInfo(**a))
            module, term = n.split("_")
            season = "فبراير" if term.endswith("B") else "أكتوبر"
            out.append(Presentation(
                id=n, role="dev", status="published", length_days=c["length_days"],
                snapshots=[s for s in SNAPSHOT_GRID if s <= c["length_days"]], cutoffs=list(MODEL_CUTS),
                registrations=c["registrations"], label_ar=f"تطوير — الوحدة {module[0:3]}، دورة {season} {term[:4]}",
                assessments=ass))
        for n in LOCKED_LISTED:   # 2014: لا يُقرأ منها شيء (D-09)؛ العدد والطول غير معلنين
            out.append(Presentation(id=n, role="confirm", status="locked", length_days=0, snapshots=[],
                                    cutoffs=list(MODEL_CUTS), registrations=0,
                                    label_ar="تأكيدي 2014 (مقفل حتى النشر)", assessments=[]))
        return out

    def _registration_frame(self, pres: str) -> pd.DataFrame:
        """ترتيب ثابت: الأكثر أياماً نشطة حتى اليوم الافتراضي أولاً (الاختيار الافتراضي في الواجهة هو أول عنصر)."""
        df = self._reg_lists.get(pres)
        if df is None:
            ix = self.repo.index(pres)
            reg = ix.reg[["date_registration"]].reset_index()
            ev = ix.events[ix.events["date"] <= DEFAULT_DAY]
            act = ev.groupby("id_student")["date"].nunique()
            reg["_act"] = -reg["id_student"].map(act).fillna(0).to_numpy()
            df = reg.sort_values(["_act", "id_student"], kind="stable").reset_index(drop=True)
            self._reg_lists[pres] = df
        return df

    def _status_sets(self, pres: str, day: int):
        key = (pres, day)
        v = self._status_cache.get(key)
        if v is None:
            ix = self.repo.index(pres)
            u = ix.reg["date_unregistration"]
            withdrawn = set(u.index[(u <= day).to_numpy()].tolist())
            active = set(np.unique(ix.ids[ix.events["date"].to_numpy() <= day]).tolist())
            v = (withdrawn, active)
            if len(self._status_cache) > 16:
                self._status_cache.clear()
            self._status_cache[key] = v
        return v

    def registrations(self, pres: str, q: str, limit: int, offset: int, day: int | None = None) -> Page[RegistrationSummary]:
        self.repo.check_presentation(pres)
        df = self._registration_frame(pres)
        if q:
            df = df[df["id_student"].astype(str).str.contains(q, regex=False)]
        page = df.iloc[offset:offset + limit]
        withdrawn, active = self._status_sets(pres, day) if day is not None else (set(), None)

        def status(i: int) -> str:
            if i in withdrawn:
                return "withdrawn"
            return "no_history" if active is not None and i not in active else "ok"
        items = [RegistrationSummary(registration=f"{pres}-{int(r.id_student)}", id_student=int(r.id_student),
                                     date_registration=_int_or_none(r.date_registration), status=status(int(r.id_student)))
                 for r in page.itertuples()]
        return Page[RegistrationSummary](items=items, total=int(len(df)), limit=limit, offset=offset)

    # ------------------------------------------------------------ التوصيات
    def withdrawn_day(self, pres: str, student: int, day: int) -> int | None:
        u = self.repo.registration_row(pres, student)["date_unregistration"]
        return None if pd.isna(u) or u > day else int(u)

    def raw_recs(self, pres: str, student: int, day: int, task: str) -> RawRecs:
        self.repo.check_presentation(pres)
        self.repo.registration_row(pres, student)
        self.repo.check_day(pres, day)
        self.repo.require_artifacts()
        key = (pres, student, day, task)
        hit = self._recs.get(key)
        if hit is not None:
            return hit
        with self.repo.lock:
            hit = self._recs.get(key)
            if hit is not None:
                return hit
            eng = self.repo.engine
            plan = eng.plan(pres, day)
            if self.withdrawn_day(pres, student, day) is not None:
                raw = RawRecs("withdrawn", plan, [], False)
            else:
                items = eng.recommend(pres, student, day, k=20, exclude_seen=(task == "A"))
                known = bool(items[0]["known_learner"]) if items else False
                raw = RawRecs("ok" if known else "no_history", plan, items, known)
            self._recs.put(key, raw)
            return raw

    def next_assessment(self, pres: str, day: int) -> NextAssessment | None:
        a = self.repo.index(pres).assessments.dropna(subset=["date"])
        a = a[a["date"] >= day]
        if a.empty:
            return None
        a = a.sort_values(["date", "weight"], ascending=[True, False])
        r = a.iloc[0]
        return NextAssessment(type=str(r["assessment_type"]), day=int(r["date"]), days_ahead=int(r["date"] - day))

    def components(self, plan) -> list[ComponentInfo]:
        _, comps, w, _, _ = plan
        return [ComponentInfo(id=comp_id(m), label=comp_label(m), weight=round(float(x), 4)) for m, x in zip(comps, w)]

    def provenance(self, cut) -> Provenance:
        return Provenance(run_id=self.repo.run_id, role="dev", model_cut=None if cut is None else int(cut))

    def recommendation(self, pres: str, student: int, day: int, k: int, task: str) -> RecommendationResponse:
        raw = self.raw_recs(pres, student, day, task)
        ix = self.repo.index(pres)
        c, _, _, _, note = raw.plan
        items = []
        for n, it in enumerate(raw.items[:k], start=1):
            exp = it["explanation"]
            items.append(RecItem(
                rank=n, id_site=int(it["id_site"]), activity_type=str(it["activity_type"]), relevance=round(float(it["score"]), 4),
                contributions={comp_id(m): round(float(v["contribution"]), 4) for m, v in it["components"].items()},
                reason=fix_ar(exp["main"]["text"]), reason_secondary=(fix_ar(exp["secondary"][0]["text"]) if exp["secondary"] else None)))
        ev = ix.student_events(student, day)
        ctx = RecContext(week=day // 7 + 1, next_assessment=self.next_assessment(pres, day),
                         active_days_to_date=int(ev["date"].nunique()))
        note = fix_ar(note)
        if raw.status == "no_history" and not note:
            note = NOTE_NO_HISTORY
        return RecommendationResponse(
            registration=f"{pres}-{student}", presentation=pres, id_student=student, requested_day=day, snapshot_day=day,
            task=task, status=raw.status, known_learner=raw.known, note=note, context=ctx,
            components=self.components(raw.plan), items=items,
            provenance=Provenance(run_id=self.repo.run_id, role="dev", model_cut=None if c is None else int(c)))

    # ------------------------------------------------------------ سجل النشاط
    def history(self, pres: str, student: int, day: int, window: int) -> LearnerHistory:
        self.repo.check_presentation(pres)
        self.repo.registration_row(pres, student)
        self.repo.check_day(pres, day)
        ix = self.repo.index(pres)
        ev = ix.student_events(student, day)
        lo = max(0, day - window + 1)
        w = ev[ev["date"] >= lo]
        per_day = w.groupby("date")["clicks"].sum()
        daily = [DailyClicks(day=d, clicks=int(per_day.get(d, 0))) for d in range(lo, day + 1)]
        rec = ev.sort_values(["date", "clicks", "id_site"], ascending=[False, False, True]).head(3)
        recent = [HistoryEvent(day=int(r.date), id_site=int(r.id_site), activity_type=str(r.activity_type), clicks=int(r.clicks))
                  for r in rec.itertuples()]
        return LearnerHistory(registration=f"{pres}-{student}", day=day, window=window,
                              active_days=int(ev["date"].nunique()), daily=daily, recent=recent,
                              provenance=self.provenance(self.repo.engine.model_cut(day)))

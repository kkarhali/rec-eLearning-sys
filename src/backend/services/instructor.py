"""خدمة لوحة المدرّس: جدول المتعلمين والعناقيد والنظرة العامة والخطر، محسوبة متجهياً لكل (عرض، يوم).

كل ما كان مطلوباً في الوثيقة 03 §8.4 ولم يُضَف بعد إلى ``serving.py`` (``learner_table``، ``cluster_summary``،
عوامل w·z ومصدر التقدير، ``median_active_days``) مُنفَّذ هنا فوق مدخلات ``Engine`` نفسها (``_features_at`` وملفات
``artifacts/``) وبالمعادلات نفسها التي في ``Engine._risk`` و``Engine._cluster`` (يتحقق ``test_instructor`` من التطابق).
نموذج الخطر M1 (D-27، §8.4 بند 2): ملامح VLE وحدها. الخطر والعنقود للمدرّس فقط (D-22).
"""
from __future__ import annotations

import csv
import json
import threading
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..errors import ApiError
from ..repository import Repository
from ..schemas import (ClusterInfo, ClusterPoint, ClusterQuality, ClusterRef, ClusterSet, Coverage, HistBin,
                       InstructorLearnerDetail, InstructorLearnerRow, InstructorOverview, Kpis, OverviewRisk, Page,
                       ProfileRow, ProfileSummary, Provenance, RiskDetail, RiskFactor, RiskRow, TopFeature, TopRec,
                       TypeShare)
from ..settings import CLUSTER_DAY, Settings
from .labels import feature_ar, phrase
from .replay import ReplayService, _LRU

PROVENANCE = "lopo_2013"           # مدرَّب على العروض الثمانية الأخرى (ترك عرض خارج التدريب، D-65)
RISK_MODEL = "M1"
MAX_POINTS = 2500
PROFILE_ROWS = (   # (الاسم، العمود، الوحدة، معامل)
    ("الأيام النشطة", "active_days", "يوم", 1.0),
    ("يوم أول وصول", "first_day", "يوم", 1.0),
    ("انحراف الفجوات", "gap_sd", "يوم", 1.0),
    ("حصة quiz", "share_quiz", "%", 100.0),
    ("الالتزام بالمواعيد", "on_time_ratio", "%", 100.0),
    ("متوسط الدرجات", "mean_score", "درجة", 1.0),
)


@dataclass
class ClusterModel:
    cols: list
    mu: np.ndarray
    sd: np.ndarray
    centres: np.ndarray
    k: int
    stable: bool
    index: pd.Index                 # id_student لصفوف ``assign`` و``Z``
    assign: np.ndarray              # عنقود كل متعلم عند ملامح اليوم 56
    Z: np.ndarray                   # ملامح اليوم 56 المطبَّعة بمعاملات التدريب المخزَّنة
    labels_ar: list
    top: list                       # لكل عنقود [(اسم، z)]
    quality: tuple                  # (silhouette, dbi, ari)
    pca_mean: np.ndarray
    pca_V: np.ndarray


@dataclass
class RiskModel:
    tc: int
    threshold: float
    features: list
    index: pd.Index
    prob: np.ndarray
    wz: np.ndarray                  # n × p: w_j·z_j
    valid: np.ndarray               # مؤهل للتقدير (مسجَّل عند القطع ولم ينسحب قبله)


@dataclass
class Snapshot:
    pres: str
    day: int
    model_cut: int | None
    index: pd.Index                 # أعضاء الفوج (مسجَّلون ≤ t ولم ينسحبوا ≤ t)
    table: pd.DataFrame
    overview: InstructorOverview
    clusters: ClusterSet
    stats: dict = field(default_factory=dict)     # عمود -> (متوسط، انحراف، وسيط) على النشطين
    F: pd.DataFrame | None = None


def _round(x, n=2) -> float:
    x = float(x)
    return 0.0 if not np.isfinite(x) else round(x, n)


class InstructorService:
    def __init__(self, repo: Repository, replay: ReplayService, settings: Settings):
        self.repo = repo
        self.replay = replay
        self.settings = settings
        self._cm: dict[str, ClusterModel] = {}
        self._rm: dict[tuple, RiskModel] = {}
        self._snap = _LRU(settings.snapshot_cache_size)

    # ------------------------------------------------------------ بوابة اليوم
    def gate(self, pres: str, day: int) -> None:
        self.repo.check_presentation(pres)
        self.repo.check_day(pres, day)
        self.repo.require_artifacts()
        if day < CLUSTER_DAY:     # R-C2: لا عناقيد قبل 56 (ولا تقدير قبل 28)؛ الواجهة تنقل الشريط إلى first_day
            raise ApiError(422, "day_before_first_snapshot",
                           message=f"لا عناقيد ولا لوحة مدرّس قبل اليوم {CLUSTER_DAY} (أول عنقدة).",
                           details={"first_day": CLUSTER_DAY, "day": day})

    # ------------------------------------------------------------ نماذج ثابتة لكل عرض
    def cluster_model(self, pres: str) -> ClusterModel:
        cm = self._cm.get(pres)
        if cm is not None:
            return cm
        with self.repo.lock:
            cm = self._cm.get(pres)
            if cm is not None:
                return cm
            from src.ml import learners as L
            eng = self.repo.engine
            f = eng.art / pres / "clusters_56.npz"
            if not f.exists():
                raise ApiError(503, "artifacts_missing", details={"missing": str(f)})
            a = np.load(f)
            cols = [str(x) for x in a["features"]]
            F = eng._features_at(pres, CLUSTER_DAY)
            Z = (F[cols].to_numpy(dtype=float) - a["mu"]) / a["sd"]          # كما في Engine._cluster
            d2 = ((Z[:, None, :] - a["centres"][None, :, :]) ** 2).sum(axis=2)
            assign = d2.argmin(axis=1)
            k = int(a["k"])
            # وصف حتمي من المركز: أكبر ملمحين انحرافاً بالقيمة المطلقة (R-C3)
            top, labels = [], []
            for j in range(k):
                z = a["centres"][j]
                order = np.argsort(-np.abs(z), kind="stable")[:2]
                top.append([(feature_ar(cols[i]), _round(z[i], 1)) for i in order])
                labels.append(" · ".join(phrase(cols[i], z[i]) for i in order))
            seen = {}
            for j, lb in enumerate(labels):                                   # تفرُّد الوصف
                seen[lb] = seen.get(lb, 0) + 1
                if seen[lb] > 1:
                    labels[j] = f"{lb} ({seen[lb]})"
            tr = F.index.get_indexer(a["students"])
            ok = tr >= 0
            Ztr, ltr = Z[tr[ok]], np.asarray(a["labels"])[ok]
            sil = L.silhouette_fast(Ztr, ltr) if k > 1 else 0.0
            dbi = L.davies_bouldin(Ztr, ltr) if k > 1 else 0.0
            ari = self._ari(pres)
            mean = Ztr.mean(axis=0)
            _, _, Vt = np.linalg.svd(Ztr - mean, full_matrices=False)
            V = Vt[:2].copy()
            for r in range(V.shape[0]):                                       # إشارة حتمية للمحاور
                V[r] *= 1.0 if V[r][np.argmax(np.abs(V[r]))] >= 0 else -1.0
            cm = ClusterModel(cols, a["mu"], a["sd"], a["centres"], k, bool(a["stable"]), F.index, assign, Z, labels, top,
                              (sil, dbi, ari), mean, V)
            self._cm[pres] = cm
        return cm

    def _ari(self, pres: str) -> float:
        from src.ml.data import RESULTS_DIR
        f = RESULTS_DIR / "dev2013" / "learner_clusters.csv"
        try:
            with open(f, encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if r["presentation"] == pres:
                        return float(r["ari_k"])
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _unstable_reason(cm: ClusterModel) -> str:
        """قاعدة D-39-ب (learners.choose_k): مستقر = k ضمن أفضل اثنين في silhouette وDBI معاً **و** ARI عبر البذور ≥ 0.8.
        ARI المعروض هو ثبات البذور لـk المختار؛ فقد يكون 1 والعناقيد «غير مستقرة» لأن k فشل في الشرط الأول."""
        ari = cm.quality[2]
        if ari < 0.8:
            return f"ثبات البذور ضعيف: ARI = {ari:.2f} < 0.8 (D-39-ب)."
        return (f"البذور مستقرة (ARI = {ari:.2f} ≥ 0.8) لكن k = {cm.k} لم يقع ضمن أفضل اثنين في silhouette وDBI معاً؛ "
                "اعتُمد أفضل silhouette بوصفه الحالة الاحتياطية الرسمية (D-39-ب).")

    def risk_model(self, pres: str, tc: int) -> RiskModel:
        key = (pres, tc)
        rm = self._rm.get(key)
        if rm is not None:
            return rm
        with self.repo.lock:
            rm = self._rm.get(key)
            if rm is not None:
                return rm
            eng = self.repo.engine
            f = eng.art / pres / f"risk_{tc}.json"
            if not f.exists():
                raise ApiError(503, "artifacts_missing", details={"missing": str(f)})
            spec = json.loads(f.read_text())["models"][RISK_MODEL]
            F = eng._features_at(pres, tc)
            reg = self.repo.index(pres).reg.reindex(F.index)
            unreg = reg["date_unregistration"].to_numpy(float)
            dreg = reg["date_registration"].to_numpy(float)
            keep = ~(unreg < tc)                                              # كما في Engine._risk (NaN -> يُبقى)
            X = F.loc[keep, spec["features"]].to_numpy(dtype=float)
            mu, sd = X.mean(axis=0), X.std(axis=0)
            Z = (F[spec["features"]].to_numpy(dtype=float) - mu) / np.where(sd > 0, sd, 1)
            w = np.asarray(spec["weights"], dtype=float)
            prob = 1.0 / (1.0 + np.exp(-(w[0] + Z @ w[1:])))
            valid = keep & ~(dreg > tc)
            rm = RiskModel(tc, float(spec["youden_threshold"]), list(spec["features"]), F.index, prob, Z * w[1:], valid)
            self._rm[key] = rm
        return rm

    @staticmethod
    def risk_cut(day: int) -> int:
        return 112 if day >= 112 else 56 if day >= 56 else 28

    # ------------------------------------------------------------ لقطة (عرض، يوم)
    def snapshot(self, pres: str, day: int) -> Snapshot:
        self.gate(pres, day)
        key = (pres, day)
        s = self._snap.get(key)
        if s is not None:
            return s
        with self.repo.lock:
            s = self._snap.get(key)
            if s is None:
                s = self._build(pres, day)
                self._snap.put(key, s)
        return s

    def _build(self, pres: str, day: int) -> Snapshot:
        eng = self.repo.engine
        ix = self.repo.index(pres)
        F = eng._features_at(pres, day)
        reg = ix.reg.reindex(F.index)
        dreg = np.nan_to_num(reg["date_registration"].to_numpy(float), nan=-1e9)
        dun = reg["date_unregistration"].to_numpy(float)
        cohort = (dreg <= day) & ~(dun <= day)
        Fc = F[cohort]
        ids = Fc.index.to_numpy()

        ev = ix.events
        last = ev.loc[ev["date"].to_numpy() <= day].groupby("id_student")["date"].max().reindex(Fc.index)

        asm = ix.assessments.dropna(subset=["date"])
        n_due = int((asm["date"] <= day).sum())
        on_ratio = Fc["on_time_ratio"].to_numpy(float)
        n_on = np.rint(on_ratio * n_due).astype(int) if n_due else np.zeros(len(Fc), int)

        cm = self.cluster_model(pres)
        pos = cm.index.get_indexer(Fc.index)
        cl = cm.assign[pos]

        tc = self.risk_cut(day)
        rm = self.risk_model(pres, tc)
        rpos = rm.index.get_indexer(Fc.index)
        prob = np.where(rm.valid[rpos], rm.prob[rpos], np.nan)
        wz = rm.wz[rpos]
        topf = np.abs(wz).argmax(axis=1)
        top_factor = np.array([feature_ar(rm.features[i]) for i in topf], dtype=object)
        above = np.where(np.isnan(prob), False, prob >= rm.threshold)

        table = pd.DataFrame({
            "id": ids, "cluster": cl, "active_days": Fc["active_days"].to_numpy(int),
            "last_access": last.to_numpy(float), "n_on": n_on, "n_due": n_due, "on_ratio": on_ratio,
            "prob": prob, "above": above, "top_factor": top_factor})

        # ---- إحصاءات الملامح على النشطين (≥ يوم نشط)
        act = Fc[Fc["active_days"] >= 1]
        stats, summary = {}, []
        for name, col, unit, scale in PROFILE_ROWS:
            x = act[col] if col != "mean_score" else act.loc[act["no_score"] == 0, col]
            v = x.to_numpy(float) * scale
            if v.size == 0:
                v = np.zeros(1)
            p25, med, p75 = np.percentile(v, [25, 50, 75])
            stats[col] = (float(v.mean()), float(v.std()), float(med), scale)
            summary.append(ProfileSummary(name=name, p25=_round(p25), median=_round(med), p75=_round(p75), unit=unit))

        # ---- التغطية: أفضل 10 لكل متعلم معروف (Engine.recommend مباشرة؛ بلا حشو ذاكرة التوصيات)
        tr = eng.train_view(pres, day)
        members = set(int(i) for i in ids)
        covered, type_counts, n_recs = set(), {}, 0
        for u in tr.users:
            if int(u) not in members:
                continue
            for r in eng.recommend(pres, int(u), day, k=10, exclude_seen=True):
                covered.add(r["id_site"])
                type_counts[r["activity_type"]] = type_counts.get(r["activity_type"], 0) + 1
                n_recs += 1
        cat_types = pd.Series(tr.item_type).value_counts()
        cat_n = int(tr.n_items)
        main = list(cat_types.index[:6])
        by_type = [TypeShare(activity_type=str(t), catalogue_share=_round(cat_types[t] / cat_n, 3),
                             recs_share=_round(type_counts.get(t, 0) / max(n_recs, 1), 3)) for t in main]
        rest = [t for t in cat_types.index if t not in main]
        if rest:
            by_type.append(TypeShare(activity_type="أخرى", catalogue_share=_round(sum(cat_types[t] for t in rest) / cat_n, 3),
                                     recs_share=_round(sum(type_counts.get(t, 0) for t in rest) / max(n_recs, 1), 3)))
        coverage = Coverage(at_10=_round(len(covered) / max(cat_n, 1), 3), catalogue_size=cat_n, covered_items=len(covered),
                            by_type=by_type)

        valid = ~np.isnan(prob)
        hist = np.histogram(prob[valid], bins=np.linspace(0, 1, 11))[0] if valid.any() else np.zeros(10, int)
        risk = OverviewRisk(cut_day=tc, threshold=_round(rm.threshold, 3), provenance=PROVENANCE,
                            histogram=[HistBin(lo=_round(i / 10, 1), hi=_round((i + 1) / 10, 1), count=int(c)) for i, c in enumerate(hist)])
        share = float(above[valid].mean()) if valid.any() else None
        mc = eng.model_cut(day)
        prov = Provenance(run_id=self.repo.run_id, role="dev", model_cut=None if mc is None else int(mc))
        kpis = Kpis(active_learners=int(len(act)), median_active_days=_round(np.median(act["active_days"]) if len(act) else 0, 1),
                    catalogue_size=cat_n, coverage_at_10=coverage.at_10,
                    share_above_threshold=None if share is None else _round(share, 3))
        overview = InstructorOverview(presentation=pres, requested_day=day, snapshot_day=day, kpis=kpis, profile_summary=summary,
                                      risk=risk, coverage=coverage, provenance=prov)

        # ---- العناقيد
        sizes = np.bincount(cl, minlength=cm.k)
        Zc = cm.Z[pos]
        P = (Zc - cm.pca_mean) @ cm.pca_V.T
        sel = np.arange(len(P)) if len(P) <= MAX_POINTS else np.linspace(0, len(P) - 1, MAX_POINTS).astype(int)
        clusters = ClusterSet(
            presentation=pres, requested_day=day, snapshot_day=day, k=cm.k, cluster_day=CLUSTER_DAY, unstable=not cm.stable,
            unstable_reason=None if cm.stable else self._unstable_reason(cm),
            quality=ClusterQuality(silhouette=_round(cm.quality[0]), dbi=_round(cm.quality[1]), ari=_round(cm.quality[2])),
            clusters=[ClusterInfo(id=j, label_ar=cm.labels_ar[j], size=int(sizes[j]),
                                  top_features=[TopFeature(name=n, z=z) for n, z in cm.top[j]]) for j in range(cm.k)],
            points=[ClusterPoint(x=_round(P[i, 0]), y=_round(P[i, 1]), cluster=int(cl[i])) for i in sel])
        return Snapshot(pres, day, None if mc is None else int(mc), Fc.index, table, overview, clusters, stats, F)

    # ------------------------------------------------------------ المخرجات
    def overview(self, pres: str, day: int) -> InstructorOverview:
        return self.snapshot(pres, day).overview

    def clusters(self, pres: str, day: int) -> ClusterSet:
        return self.snapshot(pres, day).clusters

    def _risk_row(self, snap: Snapshot, r) -> RiskRow | None:
        if np.isnan(r.prob):
            return None
        rm = self.risk_model(snap.pres, self.risk_cut(snap.day))
        return RiskRow(score=_round(r.prob, 3), cut_day=rm.tc, threshold=_round(rm.threshold, 3),
                       above_threshold=bool(r.above), provenance=PROVENANCE, top_factor=str(r.top_factor))

    def learners(self, pres: str, day: int, cluster: int | None, risk: str, sort: str, limit: int, offset: int) -> Page[InstructorLearnerRow]:
        snap = self.snapshot(pres, day)
        cm = self.cluster_model(pres)
        t = snap.table
        if cluster is not None:
            t = t[t["cluster"] == cluster]
        if risk == "above":
            t = t[t["above"]]
        desc = sort.startswith("-")
        key = sort.lstrip("-")
        t = t.assign(_cl=t["cluster"].map(lambda j: cm.labels_ar[j]), _lr=t["last_access"].fillna(-1),
                     _rk=t["prob"].fillna(-1), _ot=t["on_ratio"] + t["n_on"] * 1e-6)
        col = {"risk": "_rk", "reg": "id", "cluster": "_cl", "active_days": "active_days", "last_access": "_lr", "on_time": "_ot"}[key]
        t = t.sort_values([col, "id"], ascending=[not desc, True], kind="stable")
        page = t.iloc[offset:offset + limit]
        rows = []
        for r in page.itertuples():
            n_due = int(r.n_due)
            rows.append(InstructorLearnerRow(
                registration=f"{pres}-{int(r.id)}", cluster=ClusterRef(id=int(r.cluster), label=cm.labels_ar[int(r.cluster)]),
                active_days=int(r.active_days), last_access_day=None if np.isnan(r.last_access) else int(r.last_access),
                on_time=f"{int(r.n_on)}/{n_due}" if n_due else "—", risk=self._risk_row(snap, r)))
        return Page[InstructorLearnerRow](items=rows, total=int(len(t)), limit=limit, offset=offset)

    def learner(self, pres: str, student: int, day: int) -> InstructorLearnerDetail:
        snap = self.snapshot(pres, day)
        self.repo.registration_row(pres, student)
        F = snap.F
        if student not in F.index:
            raise ApiError(404, "registration_not_found", details={"registration": f"{pres}-{student}"})
        cm = self.cluster_model(pres)
        j = int(cm.assign[cm.index.get_loc(student)])
        row = F.loc[student]
        profile = []
        for name, col, _unit, scale in PROFILE_ROWS:
            # قيمتان تُملآن بعرف الغياب (أول وصول = t+1، الدرجة = 0) فلا تُعرضان بلا نشاط/بلا درجة
            if (col == "first_day" and row["active_days"] < 1) or (col == "mean_score" and row["no_score"] == 1):
                continue
            mean, sd, med, _ = snap.stats[col]
            v = float(row[col]) * scale
            profile.append(ProfileRow(name=name, value=_round(v), median=_round(med), z=_round((v - mean) / sd if sd > 0 else 0.0)))
        tc = self.risk_cut(day)
        rm = self.risk_model(pres, tc)
        p = rm.index.get_loc(student)
        risk = None
        if rm.valid[p]:
            wz = rm.wz[p]
            order = np.argsort(-np.abs(wz), kind="stable")
            prob = float(rm.prob[p])
            risk = RiskDetail(score=_round(prob, 3), cut_day=tc, threshold=_round(rm.threshold, 3),
                              above_threshold=prob >= rm.threshold, provenance=PROVENANCE,
                              top_factor=feature_ar(rm.features[order[0]]),
                              factors=[RiskFactor(name=feature_ar(rm.features[i]), wz=_round(wz[i])) for i in order[:5]])
        wd = self.replay.withdrawn_day(pres, student, day)
        top = []
        if wd is None:
            raw = self.replay.raw_recs(pres, student, day, "A")
            top = [TopRec(rank=n, id_site=int(x["id_site"]), activity_type=str(x["activity_type"]), reason=x["explanation"]["main"]["text"])
                   for n, x in enumerate(raw.items[:3], start=1)]
        return InstructorLearnerDetail(registration=f"{pres}-{student}", day=day, snapshot_day=day,
                                       cluster=ClusterRef(id=j, label=cm.labels_ar[j]), risk=risk, profile=profile,
                                       top_recs=top, withdrawn_day=wd)

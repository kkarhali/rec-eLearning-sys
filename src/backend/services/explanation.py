"""تفسير التوصية بالمكوّنات والدليل (الوثيقة 02 §4.8): من المساهمة الفعلية w_m·r̃_m نفسها، بلا استدعاء ثانٍ للنموذج.

العنصر يُؤخذ من أفضل 20 المخزَّنة مؤقتاً في ``ReplayService``؛ والدليل للمكوّنين الظاهرين يأتي من ``serving.recommend``،
وللبقية من ``Engine._evidence`` نفسها (الدالة الوحيدة التي تعرف كيف يُشتق الدليل من كل مكوّن).
"""
from __future__ import annotations

import numpy as np

from ..errors import ApiError
from ..schemas import AssessmentEvidence, CountEvidence, ExplanationDetail, ExplComponent, ItemEvidence
from .labels import comp_id, comp_label, fix_ar
from .replay import ReplayService

ZERO_WEIGHT_SENTENCE = "وزن هذا المكوّن في نموذج هذا القطع 0؛ لا يساهم في الدرجة."


class ExplanationService:
    def __init__(self, replay: ReplayService):
        self.replay = replay
        self.repo = replay.repo

    def _item_evidence(self, pres, student, day, id_site):
        ix = self.repo.index(pres)
        ev = ix.student_events(student, day)
        v = ev[ev["id_site"] == id_site]
        if v.empty or id_site not in ix.item_type:
            return None
        return ItemEvidence(id_site=int(id_site), activity_type=ix.item_type[int(id_site)],
                            days=int(v["date"].nunique()), last_day=int(v["date"].max()))

    def _to_evidence(self, m, ev, pres, student, day):
        if not ev:
            return None
        if m == "B3_RecentPop":
            return CountEvidence(n=int(ev["learners_in_window"]), window=int(ev["window_days"]))
        if m == "C7_ClusterPop":
            # D-70: المفتاح بلا كلمة cluster؛ يقبل اسم serving الجديد والقديم إلى أن يُعاد تسميته هناك
            n = ev["similar_learners_in_window"] if "similar_learners_in_window" in ev else ev["same_cluster_learners_in_window"]
            return CountEvidence(n=int(n), window=int(ev["window_days"]), scope="similar")
        if m in ("B5_SKNN", "B6_Markov"):
            cands = [int(i) for i in ev.get("recent_items", [])]
            best, best_last = None, -10**9
            for i in cands:                                  # أحدث ما زاره المتعلم بين عناصر الاستعلام
                e = self._item_evidence(pres, student, day, i)
                if e is not None and e.last_day > best_last:
                    best, best_last = e, e.last_day
            return best
        if m == "B4_ItemKNN" and ev.get("because_of") is not None:
            return self._item_evidence(pres, student, day, int(ev["because_of"]))
        if m == "B7_WRMF" and ev.get("closest_in_history") is not None:
            return self._item_evidence(pres, student, day, int(ev["closest_in_history"]))
        if m == "C6_AssessProx" and ev.get("days") is not None:
            na = self.replay.next_assessment(pres, day)
            if na is None:
                return None
            return AssessmentEvidence(assessment_type=na.type, days_ahead=int(ev["days"]))
        return None

    def _hidden_evidence(self, m, item, pres, student, day, plan):
        """دليل مكوّن غير ظاهر في عنصر serving (لا main ولا secondary)."""
        from src.ml import components as CP
        c, comps, w, cfgs, _ = plan
        eng = self.repo.engine
        tr = eng.train_view(pres, day)
        try:
            u = tr.user_index(student)
        except KeyError:
            return {}
        cfg = CP.parse_config(cfgs[m])
        if m == "C7_ClusterPop":
            return {"similar_learners_in_window": int(item["components"][m]["raw"]), "window_days": int(cfg.get("w", 7))}
        j = int(np.searchsorted(tr.items, item["id_site"]))
        try:
            return eng._evidence(m, tr, u, j, cfg, pres, day, c) or {}
        except Exception:        # الدليل تحسيني: غيابه لا يُسقط التفسير
            return {}

    def explain(self, pres: str, student: int, id_site: int, day: int, task: str) -> ExplanationDetail:
        from src.ml import serving
        raw = self.replay.raw_recs(pres, student, day, task)
        item = next((x for x in raw.items if x["id_site"] == id_site), None)
        if item is None:
            raise ApiError(404, "item_not_in_list", details={"id_site": id_site, "top": len(raw.items)})
        c, comps, w, cfgs, note = raw.plan
        weight = {m: float(x) for m, x in zip(comps, w)}
        exp = item["explanation"]
        shown = {exp["main"]["component"]: exp["main"], **{s["component"]: s for s in exp["secondary"]}}
        out = []
        with self.repo.lock:
            for m in comps:
                comp = item["components"][m]
                if m in shown:
                    sentence, ev = shown[m]["text"], shown[m]["evidence"]
                elif weight[m] <= 0:
                    sentence, ev = ZERO_WEIGHT_SENTENCE, {}
                else:
                    ev = self._hidden_evidence(m, item, pres, student, day, raw.plan) if raw.known else {}
                    sentence = serving.TEMPLATES[m].format(item=ev.get("item", ev.get("because_of", "?")),
                                                           type=ev.get("type", "?"), days=ev.get("days", "?"))
                evidence = self._to_evidence(m, ev, pres, student, day) if weight[m] > 0 else None
                out.append(ExplComponent(id=comp_id(m), label=comp_label(m), weight=round(weight[m], 4),
                                         r_tilde=round(float(comp["rtilde"]), 4), contribution=round(float(comp["contribution"]), 4),
                                         evidence=evidence, sentence=fix_ar(sentence)))
        out.sort(key=lambda x: -x.contribution)
        notes = [fix_ar(note)] if note else []
        if not raw.known:
            notes.append("لا نشاط سابق لهذا التسجيل؛ الدرجات غير شخصية ولا دليل فردياً.")
        return ExplanationDetail(registration=f"{pres}-{student}", id_site=id_site, activity_type=str(item["activity_type"]),
                                 task=task, day=day, snapshot_day=day, relevance=round(float(item["score"]), 4),
                                 components=out, notes=notes, provenance=self.replay.provenance(c))

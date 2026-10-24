"""Replay recommendation service for the interface (D-22, D-49), using the frozen hybrid of the 2013 runs.

    from src.ml import serving
    serving.recommend("FFF_2013J", 2548055, day=100, k=10)
    serving.learner_profile("FFF_2013J", 2548055, day=100)
    serving.presentation_overview("FFF_2013J", day=100)

Conditions of D-49:
  1. heavy components (WRMF, GRU-lite) use the parameters trained at the nearest cut c ≤ day
     (``artifacts/<presentation>/<c>/``, built by ``experiments/build_artifacts.py``);
  2. the learner state is computed at the request day: WRMF fold-in (closed-form half ALS step for x_u with
     Y fixed and W(day)); GRU forward pass over the history ≤ day. No training at request time;
  3. light components (Recent-Pop, SKNN, Markov, Item-kNN, CBF, assessment proximity, cluster popularity) are
     computed at the request day;
  4. hybrid weights are those of cut c;
  5. before day 70 no heavy component exists: the available ones are used with renormalised weights
     (initial frozen weights), and the response says so;
  6. every response carries ``model_cut`` (the model date);
  7. no evaluation number may be derived from replay.
Only the 2013 development presentations are served before the freeze (D-09). Risk probabilities are for the
teacher dashboard only (D-22); no risk label is shown to learners.
"""
from __future__ import annotations

import json
from functools import lru_cache

import numpy as np

from . import components as CP, data, hybrid, learners as L
from .metrics import rank_order
from .models import BASELINES, COMPONENTS
from .models.baskets import last_days_query
from .models.gru_lite import Sequences, forward_states
from .models.simple import recent_popularity
from .models.wrmf import als_half_step
from .signals import SignalSpec, signal_matrix, wrmf_preference_confidence
from .splits import CUTS, build_train

ART = data.REPO_ROOT / "artifacts"
FROZEN = data.RESULTS_DIR / "dev2013" / "hybrid_frozen.json"
HEAVY = {"B7_WRMF", "GRU_lite"}
TEMPLATES = {
    "B3_RecentPop": "يستخدمه كثير من زملائك هذا الأسبوع",
    "B7_WRMF": "زاره متعلمون بنمط مشابه لنمطك",
    "B4_ItemKNN": "لأنك زرت {item}",
    "B5_SKNN": "يتبع غالباً ما زرتَه مؤخراً",
    "B6_Markov": "يتبع غالباً ما زرتَه مؤخراً",
    "GRU_lite": "يناسب تسلسل نشاطك في الأيام الأخيرة",
    "B9_CBF": "من النوع الذي تستخدمه كثيراً ({type})",
    "C6_AssessProx": "مرتبط بالتقييم القادم بعد {days} أيام",
    "C7_ClusterPop": "شائع لدى متعلمين بنمط مشابه لنمطك",
}


class Engine:
    def __init__(self, frozen=FROZEN, artifacts=ART, presentations: dict | None = None, student_assessment=None):
        """``frozen``: path to hybrid_frozen.json or the dict itself; ``presentations``/``student_assessment``
        may be injected (unit tests)."""
        self.frozen = frozen if isinstance(frozen, dict) else json.loads(frozen.read_text())
        self.art = artifacts
        self._pres = dict(presentations or {})
        self._sa = student_assessment

    # ---------------------------------------------------------------- data
    def presentation(self, name):
        data.assert_allowed([name])                       # D-09: 2014 refused
        if name not in self._pres:
            self._pres[name] = data.load_presentation(name)
        return self._pres[name]

    def model_cut(self, day: int):
        cs = [c for c in CUTS if c <= day]
        return max(cs) if cs else None

    def plan(self, name, day):
        """(model_cut, components, weights, configs, note) for a request day."""
        c = self.model_cut(day)
        comps = list(self.frozen["components"])
        if c is not None:
            wmap = self.frozen["weights_by_fold"][f"{name}_{c}"]
            cfgs = self.frozen["component_configs_by_fold"][f"{name}_{c}"]
            note = None
        else:
            wmap = dict(self.frozen["initial_weights_modal"])
            first = min(CUTS)
            cfgs = self.frozen["component_configs_by_fold"][f"{name}_{first}"]
            comps = [m for m in comps if m not in HEAVY]
            note = (f"اليوم {day} قبل أول قطع ({first}): لا مكوّن ثقيل؛ استُعملت المكوّنات الخفيفة بأوزان مُعاد تطبيعها "
                    f"(D-49 (5))، وإعداداتها من القطع {first}.")
        w = np.array([float(wmap.get(m, 0.0)) for m in comps])
        if w.sum() <= 0:
            w = np.ones(len(comps))
        return c, comps, w / w.sum(), cfgs, note

    @lru_cache(maxsize=32)
    def train_view(self, name, day):
        return build_train(self.presentation(name), day, day, "replay")

    # ---------------------------------------------------------------- component scores at day
    @lru_cache(maxsize=128)
    def component_scores(self, name, day, comp, c, cfg_key):
        tr = self.train_view(name, day)
        cfg = CP.parse_config(cfg_key)
        if comp == "B7_WRMF":
            return self._wrmf_foldin(tr, name, c, cfg)
        if comp == "GRU_lite":
            return self._gru_forward(tr, name, c)
        cls = COMPONENTS.get(comp) or BASELINES[comp]
        return cls(seed=0, **cfg).fit(tr).score()

    def _artifact(self, name, c, fname):
        f = self.art / name / str(c) / fname
        if not f.exists():
            raise FileNotFoundError(f"{f} missing: run python3 -m src.ml.experiments.build_artifacts")
        return np.load(f, allow_pickle=False)

    def _map_items(self, tr, art_items):
        pos = np.searchsorted(art_items, tr.items)
        pos = np.clip(pos, 0, len(art_items) - 1)
        known = art_items[pos] == tr.items
        return pos, known

    def _wrmf_foldin(self, tr, name, c, cfg):
        a = self._artifact(name, c, "wrmf.npz")
        Y_art, items = a["Y"], a["items"]
        pos, known = self._map_items(tr, items)
        spec = cfg.get("signal", SignalSpec("L1"))
        W = signal_matrix(tr, spec)[:, known]
        P, C = wrmf_preference_confidence(W, float(cfg.get("alpha", 2.0)), binary_confidence=spec.level == "L0")
        Y = Y_art[pos[known]]
        X = als_half_step(C, P, Y, float(cfg.get("reg", 0.1)))          # fold-in at the request day
        S = np.full((tr.n_users, tr.n_items), -1e9)
        S[:, known] = X @ Y.T
        return S

    def _gru_forward(self, tr, name, c):
        a = self._artifact(name, c, "gru.npz")
        p = {k[2:]: a[k] for k in a.files if k.startswith("p_")}
        items = a["items"]
        pos, known = self._map_items(tr, items)
        keep = known[tr.ev_i]
        bu = tr.ev_u[keep]
        days = tr.ev_d[keep]
        it = pos[tr.ev_i[keep]]
        key = bu.astype(np.int64) * 100_000 + days + 50_000
        uniq, inv = np.unique(key, return_inverse=True)
        order = np.argsort(inv, kind="stable")
        ptr = np.searchsorted(inv[order], np.arange(len(uniq) + 1))
        seqs = Sequences((uniq // 100_000), ptr, it[order].astype(np.int64), tr.n_users, len(items))
        logits = np.full((tr.n_users, tr.n_items), -1e9)
        users = np.array([u for u in range(tr.n_users) if seqs.length(u) > 0])
        for s in range(0, len(users), 512):
            ub = users[s:s + 512]
            A, _, m, _ = seqs.dense_batch(ub, inputs_only=True)
            h = forward_states(p, A, m)
            out = h @ p["V"] + p["c"]
            logits[np.ix_(ub, np.flatnonzero(known))] = out[:, pos[known]]
        return logits

    # ---------------------------------------------------------------- explanations
    def _evidence(self, comp, tr, u, j, cfg, name, day, c):
        it = int(tr.items[j])
        if comp == "B3_RecentPop":
            w = int(cfg.get("w", 7))
            return {"learners_in_window": int(recent_popularity(tr, w)[j]), "window_days": w}
        if comp == "B4_ItemKNN":
            from .models.knn import item_similarity
            sim = item_similarity(tr.seen, float(cfg.get("shrink", 0.0)))
            W = signal_matrix(tr, cfg.get("signal", SignalSpec("L0")))[u]
            contrib = sim[:, j] * W
            i = int(np.argmax(contrib))
            return {"because_of": int(tr.items[i]), "because_of_type": str(tr.item_type[i]), "item": int(tr.items[i])}
        if comp == "B7_WRMF":
            a = self._artifact(name, c, "wrmf.npz")
            pos, known = self._map_items(tr, a["items"])
            hist = np.flatnonzero(tr.seen[u] & known)
            if len(hist) and known[j]:
                Y = a["Y"]
                yj = Y[pos[j]]
                Yh = Y[pos[hist]]
                cos = (Yh @ yj) / (np.linalg.norm(Yh, axis=1) * np.linalg.norm(yj) + 1e-12)
                i = hist[int(np.argmax(cos))]
                return {"closest_in_history": int(tr.items[i])}
            return {}
        if comp in ("B5_SKNN", "B6_Markov"):
            q = last_days_query(tr, 1, "binary")[u]
            return {"recent_items": tr.items[q > 0].astype(int).tolist()[:5]}
        if comp == "B9_CBF":
            return {"type": str(tr.item_type[j])}
        if comp == "C6_AssessProx":
            gap = data.next_assessment_gap([day], tr.assessments["date"])[0]
            return {"days": None if not np.isfinite(gap) else int(gap)}
        if comp == "C7_ClusterPop":
            return {"note": "count of same-cluster learners in the window"}
        return {}

    # ---------------------------------------------------------------- API
    def recommend(self, name, registration, day, k=10, exclude_seen=True):
        tr = self.train_view(name, int(day))
        c, comps, w, cfgs, note = self.plan(name, int(day))
        try:
            u = tr.user_index(registration)
        except KeyError:
            u = None
        cand = (~tr.seen[u] if (exclude_seen and u is not None) else np.ones(tr.n_items, bool))[None, :]
        rt, raw = {}, {}
        for m in comps:
            S = self.component_scores(name, int(day), m, c, cfgs[m])
            row = S[u:u + 1] if u is not None else S.mean(axis=0, keepdims=True)
            raw[m] = row[0]
            rt[m] = hybrid.rank_normalize(row, cand)[0]
        fused = sum(wi * rt[m] for wi, m in zip(w, comps))
        tb = tr.tiebreak[u:u + 1] if u is not None else np.zeros((1, tr.n_items))
        order = rank_order(fused[None, :], cand, tb)[0]
        order = order[cand[0, order]][:k]
        out = []
        for j in order:
            contrib = {m: float(wi * rt[m][j]) for wi, m in zip(w, comps)}
            tot = sum(contrib.values()) or 1.0
            ranked = sorted(contrib, key=contrib.get, reverse=True)
            shown = [ranked[0]] + ([ranked[1]] if len(ranked) > 1 and contrib[ranked[1]] > tot / 3 else [])
            expl = []
            for m in shown:
                ev = self._evidence(m, tr, u, j, CP.parse_config(cfgs[m]), name, int(day), c) if u is not None else {}
                expl.append({"component": m, "text": TEMPLATES[m].format(item=ev.get("item", "?"),
                                                                         type=ev.get("type", "?"),
                                                                         days=ev.get("days", "?")),
                             "contribution": contrib[m], "evidence": ev})
            out.append({"id_site": int(tr.items[j]), "activity_type": str(tr.item_type[j]), "score": float(fused[j]),
                        "components": {m: {"rtilde": float(rt[m][j]), "weight": float(wi), "contribution": contrib[m],
                                           "raw": float(raw[m][j])} for wi, m in zip(w, comps)},
                        "explanation": {"main": expl[0], "secondary": expl[1:]},
                        "model_cut": c, "day": int(day), "note": note,
                        "known_learner": u is not None})
        return out

    @lru_cache(maxsize=16)
    def _features_at(self, name, day):
        p = self.presentation(name)
        studs = p.students["id_student"].to_numpy()
        F = L.vle_features(p.events, studs, day).join(L.total_clicks(p.events, studs, day))
        return F.join(L.academic_features(p, studs, day, self._student_assessment()))

    def _student_assessment(self):
        if self._sa is None:
            self._sa = data.load_student_assessment("dev")
        return self._sa

    def _risk(self, name, registration, day, model="M2"):
        tcs = [t for t in (28, 56, 112) if t <= day]
        if not tcs:
            return None
        tc = max(tcs)
        f = self.art / name / f"risk_{tc}.json"
        if not f.exists():
            return None
        spec = json.loads(f.read_text())["models"][model]
        p = self.presentation(name)
        unreg = p.registrations.set_index("id_student")["date_unregistration"]
        if registration in unreg.index and unreg.get(registration) < tc:
            return {"risk_cut": tc, "probability": None, "note": "withdrawn before the cut"}
        F = self._features_at(name, tc)
        keep = ~(unreg.reindex(F.index) < tc).fillna(False).to_numpy()
        X = F.loc[keep, spec["features"]].to_numpy(dtype=float)
        mu, sd = X.mean(axis=0), X.std(axis=0)
        x = (F.loc[registration, spec["features"]].to_numpy(dtype=float) - mu) / np.where(sd > 0, sd, 1)
        prob = float(L.logistic_predict(np.array(spec["weights"]), x[None, :])[0])
        return {"risk_cut": tc, "model": model, "probability": prob, "youden_threshold": spec["youden_threshold"],
                "above_threshold": prob >= spec["youden_threshold"], "audience": "teacher only (D-22)"}

    def _cluster(self, name, registration, day):
        if day < 56:
            return None
        f = self.art / name / "clusters_56.npz"
        if not f.exists():
            return None
        a = np.load(f)
        cols = [str(x) for x in a["features"]]
        F = self._features_at(name, 56)
        x = (F.loc[registration, cols].to_numpy(dtype=float) - a["mu"]) / a["sd"]
        d = ((a["centres"] - x) ** 2).sum(axis=1)
        return {"cluster": int(np.argmin(d)), "k": int(a["k"]), "stable": bool(a["stable"]), "cluster_day": 56}

    def learner_profile(self, name, registration, day, risk_model="M2"):
        F = self._features_at(name, int(day))
        if registration not in F.index:
            raise KeyError(registration)
        r = F.loc[registration]
        shares = {c[6:]: float(r[c]) for c in F.columns if c.startswith("share_") and r[c] > 0}
        top = dict(sorted(shares.items(), key=lambda kv: -kv[1])[:3])
        p = self.presentation(name)
        ev = p.events[(p.events["id_student"] == registration) & (p.events["date"] <= day)]
        return {"presentation": name, "registration": int(registration), "day": int(day),
                "features": {"active_days": int(r["active_days"]), "total_clicks": int(r["total_clicks"]),
                             "first_day": int(r["first_day"]), "gap_sd": float(r["gap_sd"]),
                             "last_active_day": int(ev["date"].max()) if len(ev) else None,
                             "distinct_resources": int(ev["id_site"].nunique()), "top_type_shares": top,
                             "on_time_ratio": float(r["on_time_ratio"]), "mean_score": float(r["mean_score"])},
                "cluster": self._cluster(name, registration, int(day)),
                "risk": self._risk(name, registration, int(day), risk_model)}

    def presentation_overview(self, name, day, risk_model="M2"):
        p = self.presentation(name)
        tr = self.train_view(name, int(day))
        rp = recent_popularity(tr, 7)
        top = np.argsort(-rp, kind="stable")[:10]
        recent = p.events[(p.events["date"] > day - 7) & (p.events["date"] <= day)]
        asm = p.assessments.dropna(subset=["date"])
        nxt = asm[asm["date"] >= day].sort_values("date").head(3)
        out = {"presentation": name, "day": int(day), "model_cut": self.model_cut(int(day)),
               "registrations": int(len(p.students)), "active_learners_7d": int(recent["id_student"].nunique()),
               "catalogue_size": int(tr.n_items),
               "top_resources_7d": [{"id_site": int(tr.items[j]), "activity_type": str(tr.item_type[j]),
                                     "learners": int(rp[j])} for j in top],
               "next_assessments": [{"id_assessment": int(r.id_assessment), "type": r.assessment_type,
                                     "date": int(r.date)} for r in nxt.itertuples()]}
        f = self.art / name / "clusters_56.npz"
        if day >= 56 and f.exists():
            a = np.load(f)
            out["clusters_56"] = {"k": int(a["k"]), "stable": bool(a["stable"]),
                                  "sizes": np.bincount(a["labels"], minlength=int(a["k"])).tolist()}
        if day >= 28:
            probs = []
            for s in p.students["id_student"].to_numpy():
                r = self._risk(name, int(s), int(day), risk_model)
                if r and r.get("probability") is not None:
                    probs.append(r["probability"])
            if probs:
                bands = np.histogram(probs, bins=[0, 0.25, 0.5, 0.75, 1.0001])[0]
                out["risk_bands"] = {"0-0.25": int(bands[0]), "0.25-0.5": int(bands[1]), "0.5-0.75": int(bands[2]),
                                     "0.75-1": int(bands[3]), "audience": "teacher only (D-22)"}
        return out


_ENGINE: Engine | None = None


def engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = Engine()
    return _ENGINE


def recommend(presentation, registration, day, k=10, exclude_seen=True):
    return engine().recommend(presentation, registration, day, k, exclude_seen)


def learner_profile(presentation, registration, day):
    return engine().learner_profile(presentation, registration, day)


def presentation_overview(presentation, day):
    return engine().presentation_overview(presentation, day)

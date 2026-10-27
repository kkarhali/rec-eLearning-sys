"""Replay service (D-49): plan, heavy fold-in from artifacts, no leakage, explanations, 2014 refusal."""
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import numpy as np
import pandas as pd

from src.ml import data, harness, serving
from src.ml.models import BASELINES
from src.ml.signals import SignalSpec
from src.ml.splits import build_train
from src.ml.tests.helpers import make_presentation, random_presentation

NAME = "AAA_2013J"


def _augment(p):
    p.students = p.students.assign(num_of_prev_attempts=0, studied_credits=60, final_result="Pass")
    p.registrations = p.registrations.assign(date_registration=-20, date_unregistration=np.nan)
    return p


def _with_future(p, sa, day, seed=0):
    """A copy of presentation ``p`` (and of ``student_assessment`` ``sa``) with only *future* information added after
    ``day`` (ج-16): more clicks and events of existing learners, new resources (in the catalogue, used only after
    ``day``), new learners who register and act only after ``day``, a withdrawal dated after ``day``, and a late
    assessment submission. Nothing on or before ``day`` changes."""
    rng = np.random.default_rng(seed)
    ev = list(p.events[["id_student", "id_site", "date", "clicks"]].itertuples(index=False, name=None))
    types = dict(zip(p.items["id_site"].astype(int), p.items["activity_type"].astype(str)))
    old_users = sorted(int(u) for u in p.events["id_student"].unique())
    old_items = sorted(types)
    kinds = sorted({t for t in types.values()})
    new_items = {90_000 + j: kinds[j % len(kinds)] for j in range(6)}          # existing types: same categories
    new_users = [900_000 + j for j in range(12)]
    later = lambda: int(rng.integers(day + 1, p.length + 1))                     # noqa: E731
    future = [(int(u), int(i), d, c) for u, i, d, c in ev if d > day]
    ev += [(u, i, d, 5 * c) for u, i, d, c in future]                           # heavier clicks after day
    for _ in range(300):                                                       # existing learners, existing items
        ev.append((old_users[rng.integers(len(old_users))], old_items[rng.integers(len(old_items))], later(), 3))
    for i in new_items:                                                        # new resources, used after day only
        for u in rng.choice(old_users, 15, replace=False):
            ev.append((int(u), i, later(), 2))
    for u in new_users:                                                        # new learners, active after day only
        for _ in range(25):
            pool = old_items + list(new_items)
            ev.append((u, pool[rng.integers(len(pool))], later(), 4))
    q = make_presentation(ev, {**types, **new_items}, name=p.name, length=p.length,
                          assessment_dates=tuple(p.assessments["date"].tolist()))
    q.events = q.events.astype({"date": p.events["date"].dtype})
    q = _augment(q)
    base = p.registrations.set_index("id_student")
    reg = q.registrations.set_index("id_student")
    for col in ("date_registration", "date_unregistration"):
        reg.loc[base.index, col] = base[col]
    reg.loc[new_users, "date_registration"] = day + 3
    stay = base.index[base["date_unregistration"].isna()]
    reg.loc[stay[-1], "date_unregistration"] = day + 10                        # withdraws after day
    q.registrations = reg.reset_index()
    late_sub = pd.DataFrame({"id_assessment": [int(q.assessments["id_assessment"].iloc[-1])],
                             "id_student": [old_users[0]], "date_submitted": [float(day + 2)], "is_banked": [0],
                             "score": [90.0]})
    sa2 = pd.concat([sa, late_sub], ignore_index=True).astype(sa.dtypes.to_dict()) if len(sa.columns) else sa
    return q, sa2, new_users, list(new_items)


def _canon(o):
    """JSON-comparable form of an Engine response (numpy scalars, NaN -> None, floats to 12 digits)."""
    if isinstance(o, dict):
        return {str(k): _canon(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, np.ndarray)):
        return [_canon(v) for v in o]
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (np.integer, int)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 12)
    return o


def _day_responses(eng, day, students):
    """Every public Engine response at ``day`` (recommendations for tasks A and B with explanations, learner
    profile with risk and cluster, overview, registration list)."""
    out = {"overview": eng.presentation_overview(NAME, day), "registrations": eng.registrations(NAME, day)}
    for u in students:
        out[f"recs_A_{u}"] = eng.recommend(NAME, u, day, k=10, exclude_seen=True)
        out[f"recs_B_{u}"] = eng.recommend(NAME, u, day, k=10, exclude_seen=False)
        out[f"profile_{u}"] = eng.learner_profile(NAME, u, day)
    return _canon(out)


def _frozen():
    wrmf_cfg = harness.config_key({"f": 8, "reg": 0.1, "alpha": 5.0, "iters": 5, "signal": SignalSpec("L1")})
    comps = ["B3_RecentPop", "B7_WRMF", "B6_Markov"]
    cfg = {"B3_RecentPop": "w=7", "B7_WRMF": wrmf_cfg, "B6_Markov": "L=1;gamma=0.1"}
    fold = {f"{NAME}_{c}": dict(cfg) for c in (70, 126, 182)}
    w = {f"{NAME}_{c}": {"B3_RecentPop": 0.5, "B7_WRMF": 0.25, "B6_Markov": 0.25} for c in (70, 126, 182)}
    return {"components": comps, "weights_by_fold": w, "component_configs_by_fold": fold,
            "initial_weights_modal": {"B3_RecentPop": 0.5, "B7_WRMF": 0.25, "B6_Markov": 0.25}}


class TestServing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.art = Path(cls.tmp.name)
        cls.p = _augment(random_presentation(seed=11, n_students=50, n_items=30))
        frozen = _frozen()
        from src.ml.components import parse_config
        for c in (70, 126, 182):
            tr = build_train(cls.p, c, c, "test")
            m = BASELINES["B7_WRMF"](seed=0, **parse_config(frozen["component_configs_by_fold"][f"{NAME}_{c}"]["B7_WRMF"])).fit(tr)
            (cls.art / NAME / str(c)).mkdir(parents=True)
            np.savez(cls.art / NAME / str(c) / "wrmf.npz", Y=m.Y, items=tr.items, config="x")
        sa = pd.DataFrame({"id_assessment": [], "id_student": [], "date_submitted": [], "is_banked": [], "score": []})
        cls.eng = serving.Engine(frozen=frozen, artifacts=cls.art, presentations={NAME: cls.p}, student_assessment=sa)
        cls.student = int(cls.p.events["id_student"].iloc[0])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_plan_before_first_cut(self):
        c, comps, w, _, note = self.eng.plan(NAME, 40)
        self.assertIsNone(c)
        self.assertNotIn("B7_WRMF", comps)
        self.assertAlmostEqual(w.sum(), 1.0)
        self.assertIsNotNone(note)
        c, comps, w, _, note = self.eng.plan(NAME, 140)
        self.assertEqual(c, 126)
        self.assertIn("B7_WRMF", comps)
        self.assertIsNone(note)

    def test_recommend_structure_and_unseen(self):
        recs = self.eng.recommend(NAME, self.student, 140, k=5)
        self.assertEqual(len(recs), 5)
        tr = build_train(self.p, 140, 140, "replay")
        seen = set(tr.items[tr.seen[tr.user_index(self.student)]].tolist())
        for r in recs:
            self.assertNotIn(r["id_site"], seen)
            self.assertEqual(r["model_cut"], 126)
            self.assertEqual(set(r["components"]), {"B3_RecentPop", "B7_WRMF", "B6_Markov"})
            self.assertIn("text", r["explanation"]["main"])
            tot = sum(v["contribution"] for v in r["components"].values())
            self.assertAlmostEqual(tot, r["score"])
        self.assertTrue(all(recs[i]["score"] >= recs[i + 1]["score"] for i in range(4)))

    def test_no_future_data_used(self):
        """Changing events after the request day changes nothing (fold-in and light models use ≤ day)."""
        a = self.eng.recommend(NAME, self.student, 140, k=5)
        p2 = _augment(random_presentation(seed=11, n_students=50, n_items=30))
        ev = p2.events
        late = ev["date"] > 140
        ev.loc[late, "clicks"] = (ev.loc[late, "clicks"] * 7).astype(np.int32)
        p2.events = ev
        eng2 = serving.Engine(frozen=self.eng.frozen, artifacts=self.art, presentations={NAME: p2},
                              student_assessment=self.eng._sa)
        b = eng2.recommend(NAME, self.student, 140, k=5)
        self.assertEqual([r["id_site"] for r in a], [r["id_site"] for r in b])

    def test_future_events_resources_learners_change_nothing(self):
        """ج-16: adding events, resources and learners after day t leaves every response at day t unchanged
        (WRMF fold-in from artifacts, light components, explanations, profile, overview, registrations)."""
        day = 140
        students = sorted(int(u) for u in self.p.events["id_student"].unique())[:8]
        q, sa2, _, new_items = _with_future(self.p, self.eng._sa, day)
        eng2 = serving.Engine(frozen=self.eng.frozen, artifacts=self.art, presentations={NAME: q}, student_assessment=sa2)
        self.assertGreater(len(q.events), len(self.p.events))
        self.assertEqual(_day_responses(self.eng, day, students), _day_responses(eng2, day, students))
        later = {r["id_site"] for r in eng2.recommend(NAME, students[0], 250, k=200, exclude_seen=False)}
        self.assertTrue(later & set(new_items))                  # the new resources are visible after their day

    def test_wrmf_foldin_uses_artifact_items(self):
        S = self.eng.component_scores(NAME, 140, "B7_WRMF", 126,
                                      self.eng.frozen["component_configs_by_fold"][f"{NAME}_126"]["B7_WRMF"])
        tr = build_train(self.p, 140, 140, "replay")
        self.assertEqual(S.shape, (tr.n_users, tr.n_items))
        art_items = np.load(self.art / NAME / "126" / "wrmf.npz")["items"]
        new = ~np.isin(tr.items, art_items)
        if new.any():
            self.assertTrue((S[:, new] <= -1e8).all())

    def test_profile_and_overview(self):
        prof = self.eng.learner_profile(NAME, self.student, 20)
        self.assertIsNone(prof["risk"])                       # no risk model before day 28
        self.assertIsNone(prof["cluster"])                    # dashboard clusters from day 56
        self.assertIn("active_days", prof["features"])
        ov = self.eng.presentation_overview(NAME, 20)
        self.assertEqual(ov["model_cut"], None)
        self.assertLessEqual(len(ov["top_resources_7d"]), 10)

    def test_2014_refused(self):
        with self.assertRaises(data.ConfirmatoryAccessError):
            self.eng.recommend("DDD_2014B", 1, 100)


if __name__ == "__main__":
    unittest.main()


class TestServingContract(unittest.TestCase):
    """D-65 (relative risk score), D-68 (persisted cluster choice), D-70 (whitelist, no cluster in evidence), FR-40."""

    @classmethod
    def setUpClass(cls):
        from src.ml import learners as L
        cls.tmp = tempfile.TemporaryDirectory()
        cls.art = Path(cls.tmp.name) / "art"
        cls.p = _augment(random_presentation(seed=12, n_students=60, n_items=30))
        cls.p.registrations.loc[cls.p.registrations.index[:3], "date_unregistration"] = [30.0, 150.0, 250.0]
        frozen = {"components": ["C7_ClusterPop", "B6_Markov"],
                  "weights_by_fold": {f"{NAME}_{c}": {"C7_ClusterPop": 0.75, "B6_Markov": 0.25} for c in (70, 126, 182)},
                  "component_configs_by_fold": {f"{NAME}_{c}": {"C7_ClusterPop": "w=7", "B6_Markov": "L=1;gamma=0.1"}
                                                for c in (70, 126, 182)},
                  "initial_weights_modal": {"C7_ClusterPop": 0.75, "B6_Markov": 0.25}}
        feats = ["active_days", "gap_sd", "first_day"] + [f"share_{t}" for t in L.ALL_TYPES]
        (cls.art / NAME).mkdir(parents=True)
        rng = np.random.default_rng(0)
        for tc in (28, 56, 112):
            spec = {"features": feats, "weights": rng.normal(0, 0.3, len(feats) + 1).tolist(), "lambda": 0.01,
                    "youden_threshold": 0.45, "threshold_source": "test"}
            (cls.art / NAME / f"risk_{tc}.json").write_text(json.dumps({"provenance": "lopo_2013", "models": {"M1": spec}}))
        sa = pd.DataFrame({"id_assessment": pd.Series([], dtype=int), "id_student": pd.Series([], dtype=int),
                           "date_submitted": pd.Series([], dtype=float), "is_banked": pd.Series([], dtype=int),
                           "score": pd.Series([], dtype=float)})
        cls.cache = Path(cls.tmp.name) / "clusters"
        cls.eng = serving.Engine(frozen=frozen, artifacts=cls.art, presentations={NAME: cls.p}, student_assessment=sa,
                                 cluster_cache_dir=cls.cache)
        cls.student = int(cls.p.registrations["id_student"].iloc[10])        # never withdrawn

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_registrations_whitelist(self):
        regs = self.eng.registrations(NAME, 100)
        self.assertTrue(all(set(r) == {"id_student", "date_registration", "date_unregistration"} for r in regs))
        un = {r["id_student"]: r["date_unregistration"] for r in regs}
        ids = self.p.registrations["id_student"].iloc[:3].tolist()
        self.assertEqual(un[ids[0]], 30)          # past withdrawal is known
        self.assertIsNone(un[ids[1]])             # future withdrawal hidden (D-70)
        self.assertIsNone(un[ids[2]])
        self.assertNotIn("final_result", json.dumps(regs))

    def test_cluster_cache_matches_live(self):
        from src.ml.models.context import cluster_choice
        serving._CLUSTER_MEM.clear()
        a = self.eng.cluster_choice_at(NAME, 100)                     # computed and written to disk
        serving._CLUSTER_MEM.clear()
        b = self.eng.cluster_choice_at(NAME, 100)                     # read back from disk
        live = cluster_choice(build_train(self.p, 100, 100, "replay"))
        self.assertTrue((self.cache / f"{NAME}_100.npz").exists())
        for x in (a, b):
            self.assertEqual(x.k, live.k)
            np.testing.assert_array_equal(x.labels, live.labels)
            for s in range(5):
                np.testing.assert_array_equal(x.labels_by_seed[s], live.labels_by_seed[s])

    def test_precompute_clusters_fills_cache_for_every_day(self):
        """NFR-01: the precomputed day-t choice is the one a request computes; a second pass only reads it."""
        from src.ml.models.context import cluster_choice
        days = [88, 89, 90]
        for d in days:
            self.eng.cluster_cache_file(NAME, d).unlink(missing_ok=True)
        seen = []
        r = self.eng.precompute_clusters(NAME, days=days, progress=lambda i, n, d, sec: seen.append((i, n, d)))
        self.assertEqual((r["days"], r["computed"], r["already_cached"]), (3, 3, 0))
        self.assertEqual([x[0] for x in seen], [1, 2, 3])
        self.assertTrue(all(self.eng.cluster_cached(NAME, d) for d in days))
        r2 = self.eng.precompute_clusters(NAME, days=days, jobs=4)        # injected data: runs in-process
        self.assertEqual((r2["computed"], r2["already_cached"]), (0, 3))
        serving._CLUSTER_MEM.clear()
        with mock.patch.object(serving, "cluster_choice", side_effect=AssertionError("recomputed")):
            got = self.eng.cluster_choice_at(NAME, 89)                     # read from the precomputed file
        live = cluster_choice(build_train(self.p, 89, 89, "replay"))
        np.testing.assert_array_equal(got.labels, live.labels)
        with mock.patch.object(serving.Engine, "_cluster_choice_disk", return_value=(None, False)) as m:
            all_days = self.eng.precompute_clusters(NAME, days=None)          # default: every day 0..length
        self.assertEqual(all_days["days"], int(self.p.length) + 1)
        self.assertEqual(sorted(c.args[1] for c in m.call_args_list), list(range(int(self.p.length) + 1)))

    def test_evidence_has_no_cluster_and_warm(self):
        recs = self.eng.recommend(NAME, self.student, 140, k=5)
        for r in recs:
            for e in [r["explanation"]["main"], *r["explanation"]["secondary"]]:
                self.assertNotIn("cluster", json.dumps(e["evidence"]).lower())
                if e["component"] == "C7_ClusterPop":
                    self.assertIn("similar_learners_in_window", e["evidence"])
        t = self.eng.warm(NAME, days=[70, 77])
        self.assertEqual(set(t), {70, 77})

    def test_risk_is_relative_score(self):
        prof = self.eng.learner_profile(NAME, self.student, 60)
        self.assertEqual(prof["model_cut"], None)
        r = prof["risk"]
        self.assertNotIn("probability", r)
        self.assertEqual(r["provenance"], "lopo_2013")
        self.assertFalse(r["calibrated"])
        self.assertEqual(r["risk_cut"], 56)
        self.assertTrue(0 <= r["score"] <= 1)
        self.assertEqual(len(r["top_factors"]), 3)
        lt = self.eng._learner_rows(NAME, 60)
        self.assertIn("risk_score", lt.columns)
        ov = self.eng.presentation_overview(NAME, 60)
        self.assertIn("median_active_days", ov)
        self.assertFalse(ov["risk_bands"]["calibrated"])
        withdrawn = int(self.p.registrations["id_student"].iloc[0])           # withdrew on day 30 < 56
        self.assertIsNone(self.eng.learner_profile(NAME, withdrawn, 60)["risk"]["score"])

    def test_future_information_changes_nothing_with_risk_and_clusters(self):
        """ج-16 with the teacher-side responses: relative risk score (z within the cohort at the cut), cluster at day
        56, C7 cluster popularity recomputed at day t, overview counts and bands; for days 60 and 100."""
        import shutil
        tmp = tempfile.TemporaryDirectory()
        art = Path(tmp.name) / "art"
        shutil.copytree(self.art, art)
        F = self.eng._features_at(NAME, 56)
        cols = ["active_days", "gap_sd", "first_day"]
        X = F[cols].to_numpy(float)
        mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-9
        Z = (X - mu) / sd
        centres = Z[[0, 1, 2]]
        labels = ((Z[:, None, :] - centres[None]) ** 2).sum(axis=2).argmin(axis=1)
        np.savez(art / NAME / "clusters_56.npz", features=np.array(cols), mu=mu, sd=sd, centres=centres, k=3, stable=True,
                 labels=labels, students=F.index.to_numpy())
        students = [int(x) for x in self.p.registrations["id_student"].iloc[[0, 1, 5, 10, 20, 30, 40]]]
        for day in (60, 100):
            with self.subTest(day=day):
                serving._CLUSTER_MEM.clear()
                e1 = serving.Engine(frozen=self.eng.frozen, artifacts=art, presentations={NAME: self.p},
                                    student_assessment=self.eng._sa, cluster_cache_dir=Path(tmp.name) / f"c1_{day}")
                a = _day_responses(e1, day, students)
                q, sa2, new_users, _ = _with_future(self.p, self.eng._sa, day, seed=day)
                serving._CLUSTER_MEM.clear()
                e2 = serving.Engine(frozen=self.eng.frozen, artifacts=art, presentations={NAME: q}, student_assessment=sa2,
                                    cluster_cache_dir=Path(tmp.name) / f"c2_{day}")
                b = _day_responses(e2, day, students)
                self.assertTrue(any(v["risk"] and v["risk"]["score"] is not None for k, v in a.items() if k.startswith("profile_")))
                self.assertIsNotNone(a[f"profile_{students[-1]}"]["cluster"])
                for key in a:
                    self.assertEqual(a[key], b[key], key)
                self.assertNotIn(new_users[0], [r["id_student"] for r in b["registrations"]])
                prof = e2.learner_profile(NAME, new_users[0], day)        # registered after the cut: no estimate
                self.assertIsNone(prof["risk"]["score"])
        serving._CLUSTER_MEM.clear()
        tmp.cleanup()

    def test_fr40_gate(self):
        if (data.RESULTS_DIR / "conf2014" / "verdicts.csv").exists():
            self.skipTest("confirmatory verdicts exist")
        with self.assertRaises(data.ConfirmatoryAccessError):
            serving.Engine(frozen=self.eng.frozen, artifacts=self.art, allow_confirmatory=True)


class TestServingRound3(unittest.TestCase):
    def test_no_duplicate_teacher_table(self):
        """learner_table / cluster_summary live only in the backend instructor service (single implementation)."""
        self.assertFalse(hasattr(serving, "learner_table"))
        self.assertFalse(hasattr(serving, "cluster_summary"))
        self.assertFalse(hasattr(serving.Engine, "learner_table"))
        self.assertFalse(hasattr(serving.Engine, "cluster_summary"))

    def test_cluster_key_includes_frozen_fingerprints(self):
        """D-68: changing hybrid_frozen.json or freeze03_config.json invalidates the persisted cluster choice."""
        tmp = tempfile.TemporaryDirectory()
        d = Path(tmp.name)
        p = _augment(random_presentation(seed=13, n_students=40, n_items=25))
        sa = pd.DataFrame({"id_assessment": [], "id_student": [], "date_submitted": [], "is_banked": [], "score": []})
        cfg = d / "cfg.json"
        cfg.write_text('{"v": 1}')
        frozen = _frozen()
        e1 = serving.Engine(frozen=frozen, artifacts=d, presentations={NAME: p}, student_assessment=sa,
                            cluster_cache_dir=d / "cc", freeze_config=cfg)
        e1.cluster_choice_at(NAME, 100)
        f = d / "cc" / f"{NAME}_100.npz"
        fp1 = str(np.load(f)["fingerprint"])
        cfg.write_text('{"v": 2}')
        e2 = serving.Engine(frozen=frozen, artifacts=d, presentations={NAME: p}, student_assessment=sa,
                            cluster_cache_dir=d / "cc", freeze_config=cfg)
        self.assertNotEqual(e1.frozen_fingerprint, e2.frozen_fingerprint)
        e2.cluster_choice_at(NAME, 100)                      # stale entry rejected, recomputed and rewritten
        self.assertNotEqual(str(np.load(f)["fingerprint"]), fp1)
        tmp.cleanup()

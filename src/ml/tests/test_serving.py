"""Replay service (D-49): plan, heavy fold-in from artifacts, no leakage, explanations, 2014 refusal."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.ml import data, harness, serving
from src.ml.models import BASELINES
from src.ml.signals import SignalSpec
from src.ml.splits import build_train
from src.ml.tests.helpers import random_presentation

NAME = "AAA_2013J"


def _augment(p):
    p.students = p.students.assign(num_of_prev_attempts=0, studied_credits=60, final_result="Pass")
    p.registrations = p.registrations.assign(date_registration=-20, date_unregistration=np.nan)
    return p


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

"""Temporal split: no overlap, no leakage, tasks A/B, D-09 guard."""
import unittest

import numpy as np
import pandas as pd

from src.ml import data, splits
from src.ml.models import BASELINES
from src.ml.signals import SignalSpec
from src.ml.tests.helpers import make_presentation, random_presentation


class TestFolds(unittest.TestCase):
    def setUp(self):
        self.p = random_presentation(seed=3)

    def test_windows(self):
        for cut in splits.CUTS:
            for phase in splits.PHASES:
                tr, tg = splits.make_fold(self.p, cut, phase)
                t0 = cut - 14 if phase == "tune" else cut
                self.assertEqual(tr.t0, t0)
                self.assertEqual(tg.window, (t0, t0 + 14))
                self.assertLessEqual(tr.ev_d.max(), t0)
                self.assertLessEqual(tr.all_events["date"].max(), t0)
                splits.check_no_overlap(tr, tg)

    def test_tune_validation_is_inside_test_training(self):
        """validation (t−14, t] ⊂ test-phase training (≤ t); test window (t, t+14] after both."""
        tr_tune, tg_tune = splits.make_fold(self.p, 126, "tune")
        tr_test, tg_test = splits.make_fold(self.p, 126, "test")
        self.assertEqual(tg_tune.window[1], tr_test.t0)
        self.assertGreater(tg_test.window[0], tg_tune.window[0])
        self.assertEqual(tg_tune.window[1], tg_test.window[0])

    def test_catalogue_and_exclusion(self):
        tr, _ = splits.make_fold(self.p, 70, "test", exclusion="E5")
        self.assertFalse(set(tr.item_type) & data.E5)
        ev = self.p.events
        expected = np.unique(ev.loc[(ev["date"] <= 70) & ~ev["activity_type"].astype(str).isin(data.E5),
                                    "id_site"])
        np.testing.assert_array_equal(tr.items, expected)
        tr_none, _ = splits.make_fold(self.p, 70, "test", exclusion="none")
        self.assertTrue(set(tr_none.item_type) & data.E5)
        tr_e4, _ = splits.make_fold(self.p, 70, "test", exclusion="E4")
        self.assertIn("page", set(tr_e4.item_type))

    def test_tasks(self):
        tr, tg = splits.make_fold(self.p, 126, "test")
        tA, cA, uA, eA = tg.task("A")
        tB, cB, uB, eB = tg.task("B")
        self.assertFalse((tA & tr.seen).any())               # A: only new items
        self.assertTrue((tA <= tB).all())
        self.assertTrue((cA == ~tr.seen).all())
        self.assertTrue(cB.all())
        self.assertTrue((tA <= cA).all())
        # every target pair of the window is in the catalogue or counted unreachable
        ev = self.p.events
        win = ev[(ev["date"] > 126) & (ev["date"] <= 140) & ~ev["activity_type"].astype(str).isin(data.E5)]
        win = win[win["id_student"].isin(tr.users)].drop_duplicates(["id_student", "id_site"])
        self.assertEqual(int(tB.sum() + uB.sum()), len(win))

    def test_unreachable_targets(self):
        types = {1: "quiz", 2: "quiz", 3: "url"}
        ev = [(1, 1, 5, 1), (1, 2, 6, 1), (2, 1, 7, 1), (1, 3, 75, 1), (2, 2, 76, 1)]
        tr, tg = splits.make_fold(make_presentation(ev, types), 70, "test")
        self.assertEqual(tr.items.tolist(), [1, 2])
        self.assertEqual(tg.unreach.tolist(), [1, 0])           # item 3 first appears after t0
        tA, _, _, eA = tg.task("A")
        self.assertEqual(eA.tolist(), [True, True])
        self.assertEqual(tA[tr.user_index(2)].tolist(), [False, True])

    def test_no_leakage_into_models(self):
        """Changing anything after t0 changes no training structure and no model score."""
        cut, phase = 126, "tune"
        tr1, _ = splits.make_fold(self.p, cut, phase)
        p2 = random_presentation(seed=3)
        ev = p2.events
        late = ev["date"] > tr1.t0
        rng = np.random.default_rng(9)
        ev.loc[late, "clicks"] = rng.integers(1, 500, late.sum()).astype(np.int32)
        extra = ev[late].sample(200, random_state=1).copy()
        extra["date"] = np.minimum(extra["date"] + 1, p2.length - 1)
        p2.events = pd.concat([ev, extra]).drop_duplicates(["id_student", "id_site", "date"]).reset_index(drop=True)
        tr2, _ = splits.make_fold(p2, cut, phase)
        for f in ("users", "items", "ev_u", "ev_i", "ev_d", "ev_c", "seen", "tiebreak"):
            np.testing.assert_array_equal(getattr(tr1, f), getattr(tr2, f), err_msg=f)
        cfgs = {"B4_ItemKNN": {"k": 20, "shrink": 10.0, "signal": SignalSpec("L3", tau=14, beta=1.0)},
                "B5_SKNN": {"L": 3, "k": 50, "M": None, "variant": "vsknn"},
                "B6_Markov": {"gamma": 0.1, "L": 1}, "B7_WRMF": {"f": 8, "iters": 3},
                "B9_CBF": {}, "B3_RecentPop": {"w": 21}, "B2_Pop": {}, "B8_PersonalRepeat": {"tau": 14.0},
                "B10_EASE": {"lam": 50.0}}
        for name, cfg in cfgs.items():
            s1 = BASELINES[name](seed=0, **cfg).fit(tr1).score()
            s2 = BASELINES[name](seed=0, **cfg).fit(tr2).score()
            np.testing.assert_array_equal(s1, s2, err_msg=name)

    def test_window_beyond_length_rejected(self):
        p = random_presentation(seed=1, length=150)
        with self.assertRaises(ValueError):
            splits.make_fold(p, 182, "test")

    def test_tiebreak_deterministic_and_order_free(self):
        a = splits.tiebreak_keys("FFF_2013J", 70, np.array([5, 9]), np.array([100, 200, 300]))
        b = splits.tiebreak_keys("FFF_2013J", 70, np.array([9]), np.array([300, 100]))
        self.assertAlmostEqual(a[1, 2], b[0, 0])
        self.assertAlmostEqual(a[1, 0], b[0, 1])
        self.assertTrue(((a >= 0) & (a < 1)).all())
        c = splits.tiebreak_keys("FFF_2013J", 126, np.array([5, 9]), np.array([100, 200, 300]))
        self.assertFalse(np.allclose(a, c))


class TestConfirmatoryGuard(unittest.TestCase):
    def test_2014_refused(self):
        with self.assertRaises(data.ConfirmatoryAccessError):
            data.assert_allowed(["DDD_2014B"])
        with self.assertRaises(data.ConfirmatoryAccessError):
            data.load_presentation("CCC_2014J")
        with self.assertRaises(data.ConfirmatoryAccessError):
            data.load_daily_events("conf")
        data.assert_allowed(data.DEV_PRESENTATIONS)
        self.assertEqual(len(data.DEV_PRESENTATIONS), 9)
        self.assertEqual(len(data.CONF_PRESENTATIONS), 13)

    def test_exclusion_sets(self):
        self.assertEqual(data.EXCLUSION_SETS["E5"],
                         {"homepage", "subpage", "sharedsubpage", "folder", "page"})
        self.assertEqual(data.EXCLUSION_SETS["E4"], data.EXCLUSION_SETS["E5"] - {"page"})
        self.assertEqual(data.EXCLUSION_SETS["none"], frozenset())

    def test_assessment_gap(self):
        gaps = data.next_assessment_gap([40, 70, 200], [19, 47, 96, 131, 173, np.nan])
        np.testing.assert_array_equal(gaps, [7, 26, np.inf])      # FFF_2013J example of draft §3.6
        np.testing.assert_array_equal(data.proximity_bin(np.array([0, 3, 4, 7, 8, 14, 15, np.inf])),
                                      [0, 0, 1, 1, 2, 2, 3, 3])


if __name__ == "__main__":
    unittest.main()


class TestConfirmatoryIdRead(unittest.TestCase):
    """D-47: only (code_module, code_presentation, id_student) of studentRegistration may be read."""

    def test_columns_and_log(self):
        import json
        import tempfile
        from pathlib import Path
        calls = []

        def fake_reader(path, usecols=None, **kw):
            calls.append((Path(path).name, tuple(usecols), kw))
            return pd.DataFrame({"code_module": ["AAA", "DDD", "DDD"], "code_presentation": ["2013J", "2014B", "2014J"],
                                 "id_student": [1, 2, 3]})[list(usecols)]
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "access_log.jsonl"
            ids = data.confirmatory_student_ids(log_path=log, reader=fake_reader)
            rec = json.loads(log.read_text().strip())
        self.assertEqual(ids, {2, 3})
        self.assertEqual(calls, [("studentRegistration.csv", ("code_module", "code_presentation", "id_student"), {})])
        self.assertEqual(rec["columns"], ["code_module", "code_presentation", "id_student"])
        self.assertEqual(rec["n_ids"], 2)
        for k in ("time", "md5", "commit"):
            self.assertIn(k, rec)

    def test_rest_of_barrier_intact(self):
        with self.assertRaises(data.ConfirmatoryAccessError):
            data.load_presentation("DDD_2014B")
        with self.assertRaises(data.ConfirmatoryAccessError):
            data.load_daily_events("conf")

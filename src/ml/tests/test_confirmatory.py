"""Guards and verdict assembly of the confirmatory runner (D-63), without running any model."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.ml.experiments import run_confirmatory as RC


def fake_git(head="aaa", tag="aaa", dirty="", tag_exists=True):
    def git(*args):
        if args[:1] == ("rev-parse",) and args[1].endswith("^{commit}"):
            if not tag_exists:
                raise RuntimeError("no tag")
            return tag
        if args == ("rev-parse", "HEAD"):
            return head
        if args == ("status", "--porcelain"):
            return dirty
        raise AssertionError(args)
    return git


class TestGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "conf2014"

    def tearDown(self):
        self.tmp.cleanup()

    def test_ok(self):
        self.assertEqual(RC.check_guards("freeze-03", self.out, git=fake_git()), "aaa")

    def test_refusals(self):
        with self.assertRaises(RC.GuardError):
            RC.check_guards("freeze-03", self.out, git=fake_git(tag_exists=False))
        with self.assertRaises(RC.GuardError):
            RC.check_guards("freeze-03", self.out, git=fake_git(head="bbb"))
        with self.assertRaises(RC.GuardError):
            RC.check_guards("freeze-03", self.out, git=fake_git(dirty=" M src/ml/x.py"))
        self.out.mkdir()
        with self.assertRaises(RC.GuardError):
            RC.check_guards("freeze-03", self.out, git=fake_git())


class TestVerdicts(unittest.TestCase):
    def test_table(self):
        idx = [f"P{i}" for i in range(13)]
        rng = np.random.default_rng(0)
        per = {"H1": pd.Series(0.05 + rng.normal(0, 0.01, 13), index=idx),       # clear positive effect ≥ δ
               "H2-a": pd.Series(rng.normal(0.0, 0.003, 13), index=idx),        # practically null → refuted
               "H3": pd.Series(np.resize([0.10, -0.06], 13), index=idx),       # wide → inconclusive
               "H4-a": pd.Series(np.r_[np.zeros(10), [0.01, 0.02, 0.03]], index=idx)}   # degenerate interval
        mde = {"H1": {"MDE80": 0.0375}, "H2-a": {"MDE80": 0.045}, "H3": {"MDE80": 0.05}, "H4-a": {"MDE80": 0.0225}}
        v = RC.build_verdicts(per, mde, gru_passed=True).set_index("hypothesis")
        self.assertEqual(v.loc["H1", "verdict"], "confirmed")
        self.assertEqual(v.loc["H2-a", "verdict"], "refuted")
        self.assertEqual(v.loc["H3", "verdict"], "inconclusive")
        self.assertIn("MDE80 = 0.0500", v.loc["H3", "D48_text"])
        self.assertTrue(v.loc["H4-a", "degenerate"])
        self.assertEqual(v.loc["H4-a", "verdict"], "inconclusive")       # +∞ upper bound forbids "refuted" (D-52)
        # Holm with m = 4
        p = v["p"].to_numpy()
        np.testing.assert_allclose(v["p_holm"].to_numpy(), RC.stats.holm(p))
        md = RC.verdicts_md(v.reset_index(), "test")
        self.assertIn("منحلّ", md)
        self.assertIn("H2-ب", md)

    def test_untestable_h3(self):
        per = {h: pd.Series(np.linspace(0.01, 0.05, 13)) for h in RC.HYPOTHESES}
        v = RC.build_verdicts(per, {}, gru_passed=False).set_index("hypothesis")
        self.assertTrue(v.loc["H3", "verdict"].startswith("untestable"))
        self.assertEqual(v.loc["H3", "p"], 1.0)

    def test_deployable_training(self):
        dev = ["BBB_2013B", "BBB_2013J", "FFF_2013B"]
        self.assertEqual(RC.deployable_training("BBB_2013J", dev), ["BBB_2013B", "FFF_2013B"])
        self.assertEqual(RC.deployable_training("BBB_2013B", dev), [])


if __name__ == "__main__":
    unittest.main()

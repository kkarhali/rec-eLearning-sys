"""Unit checks of the parts of scripts/posthoc/sklearn_equivalence.py that do not need scikit-learn (A-5).

    python3 -m unittest discover -s scripts/posthoc -p 'test_*.py'
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402

import _common as C  # noqa: E402
import sklearn_equivalence as SE  # noqa: E402
from src.ml import data, learners as L  # noqa: E402

RAW_OK = (data.RAW_DIR / "studentVle.csv").exists()


class TestSklearnMissing(unittest.TestCase):
    def test_exits_with_clear_message(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            SE.require_sklearn(find_spec=lambda name: None)
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("scikit-learn is not installed", err.getvalue())
        self.assertIn("Nothing was computed or written", err.getvalue())

    def test_present_passes(self):
        SE.require_sklearn(find_spec=lambda name: object())          # no exit


class TestLambdaToC(unittest.TestCase):
    """C = 1/(λn) must make our minimiser a stationary point of sklearn's objective C·Σ logloss + ½‖w‖²."""

    def test_mapping_values(self):
        self.assertAlmostEqual(SE.lambda_to_C(0.1, 200), 0.05)
        with self.assertRaises(ValueError):
            SE.lambda_to_C(0.0, 10)

    def test_our_solution_is_stationary_for_sklearn_objective(self):
        rng = np.random.default_rng(0)
        n, d = 400, 5
        X = rng.normal(size=(n, d))
        y = (X @ rng.normal(size=d) + 0.5 * rng.normal(size=n) > 0).astype(float)
        for lam in (1e-3, 1e-2, 1e-1, 1.0, 10.0):
            w = L.logistic_fit(X, y, lam, max_iter=200, tol=1e-14)
            Cc = SE.lambda_to_C(lam, n)
            Xb = np.hstack([np.ones((n, 1)), X])
            p = 1 / (1 + np.exp(-(Xb @ w)))
            g = Cc * Xb.T @ (p - y)                                   # ∇ C·Σ logloss
            g[1:] += w[1:]                                             # ∇ ½‖w‖², intercept unpenalised
            self.assertLess(np.abs(g).max(), 1e-6, f"λ={lam}")


@unittest.skipUnless(RAW_OK, "OULAD raw files not present")
class TestPrepare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pres, cls.df, cls.y, cls.fs, cls.X = SE.prepare(56)

    def test_only_2013_and_no_sensitive(self):
        self.assertTrue(self.df["presentation"].isin(data.DEV_PRESENTATIONS).all())
        self.assertEqual(self.df["presentation"].nunique(), 9)
        self.assertFalse(set(self.df.columns) & set(data.SENSITIVE_COLUMNS))
        for cols in self.fs.values():
            self.assertFalse(set(cols) & set(data.SENSITIVE_COLUMNS))

    def test_rows_match_locked_learner_table(self):
        meta = json.loads((C.DEV / "learner_meta.json").read_text())
        self.assertEqual(len(self.df), meta["rows_day56"])

    def test_feature_sets_and_standardisation(self):
        self.assertEqual(self.fs["M0"], ["total_clicks"])
        self.assertTrue(set(self.fs["M1"]) < set(self.fs["M2"]))
        for m, Xm in self.X.items():
            self.assertEqual(Xm.shape, (len(self.df), len(self.fs[m])))
            self.assertTrue(np.isfinite(Xm).all())
            for _, idx in self.df.groupby("presentation").indices.items():
                self.assertLess(np.abs(Xm[idx].mean(axis=0)).max(), 1e-9)
        self.assertTrue(set(np.unique(self.y)) <= {0, 1})


if __name__ == "__main__":
    unittest.main()

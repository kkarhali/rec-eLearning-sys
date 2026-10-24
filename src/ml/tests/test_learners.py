"""Learner analysis against the worked examples of draft §4.7 and sanity checks (§4.11 Table 17-b)."""
import unittest

import numpy as np
import pandas as pd

from src.ml import learners as L

PTS = np.array([[1, 1], [1.5, 2], [3, 4], [5, 7], [3.5, 5], [4.5, 5]], dtype=float)


class TestClustering(unittest.TestCase):
    def test_kmeanspp_probabilities(self):
        d2 = ((PTS - PTS[0]) ** 2).sum(axis=1)
        np.testing.assert_allclose(d2, [0, 1.25, 13, 52, 22.25, 28.25])
        self.assertAlmostEqual(d2[3] / d2.sum(), 0.445, places=3)
        self.assertAlmostEqual(d2[1] / d2.sum(), 0.011, places=3)

    def test_silhouette_dbi_examples(self):
        lab = np.array([0, 0, 1, 1, 1, 1])
        D = np.sqrt(((PTS[:, None] - PTS[None]) ** 2).sum(axis=2))
        a, b = D[0, 1], D[0, 2:].mean()
        self.assertAlmostEqual(a, 1.118, places=3)
        self.assertAlmostEqual(b, 5.212, places=3)
        self.assertAlmostEqual((b - a) / max(a, b), 0.785, places=3)
        self.assertAlmostEqual(L.silhouette(PTS, lab), L.silhouette_fast(PTS, lab), places=12)
        self.assertAlmostEqual(L.davies_bouldin(PTS, lab), 0.375, places=3)

    def test_ari(self):
        self.assertAlmostEqual(L.adjusted_rand_index(np.array([0, 0, 1, 1, 1, 1]), np.array([0, 0, 1, 1, 2, 2])),
                               0.444, places=3)
        self.assertAlmostEqual(L.adjusted_rand_index(np.array([0, 0, 1, 1]), np.array([1, 1, 0, 0])), 1.0)

    def test_recovers_separated_gaussians(self):
        rng = np.random.default_rng(0)
        centres = np.array([[0, 0], [10, 0], [0, 10]])
        truth = np.repeat([0, 1, 2], 60)
        X = centres[truth] + rng.normal(0, 0.5, (180, 2))
        lab, _, _ = L.kmeans(X, 3, seed=1)
        self.assertAlmostEqual(L.adjusted_rand_index(truth, lab), 1.0)
        ch = L.choose_k(X, ks=range(2, 6), seeds=(0, 1, 2), n_init=5)
        self.assertEqual(ch.k, 3)
        self.assertTrue(ch.stable)


class TestClassifiers(unittest.TestCase):
    def test_logistic_example(self):
        w = np.array([0.3, -1.2, 0.8])
        self.assertAlmostEqual(L.logistic_predict(w, np.array([[1.5, 0.5]]))[0], 0.25, places=2)

    def test_logistic_separable_and_permuted(self):
        rng = np.random.default_rng(0)
        X = rng.normal(size=(400, 3))
        y = (X[:, 0] > 0).astype(int)
        w = L.logistic_fit(X, y, 1e-3)
        self.assertGreater(((L.logistic_predict(w, X) > 0.5) == y).mean(), 0.99)
        yp = rng.permutation(y)
        Xt, yt = rng.normal(size=(4000, 3)), rng.integers(0, 2, 4000)
        w2 = L.logistic_fit(X, yp, 1.0)
        self.assertAlmostEqual(L.roc_auc(yt, L.logistic_predict(w2, Xt)), 0.5, delta=0.04)

    def test_logistic_one_dimensional_closed_form(self):
        """Unpenalised intercept-only fit equals the log-odds of the base rate."""
        y = np.array([1, 0, 0, 0, 1, 0, 0, 0])
        w = L.logistic_fit(np.zeros((8, 1)), y, 1.0)
        self.assertAlmostEqual(w[0], np.log(2 / 6), places=6)

    def test_gini_example(self):
        y = np.array([1, 1, 1, 0, 1, 0, 0, 0, 0, 0])
        x = np.array([1, 2, 3, 4, 20, 21, 22, 23, 24, 25], dtype=float)
        self.assertAlmostEqual(L.gini(y), 0.48)
        self.assertAlmostEqual(L.gini(y[:4]), 0.375)
        self.assertAlmostEqual(L.gini(y[4:]), 0.2778, places=4)
        tree = L.cart_fit(x[:, None], y, max_depth=1, min_leaf=1)
        # best depth-1 split separates {1,2,3} from the rest here; check the documented split value too
        self.assertIn("feature", tree)
        gain_doc = 0.48 - (0.4 * 0.375 + 0.6 * (1 - (1 / 6) ** 2 - (5 / 6) ** 2))
        self.assertAlmostEqual(gain_doc, 0.163, places=3)
        self.assertGreaterEqual(tree["gain"], gain_doc - 1e-12)

    def test_auc_ap_youden(self):
        y = np.array([0, 0, 1, 1])
        self.assertAlmostEqual(L.roc_auc(y, np.array([0.1, 0.4, 0.35, 0.8])), 0.75)
        self.assertAlmostEqual(L.roc_auc(y, np.array([0.5, 0.5, 0.5, 0.5])), 0.5)
        self.assertAlmostEqual(L.average_precision(y, np.array([0.1, 0.4, 0.35, 0.8])), (1 + 2 / 3) / 2)
        thr = L.youden_threshold(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.7, 0.9]))
        self.assertAlmostEqual(thr, 0.7)
        m = L.threshold_metrics(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.7, 0.9]), thr)
        self.assertEqual((m["FNR"], m["FPR"], m["balanced_accuracy"]), (0.0, 0.0, 1.0))


class TestFeatures(unittest.TestCase):
    def test_vle_features(self):
        ev = pd.DataFrame({"id_student": [1, 1, 1, 2], "date": [2, 5, 9, 70], "clicks": [3, 1, 4, 5],
                           "activity_type": pd.Categorical(["quiz", "homepage", "quiz", "url"])})
        F = L.vle_features(ev, np.array([1, 2]), 56)
        self.assertEqual(F.loc[1, "active_days"], 3)
        self.assertAlmostEqual(F.loc[1, "gap_sd"], np.std([3, 4]))
        self.assertEqual(F.loc[1, "first_day"], 2)
        self.assertAlmostEqual(F.loc[1, "share_quiz"], 7 / 8)
        self.assertAlmostEqual(F.loc[1, "share_homepage"], 1 / 8)
        self.assertEqual(F.loc[2, "active_days"], 0)          # day 70 > cut
        self.assertEqual(F.loc[2, "first_day"], 57)


if __name__ == "__main__":
    unittest.main()

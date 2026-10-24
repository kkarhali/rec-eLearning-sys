"""Metrics against the hand-computed examples of draft §5.4.1 (Table 19)."""
import math
import unittest

import numpy as np

from src.ml import metrics

TABLE19 = {
    "A": (["a", "b", "c", "d", "e"], {"b", "e", "x"}),
    "B": (["c", "f", "g", "h", "a"], {"z"}),
    "C": (["a", "c", "f", "b", "k"], {"a"}),
}


class TestTable19(unittest.TestCase):
    def test_per_learner_values(self):
        a = metrics.list_metrics(*TABLE19["A"], k=5)
        self.assertAlmostEqual(a["P"], 0.40)
        self.assertAlmostEqual(a["R"], 2 / 3)
        self.assertEqual(a["HR"], 1.0)
        self.assertAlmostEqual(a["NDCG"], 0.4776, places=4)       # 1.0178 / 2.1309
        self.assertAlmostEqual(a["RR"], 0.5)
        b = metrics.list_metrics(*TABLE19["B"], k=5)
        self.assertEqual((b["P"], b["R"], b["HR"], b["NDCG"], b["RR"]), (0.0, 0.0, 0.0, 0.0, 0.0))
        c = metrics.list_metrics(*TABLE19["C"], k=5)
        self.assertAlmostEqual(c["P"], 0.2)
        self.assertAlmostEqual(c["R"], 1.0)
        self.assertAlmostEqual(c["NDCG"], 1.0)
        self.assertAlmostEqual(c["RR"], 1.0)

    def test_dcg_details(self):
        self.assertAlmostEqual(1 / math.log2(3) + 1 / math.log2(6), 1.0178, places=4)
        self.assertAlmostEqual(1 + 1 / math.log2(3) + 0.5, 2.1309, places=4)

    def test_means_and_coverage(self):
        vals = [metrics.list_metrics(*TABLE19[u], k=5) for u in "ABC"]
        mean = {m: np.mean([v[m] for v in vals]) for m in vals[0]}
        self.assertAlmostEqual(mean["P"], 0.20)
        self.assertAlmostEqual(mean["R"], 0.5556, places=4)
        self.assertAlmostEqual(mean["HR"], 0.6667, places=4)
        self.assertAlmostEqual(mean["NDCG"], 0.4925, places=4)    # draft rounds to 0.49
        self.assertAlmostEqual(mean["RR"], 0.50)
        self.assertAlmostEqual(metrics.coverage([TABLE19[u][0] for u in "ABC"], 20), 0.45)

    def test_vectorised_matches_reference(self):
        """Same example through the vectorised evaluator (20-item catalogue, x and z unreachable)."""
        cat = list("abcdefghk") + [f"o{j}" for j in range(11)]          # 20 items; x, z not in catalogue
        I = len(cat)
        pos = {c: j for j, c in enumerate(cat)}
        U = 3
        scores = np.zeros((U, I))
        tgt = np.zeros((U, I), dtype=bool)
        unreach = np.zeros(U, dtype=int)
        for u, key in enumerate("ABC"):
            lst, T = TABLE19[key]
            for r, item in enumerate(lst):
                scores[u, pos[item]] = 10 - r
            for t in T:
                if t in pos:
                    tgt[u, pos[t]] = True
                else:
                    unreach[u] += 1
        cand = np.ones((U, I), dtype=bool)
        tb = np.random.default_rng(0).random((U, I))
        res = metrics.evaluate(scores, cand, tgt, unreach, np.ones(U, bool), tb, ks=(5,))
        pu = res["per_user"]
        np.testing.assert_allclose(pu["NDCG@5"], [0.4776, 0.0, 1.0], atol=1e-4)
        np.testing.assert_allclose(pu["P@5"], [0.4, 0.0, 0.2])
        np.testing.assert_allclose(pu["R@5"], [2 / 3, 0.0, 1.0])
        np.testing.assert_allclose(pu["MRR@5"], [0.5, 0.0, 1.0])
        self.assertAlmostEqual(res["coverage"][5], 0.45)


class TestSanity(unittest.TestCase):
    def test_oracle_gives_one(self):
        rng = np.random.default_rng(1)
        U, I = 50, 100
        tgt = rng.random((U, I)) < 0.05
        tgt[:, 0] = True
        cand = np.ones((U, I), dtype=bool)
        res = metrics.evaluate(tgt.astype(float), cand, tgt, np.zeros(U, int), np.ones(U, bool),
                               rng.random((U, I)), ks=(10,))
        np.testing.assert_allclose(res["per_user"]["NDCG@10"], 1.0)
        np.testing.assert_allclose(res["per_user"]["HR@10"], 1.0)

    def test_random_hr_matches_theory(self):
        """B1 check of draft §4.2.1: N = 300 candidates, 3 targets ⇒ HR@10 ≈ 0.097."""
        N, T, K, U = 300, 3, 10, 20000
        theory = 1 - math.comb(N - T, K) / math.comb(N, K)
        self.assertAlmostEqual(theory, 0.0970, places=4)
        rng = np.random.default_rng(2)
        tgt = np.zeros((U, N), dtype=bool)
        tgt[:, :T] = True
        res = metrics.evaluate(rng.random((U, N)), np.ones((U, N), bool), tgt, np.zeros(U, int),
                               np.ones(U, bool), rng.random((U, N)), ks=(K,))
        self.assertAlmostEqual(res["per_user"]["HR@10"].mean(), theory, delta=0.006)

    def test_candidates_and_ties(self):
        # non-candidates are never recommended; ties follow the tie-break key
        scores = np.array([[1.0, 1.0, 1.0, 5.0]])
        cand = np.array([[True, True, True, False]])
        tb = np.array([[0.3, 0.1, 0.2, 0.0]])
        order = metrics.rank_order(scores, cand, tb)[0]
        self.assertEqual(order.tolist(), [1, 2, 0, 3])
        ranks = metrics.candidate_ranks(scores, cand, tb)[0]
        self.assertEqual(ranks.tolist(), [3, 1, 2, 5])

    def test_unreachable_counts_in_idcg(self):
        res = metrics.evaluate(np.array([[2.0, 1.0]]), np.ones((1, 2), bool), np.array([[True, False]]),
                               np.array([1]), np.ones(1, bool), np.zeros((1, 2)), ks=(5,))
        self.assertAlmostEqual(res["per_user"]["NDCG@5"][0], 1 / (1 + 1 / math.log2(3)))
        self.assertAlmostEqual(res["per_user"]["R@5"][0], 0.5)

    def test_popularity_percentile(self):
        np.testing.assert_allclose(metrics.popularity_percentile(np.array([5, 1, 3])), [1.0, 0.0, 0.5])
        np.testing.assert_allclose(metrics.popularity_percentile(np.array([1, 1, 3])), [0.25, 0.25, 1.0])


if __name__ == "__main__":
    unittest.main()

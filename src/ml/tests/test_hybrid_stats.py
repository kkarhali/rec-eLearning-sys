"""Rank fusion (draft §4.4.4, Table 14) and statistics (draft §5.6–5.7)."""
import unittest

import numpy as np

from src.ml import hybrid, stats


class TestRankFusion(unittest.TestCase):
    def test_table14(self):
        # candidates i2, i3, i5 (columns 0..2); ranks per component as in Table 14
        cand = np.ones((1, 3), dtype=bool)
        tb = np.zeros((1, 3))
        recent = hybrid.rank_normalize(np.array([[3.0, 2.0, 1.0]]), cand, tb)   # i2 > i3 > i5
        wrmf = hybrid.rank_normalize(np.array([[1.0, 3.0, 2.0]]), cand, tb)     # i3 > i5 > i2
        iknn = hybrid.rank_normalize(np.array([[3.0, 1.0, 2.0]]), cand, tb)     # i2 > i5 > i3
        np.testing.assert_allclose(recent, [[1.0, 0.5, 0.0]])
        s1 = hybrid.fuse([recent, wrmf, iknn], (0.5, 0.3, 0.2))
        np.testing.assert_allclose(s1, [[0.70, 0.55, 0.25]])
        s2 = hybrid.fuse([recent, wrmf, iknn], (0.2, 0.6, 0.2))
        np.testing.assert_allclose(s2, [[0.40, 0.70, 0.40]])

    def test_rank_normalize_respects_candidates(self):
        cand = np.array([[True, False, True, True], [False, True, False, False]])
        r = hybrid.rank_normalize(np.array([[1.0, 9.0, 3.0, 2.0], [0.0, 1.0, 0.0, 0.0]]), cand,
                                  np.zeros((2, 4)))
        np.testing.assert_allclose(r, [[0.0, 0.0, 1.0, 0.5], [0.0, 1.0, 0.0, 0.0]])

    def test_simplex_grid_sizes(self):
        # budgeted grid (D-29): step 1/4 for 2–3 components, 1/3 for 4 ⇒ ≤ 20 settings
        for m, n in ((2, 5), (3, 15), (4, 20)):
            g = hybrid.simplex_grid(m)
            self.assertEqual(len(g), n)
            self.assertLessEqual(len(g), 20)
            np.testing.assert_allclose(g.sum(axis=1), 1.0)
            self.assertTrue((g >= 0).all())
        # sensitivity grid step 0.1 (draft §4.4.2)
        for m, n in ((2, 11), (3, 66), (4, 286)):
            self.assertEqual(len(hybrid.simplex_grid(m, 0.1)), n)

    def test_mid_rank_on_ties(self):
        """D-32: tied scores share the average rank; r̃ = 1 when |C_u| = 1."""
        cand = np.ones((1, 4), dtype=bool)
        r = hybrid.rank_normalize(np.array([[5.0, 3.0, 3.0, 1.0]]), cand)
        np.testing.assert_allclose(r, [[1.0, 0.5, 0.5, 0.0]])          # ranks 1, 2.5, 2.5, 4
        r = hybrid.rank_normalize(np.array([[2.0, 2.0, 2.0, 2.0]]), cand)
        np.testing.assert_allclose(r, [[0.5, 0.5, 0.5, 0.5]])
        one = np.array([[False, True, False, False]])
        np.testing.assert_allclose(hybrid.rank_normalize(np.array([[1.0, 0.0, 3.0, 2.0]]), one),
                                   [[0, 1, 0, 0]])
        np.testing.assert_allclose(hybrid.mid_ranks(np.array([[1.0, 1.0, 0.0]]), np.ones((1, 3), bool)),
                                   [[1.5, 1.5, 3.0]])

    def test_tune_weights_finds_oracle_component(self):
        rng = np.random.default_rng(0)
        U, I = 200, 30
        tgt = rng.random((U, I)) < 0.1
        cand = np.ones((U, I), dtype=bool)
        tb = rng.random((U, I))
        good = hybrid.rank_normalize(tgt + 0.01 * rng.random((U, I)), cand, tb)
        noise = hybrid.rank_normalize(rng.random((U, I)), cand, tb)
        w, best, _ = hybrid.tune_weights([noise, good], cand, tgt, np.zeros(U, int), tgt.any(axis=1), tb)
        self.assertGreaterEqual(w[1], 0.6)
        self.assertGreater(best, 0.9)

    def test_acceptance_rule(self):
        acc = hybrid.accept_component("x", [0.01, 0.02, 0.015, 0.03, 0.01, 0.02, 0.025, 0.01, 0.02])
        self.assertTrue(acc.accepted)
        rej = hybrid.accept_component("y", [0.01, -0.02, 0.015, -0.03, 0.01, 0.02, -0.025, 0.01, 0.0])
        self.assertFalse(rej.accepted)
        # stochastic: lift must exceed the SD across seeds
        self.assertFalse(hybrid.accept_component("z", [0.01] * 9, seed_sd=0.02).accepted)

    def test_greedy_forward(self):
        base = np.full(9, 0.40)
        table = {("rp",): base, ("wrmf",): base - 0.1, ("noise",): base - 0.2,
                 ("rp", "wrmf"): base + 0.03, ("rp", "noise"): base + np.r_[0.01, -0.01] .repeat([5, 4]),
                 ("rp", "wrmf", "noise"): base + 0.03}
        res = hybrid.greedy_forward(["rp", "wrmf", "noise"], lambda c: (table[tuple(c)], None), n_boot=2000)
        self.assertEqual(res.combination, ["rp", "wrmf"])
        self.assertIsNone(res.floor_component)

    def test_personalisation_floor(self):
        """D-30: if no personal component is accepted, the one with the largest lift is added and flagged."""
        base = np.full(9, 0.40)
        mixed = np.r_[0.01, -0.01].repeat([5, 4])
        table = {("rp",): base, ("knn",): base - 0.1, ("wrmf",): base - 0.2,
                 ("rp", "knn"): base + mixed, ("rp", "wrmf"): base + mixed - 0.002}
        res = hybrid.greedy_forward(["rp", "knn", "wrmf"], lambda c: (table[tuple(c)], None), n_boot=2000,
                                    personal={"knn", "wrmf"})
        self.assertEqual(res.combination, ["rp", "knn"])
        self.assertEqual(res.floor_component, "knn")


class TestStats(unittest.TestCase):
    def test_sign_flip_example(self):
        """§5.6.2: Δ = (0.030, 0.010, 0.025, −0.005) ⇒ p = 4/16 = 0.25."""
        self.assertAlmostEqual(stats.sign_flip_test([0.030, 0.010, 0.025, -0.005]), 0.25)

    def test_sign_flip_extremes(self):
        self.assertAlmostEqual(stats.sign_flip_test([0.1, 0.2, 0.3, 0.4]), 2 / 16)
        self.assertAlmostEqual(stats.sign_flip_test(np.linspace(0.01, 0.13, 13)), 2 / 8192)
        self.assertAlmostEqual(stats.sign_flip_test([0.0, 0.0, 0.0]), 1.0)
        mc = stats.sign_flip_test(np.linspace(0.01, 0.2, 22), exact_max_n=20, n_mc=20000)
        self.assertLess(mc, 0.001)

    def test_holm_example(self):
        """§5.6.3: (H1 .002, H2a .030, H3 .010, H4a .200, H4b .040)."""
        adj = stats.holm([0.002, 0.030, 0.010, 0.200, 0.040])
        np.testing.assert_allclose(adj, [0.010, 0.090, 0.040, 0.200, 0.090])
        self.assertEqual(list(adj < 0.05), [True, False, True, False, False])

    def test_bootstrap(self):
        d = np.array([0.030, 0.010, 0.025, -0.005])
        mean, lo, hi = stats.cluster_bootstrap_ci(d, n_boot=10000, seed=0)
        self.assertAlmostEqual(mean, 0.015)
        self.assertTrue(-0.005 <= lo < mean < hi <= 0.030)
        self.assertEqual(stats.cluster_bootstrap_ci(d, seed=1), stats.cluster_bootstrap_ci(d, seed=1))
        # constant differences ⇒ degenerate interval
        self.assertEqual(stats.cluster_bootstrap_ci([0.02] * 5)[1:], (0.02, 0.02))

    def test_verdicts_table19a(self):
        self.assertEqual(stats.verdict(0.031, 0.012, 0.049, 0.004), "confirmed")
        self.assertEqual(stats.verdict(0.006, -0.004, 0.015, 0.41), "refuted")
        self.assertEqual(stats.verdict(0.018, -0.003, 0.040, 0.12), "inconclusive")
        self.assertEqual(stats.verdict(0.024, 0.002, 0.047, 0.07), "inconclusive")
        self.assertEqual(stats.verdict(-0.027, -0.045, -0.010, 0.003), "refuted_reverse")

    def test_bidirectional_h3_table(self):
        """ADR-004 §2.2 six-level precedence table for H3."""
        v = stats.verdict_bidirectional
        self.assertEqual(v(0.030, 0.010, 0.050, 0.01), "superior_confirmed")
        self.assertEqual(v(-0.030, -0.050, -0.010, 0.01), "inferior_confirmed")
        self.assertEqual(v(0.001, -0.010, 0.012, 0.8), "equivalent")
        self.assertEqual(v(-0.015, -0.030, -0.002, 0.2), "inferior")
        self.assertEqual(v(0.000, -0.030, 0.015, 0.9), "refuted")
        self.assertEqual(v(0.010, -0.030, 0.050, 0.5), "inconclusive")

    def test_bootstrap_t(self):
        d = np.array([0.030, 0.010, 0.025, -0.005, 0.02, 0.0, 0.015])
        mean, lo, hi = stats.cluster_bootstrap_t_ci(d, n_boot=10000, seed=0)
        self.assertAlmostEqual(mean, d.mean())
        self.assertTrue(lo < mean < hi)
        self.assertEqual(stats.cluster_bootstrap_t_ci(d, seed=3), stats.cluster_bootstrap_t_ci(d, seed=3))
        self.assertEqual(stats.cluster_bootstrap_t_ci([0.02] * 5), (0.02, 0.02, 0.02))
        c = stats.compare(d)
        self.assertEqual((c["ci_lo"], c["ci_hi"]), (lo, hi))

    def test_bootstrap_t_coverage(self):
        """Calibrated interval should cover ≈ 95 % at n = 13 (ADR-004 §1: percentile ≈ 92 %)."""
        rng = np.random.default_rng(5)
        cover = 0
        n_sim = 300
        for k in range(n_sim):
            d = rng.normal(0.01, 0.03, 13)
            _, lo, hi = stats.cluster_bootstrap_t_ci(d, n_boot=2000, seed=k)
            cover += lo <= 0.01 <= hi
        self.assertGreater(cover / n_sim, 0.90)

    def test_margin_and_power(self):
        self.assertLess(stats.margin_test(np.full(9, 0.05) + np.linspace(-0.01, 0.01, 9)), 0.01)
        self.assertGreater(stats.margin_test(np.full(9, 0.0)), 0.5)
        self.assertTrue(stats.confirmed_with_margin(0.021))
        p = stats.confirmation_power(0.02, 0.02, n_sim=300, n_boot=1000)
        self.assertTrue(0.35 < p < 0.6)                        # ≈ 0.5 at μ = δ by construction
        self.assertGreater(stats.mde80(0.02, n_sim=200, n_boot=500), 0.02)


if __name__ == "__main__":
    unittest.main()


class TestDegenerate(unittest.TestCase):
    """D-52: identical unit lifts make some resamples degenerate (s_b = 0); the bound becomes ±∞ and is labelled."""

    def test_degenerate_label_and_verdict(self):
        d = np.array([0.0] * 7 + [0.01, 0.02])
        r = stats.cluster_bootstrap_t(d, n_boot=10000, seed=0)
        self.assertTrue(r["degenerate"])
        self.assertGreater(r["n_degenerate"], 0)
        # all-zero resamples lie below the mean (t* → −∞), so the UPPER bound is +∞
        self.assertEqual(r["hi"], float("inf"))
        self.assertTrue(np.isfinite(r["lo"]))
        c = stats.compare(d)
        self.assertIn("منحلّ", stats.format_ci(c))
        # +∞ upper bound prevents "refuted"; −∞ lower bound prevents "confirmed" (applied literally, D-52)
        self.assertNotIn(stats.verdict(c["mean"], c["ci_lo"], c["ci_hi"], 0.001), ("refuted", "refuted_reverse"))
        r2 = stats.cluster_bootstrap_t(-d, seed=0)
        self.assertEqual(r2["lo"], float("-inf"))
        self.assertEqual(stats.verdict(0.03, float("-inf"), float("inf"), 0.001), "inconclusive")

    def test_non_degenerate_unchanged(self):
        d = np.array([0.030, 0.010, 0.025, -0.005, 0.02, 0.0, 0.015])
        r = stats.cluster_bootstrap_t(d, seed=0)
        self.assertFalse(r["degenerate"])
        self.assertTrue(np.isfinite(r["lo"]) and np.isfinite(r["hi"]))

    def test_t_quantile(self):
        self.assertAlmostEqual(stats.t_quantile(0.975, 8), 2.3060, places=3)
        self.assertAlmostEqual(stats.t_quantile(0.975, 12), 2.1788, places=3)
        self.assertAlmostEqual(stats.t_quantile(0.5, 5), 0.0, places=6)

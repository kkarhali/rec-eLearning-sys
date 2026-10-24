"""Baselines against the worked examples of draft §4.2 (mini example of Table 11)."""
import unittest

import numpy as np

from src.ml import splits
from src.ml.models import CBF, EASE, SKNN, ItemKNN, Markov, Pop, RandomRec, RecentPop, WRMF, PersonalRepeat
from src.ml.models import ease, knn, markov, wrmf
from src.ml.models.baskets import consecutive_day_transitions, last_days_query, recency_rank
from src.ml.signals import SignalSpec
from src.ml.tests.helpers import MINI_TYPES, make_presentation, mini_example_events, random_presentation


def fold(events, types=MINI_TYPES, cut=70, phase="test"):
    return splits.make_fold(make_presentation(events, types), cut, phase)[0]


class TestItemKNN(unittest.TestCase):
    """Table 12 (λ = 1, binary columns)."""

    def setUp(self):
        self.tr = fold(mini_example_events())
        self.u4 = self.tr.user_index(4)

    def test_similarities(self):
        S = knn.item_similarity(self.tr.seen, 1.0)
        self.assertAlmostEqual(S[0, 1], 0.2041, places=4)        # sim(i1, i2)
        self.assertAlmostEqual(S[3, 1], 0.5443, places=4)        # sim(i4, i2)
        self.assertAlmostEqual(S[0, 2], 0.2887, places=4)        # sim(i1, i3)
        self.assertAlmostEqual(S[3, 2], 0.0, places=4)
        self.assertAlmostEqual(S[0, 4], 0.2041, places=4)
        self.assertAlmostEqual(S[3, 4], 0.2041, places=4)
        np.testing.assert_allclose(S, S.T)

    def test_scores(self):
        sb = ItemKNN(k=None, shrink=1.0, signal=SignalSpec("L0")).fit(self.tr).score()[self.u4]
        np.testing.assert_allclose(sb[[1, 2, 4]], [0.7485, 0.2887, 0.4082], atol=1e-4)
        sd = ItemKNN(k=None, shrink=1.0, signal=SignalSpec("L1")).fit(self.tr).score()[self.u4]
        np.testing.assert_allclose(sd[[1, 2, 4]], [0.9526, 0.5774, 0.6124], atol=1e-4)
        self.assertEqual(ItemKNN(k=None, shrink=1.0, signal=SignalSpec("L1")).fit(self.tr)
                         .recommend(4, k=3, exclude_seen=True), [2, 5, 3])

    def test_top_k_neighbours(self):
        S = knn.item_similarity(self.tr.seen, 0.0)
        Sk = knn.keep_top_k_per_column(S, 1)
        self.assertTrue(((Sk > 0).sum(axis=0) <= 1).all())
        for j in range(S.shape[1]):
            self.assertAlmostEqual(Sk[:, j].max(), S[:, j].max())


class TestSKNN(unittest.TestCase):
    """§4.2.5: neighbours n1={i1,i2,i4}, n2={i1,i3,i5}, n3={i2,i5}, n4={i4,i5}."""

    def build(self, query_days):
        ev = []
        for owner, items in ((11, (1, 2, 4)), (12, (1, 3, 5)), (13, (2, 5)), (14, (4, 5))):
            ev += [(owner, i, 3, 1) for i in items]                     # one weekly basket each
        for day, items in query_days:
            ev += [(4, i, day, 1) for i in items]
        return fold(ev)

    def test_sknn_example(self):
        tr = self.build([(30, (1, 4))])
        s = SKNN(L=1, k=3, M=None, variant="sknn").fit(tr).score()[tr.user_index(4)]
        np.testing.assert_allclose(s[[1, 2, 4]], [0.8165, 0.4082, 0.9082], atol=1e-4)

    def test_vsknn_example(self):
        tr = self.build([(28, (1,)), (30, (1, 4))])
        s = SKNN(L=2, k=3, M=None, variant="vsknn").fit(tr).score()[tr.user_index(4)]
        np.testing.assert_allclose(s[[1, 2, 4]], [0.8006, 0.4804, 0.8726], atol=1e-4)
        Q = last_days_query(tr, 2, "linear")[tr.user_index(4)]
        np.testing.assert_allclose(Q[[0, 3]], [1.5, 1.0])

    def test_own_baskets_excluded(self):
        tr = self.build([(30, (1, 4))])
        m = SKNN(L=1, k=50, M=None, variant="sknn").fit(tr)
        s = m.score()[tr.user_index(4)]
        # if u4's own basket {i1,i4} were a neighbour, i1 and i4 would get sim 1.0 extra
        self.assertAlmostEqual(s[0], 0.8165 + 0.4082, places=4)

    def test_recency_rank(self):
        np.testing.assert_array_equal(recency_rank(np.array([0, 0, 0, 1, 2, 2])), [2, 1, 0, 0, 1, 0])


class TestMarkov(unittest.TestCase):
    """§4.2.6 (γ = 0.5)."""

    def setUp(self):
        seqs = {1: [(1, 4), (2,), (1,)], 2: [(1,), (3, 5)], 3: [(4,), (2, 5), (5,)], 4: [(1, 4)]}
        ev = [(u, i, 10 + 2 * d, 1) for u, bs in seqs.items() for d, b in enumerate(bs) for i in b]
        self.tr = fold(ev)

    def test_counts_and_probabilities(self):
        N = consecutive_day_transitions(self.tr)
        np.testing.assert_array_equal(N[0], [0, 1, 1, 0, 1])     # from i1
        np.testing.assert_array_equal(N[3], [0, 2, 0, 0, 1])     # from i4
        P = markov.transition_probabilities(N, 0.5)
        np.testing.assert_allclose(P.sum(axis=1), 1.0)
        self.assertAlmostEqual(P[0, 1], 0.2727, places=4)
        self.assertAlmostEqual(P[3, 1], 0.4545, places=4)
        self.assertAlmostEqual(P[3, 2], 0.0909, places=4)

    def test_scores(self):
        s = Markov(gamma=0.5, L=1).fit(self.tr).score()[self.tr.user_index(4)]
        np.testing.assert_allclose(s[[1, 4, 2]], [0.3636, 0.2727, 0.1818], atol=1e-4)


class TestWRMF(unittest.TestCase):
    Y = np.array([[0.5, 0.1], [0.1, 0.6], [0.3, 0.2], [0.6, 0.2], [0.2, 0.5]])

    def test_single_learner_step(self):
        """§4.2.7: f = 2, λ = 0.1, α = 2, W = (2,0,0,1,0)."""
        C = np.array([[5.0, 1, 1, 3, 1]])
        P = np.array([[1.0, 0, 0, 1, 0]])
        A = wrmf.normal_matrices(C, self.Y, 0.1)[0]
        np.testing.assert_allclose(A, [[2.57, 0.83], [0.83, 0.92]], atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(A), 1.6755, places=4)
        x = wrmf.als_half_step(C, P, self.Y, 0.1)[0]
        np.testing.assert_allclose(x, [1.8162, -0.4429], atol=1e-4)
        np.testing.assert_allclose((self.Y @ x)[[1, 2, 4]], [-0.0841, 0.4563, 0.1418], atol=1e-4)
        xb = wrmf.als_half_step(np.array([[3.0, 1, 1, 3, 1]]), P, self.Y, 0.1)[0]
        np.testing.assert_allclose(xb, [1.7390, -0.4105], atol=1e-4)
        np.testing.assert_allclose((self.Y @ xb)[[1, 2, 4]], [-0.0724, 0.4396, 0.1425], atol=1e-4)

    def test_loss_monotone(self):
        rng = np.random.default_rng(0)
        W = (rng.random((80, 30)) < 0.2) * rng.integers(1, 6, (80, 30))
        P = (W > 0).astype(float)
        C = 1 + 5.0 * W
        _, _, losses, _ = wrmf.als(C, P, 6, 0.1, 15, seed=0, track_loss=True)
        self.assertTrue(np.all(np.diff(losses) <= 1e-6 * abs(losses[0])), losses)

    def test_recovers_low_rank(self):
        rng = np.random.default_rng(1)
        Xt, Yt = rng.normal(size=(60, 3)), rng.normal(size=(25, 3))
        M = Xt @ Yt.T
        C = np.ones_like(M)
        X, Y, _, _ = wrmf.als(C, M, 3, 1e-6, 50, seed=0)
        self.assertLess(np.abs(X @ Y.T - M).max(), 1e-3)

    def test_deterministic_given_seed_and_snapshots(self):
        tr = splits.make_fold(random_presentation(seed=4), 126, "tune")[0]
        a = WRMF(seed=3, f=8, iters=10).fit(tr).score()
        b = WRMF(seed=3, f=8, iters=10).fit(tr).score()
        np.testing.assert_array_equal(a, b)
        m = WRMF(seed=3, f=8, iters=15, checkpoints=(10, 15)).fit(tr)
        np.testing.assert_array_equal(m.scores_at(10), a)


class TestEASE(unittest.TestCase):
    def test_closed_form_kkt(self):
        """Off-diagonal gradient of ‖X − XB‖² + λ‖B‖² vanishes and diag(B) = 0."""
        rng = np.random.default_rng(0)
        X = (rng.random((40, 12)) < 0.3).astype(float)
        lam = 10.0
        B = ease.ease_weights(X, lam)
        np.testing.assert_allclose(np.diag(B), 0.0)
        grad = (X.T @ X + lam * np.eye(12)) @ B - X.T @ X
        off = grad - np.diag(np.diag(grad))
        np.testing.assert_allclose(off, 0.0, atol=1e-9)

    def test_model_and_space(self):
        tr = fold(mini_example_events())
        m = EASE(lam=1.0).fit(tr)
        np.testing.assert_allclose(m.score(), tr.seen @ m.B)
        self.assertEqual([c["lam"] for c in EASE.param_space()], [1.0, 10.0, 50.0, 100.0, 500.0])


class TestSpaces(unittest.TestCase):
    def test_adr004_spaces(self):
        self.assertEqual([c["w"] for c in RecentPop.param_space()], [3, 7, 14, 21, 28])
        self.assertEqual(sorted({c["f"] for c in WRMF.param_space()}), [16, 32, 64])
        from src.ml.harness import model_configs
        for name in ("B4_ItemKNN", "B5_SKNN", "B7_WRMF", "B9_CBF", "B3_RecentPop", "B10_EASE"):
            self.assertLessEqual(len(model_configs(name)), 20, name)


class TestSimpleAndCBF(unittest.TestCase):
    def test_pop_and_recent_pop(self):
        tr = fold(mini_example_events())
        np.testing.assert_array_equal(tr.popularity(), [3, 2, 1, 3, 2])
        s = Pop().fit(tr).score()
        self.assertTrue((s == s[0]).all())
        ev = [(1, 1, 60, 1), (2, 1, 69, 1), (2, 2, 70, 1), (3, 2, 50, 1), (3, 3, 65, 1), (1, 3, 64, 1)]
        tr2 = fold(ev)
        np.testing.assert_array_equal(RecentPop(w=7).fit(tr2).score()[0], [1, 1, 2])  # d > 63
        np.testing.assert_array_equal(RecentPop(w=14).fit(tr2).score()[0], [2, 1, 2])

    def test_personal_repeat(self):
        ev = [(1, 1, 30, 1), (1, 1, 50, 1), (1, 1, 55, 1), (1, 2, 20, 1), (1, 2, 40, 1), (1, 3, 54, 1),
              (1, 4, 10, 1)]
        tr = fold(ev, cut=70, phase="tune")             # t0 = 56
        s = PersonalRepeat(tau=14.0).fit(tr).score()[0]
        np.testing.assert_allclose(s, [1.7386, 0.3953, 0.8669, 0.0374], atol=1e-4)
        self.assertEqual(PersonalRepeat.tasks, ("B",))

    def test_cbf_example(self):
        """§4.2.9: features [type one-hot, first-use week / 10], profile weighted by days."""
        first_day = {1: 8, 2: 22, 3: 9, 4: 15, 5: 16}            # weeks 1, 3, 1, 2, 2
        ev = [(9, i, d, 1) for i, d in first_day.items()]
        ev += [(4, 1, 30, 1), (4, 1, 33, 1), (4, 4, 31, 1)]       # u4: i1 two days, i4 one day
        tr = fold(ev)
        s = CBF(w_type=1.0, w_week=1.0, w_assess=0.0).fit(tr).score()[tr.user_index(4)]
        np.testing.assert_allclose(s[[1, 4, 2]], [0.0506, 0.0345, 0.0175], atol=1e-4)

    def test_random_seeds(self):
        tr = fold(mini_example_events())
        a = RandomRec(seed=0).fit(tr).score()
        b = RandomRec(seed=0).fit(tr).score()
        c = RandomRec(seed=1).fit(tr).score()
        np.testing.assert_array_equal(a, b)
        self.assertFalse(np.allclose(a, c))

    def test_recommend_interface(self):
        tr = fold(mini_example_events())
        recs = Pop().fit(tr).recommend(4, k=3, exclude_seen=True)
        self.assertEqual(set(recs), {2, 3, 5})
        self.assertEqual(recs[-1], 3)                            # i3 least popular
        self.assertEqual(len(Pop().fit(tr).recommend(4, k=5, exclude_seen=False)), 5)


if __name__ == "__main__":
    unittest.main()

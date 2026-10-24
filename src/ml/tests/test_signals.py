"""Nested signal family against draft §3.4.1 (Tables 7–8) and §3.5."""
import math
import unittest

import numpy as np

from src.ml import signals, splits
from src.ml.signals import SignalSpec
from src.ml.tests.helpers import make_presentation

# Table 7: t0 = 56, τ = 14, β = 0.5, illustrative medians
EXAMPLE = {
    "i1": ([30, 50, 55], [10, 5, 5], 5.0),
    "i2": ([20, 40], [3, 6], 3.0),
    "i3": ([54], [24], 12.0),
    "i4": ([10], [1], 1.0),
}
TABLE8 = {  # L1, L2, L3, WRMF confidence (α = 2)
    "i1": (3, 1.7386, 2.3728, 5.7457),
    "i2": (2, 0.3953, 0.5970, 2.1940),
    "i3": (1, 0.8669, 1.3431, 3.6861),
    "i4": (1, 0.0374, 0.0504, 1.1008),
}


def level_value(spec, item):
    days, clicks, med = EXAMPLE[item]
    return signals.event_weights(spec, 56, days, clicks, np.full(len(days), med)).sum()


class TestTable8(unittest.TestCase):
    def test_factors(self):
        self.assertAlmostEqual(math.exp(-26 / 14), 0.1561, places=4)
        np.testing.assert_allclose(signals.recency_factor(56, [30, 50, 55], 14), [0.1561, 0.6514, 0.9311],
                                   atol=1e-4)
        np.testing.assert_allclose(signals.intensity_factor([10, 5, 5], 5.0, 0.5), [1.5493, 1.3466, 1.3466],
                                   atol=1e-4)

    def test_levels(self):
        for item, (l1, l2, l3, conf) in TABLE8.items():
            self.assertAlmostEqual(level_value(SignalSpec("L1"), item), l1)
            self.assertAlmostEqual(level_value(SignalSpec("L2", tau=14), item), l2, places=4)
            self.assertAlmostEqual(level_value(SignalSpec("L3", tau=14, beta=0.5), item), l3, places=4)
            _, C = signals.wrmf_preference_confidence(np.array([[l3]]), 2.0)
            self.assertAlmostEqual(C[0, 0], conf, delta=2e-4)

    def test_rankings(self):
        def order(spec):
            v = {i: level_value(spec, i) for i in EXAMPLE}
            return sorted(v, key=lambda i: -v[i])
        self.assertEqual(order(SignalSpec("L2", tau=14)), ["i1", "i3", "i2", "i4"])
        self.assertEqual(order(SignalSpec("L3", tau=14, beta=0.5)), ["i1", "i3", "i2", "i4"])

    def test_nesting_special_cases(self):
        """β = 0, τ = ∞ ⇒ days; L3 with β = 0 ⇒ L2."""
        for item in EXAMPLE:
            self.assertAlmostEqual(level_value(SignalSpec("L3", tau=math.inf, beta=0.0), item),
                                   level_value(SignalSpec("L1"), item))
            self.assertAlmostEqual(level_value(SignalSpec("L3", tau=14, beta=0.0), item),
                                   level_value(SignalSpec("L2", tau=14), item))


class TestSignalMatrix(unittest.TestCase):
    def setUp(self):
        types = {1: "forumng", 2: "oucontent", 3: "quiz", 4: "resource"}
        ev = [(7, 1, 30, 10), (7, 1, 50, 5), (7, 1, 55, 5), (7, 2, 20, 3), (7, 2, 40, 6), (7, 3, 54, 24),
              (7, 4, 10, 1), (8, 1, 12, 5), (8, 3, 12, 12), (8, 2, 2, 3), (7, 2, 60, 99)]   # day 60 > t0
        p = make_presentation(ev, types)
        self.train, _ = splits.make_fold(p, 70, "tune")       # t0 = 56

    def test_type_medians_from_training_only(self):
        # oucontent daily clicks before t0: 3, 6, 3 → median 3 (day-60 row is excluded)
        self.assertEqual(self.train.type_medians["oucontent"], 3.0)
        self.assertEqual(self.train.type_medians["quiz"], 18.0)

    def test_levels_on_matrix(self):
        W0 = signals.signal_matrix(self.train, SignalSpec("L0"))
        W1 = signals.signal_matrix(self.train, SignalSpec("L1"))
        W2 = signals.signal_matrix(self.train, SignalSpec("L2", tau=14))
        u = self.train.user_index(7)
        np.testing.assert_array_equal(W0[u], [1, 1, 1, 1])
        np.testing.assert_array_equal(W1[u], [3, 2, 1, 1])
        np.testing.assert_allclose(W2[u], [1.7386, 0.3953, 0.8669, 0.0374], atol=1e-4)
        self.assertTrue(((W1 > 0) == (W0 > 0)).all())

    def test_binary_confidence(self):
        W = np.array([[0.0, 2.0]])
        P, C = signals.wrmf_preference_confidence(W, 3.0, binary_confidence=True)
        np.testing.assert_array_equal(P, [[0, 1]])
        np.testing.assert_array_equal(C, [[1, 4]])


if __name__ == "__main__":
    unittest.main()

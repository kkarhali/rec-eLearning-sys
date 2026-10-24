"""GRU-lite unit tests: gradients, masking (S6), truncation, worked example of draft §4.6.4."""
import unittest

import numpy as np

from src.ml import splits
from src.ml.models import gru_lite as G
from src.ml.tests.helpers import make_presentation, mini_example_events, MINI_TYPES


def _small(seed=0):
    rng = np.random.default_rng(seed)
    I = 6
    p = G.init_params(I, 4, 3, seed=seed, dtype=np.float64)
    for b in G.BIASES:
        p[b] = rng.normal(0, 0.1, p[b].shape)
    seqs = G.Sequences.from_lists([[[0], [1, 2]], [[1], [3], [4, 5], [0]], [[2], [5], [1, 3], [0], [4], [2]]], I)
    return p, seqs, rng


class TestGRU(unittest.TestCase):
    def test_worked_example_442(self):
        """§4.6.4: one forward step with d_e = d_h = 2, h0 = 0, zero biases."""
        p = {k: None for k in G.MATS + G.BIASES}
        E = np.zeros((5, 2))
        E[0], E[3] = (0.2, 0.1), (0.4, 0.0)
        p.update(E=E, Wz=np.array([[0.5, -0.3], [0.2, 0.4]]).T, Wr=np.array([[0.3, 0.1], [-0.2, 0.5]]).T,
                 Wh=np.array([[1.0, 0.5], [-0.5, 1.0]]).T, Uz=np.zeros((2, 2)), Ur=np.zeros((2, 2)),
                 Uh=np.zeros((2, 2)), V=np.array([[0.5, 0.2], [1.0, -0.5], [0.1, 0.1], [-0.3, 0.8], [0.6, 0.6]]).T,
                 bz=np.zeros(2), br=np.zeros(2), bh=np.zeros(2), c=np.zeros(5))
        A = np.zeros((1, 1, 5))
        A[0, 0, [0, 3]] = 0.5
        Y = np.zeros((1, 1, 5))
        Y[0, 0, [1, 4]] = 0.5
        h1 = G.forward_states(p, A, np.ones((1, 1)))
        np.testing.assert_allclose(h1[0], [0.1676, -0.0518], atol=1e-4)
        loss, g, _ = G.window_loss_grad(p, A, Y, np.ones((1, 1)), np.ones((1, 1)), np.zeros((1, 2)), l2=0.0)
        self.assertAlmostEqual(loss, 1.5335, places=4)
        # draft's W_h[1,1] (input e_1 → hidden 1) = our Wh[0, 0] in row-vector convention
        self.assertAlmostEqual(g["Wh"][0, 0], -0.054780, places=5)

    def test_gradient_check(self):
        p, seqs, rng = _small(1)
        A, Y, m, tm = seqs.dense_batch([0, 1, 2], "next-new", dtype=np.float64)
        h0 = rng.normal(0, 0.5, (3, 3))
        _, g, _ = G.window_loss_grad(p, A, Y, m, tm, h0)
        for k in p:
            flat = p[k].ravel()
            for j in range(min(flat.size, 8)):
                old = flat[j]
                flat[j] = old + 1e-6
                lp = G.window_loss_grad(p, A, Y, m, tm, h0, need_grad=False)[0]
                flat[j] = old - 1e-6
                lm = G.window_loss_grad(p, A, Y, m, tm, h0, need_grad=False)[0]
                flat[j] = old
                gn = (lp - lm) / 2e-6
                ga = g[k].ravel()[j]
                self.assertLess(abs(ga - gn) / max(abs(ga), abs(gn), 1e-6), 1e-4, (k, j))

    def test_padded_steps_keep_state(self):
        """S6: a padded step leaves h unchanged and contributes no loss."""
        p, seqs, rng = _small(2)
        A, Y, m, tm = seqs.dense_batch([0, 2], "next", dtype=np.float64)
        self.assertEqual(m[:, 0].tolist(), [1, 0, 0, 0, 0])
        h_after_1 = G.forward_states(p, A[:1, :1], m[:1, :1])
        h_all = G.forward_states(p, A[:, :1], m[:, :1])
        np.testing.assert_allclose(h_after_1, h_all)
        # loss of the batch equals the sum of per-sequence losses with the batch normaliser
        n = tm.sum()
        l_both = G.window_loss_grad(p, A, Y, m, tm, np.zeros((2, 3)), l2=0.0, need_grad=False)[0]
        l0 = G.window_loss_grad(p, A[:, :1], Y[:, :1], m[:, :1], tm[:, :1], np.zeros((1, 3)), l2=0.0,
                                n_norm=n, need_grad=False)[0]
        l1 = G.window_loss_grad(p, A[:, 1:], Y[:, 1:], m[:, 1:], tm[:, 1:], np.zeros((1, 3)), l2=0.0,
                                n_norm=n, need_grad=False)[0]
        self.assertAlmostEqual(l_both, l0 + l1)

    def test_truncation_with_long_window_equals_full(self):
        """S1 companion: windows of T ≥ length reproduce the untruncated loss; state carried without gradient."""
        p, seqs, _ = _small(3)
        A, Y, m, tm = seqs.dense_batch([0, 1, 2], "next", dtype=np.float64)
        h0 = np.zeros((3, 3))
        full = G.window_loss_grad(p, A, Y, m, tm, h0, l2=0.0, need_grad=False)[0]
        n = tm.sum()
        part, h = 0.0, h0
        for w0 in range(0, A.shape[0], 2):               # T = 2 < length: same forward values
            sl = slice(w0, w0 + 2)
            l, _, h = G.window_loss_grad(p, A[sl], Y[sl], m[sl], tm[sl], h, l2=0.0, n_norm=n, need_grad=False)
            part += l
        self.assertAlmostEqual(full, part)

    def test_targets(self):
        seqs = G.Sequences.from_lists([[[0, 1], [1, 2], [0, 2], [3]]], 4)
        _, Yn, _, tmn = seqs.dense_batch([0], "next")
        _, Yw, _, tmw = seqs.dense_batch([0], "next-new")
        np.testing.assert_allclose(Yn[:, 0], [[0, .5, .5, 0], [.5, 0, .5, 0], [0, 0, 0, 1]])
        np.testing.assert_allclose(Yw[:, 0], [[0, 0, 1, 0], [0, 0, 0, 0], [0, 0, 0, 1]])
        self.assertEqual(tmw[:, 0].tolist(), [1, 0, 1])           # empty new-target step masked

    def test_model_masking_task_a(self):
        """S6: the harness masks seen items in task A; GRU recommend() never returns a seen item."""
        tr = splits.make_fold(make_presentation(mini_example_events(), MINI_TYPES), 70, "test")[0]
        m = G.GRULite(seed=0, epochs=2).fit(tr)
        recs = m.recommend(4, k=5, exclude_seen=True)
        self.assertEqual(set(recs), {2, 3, 5})
        self.assertEqual(m.score().shape, (tr.n_users, tr.n_items))
        self.assertEqual(len(G.GRULite.param_space()), 6)

    def test_adam_clipping(self):
        p = {"x": np.array([1.0, 1.0])}
        opt = G.Adam(p, 0.1)
        norm = opt.step(p, {"x": np.array([300.0, 400.0])})
        self.assertAlmostEqual(norm, 500.0)
        np.testing.assert_allclose(p["x"], [0.9, 0.9], atol=1e-6)   # first Adam step = lr · sign


if __name__ == "__main__":
    unittest.main()

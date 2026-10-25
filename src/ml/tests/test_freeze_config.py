"""freeze_config --checklist (D-84): the λ-row filter with NaN notes, and the literal ش8 sign-off line."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.ml import data
from src.ml.experiments import freeze_config as F


class _TmpRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for d in ("results/dev2013", "results/frozen", "results/dryrun2013", "docs/meetings", "docs/working"):
            (self.root / d).mkdir(parents=True)
        (self.root / "docs/working/02-hypotheses-algorithms.md").write_text("جدول 2-ب\n", encoding="utf-8")
        self.old = data.REPO_ROOT, data.RESULTS_DIR, F.DEV, F.FROZEN
        data.REPO_ROOT, data.RESULTS_DIR = self.root, self.root / "results"
        F.DEV, F.FROZEN = self.root / "results/dev2013", self.root / "results/frozen"

    def tearDown(self):
        data.REPO_ROOT, data.RESULTS_DIR, F.DEV, F.FROZEN = self.old
        self.tmp.cleanup()

    def row(self, md, key):
        return next(l for l in md.splitlines() if l.startswith(f"| {key} |"))


class TestLambdaFilter(_TmpRepo):
    def test_nan_note_does_not_crash_and_only_lambda_row_dropped(self):
        """The final reproduce_dev crashed here (pandas 3.0.5): empty notes are NaN floats."""
        pd.DataFrame({"file": ["baselines.csv", "gru.csv", "h4a_auc.csv vs learner_auc.csv (day 56)"],
                      "metric": ["NDCG@10", "NDCG@10", "ROC_AUC"], "rows_compared": [3780, 1080, 45],
                      "max_abs_diff": [0.0, 2e-7, 0.0036],
                      "note": [np.nan, np.nan, "dev: λ chosen by nested inner LOPO; dry run: frozen λ (D-58)"]}).to_csv(
            self.root / "results/dryrun2013/dryrun_vs_dev.csv", index=False)
        for flag in (True, False):                       # with and without pandas string inference
            with pd.option_context("future.infer_string", flag):
                r7 = self.row(F.checklist(), "ش7")
            self.assertIn("max |Δ| = 2e-07", r7)         # the λ row (0.0036) is dropped, the 2e-7 row is kept

    def test_documented_command_on_this_repo(self):
        data.REPO_ROOT, data.RESULTS_DIR, F.DEV, F.FROZEN = self.old
        if not (data.RESULTS_DIR / "dryrun2013" / "dryrun_vs_dev.csv").exists():
            self.skipTest("no dry run here")
        self.assertIn("| ش7 |", F.checklist())


class TestPeerSignoff(_TmpRepo):
    def f(self):
        return self.root / F.PEER_SIGNOFF

    def test_missing_file(self):
        self.assertFalse(F.peer_final_approval(self.f()))
        self.assertIn("| ✗ |", self.row(F.checklist(), "ش8"))

    def test_not_approved(self):
        self.f().write_text("# توقيع\n\n**الحكم النهائي: غير موافق في الحالة الحالية**\nموافق على D-47\n", encoding="utf-8")
        self.assertFalse(F.peer_final_approval(self.f()))
        self.assertIn("| ✗ |", self.row(F.checklist(), "ش8"))

    def test_literal_line(self):
        for line in ("الحكم النهائي: موافق", "**الحكم النهائي: موافق**", "## الحكم النهائي: موافق"):
            self.f().write_text(f"# توقيع\n\n{line}\n", encoding="utf-8")
            self.assertTrue(F.peer_final_approval(self.f()), line)
            self.assertIn("| ✓ |", self.row(F.checklist(), "ش8"))
        self.f().write_text("الحكم النهائي: موافق بشرط\n", encoding="utf-8")
        self.assertFalse(F.peer_final_approval(self.f()))


if __name__ == "__main__":
    unittest.main()

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


class TestDryRunRehearsal(unittest.TestCase):
    """ش7: the dry run evaluates every guard without stopping and audits the access log for 2014 reads."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "conf2014"

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_tree_passes_with_tag_at_head(self):
        r = RC.guard_rehearsal("freeze-03", self.out, git=fake_git(tag_exists=False))
        self.assertFalse(r["tag_exists"])
        self.assertTrue(r["tree_clean"] and r["conf2014_absent"])
        self.assertEqual(r["check_guards_with_tag_at_HEAD"], "pass")

    def test_blocked_reported_not_raised(self):
        r = RC.guard_rehearsal("freeze-03", self.out, git=fake_git(tag_exists=False, dirty=" M a.py"))
        self.assertFalse(r["tree_clean"])
        self.assertTrue(r["check_guards_with_tag_at_HEAD"].startswith("blocked"))

    def test_audit_flags_full_read(self):
        import json

        class Ctx:
            loaded = {"load_daily_events": {"AAA_2013J"}}

            def presentations(self):
                return {"AAA_2013J": None}
        log = Path(self.tmp.name) / "access_log.jsonl"
        old = RC.data.RESULTS_DIR
        try:
            RC.data.RESULTS_DIR = Path(self.tmp.name)
            log.write_text("")
            before = RC.access_log_lines()
            log.write_text(json.dumps({"columns": ["code_module", "code_presentation", "id_student"]}) + "\n")
            self.assertTrue(RC.audit_2014(before, Ctx())["ok"])
            with open(log, "a") as f:
                f.write(json.dumps({"event": "confirmatory_full_read"}) + "\n")
            self.assertFalse(RC.audit_2014(before, Ctx())["ok"])
            Ctx.loaded = {"load_daily_events": {"AAA_2014J"}}
            log.write_text("")
            self.assertFalse(RC.audit_2014(before, Ctx())["ok"])
        finally:
            RC.data.RESULTS_DIR = old


class TestPeerM1M2M3(unittest.TestCase):
    """Peer review of freeze-03: m2 (phase 2 verifies LOCK and HEAD = tag), m3 (raw MD5 compared to the frozen value)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _lock(self, commit="aaa", tag="freeze-03"):
        import json
        (self.d / "verdicts.csv").write_text("h,v\n")
        (self.d / "verdicts.md").write_text("# v\n")
        (self.d / "LOCK").write_text(json.dumps({"tag": tag, "commit": commit,
                                                  "verdicts_csv_sha256": RC.sha256(self.d / "verdicts.csv"),
                                                  "verdicts_md_sha256": RC.sha256(self.d / "verdicts.md")}))

    def test_lock_ok(self):
        self._lock()
        self.assertEqual(RC.verify_lock(self.d, "freeze-03", dry=False, git=fake_git())["commit"], "aaa")
        self.assertEqual(RC.verify_lock(self.d, "freeze-03", dry=True, git=fake_git(tag_exists=False))["commit"], "aaa")

    def test_lock_refusals(self):
        with self.assertRaises(RC.GuardError):                       # no LOCK
            RC.verify_lock(self.d, "freeze-03", dry=False, git=fake_git())
        self._lock()
        with self.assertRaises(RC.GuardError):                       # HEAD moved after phase 1
            RC.verify_lock(self.d, "freeze-03", dry=False, git=fake_git(head="bbb", tag="bbb"))
        with self.assertRaises(RC.GuardError):                       # HEAD is not the tag
            RC.verify_lock(self.d, "freeze-03", dry=False, git=fake_git(tag="ccc"))
        with self.assertRaises(RC.GuardError):                       # no tag in confirmatory mode
            RC.verify_lock(self.d, "freeze-03", dry=False, git=fake_git(tag_exists=False))
        (self.d / "verdicts.md").write_text("# edited after LOCK\n")
        with self.assertRaises(RC.GuardError):
            RC.verify_lock(self.d, "freeze-03", dry=True, git=fake_git())

    def test_raw_md5_compared(self):
        import hashlib
        import json
        raw, fz = self.d / "raw", self.d / "frozen"
        raw.mkdir(), fz.mkdir()
        names = ["assessments.csv", "courses.csv", "studentAssessment.csv", "studentInfo.csv",
                 "studentRegistration.csv", "studentVle.csv", "vle.csv"]
        for n in names:
            (raw / n).write_text(n)
        for n in ("mde80.json", "hybrid_frozen.json", "risk_final.json"):
            (fz / n).write_text("{}")
        cfg = {"sha256": {n: RC.sha256(fz / n) for n in ("mde80.json", "hybrid_frozen.json", "risk_final.json")},
               "raw_md5": {n: {"md5": hashlib.md5(n.encode()).hexdigest()} for n in names}}
        (fz / "freeze03_config.json").write_text(json.dumps(cfg))
        old = RC.FROZEN, RC.DEV, RC.data.RAW_DIR
        try:
            RC.FROZEN, RC.DEV, RC.data.RAW_DIR = fz, fz, raw
            self.assertEqual(len(RC.check_integrity()["raw_md5_checked"]), 7)
            (raw / "studentVle.csv").write_text("changed")
            with self.assertRaises(RC.GuardError):
                RC.check_integrity()
        finally:
            RC.FROZEN, RC.DEV, RC.data.RAW_DIR = old


def repo_git(head="aaa", tag="aaa", status="", tagged_log="", tag_exists=True):
    def git(*args):
        if args[:1] == ("rev-parse",) and args[1].endswith("^{commit}"):
            if not tag_exists:
                raise RuntimeError("no tag")
            return tag
        if args == ("rev-parse", "HEAD"):
            return head
        if args == ("status", "--porcelain"):
            return status
        if args[:1] == ("show",):
            return tagged_log
        raise AssertionError(args)
    return git


class TestD75Resume(unittest.TestCase):
    """D-75: clean-tree exemptions, LOCK over every phase-1 file, and the three --resume outcomes."""

    def setUp(self):
        import json
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "results").mkdir()
        self.log = self.root / "results" / "access_log.jsonl"
        self.log.write_text('{"a": 1}\n' + json.dumps({"event": "confirmatory_full_read", "commit": "aaa"}) + "\n")
        self.out = self.root / "results" / "conf2014"
        self.old = RC.data.REPO_ROOT, RC.data.RESULTS_DIR
        RC.data.REPO_ROOT, RC.data.RESULTS_DIR = self.root, self.root / "results"

    def tearDown(self):
        RC.data.REPO_ROOT, RC.data.RESULTS_DIR = self.old
        self.tmp.cleanup()

    def _phase1(self, lock=True):
        import json

        class Ctx:
            tag, commit, out = "freeze-03", "aaa", self.out
        (self.out / "figures").mkdir(parents=True)
        (self.out / ".lock").write_text(json.dumps({"tag": "freeze-03", "commit": "aaa"}))
        for f in ("verdicts.csv", "verdicts.md", "secondary.csv", "figures/fig1.svg", "figures/fig1.png"):
            (self.out / f).write_text(f)
        (self.out / "deviations.md").write_text("# d\n\nلا شيء.\n")
        if lock:
            RC.write_lock(Ctx())

    def test_exemptions(self):
        st = " M results/access_log.jsonl\n?? results/conf2014_aborted_1/\n?? results/conf2014_aborted_1.sha256.json"
        self.assertEqual(RC.dirty_paths("freeze-03", repo_git(status=st, tagged_log='{"a": 1}')), [])
        # the tagged log is not a prefix (a line was edited, not appended) → not exempt
        self.assertEqual(len(RC.dirty_paths("freeze-03", repo_git(status=st, tagged_log='{"a": 2}'))), 1)
        self.assertEqual(len(RC.dirty_paths("freeze-03", repo_git(status=" M src/ml/data.py"))), 1)
        self.assertEqual(RC.check_guards("freeze-03", self.out, git=repo_git(status=st, tagged_log='{"a": 1}')), "aaa")
        self.out.mkdir()
        with self.assertRaises(RC.GuardError):
            RC.check_guards("freeze-03", self.out, git=repo_git())
        self.assertEqual(RC.check_guards("freeze-03", self.out, git=repo_git(status="?? results/conf2014/"), resume=True), "aaa")

    def test_guard_scope(self):
        """The clean-tree guard covers code, data and results only; docs/ and deliverables/ are outside it."""
        st = (" M docs/working/03-analysis-design.md\n M deliverables/x.docx\n?? .claude/settings.json\n"
              "?? results/dryrun2013/LOCK\n M README.md\n D \"deliverables/.~lock.x#\"")
        self.assertEqual(RC.dirty_paths("freeze-03", repo_git(status=st)), [])
        for line in (" M src/ml/data.py", "?? scripts/new.py", " M results/dev2013/summary.md", "?? data/raw/x.csv",
                     "?? run.py", " M requirements.txt", "R  src/a.py -> src/b.py"):
            self.assertEqual(RC.dirty_paths("freeze-03", repo_git(status=line)), [line], line)
        self.assertEqual(RC.check_guards("freeze-03", self.out, git=repo_git(status=st)), "aaa")

    def test_head_moved_message(self):
        self._phase1()
        with self.assertRaisesRegex(RC.GuardError, "HEAD moved"):
            RC.verify_lock(self.out, "freeze-03", dry=True, git=repo_git(head="bbb"))

    def test_lock_covers_phase1_files(self):
        import json
        self._phase1()
        lock = json.loads((self.out / "LOCK").read_text())
        self.assertEqual(set(lock["files"]), {"verdicts.csv", "verdicts.md", "secondary.csv", "figures/fig1.svg", "figures/fig1.png"})
        (self.out / "figures/fig1.png").write_text("changed")
        with self.assertRaises(RC.GuardError):
            RC.verify_lock(self.out, "freeze-03", dry=False, git=repo_git())

    def test_resume_before_lock(self):
        import json
        self._phase1(lock=False)
        info = RC.resume_prepare(self.out, "freeze-03", git=repo_git(status="?? results/conf2014/"))
        self.assertEqual(info["action"], "phase1")
        self.assertFalse(self.out.exists())
        self.assertTrue((self.root / "results" / "conf2014_aborted_1" / "verdicts.csv").exists())
        man = json.loads((self.root / "results" / "conf2014_aborted_1.sha256.json").read_text())
        self.assertEqual(len(man), 7)
        self.assertIn('"confirmatory_resume"', self.log.read_text())
        self.out.mkdir()
        RC.record_resume_deviation(self.out, info)
        self.assertIn("conf2014_aborted_1", (self.out / "deviations.md").read_text())

    def test_resume_after_lock(self):
        self._phase1()
        (self.out / "fairness.csv").write_text("partial phase 2")
        info = RC.resume_prepare(self.out, "freeze-03", git=repo_git(status="?? results/conf2014/"))
        self.assertEqual(info["action"], "phase2")
        self.assertEqual(info["removed_unlocked"], ["fairness.csv"])
        self.assertTrue((self.out / "verdicts.csv").exists() and (self.out / "deviations.md").exists())

    def test_resume_refusals(self):
        import json
        self._phase1()
        g = repo_git(status="?? results/conf2014/")
        (self.out / "secondary.csv").write_text("tampered")
        with self.assertRaises(RC.GuardError):
            RC.resume_prepare(self.out, "freeze-03", git=g)                       # locked file changed → stop
        (self.out / "secondary.csv").write_text("secondary.csv")
        with self.assertRaises(RC.GuardError):
            RC.resume_prepare(self.out, "freeze-03", git=repo_git(head="bbb", tag="ccc", status="?? results/conf2014/"))
        with self.assertRaises(RC.GuardError):
            RC.resume_prepare(self.out, "freeze-03", git=repo_git(status="?? results/conf2014/\n M src/ml/data.py"))
        (self.out / ".lock").write_text(json.dumps({"tag": "freeze-03", "commit": "zzz"}))
        with self.assertRaises(RC.GuardError):
            RC.resume_prepare(self.out, "freeze-03", git=g)                       # start record of another commit
        (self.out / ".lock").write_text(json.dumps({"tag": "freeze-03", "commit": "aaa"}))
        self.log.write_text("")
        with self.assertRaises(RC.GuardError):
            RC.resume_prepare(self.out, "freeze-03", git=g)                       # no full-read record
        with self.assertRaises(RC.GuardError):
            RC.resume_prepare(self.out.parent / "conf2014_never_started", "freeze-03", git=repo_git())  # nothing to resume


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

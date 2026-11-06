"""Failure-oriented tests; fake providers are fixtures, never real cross-review."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from workflow import Ledger, STAGES, WorkflowError, inside, clean_packet, main


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temp_root = os.environ.get("WORKFLOW_TEST_TMP")
        if temp_root:
            Path(temp_root).mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="workflow-test-", dir=temp_root)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.file("approval.md", "Test fixture approval, not a real user approval")
        self.request = dict(title="시험", goal="검증", audience="테스터", why="오판 방지", approach="임시 파일",
                            scope=["테스트"], out_of_scope=["실제 LLM"], spec_version="1", approval="approval.md",
                            criteria={"R1": "원문과 결과 대조"})
        self.ledger = Ledger(self.root, "test")
        self.ledger.init(self.request)
        self.seq = 0

    def file(self, name, content="test evidence"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return name

    def act(self, action, stage=STAGES[0], packet=None, op=None):
        self.seq += 1
        return self.ledger.act(action, stage, packet or {}, op or f"op-{self.seq}")

    def start(self, stage=STAGES[0]):
        return self.act("start", stage, dict(session=stage, provider="claude" if stage in (STAGES[1], STAGES[3]) else "gpt",
                    model="TEST-FAKE", task="fixture", fallback_reason="fixture Hermes absent"))

    def submit(self, stage=STAGES[0]):
        packet = dict(session=stage, spec_version="1", summary="fixture", self_test="fixture checks",
                      limitations=["실제 모델 호출 아님"], artifacts=[self.file(f"{stage}/output.md")])
        if stage == STAGES[2]:
            packet["scenarios"] = [dict(id=k, kind=k, criterion="R1", conditions="fixture", expected="pass",
                                        actual="pass", passed=True, evidence=[self.file(f"{stage}/{k}.log")])
                                   for k in ("normal", "expected_error")]
        return self.act("submit", stage, packet)

    def review_packet(self, stage=STAGES[0], fail=False):
        return dict(session="review-" + stage, provider="claude" if stage == STAGES[0] else "gpt", model="TEST-FAKE",
                    summary="fixture", spec_version="1", criteria=["R1"], verdict="fail" if fail else "pass",
                    defects=[dict(id="D1", reason="fixture defect", reproduce="read output")] if fail else [],
                    suggestions=[], evidence=[self.file(f"{stage}/review.log")])

    def finish(self, stage=STAGES[0]):
        self.start(stage)
        self.submit(stage)
        self.act("review", stage, self.review_packet(stage))
        return self.act("complete", stage, dict(role="master", session="master", reason="fixture verified"))

    def test_complete_cycle_and_resume_from_disk(self):
        for stage in STAGES:
            self.finish(stage)
            self.ledger = Ledger(self.root, "test")
        self.assertTrue(self.ledger.summary()["complete"])
        self.assertIsNone(self.ledger.summary()["next_stage"])

    def test_duplicate_init_is_noop_and_different_request_rejected(self):
        before = self.ledger.path.read_bytes()
        self.ledger.init(self.request)
        self.assertEqual(before, self.ledger.path.read_bytes())
        altered = {**self.request, "goal": "different"}
        with self.assertRaises(WorkflowError):
            self.ledger.init(altered)

    def test_idempotent_operation_and_collision(self):
        packet = dict(session="s", provider="gpt", model="TEST", task="fixture")
        self.act("start", packet=packet, op="same")
        before = self.ledger.path.read_bytes()
        self.act("start", packet=packet, op="same")
        self.assertEqual(before, self.ledger.path.read_bytes())
        with self.assertRaises(WorkflowError):
            self.act("start", packet={**packet, "task": "other"}, op="same")

    def test_predecessor_and_self_review_blocked(self):
        with self.assertRaises(WorkflowError):
            self.start(STAGES[1])
        self.start()
        self.submit()
        packet = self.review_packet()
        packet["session"] = STAGES[0]
        with self.assertRaises(WorkflowError):
            self.act("review", packet=packet)

    def test_wrong_provider_and_missing_criteria(self):
        self.start()
        self.submit()
        packet = self.review_packet()
        packet["provider"] = "gpt"
        with self.assertRaises(WorkflowError):
            self.act("review", packet=packet)
        packet = self.review_packet()
        packet["criteria"] = []
        with self.assertRaises(WorkflowError):
            self.act("review", packet=packet)

    def test_completion_requires_review_and_evidence(self):
        self.start()
        self.submit()
        with self.assertRaises(WorkflowError):
            self.act("complete", packet=dict(role="master", session="m", reason="done"))
        packet = self.review_packet()
        packet["evidence"] = ["missing.log"]
        with self.assertRaises(WorkflowError):
            self.act("review", packet=packet)

    def test_modified_after_review_cannot_complete(self):
        self.start()
        self.submit()
        self.act("review", packet=self.review_packet())
        self.file(f"{STAGES[0]}/output.md", "changed")
        with self.assertRaises(WorkflowError):
            self.act("complete", packet=dict(role="master", session="m", reason="done"))

    def test_completed_evidence_tamper_invalidates_report(self):
        for stage in STAGES:
            self.finish(stage)
        self.file(f"{STAGES[0]}/output.md", "changed")
        report = self.ledger.summary()
        self.assertFalse(report["complete"])
        self.assertTrue(report["integrity_problems"])

    def test_repeat_defect_escalates_and_needs_reassessment(self):
        for _ in range(3):
            self.start()
            self.submit()
            self.act("review", packet=self.review_packet(fail=True))
        state = self.ledger.load()["stages"][STAGES[0]]
        self.assertEqual(state["status"], "blocked")
        packet = dict(role="master", session="m", reason="reason")
        with self.assertRaises(WorkflowError):
            self.act("resume", packet=packet)
        self.act("reassess", packet={**packet, "resolution": "change approach"})
        self.start()

    def test_fourth_review_escalates_even_with_different_defects(self):
        for i in range(4):
            self.start()
            self.submit()
            packet = self.review_packet(fail=True)
            packet["defects"][0]["id"] = f"D{i}"
            self.act("review", packet=packet)
        self.assertEqual(self.ledger.load()["stages"][STAGES[0]]["status"], "blocked")

    def test_block_resume_preserves_attempt_and_task(self):
        self.start()
        self.act("block", packet=dict(reason="usage limit"))
        self.act("resume", packet=dict(role="master", session="m", reason="quota reset"))
        state = self.ledger.load()["stages"][STAGES[0]]
        self.assertEqual(state["status"], "running")
        self.assertEqual(state["attempt"], 1)

    def test_qa_requires_normal_error_and_all_criteria(self):
        for stage in STAGES[:2]:
            self.finish(stage)
        self.start(STAGES[2])
        with self.assertRaises(WorkflowError):
            self.act("submit", STAGES[2], dict(session=STAGES[2], spec_version="1", summary="x", self_test="x",
                    limitations=[], artifacts=[self.file("qa.txt")], scenarios=[]))

    def test_request_version_drift_and_secrets_rejected(self):
        self.file("approval.md", "changed approval")
        with self.assertRaises(WorkflowError):
            self.start()
        with self.assertRaises(WorkflowError):
            clean_packet({"api_key": "not-even-real"})

    def test_path_escape_and_empty_evidence_rejected(self):
        for path in ("../out.txt", "C:/secret.txt", "/secret.txt"):
            with self.assertRaises(WorkflowError):
                inside(self.root, path)
        with self.assertRaises(WorkflowError):
            Ledger(self.root, "../escape")
        with self.assertRaises(WorkflowError):
            self.ledger.evidence([self.file("empty.txt", "")])

    def test_lock_prevents_simultaneous_writer(self):
        with self.ledger.locked():
            with self.assertRaises(WorkflowError):
                self.start()

    def test_timeline_can_be_rebuilt_without_state_mutation(self):
        self.start()
        before = self.ledger.path.read_bytes()
        self.ledger.render(self.ledger.load())
        self.assertEqual(before, self.ledger.path.read_bytes())
        self.assertIn("raw/0002-start.json", (self.ledger.run / "timeline.md").read_text(encoding="utf-8"))

    def test_failed_qa_is_recorded_but_cannot_pass(self):
        for stage in STAGES[:2]:
            self.finish(stage)
        self.start(STAGES[2])
        packet = dict(session=STAGES[2], spec_version="1", summary="failed QA", self_test="actual failure",
            limitations=[], artifacts=[self.file("qa-failure.txt")], scenarios=[
                dict(id=k, kind=k, criterion="R1", conditions="fixture", expected="success", actual="error",
                     passed=False, evidence=["qa-failure.txt"]) for k in ("normal", "expected_error")])
        self.act("submit", STAGES[2], packet)
        self.assertFalse(self.ledger.load()["stages"][STAGES[2]]["submission"]["scenarios"][0]["passed"])
        with self.assertRaises(WorkflowError):
            self.act("review", STAGES[2], self.review_packet(STAGES[2]))
        self.act("review", STAGES[2], self.review_packet(STAGES[2], fail=True))

    def test_reopen_invalidates_downstream_and_keeps_history(self):
        for stage in STAGES:
            self.finish(stage)
        self.file(f"{STAGES[1]}/output.md", "defect fix outside ledger")
        packet = dict(role="master", session="master", reason="QA discovered defect")
        self.act("reopen", STAGES[1], packet)
        state = self.ledger.load()
        self.assertEqual(state["stages"][STAGES[0]]["status"], "complete")
        self.assertEqual(state["stages"][STAGES[1]]["status"], "revision")
        self.assertEqual(state["stages"][STAGES[2]]["status"], "waiting")
        self.assertEqual(state["stages"][STAGES[1]]["archived_rounds"][0]["history"][0]["verdict"], "pass")
        snapshot = state["stages"][STAGES[1]]["archived_rounds"][0]["submission"]["artifacts"][0]["snapshot"]
        self.assertEqual((self.root / snapshot).read_text(), "test evidence")
        for stage in STAGES[1:]:
            self.finish(stage)
        self.assertTrue(self.ledger.summary()["complete"])


    def test_qa_reviewer_cannot_be_developer(self):
        for stage in STAGES[:2]:
            self.finish(stage)
        self.start(STAGES[2])
        self.submit(STAGES[2])
        packet = self.review_packet(STAGES[2])
        packet.update(session=STAGES[1], provider="claude")
        with self.assertRaises(WorkflowError):
            self.act("review", STAGES[2], packet)

    def test_secret_evidence_is_not_copied(self):
        path = self.file("private.log", "sk-" + "x" * 32)
        before = set((self.ledger.run / "evidence").iterdir())
        with self.assertRaises(WorkflowError):
            self.ledger.evidence([path])
        self.assertEqual(before, set((self.ledger.run / "evidence").iterdir()))

    def test_revision_preserves_previous_submission_and_limitations(self):
        self.start()
        self.submit()
        self.act("review", packet=self.review_packet(fail=True))
        self.start()
        stage = self.ledger.load()["stages"][STAGES[0]]
        self.assertIn("self_test", stage["revision_rounds"][0]["submission"])
        self.assertTrue(self.ledger.summary()["previous_limitations"][STAGES[0]])

    def test_waiting_can_be_blocked_and_resumed(self):
        self.act("block", packet=dict(reason="tool_missing: Claude not installed"))
        self.act("resume", packet=dict(role="master", session="m", reason="installed"))
        self.assertEqual(self.ledger.load()["stages"][STAGES[0]]["status"], "waiting")

    def test_bad_packet_type_rejected(self):
        with self.assertRaises(WorkflowError):
            self.ledger.init([])

    def test_replayed_operation_detects_artifact_drift(self):
        self.start()
        self.submit()
        packet = self.review_packet()
        self.act("review", packet=packet, op="review-once")
        self.file(f"{STAGES[0]}/output.md", "modified")
        with self.assertRaises(WorkflowError):
            self.act("review", packet=packet, op="review-once")


if __name__ == "__main__":
    unittest.main(verbosity=2)


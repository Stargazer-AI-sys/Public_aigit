"""Offline synthetic tests; these never invoke Hermes or access credentials."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

import hermes_worker as w


def event(value):
    return (json.dumps(value) + "\n").encode()


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hermes-worker-test-", dir=w.ROOT / ".local")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.packet = {"run_id": "synthetic-run", "task_id": "ENV-01", "purpose": "record-summary", "instruction": "Summarize: sample check passed; QA remains unverified.", "sources": []}
        self.preflight = Mock(return_value={"model": w.MODEL, "billing_mode": "subscription"})
        self.result = {"type": "result", "session_id": "synthetic-session", "exit_code": 0, "text": "Sample check passed. QA remains unverified."}
        self.invoke = Mock(return_value=subprocess.CompletedProcess([], 0, event(self.result), b""))

    def run_worker(self):
        return w.execute(self.root, self.packet, preflight=self.preflight, invoke=self.invoke)

    def test_success_has_originals_hashes_and_fresh_safe_invocation(self):
        state = self.root / "docs/workflows/synthetic-run/state.json"
        state.parent.mkdir(parents=True)
        state.write_bytes(b'{"approval":"unchanged"}')
        base = self.run_worker()
        self.assertEqual(state.read_bytes(), b'{"approval":"unchanged"}')
        self.assertEqual((base / "stdout.jsonl").read_bytes(), event(self.result))
        outcome = json.loads((base / "99-outcome.json").read_text())
        self.assertEqual(outcome["status"], "returned_draft")
        self.assertEqual(outcome["result_sha256"], w.digest((base / "result.txt").read_bytes()))
        cmd = self.invoke.call_args.args[0]
        self.assertIn("--safe-mode", cmd)
        self.assertEqual(cmd[cmd.index("--toolsets") + 1], "")
        self.assertNotIn("--resume", cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], w.MODEL)
        self.assertEqual(json.loads((base / "packet.json").read_text()), self.packet)

    def test_duplicate_never_resends_even_changed_instruction(self):
        self.run_worker()
        self.packet["instruction"] = "Different content"
        with self.assertRaises(w.WorkerError):
            self.run_worker()
        self.assertEqual(self.invoke.call_count, 1)

    def test_preflight_failure_never_dispatches_and_blocks_replay(self):
        self.preflight.side_effect = RuntimeError("private diagnostic")
        with self.assertRaisesRegex(w.WorkerError, "not sent"):
            self.run_worker()
        self.invoke.assert_not_called()
        self.preflight.side_effect = None
        with self.assertRaises(w.WorkerError):
            self.run_worker()

    def test_timeout_is_uncertain_and_never_automatically_retried(self):
        self.invoke.side_effect = subprocess.TimeoutExpired("synthetic", 180)
        with self.assertRaises(w.WorkerError):
            self.run_worker()
        outcome = json.loads((self.root / "docs/workflows/synthetic-run/raw/hermes-ENV-01/99-outcome.json").read_text())
        self.assertEqual(outcome["status"], "failed_or_uncertain")
        with self.assertRaises(w.WorkerError):
            self.run_worker()
        self.assertEqual(self.invoke.call_count, 1)

    def test_path_traversal_reserved_ids_and_unapproved_sources_rejected(self):
        for value in ("../escape", "CON", "A/B", "C:foo", "..", "a.b"):
            with self.subTest(value=value), self.assertRaises(w.WorkerError):
                w.identifier(value)
        for path in (".local/auth.json", "guide_docs/AI_작업_요청과_재개_가이드.html", "docs/workflows/guide-prototype/state.json", "../skills/simple-user-guide/SKILL.md"):
            self.packet["sources"] = [{"path": path, "sha256": "0" * 64, "start_line": 1, "end_line": 1}]
            with self.subTest(path=path), self.assertRaises(w.WorkerError):
                w.prepare(self.root, self.packet)

    def test_source_hash_pins_exact_content(self):
        raw = b"Synthetic approved source. Unknown remains unknown."
        (self.root / "README.md").write_bytes(raw)
        self.packet["sources"] = [{"path": "README.md", "sha256": w.digest(raw), "start_line": 1, "end_line": 1}]
        self.assertIn(raw, w.prepare(self.root, self.packet))
        (self.root / "README.md").write_bytes(raw + b"changed")
        with self.assertRaises(w.WorkerError):
            w.prepare(self.root, self.packet)

    def test_no_implicit_project_reads(self):
        (self.root / "README.md").write_text("Do not transmit this implicit text")
        self.assertNotIn(b"Do not transmit", w.prepare(self.root, self.packet))

    def test_held_run_cannot_receive_records(self):
        self.packet["run_id"] = "guide-prototype"
        with self.assertRaises(w.WorkerError):
            self.run_worker()
        self.invoke.assert_not_called()

    def test_source_range_only_and_limit(self):
        raw = b"Excluded first\nIncluded second\n" + b"Excluded tail\n" * 201
        (self.root / "README.md").write_bytes(raw)
        source = {"path": "README.md", "sha256": w.digest(raw), "start_line": 2, "end_line": 2}
        self.packet["sources"] = [source]
        prepared = w.prepare(self.root, self.packet)
        self.assertIn(b"Included second", prepared)
        self.assertNotIn(b"Excluded", prepared)
        for start, end in ((0, 2), (3, 2), (1, 201), (1, 999), (True, 2)):
            source.update(start_line=start, end_line=end)
            with self.subTest(start=start, end=end), self.assertRaises(w.WorkerError):
                w.prepare(self.root, self.packet)

    def test_known_secret_input_rejected_before_recording(self):
        self.packet["instruction"] = "Bearer " + "syntheticcredential" * 2
        with self.assertRaises(w.WorkerError):
            self.run_worker()
        self.assertFalse((self.root / "docs").exists())

    def test_known_secret_output_omitted(self):
        self.invoke.return_value.stdout = b"Bearer syntheticcredential0000000000"
        with self.assertRaises(w.WorkerError):
            self.run_worker()
        base = self.root / "docs/workflows/synthetic-run/raw/hermes-ENV-01"
        self.assertFalse((base / "stdout.jsonl").exists())
        self.assertFalse((base / "result.txt").exists())

    def test_invalid_results_do_not_mean_success(self):
        for raw in (b"", b"not json", event(self.result) * 2, event({**self.result, "exit_code": 1}), event({**self.result, "session_id": ""}), event({**self.result, "text": ""}), event({"type": "tool_call"}) + event(self.result)):
            with self.subTest(raw=raw), self.assertRaises((w.WorkerError, ValueError)):
                w.parse_response(raw)

    def test_nonzero_exit_preserves_raw_but_is_not_success(self):
        self.invoke.return_value.returncode = 1
        with self.assertRaises(w.WorkerError):
            self.run_worker()
        base = self.root / "docs/workflows/synthetic-run/raw/hermes-ENV-01"
        self.assertTrue((base / "stdout.jsonl").exists())
        self.assertFalse((base / "result.txt").exists())


if __name__ == "__main__":
    unittest.main()

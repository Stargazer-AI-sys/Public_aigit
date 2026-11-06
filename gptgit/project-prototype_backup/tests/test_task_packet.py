import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("task_packet", Path(__file__).resolve().parents[1] / "tools/task_packet.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "spec.md").write_text("requirement\nsecond\n", encoding="utf-8")
        (self.root / "plan.md").write_text("plan\n", encoding="utf-8")
        self.packet = {"task_id": "TASK-01", "role": "developer", "goal": "Implement one requirement", "work_spec": "spec.md", "development_plan": "plan.md", "acceptance": ["expected result"], "inputs": [{"path": "spec.md", "reason": "requirement", "lines": [1, 1]}], "write_scope": ["src/new.py"], "constraints": ["No model fallback"], "expected_output": "Code and test evidence", "session": {"provider": "claude", "actual_id": None}}

    def tearDown(self):
        self.temp.cleanup()

    def errors(self, **changes):
        packet = copy.deepcopy(self.packet)
        packet.update(changes)
        return MODULE.validate(packet, self.root)

    def test_valid_and_no_output_creation(self):
        self.assertEqual([], self.errors())
        self.assertFalse((self.root / "src").exists())

    def test_escape_and_absolute_paths(self):
        for value in ("../outside.py", "C:/outside.py", "C:outside.py", "/outside.py", "src/../outside.py", "src/*.py"):
            with self.subTest(value=value):
                self.assertTrue(self.errors(write_scope=[value]))

    def test_link_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            try:
                (self.root / "link").symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic link privilege unavailable: {exc}")
            self.assertTrue(self.errors(write_scope=["link/out.py"]))

    def test_review_and_qa_readonly(self):
        for role in ("planning-reviewer", "qa"):
            session = {"provider": MODULE.PROVIDERS[role], "actual_id": None}
            self.assertTrue(self.errors(role=role, session=session))
            self.assertEqual([], self.errors(role=role, write_scope=[], session=session))

    def test_documenter_only_drafts(self):
        session = {"provider": "hermes", "actual_id": None}
        self.assertTrue(self.errors(role="documenter", session=session, write_scope=["wiki/index.md"]))
        self.assertTrue(self.errors(role="documenter", session=session, write_scope=["docs/runs/RUN-01/drafts/wiki.md"]))
        self.assertEqual([], self.errors(role="documenter", session=session, write_scope=["docs/workflows/RUN-01/drafts/wiki.md"]))

    def test_required_acceptance_and_missing_field(self):
        self.assertTrue(self.errors(acceptance=[]))
        packet = dict(self.packet)
        del packet["goal"]
        self.assertTrue(MODULE.validate(packet, self.root))

    def test_no_whole_history_or_directory(self):
        (self.root / "management_log.md").write_text("old\ncurrent\n", encoding="utf-8")
        self.assertTrue(self.errors(inputs=[{"path": "management_log.md", "reason": "history"}]))
        self.assertEqual([], self.errors(inputs=[{"path": "management_log.md", "reason": "selected evidence", "lines": [2, 2]}]))
        self.assertTrue(self.errors(inputs=[{"path": ".", "reason": "all files"}]))

    def test_line_range_and_session(self):
        self.assertTrue(self.errors(inputs=[{"path": "spec.md", "reason": "requirement", "lines": [1, 100]}]))
        self.assertTrue(self.errors(session={"provider": "claude"}))

    def test_planner_may_not_have_plan_yet(self):
        self.assertEqual([], self.errors(role="planner", session={"provider": "codex", "actual_id": None}, development_plan=None, write_scope=["plan.md"]))
        self.assertTrue(self.errors(development_plan=None))

    def test_provider_mapping(self):
        for role, provider in MODULE.PROVIDERS.items():
            with self.subTest(role=role):
                self.assertEqual([], self.errors(role=role, session={"provider": provider, "actual_id": None}, write_scope=[]))
                self.assertTrue(self.errors(role=role, session={"provider": "wrong", "actual_id": None}, write_scope=[]))

    def test_qa_test_outputs(self):
        changes = {"role": "qa", "session": {"provider": "codex", "actual_id": None}, "write_scope": []}
        self.assertEqual([], self.errors(**changes, test_write_scope=[".local/qa/TASK-01/output.txt"]))
        for path in (".local/qa/OTHER/output.txt", "src/result.txt", "../out.txt", ".local/qa/TASK-01"):
            with self.subTest(path=path):
                self.assertTrue(self.errors(**changes, test_write_scope=[path]))
        self.assertTrue(self.errors(test_write_scope=[".local/qa/TASK-01/output.txt"]))
        self.assertTrue(self.errors(**changes, test_write_scope=".local/qa/TASK-01/output.txt"))

    def test_qa_cannot_overwrite_test_input(self):
        source = self.root / ".local/qa/TASK-01/input.txt"
        source.parent.mkdir(parents=True)
        source.write_text("fixture", encoding="utf-8")
        self.assertTrue(self.errors(role="qa", session={"provider": "codex", "actual_id": None}, write_scope=[], inputs=[{"path": ".local/qa/TASK-01/input.txt", "reason": "fixture"}], test_write_scope=[".local/qa/TASK-01/input.txt"]))

    def test_template_is_not_dispatchable(self):
        self.assertTrue(self.errors(template_only=True))

    def test_history_cannot_be_disguised_as_spec(self):
        (self.root / "management_log.md").write_text("history\n", encoding="utf-8")
        self.assertTrue(self.errors(work_spec="management_log.md"))


if __name__ == "__main__":
    unittest.main()

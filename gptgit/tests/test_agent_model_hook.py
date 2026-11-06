import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

HOOK = Path(__file__).resolve().parent.parent / "tools" / "agent_model_hook.py"
sys.path.insert(0, str(HOOK.parent))
spec = importlib.util.spec_from_file_location("agent_model_hook", HOOK)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def event(command, cwd=None, tool="exec_command", key="cmd"):
    return {"hook_event_name": "PreToolUse", "cwd": str(cwd or hook.ROOT),
            "tool_name": tool, "tool_input": {key: command}}


class GuardTests(unittest.TestCase):
    def test_direct_codex_denied_even_with_master_model(self):
        for command in ("codex", "codex --model gpt-6-astra", "codex exec hello", r"C:\bin\codex.cmd -m gpt-6-luna"):
            with self.subTest(command=command):
                self.assertIsNotNone(hook.evaluate(event(command)))

    def test_read_only_and_launcher(self):
        for command in ("codex --help", "codex features", "codex features list", "codex login status", "python tools/start_agent.py --model gpt-6-astra"):
            with self.subTest(command=command):
                self.assertIsNone(hook.evaluate(event(command)))

    def test_herdr_requires_exactly_one_allowed_model(self):
        prefix = "herdr agent start worker1 --kind codex --pane p1 -- "
        denied = ("", "--model gpt-6-astra", "--model", "--model gpt-6-luna --model gpt-6-astra",
                  "-m gpt-6-luna", "--model=gpt-6-luna", "--model gpt-6-luna -m gpt-6-astra",
                  "--model gpt-6-luna --model=gpt-6-astra", "--model gpt-6-luna -c model=gpt-6-astra",
                  "--model gpt-6-luna --config=model=gpt-6-astra", "--model gpt-6-luna -c")
        for args in denied:
            with self.subTest(args=args):
                self.assertIsNotNone(hook.evaluate(event(prefix + args)))
        for model in ("gpt-6-luna", "gpt-6.1-terra"):
            self.assertIsNone(hook.evaluate(event(prefix + "--model " + model)))
        self.assertIsNone(hook.evaluate(event(prefix + '--model gpt-6-luna -c forced_login_method="chatgpt"')))
        self.assertIsNone(hook.evaluate(event("herdr agent start worker --kind claude --pane p")))
        self.assertIsNotNone(hook.evaluate(event("herdr agent start worker --kind=codex --pane p -- --model gpt-6-astra")))

    def test_shared_policy_is_authoritative(self):
        command = "herdr agent start worker --kind codex --pane p -- --model example"
        with mock.patch.object(hook, "validate", return_value=[]) as validator:
            self.assertIsNone(hook.evaluate(event(command)))
            validator.assert_called_once_with("worker", "codex", "example")
        with mock.patch.object(hook, "validate", return_value=["denied"]):
            self.assertIsNotNone(hook.evaluate(event(command)))

    def test_shell_and_mcp(self):
        for command in ("echo safe; codex exec test", "bash -c 'codex exec test'", ["codex", "exec", "test"]):
            self.assertIsNotNone(hook.evaluate(event(command, tool="mcp__server__exec_command", key="command")))
        self.assertIsNone(hook.evaluate(event("echo codex", tool="shell")))

    def test_scope_and_unrecognized_events(self):
        for cwd in (hook.ROOT / "other-project", hook.ROOT.parent, hook.ROOT / "project-prototype-extra"):
            self.assertIsNone(hook.evaluate(event("codex", cwd=cwd)))
        self.assertIsNotNone(hook.evaluate(event("codex", cwd=hook.ROOT / "project-prototype")))
        self.assertIsNotNone(hook.evaluate(event("codex", cwd=hook.ROOT / "project-management")))
        self.assertIsNone(hook.evaluate({**event("codex"), "hook_event_name": "PreModelRequest"}))
        self.assertIsNone(hook.evaluate(event("codex", tool="other")))
        self.assertIsNone(hook.evaluate({**event("codex"), "cwd": None}))

    def test_deny_json_and_failure_open(self):
        for payload, expected in ((json.dumps(event("codex")), True), ("{invalid", False)):
            proc = subprocess.run([sys.executable, "-B", str(HOOK)], input=payload, text=True, capture_output=True, check=False)
            self.assertEqual(proc.returncode, 0)
            if expected:
                self.assertEqual(json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
            else:
                self.assertEqual(proc.stdout, "")
                self.assertIn("agent_model_hook", proc.stderr)

    def test_unparseable_command_fails_open(self):
        with mock.patch.object(hook.sys, "stdin", io.StringIO(json.dumps(event("codex '")))), mock.patch.object(hook.sys, "stdout", new_callable=io.StringIO), mock.patch.object(hook.sys, "stderr", new_callable=io.StringIO):
            self.assertEqual(hook.main(), 0)
            self.assertEqual(hook.sys.stdout.getvalue(), "")
            self.assertIn("agent_model_hook", hook.sys.stderr.getvalue())


if __name__ == "__main__":
    unittest.main()


"""CheckOnly and failure boundaries; never starts an agent or contacts Herdr."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]

class StartRoleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='start-role-')
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root = base / 'project'
        (self.root / 'tools').mkdir(parents=True)
        (self.root / 'config').mkdir()
        (base / 'tools').mkdir()
        for name in ('start_role.ps1', 'task_packet.py'):
            shutil.copyfile(SOURCE / 'tools' / name, self.root / 'tools' / name)
        shutil.copyfile(SOURCE.parent / 'tools/check_agent_model.py', base / 'tools/check_agent_model.py')
        (self.root / 'config/runtime.example.json').write_text(json.dumps({'python':sys.executable, 'codex':'cmd.exe', 'claude':'cmd.exe'}), encoding='utf-8')
        (self.root / 'CLAUDE.md').write_text('fixture instructions', encoding='utf-8')
        (self.root / 'spec.md').write_text('fixture spec', encoding='utf-8')
        (self.root / 'plan.md').write_text('fixture plan', encoding='utf-8')
        self.packet = {'task_id':'TEST-1', 'role':'qa', 'goal':'SECRET TASK CONTENT', 'work_spec':'spec.md', 'development_plan':'plan.md', 'acceptance':['ok'], 'inputs':[{'path':'spec.md','reason':'fixture'}], 'write_scope':[], 'constraints':['fixture'], 'expected_output':'fixture', 'session':{'provider':'codex','model':'gpt-6.1-terra','actual_id':None}}
        self.packet_path = self.root / 'packet.json'
        self.env = os.environ.copy()
        for key in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL','OPENAI_API_BASE','ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_USE_FOUNDRY'):
            self.env.pop(key, None)
        self.ps = shutil.which('pwsh') or shutil.which('powershell')
        if not self.ps: self.skipTest('PowerShell unavailable')

    def run_check(self, *args, env=None):
        self.packet_path.write_text(json.dumps(self.packet), encoding='utf-8')
        return subprocess.run([self.ps, '-NoProfile', '-File', str(self.root/'tools/start_role.ps1'), *args, '-CheckOnly'], cwd=self.root, env=env or self.env, text=True, encoding='utf-8', capture_output=True)

    def test_qa_packet_model_and_no_task_sent(self):
        r = self.run_check('-Role','qa','-Packet',str(self.packet_path))
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(r.stdout)
        self.assertEqual(result['model'], 'gpt-6.1-terra')
        self.assertFalse(result['model_called'])
        self.assertFalse(result['authentication_checked'])
        self.assertIn('read-only', result['arguments'])
        self.assertIn('auto_review', ' '.join(result['arguments']))
        self.assertNotIn('SECRET TASK CONTENT', r.stdout)

    def test_master_requires_astra(self):
        self.assertNotEqual(self.run_check('-Role','master').returncode, 0)
        self.assertNotEqual(self.run_check('-Role','master','-Model','gpt-6-luna').returncode, 0)
        r = self.run_check('-Role','master','-Model','gpt-6-astra')
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_missing_disallowed_and_conflicting_model_fail(self):
        self.packet['session'].pop('model')
        self.assertNotEqual(self.run_check('-Role','qa','-Packet',str(self.packet_path)).returncode, 0)
        self.packet['session']['model'] = 'gpt-6-astra'
        self.assertNotEqual(self.run_check('-Role','qa','-Packet',str(self.packet_path)).returncode, 0)
        self.packet['session']['model'] = 'gpt-6-luna'
        self.assertNotEqual(self.run_check('-Role','qa','-Packet',str(self.packet_path),'-Model','gpt-6.1-terra').returncode, 0)

    def test_claude_reviewer_read_only_and_model(self):
        self.packet['role'] = 'planning-reviewer'
        self.packet['session'] = {'provider':'claude','model':'claude-sonnet-4-6','actual_id':None}
        r = self.run_check('-Role','planning-reviewer','-Packet',str(self.packet_path))
        self.assertEqual(r.returncode, 0, r.stderr)
        result=json.loads(r.stdout)
        self.assertIn('Read,Grep,Glob', result['arguments'])
        self.assertIn('claude-sonnet-4-6', result['arguments'])
        self.assertNotIn('SECRET TASK CONTENT', r.stdout)
        self.packet['session']['model'] = 'gpt-6-astra'
        self.assertNotEqual(self.run_check('-Role','planning-reviewer','-Packet',str(self.packet_path)).returncode, 0)

    def test_subscription_environment_blocked(self):
        env=self.env.copy();env['OPENAI_API_KEY']='fixture-not-a-real-key'
        self.assertNotEqual(self.run_check('-Role','qa','-Packet',str(self.packet_path),env=env).returncode, 0)

    def run_auth_fixture(self, status_exit, status_text):
        fake = self.root / 'fake-codex.cmd'
        marker = self.root / 'started.txt'
        fake.write_text('@echo off\r\nif "%1 %2"=="login status" (\r\n  echo ' + status_text + ' 1>&2\r\n  exit /b ' + str(status_exit) + '\r\n)\r\necho started > "' + str(marker) + '"\r\nexit /b 0\r\n', encoding='ascii')
        (self.root / 'config/runtime.example.json').write_text(json.dumps({'python':sys.executable, 'codex':str(fake), 'claude':'cmd.exe'}), encoding='utf-8')
        env=self.env.copy(); env['HERDR_ENV']='1'
        result=subprocess.run([self.ps, '-NoProfile', '-File', str(self.root/'tools/start_role.ps1'), '-Role','master','-Model','gpt-6-astra'], cwd=self.root, env=env, text=True, encoding='utf-8', capture_output=True)
        return result, marker.exists()

    def test_auth_success_on_stderr_starts_session(self):
        result, started=self.run_auth_fixture(0, 'Logged in using ChatGPT')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(started)

    def test_auth_failure_blocks_session(self):
        for code, message in ((1, 'Logged in using ChatGPT'), (0, 'Not authenticated')):
            with self.subTest(code=code, message=message):
                result, started=self.run_auth_fixture(code, message)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(started)

    def test_checker_unavailable_fails_closed(self):
        (self.root.parent/'tools/check_agent_model.py').unlink()
        self.assertNotEqual(self.run_check('-Role','master','-Model','gpt-6-astra').returncode, 0)

if __name__ == '__main__': unittest.main()

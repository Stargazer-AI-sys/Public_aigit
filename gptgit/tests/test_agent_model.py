import sys
from pathlib import Path
import unittest
import json
import subprocess
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_agent_model import validate
from start_managed_agent import launch
import start_managed_agent as launcher


class PolicyTests(unittest.TestCase):
    def test_allowed_roles(self):
        self.assertEqual(validate('master','codex','gpt-6-astra'), [])
        for model in ('gpt-6-luna','gpt-6.1-terra'):
            self.assertEqual(validate('qa','codex',model), [])
    def test_forbidden_and_missing(self):
        for model in ('gpt-6-astra','',None,'gpt-6-astra-latest','unknown'):
            self.assertTrue(validate('writer','codex',model))
        self.assertTrue(validate('master','codex','gpt-6-luna'))
    def test_external_contract(self):
        self.assertEqual(validate('developer','claude','sonnet'), [])
        self.assertTrue(validate('qa','claude','gpt-6-astra'))
    def test_check_only_and_read_only(self):
        with patch('subprocess.run') as run:
            result=launch('qa','gpt-6.1-terra','review-test',True)
            run.assert_not_called()
        self.assertIn('read-only',result['native_args'])
        self.assertNotIn('--approve-for-me',result['native_args'])
        self.assertFalse(result['task_sent'])
    def test_invalid_launch_has_no_side_effect(self):
        with patch('subprocess.run') as run:
            with self.assertRaises(ValueError): launch('writer','gpt-6-astra','test')
            run.assert_not_called()

    def test_launch_creates_separate_tab_without_prompt(self):
        calls=[]
        extra_tab=[]
        def fake(args, **kwargs):
            calls.append(args)
            if args[1:] == ['login','status']:
                return subprocess.CompletedProcess(args,0,'','Logged in using ChatGPT')
            if args[1:3] == ['pane','current']:
                result={'pane':{'cwd':str(launcher.PROJECT),'workspace_id':'w1','tab_id':'w1:t1'}}
            elif args[1:3] == ['tab','list']:
                result={'tabs':[{'tab_id':'w1:t1'}] + extra_tab}
            elif args[1:3] == ['tab','create']:
                result={'tab':{'tab_id':'w1:t2'},'root_pane':{'pane_id':'w1:p2','cwd':str(launcher.PROJECT)}}
            else:
                result={'agent':{'pane_id':'w1:p2','agent_status':'idle'}}
            return subprocess.CompletedProcess(args,0,json.dumps({'result':result}),'')
        with patch.dict(launcher.os.environ,{'HERDR_ENV':'1','HERDR_PANE_ID':'w1:p1'},clear=True), patch.object(launcher.shutil,'which',side_effect=lambda name:name), patch.object(launcher.subprocess,'run',side_effect=fake):
            result=launch('qa','gpt-6.1-terra','qa-check')
        self.assertEqual(result['tab_id'],'w1:t2')
        self.assertEqual(result['status'],'awaiting_model_verification')
        self.assertFalse(result['task_sent'])
        self.assertFalse(any('split' in args or 'prompt' in args for args in calls))
        self.assertIn('--no-focus',calls[3])
        calls.clear()
        extra_tab.append({'tab_id':'w1:t2'})
        with patch.dict(launcher.os.environ,{'HERDR_ENV':'1','HERDR_PANE_ID':'w1:p1'},clear=True), patch.object(launcher.shutil,'which',side_effect=lambda name:name), patch.object(launcher.subprocess,'run',side_effect=fake):
            with self.assertRaises(RuntimeError): launch('qa','gpt-6.1-terra','qa-check')
        self.assertFalse(any(args[1:3] == ['agent','start'] for args in calls))

    def test_auth_failure_never_creates_tab(self):
        with patch.dict(launcher.os.environ,{'HERDR_ENV':'1','HERDR_PANE_ID':'w1:p1'},clear=True), patch.object(launcher.shutil,'which',side_effect=lambda name:name), patch.object(launcher.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','not logged in')) as run:
            with self.assertRaises(ValueError): launch('qa','gpt-6.1-terra','qa-check')
            self.assertEqual(run.call_count,1)


if __name__=='__main__': unittest.main()

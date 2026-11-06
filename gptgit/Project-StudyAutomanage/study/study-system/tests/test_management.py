"""Offline manager integration: no real API, credentials or Notion writes."""
import io
import json
import re
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from analyzer.core import AnalysisError
from analyzer.management import Manager, page
from analyzer.notion_intake import prepare_sources
from analyzer.notion_prepared import load, validate
from analyzer.review_server import make_server
from test_notion_intake import IntakeTests
import test_notion_prepared as fixtures


class FakeKeys:
    def __init__(self):
        self.key = None

    def read(self):
        return self.key

    def save(self, key):
        self.key = key

    def delete(self):
        self.key = None


class ManagerTests(unittest.TestCase):
    setUp = IntakeTests.setUp
    send = fixtures.PreparedTests.send
    add = IntakeTests.add

    def manager(self):
        return Manager(self.store.root, self.source, self.root, self.target_file,
                       self.home_file, keys=FakeKeys())

    def finish(self, manager):
        manager.worker.join(20)
        self.assertFalse(manager.worker.is_alive())
        return manager.state

    def test_partial_new_failure_does_not_block_valid_approved_publication(self):
        (self.source/'failed.txt').write_text('invalid result', encoding='utf-8')
        before = self.store.path.read_bytes()
        result = prepare_sources(self.store.root, self.target_file, self.home_file,
                                 self.root, self.root/'prepared', self.source, allow_partial=True)
        self.assertTrue(result['ready'])
        self.assertFalse(result['all_sources_ready'])
        self.assertEqual(result['materials'], 1)
        self.assertEqual(result['skipped'][0]['filename'], 'failed.txt')
        validate(load(result['package']))
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_partial_does_not_silently_publish_stale_changed_approval(self):
        next(self.source.iterdir()).write_text('changed text', encoding='utf-8')
        with self.assertRaises(AnalysisError) as error:
            prepare_sources(self.store.root, self.target_file, self.home_file,
                            self.root, self.root/'prepared', self.source, allow_partial=True)
        self.assertEqual(error.exception.code, 'PARTIAL_SOURCE_CONFLICT')

    def test_unsupported_file_is_advisory_but_covered_by_manifest(self):
        (self.source/'참고.pdf').write_bytes(b'not supported')
        result = prepare_sources(self.store.root, self.target_file, self.home_file,
                                 self.root, self.root/'prepared', self.source, allow_partial=True)
        self.assertEqual(result['skipped'][0]['status'], 'unsupported')
        package = load(result['package'])
        validate(package)
        (self.source/'참고.pdf').write_bytes(b'changed')
        with self.assertRaises(Exception) as error:
            validate(package)
        self.assertEqual(error.exception.code, 'PUBLISH_SOURCE_CHANGED')

    def test_explicit_api_scope_and_key_required(self):
        manager = self.manager()
        for request in ({}, {'filenames': ['new.txt'], 'max_new_calls': 1},
                        {'filenames': ['new.txt'], 'max_new_calls': 1, 'allow_api': True}):
            with self.assertRaises(ValueError):
                manager.start('analyze', request)
            self.assertFalse(manager.mutex.locked())

    def test_missing_original_retains_existing_approval_with_explicit_notice(self):
        next(self.source.iterdir()).unlink()
        result = prepare_sources(self.store.root, self.target_file, self.home_file,
                                 self.root, self.root/'prepared', self.source, allow_partial=True)
        self.assertEqual(result['materials'], 1)
        self.assertEqual(result['skipped'], [])
        self.assertEqual(result['retained'][0]['status'], 'missing')
        validate(load(result['package']))

    def test_limit_persists_and_invalid_limit_does_not_replace_it(self):
        manager = self.manager()
        manager.post('/api/manage/settings', {'max_new_calls': 2}, None)
        with self.assertRaises(ValueError):
            manager.post('/api/manage/settings', {'max_new_calls': True}, None)
        self.assertEqual(self.manager().settings['max_new_calls'], 2)

    def test_partial_analysis_preserves_diagnostics_without_saving_key(self):
        manager = self.manager()
        manager.keys.save('dummy-secret-123456')
        report = {'analysis': {'failed': 1, 'blocked': 0, 'items': [
            {'filename': 'bad.txt', 'error': {'code': 'JSON_PARSE_ERROR', 'message': 'invalid JSON'}}]},
            'analysis_not_run': []}
        with patch('analyzer.management.analyze', return_value=report) as analyze:
            manager.start('analyze', {'filenames': ['bad.txt'], 'max_new_calls': 1, 'allow_api': True})
            state = self.finish(manager)
        self.assertEqual(state['status'], 'partial')
        self.assertEqual(analyze.call_args.kwargs['api_key'], 'dummy-secret-123456')
        self.assertNotIn('dummy-secret', (manager.ui/'state.json').read_text())
        restored = self.manager()
        self.assertIsNotNone(restored.status()['last_analysis'])

    def test_single_worker_and_shutdown_protection(self):
        manager = self.manager()
        entered, release = threading.Event(), threading.Event()
        def slow(*args, **kwargs):
            entered.set(); release.wait(10)
            return {'package': None}
        with patch('analyzer.management.prepare_sources', side_effect=slow):
            manager.start('prepare', {})
            self.assertTrue(entered.wait(5))
            try:
                with self.assertRaises(AnalysisError):
                    manager.start('prepare', {})
                with self.assertRaises(ValueError):
                    manager.post('/api/manage/shutdown', {}, SimpleNamespace())
            finally:
                release.set()
            self.finish(manager)

    def test_prepare_preview_send_to_mock_preserves_approvals(self):
        manager = self.manager()
        before = self.store.path.read_bytes()
        manager.start('prepare', {})
        self.assertEqual(self.finish(manager)['status'], 'complete')
        self.assertIn('Notion'.encode(), manager.get('/api/manage/preview'))
        with self.assertRaises(ValueError):
            manager.start('send', {})
        from analyzer.notion_prepared import publish
        def offline(package, **kwargs):
            return publish(package, call=lambda *a: fixtures.PreparedTests.call(self, *a),
                           call_many=lambda rs: [fixtures.PreparedTests.call(self, r['tool'], r['args']) for r in rs])
        with patch('analyzer.management.publish', side_effect=offline):
            manager.start('send', {'confirmed': True})
            state = self.finish(manager)
        self.assertEqual(state['status'], 'complete', state)
        self.assertIn('run_dispatch.js', state['relay'])
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_stale_preview_blocks_before_any_send(self):
        manager = self.manager()
        manager.start('prepare', {}); self.finish(manager)
        self.add()
        with self.assertRaises(Exception) as error:
            manager.start('send', {'confirmed': True})
        self.assertEqual(error.exception.code, 'PUBLISH_SOURCE_CHANGED')
        self.assertFalse(manager.mutex.locked())

    def test_interrupted_state_never_auto_resumes(self):
        manager = self.manager()
        manager.save_json('state.json', {'status': 'running', 'operation': 'send'})
        manager = self.manager()
        self.assertEqual(manager.state['status'], 'interrupted')
        self.assertIsNone(manager.worker)

    def test_key_endpoint_requires_origin_and_token_and_never_echoes_key(self):
        manager = self.manager()
        with patch('analyzer.review_server.ThreadingHTTPServer') as factory:
            make_server(self.store, 0, manager=manager)
        Handler = factory.call_args.args[1]
        handler = object.__new__(Handler)
        handler.server = SimpleNamespace(server_port=8765)
        handler.headers = {'Host': '127.0.0.1:8765'}
        handler.path = '/'
        replies = []
        handler.reply = lambda status, body, *args: replies.append((status, body))
        handler.do_GET()
        html = replies[-1][1].decode()
        self.assertIn('manageAnalyze', html)
        self.assertNotIn('__TOKEN__', html)
        token = re.search(r"const token='([^']+)'", html)[1]
        body = json.dumps({'key': 'dummy-secret-123456'}).encode()
        handler.path = '/api/manage/key'
        handler.headers['Content-Length'] = str(len(body))
        handler.rfile = io.BytesIO(body)
        handler.do_POST()
        self.assertEqual(replies[-1][0], 403)
        self.assertIsNone(manager.keys.read())
        handler.headers.update({'Origin': 'http://127.0.0.1:8765', 'X-Review-Token': token})
        handler.rfile = io.BytesIO(body)
        handler.do_POST()
        self.assertEqual(replies[-1][0], 200)
        self.assertNotIn('dummy-secret', json.dumps(replies[-1]))
        handler.path = '/api/manage/status'; handler.do_GET()
        self.assertNotIn('dummy-secret', json.dumps(replies[-1]))
        manager.post('/api/manage/delete-key', {}, handler.server)
        self.assertIsNone(manager.keys.read())


if __name__ == '__main__':
    unittest.main()

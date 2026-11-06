import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.core import AnalysisError
from analyzer.notion_intake import inspect, analyze, prepare_sources
from analyzer.notion_prepared import validate, load, publish
from analyzer.notion_sync import DeliveryError
from analyzer.review_server import make_server
import test_notion_prepared as prepared_fixtures
from test_organizer import material


class IntakeTests(unittest.TestCase):
    send = prepared_fixtures.PreparedTests.send

    def setUp(self):
        prepared_fixtures.PreparedTests.setUp(self)
        self.source = self.root/'source'
        self.source.mkdir()
        data, _ = material()
        (self.source/data['filename']).write_bytes(data['extracted_text'].encode('utf-8'))

    def prepare(self):
        return prepare_sources(self.store.root, self.target_file, self.home_file,
                               self.root, self.root/'prepared', self.source)

    def add(self, filename='new.txt'):
        data, analysis = material(filename, 'new material source')
        (self.source/filename).write_bytes(data['extracted_text'].encode('utf-8'))
        response = self.root/'response.json'
        response.write_text(json.dumps(analysis, ensure_ascii=False), encoding='utf-8')
        mapping = self.root/'responses.json'
        mapping.write_text(json.dumps({filename: str(response)}), encoding='utf-8')
        return mapping

    def test_new_source_blocks_package_without_api_or_touching_approvals(self):
        self.add()
        before = self.store.path.read_bytes()
        with patch('analyzer.openai_provider.OpenAIProvider.generate', side_effect=AssertionError('paid call')):
            report = self.prepare()
        self.assertFalse(report['ready'])
        self.assertIsNone(report['package'])
        self.assertEqual(report['counts'], {'new': 1, 'approved': 1})
        self.assertEqual(report['new_api_attempts'], 0)
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertFalse(list((self.root/'prepared').glob('*/package.json')))

    def test_new_file_extraction_analysis_review_approval_then_package(self):
        import io
        from types import SimpleNamespace
        responses = self.add('추가 [IPv4].txt')
        old = copy.deepcopy(self.store.approved()['materials'][0])
        report = analyze(self.source, self.store.root, self.root, responses=responses,
                         filenames=['추가 [IPv4].txt'])
        self.assertEqual(report['analysis']['new_successes'], 1)
        self.assertEqual(report['new_api_attempts'], 0)
        self.assertEqual(report['counts']['pending'], 1)
        self.assertIsNone(self.prepare()['package'])
        r = next(r for r in self.store.list() if r['analysis']['source']['filename'] == '추가 [IPv4].txt')
        # Exercise the existing review HTTP endpoint, including its origin/token
        # protection, rather than auto-approving from the intake implementation.
        with patch('analyzer.review_server.ThreadingHTTPServer') as factory:
            make_server(self.store, 0)
        Handler = factory.call_args.args[1]
        handler = object.__new__(Handler)
        handler.server = SimpleNamespace(server_port=8765)
        handler.headers = {'Host': '127.0.0.1:8765'}
        handler.path = '/'
        replies = []
        handler.reply = lambda status, body, *args: replies.append((status, body))
        handler.do_GET()
        import re
        token = re.search(r"const token='([^']+)'", replies[-1][1].decode('utf-8'))[1]
        body = json.dumps({'id': r['id'], 'snapshot': r['snapshot'], 'action': 'approve'}).encode()
        handler.path = '/api/decide'
        handler.headers.update({'Origin': 'http://127.0.0.1:8765', 'X-Review-Token': token,
                                'Content-Length': str(len(body))})
        handler.rfile = io.BytesIO(body)
        handler.do_POST()
        self.assertEqual(replies[-1][0], 200, replies[-1])
        result = self.prepare()
        self.assertTrue(result['ready'])
        self.assertEqual(result['materials'], 2)
        package = load(result['package'])
        validate(package)
        self.assertIn(r['id'], package['plan']['approvals'])
        self.assertEqual(self.store.get(old['id'])['snapshot'], old['snapshot'])

    def test_original_changed_or_file_added_after_preparation_blocks_before_network(self):
        result = self.prepare()
        self.add()
        calls = []
        with self.assertRaises(DeliveryError) as error:
            publish(result['package'], call=lambda *a: calls.append(a), call_many=lambda a: calls.append(a))
        self.assertEqual(error.exception.code, 'PUBLISH_SOURCE_CHANGED')
        self.assertFalse(calls)

    def test_matching_saved_analysis_is_reused_and_still_requires_approval(self):
        from analyzer.cache import context_for, digest, store_cache
        from analyzer.openai_provider import OpenAIProvider
        from analyzer.core import load_schema, from_collector
        from analyzer.schemas import DEFAULT_SCHEMA
        responses = self.add()
        _, rows = inspect(self.source, self.store.root)
        data = from_collector(next(row for row in rows if row['filename'] == 'new.txt'))
        analysis = json.loads((self.root/'response.json').read_text(encoding='utf-8'))
        schema = load_schema(DEFAULT_SCHEMA)
        context, _ = context_for(data, OpenAIProvider(schema), schema)
        cache = self.store.root/'cache'; cache.mkdir(exist_ok=True)
        store_cache(cache/(digest(context)+'.json'), context, analysis, {'kind': 'test saved response'})
        with patch('analyzer.openai_provider.OpenAIProvider.generate', side_effect=AssertionError('paid call')):
            result = self.prepare()
        self.assertEqual(result['counts'], {'pending': 1, 'approved': 1})
        self.assertIsNone(result['package'])
        self.assertEqual(result['new_api_attempts'], 0)

    def test_modify_and_delete_original_after_package_are_blocked(self):
        package = load(self.prepare()['package'])
        path = next(self.source.iterdir())
        original = path.read_bytes()
        path.write_bytes(original+b'\nchanged')
        with self.assertRaises(DeliveryError) as error:
            validate(package)
        self.assertEqual(error.exception.code, 'PUBLISH_SOURCE_CHANGED')
        path.unlink()
        with self.assertRaises(DeliveryError):
            validate(package)

    def test_changed_approved_source_waits_for_new_analysis_and_approval(self):
        path = next(self.source.iterdir())
        path.write_text(path.read_text(encoding='utf-8')+'\nchanged', encoding='utf-8')
        report, _ = inspect(self.source, self.store.root)
        self.assertEqual(report['counts'], {'changed': 1})
        self.assertFalse(report['ready'])

    def test_deleted_or_unsupported_file_and_duplicate_names_are_visible(self):
        path = next(self.source.iterdir())
        path.unlink()
        (self.source/'notes.pdf').write_bytes(b'unsupported')
        report, _ = inspect(self.source, self.store.root)
        self.assertEqual(report['counts']['missing'], 1)
        self.assertEqual(report['counts']['unsupported'], 1)
        (self.source/'a').mkdir(); (self.source/'b').mkdir()
        for folder in ('a', 'b'):
            (self.source/folder/'duplicate.txt').write_text('test', encoding='utf-8')
        report, _ = inspect(self.source, self.store.root)
        self.assertEqual(report['counts']['error'], 2)
        self.assertFalse(report['ready'])

    def test_paid_scope_is_explicit_and_approved_files_not_selected(self):
        self.add()
        with self.assertRaises(AnalysisError):
            analyze(self.source, self.store.root, self.root, allow_api=True)
        fake = {'new_api_attempts': 1, 'status': 'PASS', 'items': [], 'report_path': 'local-test'}
        with patch('analyzer.batch.run_batch', return_value=fake) as batch:
            analyze(self.source, self.store.root, self.root, allow_api=True, max_new_calls=1,
                    filenames=['new.txt'])
        from analyzer.main import read_rows
        rows = read_rows(batch.call_args.args[0])
        self.assertEqual([r['filename'] for r in rows], ['new.txt'])
        self.assertTrue(batch.call_args.kwargs['allow_api'])
        self.assertEqual(batch.call_args.kwargs['max_new_calls'], 1)

    def test_review_launcher_prepares_package_after_user_approval(self):
        import io
        from contextlib import redirect_stdout
        from types import SimpleNamespace
        from analyzer.notion_cli import execute
        responses = self.add()
        analyze(self.source, self.store.root, self.root, responses=responses)
        def user_review(store, port):
            r = next(r for r in store.list() if r['status'] == 'pending')
            store.decide(r['id'], r['snapshot'], 'approve')
        args = SimpleNamespace(notion_action='review', source_dir=self.source,
            workspace=self.store.root, target=self.target_file, home=self.home_file,
            publication_dir=self.root, output_dir=self.root/'prepared', port=8765)
        with patch('analyzer.review_server.serve', side_effect=user_review) as review, redirect_stdout(io.StringIO()):
            code = execute(args)
        self.assertEqual(code, 0)
        review.assert_called_once()
        packages = list((self.root/'prepared').glob('*/package.json'))
        self.assertEqual(len(packages), 1)
        validate(load(packages[0]))

    def test_interrupt_during_preparation_prints_resume_message_without_traceback(self):
        import io
        from contextlib import redirect_stdout
        from analyzer.main import main
        output = io.StringIO()
        with patch('sys.argv', ['study', 'notion', 'prepare']), \
             patch('analyzer.notion_cli.execute', side_effect=KeyboardInterrupt), \
             redirect_stdout(output):
            code = main()
        self.assertEqual(code, 130)
        self.assertIn('저장된 승인은 유지', output.getvalue())
        self.assertNotIn('Traceback', output.getvalue())


if __name__ == '__main__':
    unittest.main()

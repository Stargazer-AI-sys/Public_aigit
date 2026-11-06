import copy
import json
import re
import tempfile
import threading
import time
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from pathlib import Path
from uuid import uuid4

from analyzer.core import AnalysisError
from analyzer.notion_mcp import NotionMCP, check_scope, inline_text, inline_value, rpc, rpc_many
from analyzer.notion_sync import DeliveryError, MAPPING, deliver_plan, make_plan
from analyzer.workspace import Workspace
from test_organizer import material


def binding():
    collections = {}
    for kind, spec in MAPPING['collections'].items():
        collections[kind] = {'data_source_id': str(uuid4()), 'id': str(uuid4()), 'view_url': 'view://'+str(uuid4()),
            'property_mapping': {k: k for k in spec['properties']}, 'relation_mapping': {k: k for k in spec['relations']},
            'observed_properties': dict(spec['properties'], managed_digest='rich_text', operation_id='rich_text'),
            'system_properties': {'digest': 'managed_digest', 'operation': 'operation_id'}}
    for kind, spec in MAPPING['collections'].items():
        collections[kind]['observed_relations'] = {k: collections[v]['data_source_id'] for k, v in spec['relations'].items()}
    return {'format_version': 1, 'live_write_enabled': False, 'parent_page': {'id': str(uuid4()), 'name': 'parent'},
            'material_database': collections['material'], 'collections': collections}


class FakePlugin:
    def __init__(self, target):
        self.target, self.pages, self.writes, self.calls = target, {}, 0, []

    def __call__(self, tool, args):
        self.calls.append(tool)
        if tool == 'query_data_sources':
            source = next(b['data_source_id'] for b in self.target['collections'].values() if b['view_url'] == args['data']['view_url'])
            return {'results': [{'id': pid, 'url': pid} for pid, p in self.pages.items() if p['source'] == source], 'has_more': False}
        if tool == 'fetch':
            pid = args['id'].replace('-', '')
            p = self.pages[pid]
            encoded = {k: inline_text(v) if isinstance(v, str) else v for k, v in p['properties'].items()}
            text = '<properties>\n'+json.dumps(encoded)+'\n</properties>\n<content>\n'+p['body']+'\n</content>'
            return {'id': pid, 'text': text}
        if tool == 'notion_create_pages':
            result = []
            for p in args['pages']:
                pid = uuid4().hex
                self.pages[pid] = {'properties': self.decode(p['properties']), 'body': p['content'], 'source': args['parent']['data_source_id']}
                self.writes += 1
                result.append({'id': pid})
            return {'pages': result}
        if tool == 'notion_update_page':
            p = self.pages[args['page_id']]
            if args['command'] == 'replace_content':
                p['body'] = args['new_str']
            else:
                p['properties'].update(self.decode(args['properties']))
            self.writes += 1
            return {'success': True}
        raise AssertionError(tool)

    @staticmethod
    def decode(properties):
        return {k: re.sub(r'\\([\\*~`$\[\]<>{}|^])', r'\1', v) if isinstance(v, str) else v
                for k, v in properties.items()}


class NotionMCPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Workspace(self.root/'library')
        self.data, self.analysis = material()
        self.location = self.root/'sample.txt'
        self.r = self.store.ingest(self.analysis, self.data, location=self.location)
        self.r = self.store.decide(self.r['id'], self.r['snapshot'], 'approve')
        self.target = binding(); self.plugin = FakePlugin(self.target)

    def send(self, **kwargs):
        remote = NotionMCP(self.target, self.root/'outbox', self.plugin)
        return deliver_plan(make_plan(self.store, target=self.target), self.store, remote, self.root/'outbox', target=self.target, **kwargs)

    def test_plugin_mapping_create_relations_and_repeat_without_writes(self):
        report = self.send(); self.assertFalse(report['errors'])
        before = self.plugin.writes
        repeat = self.send()
        self.assertFalse(repeat['errors']); self.assertEqual(repeat['writes'], 0)
        self.assertEqual(before, self.plugin.writes)
        material_page = next(p for p in self.plugin.pages.values() if p['source'] == self.target['collections']['material']['data_source_id'])
        self.assertFalse(material_page['body'].startswith('# sample.txt'))
        self.assertTrue(material_page['properties']['concepts'])

    def test_multiple_materials_create_in_one_call_and_measure_actual_calls(self):
        data, analysis = material('other.txt', 'other original')
        r = self.store.ingest(analysis, data)
        self.store.decide(r['id'], r['snapshot'], 'approve')
        report = self.send()
        self.assertFalse(report['errors'])
        calls = self.plugin.calls.count('notion_create_pages')
        self.assertEqual(calls, len(self.target['collections']))
        self.assertEqual(report['transport_metrics']['batch_creates'], calls)
        self.assertGreater(len(self.plugin.pages), calls)
        self.assertIn('relations', report['phase_seconds'])

    def test_batch_response_loss_requires_explicit_resume_and_no_duplicates(self):
        original = self.plugin
        lost = False
        def wrapper(tool, args):
            nonlocal lost
            result = original(tool, args)
            if tool == 'notion_create_pages' and not lost:
                lost = True
                raise DeliveryError('RESPONSE_LOST')
            return result
        self.plugin = wrapper
        self.assertEqual(self.send()['errors'][0]['code'], 'RESPONSE_LOST')
        self.plugin = original
        self.assertEqual(self.send()['errors'][0]['code'], 'EXPLICIT_RETRY_REQUIRED')
        report = self.send(retry=True)
        self.assertFalse(report['errors'])
        keys = [p['properties']['sync_key'] for p in original.pages.values()]
        self.assertEqual(len(keys), len(set(keys)))

    def test_changed_original_updates_same_page_and_rechecks_approval(self):
        self.send()
        old_pages = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        data, analysis = material(extra='new original')
        analysis['summary'] = '변경된 원본의 VLAN 설정이다.'
        r = self.store.ingest(analysis, data, location=self.location)
        self.assertEqual(make_plan(self.store)['approvals'], {})
        self.store.decide(r['id'], r['snapshot'], 'approve')
        result = self.send(); self.assertFalse(result['errors'])
        new_pages = {p['properties']['sync_key']: pid for pid, p in self.plugin.pages.items()}
        self.assertEqual(old_pages, new_pages)
        source = self.target['collections']['material']['data_source_id']
        material_page = next(p for p in self.plugin.pages.values() if p['source'] == source)
        self.assertEqual(material_page['properties']['source_hash'], data['material_id'])

    def test_user_edit_is_preserved_and_blocks_live_update(self):
        self.send()
        first = next(iter(self.plugin.pages.values())); first['body'] += '\nuser edit'
        before = self.plugin.writes
        report = self.send()
        self.assertEqual(report['errors'][0]['code'], 'REMOTE_CONFLICT')
        self.assertEqual(before, self.plugin.writes)

    def test_selected_material_does_not_publish_others(self):
        d2, a2 = material('other.txt', 'other source')
        r = self.store.ingest(a2, d2); self.store.decide(r['id'], r['snapshot'], 'approve')
        plan = make_plan(self.store, target=self.target, material_ids=[self.r['id']])
        self.assertEqual(list(plan['approvals']), [self.r['id']])
        self.assertEqual(sum(e['kind'] == 'material' for e in plan['entities']), 1)

    def test_reader_resolves_new_page_ids_then_repeats_without_writes(self):
        from analyzer.notion_reader import refresh_reader_target
        self.target['reader'] = {'version': 1, 'pages': {}, 'indexes': {}}
        first = self.send()
        self.assertFalse(first['errors'])
        self.target = refresh_reader_target(self.target, self.root/'outbox')
        self.assertEqual(len(self.target['reader']['pages']), len(self.plugin.pages))
        second = self.send()
        self.assertFalse(second['errors'])
        self.assertEqual(self.send()['writes'], 0)

    def test_ambiguous_same_name_sources_require_identity(self):
        data, analysis = material(extra='another same name source')
        r = self.store.ingest(analysis, data)
        self.store.decide(r['id'], r['snapshot'], 'approve')
        with self.assertRaises(AnalysisError) as error:
            make_plan(self.store)
        self.assertEqual(error.exception.code, 'PUBLISH_SOURCE_AMBIGUOUS')

    def test_inline_property_roundtrip_preserves_windows_paths_and_markdown(self):
        value = r'C:\Users\ICT\notes\VLAN [a]*.txt'
        self.assertEqual(inline_value(inline_text(value)), value)

    def interrupt_property_update(self):
        self.send()
        r = self.store.revise(self.r['id'], self.r['snapshot'], [{'path': '/summary', 'value': '승인한 새 VLAN 설명이다.'}])
        self.store.decide(r['id'], r['snapshot'], 'approve')
        original = self.plugin
        self.body_writes = 0
        def wrapper(tool, args):
            if tool == 'notion_update_page':
                if args['command'] == 'replace_content':
                    self.body_writes += 1
                elif args['command'] == 'update_properties':
                    raise DeliveryError('SERVICE_UNAVAILABLE')
            return original(tool, args)
        self.plugin = wrapper
        result = self.send()
        self.assertEqual(result['errors'][0]['code'], 'SERVICE_UNAVAILABLE')
        self.plugin = original
        return original

    def test_body_stage_checkpoint_resumes_property_failure_without_replacing_body(self):
        plugin = self.interrupt_property_update()
        self.assertEqual(self.body_writes, 1)
        self.assertEqual(self.send()['errors'][0]['code'], 'EXPLICIT_RETRY_REQUIRED')
        before = plugin.writes
        resumed = self.send(retry=True)
        self.assertFalse(resumed['errors'])
        self.assertEqual(plugin.writes-before, 1)

    def test_manual_edit_after_partial_body_write_is_not_overwritten(self):
        plugin = self.interrupt_property_update()
        source = self.target['collections']['material']['data_source_id']
        page = next(p for p in plugin.pages.values() if p['source'] == source)
        page['body'] += '\nmanual edit'
        before = plugin.writes
        result = self.send(retry=True)
        self.assertEqual(result['errors'][0]['code'], 'REMOTE_CONFLICT')
        self.assertEqual(before, plugin.writes)

    def test_partial_scope_cannot_drop_previous_published_material_explanations(self):
        plan = make_plan(self.store)
        scope = check_scope(plan, self.root)
        (self.root/'published_scope.json').write_text(json.dumps(scope), encoding='utf-8')
        plan['entities'] = [e for e in plan['entities'] if e['kind'] != 'material']
        with self.assertRaises(AnalysisError) as error:
            check_scope(plan, self.root)
        self.assertEqual(error.exception.code, 'PUBLISH_SCOPE_INCOMPLETE')

    def test_file_bridge_preserves_unicode_quotes_and_backslashes(self):
        payload = {'text': '한글 “인용” ’문자’, C:\\Users\\ICT'}
        def dispatcher():
            request = self.root/'request.json'
            deadline = time.monotonic()+3
            while not request.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            data = json.loads(request.read_text(encoding='utf-8'))
            (self.root/(data['request_id']+'.json')).write_text(json.dumps({'request_id': data['request_id'],
                'result': {'structuredContent': payload}}, ensure_ascii=True), encoding='utf-8')
        worker = threading.Thread(target=dispatcher); worker.start()
        with patch('analyzer.notion_mcp.BRIDGE_DIRECTORY', self.root), redirect_stdout(io.StringIO()):
            value = rpc('fetch', {'id': 'safe-test'})
        worker.join()
        self.assertEqual(value, payload)

    def test_batched_file_bridge_preserves_order_and_unicode(self):
        requests = [{'tool': 'fetch', 'args': {'id': 'first'}},
                    {'tool': 'fetch', 'args': {'id': 'second'}}]
        payloads = [{'text': '첫 응답 “한글” C:\\Users\\ICT'}, {'text': '두 번째 응답'}]
        observed = []
        def dispatcher():
            request = self.root/'request.json'
            deadline = time.monotonic()+3
            while not request.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            data = json.loads(request.read_text(encoding='utf-8'))
            observed.extend(data['requests'])
            (self.root/(data['request_id']+'.json')).write_text(json.dumps({
                'request_id': data['request_id'],
                'results': [{'structuredContent': p} for p in payloads]}, ensure_ascii=True), encoding='utf-8')
        worker = threading.Thread(target=dispatcher); worker.start()
        with patch('analyzer.notion_mcp.BRIDGE_DIRECTORY', self.root), redirect_stdout(io.StringIO()):
            values = rpc_many(requests)
        worker.join()
        self.assertEqual(observed, requests)
        self.assertEqual(values, payloads)

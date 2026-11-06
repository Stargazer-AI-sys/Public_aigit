import copy
import hashlib
import http.client
import json
import re
import tempfile
import threading
import unittest
from pathlib import Path

from analyzer.batch import run_batch
from analyzer.cache import context_for, digest
from analyzer.classification import DEFAULT_POLICY, suggest, validate_policy
from analyzer.core import AnalysisError
from analyzer.review_server import make_server
from analyzer.workspace import Workspace
from collector.main import save_inventory
from smoke_check import sample, OfflineProvider


def material(filename='sample.txt', extra=''):
    data, analysis = sample()
    data['filename'] = filename
    if extra:
        data['extracted_text'] += '\n'+extra
        data['material_id'] = hashlib.sha256(data['extracted_text'].encode()).hexdigest()
    analysis['source'] = {k: data[k] for k in ('filename', 'extension', 'material_id')}
    return data, analysis


class OrganizerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = Workspace(self.root/'library')
        self.data, self.analysis = material()

    def inventory(self, materials):
        rows = [{'filename': d['filename'], 'extension': d['extension'], 'sha256': d['material_id'],
                 'text': d['extracted_text'], 'status': 'success', 'path': str(self.root/d['filename'])} for d, _ in materials]
        p = self.root/'inventory.csv'; save_inventory(rows, p)
        return p

    def test_classification_uses_topics_and_keeps_unknown_scope(self):
        known = suggest(self.analysis, DEFAULT_POLICY)
        self.assertTrue(known['scope_confirmed'])
        self.assertEqual(known['paths'][0][:2], ['NETWORK', '2. 네트워크 접속'])
        changed = copy.deepcopy(self.analysis)
        changed['topics'] = [{'name': '웹 쇼핑몰 UI'}]
        unknown = suggest(changed, DEFAULT_POLICY)
        self.assertFalse(unknown['scope_confirmed'])
        self.assertIn(['NETWORK', '관련성 미확인'], unknown['paths'])

    def test_hybrid_routing_is_not_cloud_hybrid_and_alias_cycle_rejected(self):
        changed = copy.deepcopy(self.analysis)
        changed['topics'] = [{'name': '동적 라우팅', 'children': [{'name': 'Hybrid'}]}]
        self.assertEqual(suggest(changed, DEFAULT_POLICY)['paths'][0][1], '3. IP 라우팅')
        policy = copy.deepcopy(DEFAULT_POLICY); policy['concept_aliases'] = {'a': 'b', 'b': 'a'}
        with self.assertRaises(AnalysisError): validate_policy(policy)

    def test_related_materials_preserve_different_descriptions(self):
        self.store.ingest(self.analysis, self.data)
        d2, a2 = material('second.txt', 'additional original note')
        a2['concepts'][0]['description'] = '다른 원문의 VLAN 설명이다.'
        second = self.store.ingest(a2, d2)
        catalog = self.store.catalog()
        self.assertEqual(len(catalog['materials']), 2)
        self.assertEqual(len(catalog['concepts']), 1)
        self.assertEqual(len(catalog['concepts'][0]['sources']), 2)
        self.assertTrue(catalog['concepts'][0]['different_descriptions'])
        self.assertFalse(catalog['related'][second['id']][0]['semantic_duplicate_confirmed'])

    def test_approval_is_revision_bound_and_export_only_approved(self):
        r = self.store.ingest(self.analysis, self.data)
        d2, a2 = material('pending.txt', 'note'); self.store.ingest(a2, d2)
        approved = self.store.decide(r['id'], r['snapshot'], 'approve')
        self.assertEqual(len(self.store.approved()['materials']), 1)
        with self.assertRaises(AnalysisError) as error:
            self.store.decide(r['id'], r['snapshot'], 'hold')
        self.assertEqual(error.exception.code, 'REVIEW_STALE')
        self.store.decide(approved['id'], approved['snapshot'], 'edit', paths=[['NETWORK', '사용자 분류', 'VLAN']])
        self.assertEqual(self.store.approved()['materials'], [])
        self.assertEqual(len(self.store.history(r['id'])), 3)

    def test_same_import_keeps_approval_changed_analysis_invalidates(self):
        r = self.store.ingest(self.analysis, self.data)
        approved = self.store.decide(r['id'], r['snapshot'], 'approve')
        same = self.store.ingest(self.analysis, self.data)
        self.assertEqual(same['snapshot'], approved['snapshot'])
        updated = copy.deepcopy(self.analysis); updated['summary'] = 'VLAN 10 설정 명령 예시를 정리한다.'
        changed = self.store.ingest(updated, self.data)
        self.assertEqual(changed['status'], 'pending')
        self.assertEqual(self.store.approved()['materials'], [])

    def test_publication_hold_cannot_be_approved_without_explicit_release(self):
        policy = copy.deepcopy(DEFAULT_POLICY); policy['publication_holds'][self.data['filename']] = '원문 내용 검토 필요'
        self.store.set_policy(policy)
        r = self.store.ingest(self.analysis, self.data)
        with self.assertRaises(AnalysisError): self.store.decide(r['id'], r['snapshot'], 'approve')
        released = self.store.release_hold(r['id'], r['snapshot'], '별도 검토로 원문 확인')
        self.assertEqual(released['status'], 'pending')
        self.store.decide(r['id'], released['snapshot'], 'approve')
        self.assertEqual(len(self.store.approved()['materials']), 1)

    def test_user_prose_edit_preserves_evidence_resets_approval_and_survives_reimport(self):
        r = self.store.ingest(self.analysis, self.data)
        approved = self.store.decide(r['id'], r['snapshot'], 'approve')
        revised = self.store.revise(r['id'], approved['snapshot'], [{'path': '/practice/0/description', 'value': '사용자가 검토한 VLAN 10 설정 예시다.'}])
        self.assertEqual(revised['status'], 'pending')
        self.assertEqual(revised['analysis']['practice'][0]['evidence'], self.analysis['practice'][0]['evidence'])
        self.assertEqual(self.store.approved()['materials'], [])
        imported = self.store.ingest(self.analysis, self.data)
        self.assertEqual(imported['analysis']['practice'][0]['description'], '사용자가 검토한 VLAN 10 설정 예시다.')
        self.assertEqual(len(imported['content_edits']), 1)
        with self.assertRaises(AnalysisError):
            self.store.revise(r['id'], revised['snapshot'], [{'path': '/practice/0/evidence', 'value': '변경 금지'}])
        with self.assertRaises(AnalysisError):
            self.store.revise(r['id'], revised['snapshot'], [{'path': '/summary', 'value': 'a'*121}])

    def test_policy_change_invalidates_prior_approval_and_preserves_history(self):
        r = self.store.ingest(self.analysis, self.data)
        self.store.decide(r['id'], r['snapshot'], 'approve')
        p = copy.deepcopy(DEFAULT_POLICY); p['concept_aliases']['VLAN'] = 'Virtual LAN'
        self.store.set_policy(p)
        self.assertEqual(self.store.approved()['materials'], [])
        self.assertEqual(self.store.catalog()['concepts'][0]['name'], 'Virtual LAN')
        self.assertGreaterEqual(len(self.store.history(r['id'])), 3)

    def test_changed_source_same_path_keeps_old_revision_but_exports_current_only(self):
        location = self.root/'sample.txt'
        r = self.store.ingest(self.analysis, self.data, location=location)
        self.store.decide(r['id'], r['snapshot'], 'approve')
        d2, a2 = material(extra='changed source')
        new = self.store.ingest(a2, d2, location=location)
        self.assertNotEqual(new['id'], r['id'])
        self.assertEqual(len(self.store.list()), 1)
        self.assertEqual(len(self.store.list(current=False)), 2)
        self.assertEqual(self.store.approved()['materials'], [])

    def test_bad_source_and_modified_saved_result_block_reuse(self):
        bad = copy.deepcopy(self.analysis); bad['source']['material_id'] = '0'*64
        with self.assertRaises(AnalysisError): self.store.ingest(bad, self.data)
        r = self.store.ingest(self.analysis, self.data)
        with self.store.db() as db:
            r['analysis']['summary'] = 'tampered'
            db.execute('UPDATE materials SET record=? WHERE id=?', (json.dumps(r), r['id']))
        with self.assertRaises(AnalysisError): self.store.reusable(self.data)

    def test_batch_reuses_existing_import_and_generates_missing_only(self):
        from analyzer.core import load_schema
        from analyzer.schemas import DEFAULT_SCHEMA
        context, _ = context_for(self.data, OfflineProvider(self.analysis), load_schema(DEFAULT_SCHEMA))
        first = self.store.ingest(self.analysis, self.data, analysis_context=context)
        d2, a2 = material('new.txt', 'new source')
        calls = []
        def factory(data):
            calls.append(data['filename']); return OfflineProvider(a2)
        report = run_batch(self.inventory([(self.data, self.analysis), (d2, a2)]), self.store.root, provider_factory=factory)
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['reused'], 1); self.assertEqual(report['new_successes'], 1)
        self.assertEqual(calls, ['sample.txt', 'new.txt'])
        second = run_batch(self.root/'inventory.csv', self.store.root, provider_factory=lambda d: OfflineProvider(self.analysis if d['filename'] == self.data['filename'] else a2))
        self.assertEqual(second['reused'], 2)
        self.assertEqual(second['new_api_attempts'], 0)

    def test_missing_concept_report_blocks_import_and_automatic_retry(self):
        broken = copy.deepcopy(self.analysis)
        broken['practice'][0]['related_concepts'] = ['누락개념']
        inventory = self.inventory([(self.data, broken)])
        provider = OfflineProvider(broken)
        report = run_batch(inventory, self.store.root, provider_factory=lambda d: provider)
        self.assertEqual(report['failed'], 1)
        self.assertEqual(provider.calls, 1)
        item = report['items'][0]
        self.assertTrue(item['review_required'])
        review = json.loads(Path(item['review_report']).read_text(encoding='utf-8'))
        self.assertEqual(review['items'][0]['name'], '누락개념')
        self.assertEqual(self.store.list(), [])
        again = run_batch(inventory, self.store.root, provider_factory=lambda d: provider)
        self.assertEqual(again['blocked'], 1)
        self.assertEqual(provider.calls, 1)

    def test_failed_jobs_are_not_automatically_retried(self):
        inventory = self.inventory([(self.data, self.analysis)])
        class Broken(OfflineProvider):
            def generate(self, messages): return 'broken JSON'
        first = run_batch(inventory, self.store.root, provider_factory=lambda d: Broken(self.analysis))
        self.assertEqual(first['failed'], 1)
        provider = OfflineProvider(self.analysis)
        again = run_batch(inventory, self.store.root, provider_factory=lambda d: provider)
        self.assertEqual(again['blocked'], 1); self.assertEqual(provider.calls, 0)
        retried = run_batch(inventory, self.store.root, provider_factory=lambda d: provider, retry_failed=True)
        self.assertEqual(retried['new_successes'], 1)

    def test_interrupted_job_requires_explicit_retry_and_workspace_lock(self):
        inventory = self.inventory([(self.data, self.analysis)])
        class Interrupted(OfflineProvider):
            def generate(self, messages): raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt): run_batch(inventory, self.store.root, provider_factory=lambda d: Interrupted(self.analysis))
        again = run_batch(inventory, self.store.root, provider_factory=lambda d: OfflineProvider(self.analysis))
        self.assertEqual(again['blocked'], 1)
        (self.store.root/'batch.lock').write_text('other-worker')
        with self.assertRaises(AnalysisError): run_batch(inventory, self.store.root)

    def test_batch_without_api_opt_in_never_calls_provider(self):
        inventory = self.inventory([(self.data, self.analysis)])
        engine = OfflineProvider(self.analysis)
        result = run_batch(inventory, self.store.root, provider='openai', provider_factory=lambda d: engine)
        self.assertEqual(engine.calls, 0)
        self.assertEqual(result['new_api_attempts'], 0)

    def test_explicit_interrupted_recovery_removes_stale_cache_lock(self):
        from analyzer.cache import context_for
        from analyzer.core import load_schema
        from analyzer.schemas import DEFAULT_SCHEMA
        inventory = self.inventory([(self.data, self.analysis)])
        engine = OfflineProvider(self.analysis)
        context, _ = context_for(self.data, engine, load_schema(DEFAULT_SCHEMA))
        cache = self.store.root/'cache'; cache.mkdir()
        stale = cache/(digest(context)+'.lock'); stale.write_text('stopped-worker')
        (self.store.root/'batch.lock').write_text('stopped-worker')
        result = run_batch(inventory, self.store.root, provider_factory=lambda d: engine,
                           recover_interrupted=True, retry_failed=True)
        self.assertEqual(result['new_successes'], 1)
        self.assertEqual(result['recovered_cache_locks'], 1)
        self.assertFalse(stale.exists())

    def test_batch_caps_new_attempts_even_when_many_materials_are_pending(self):
        d2, a2 = material('second.txt', 'new source')
        inventory = self.inventory([(self.data, self.analysis), (d2, a2)])
        engines = []
        class Counted(OfflineProvider):
            def __init__(self, analysis):
                super().__init__(analysis)
                self.trace = {'api_request_attempted': True, 'actual_ai_call': False}
        def factory(data):
            engine = Counted(self.analysis if data['filename'] == self.data['filename'] else a2)
            engines.append(engine); return engine
        result = run_batch(inventory, self.store.root, provider='openai', allow_api=True, max_new_calls=1, provider_factory=factory)
        self.assertEqual(sum(e.calls for e in engines), 1)
        self.assertEqual(result['new_api_attempts'], 1)
        self.assertEqual(result['new_successes'], 1)

    def test_server_rejects_external_origin_and_stale_decisions(self):
        r = self.store.ingest(self.analysis, self.data)
        server = make_server(self.store)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), thread.join()))
        conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
        self.addCleanup(conn.close)
        conn.request('GET', '/'); response = conn.getresponse(); page = response.read().decode()
        self.assertEqual(response.status, 200)
        token = re.search("const token='([^']+)'", page).group(1)
        payload = json.dumps({'id': r['id'], 'snapshot': r['snapshot'], 'action': 'approve'})
        origin = f'http://127.0.0.1:{server.server_port}'
        conn.request('POST', '/api/decide', payload, {'Origin': 'https://external.example', 'X-Review-Token': token})
        response=conn.getresponse(); response.read(); self.assertEqual(response.status, 403)
        headers={'Origin': origin, 'X-Review-Token': token, 'Content-Type': 'application/json'}
        conn.request('POST', '/api/decide', payload, headers)
        response=conn.getresponse(); response.read(); self.assertEqual(response.status, 200)
        conn.request('POST', '/api/decide', payload, headers)
        response=conn.getresponse(); response.read(); self.assertEqual(response.status, 409)
        conn.request('POST', '/api/revise', '{}', headers)
        response=conn.getresponse(); response.read(); self.assertEqual(response.status, 404)
        conn.request('POST', '/api/decide', json.dumps({'id':r['id'],'snapshot':r['snapshot'],'action':'edit'}), headers)
        response=conn.getresponse(); response.read(); self.assertEqual(response.status, 400)
        conn.request('POST', '/api/export', '{}', headers)
        response=conn.getresponse(); export=json.loads(response.read()); self.assertEqual(export['count'], 1)
        self.assertFalse(export['notion_sent'])

    def test_curriculum_groups_concepts_under_learning_units_with_pinned_sources(self):
        self.store.ingest(self.analysis, self.data)
        view = self.store.catalog()['curriculum']
        self.assertEqual(len(view['domains']), 6)
        self.assertIn('v1.1', view['title'])
        access = view['domains'][1]
        vlan = next(u for u in access['units'] if u['code']=='2.1')
        self.assertEqual(vlan['concepts'][0]['name'], 'VLAN')
        self.assertEqual(len(vlan['material_ids']), 1)
        self.assertIn('cisco.com', vlan['references'][0]['url'])
        rip = next(u for u in view['domains'][2]['units'] if 'RIP' in u['title'])
        self.assertEqual(rip['scope'], 'extension')
        self.assertIn('rfc-editor.org', rip['references'][0]['url'])
        self.assertEqual(rip['concepts'], [])

    def test_malformed_curriculum_is_rejected(self):
        policy = copy.deepcopy(DEFAULT_POLICY)
        policy['curriculum']['domains'][0]['units'][0]['references'][0]['url'] = 'javascript:alert(1)'
        with self.assertRaises(AnalysisError): validate_policy(policy)

    def test_generic_json_web_app_is_not_forced_into_network_automation(self):
        data = copy.deepcopy(self.analysis)
        data['topics'] = [{'name': '웹 애플리케이션 JSON'}]
        data['concepts'] = [{'name': 'JSON', 'description': '웹 앱 데이터'}]
        self.assertFalse(suggest(data, DEFAULT_POLICY)['scope_confirmed'])

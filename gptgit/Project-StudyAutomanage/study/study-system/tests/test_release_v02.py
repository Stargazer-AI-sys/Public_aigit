import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from analyzer.cache import context_for, run_with_cache
from analyzer.core import AnalysisError, analyze, build_prompt, load_schema
from analyzer.main import main
from analyzer.openai_provider import OpenAIProvider
from analyzer.render import redact, render_markdown
from analyzer.schemas import DEFAULT_SCHEMA, schema_for, schema_for_run
from smoke_check import sample, OfflineProvider
import test_knowledge

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]


class StableKnowledgeTests(test_knowledge.KnowledgeTests):
    """Run the existing reviewed-comment and API-wire cases against stable v0.2."""
    def setUp(self):
        super().setUp()
        self.schema = load_schema(DEFAULT_SCHEMA)
        self.analysis['schema_version'] = '0.2'


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.data, self.analysis = sample()
        self.schema = load_schema(DEFAULT_SCHEMA)

    def cli(self, *args):
        with patch('sys.argv', ['analyzer', *map(str, args)]), patch('builtins.print'):
            return main()

    def test_version_detection_and_source_schemas_match(self):
        for version, filename in [('0.2', 'study_material_analysis_schema_v0.2.json'),
                                  ('0.2-draft', 'study_material_analysis_schema_v0.2_draft.json')]:
            item = dict(self.analysis, schema_version=version)
            self.assertEqual(schema_for(item)['properties']['schema_version']['const'], version)
            self.assertEqual((ROOT/'output'/filename).read_bytes(), (PROJECT/'output'/filename).read_bytes())
        old = copy.deepcopy(self.analysis)
        old.pop('schema_version'); old.pop('sections')
        self.assertNotIn('schema_version', schema_for(old)['properties'])
        with self.assertRaises(AnalysisError): schema_for(dict(old, schema_version='9.0'))

    def test_default_run_saves_readable_and_reuses_cache(self):
        from collector.main import save_inventory
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            row = {'filename': self.data['filename'], 'extension': self.data['extension'],
                   'sha256': self.data['material_id'], 'status': 'success', 'text': self.data['extracted_text']}
            save_inventory([row], p/'inventory.csv')
            (p/'response.json').write_text(json.dumps(self.analysis), encoding='utf-8')
            args = ('run', '--inventory', p/'inventory.csv', '--filename', self.data['filename'],
                    '--response-file', p/'response.json', '--cache-dir', p/'cache', '--output-dir', p/'runs')
            self.assertEqual(self.cli(*args), 0)
            self.assertEqual(self.cli(*args, '--reuse-only'), 0)
            runs = list((p/'runs').iterdir())
            self.assertEqual(len(runs), 2)
            traces = [json.loads((r/'trace.json').read_text(encoding='utf-8')) for r in runs]
            self.assertEqual(sum(t.get('result_reused', False) for t in traces), 1)
            for r in runs:
                saved = json.loads((r/'success/analysis.json').read_text(encoding='utf-8'))
                self.assertEqual(saved['schema_version'], '0.2')
                self.assertIn('sw acc vlan 10', (r/'result.md').read_text(encoding='utf-8'))

    def test_validate_mixed_versions_and_unknown_version(self):
        old = copy.deepcopy(self.analysis); old.pop('schema_version'); old.pop('sections')
        draft = dict(self.analysis, schema_version='0.2-draft')
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'results.json').write_text(json.dumps({'materials': [old, draft, self.analysis]}), encoding='utf-8')
            self.assertEqual(self.cli('validate', '--file', p/'results.json', '--output-dir', p/'checks'), 0)
            (p/'results.json').write_text(json.dumps(dict(self.analysis, schema_version='9.0')), encoding='utf-8')
            self.assertEqual(self.cli('validate', '--file', p/'results.json', '--output-dir', p/'checks'), 1)

    def test_recheck_detects_old_draft_and_stable_without_rewriting(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'analyzer_input.json').write_text(json.dumps(self.data), encoding='utf-8')
            for version in ['0.1', '0.2-draft', '0.2']:
                item = copy.deepcopy(self.analysis)
                if version == '0.1': item.pop('schema_version'); item.pop('sections')
                else: item['schema_version'] = version
                (p/'raw_response.json').write_text(json.dumps(json.dumps(item)), encoding='utf-8')
                before = (p/'raw_response.json').read_bytes()
                self.assertEqual(self.cli('recheck', '--run-dir', p, '--output-dir', p/'runs'), 0)
                self.assertEqual((p/'raw_response.json').read_bytes(), before)
            self.assertEqual(len(list((p/'runs').iterdir())), 3)

    def test_stable_links_are_validated_and_unambiguous_repair_preserved(self):
        item = copy.deepcopy(self.analysis)
        item['concepts'].append({'name': '포트', 'description': 'Fa0/1 설정 예시다.'})
        item['relationships'] = [{'from': 'VLAN', 'relation': '설정 예시에서 지정한다', 'to': '포트'}]
        item['sections'][0]['content_refs'].append('/concepts/1')
        result, audit = analyze(self.data, OfflineProvider(item), self.schema)
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertIn('/relationships/0', result['analysis']['sections'][0]['content_refs'])
        self.assertTrue(audit['section_link_repairs'])
        item['sections'][0]['content_refs'].append('/practice/999')
        failed, _ = analyze(self.data, OfflineProvider(item), self.schema)
        self.assertEqual(failed['error']['code'], 'QUALITY_VALIDATION_ERROR')

    def test_renderer_shows_body_and_masks_credentials_without_editing_json(self):
        item = copy.deepcopy(self.analysis)
        marker = 'example-private-value'
        item['practice'][0]['evidence'] += '\nvtp password ' + marker + '\n```\n<script>x</script>'
        before = copy.deepcopy(item)
        text = render_markdown(item)
        self.assertIn('Fa0/1', text)
        self.assertIn('sw acc vlan 10', text)
        self.assertNotIn(marker, text)
        self.assertIn('````text', text)
        self.assertEqual(item, before)
        item['sections'][0]['content_refs'] = ['/practice/999']
        with self.assertRaises(AnalysisError): render_markdown(item)

    def test_renderer_reviewed_comments_and_comparisons(self):
        item = copy.deepcopy(self.analysis)
        item['theory'] = {'comparisons': [{'subject_a': 'A', 'subject_b': 'B', 'criteria': ['원문 비교 항목'], 'evidence': 'A B'}]}
        item['sections'][0]['content_refs'].append('/theory/comparisons/0')
        item['references'] = [{'id': 'source-a', 'title': '검토 출처', 'url': 'https://example.com/source',
                               'verification_status': 'source_checked', 'checked_on': '2026-10-16'}]
        item['sections'][0]['comment'] = {'kind': 'supplement', 'text': '검토된 설명이다.', 'reference_ids': ['source-a']}
        text = render_markdown(item, pending=1, excluded=2)
        self.assertIn('❗ 보충:', text)
        self.assertIn('https://example.com/source', text)
        self.assertIn('원문 비교 항목', text)
        self.assertIn('검토 대기 후보 1개', text)
        item['references'][0]['verification_status'] = 'unverified'
        with self.assertRaises(AnalysisError): render_markdown(item)

    def test_redaction_preserves_prose_and_masks_only_credential_values(self):
        prose = 'domain, password 를 지정하고 그 정보로 동기화'
        text = prose + '\nvtp password example-private-value\nOPENAI_API_KEY="offline-placeholder"\nnext line'
        redacted = redact(text)
        self.assertIn(prose, redacted)
        self.assertIn('next line', redacted)
        self.assertNotIn('example-private-value', redacted)
        self.assertNotIn('offline-placeholder', redacted)

    def test_no_cross_version_cache_reuse_or_paid_call_on_miss(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            draft = dict(self.analysis, schema_version='0.2-draft')
            provider = OfflineProvider(draft)
            result, _ = run_with_cache(self.data, provider, schema_for(draft), p/'cache', p)
            self.assertEqual(result['status'], 'SUCCESS')
            stable = OfflineProvider(self.analysis)
            missing, _ = run_with_cache(self.data, stable, self.schema, p/'cache', p, reuse_only=True)
            self.assertEqual(missing['error']['code'], 'CACHE_MISS')
            self.assertEqual(stable.calls, 0)

    def test_apply_review_auto_version_saves_readable_and_preserves_core(self):
        from analyzer.comment_review import make_request
        request = make_request(self.analysis, [{'section_id': 'vlan', 'kind': 'supplement',
            'text': '검토된 보충 문장이다.', 'reason': '테스트용 검토 후보', 'search_query': 'VLAN'}])
        decisions = [{'candidate_id': request['candidates'][0]['id'], 'outcome': 'supported',
                      'reason': '테스트용 로컬 검토 결정', 'reference': {
                          'id': 'source-a', 'title': '테스트 출처', 'url': 'https://example.com/source',
                          'verification_status': 'source_checked', 'checked_on': '2026-10-16'}}]
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/self.data['filename']).write_bytes(self.data['extracted_text'].encode('utf-8'))
            for name, data in [('analysis', self.analysis), ('request', request), ('decisions', decisions)]:
                (p/(name+'.json')).write_text(json.dumps(data), encoding='utf-8')
            before = (p/'analysis.json').read_bytes()
            self.assertEqual(self.cli('apply-review', '--analysis', p/'analysis.json',
                                     '--request', p/'request.json', '--decisions', p/'decisions.json',
                                     '--source-file', p/self.data['filename'], '--output-dir', p/'runs'), 0)
            output = next((p/'runs').iterdir())
            saved = json.loads((output/'analysis.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['practice'], self.analysis['practice'])
            self.assertEqual(saved['schema_version'], '0.2')
            self.assertIn('❗ 보충:', (output/'result.md').read_text(encoding='utf-8'))
            self.assertEqual(before, (p/'analysis.json').read_bytes())

    def test_wire_prompt_uses_stable_version_and_preserves_scope(self):
        provider = OpenAIProvider(self.schema, api_key='offline-placeholder', transport=lambda *a, **k: None)
        messages = provider.prepare_messages(build_prompt(self.data, self.schema))
        self.assertIn('schema_version은 0.2입니다', messages[0]['content'])
        self.assertIn('장비별 비교', messages[0]['content'])
        self.assertEqual(provider.transport_schema['properties']['schema_version']['enum'], ['0.2'])
        self.assertFalse(provider.trace['api_request_attempted'])

    def test_distribution_is_self_contained_and_has_no_materials(self):
        spec = importlib.util.spec_from_file_location('build_distribution', PROJECT/'tools/build_analyzer_distribution.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            manifest = module.build(p/'release.zip')
            with ZipFile(p/'release.zip') as archive:
                names = archive.namelist()
                self.assertFalse(any('/sourcefile/' in n or '.sqlite3' in n or 'raw_response' in n for n in names))
                archive.extractall(p/'unpacked')
            extracted = p/'unpacked/study-system'
            for name, expected in manifest['files'].items():
                self.assertEqual(hashlib.sha256((extracted/name).read_bytes()).hexdigest(), expected)
            run = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(extracted/'smoke_check.py')],
                                 cwd=p, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

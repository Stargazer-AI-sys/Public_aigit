import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_knowledge
from test_knowledge import Stub, ROOT
from test_openai import Response
from analyzer.core import analyze, build_prompt
from analyzer.cache import run_with_cache
from analyzer.openai_provider import OpenAIProvider
from analyzer.main import main


class AuxiliaryTests(unittest.TestCase):
    def setUp(self):
        fixture = test_knowledge.KnowledgeTests()
        fixture.setUp()
        self.schema, self.data = fixture.schema, fixture.data
        self.full, self.context = fixture.analysis, fixture.context
        self.base = copy.deepcopy(self.full)
        self.base['sections'][-1].pop('comment')
        self.base.pop('references')
        self.candidate = {'section_id': 'vtp', 'kind': 'supplement',
                          'text': '예시 보충 후보이다.', 'reason': '핵심 의미를 이해하기 어렵다.',
                          'search_query': 'Cisco VTP'}

    def wire(self, value, node=None):
        node = self.schema if node is None else node
        if '$ref' in node:node = self.schema['$defs'][node['$ref'].split('/')[-1]]
        if isinstance(value, dict):
            result = {}
            for key, child in node.get('properties', {}).items():
                if key in ('source', 'references'):continue
                if key == 'evidence' and key in value:
                    text = self.data['extracted_text']; quote = value[key]; pos = text.index(quote)
                    result[key] = {'start_line': text[:pos].count('\n') + 1,
                                   'end_line': text[:pos + len(quote) - 1].count('\n') + 1}
                else:result[key] = self.wire(value[key], child) if key in value else None
            return result
        if isinstance(value, list):return [self.wire(x, node['items']) for x in value]
        return value

    def api(self, wire):
        calls = []
        body = {'status': 'completed', 'model': 'gpt-6-luna', 'output': [
            {'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(wire)}]}]}
        def transport(*args, **kwargs):
            calls.append(1)
            return Response(body)
        provider = OpenAIProvider(self.schema, api_key='test-key', transport=transport)
        provider.reference_context = self.context
        result, audit = analyze(self.data, provider, self.schema)
        self.assertEqual(len(calls), 1)  # No corrective retry for auxiliary errors.
        self.assertFalse(audit['trace']['actual_ai_call'])
        return result, audit

    def test_network_and_minimal_supplement_policy_in_prompt(self):
        prompt = build_prompt(self.data, self.schema)[0]['content']
        self.assertIn('[NETWORK SCOPE]', prompt)
        for text in ('온프레미스', '클라우드 네트워크', '네트워크 자동화', '0개여도 정상', '핵심 의미를 이해할 수 없는 경우'):
            self.assertIn(text, prompt)

    def test_malformed_candidate_does_not_fail_core(self):
        for candidates in ('bad', 17, {'status': 'source_checked'}):
            result, audit = analyze(self.data, Stub(dict(self.base, review_candidates=candidates)), self.schema)
            self.assertEqual(result['analysis'], self.base)
            self.assertTrue(audit['auxiliary_review']['issues'])
            self.assertEqual(audit['review_request']['candidates'], [])

    def test_valid_candidate_survives_invalid_neighbor(self):
        response = dict(self.base, review_candidates=[{'broken': True}, self.candidate])
        result, audit = analyze(self.data, Stub(response), self.schema)
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(len(audit['review_request']['candidates']), 1)
        self.assertEqual(audit['review_request']['candidates'][0]['section_id'], 'vtp')

    def test_bad_comment_cannot_poison_evidence_resolution(self):
        wire = self.wire(self.full)
        wire['sections'][0]['comment'] = {'evidence': {'start_line': 999, 'end_line': 1000}}
        wire['review_candidates'] = 'bad'
        result, audit = self.api(wire)
        self.assertEqual(result['analysis'], self.full)
        self.assertGreaterEqual(len(audit['auxiliary_review']['issues']), 2)

    def test_api_core_without_any_comments_or_candidates(self):
        wire = self.wire(self.base)
        wire['review_candidates'] = None
        result, audit = self.api(wire)
        self.assertEqual(result['analysis'], self.base)
        self.assertEqual(audit['auxiliary_review']['status'], 'OK')

    def test_core_errors_remain_fatal_with_bad_auxiliary(self):
        for mutate, expected in [
            (lambda w: w.update(summary=None), 'SCHEMA_VALIDATION_ERROR'),
            (lambda w: w['practice'][0].update(evidence={'start_line': 999, 'end_line': 1000}), 'EVIDENCE_REFERENCE_ERROR'),
            (lambda w: w['relationships'][0].update(to='없는 개념'), 'QUALITY_VALIDATION_ERROR'),
            (lambda w: w['sections'][0].update(content_refs=['/practice/999']), 'QUALITY_VALIDATION_ERROR')]:
            wire = self.wire(self.base); wire['review_candidates'] = 'bad'; mutate(wire)
            result, _ = self.api(wire)
            self.assertEqual(result['error']['code'], expected)

    def test_whole_response_parse_error_is_not_auxiliary(self):
        result, _ = analyze(self.data, Stub(None), self.schema)
        self.assertEqual(result['error']['code'], 'SCHEMA_VALIDATION_ERROR')
        class Broken:
            name = 'broken-json'
            def generate(self, messages):return '{bad json'
        result, _ = analyze(self.data, Broken(), self.schema)
        self.assertEqual(result['error']['code'], 'JSON_PARSE_ERROR')

    def test_dropped_auxiliary_diagnostics_survive_cache_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            response = dict(self.base, review_candidates='bad')
            result, audit = run_with_cache(self.data, Stub(response), self.schema,
                                           Path(directory)/'cache', directory)
            reused, cached = run_with_cache(self.data, Stub(response), self.schema,
                                            Path(directory)/'cache', directory, reuse_only=True)
            self.assertEqual(result, reused)
            self.assertEqual(audit['auxiliary_review'], cached['auxiliary_review'])
            self.assertTrue(cached['trace']['warnings'])

    def test_cli_missing_context_file_keeps_saved_core(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'analyzer_input.json').write_text(json.dumps(self.data), encoding='utf-8')
            (path/'raw_response.json').write_text(json.dumps(self.full), encoding='utf-8')
            args = ['analyzer', 'recheck', '--run-dir', str(path), '--schema',
                    str(ROOT/'output/study_material_analysis_schema_v0.2_draft.json'),
                    '--reference-context', str(path/'missing.json'), '--output-dir', str(path/'runs')]
            with patch('sys.argv', args), patch('builtins.print'):
                self.assertEqual(main(), 0)
            run = next((path/'runs').iterdir())
            result = json.loads((run/'success/analysis.json').read_text(encoding='utf-8'))
            self.assertEqual(result, self.base)
            self.assertTrue((run/'auxiliary_review.json').exists())

    def test_storage_failure_remains_fatal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'analyzer_input.json').write_text(json.dumps(self.data), encoding='utf-8')
            (path/'raw_response.json').write_text(json.dumps(self.base), encoding='utf-8')
            args = ['analyzer', 'recheck', '--run-dir', str(path), '--schema',
                    str(ROOT/'output/study_material_analysis_schema_v0.2_draft.json')]
            with patch('sys.argv', args), patch('analyzer.main.new_run', side_effect=PermissionError()), patch('builtins.print'):
                self.assertEqual(main(), 2)

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.comment_review import apply_review, make_request, validate_request
from analyzer.core import AnalysisError, analyze, load_schema
from analyzer.cache import run_with_cache
from analyzer.recheck import recheck_run
import test_knowledge
from test_knowledge import Stub, ROOT


class CommentReviewTests(unittest.TestCase):
    def setUp(self):
        fixture = test_knowledge.KnowledgeTests()
        fixture.setUp()
        self.schema, self.material = fixture.schema, fixture.data
        self.base = copy.deepcopy(fixture.analysis)
        self.base['sections'][-1].pop('comment')
        self.base.pop('references')
        self.candidate = {'section_id': 'etherchannel', 'kind': 'correction',
                          'text': 'channel-group ?는 명령의 입력 인수·옵션을 확인하는 도움말 구문이다.',
                          'reason': '기존 분석에서 도움말 조회를 미완성 메모로 해석했다.',
                          'search_query': 'Cisco IOS context sensitive help question mark'}
        self.request = make_request(self.base, [self.candidate])
        self.decision = {'candidate_id': self.request['candidates'][0]['id'],
                         'outcome': 'supported',
                         'reason': '공식 CLI 문서에서 공백 뒤 물음표의 인수·키워드 도움말 기능을 확인했다.',
                         'reference': copy.deepcopy(fixture.analysis['references'][0])}

    def test_proposal_is_audit_only(self):
        response = dict(self.base, review_candidates=[self.candidate])
        result, audit = analyze(self.material, Stub(response), self.schema)
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertEqual(result['analysis'], self.base)
        self.assertEqual(audit['review_request'], self.request)
        self.assertFalse(audit['trace']['actual_ai_call'])

    def test_verified_comment_preserves_body_and_source(self):
        original = copy.deepcopy(self.base)
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('no network')):
            result, report = apply_review(self.base, self.request, [self.decision], self.schema, self.material)
        self.assertEqual(report['decisions'][0]['status'], 'applied')
        self.assertEqual(result['sections'][-1]['comment']['text'], self.candidate['text'])
        self.assertEqual(result['practice'], original['practice'])
        self.assertEqual(result['source'], original['source'])
        self.assertEqual(self.base, original)

    def test_unresolved_rejected_pending_never_publish(self):
        for outcome in ('rejected', 'unresolved', None):
            decisions = [] if outcome is None else [{'candidate_id': self.decision['candidate_id'],
                                                    'outcome': outcome, 'reason': '확인 근거가 부족하다.'}]
            result, report = apply_review(self.base, self.request, decisions, self.schema, self.material)
            self.assertEqual(result, self.base)
            self.assertEqual(report['decisions'][0]['status'], outcome or 'pending')

    def test_mismatched_or_tampered_request_rejected(self):
        for mutate in (lambda a: a.update(summary='변경된 요약이다.'),
                       lambda a: a['source'].update(material_id='0' * 64)):
            changed = copy.deepcopy(self.base)
            mutate(changed)
            with self.assertRaises(AnalysisError):
                apply_review(changed, self.request, [self.decision], self.schema, self.material)
        request = copy.deepcopy(self.request)
        request['candidates'][0]['text'] = '변조된 후보이다.'
        with self.assertRaises(AnalysisError):validate_request(self.base, request)

    def test_invalid_proposals_omitted(self):
        for candidates in ([self.candidate, self.candidate],
                           [dict(self.candidate, section_id='missing')],
                           [dict(self.candidate, verification_status='source_checked')],
                           [dict(self.candidate, text='첫 문장이다. 다음 문장이다.')]):
            result, audit = analyze(self.material, Stub(dict(self.base, review_candidates=candidates)), self.schema)
            self.assertEqual(result['status'], 'SUCCESS')
            self.assertEqual(result['analysis'], self.base)
            self.assertTrue(audit['auxiliary_review']['issues'])

    def test_invalid_decisions_blocked(self):
        for mutate in (lambda d: d.update(candidate_id='missing'),
                       lambda d: d['reference'].update(verification_status='unverified'),
                       lambda d: d['reference'].pop('checked_on'),
                       lambda d: d.update(reason=''),
                       lambda d: d['reference'].update(url='invalid')):
            decision = copy.deepcopy(self.decision)
            mutate(decision)
            with self.assertRaises(AnalysisError):
                apply_review(self.base, self.request, [decision], self.schema, self.material)
        with self.assertRaises(AnalysisError):
            apply_review(self.base, self.request, [self.decision] * 2, self.schema, self.material)

    def test_existing_comment_is_not_overwritten(self):
        result, _ = apply_review(self.base, self.request, [self.decision], self.schema, self.material)
        candidate = dict(self.candidate, text='다른 검토 코멘트이다.')
        request = make_request(result, [candidate])
        decision = dict(self.decision, candidate_id=request['candidates'][0]['id'])
        changed, report = apply_review(result, request, [decision], self.schema, self.material)
        self.assertEqual(changed, result)
        self.assertEqual(report['decisions'][0]['status'], 'conflict')

    def test_pending_request_survives_cache_reuse(self):
        response = dict(self.base, review_candidates=[self.candidate])
        with tempfile.TemporaryDirectory() as directory:
            first = Stub(response)
            result, audit = run_with_cache(self.material, first, self.schema, Path(directory)/'cache', directory)
            second = Stub(response)
            reused, cached = run_with_cache(self.material, second, self.schema,
                                            Path(directory)/'cache', directory, reuse_only=True)
            self.assertEqual(result, reused)
            self.assertEqual(audit['review_request'], cached['review_request'])
            self.assertEqual(second.called, 0)

    def test_recheck_preserves_pending_proposals(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/'analyzer_input.json').write_text(json.dumps(self.material), encoding='utf-8')
            (path/'raw_response.json').write_text(json.dumps(dict(self.base, review_candidates=[self.candidate])), encoding='utf-8')
            _, result, audit = recheck_run(path, self.schema)
            self.assertEqual(result['status'], 'SUCCESS')
            self.assertEqual(audit['review_request'], self.request)

    def test_cli_apply_creates_new_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for name, value in [('analysis', self.base), ('request', self.request), ('decisions', [self.decision])]:
                (path/(name+'.json')).write_text(json.dumps(value), encoding='utf-8')
            args = [sys.executable, '-m', 'analyzer.main', 'apply-review',
                    '--analysis', str(path/'analysis.json'), '--request', str(path/'request.json'),
                    '--decisions', str(path/'decisions.json'), '--source-file', str(ROOT/'test_file/18일차.txt'),
                    '--schema', str(ROOT/'output/study_material_analysis_schema_v0.2_draft.json'),
                    '--output-dir', str(path/'runs')]
            done = subprocess.run(args, cwd=ROOT/'study/study-system', capture_output=True)
            self.assertEqual(done.returncode, 0, done.stdout)
            output = next((path/'runs').iterdir())
            self.assertTrue((output/'analysis.json').exists())
            self.assertEqual(json.loads((path/'analysis.json').read_text(encoding='utf-8')), self.base)

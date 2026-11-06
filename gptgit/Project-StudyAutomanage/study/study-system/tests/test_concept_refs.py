import copy
import unittest

from analyzer.concept_refs import normalize_references, source_mentions
from analyzer.core import analyze, build_prompt
import test_knowledge
from test_knowledge import Stub


class ConceptReferenceTests(unittest.TestCase):
    def test_only_unique_whitespace_case_references_change(self):
        analysis = {'concepts': [{'name': 'MAC Table'}, {'name': 'VLAN'}],
                    'relationships': [{'from': ' mac\tTABLE ', 'to': 'v l a n', 'description': 'mac table'}],
                    'practice': [{'related_concepts': ['MACtable'], 'evidence': 'MACtable'}],
                    'source': {'filename': 'same.txt'}}
        before = copy.deepcopy(analysis)
        report = normalize_references(analysis, 'MACtable')
        self.assertEqual(len(report['normalizations']), 3)
        self.assertEqual(analysis['relationships'][0]['from'], 'MAC Table')
        self.assertEqual(analysis['relationships'][0]['to'], 'VLAN')
        self.assertEqual(analysis['practice'][0]['related_concepts'], ['MAC Table'])
        for field in ('concepts', 'source'):
            self.assertEqual(analysis[field], before[field])
        self.assertEqual(analysis['practice'][0]['evidence'], 'MACtable')
        self.assertEqual(analysis['relationships'][0]['description'], 'mac table')
        self.assertFalse(normalize_references(analysis, '')['normalizations'])

    def test_no_alias_fuzzy_punctuation_or_compatibility_repair(self):
        for reference in ('VLAN', 'VLAN-access-port', 'ＶＬＡＮ 액세스 포트', 'Virtual LAN'):
            analysis = {'concepts': [{'name': 'VLAN 액세스 포트'}],
                        'relationships': [{'from': 'VLAN 액세스 포트', 'to': reference}]}
            before = copy.deepcopy(analysis)
            report = normalize_references(analysis, 'VLAN DB에 VLAN 10을 설정한다.')
            self.assertEqual(analysis, before)
            self.assertEqual(report['status'], 'needs_review')
            self.assertEqual(report['items'][0]['reason'], 'missing_concept')
            if reference == 'VLAN':
                self.assertTrue(report['items'][0]['source_mentions'])
            else:
                self.assertEqual(report['items'][0]['source_mentions'], [])

    def test_ambiguous_match_is_left_for_review(self):
        analysis = {'concepts': [{'name': 'VLAN'}, {'name': 'v lan'}],
                    'practice': [{'related_concepts': ['vlan']}]}
        report = normalize_references(analysis, '')
        self.assertEqual(analysis['practice'][0]['related_concepts'], ['vlan'])
        self.assertEqual(report['items'][0]['reason'], 'ambiguous_spelling')

    def test_source_mentions_have_locations_and_do_not_match_substrings(self):
        text = 'VLAN만 있음\nVLAN DB 설정\npassword: VLAN\n'
        self.assertEqual(source_mentions('LAN', text), [])
        mentions = source_mentions('vlan', text)
        self.assertEqual(mentions[0]['start_line'], 2)
        self.assertEqual(mentions[0]['quote'], 'VLAN DB 설정')
        self.assertTrue(mentions[1]['redacted'])
        self.assertNotIn('VLAN', mentions[1]['quote'])
        self.assertEqual(source_mentions('없는개념', text), [])

    def fixture(self):
        fixture = test_knowledge.KnowledgeTests()
        fixture.setUp()
        analysis = copy.deepcopy(fixture.analysis)
        analysis.pop('references')
        for section in analysis['sections']:
            section.pop('comment', None)
        return fixture, analysis

    def test_pipeline_normalizes_before_section_link_repair(self):
        fixture, analysis = self.fixture()
        analysis['sections'][0]['content_refs'].remove('/relationships/0')
        original = analysis['relationships'][0]['to']
        analysis['relationships'][0]['to'] = ' ' + original.lower() + ' '
        provider = Stub(analysis)
        result, audit = analyze(fixture.data, provider, fixture.schema)
        self.assertEqual(result['status'], 'SUCCESS', result)
        self.assertEqual(provider.called, 1)
        self.assertEqual(result['analysis']['relationships'][0]['to'], original)
        self.assertIn('section_link_repairs', audit)
        self.assertEqual(len(audit['concept_reference_review']['normalizations']), 1)

    def test_missing_concept_stays_failed_without_retry_or_addition(self):
        fixture, analysis = self.fixture()
        analysis['relationships'][0]['to'] = '누락개념'
        before = copy.deepcopy(analysis)
        provider = Stub(analysis)
        result, audit = analyze(fixture.data, provider, fixture.schema)
        self.assertEqual(result['error']['code'], 'QUALITY_VALIDATION_ERROR')
        self.assertEqual(provider.called, 1)
        self.assertEqual(analysis, before)
        review = audit['concept_reference_review']
        self.assertEqual(review['status'], 'needs_review')
        self.assertEqual(review['concepts_added'], 0)
        self.assertFalse(review['automatic_api_retry'])
        self.assertEqual(review['items'][0]['path'], '/relationships/0/to')
        self.assertEqual(review['items'][0]['source_evidence_status'], 'not_found')
        self.assertFalse(audit['trace']['actual_ai_call'])

    def test_generation_prompt_requires_endpoint_self_check(self):
        fixture, _ = self.fixture()
        prompt = build_prompt(fixture.data, fixture.schema)[0]['content']
        self.assertIn('양쪽 대상 개념을 반드시', prompt)
        self.assertIn('출력 직전에', prompt)
        self.assertIn('임의 개념을 추가하지', prompt)

import copy
import unittest
import test_knowledge
from test_knowledge import Stub
from analyzer.core import analyze


class SectionLinkTests(unittest.TestCase):
    def setUp(self):
        fixture = test_knowledge.KnowledgeTests()
        fixture.setUp()
        self.schema, self.data = fixture.schema, fixture.data
        self.analysis = copy.deepcopy(fixture.analysis)
        for section in self.analysis['sections']:section.pop('comment', None)
        self.analysis.pop('references')
        # Relationship 0 is access port -> VLAN, both in the first section.
        self.analysis['sections'][0]['content_refs'].remove('/relationships/0')

    def test_unique_endpoint_section_is_repaired_without_content_changes(self):
        before = copy.deepcopy(self.analysis)
        result, audit = analyze(self.data, Stub(self.analysis), self.schema)
        self.assertEqual(result['status'], 'SUCCESS')
        fixed = result['analysis']
        for name in ('concepts', 'relationships', 'theory', 'practice', 'source'):
            self.assertEqual(fixed[name], before[name])
        self.assertIn('/relationships/0', fixed['sections'][0]['content_refs'])
        self.assertEqual(len(audit['section_link_repairs']), 1)
        self.assertEqual(self.analysis, before)

    def test_ambiguous_section_is_not_guessed(self):
        self.analysis['sections'][1]['content_refs'] += ['/concepts/0', '/concepts/1']
        result, audit = analyze(self.data, Stub(self.analysis), self.schema)
        self.assertEqual(result['error']['code'], 'QUALITY_VALIDATION_ERROR')
        self.assertIn('/relationships/0', result['error']['message'])
        self.assertNotIn('section_link_repairs', audit)

    def test_split_endpoints_are_not_guessed(self):
        self.analysis['sections'][0]['content_refs'].remove('/concepts/1')
        self.analysis['sections'][1]['content_refs'].append('/concepts/1')
        result, audit = analyze(self.data, Stub(self.analysis), self.schema)
        self.assertEqual(result['error']['code'], 'QUALITY_VALIDATION_ERROR')
        self.assertNotIn('section_link_repairs', audit)

    def test_missing_concept_link_is_not_repaired(self):
        self.analysis['sections'][0]['content_refs'].append('/relationships/0')
        self.analysis['sections'][0]['content_refs'].remove('/concepts/0')
        result, audit = analyze(self.data, Stub(self.analysis), self.schema)
        self.assertEqual(result['error']['code'], 'QUALITY_VALIDATION_ERROR')
        self.assertNotIn('section_link_repairs', audit)

    def test_repaired_result_does_not_need_repair_again(self):
        result, _ = analyze(self.data, Stub(self.analysis), self.schema)
        again, audit = analyze(self.data, Stub(result['analysis']), self.schema)
        self.assertEqual(again, result)
        self.assertNotIn('section_link_repairs', audit)

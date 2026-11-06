import copy
import unittest

from analyzer.classification import DEFAULT_POLICY
from analyzer.notion_reader import build_reader


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.analysis = {
            'source': {'filename': 'lesson.txt'}, 'summary': '원문 요약',
            'concepts': [{'name': '스패닝 트리', 'description': 'STP 설명'},
                         {'name': 'VTP', 'description': 'VTP 설명'}],
            'practice': [{'title': 'STP 설정', 'description': 'STP 예시', 'evidence': 'spanning-tree mode rapid-pvst'},
                         {'title': 'VTP 설정', 'description': 'VTP 예시', 'evidence': 'vtp password private-value'}],
            'sections': [{'title': 'STP', 'content_refs': ['/concepts/0', '/practice/0']},
                         {'title': 'VTP', 'content_refs': ['/concepts/1', '/practice/1']}]}
        paths = [['NETWORK', '2. 네트워크 접속', '스패닝 트리와 루프 방지'],
                 ['NETWORK', '2. 네트워크 접속', 'VTP와 PAgP']]
        record = {'id': 'm', 'analysis': self.analysis, 'classification': {'paths': paths}, 'locations': []}
        self.approved = {'materials': [record], 'concepts': [
            {'id': 'stp', 'name': '스패닝 트리', 'aliases': ['STP'],
             'sources': [{'material_id': 'm', 'filename': 'lesson.txt', 'description': 'STP 설명'}]},
            {'id': 'vtp', 'name': 'VTP', 'aliases': ['VTP'],
             'sources': [{'material_id': 'm', 'filename': 'lesson.txt', 'description': 'VTP 설명'}]}]}
        self.entities = {}
        for eid, kind, name in [('material:m', 'material', 'lesson.txt'),
                                ('concept:stp', 'concept', '스패닝 트리'), ('concept:vtp', 'concept', 'VTP'),
                                ('practice:stp', 'practice', 'STP 설정'), ('practice:vtp', 'practice', 'VTP 설정')]:
            self.entities[eid] = {'kind': kind, 'properties': {'name': name}, 'relations': {}}
        self.entities['material:m']['relations']['practice'] = ['practice:stp', 'practice:vtp']
        for suffix, path in zip(('stp', 'vtp'), paths):
            self.entities['category:'+suffix] = {'kind': 'category',
                'properties': {'name': path[-1], 'path': ' / '.join(path)}, 'relations': {'parent': []}}
        self.target = {'parent_page': {'id': 'home'}, 'reader': {'pages': {k: 'id-'+str(i) for i,k in enumerate(self.entities)}}}

    def build(self):
        return build_reader(self.entities, self.approved, DEFAULT_POLICY, self.target, {'m': 'material:m'})

    def test_practices_follow_explicit_sections_not_all_source_concepts(self):
        model = self.build()
        self.assertEqual(model['concept_practices']['concept:stp'], ['practice:stp'])
        self.assertEqual(model['practice_concepts']['practice:vtp'], ['concept:vtp'])
        self.assertEqual(model['concept_paths']['concept:stp'], ['NETWORK / 2. 네트워크 접속 / 스패닝 트리와 루프 방지'])
        self.assertNotIn('VTP 설정', model['bodies']['concept:stp'])

    def test_material_preserves_evidence_but_hides_developer_metadata(self):
        body = self.build()['bodies']['material:m']
        self.assertIn('## 핵심 정리', body)
        self.assertIn('<details>', body)
        self.assertIn('spanning-tree mode rapid-pvst', body)
        self.assertIn('[인증값 숨김]', body)
        self.assertNotIn('private-value', body)
        self.assertNotIn('Schema', body)

    def test_reader_does_not_modify_approved_analysis_or_classifications(self):
        original = copy.deepcopy(self.approved)
        self.build()
        self.assertEqual(self.approved, original)

    def test_unbound_page_is_readable_text_not_a_broken_link(self):
        self.target['reader']['pages'] = {}
        body = self.build()['bodies']['concept:stp']
        self.assertIn('lesson.txt', body)
        self.assertNotIn('notion.com/p/None', body)


if __name__ == '__main__':
    unittest.main()

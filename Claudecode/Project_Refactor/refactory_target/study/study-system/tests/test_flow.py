"""새 흐름(파일 분석 → CCNA 분류 → 게시 내용 → 게시 요청 → AI 코멘트) 확인. 유료 API·Notion은 호출하지 않는다."""
import json
import tempfile
import unittest
import urllib.request
import threading
from pathlib import Path

from analyzer import analysis, publish, records
from analyzer.app import Manager, make_server
from analyzer.ccna import unit_names
from analyzer.sources import file_hash, list_sources, read_text

SOURCE_TEXT = 'R1 설정\nconf t\nusername user pass 2222\nenable secret abc\n\nOSPF는 링크 상태 방식이다.\n'
CONFIG = {'home_title': 'Network 학습 자료', 'home_url': 'https://app.notion.com/p/home'}


def fake_response(**change):
    data = {
        'summary': 'R1 설정과 OSPF 설명.',
        'categories': ['3. IP 라우팅 / 단일 영역 OSPFv2'],
        'concepts': ['OSPF'],
        'sections': [{
            'title': 'OSPF 기초',
            'points': [{'subject': 'OSPF', 'content': '링크 상태 방식', 'evidence': {'start_line': 6, 'end_line': 6}}],
            'practice': [{'title': 'R1 설정', 'description': '계정 설정', 'evidence': {'start_line': 1, 'end_line': 4}}],
            'comment': {'kind': '보충', 'text': 'OSPF 비용 계산 기준을 함께 알아 두세요.'}}],
        'ccna_gaps': [{'category': '3. IP 라우팅 / 단일 영역 OSPFv2', 'text': 'DR/BDR 선출 설명이 없습니다.'}]}
    data.update(change)
    return json.dumps(data, ensure_ascii=False)


class FakeKeys:
    def __init__(self, key='sk-test-key-123456'):
        self.key = key

    def read(self):
        return self.key

    def save(self, key):
        self.key = key

    def delete(self):
        self.key = None


class Folder(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.source, self.data = root / 'sourcefile', root / 'data'
        self.source.mkdir()
        (self.source / 'a.txt').write_text(SOURCE_TEXT, encoding='utf-8')
        (self.source / 'b.txt').write_text('VLAN 메모', encoding='cp949')
        (self.source / 'ignore.pdf').write_bytes(b'x')

    def tearDown(self):
        self.temp.cleanup()

    def analyzed(self, filename='a.txt'):
        path = self.source / filename
        result = analysis.check(fake_response(), read_text(path))
        return records.save_result(self.data, filename, file_hash(path), 'gpt-6-luna', result)


class SourceTest(Folder):
    def test_lists_supported_files_and_reads_cp949(self):
        self.assertEqual([p.name for p in list_sources(self.source)], ['a.txt', 'b.txt'])
        self.assertEqual(read_text(self.source / 'b.txt'), 'VLAN 메모')


class AnalysisTest(unittest.TestCase):
    def test_evidence_lines_become_source_quotes(self):
        result = analysis.check(fake_response(), SOURCE_TEXT)
        section = result['sections'][0]
        self.assertEqual(section['points'][0]['evidence'], 'OSPF는 링크 상태 방식이다.')
        self.assertTrue(section['practice'][0]['evidence'].startswith('R1 설정\nconf t'))

    def test_rejects_bad_responses(self):
        bad = [fake_response(categories=[]), fake_response(categories=['없는 분류']), 'not json',
               fake_response(sections=[{'title': 'x', 'points': [], 'practice': [], 'comment': None}])]
        out_of_range = json.loads(fake_response())
        out_of_range['sections'][0]['points'][0]['evidence'] = {'start_line': 6, 'end_line': 99}
        blank = json.loads(fake_response())
        blank['sections'][0]['points'][0]['evidence'] = {'start_line': 5, 'end_line': 5}
        for raw in bad + [json.dumps(out_of_range), json.dumps(blank)]:
            with self.assertRaises(analysis.AnalysisError):
                analysis.check(raw, SOURCE_TEXT)

    def test_schema_meets_openai_strict_rules(self):
        def visit(node):
            if node.get('type') == 'object':
                self.assertFalse(node['additionalProperties'])
                self.assertEqual(set(node['required']), set(node['properties']))
            for child in node.get('properties', {}).values():
                visit(child)
            for child in node.get('anyOf', []):
                visit(child)
            if 'items' in node:
                visit(node['items'])
        visit(analysis.response_schema())

    def test_prompt_numbers_lines_and_lists_ccna_units(self):
        system, user = analysis.build_messages('a.txt', SOURCE_TEXT)
        self.assertIn('[L6] OSPF는 링크 상태 방식이다.', user['content'])
        for name in unit_names():
            self.assertIn(name, system['content'])


class RecordTest(Folder):
    def test_status_moves_from_new_to_published_to_changed(self):
        status = lambda: {r['filename']: r['status'] for r in records.statuses(self.source, self.data)}
        self.assertEqual(status()['a.txt'], 'new')
        self.analyzed()
        self.assertEqual(status()['a.txt'], 'analyzed')
        publish.build(self.source, self.data, CONFIG)
        records.write_json(self.data / 'publish' / 'result.json',
                           {'published_at': '2026-10-28T00:00:00Z', 'pages': {'a.txt': 'https://app.notion.com/p/a'}})
        self.assertEqual(status()['a.txt'], 'published')
        (self.source / 'a.txt').write_text(SOURCE_TEXT + '추가\n', encoding='utf-8')
        self.assertEqual(status()['a.txt'], 'changed')


class PublishTest(Folder):
    def test_package_contains_pages_prompt_and_masks_passwords(self):
        self.analyzed()
        result = publish.build(self.source, self.data, CONFIG)
        folder = Path(result['folder'])
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual([m['filename'] for m in manifest['materials']], ['a.txt'])
        page = (folder / manifest['materials'][0]['file']).read_text(encoding='utf-8')
        self.assertNotIn('2222', page)
        self.assertNotIn('abc', page)
        self.assertIn('AI 검토 의견 · 보충', page)
        self.assertIn('CCNA 기준 보완할 점', page)
        self.assertIn('{{page:학습자료}}', page)
        # Notion 마크다운: 접기는 <toggle>, 코드 블록은 들여쓰지 않는다.
        self.assertIn('<toggle>\nOSPF 기초\n\n', page)
        self.assertNotIn('\t', page)
        self.assertNotIn('<details>', page)
        # "3. IP 라우팅"이 글머리 안의 번호 목록으로 바뀌지 않게 점을 일반 글자로 쓴다.
        self.assertIn('- 3\\. IP 라우팅 / 단일 영역 OSPFv2', page)
        domain = (folder / 'pages' / 'domain_3.md').read_text(encoding='utf-8')
        self.assertIn('{{page:a.txt}}', domain)
        concepts = (folder / 'pages' / '개념 찾아보기.md').read_text(encoding='utf-8')
        self.assertEqual(concepts.count('**OSPF**'), 1)
        self.assertIn(str(folder), result['prompt'])
        self.assertTrue((folder / 'preview.html').is_file())

    def test_published_material_is_linked_not_republished(self):
        self.analyzed()
        records.write_json(self.data / 'published.json', {'a.txt': {
            'sha256': file_hash(self.source / 'a.txt'), 'url': 'https://app.notion.com/p/a', 'published_at': 'x'}})
        result = publish.build(self.source, self.data, CONFIG)
        self.assertEqual(result['materials'], [])
        listing = (Path(result['folder']) / 'pages' / '학습자료.md').read_text(encoding='utf-8')
        self.assertIn('<mention url="https://app.notion.com/p/a">a.txt</mention>', listing)

    def test_changed_source_is_left_out(self):
        self.analyzed()
        (self.source / 'a.txt').write_text('바뀐 내용', encoding='utf-8')
        with self.assertRaises(ValueError):
            publish.build(self.source, self.data, CONFIG)


class ManagerTest(Folder):
    def manager(self, analyze):
        config = Path(self.temp.name) / 'notion.json'
        config.write_text(json.dumps(CONFIG), encoding='utf-8')
        return Manager(self.source, self.data, config, keys=FakeKeys(), analyze=analyze)

    def test_analysis_job_saves_results_and_reports_failures(self):
        def analyze(filename, text, key, model):
            if filename == 'b.txt':
                raise analysis.AnalysisError('AI 응답 형식 오류')
            return analysis.check(fake_response(), text), {'total_tokens': 1}
        manager = self.manager(analyze)
        manager.job = {'status': 'running', 'total': 2, 'done': [], 'failed': []}
        manager.run_analysis(['a.txt', 'b.txt'], 'gpt-6-luna', 'key')
        self.assertEqual(manager.job['done'], ['a.txt'])
        self.assertEqual(manager.job['failed'][0]['filename'], 'b.txt')
        self.assertIsNotNone(records.load_result(self.data, 'a.txt'))

    def test_unexpected_error_does_not_leak_message(self):
        def analyze(*args):
            raise RuntimeError('secret sk-test-key-123456')
        manager = self.manager(analyze)
        manager.job = {'status': 'running', 'total': 1, 'done': [], 'failed': []}
        manager.run_analysis(['a.txt'], 'gpt-6-luna', 'key')
        self.assertNotIn('sk-test', manager.job['failed'][0]['error'])
        self.assertEqual(manager.job['status'], 'finished')

    def test_start_requires_known_files(self):
        manager = self.manager(lambda *a: None)
        with self.assertRaises(ValueError):
            manager.start_analysis(['없는파일.txt'], 'gpt-6-luna')

    def test_server_rejects_post_without_token(self):
        server = make_server(self.manager(lambda *a: None))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            base = f'http://127.0.0.1:{server.server_port}'
            with urllib.request.urlopen(base + '/api/status') as response:
                self.assertEqual(len(json.loads(response.read())['files']), 2)
            request = urllib.request.Request(base + '/api/prepare', data=b'{}', method='POST',
                                             headers={'Origin': base, 'Content-Type': 'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request)
            self.assertEqual(caught.exception.code, 403)
            caught.exception.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    unittest.main()

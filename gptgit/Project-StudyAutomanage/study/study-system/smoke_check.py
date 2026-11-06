"""Synthetic offline release check, including cache reuse and readable output."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path


def sample():
    text = 'vlan 10\nint fa0/1\nsw acc vlan 10'
    data = {'material_id': hashlib.sha256(text.encode()).hexdigest(), 'filename': 'offline_sample.txt',
            'extension': '.txt', 'extracted_text': text}
    analysis = {
        'schema_version': '0.2',
        'source': {k: data[k] for k in ('material_id', 'filename', 'extension')},
        'material_type': {'material_type': '실습', 'confidence': 1, 'reason': '설정 명령 예시'},
        'summary': 'VLAN 10과 액세스 포트 설정 예시다.',
        'topics': [{'name': 'NETWORK', 'children': [{'name': 'VLAN'}]}],
        'keywords': [{'name': 'VLAN'}],
        'concepts': [{'name': 'VLAN', 'description': '예시의 VLAN 번호는 10이다.'}],
        'practice': [{'title': 'VLAN 설정', 'description': 'VLAN 10을 만들고 Fa0/1에 VLAN 10을 지정하는 설정 예시다.',
                      'evidence': text, 'related_concepts': ['VLAN']}],
        'sections': [{'id': 'vlan', 'title': 'VLAN 설정', 'content_refs': ['/concepts/0', '/practice/0']}],
    }
    return data, analysis


class OfflineProvider:
    name = 'release-offline'

    def __init__(self, analysis):
        self.analysis, self.calls = analysis, 0

    def generate(self, messages):
        self.calls += 1
        return json.dumps(self.analysis, ensure_ascii=False)


def main():
    from analyzer.cache import run_with_cache
    from analyzer.core import load_schema
    from analyzer.render import render_markdown
    from analyzer.schemas import DEFAULT_SCHEMA
    schema = load_schema(DEFAULT_SCHEMA)
    data, analysis = sample()
    before = copy.deepcopy(analysis)
    provider = OfflineProvider(analysis)
    with tempfile.TemporaryDirectory() as directory:
        cache = Path(directory) / 'cache'
        first, audit = run_with_cache(data, provider, schema, cache, directory)
        assert first['status'] == 'SUCCESS', first
        second, reused = run_with_cache(data, provider, schema, cache, directory, reuse_only=True)
        assert first == second and provider.calls == 1
        assert reused['trace']['result_reused']
        text = render_markdown(first['analysis'])
        assert 'Fa0/1' in text and 'sw acc vlan 10' in text
        assert not audit['trace']['actual_ai_call']
        assert analysis == before
    print('PASS: v0.2 offline pipeline, cache reuse, readable result; API calls=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

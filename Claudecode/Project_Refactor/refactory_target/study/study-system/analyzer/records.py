"""분석 결과와 게시 기록. 자료는 파일명으로 구분하고, 내용 해시는 변경 감지에만 쓴다."""
import json
from datetime import datetime, timezone
from pathlib import Path

from .sources import file_hash, list_sources

STATUS_LABELS = {'new': '새 자료', 'changed': '내용 변경', 'analyzed': '게시 대기',
                 'published': '게시 완료'}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except FileNotFoundError:
        return default


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def result_path(data, filename):
    return Path(data) / 'results' / (filename + '.json')


def load_result(data, filename):
    return read_json(result_path(data, filename))


def save_result(data, filename, sha256, model, analysis, usage=None):
    record = {'filename': filename, 'sha256': sha256, 'analyzed_at': now(), 'model': model,
              'usage': usage, 'analysis': analysis}
    write_json(result_path(data, filename), record)
    return record


def all_results(data):
    folder = Path(data) / 'results'
    if not folder.is_dir():
        return []
    return [read_json(p) for p in sorted(folder.glob('*.json'), key=lambda p: p.name.lower())]


def published(data):
    return read_json(Path(data) / 'published.json', {})


def merge_publish_result(data):
    """채팅 AI가 남긴 게시 결과(publish/result.json)를 게시 기록에 합친다."""
    folder = Path(data) / 'publish'
    result, manifest = read_json(folder / 'result.json'), read_json(folder / 'manifest.json')
    if not result or not manifest:
        return published(data)
    record = published(data)
    hashes = {m['filename']: m['sha256'] for m in manifest['materials']}
    for filename, url in (result.get('pages') or {}).items():
        if filename in hashes and isinstance(url, str) and url.startswith('https://'):
            record[filename] = {'sha256': hashes[filename], 'url': url,
                                'published_at': result.get('published_at') or now()}
    write_json(Path(data) / 'published.json', record)
    return record


def statuses(source, data):
    done = merge_publish_result(data)
    rows = []
    for path in list_sources(source):
        sha256 = file_hash(path)
        result = load_result(data, path.name)
        if result is None:
            status = 'new'
        elif result['sha256'] != sha256:
            status = 'changed'
        elif done.get(path.name, {}).get('sha256') == sha256:
            status = 'published'
        else:
            status = 'analyzed'
        rows.append({'filename': path.name, 'sha256': sha256, 'status': status,
                     'label': STATUS_LABELS[status],
                     'summary': result['analysis']['summary'] if result else None,
                     'analyzed_at': result['analyzed_at'] if result else None,
                     'url': done.get(path.name, {}).get('url')})
    return rows

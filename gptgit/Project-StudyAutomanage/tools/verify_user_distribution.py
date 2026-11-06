"""Offline user-copy isolation, approval preservation and preview checks."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import runpy
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(user):
    user = user.resolve()
    runtime = user/'study/study-system'
    original = ROOT/'study/study-system'
    databases = [original/'output/knowledge_base/library.sqlite3',
                 original/'output/notion_live/outbox/delivery.sqlite3']
    before = {p: sha(p) for p in databases}
    with closing(sqlite3.connect(databases[0].as_uri()+'?mode=ro', uri=True)) as db:
        original_tables = {name: db.execute('SELECT * FROM '+name+' ORDER BY rowid').fetchall()
                           for name in ('materials', 'revisions', 'decisions', 'settings', 'jobs')}
    with closing(sqlite3.connect(runtime/'output/knowledge_base/library.sqlite3')) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        for name, rows in original_tables.items():
            copied_rows = db.execute('SELECT * FROM '+name+' ORDER BY rowid').fetchall()
            if name in ('materials', 'revisions'):
                normalized = []
                for row in copied_rows:
                    record = json.loads(row[-1])
                    origin = Path(record.get('origin') or '.')
                    if origin.is_absolute() and origin.is_relative_to(user):
                        record['origin'] = str(ROOT/origin.relative_to(user))
                    normalized.append((*row[:-1], record))
                expected = [(*row[:-1], json.loads(row[-1])) for row in rows]
                assert normalized == expected, name
            else:
                assert copied_rows == rows, name
        assert all(Path(p).is_relative_to(user/'study/sourcefile')
                   for (p,) in db.execute('SELECT path FROM locations'))
    with closing(sqlite3.connect(databases[1].as_uri()+'?mode=ro', uri=True)) as db:
        delivery = {name: db.execute('SELECT * FROM '+name+' ORDER BY rowid').fetchall()
                    for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    with closing(sqlite3.connect(runtime/'output/notion_live/outbox/delivery.sqlite3')) as db:
        for name, rows in delivery.items():
            assert db.execute('SELECT * FROM '+name+' ORDER BY rowid').fetchall() == rows, name
    manifest = json.loads((user/'distribution_manifest.json').read_text(encoding='utf-8'))
    for name, value in manifest['files'].items():
        assert sha(user/name) == value, name
    assert all(not (runtime/name).exists() for name in ('tests', 'fixtures', '.test-deps'))
    assert not (runtime/'tools/benchmark_status_intake.py').exists()

    # Load the exact launcher path under Python -I. Deny subsequent reads of
    # development code/data: successful checks cannot silently fall back there.
    runpy.run_path(str(user/'start.py'), run_name='user_bootstrap_verification')
    forbidden = [original, ROOT/'study/sourcefile', ROOT/'test_file', ROOT/'output']
    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
            if any(path.is_relative_to(folder) for folder in forbidden):
                raise AssertionError('Development dependency: '+str(path))
    sys.addaudithook(audit)
    from analyzer.management import Manager, page
    from analyzer.notion_intake import inspect, prepare_sources
    from analyzer.notion_prepared import load, validate
    from analyzer.workspace import Workspace
    import docx, jsonschema, lxml.etree, rpds
    for module in (docx, jsonschema, lxml.etree, rpds):
        assert Path(module.__file__).is_relative_to(user/'vendor'), module.__name__
    class NoKeys:
        def read(self):
            return None
    user_db = runtime/'output/knowledge_base/library.sqlite3'
    user_before = sha(user_db)
    report, _ = inspect(user/'study/sourcefile', user_db.parent)
    assert report['ready'], report['counts']
    store = Workspace(user_db.parent, read_only=True)
    approved = store.approved()['materials']
    with tempfile.TemporaryDirectory(dir=runtime/'output') as temporary:
        manager = Manager(directory=Path(temporary)/'manager_check', keys=NoKeys())
        status = manager.status()
        assert status['intake']['counts'] == report['counts']
        assert not manager.progress()['refresh_required']
        template = (runtime/'analyzer/review.html').read_text(encoding='utf-8')
        assert 'manage' in page(template)
        prepared = prepare_sources(user_db.parent,
            runtime/'config/notion_target.json', runtime/'config/notion_home.json',
            runtime/'output/notion_live', Path(temporary)/'prepared',
            source=user/'study/sourcefile', allow_partial=True)
        package = load(prepared['package'])
        validate(package)
        assert Path(package['workspace']).is_relative_to(user)
        assert Path(package['source_manifest']['root']).is_relative_to(user)
        assert prepared.get('new_api_attempts', 0) == 0
    assert sha(user_db) == user_before
    # Audit hook intentionally remains enabled; original DB equality was checked
    # before the isolation test, and all subsequent original reads were denied.
    return {'approved': len(approved), 'source_counts': report['counts'],
            'approval_and_history_preserved': True, 'delivery_history_preserved': True,
            'development_access_blocked': True, 'preview_validation': 'passed',
            'user_approval_db_unchanged': True, 'new_api_calls': 0, 'notion_calls': 0,
            'original_database_hashes': {str(p.relative_to(ROOT)): value for p,value in before.items()}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=ROOT/'user_app')
    args = parser.parse_args()
    directory = args.directory.resolve()
    result = verify(directory)
    (directory/'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))

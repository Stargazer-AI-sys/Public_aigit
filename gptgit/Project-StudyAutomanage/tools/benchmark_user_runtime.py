"""Read-only runtime review metrics; no credentials, paid API or Notion calls."""
import argparse
import copy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
USER = ROOT/'user_app'
RUNTIME = USER/'study/study-system'
sys.path[:0] = [str(USER/'vendor'), str(RUNTIME)]
sys.dont_write_bytecode = True


def main():
    from analyzer import workspace, classification
    from analyzer.notion_intake import inspect
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    db = RUNTIME/'output/knowledge_base/library.sqlite3'
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    store = workspace.Workspace(db.parent, read_only=True)
    result = {}
    for name, operation in [('inspect', lambda: inspect(USER/'study/sourcefile', db.parent)[0]),
                            ('catalog', store.catalog), ('approved', store.approved)]:
        samples = []
        for _ in range(3):
            counters = {'sqlite_connections': 0, 'policy_evaluations': 0, 'knowledge_indexes': 0}
            connect = workspace.sqlite3.connect
            effect = workspace.Workspace.policy_effect
            index = workspace.knowledge_index
            def connection(*a, **k):
                counters['sqlite_connections'] += 1
                return connect(*a, **k)
            def policy(*a, **k):
                counters['policy_evaluations'] += 1
                return effect(*a, **k)
            def knowledge(*a, **k):
                counters['knowledge_indexes'] += 1
                return index(*a, **k)
            with patch.object(workspace.sqlite3, 'connect', connection), \
                 patch.object(workspace.Workspace, 'policy_effect', staticmethod(policy)), \
                 patch.object(workspace, 'knowledge_index', knowledge):
                start = time.perf_counter()
                value = operation()
                samples.append({'seconds': time.perf_counter()-start, **counters})
        result[name] = {'median_seconds': statistics.median(s['seconds'] for s in samples),
                        'samples': samples, 'result_sha256': classification.digest(value)}
    base = store.list()[0]
    materials = []
    for n in range(600):
        record = copy.deepcopy(base)
        record['id'] = str(n)
        record['analysis']['source']['material_id'] = str(n)
        record['analysis']['concepts'] = [{'name': 'isolated_'+str(n), 'description': 'sample'}]
        materials.append(record)
    start = time.perf_counter()
    value = classification.knowledge_index(materials, store.policy())
    result['sparse_relations_600'] = {'seconds': time.perf_counter()-start,
        'result_sha256': classification.digest(value), 'relations': sum(len(v) for v in value['related'].values())}
    result['approval_db_unchanged'] = hashlib.sha256(db.read_bytes()).hexdigest() == before
    result['paid_api_calls'] = result['notion_calls'] = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: ({'seconds': v.get('median_seconds', v.get('seconds')),
                          'counts': v.get('samples', [{}])[0]} if isinstance(v, dict) else v)
                      for k,v in result.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""Read-only source/library benchmark. No real keys, AI or Notion calls."""
import argparse
from collections import Counter
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyzer.management import Manager
from analyzer.notion_intake import DEFAULT_SOURCE, inspect
from analyzer.organizer import DEFAULT_WORKSPACE
import analyzer.notion_intake as intake
import collector.main as collector
from analyzer.workspace import Workspace


class NoKeys:
    def read(self):
        return None


def measure(work, repeats):
    samples = []
    for _ in range(repeats):
        counts = Counter()
        def counted(name, function):
            def wrapped(*args, **kwargs):
                counts[name] += 1
                return function(*args, **kwargs)
            return wrapped
        with ExitStack() as stack:
            for obj, attr, label in [(collector, 'calculate_sha256', 'source_hashes'),
                                     (intake, 'calculate_sha256', 'source_hashes'),
                                     (collector, 'extract_text', 'extractions'),
                                     (Path, 'rglob', 'directory_walks'),
                                     (Workspace, 'reusable', 'library_validations'),
                                     (NoKeys, 'read', 'key_reads')]:
                stack.enter_context(patch.object(obj, attr, counted(label, getattr(obj, attr))))
            started = time.perf_counter()
            work()
            elapsed = time.perf_counter() - started
        samples.append({'seconds': round(elapsed, 6), **{k: counts[k] for k in
            ('source_hashes', 'extractions', 'directory_walks', 'library_validations', 'key_reads')}})
    return {'median_seconds': statistics.median(s['seconds'] for s in samples), 'samples': samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error('repeats must be 1..10')
    database = DEFAULT_WORKSPACE/'library.sqlite3'
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    # Keep manager files separate from the live UI and publication state.
    with tempfile.TemporaryDirectory(dir=ROOT/'output/test_tmp') as directory:
        manager = Manager(directory=Path(directory), keys=NoKeys())
        full = measure(manager.status, args.repeats)
        poll = measure(getattr(manager, 'progress', manager.status), args.repeats)
        scan = measure(lambda: inspect(DEFAULT_SOURCE, DEFAULT_WORKSPACE), args.repeats)
    after = hashlib.sha256(database.read_bytes()).hexdigest()
    result = {'source': str(DEFAULT_SOURCE), 'library_unchanged': before == after,
              'full_status': full, 'periodic_poll': poll, 'source_inspection': scan,
              'paid_api_calls': 0, 'notion_calls': 0}
    if before != after:
        raise RuntimeError('Library changed during the read-only benchmark')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""Offline readback audit; reuses publication parsing/property rules.

Input files must contain compact tool response wrappers, in any page order.
This script never fetches or writes Notion and opens the delivery ledger read-only.
Stored snapshots establish saved-state consistency, not current remote freshness.
Run from study-system: python tools/notion_bridge/verify.py --help
"""
import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analyzer.cache import digest
from analyzer.notion_mcp import NotionMCP, content_for, page_id, unpack
from analyzer.notion_sync import DeliveryError


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def body_normalized(value):
    """Normalize only observed native formatting, retaining meaningful code spaces."""
    value = re.sub(r'<mention-page url="([^"]+)"[^>]*>[^<]*</mention-page>',
                   r'<mention-page url="\1"/>', value)
    value = re.sub(r'https://app\.notion\.com/p/([a-f0-9-]+)',
                   lambda m: 'https://app.notion.com/p/'+m[1].replace('-', ''), value)
    # Nested Notion code content is returned unindented; opening/closing fences
    # retain the block indentation. Preserve indentation within the code itself.
    def code(match):
        indent, fence, _, body = match.groups()
        body = '\n'.join(line[len(indent):] if indent and line.startswith(indent) else line
                         for line in body.splitlines())
        return indent+fence+'text\n'+body+'\n'+indent+fence
    value = re.sub(r'^(\t*)(`{3,})(text|plain text)\n([\s\S]*?)\n\1\2(?=\n|$)',
                   code, value, flags=re.M)
    return '\n'.join(line.rstrip() for line in value.splitlines() if line.strip())


def responses(path):
    data = load(path)
    if isinstance(data, dict):
        data = data.get('results', [data['result']] if 'result' in data else None)
    if not isinstance(data, list):
        raise ValueError('invalid response envelope')
    return [unpack(item) for item in data]


def audit(target_path, outbox, readback, front_readback=None, entity_keys=None):
    target = load(target_path)
    ledger = Path(outbox)/'delivery.sqlite3'
    with closing(sqlite3.connect(ledger.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        destination = db.execute('SELECT id FROM destination').fetchone()
        expected = 'notion-mcp:'+digest({k: v['data_source_id'] for k, v in target['collections'].items()})
        if not destination or destination[0] != expected:
            raise DeliveryError('PUBLISH_DESTINATION_MISMATCH')
        receipts = {key: json.loads(raw) for key, raw in db.execute('SELECT entity_key,record FROM receipts')}
        states = dict(db.execute('SELECT state,count(*) FROM operations GROUP BY state'))
    expected_keys = set(receipts) if entity_keys is None else set(entity_keys)
    if not expected_keys or not expected_keys <= receipts.keys():
        raise DeliveryError('INVALID_AUDIT_SCOPE')
    # Reuse readback and mapping rules without constructing a writable Outbox.
    remote = NotionMCP.__new__(NotionMCP)
    remote.target = target
    rows = responses(readback)
    fronts = responses(front_readback) if front_readback else []
    keys, errors = [], []
    for data in rows:
        raw = remote.parse_page(data['id'], data)
        candidates = [(kind, binding, raw['properties'].get(binding['property_mapping']['sync_key']))
                      for kind, binding in target['collections'].items()]
        found = [(kind, binding, key) for kind, binding, key in candidates
                 if isinstance(key, str) and key.startswith(kind+':')]
        if len(found) != 1:
            errors.append({'id': raw['id'], 'code': 'UNKNOWN_SYNC_KEY'})
            continue
        kind, binding, key = found[0]
        keys.append(key)
        if entity_keys is not None and key not in expected_keys:
            errors.append({'key': key, 'code': 'UNEXPECTED_READBACK'})
        receipt = receipts.get(key)
        if not receipt:
            errors.append({'key': key, 'code': 'MISSING_RECEIPT'})
            continue
        doc = receipt['document']
        checks = {'ID': page_id(receipt['id']) == raw['id'],
                  'PROPERTIES': remote.properties_match(raw, doc),
                  'DIGEST': raw['properties'].get(binding['system_properties']['digest']) == digest(doc),
                  'OPERATION': raw['properties'].get(binding['system_properties']['operation']) == receipt['operation_id'],
                  'BODY': body_normalized(raw['body']) == body_normalized(content_for(doc))}
        if receipt.get('confirmation') != 'write-response':
            checks['STAMP'] = receipt['stamp'] == raw['stamp']
        errors.extend({'key': key, 'code': name+'_MISMATCH'} for name, ok in checks.items() if not ok)
    errors.extend({'key': key, 'code': 'DUPLICATE_SYNC_KEY'}
                  for key, count in Counter(keys).items() if count > 1)
    errors.extend({'key': key, 'code': 'MISSING_READBACK'} for key in expected_keys-set(keys))
    known = {page_id(r['id']) for r in receipts.values()} | {page_id(row['id']) for row in fronts}
    unknown = set()
    for data in rows+fronts:
        body = re.search(r'<content>\n?([\s\S]*?)\n?</content>', data.get('text', ''))
        if not body:
            if data in fronts:
                errors.append({'id': data['id'], 'code': 'MISSING_FRONT_CONTENT'})
            continue
        for pid in re.findall(r'https://app\.notion\.com/p/([a-f0-9-]+)', body[1]):
            if page_id(pid) not in known:
                unknown.add(pid)
    pending = sum(count for state, count in states.items() if state != 'success')
    locks = [name for name in ('delivery.lock',) if (Path(outbox)/name).exists()]
    return {'mode': 'offline-snapshot-audit', 'remote_freshness_checked': False,
            'scope': 'selected' if entity_keys is not None else 'all',
            'expected_entities': len(expected_keys),
            'entities': len(rows), 'unique_sync_keys': len(set(keys)),
            'stored_receipts': len(receipts),
            'receipt_confirmations': dict(Counter(receipts[k].get('confirmation', 'readback') for k in expected_keys)),
            'physical_stamp_checked_entities': sum(receipts[k].get('confirmation') != 'write-response'
                                                   for k in set(keys) & receipts.keys()),
            'kinds': dict(Counter(key.split(':')[0] for key in keys)), 'errors': errors,
            'pending_operations': pending, 'lock_files': locks, 'operations': states,
            'front_pages': len(fronts),
            'front_database_blocks': sum('<database ' in row.get('text', '') for row in fronts),
            'unknown_internal_link_targets': sorted(unknown),
            'front_layout_compared': False,
            'ok': not errors and not unknown and not pending and not locks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, default=ROOT/'config/notion_target.json')
    parser.add_argument('--outbox', type=Path, default=ROOT/'output/notion_live/outbox')
    parser.add_argument('--readback', type=Path, required=True)
    parser.add_argument('--front-readback', type=Path)
    parser.add_argument('--entity-key', action='append', help='검증할 관리 키; 미지정 시 전체 영수증 검증')
    parser.add_argument('--report', type=Path, help='Optional local result path; no output written unless supplied')
    args = parser.parse_args()
    try:
        result = audit(args.target, args.outbox, args.readback, args.front_readback, args.entity_key)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error, DeliveryError) as error:
        result = {'ok': False, 'mode': 'offline-snapshot-audit',
                  'errors': [{'code': getattr(error, 'code', 'INVALID_AUDIT_INPUT')}]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    # Summaries contain codes/IDs only, never a full response, source body or token.
    print(json.dumps(result, ensure_ascii=False))
    return int(not result['ok'])


if __name__ == '__main__':
    raise SystemExit(main())

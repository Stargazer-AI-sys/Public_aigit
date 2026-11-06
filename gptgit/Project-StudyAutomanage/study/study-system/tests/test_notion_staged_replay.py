"""Offline replay of the saved five-to-six-material routing publication.

Only temporary outboxes and fake Notion pages are written. The real approval DB
is opened read-only. No API client, credentials, approval changes or live tools.
"""
import copy
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from analyzer.cache import digest
from analyzer.classification import knowledge_index
from analyzer.notion_front import refresh
from analyzer.notion_mcp import content_for
from analyzer.notion_publisher import NotionPublisher, publish_staged
from analyzer.notion_sync import make_plan
from analyzer.workspace import Workspace
import test_notion_publisher as fixtures


class ReplayPlugin(fixtures.PublicationPlugin):
    def touch(self, pid):
        self.clock += 1
        binding = next(b for b in self.target['collections'].values()
                       if b['data_source_id'] == self.pages[pid]['source'])
        self.pages[pid]['properties'][binding['revision_property']] = f'2026-10-19T00:00:00.{self.clock:06d}Z'


class SavedPublicationReplayTests(unittest.TestCase):
    def test_saved_routing_publication_has_one_final_write_set(self):
        project = Path(__file__).resolve().parents[1]
        live = project/'output/notion_live'
        baseline = live/'runs/20261019T041500Z_630720e3a988/plan.json'
        published = live/'runs/20261019T052500Z_09ae147b0bb6/plan.json'
        if not baseline.is_file() or not published.is_file():
            self.skipTest('saved routing publication unavailable')
        old = json.loads(baseline.read_text(encoding='utf-8'))
        actual = json.loads(published.read_text(encoding='utf-8'))
        target = copy.deepcopy(old['mapping']['target'])
        store = Workspace(project/'output/knowledge_base', read_only=True)
        before = store.path.read_bytes()
        approved, policy = store.approved(), store.policy()
        selected = actual['approvals']
        if {r['id']: r['snapshot'] for r in approved['materials'] if r['id'] in selected} != selected:
            self.skipTest('saved routing approvals have since changed')
        approved['materials'] = [r for r in approved['materials'] if r['id'] in selected]
        approved.update(knowledge_index(approved['materials'], policy))
        # Frozen read-only approval snapshot avoids disk reads on every mock
        # guard; this benchmark compares requests, never runtime or billing.
        class Snapshot:
            path = store.path
            def approved(self):
                return copy.deepcopy(approved)
            def policy(self):
                return copy.deepcopy(policy)
        frozen = Snapshot()
        with tempfile.TemporaryDirectory() as folder:
            remote_pages = target['reader']['pages']
            plugin = ReplayPlugin(target)
            remote = NotionPublisher(target, folder, plugin)
            for entity in old['entities']:
                eid, kind = entity['key'], entity['kind']
                document = {'kind': kind, 'properties': entity['properties'], 'body': entity['body'],
                            'relations': {name: [remote_pages[k] for k in keys]
                                          for name, keys in entity['relations'].items()}}
                pid = remote_pages[eid].replace('-', '')
                binding = target['collections'][kind]
                props = remote.projected_properties(document)
                props[binding['system_properties']['digest']] = digest(document)
                props[binding['system_properties']['operation']] = 'baseline-'+eid
                plugin.pages[pid] = {'source': binding['data_source_id'], 'properties': props,
                                     'body': content_for(document)}
                plugin.touch(pid)
                raw = remote.parse_page(pid, plugin('fetch', {'id': pid}))
                remote.outbox.save('receipts', eid, {'id': pid, 'document': document,
                    'stamp': raw['stamp'], 'operation_id': props[binding['system_properties']['operation']],
                    'remote_revision': raw['remote_revision']})
            remote.metrics['body_read_pages'] = 0
            plugin.details.clear()
            plan = make_plan(frozen, target=target, material_ids=list(selected))
            final, target, remote, report = publish_staged(plan, frozen, remote, folder,
                                                          target=target, material_ids=list(selected))
            self.assertFalse(report['errors'])
            expected_entities = copy.deepcopy(actual['entities'])
            for entity in expected_entities:
                for eid, old_pid in actual['mapping']['target']['reader']['pages'].items():
                    entity['body'] = entity['body'].replace(old_pid.replace('-', ''),
                                                           target['reader']['pages'][eid].replace('-', ''))
            self.assertEqual(final['entities'], expected_entities)
            # Existing generated navigation baseline and final saved bodies are
            # already present in the two plans; use their reader UI models.
            from analyzer.notion_reader import build_front_pages
            home = json.loads((project/'config/notion_home.json').read_text(encoding='utf-8'))
            old_approved = copy.deepcopy(approved)
            old_approved['materials'] = [r for r in old_approved['materials'] if r['id'] in old['approvals']]
            old_approved.update(knowledge_index(old_approved['materials'], policy))
            old_front = build_front_pages(old, old_approved, policy, old['mapping']['target'], home)
            new_front = build_front_pages(final, approved, policy, target, home)
            state = {}
            for page in old_front:
                pid = page['page_id'].replace('-', '')
                state[pid] = {'expected_body': page['body'], 'observed_body': page['body']}
                plugin.pages[pid] = {'source': 'navigation', 'properties': {}, 'body': page['body']}
            # Front writes need no revision property and no inventory queries.
            original_touch = plugin.touch
            plugin.touch = lambda pid: original_touch(pid) if plugin.pages[pid]['source'] != 'navigation' else None
            fronts = refresh(new_front, state, remote, lambda _: None)
            self.assertFalse(fronts['errors'])
            calls = Counter()
            writes = Counter()
            for tool, args in plugin.details:
                label = tool + (':'+args['command'] if tool == 'notion_update_page' else '')
                calls[label] += 1
                if tool == 'notion_update_page':
                    writes[(args['page_id'], args['command'])] += 1
            self.assertTrue(all(count == 1 for count in writes.values()))
            self.assertEqual(calls, {'query_data_sources': 4, 'notion_create_pages': 3,
                                     'notion_update_page:replace_content': 25,
                                     'notion_update_page:update_properties': 23})
            self.assertEqual(report['initial_pass']['transport_metrics']['exchanges']
                             + report['transport_metrics']['exchanges'], 5)
            self.assertNotIn('fetch', calls)
            self.assertEqual(fronts['writes'], 5)
            self.assertEqual(store.path.read_bytes(), before)
            print('STAGED_REPLAY '+json.dumps({'mode': 'offline saved-case replay',
                'old_actual_calls': 87, 'new_mock_calls': sum(calls.values()), 'new_commands': dict(calls),
                'old_actual_bridge_exchanges': 17, 'new_mock_bridge_exchanges': 5,
                'normal_body_reads': 0, 'duplicate_body_or_property_writes': 0,
                'approval_db_unchanged': True, 'actual_notion_calls': 0, 'paid_ai_calls': 0}))

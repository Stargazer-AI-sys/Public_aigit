"""Explicit partial classification acknowledgement, never implicit approval."""
import copy
import io
import json
import re
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from analyzer.core import AnalysisError
from analyzer.review_server import make_server
from test_organizer import OrganizerTests


class ScopeReviewTests(unittest.TestCase):
    setUp = OrganizerTests.setUp

    def partial(self):
        analysis = copy.deepcopy(self.analysis)
        analysis['topics'].append({'name': '미분류 보조 메모'})
        return self.store.ingest(analysis, self.data)

    def test_partial_requires_ack_and_preserves_body_and_unmatched_topic(self):
        record = self.partial()
        self.assertFalse(record['classification']['scope_confirmed'])
        with self.assertRaises(AnalysisError):
            self.store.decide(record['id'], record['snapshot'], 'approve')
        held = self.store.decide(record['id'], record['snapshot'], 'hold')
        result = self.store.decide(record['id'], held['snapshot'], 'approve', confirm_partial_scope=True)
        self.assertEqual(result['analysis'], record['analysis'])
        self.assertEqual(result['classification']['unclassified_topics'], [['미분류 보조 메모']])
        self.assertTrue(result['classification']['partial_scope_confirmed_by_user'])
        self.assertFalse(any('관련성 미확인' in p for p in result['classification']['paths']))
        self.assertEqual(len(self.store.approved()['materials']), 1)

    def test_no_known_category_remains_blocked(self):
        policy = copy.deepcopy(self.store.policy())
        for domain in policy['curriculum']['domains']:
            for unit in domain['units']:
                unit['terms'] = ['NO_MATCH_TEST']
        self.store.set_policy(policy)
        record = self.partial()
        with self.assertRaises(AnalysisError):
            self.store.decide(record['id'], record['snapshot'], 'approve', confirm_partial_scope=True)
        self.assertEqual(self.store.approved()['materials'], [])

    def test_publication_hold_cannot_be_bypassed(self):
        policy = copy.deepcopy(self.store.policy())
        policy['publication_holds'][self.data['filename']] = '검토 필요'
        self.store.set_policy(policy)
        record = self.partial()
        with self.assertRaises(AnalysisError):
            self.store.decide(record['id'], record['snapshot'], 'approve', confirm_partial_scope=True)

    def test_stale_ack_does_not_change_newer_decision(self):
        record = self.partial()
        held = self.store.decide(record['id'], record['snapshot'], 'hold')
        with self.assertRaises(AnalysisError) as error:
            self.store.decide(record['id'], record['snapshot'], 'approve', confirm_partial_scope=True)
        self.assertEqual(error.exception.code, 'REVIEW_STALE')
        self.assertEqual(self.store.get(record['id'])['snapshot'], held['snapshot'])

    def test_http_ack_is_explicit_and_boolean(self):
        record = self.partial()
        with patch('analyzer.review_server.ThreadingHTTPServer') as factory:
            make_server(self.store, 0)
        handler = object.__new__(factory.call_args.args[1])
        handler.server = SimpleNamespace(server_port=8765)
        handler.headers = {'Host': '127.0.0.1:8765'}
        handler.path = '/'
        replies = []
        handler.reply = lambda status, body, *args: replies.append((status, body))
        handler.do_GET()
        token = re.search(r"const token='([^']+)'", replies[-1][1].decode())[1]
        handler.path = '/api/decide'
        handler.headers.update({'Origin': 'http://127.0.0.1:8765', 'X-Review-Token': token})
        def post(extra):
            body = json.dumps({'id': record['id'], 'snapshot': record['snapshot'], 'action': 'approve', **extra}).encode()
            handler.headers['Content-Length'] = str(len(body))
            handler.rfile = io.BytesIO(body)
            handler.do_POST()
            return replies[-1][0]
        self.assertEqual(post({}), 400)
        self.assertEqual(post({'confirm_partial_scope': 'true'}), 400)
        self.assertEqual(post({'confirm_partial_scope': True}), 200)
        self.assertEqual(len(self.store.approved()['materials']), 1)


if __name__ == '__main__':
    unittest.main()

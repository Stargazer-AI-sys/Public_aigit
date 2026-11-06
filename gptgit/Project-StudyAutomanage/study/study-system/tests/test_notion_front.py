import copy
import unittest

from analyzer.notion_front import normalized_body, refresh


class Remote:
    def __init__(self, bodies):
        self.bodies = dict(bodies)
        self.requests = []

    def calls(self, requests):
        self.requests.extend(requests)
        result = []
        for request in requests:
            args = request['args']
            if request['tool'] == 'fetch':
                result.append({'id': args['id'], 'body': self.bodies[args['id']]})
            else:
                self.bodies[args['page_id']] = args['new_str']
                result.append({'success': True})
        return result

    def parse_page(self, pid, result):
        return result


class FrontTests(unittest.TestCase):
    def test_guarded_local_front_preserves_manual_edit_and_repeat_skips_reads(self):
        a, b = 'a'*32, 'b'*32
        state = {pid: {'expected_body': 'old', 'observed_body': 'old'} for pid in (a, b)}
        remote = Remote({a: 'manual', b: 'old'})
        remote.local_source = True
        pages = [{'page_id': a, 'body': 'new'}, {'page_id': b, 'body': 'old'}]
        report = refresh(pages, state, remote, lambda _: None, guard_changes=True)
        self.assertEqual((report['reads'], report['writes'], report['unchanged']), (1, 0, 1))
        self.assertEqual(report['errors'][0]['code'], 'FRONT_REMOTE_CONFLICT')
        self.assertEqual(remote.bodies[a], 'manual')
        remote.bodies[a] = 'old'
        saved = []
        report = refresh(pages, state, remote, lambda s: saved.append(copy.deepcopy(s)), guard_changes=True)
        self.assertEqual((report['reads'], report['writes']), (1, 1))
        count = len(remote.requests)
        again = refresh(pages, saved[-1], remote, lambda _: None, guard_changes=True)
        self.assertEqual((again['reads'], again['writes'], again['unchanged']), (0, 0, 2))
        self.assertEqual(len(remote.requests), count)

    def test_local_source_groups_independent_fronts_and_persists_all_intents(self):
        ids = ['a'*32, 'b'*32, 'c'*32]
        remote = Remote({pid: 'old' for pid in ids})
        remote.local_source = True
        groups, saved = [], []
        original = remote.calls
        def calls(requests):
            groups.append(len(requests))
            self.assertTrue(all(saved[-1][pid].get('pending_body') == 'new' for pid in ids))
            return original(requests)
        remote.calls = calls
        report = refresh([{'page_id': pid, 'body': 'new'} for pid in ids],
                         {pid: {'expected_body': 'old', 'observed_body': 'old'} for pid in ids}, remote,
                         lambda state: saved.append(copy.deepcopy(state)))
        self.assertEqual(groups, [3])
        self.assertEqual((report['reads'], report['writes']), (0, 3))
        self.assertTrue(all('pending_body' not in saved[-1][pid] for pid in ids))

    def test_local_source_writes_without_body_read_and_repeat_has_no_calls(self):
        pid = 'a'*32
        remote = Remote({pid: 'old'})
        remote.local_source = True
        saved = []
        report = refresh([{'page_id': pid, 'body': 'new'}],
                         {pid: {'expected_body': 'old', 'observed_body': 'old'}},
                         remote, lambda s: saved.append(copy.deepcopy(s)))
        self.assertEqual((report['reads'], report['writes']), (0, 1))
        self.assertEqual(report['verified_page_ids'], [])
        self.assertEqual(report['acknowledged_page_ids'], [pid])
        self.assertEqual(saved[-1][pid]['confirmation'], 'write-response')
        count = len(remote.requests)
        again = refresh([{'page_id': pid, 'body': 'new'}], saved[-1], remote, lambda _: None)
        self.assertEqual(again['unchanged'], 1)
        self.assertEqual(len(remote.requests), count)

    def test_local_source_recovers_lost_response_only_for_pending_page(self):
        pid = 'a'*32
        remote = Remote({pid: 'new'})
        remote.local_source = True
        state = {pid: {'expected_body': 'old', 'observed_body': 'old', 'pending_body': 'new'}}
        report = refresh([{'page_id': pid, 'body': 'new'}], state, remote, lambda _: None)
        self.assertEqual((report['reads'], report['writes'], report['recovered']), (1, 0, 1))

    def test_local_source_does_not_replay_uncertain_or_manually_edited_front(self):
        pid = 'a'*32
        for current in ('old', 'manual'):
            remote = Remote({pid: current})
            remote.local_source = True
            state = {pid: {'expected_body': 'old', 'observed_body': 'old', 'pending_body': 'new'}}
            report = refresh([{'page_id': pid, 'body': 'new'}], state, remote, lambda _: None)
            self.assertEqual(report['writes'], 0)
            self.assertEqual(report['errors'][0]['code'], 'FRONT_UNRESOLVED_WRITE')

    def test_local_source_saves_intent_before_lost_response_and_recovers(self):
        from analyzer.notion_sync import DeliveryError
        pid = 'a'*32
        remote = Remote({pid: 'old'})
        remote.local_source = True
        original = remote.calls
        saved = []
        def lose(requests):
            original(requests)
            raise DeliveryError('RESPONSE_LOST')
        remote.calls = lose
        with self.assertRaises(DeliveryError):
            refresh([{'page_id': pid, 'body': 'new'}],
                    {pid: {'expected_body': 'old', 'observed_body': 'old'}},
                    remote, lambda s: saved.append(copy.deepcopy(s)))
        self.assertEqual(saved[-1][pid]['pending_body'], 'new')
        remote.calls = original
        report = refresh([{'page_id': pid, 'body': 'new'}], saved[-1], remote, lambda _: None)
        self.assertEqual((report['reads'], report['writes'], report['recovered']), (1, 0, 1))

    def test_local_source_retries_only_after_confirming_old_front(self):
        pid = 'a'*32
        remote = Remote({pid: 'old'})
        remote.local_source = True
        remote.retry_requested = True
        saved = []
        state = {pid: {'expected_body': 'old', 'observed_body': 'old', 'pending_body': 'new'}}
        report = refresh([{'page_id': pid, 'body': 'new'}], state, remote,
                         lambda s: saved.append(copy.deepcopy(s)))
        self.assertEqual((report['reads'], report['writes']), (1, 1))
        self.assertNotIn('pending_body', saved[-1][pid])

    def test_changed_page_only_and_repeat_has_no_calls(self):
        a, b = 'a'*32, 'b'*32
        state = {pid: {'expected_body': 'old', 'observed_body': 'old'} for pid in (a,b)}
        remote = Remote({a:'old', b:'old'})
        saved = []
        report = refresh([{'page_id':a,'body':'new'}, {'page_id':b,'body':'old'}],
                         state, remote, lambda value: saved.append(copy.deepcopy(value)))
        self.assertEqual((report['reads'], report['writes'], report['unchanged']), (2,1,1))
        self.assertEqual(remote.bodies[b], 'old')
        calls = len(remote.requests)
        again = refresh([{'page_id':a,'body':'new'}, {'page_id':b,'body':'old'}],
                        saved[-1], remote, lambda _: self.fail('unexpected checkpoint'))
        self.assertEqual(again['unchanged'], 2)
        self.assertEqual(len(remote.requests), calls)

    def test_manual_edit_blocks_replacement(self):
        pid = 'a'*32
        remote = Remote({pid:'사용자 수정'})
        state = {pid:{'expected_body':'old','observed_body':'old'}}
        report = refresh([{'page_id':pid,'body':'new'}], state, remote, lambda _:None)
        self.assertEqual(report['writes'], 0)
        self.assertEqual(report['errors'][0]['code'], 'FRONT_REMOTE_CONFLICT')
        self.assertEqual(remote.bodies[pid], '사용자 수정')

    def test_interrupted_success_is_recovered_without_rewrite(self):
        pid = 'a'*32
        remote = Remote({pid:'new'})
        state = {pid:{'expected_body':'old','observed_body':'old'}}
        saved = []
        report = refresh([{'page_id':pid,'body':'new'}], state, remote, saved.append)
        self.assertEqual((report['recovered'], report['reads'], report['writes']), (1,1,0))
        self.assertEqual(saved[-1][pid]['expected_body'], 'new')

    def test_native_table_formatting_only_is_ignored(self):
        a = '<table header-row="true" fit-page-width="true">\n\t<tr><td>자료</td></tr>\n</table>'
        b = '<table fit-page-width="true" header-row="true">\n<tr>\n<td>자료</td>\n</tr>\n</table>'
        self.assertEqual(normalized_body(a), normalized_body(b))
        self.assertNotEqual(normalized_body(a), normalized_body(b.replace('자료','수정')))

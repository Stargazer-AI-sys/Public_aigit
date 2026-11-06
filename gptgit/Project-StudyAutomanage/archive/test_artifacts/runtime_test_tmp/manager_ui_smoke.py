import json
from pathlib import Path
import analyzer.management as management
from analyzer.management import Manager
from analyzer.review_server import make_server
from analyzer.notion_intake import analyze as intake_analyze
from analyzer.notion_prepared import publish as real_publish
from test_management import ManagerTests, FakeKeys
import test_notion_prepared as fixtures
case = ManagerTests('test_prepare_preview_send_to_mock_preserves_approvals')
case.setUp()
responses = case.add('화면 확인용 신규.txt')
intake_analyze(case.source, case.store.root, case.root, responses=responses)
bad_responses = case.add('오류 안내 테스트.txt')
(case.root/'response.json').write_text('invalid JSON',encoding='utf-8')
def offline_analyze(source, workspace, directory, **kwargs):
    return intake_analyze(source, workspace, directory, filenames=kwargs['filenames'], responses=bad_responses,
                          retry_failed=kwargs.get('retry_failed',False))
management.analyze = offline_analyze
management.publish = lambda package, **kw: real_publish(package,
    call=lambda *a: fixtures.PreparedTests.call(case,*a),
    call_many=lambda rs: [fixtures.PreparedTests.call(case,r['tool'],r['args']) for r in rs])
manager = Manager(case.store.root, case.source, case.root, case.target_file, case.home_file, keys=FakeKeys())
server = make_server(case.store, 0, manager=manager)
Path('output/test_tmp/manager_ui_endpoint.json').write_text(json.dumps({'port': server.server_port}), encoding='utf-8')
print('UI_PREVIEW http://127.0.0.1:'+str(server.server_port), flush=True)
try: server.serve_forever()
finally: server.server_close(); case.doCleanups()

import json
from pathlib import Path
from analyzer.management import Manager
from analyzer.review_server import make_server
from analyzer.notion_intake import analyze
import collector.main as collector
from test_management import ManagerTests,FakeKeys
case=ManagerTests('test_prepare_preview_send_to_mock_preserves_approvals');case.setUp()
responses=case.add('화면 시험.txt');analyze(case.source,case.store.root,case.root,responses=responses)
counters={'full_status':0,'progress':0,'extractions':0}
original_extract=collector.extract_text
counter_file=Path('output/test_tmp/status_ui_counters.json')
def extract(*args,**kwargs):
 counters['extractions']+=1
 return original_extract(*args,**kwargs)
collector.extract_text=extract
class Observed(Manager):
 def status(self):
  result=super().status();counters['full_status']+=1;counter_file.write_text(json.dumps(counters),encoding='utf-8');return result
 def progress(self):
  result=super().progress();counters['progress']+=1;counter_file.write_text(json.dumps(counters),encoding='utf-8');return result
manager=Observed(case.store.root,case.source,case.root,case.target_file,case.home_file,keys=FakeKeys())
server=make_server(case.store,0,manager=manager)
Path('output/test_tmp/status_ui_endpoint.json').write_text(json.dumps({'port':server.server_port,'source':str(case.source)}),encoding='utf-8')
print('STATUS_UI http://127.0.0.1:'+str(server.server_port),flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close();case.doCleanups()

import threading
from test_scope_review import ScopeReviewTests
from analyzer.review_server import make_server
case=ScopeReviewTests('test_partial_requires_ack_and_preserves_body_and_unmatched_topic')
case.setUp();case.partial()
server=make_server(case.store,0)
timer=threading.Timer(240,server.shutdown);timer.daemon=True;timer.start()
print('SCOPE_UI http://127.0.0.1:'+str(server.server_port),flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:timer.cancel();server.server_close();case.doCleanups()

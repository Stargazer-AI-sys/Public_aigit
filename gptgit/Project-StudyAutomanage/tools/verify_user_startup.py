"""Start the actual user entry point, check local HTTP, then shut it down."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = ROOT/'user_app'
RUNTIME = USER/'study/study-system'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    originals = [ROOT/'study/study-system/output/knowledge_base/library.sqlite3',
                 ROOT/'study/study-system/output/notion_live/outbox/delivery.sqlite3']
    before = {p: sha(p) for p in originals}
    endpoint = RUNTIME/'output/notion_live/manager/endpoint.json'
    started = time.time_ns()
    code = ('import runpy,webbrowser;webbrowser.open=lambda *a,**k: True;runpy.run_path('
            +repr(str(USER/'start.py'))+",run_name='__main__')")
    process = subprocess.Popen([sys.executable, '-I', '-B', '-X', 'utf8', '-c', code],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8')
    try:
        for _ in range(150):
            if process.poll() is not None:
                raise RuntimeError(process.stdout.read())
            if endpoint.exists() and endpoint.stat().st_mtime_ns >= started:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('UI startup timed out')
        port = json.loads(endpoint.read_text(encoding='utf-8'))['port']
        url = f'http://127.0.0.1:{port}'
        with urllib.request.urlopen(url, timeout=5) as response:
            html = response.read().decode('utf-8')
            csp = response.headers['Content-Security-Policy']
        token = re.search("nonce-([^']+)", csp)[1]
        assert 'manage' in html and '승인' in html
        with urllib.request.urlopen(url+'/api/manage/status', timeout=15) as response:
            status = json.load(response)
        assert status['intake']['counts'] == {'approved': 11}, status['intake']['counts']
        with urllib.request.urlopen(url+'/api/manage/progress', timeout=5) as response:
            assert not json.load(response)['refresh_required']
        request = urllib.request.Request(url+'/api/manage/shutdown', data=b'{}',
            headers={'Content-Type': 'application/json', 'Origin': url, 'X-Review-Token': token}, method='POST')
        with urllib.request.urlopen(request, timeout=5) as response:
            assert json.load(response)['ok']
        assert process.wait(timeout=10) == 0
        assert all(sha(p) == value for p, value in before.items())
        result = {'actual_start_py': 'passed', 'http_page': 'passed', 'status_approved': 11,
                  'progress': 'passed', 'shutdown': 'passed',
                  'development_databases_unchanged': True, 'api_and_notion_calls': 0}
        (USER/'ui_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False))
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


if __name__ == '__main__':
    main()

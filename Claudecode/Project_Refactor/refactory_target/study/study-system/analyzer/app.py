"""로컬 관리 화면: 자료 목록 → 분석 → 미리보기·게시 요청문 만들기."""
import json
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import analysis, publish, records
from .sources import file_hash, read_text

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'sourcefile'
DATA = ROOT / 'data'
CONFIG = ROOT / 'config' / 'notion.json'


class Manager:
    def __init__(self, source=SOURCE, data=DATA, config=CONFIG, keys=None, analyze=analysis.analyze):
        self.source, self.data, self.config = Path(source), Path(data), Path(config)
        if keys is None:
            from .credentials import KeyStore
            keys = KeyStore()
        self.keys, self.analyze = keys, analyze
        self.lock = threading.Lock()
        self.job = {'status': 'idle'}

    def key_saved(self):
        try:
            return bool(self.keys.read())
        except OSError:
            return False

    def status(self):
        with self.lock:
            job = dict(self.job)
        return {'files': records.statuses(self.source, self.data), 'key_saved': self.key_saved(),
                'models': list(analysis.MODELS), 'job': job}

    def start_analysis(self, filenames, model):
        names = {p['filename'] for p in records.statuses(self.source, self.data)}
        if not filenames or not isinstance(filenames, list) or not set(filenames) <= names:
            raise ValueError('분석할 자료를 목록에서 선택하세요.')
        if model not in analysis.MODELS:
            raise ValueError('모델을 선택하세요.')
        api_key = self.keys.read()
        if not api_key:
            raise ValueError('설정에서 API 키를 먼저 등록하세요.')
        with self.lock:
            if self.job['status'] == 'running':
                raise ValueError('분석이 진행 중입니다. 끝난 뒤 다시 실행하세요.')
            self.job = {'status': 'running', 'total': len(filenames), 'done': [], 'failed': []}
        threading.Thread(target=self.run_analysis, args=(filenames, model, api_key), daemon=True).start()

    def run_analysis(self, filenames, model, api_key):
        for filename in filenames:
            path = self.source / filename
            try:
                sha256, text = file_hash(path), read_text(path)
                result, usage = self.analyze(filename, text, api_key, model)
                records.save_result(self.data, filename, sha256, model, result, usage)
                outcome = ('done', filename)
            except Exception as error:
                # 예상한 오류만 내용을 보여 준다. 다른 오류 문자열에는 키 같은 값이 섞일 수 있다.
                message = (str(error) if isinstance(error, (analysis.AnalysisError, ValueError))
                           else '파일을 읽거나 저장하지 못했습니다.' if isinstance(error, OSError)
                           else '분석 중 예상하지 못한 오류가 났습니다.')
                outcome = ('failed', {'filename': filename, 'error': publish.redact(message)})
            with self.lock:
                self.job[outcome[0]].append(outcome[1])
        with self.lock:
            self.job['status'] = 'finished'

    def prepare(self):
        with self.lock:
            if self.job['status'] == 'running':
                raise ValueError('분석이 끝난 뒤 게시 준비를 하세요.')
        config = json.loads(self.config.read_text(encoding='utf-8'))
        return publish.build(self.source, self.data, config)


def make_server(manager, port=0):
    token = secrets.token_urlsafe(32)
    page = (Path(__file__).with_name('app.html').read_text(encoding='utf-8')
            .replace('__TOKEN__', token).encode('utf-8'))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, body, kind='application/json; charset=utf-8'):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy',
                             f"default-src 'self'; script-src 'nonce-{token}'; style-src 'unsafe-inline'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def local(self):
            # 다른 웹사이트가 이 화면에 요청을 보내지 못하게 주소를 확인한다.
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            if not self.local():
                return self.reply(403, {'error': '로컬 주소로 접속하세요.'})
            path = urlparse(self.path).path
            try:
                if path == '/':
                    return self.reply(200, page, 'text/html; charset=utf-8')
                if path == '/api/status':
                    return self.reply(200, manager.status())
                if path == '/preview':
                    preview = manager.data / 'publish' / 'preview.html'
                    if not preview.is_file():
                        return self.reply(404, {'error': '미리보기를 먼저 만드세요.'})
                    return self.reply(200, preview.read_bytes(), 'text/html; charset=utf-8')
                return self.reply(404, {'error': '찾을 수 없습니다.'})
            except (OSError, ValueError):
                return self.reply(500, {'error': '자료를 읽지 못했습니다. 원본 폴더를 확인하세요.'})

        def do_POST(self):
            if (not self.local() or self.headers.get('X-Token') != token
                    or self.headers.get('Origin') != f'http://127.0.0.1:{self.server.server_port}'):
                return self.reply(403, {'error': '화면을 새로 고친 뒤 다시 시도하세요.'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 100000:
                    raise ValueError('요청 크기를 확인하세요.')
                data = json.loads(self.rfile.read(size).decode('utf-8'))
                action = urlparse(self.path).path
                if action == '/api/analyze':
                    manager.start_analysis(data.get('filenames'), data.get('model'))
                    return self.reply(200, {'started': True})
                if action == '/api/prepare':
                    return self.reply(200, manager.prepare())
                if action == '/api/key':
                    manager.keys.save(data.get('key'))
                    return self.reply(200, {'ok': True})
                if action == '/api/delete-key':
                    manager.keys.delete()
                    return self.reply(200, {'ok': True})
                if action == '/api/shutdown':
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return self.reply(200, {'ok': True})
                return self.reply(404, {'error': '찾을 수 없습니다.'})
            except ValueError as error:
                return self.reply(400, {'error': str(error)})
            except OSError:
                return self.reply(500, {'error': '저장하거나 읽지 못했습니다. 폴더와 권한을 확인하세요.'})

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    import msvcrt
    app_dir = DATA / 'app'
    app_dir.mkdir(parents=True, exist_ok=True)
    lock = (app_dir / 'instance.lock').open('a+b')
    if not lock.tell():
        lock.write(b'0')
        lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock.close()
        endpoint = records.read_json(app_dir / 'endpoint.json', {})
        if isinstance(endpoint.get('port'), int):
            webbrowser.open(f"http://127.0.0.1:{endpoint['port']}")
        print('이미 실행 중입니다. 열려 있는 화면을 사용하세요.', flush=True)
        return
    manager = Manager()
    server = make_server(manager)
    records.write_json(app_dir / 'endpoint.json', {'port': server.server_port})
    url = f'http://127.0.0.1:{server.server_port}'
    print('학습자료 관리: ' + url + '\n종료는 화면의 [프로그램 종료] 버튼을 누르세요.', flush=True)
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        lock.close()

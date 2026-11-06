"""Loopback-only review UI. No API generation or Notion writes from this server."""
import json
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .core import AnalysisError
from .render import redact
from .notion_sync import DeliveryError


def warnings_for(record):
    """Diagnostics are advisory only after canonical ingest has succeeded."""
    origin = Path(record.get('origin') or '.')
    messages = []
    for name in ('trace', 'auxiliary_review'):
        try:
            value = json.loads((origin/(name+'.json')).read_text(encoding='utf-8'))
            if name == 'trace':
                messages.extend(value.get('warnings', []))
            else:
                messages.extend('보조 항목 제외: '+json.dumps(issue, ensure_ascii=False)
                                for issue in value.get('issues', []))
        except (OSError, ValueError, TypeError):
            pass
    return [redact(str(value)) for value in messages]


def public(value):
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [public(v) for v in value]
    if isinstance(value, dict):
        return {k: public(v) for k, v in value.items() if k not in ('origin', 'locations')}
    return value


def make_server(store, port=0, *, manager=None):
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError('포트 범위를 확인하세요.')
    token = secrets.token_urlsafe(32)
    template = Path(__file__).with_name('review.html').read_text(encoding='utf-8')
    if manager is not None:
        from .management import page as management_page
        template = management_page(template)
    page = template.replace('__TOKEN__', token).encode('utf-8')

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def valid_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def reply(self, status, body, kind='application/json; charset=utf-8'):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            ancestors = "'self'" if manager is not None else "'none'"
            self.send_header('Content-Security-Policy', f"default-src 'self'; script-src 'nonce-{token}'; style-src 'unsafe-inline'; frame-ancestors {ancestors}; base-uri 'none'")
            self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            if not self.valid_host():
                return self.reply(403, {'error': '로컬 주소로 접속하세요.'})
            path = urlparse(self.path).path
            try:
                if path == '/':
                    return self.reply(200, page, 'text/html; charset=utf-8')
                if manager is not None and path.startswith('/api/manage/'):
                    result = manager.get(path)
                    return self.reply(200, public(result) if not isinstance(result, bytes) else result,
                                      'text/html; charset=utf-8' if isinstance(result, bytes) else 'application/json; charset=utf-8')
                if path == '/api/catalog':
                    catalog = store.catalog()
                    # Keep the list compact; full bodies are fetched only on selection.
                    return self.reply(200, public({'materials': [{k: r[k] for k in ('id', 'classification', 'status', 'holds', 'snapshot', 'revision')}
                                | {'filename': r['analysis']['source']['filename'], 'summary': r['analysis']['summary']} for r in catalog['materials']],
                              'categories': catalog['categories'], 'concepts': catalog['concepts'], 'related': catalog['related'],
                              'curriculum': catalog['curriculum']}))
                if path.startswith('/api/material/'):
                    mid = path.rsplit('/', 1)[-1]
                    record = store.get(mid)
                    history = store.history(mid)
                    previous = history[-2] if len(history) > 1 else None
                    return self.reply(200, public({'record': record, 'previous': previous,
                                                  'warnings': warnings_for(record)}))
                return self.reply(404, {'error': '찾을 수 없습니다.'})
            except AnalysisError as error:
                return self.reply(400, {'error': str(error), 'code': error.code})
            except DeliveryError as error:
                return self.reply(409, {'error': '게시안이 변경됐거나 유효하지 않습니다. 미리보기를 다시 생성하세요.', 'code': error.code})
            except (OSError, ValueError, sqlite3.Error):
                return self.reply(500, {'error': '자료를 읽지 못했습니다. 저장소 상태를 확인하세요.'})

        def do_POST(self):
            expected_origin = f'http://127.0.0.1:{self.server.server_port}'
            if (not self.valid_host() or self.headers.get('Origin') != expected_origin
                    or self.headers.get('X-Review-Token') != token):
                return self.reply(403, {'error': '검토 요청을 확인할 수 없습니다. 화면을 새로 여세요.'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 1000000:
                    return self.reply(413, {'error': '요청 크기를 확인하세요.'})
                from .core import strict_json
                data = strict_json(self.rfile.read(size).decode('utf-8'))
                if not isinstance(data, dict):
                    raise ValueError('객체 요청이 필요합니다.')
                if manager is not None and self.path.startswith('/api/manage/'):
                    return self.reply(200, public(manager.post(self.path, data, self.server)))
                if manager is not None and manager.mutex.locked():
                    return self.reply(409, {'error': '작업 완료 후 승인·보류를 진행하세요.'})
                if self.path == '/api/decide':
                    if data.get('action') not in ('approve', 'hold') or set(data) - {'id', 'snapshot', 'action', 'note', 'confirm_partial_scope'}:
                        raise ValueError('이 단계에서는 승인·보류만 가능합니다.')
                    if type(data.get('confirm_partial_scope', False)) is not bool:
                        raise ValueError('분류 확인 값은 참/거짓이어야 합니다.')
                    record = store.decide(data['id'], data['snapshot'], data['action'], note=data.get('note', ''),
                                          confirm_partial_scope=data.get('confirm_partial_scope', False))
                    return self.reply(200, {'status': record['status'], 'snapshot': record['snapshot']})
                if self.path == '/api/export':
                    from .organizer import export_approved
                    path, count = export_approved(store)
                    return self.reply(200, {'count': count, 'path': str(path), 'notion_sent': False})
                return self.reply(404, {'error': '찾을 수 없습니다.'})
            except AnalysisError as error:
                return self.reply(409 if error.code == 'REVIEW_STALE' else 400, {'error': str(error), 'code': error.code})
            except DeliveryError as error:
                return self.reply(409, {'error': '게시안이 변경됐거나 유효하지 않습니다. 미리보기를 다시 생성하세요.', 'code': error.code})
            except (ValueError, UnicodeError, KeyError, TypeError):
                return self.reply(400, {'error': '요청 내용을 확인하세요.'})
            except (OSError, sqlite3.Error):
                return self.reply(500, {'error': '저장에 실패했습니다. 다시 확인하세요.'})

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def serve(store, port=8765):
    server = make_server(store, port)
    print(f'분류·지식베이스 검토: http://127.0.0.1:{server.server_port}\n종료: Ctrl+C / API 호출·Notion 전송 없음', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

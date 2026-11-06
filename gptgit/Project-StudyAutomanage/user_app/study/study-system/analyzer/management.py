"""Local UI orchestration; analysis is explicit, approval stays in review_server."""
import copy
import json
import threading
import webbrowser
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from collector.scanner import scan_all_files

from .core import AnalysisError
from .notion_intake import DEFAULT_SOURCE, inspect, analyze, prepare_sources
from .notion_prepared import load, validate, publish
from .organizer import DEFAULT_WORKSPACE
from .render import redact
from .workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]


class Manager:
    def __init__(self, workspace=DEFAULT_WORKSPACE, source=DEFAULT_SOURCE, directory=None,
                 target=None, home=None, keys=None):
        self.workspace, self.source = Path(workspace), Path(source)
        self.directory = Path(directory or ROOT/'output/notion_live')
        self.target = Path(target or ROOT/'config/notion_target.json')
        self.home = Path(home or ROOT/'config/notion_home.json')
        self.ui = self.directory/'manager'
        self.ui.mkdir(parents=True, exist_ok=True)
        if keys is None:
            from .credentials import KeyStore
            keys = KeyStore()
        self.keys = keys
        self.lock, self.mutex = threading.RLock(), threading.Lock()
        self.settings = {'max_new_calls': 1}
        try:
            saved = load(self.ui/'settings.json')
            self.check_limit(saved['max_new_calls'])
            self.settings['max_new_calls'] = saved['max_new_calls']
        except (OSError, ValueError, KeyError, TypeError):
            pass
        try:
            self.state = load(self.ui/'state.json')
        except (OSError, ValueError):
            self.state = {'status': 'idle', 'operation': None, 'result': None}
        if self.state.get('status') == 'running':
            self.state.update(status='interrupted', error='이전 실행이 중단됐습니다. 자동 재실행하지 않습니다. 기록을 확인하세요.')
        self.worker = None
        self._inspection_stamp = None

    def observation_stamp(self):
        """Change hint only. Publication/analysis guards still hash real bytes."""
        def metadata(path):
            try:
                value = path.stat()
                return (str(path), value.st_size, value.st_mtime_ns, value.st_ctime_ns,
                        value.st_ino, value.st_dev)
            except OSError as error:
                return (str(path), type(error).__name__)
        try:
            sources = tuple(metadata(path) for path in scan_all_files(self.source))
        except OSError as error:
            sources = (type(error).__name__,)
        database = self.workspace/'library.sqlite3'
        library = tuple(metadata(Path(str(database)+suffix)) for suffix in ('', '-wal', '-journal'))
        return (sources, library)

    def progress(self):
        stamp = self.observation_stamp()
        with self.lock:
            return {'job': copy.deepcopy(self.state), 'busy': self.mutex.locked(),
                    'refresh_required': self._inspection_stamp is None or stamp != self._inspection_stamp}

    @staticmethod
    def check_limit(value):
        if type(value) is not int or not 1 <= value <= 100:
            raise ValueError('새 API 호출 한도는 1~100회입니다.')

    def save_json(self, name, value):
        path = self.ui/name
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(path)

    def status(self):
        # Capture BEFORE reading: edits during inspection trigger another scan.
        stamp = self.observation_stamp()
        report, _ = inspect(self.source, self.workspace)
        # Include diagnostics even after restart; never return raw provider errors/keys.
        diagnostics = []
        store = Workspace(self.workspace, read_only=True)
        from .review_server import warnings_for
        for record in store.list():
            for warning in warnings_for(record):
                diagnostics.append({'filename': record['analysis']['source']['filename'], 'warning': warning})
        try:
            last_analysis = load(self.ui/'last_analysis.json')
        except (OSError, ValueError):
            last_analysis = None
        try:
            key_saved, key_error = bool(self.keys.read()), None
        except OSError:
            key_saved, key_error = False, 'Windows 자격 증명 관리자에 접근하지 못했습니다. 일반 Windows 사용자 세션에서 실행하세요.'
        with self.lock:
            self._inspection_stamp = stamp
            return {'intake': report, 'job': copy.deepcopy(self.state),
                    'settings': dict(self.settings), 'key_saved': key_saved, 'key_error': key_error,
                    'diagnostics': diagnostics, 'last_analysis': last_analysis, 'busy': self.mutex.locked(),
                    'intake_checked_at': datetime.now(timezone.utc).isoformat()}

    def start(self, operation, data):
        if operation not in ('analyze', 'prepare', 'send'):
            raise ValueError('알 수 없는 작업입니다.')
        if not self.mutex.acquire(blocking=False):
            raise AnalysisError('MANAGER_BUSY', '작업이 진행 중입니다. 완료 후 실행하세요.')
        try:
            if operation == 'analyze':
                filenames = data.get('filenames')
                if not isinstance(filenames, list) or not filenames or any(not isinstance(v, str) for v in filenames):
                    raise ValueError('분석할 신규·변경 자료를 선택하세요.')
                self.check_limit(data.get('max_new_calls'))
                if data.get('allow_api') is not True:
                    raise ValueError('선택 자료의 유료 분석 허용을 확인하세요.')
                if not self.keys.read():
                    raise ValueError('설정에서 API 키를 먼저 등록하세요.')
            with self.lock:
                if operation == 'send':
                    if data.get('confirmed') is not True:
                        raise ValueError('미리보기 확인 후 게시 준비를 누르세요.')
                    prepared = self.state.get('prepared')
                    if not prepared:
                        raise ValueError('게시 미리보기를 먼저 생성하세요.')
                    validate(load(prepared['package']))
                prepared = self.state.get('prepared') if operation == 'send' else None
                self.state = {'operation': operation, 'status': 'running', 'result': None, 'job_id': uuid4().hex,
                              'prepared': prepared}
                if operation == 'send':
                    bridge = self.directory/'bridge'
                    self.state['relay'] = ('다음 게시 전송을 현재 Notion 연결 도구로 중계해줘. '
                        '저장된 tools/notion_bridge/run_dispatch.js를 재사용하고 완료까지 진행해줘.\n'
                        f'전달 폴더: {bridge.resolve()}\n게시 패키지: {prepared["package"]}')
                self.save_json('state.json', self.state)
            self.worker = threading.Thread(target=self.run, args=(operation, copy.deepcopy(data)), daemon=True)
            self.worker.start()
        except Exception:
            self.mutex.release()
            raise
        with self.lock:
            return {'started': True, 'relay': self.state.get('relay') if operation == 'send' else None}

    def run(self, operation, data):
        try:
            if operation == 'analyze':
                result = analyze(self.source, self.workspace, self.directory,
                    filenames=data['filenames'], allow_api=True, max_new_calls=data['max_new_calls'],
                    api_key=self.keys.read(), retry_failed=data.get('retry_failed') is True,
                    recover_interrupted=data.get('recover_interrupted') is True)
                # All persisted errors are existing redacted analyzer diagnostics.
                batch = result.get('analysis') or {}
                outcome = 'partial' if (batch.get('failed') or batch.get('blocked') or result.get('analysis_not_run')) else 'complete'
                self.save_json('last_analysis.json', result)
            elif operation == 'prepare':
                result = prepare_sources(self.workspace, self.target, self.home, self.directory,
                    self.directory/'prepared', self.source, allow_partial=True)
                if not result.get('package'):
                    raise ValueError('게시 가능한 승인 자료가 없습니다. 승인 대기 탭을 확인하세요.')
                try:
                    last = load(self.ui/'last_analysis.json')
                    problems = {i['filename']: i.get('error', {}).get('code') or i.get('reason')
                                for i in (last.get('analysis') or {}).get('items', [])
                                if i.get('error') or i.get('reason')}
                    for skipped in result.get('skipped', []):
                        if skipped['filename'] in problems:
                            skipped['reason'] = problems[skipped['filename']]
                except (OSError, ValueError):
                    pass
                outcome = 'complete'
                with self.lock:
                    self.state['prepared'] = result
            else:
                from . import notion_mcp
                package = self.state['prepared']['package']
                notion_mcp.BRIDGE_DIRECTORY = self.directory/'bridge'
                notion_mcp.BRIDGE_PACKAGE = package
                result = publish(package, call=notion_mcp.rpc, call_many=notion_mcp.rpc_many,
                    retry=data.get('retry_failed') is True,
                    recover_interrupted=data.get('recover_interrupted') is True)
                outcome = 'complete' if not result['errors'] and result['front_completion'] == 'complete' else 'partial'
            with self.lock:
                self.state.update(status=outcome, result=result)
        except Exception as error:
            # Do not echo unexpected exception strings: they can contain credentials.
            code = getattr(error, 'code', 'MANAGER_OPERATION_ERROR')
            message = str(error) if isinstance(error, (AnalysisError, ValueError)) else '작업을 완료하지 못했습니다. 저장 기록과 실행 환경을 확인하세요.'
            with self.lock:
                self.state.update(status='failed', error=redact(message), code=code)
        finally:
            try:
                with self.lock:
                    self.save_json('state.json', self.state)
            finally:
                self.mutex.release()

    def get(self, path):
        if path == '/api/manage/progress':
            return self.progress()
        if path == '/api/manage/status':
            return self.status()
        if path == '/api/manage/preview':
            with self.lock:
                prepared = self.state.get('prepared')
            if not prepared:
                raise ValueError('게시 미리보기를 먼저 생성하세요.')
            validate(load(prepared['package']))
            return Path(prepared['preview']).read_bytes()
        raise ValueError('알 수 없는 요청입니다.')

    def post(self, path, data, server):
        action = path.rsplit('/', 1)[-1]
        if action in ('analyze', 'prepare', 'send'):
            return self.start(action, data)
        if self.mutex.locked():
            raise ValueError('작업 완료 후 설정 변경·종료를 진행하세요.')
        if action == 'settings':
            self.check_limit(data.get('max_new_calls'))
            self.settings = {'max_new_calls': data['max_new_calls']}
            self.save_json('settings.json', self.settings)
        elif action == 'key':
            self.keys.save(data.get('key'))
        elif action == 'delete-key':
            self.keys.delete()
        elif action == 'shutdown':
            threading.Thread(target=server.shutdown, daemon=True).start()
        else:
            raise ValueError('알 수 없는 요청입니다.')
        return {'ok': True}


def page(template):
    controls = (Path(__file__).with_name('management.html')).read_text(encoding='utf-8')
    return template.replace('<div id="message"', controls.split('<!--SCRIPT-->')[0]+'<div id="message"', 1).replace(
        '</html>', controls.split('<!--SCRIPT-->')[1]+'</html>')


def main():
    from .review_server import make_server
    import msvcrt
    instance_dir = ROOT/'output/notion_live/manager'
    instance_dir.mkdir(parents=True, exist_ok=True)
    instance = (instance_dir/'instance.lock').open('a+b')
    if not instance.tell():
        instance.write(b'0'); instance.flush()
    instance.seek(0)
    try:
        msvcrt.locking(instance.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        instance.close()
        try:
            endpoint = load(instance_dir/'endpoint.json')
            port = endpoint['port']
            if type(port) is int and 1 <= port <= 65535:
                webbrowser.open(f'http://127.0.0.1:{port}')
        except (OSError, ValueError, KeyError):
            pass
        print('학습자료 관리가 이미 실행 중입니다. 기존 화면을 사용하세요.', flush=True)
        return
    store = Workspace(DEFAULT_WORKSPACE)
    manager = Manager()
    server = make_server(store, 0, manager=manager)
    manager.save_json('endpoint.json', {'port': server.server_port})
    url = f'http://127.0.0.1:{server.server_port}'
    print('학습자료 관리: '+url+'\n종료는 웹 화면의 프로그램 종료 버튼을 누르세요.', flush=True)
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Keep active worker alive on Ctrl+C rather than abandoning an uncertain write.
        if manager.worker and manager.worker.is_alive():
            print('진행 중 작업의 종료를 기다립니다.', flush=True)
            manager.worker.join()
        server.server_close()
        instance.close()


if __name__ == '__main__':
    main()

"""Create a separate Windows user copy without changing the development tree.

Existing destinations are never replaced. Historical signed packages/receipts
are copied verbatim; only current source locations in the copied library move.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'study/study-system'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def selected():
    files = []
    for folder in ('analyzer', 'collector', 'config', 'tools/notion_bridge'):
        files += [p for p in (SOURCE/folder).rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts]
    files += [SOURCE/'requirements.txt']
    files += list((SOURCE/'output').glob('study_material_analysis_schema_*.json'))
    for folder in ('knowledge_base', 'analyzer_cache', 'free_recheck_runs',
                   'new_material_test', 'notion_live'):
        for path in (SOURCE/'output'/folder).rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            if path.parent == SOURCE/'output/notion_live/manager' and path.name != 'settings.json':
                continue
            if path.suffix == '.lock':
                raise RuntimeError('작업 잠금이 있습니다. 종료·복구 상태를 확인하세요: '+str(path))
            if not path.name.endswith(('-wal', '-shm', '-journal')):
                files.append(path)
    return sorted(set(files))


def relocate_origins(destination):
    """Relocate advisory evidence links without altering approval snapshots."""
    runtime = destination/'study/study-system'
    count = 0
    with closing(sqlite3.connect(runtime/'output/knowledge_base/library.sqlite3')) as db:
        for table in ('materials', 'revisions'):
            for rowid, raw in db.execute('SELECT rowid,record FROM '+table).fetchall():
                record = json.loads(raw)
                origin = Path(record.get('origin') or '.')
                if not origin.is_absolute() or not origin.is_relative_to(ROOT):
                    continue
                if origin.is_relative_to(destination):
                    continue
                target = destination/origin.relative_to(ROOT)
                if not origin.is_relative_to(SOURCE) and origin.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(origin, target)
                record['origin'] = str(target)
                db.execute('UPDATE '+table+' SET record=? WHERE rowid=?',
                           (json.dumps(record, ensure_ascii=False), rowid))
                count += 1
        db.commit()
    return count


def build(destination):
    destination = Path(destination).resolve()
    if not destination.is_relative_to(ROOT) or destination == ROOT:
        raise ValueError('사용자용 폴더는 프로젝트 내부의 새 폴더로 지정하세요.')
    if destination.exists():
        raise FileExistsError('기존 사용자 폴더는 덮어쓰지 않습니다: '+str(destination))
    if sys.version_info[:2] != (3, 14) or platform.system() != 'Windows':
        raise RuntimeError('현재 보관 라이브러리는 Windows Python 3.14용입니다.')
    import msvcrt
    lock_path = SOURCE/'output/notion_live/manager/instance.lock'
    lock = lock_path.open('r+b') if lock_path.exists() else None
    try:
        if lock:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        delivery = SOURCE/'output/notion_live/outbox/delivery.sqlite3'
        if delivery.is_file():
            with closing(sqlite3.connect(delivery.as_uri()+'?mode=ro', uri=True)) as db:
                if db.execute("SELECT COUNT(*) FROM operations WHERE state!='success'").fetchone()[0]:
                    raise RuntimeError('미완료 게시 작업을 먼저 확인하세요. 불확실한 전송 상태는 복제하지 않습니다.')
        files = selected()
        originals = {p: sha(p) for p in files}
        raw_sources = sorted(p for p in (ROOT/'study/sourcefile').rglob('*') if p.is_file())
        originals.update({p: sha(p) for p in raw_sources})
        destination.mkdir()
        runtime = destination/'study/study-system'
        for path in files:
            target = runtime/path.relative_to(SOURCE)
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == '.sqlite3':
                with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as source_db:
                    with closing(sqlite3.connect(target)) as target_db:
                        source_db.backup(target_db)
                        assert target_db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            else:
                shutil.copy2(path, target)
        for path in raw_sources:
            target = destination/'study/sourcefile'/path.relative_to(ROOT/'study/sourcefile')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        shutil.copytree(SOURCE/'.test-deps', destination/'vendor',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'bin', '.gitignore'))
        # Records, snapshots, approvals and receipts stay byte-for-byte logical
        # equivalents. Only the mutable path-to-material index is relocated.
        relocated = 0
        with closing(sqlite3.connect(runtime/'output/knowledge_base/library.sqlite3')) as db:
            for path, mid in db.execute('SELECT path,material_id FROM locations').fetchall():
                old = Path(path)
                if old.is_relative_to(ROOT/'study/sourcefile'):
                    new = destination/'study/sourcefile'/old.relative_to(ROOT/'study/sourcefile')
                    db.execute('UPDATE locations SET path=? WHERE path=?', (str(new), path))
                    relocated += 1
            db.commit()
        origin_count = relocate_origins(destination)
        assert all(sha(path) == value for path, value in originals.items()), '개발 원본이 변경됐습니다.'
        (destination/'start.py').write_text(BOOTSTRAP, encoding='utf-8')
        (destination/'프로그램_실행.cmd').write_text(LAUNCHER, encoding='utf-8')
        (destination/'README.md').write_text(USER_README, encoding='utf-8')
        manifest = {'created_at': datetime.now(timezone.utc).isoformat(),
                    'status': 'built', 'python': '3.14', 'platform': platform.machine(),
                    'development_source': str(SOURCE), 'relocated_locations': relocated,
                    'relocated_advisory_origins': origin_count,
                    'original_files_unchanged': len(originals),
                    'excluded': ['tests', 'fixtures', '.test-deps', '__pycache__',
                                 'benchmark_status_intake.py', 'temporary test outputs'],
                    'data': 'independent snapshot; approvals and receipts preserved; regenerate preview',
                    'files': {p.relative_to(destination).as_posix(): sha(p)
                              for p in destination.rglob('*') if p.is_file()}}
        (destination/'distribution_manifest.json').write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        return manifest
    finally:
        if lock:
            lock.close()


BOOTSTRAP = '''"""User entry point. Uses only the adjacent application and libraries."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT/'study/study-system'
if sys.version_info[:2] != (3, 14):
    raise SystemExit('이 사용자용 폴더는 Python 3.14가 필요합니다.')
sys.path[:0] = [str(ROOT/'vendor'), str(RUNTIME)]
os.environ['PYTHONPATH'] = os.pathsep.join([str(ROOT/'vendor'), str(RUNTIME)])
sys.dont_write_bytecode = True
os.chdir(RUNTIME)
if __name__ == '__main__':
    from analyzer.management import main
    main()
'''

USER_README = '''# 일반 사용자용 프로그램

현재 PC의 Windows Python 3.14용 실행 복사본입니다. `프로그램_실행.cmd`가 통합 관리 화면을 엽니다.

| 위치 | 역할 |
| --- | --- |
| study/sourcefile | 실제 학습 원본 |
| study/study-system | 프로그램과 설정 |
| study/study-system/output | 분석 캐시·승인 정보·게시 이력·실행 결과 |
| vendor | 실행 라이브러리 |

생성 시점의 학습 원본·승인 정보·게시 이력을 포함합니다. 개발용 tests·fixtures·임시 시험 결과·성능 측정 도구는 제외하고 게시 중계 코드는 유지합니다.

기존 프로젝트는 개발용으로 유지합니다. 실제 자료 입력·분석·승인·게시 준비는 이 사용자용 폴더에서 진행합니다. 두 폴더의 자료와 이력은 자동으로 합쳐지지 않습니다. 첫 게시 준비는 이 화면에서 미리보기를 새로 생성합니다. 복사된 과거 패키지는 당시 이력입니다.

API 키 파일은 복사하지 않습니다. 같은 Windows 계정에서는 자격 증명 관리자에 저장한 키를 재사용합니다. 설정 탭에서 등록 상태를 확인합니다. 예산 한도 기록은 기존 계정 단위 기록을 사용합니다. 실제 Notion 전송은 기존 채팅 중계 방식입니다.

distribution_manifest.json은 생성 시점 파일 목록과 검증값입니다. 실행 데이터는 사용하면서 변경됩니다. verification.json과 ui_verification.json은 로컬 검증 결과입니다. 생성한 현재 경로에서 사용하며, 다른 PC나 경로로 옮길 때에는 Python·라이브러리와 저장 경로를 다시 확인해야 합니다.
'''

LAUNCHER = '''@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if defined STUDY_PYTHON goto selected
where py >nul 2>nul
if not errorlevel 1 (
    py -3.14 -I -B -X utf8 "%~dp0start.py"
) else (
    python -I -B -X utf8 "%~dp0start.py"
)
goto finished
:selected
"%STUDY_PYTHON%" -I -B -X utf8 "%~dp0start.py"
:finished
if errorlevel 1 pause
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'user_app')
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, ensure_ascii=False))

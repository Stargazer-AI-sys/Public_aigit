import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import shutil

if __package__:
    from .scanner import scan_files
    from .extractor import extract_text
    from .hasher import calculate_sha256
else:
    from scanner import scan_files
    from extractor import extract_text
    from hasher import calculate_sha256

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ['filename', 'path', 'extension', 'size_bytes', 'created_at', 'modified_at',
          'sha256', 'text_length', 'status', 'error', 'text']


def process_file(file_path):
    result = dict.fromkeys(FIELDS, '')
    result.update(filename=file_path.name, path=str(file_path), extension=file_path.suffix.lower(), text_length=0)
    try:
        stat = file_path.stat()
        result.update(size_bytes=stat.st_size,
                      created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(timespec='seconds'),
                      modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds'))
        result['sha256'] = calculate_sha256(file_path)
        text = extract_text(file_path)
        if calculate_sha256(file_path) != result['sha256']:
            raise ValueError('추출 도중 원본이 변경되었습니다. 다시 수집하세요.')
        if not text.strip():
            raise ValueError('추출 본문이 비어 있습니다.')
        result.update(text=text, text_length=len(text), status='success', error='')
    except Exception as error:
        result.update(status='error', error=str(error), text='', text_length=0)
    return result


def save_inventory(results, output_file):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    token = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:12]
    temporary = output_file.with_name(output_file.name + '.' + token + '.tmp')
    try:
        with temporary.open('x', newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(results)
        if output_file.exists():
            backup = output_file.with_name(output_file.stem + '.backup_' + token + output_file.suffix)
            shutil.copy2(output_file, backup)
            print(f'이전 CSV 보관: {backup}')
        temporary.replace(output_file)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description='Study Material Collector v0.2')
    parser.add_argument('--source-dir', type=Path, default=ROOT.parent / 'sourcefile')
    parser.add_argument('--output-file', type=Path, default=ROOT / 'output/material_inventory.csv')
    args = parser.parse_args()
    try:
        source, output = args.source_dir.resolve(), args.output_file.resolve()
        if output.is_relative_to(source):
            raise ValueError('결과 CSV는 원본 폴더 밖에 지정하세요.')
        files = scan_files(source)
        if not files:
            raise ValueError('TXT/DOCX 파일을 찾지 못했습니다. 기존 결과는 유지합니다.')
        results = [process_file(path) for path in files]
        save_inventory(results, output)
        count = sum(row['status'] == 'success' for row in results)
        print(f'전체={len(results)}, 성공={count}, 실패={len(results)-count}\n{output}')
        return 0 if count == len(results) else 1
    except (OSError, ValueError) as error:
        print(f'수집 설정 오류: {error}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

"""원본 학습자료 읽기. 원본 파일은 읽기만 한다."""
from hashlib import sha256
from pathlib import Path

from docx import Document

SUPPORTED = {'.txt', '.docx'}


def list_sources(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f'원본 폴더를 찾을 수 없습니다: {folder}')
    # 파일명이 자료 구분 기준이므로 하위 폴더는 보지 않는다. 같은 이름이 둘이면 구분할 수 없다.
    return sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED),
                  key=lambda p: p.name.lower())


def file_hash(path):
    digest = sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path):
    path = Path(path)
    if path.suffix.lower() == '.docx':
        return '\n'.join(p.text.strip() for p in Document(path).paragraphs if p.text.strip())
    for encoding in ('utf-8-sig', 'cp949'):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f'UTF-8·CP949로 읽을 수 없는 파일입니다: {path.name}')

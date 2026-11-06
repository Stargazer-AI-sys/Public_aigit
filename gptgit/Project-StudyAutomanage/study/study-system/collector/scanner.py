from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".docx"}


def scan_all_files(source_dir: Path) -> list[Path]:
    """
    source_dir 이하의 모든 파일을 재귀적으로 검색한다.

    지원 여부와 무관하게 파일 목록을 한 번 탐색한다. 원본은 수정하지 않는다.
    """

    if not source_dir.exists():
        raise FileNotFoundError(
            f"원본 폴더를 찾을 수 없습니다: {source_dir}"
        )

    if not source_dir.is_dir():
        raise NotADirectoryError(
            f"원본 경로가 폴더가 아닙니다: {source_dir}"
        )

    files = []

    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue

        files.append(path)

    return sorted(files, key=lambda p: str(p).lower())


def scan_files(source_dir: Path) -> list[Path]:
    """기존 Collector 진입점: TXT/DOCX만 반환한다."""
    return [path for path in scan_all_files(source_dir)
            if path.suffix.lower() in SUPPORTED_EXTENSIONS]


from hashlib import sha256
from pathlib import Path


def calculate_sha256(
    file_path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """
    파일 전체 내용을 읽어 SHA-256 Hash를 계산한다.

    chunk_size:
        한 번에 읽을 바이트 크기.
        기본값: 1MB
    """

    hash_object = sha256()

    with file_path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)

            if not chunk:
                break

            hash_object.update(chunk)

    return hash_object.hexdigest()


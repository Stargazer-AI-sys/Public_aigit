from pathlib import Path

from docx import Document


def extract_txt(file_path: Path) -> str:
    """
    TXT 파일의 텍스트를 읽는다.

    UTF-8을 우선 사용하고,
    실패할 경우 CP949를 시도한다.
    """

    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]

    last_error = None

    for encoding in encodings:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error

    raise UnicodeDecodeError(
        "unknown",
        b"",
        0,
        1,
        f"지원하는 인코딩으로 읽을 수 없습니다: {last_error}",
    )


def extract_docx(file_path: Path) -> str:
    """
    DOCX의 일반 문단 텍스트를 추출한다.
    """

    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def extract_text(file_path: Path) -> str:
    """
    파일 확장자에 따라 적절한 텍스트 추출기를 선택한다.
    """

    extension = file_path.suffix.lower()

    if extension == ".txt":
        return extract_txt(file_path)

    if extension == ".docx":
        return extract_docx(file_path)

    raise ValueError(
        f"지원하지 않는 파일 형식입니다: {file_path}"
    )


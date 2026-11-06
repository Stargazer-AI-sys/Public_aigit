# CCNA 학습자료 정리 프로그램

Windows Python 3.14용입니다. `프로그램_실행.cmd`를 실행하면 관리 화면이 열립니다.

## 흐름
1. **자료 분석**: `study/sourcefile`의 `.txt`·`.docx` 중 고른 자료를 OpenAI로 분석합니다(자료마다 유료 호출 1번). 분석 결과에는 CCNA 분류, 주제별 정리, 원문 근거, AI 검토 의견(CCNA 기준 정정·보충, 보완할 점)이 들어갑니다.
2. **게시 준비**: [미리보기·게시 요청문 만들기]를 누르면 게시할 페이지와 미리보기가 만들어집니다.
3. **Notion 게시**: 게시 요청문을 복사해 Notion이 연결된 채팅(Codex 또는 Claude Code)에 붙여 넣습니다. 채팅 AI가 `data/publish/GUIDE.md`에 따라 게시하고 `result.json`을 남깁니다.
4. [목록 새로 고침]을 누르면 게시한 자료가 '게시 완료'로 바뀝니다.

## 자료 구분
- 자료는 **파일명**으로 구분합니다. 같은 이름의 Notion 페이지가 있으면 새로 만들지 않고 내용을 바꿉니다.
- 파일 내용 해시(SHA-256)는 내용이 바뀌었는지 확인하는 데만 씁니다. 내용이 바뀐 자료는 '내용 변경'으로 표시되고 다시 분석해야 게시됩니다.

## 위치
| 위치 | 역할 |
| --- | --- |
| study/sourcefile | 학습 원본(프로그램은 읽기만 함) |
| study/study-system/analyzer | 프로그램 |
| study/study-system/config/notion.json | 게시할 Notion 홈 페이지 주소 |
| study/study-system/data/results | 자료별 분석 결과 |
| study/study-system/data/publish | 최근 게시 패키지(페이지·미리보기·요청문) |
| study/study-system/data/published.json | 게시 완료 기록(파일명, 해시, 페이지 주소) |
| study/study-system/tests | 확인용 테스트(유료 API·Notion 호출 없음) |
| vendor | 실행 라이브러리(python-docx, jsonschema) |

## 참고
- API 키는 Windows 자격 증명 관리자에 저장합니다. 프로젝트 파일에는 저장하지 않습니다.
- Notion 페이지에서는 장비 설정 예시의 비밀번호·키 값을 `[인증값 숨김]`으로 가립니다. 분석 결과 파일에는 원문이 그대로 남습니다.
- 테스트 실행: `study/study-system` 폴더에서 `PYTHONPATH=../../vendor;.` 설정 후 `py -3.14 -B -X utf8 -m unittest discover -s tests`

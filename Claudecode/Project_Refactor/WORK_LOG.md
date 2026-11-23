# Project_Refactor 작업 기록

> 최종 갱신 2026-11-06 (ICT PC 세션) | 새 세션은 §0 "인계 요약"부터 읽는다. 경로는 저장소 루트(`aigit`) 기준 상대 경로다.

## 0. 인계 요약 (가장 먼저 읽기)

### 현재 상태
- 간소화 재설계 프로그램(9개 파일, 약 700줄)으로 첫 실제 시험(10-29)을 마쳤고, **11-06에 자료 4개를 추가로 분석(사용자가 직접 테스트)해 Notion에 게시했다**. 게시는 성공했고 실패는 0건이다(§8).
- Notion에는 자료 5개가 있다: `2일차_원격접속.txt`(10-29 게시, 옛 분석 기준), `12일차.docx`, `15일차 Dynamic routing_IGP.txt`, `18일차.txt`, `1일차_LAN구성.txt`(11-06 게시). 주소는 §6.
- `data/publish/result.json`은 만들었지만 `data/published.json`에는 아직 합치지 않았다.
- 테스트 결과 문서: `Claudecode/Project_Refactor/test_result/20261106_Notion게시_자료4개_게시테스트.md`.
- 브라우저 화면은 아직 직접 눌러 보지 않았다.

### 다음 단계
1. 프로그램에서 [게시 결과 반영]을 실행해 `published.json`에 합친다.
2. Notion 화면에서 접기·콜아웃·링크가 의도대로 보이는지 사용자가 직접 확인한다.
3. **결정 필요:** 자동 게시(A: Notion 공식 API를 프로그램이 직접 호출) 도입 여부. 하려면 사용자가 Notion 내부 연동 토큰을 발급하고 홈 페이지를 연동에 공유해야 한다. 그다음 테스트용 페이지 1개로 생성·갱신·하위 페이지 유지를 시험한다(§10).
4. `2일차_원격접속.txt`를 다시 분석·게시한다(Notion 본문이 옛 분석 그대로다). **유료이므로 사용자 요청 후에만 한다.**
5. 나머지 자료를 분석·게시한다. **유료이므로 사용자 요청 후에만 한다.**
6. 최종 결과를 `Project_Refactor/refactory_result/`에 만든다. 사용자가 요청할 때만 한다.

### 잊기 쉬운 주의사항
- **PC별로 다시 설정해야 하는 것(git으로 옮겨지지 않음):**
  - Notion MCP: `~/.claude.json`의 local 범위에 있다. ICT PC는 10-29에 추가·인증을 마쳤다. 집 PC는 기존 설정을 쓴다.
  - OpenAI API 키: Windows 자격 증명 관리자 `StudyAutomanage/OpenAI/APIKey`. ICT PC는 10-29에 사용자가 화면의 키 저장 기능으로 새 키를 등록했다(예전 키는 만료).
- 실행 중인 `start.py`가 있으면 사본 파일을 고치지 않는다. 확인 방법: `Get-CimInstance Win32_Process -Filter "Name like 'py%'"`에서 `start.py`를 찾는다. [프로그램 종료] 직후에는 프로세스가 잠시 남아 있을 수 있다.
- 게시 요청문(`data/publish/prompt.txt`)에는 그 PC의 절대 경로가 들어간다. 게시 준비와 게시는 같은 PC에서 한다.
- 사용자가 작업기록을 수시로 갱신하지 말라고 했다. 작업을 마칠 때 요청을 받으면 한 번에 정리한다.

## 1. 목적
`gptgit/Project-StudyAutomanage/user_app`(학습자료 분석·Notion 게시 프로그램)을 사용자에게 필요한 흐름 중심으로 **간소화 재설계**한다. 사용자는 코딩 지식이 낮으므로 구조와 위험은 쉬운 말로 설명한다.
- 사용자 흐름: ① 파일 하나 분석 → ② CCNA 학습 분류 → ③ 게시할 내용 정리 → ④ Notion 반영 → ⑤ CCNA 기준으로 부실하면 AI 코멘트.

## 2. 폴더와 PC 규칙
- 원본(읽기만): `gptgit/Project-StudyAutomanage/`(`user_app` 포함).
- 작업 사본(여기서만 수정): `Claudecode/Project_Refactor/refactory_target`.
- 최종 결과: `Claudecode/Project_Refactor/refactory_result/`. 작업이 끝나고 사용자가 요청한 뒤에만 만든다.
- 사용자는 개인 저장소 `aigit`을 PC 사이에서 commit/pull로 옮긴다. ICT PC: `C:\Users\ICT\Desktop\Aigit`, 집 PC: `C:\Users\Stargazer\OneDrive\Desktop\aigit`. commit과 push는 사용자가 요청하면 Claude가 한다.

## 3. 프로그램 실행
- `프로그램_실행.cmd` 또는 `py -3.14 -I -B -X utf8 start.py`. Python 3.14가 필요하다(ICT PC: 3.14.8). `start.py`는 `analyzer.app.main()`을 실행하고 로컬 웹 화면을 연다.
- 화면 구성: ① 자료 분석(자료 선택, 모델 선택, 유료 확인 창) → ② 미리보기·게시 요청문 만들기, 요청문 복사 → ③ API 키 저장·삭제, 목록 새로 고침, 프로그램 종료.
- 실행하면 `study/study-system/data/`가 바뀐다. 분석 버튼은 유료 OpenAI API를 자료마다 1번 호출한다. 자동 재시도는 없다.
- **화면 없이 시험하는 방법(10-29 사용):**
  - 포트는 `data/app/endpoint.json`에 있다. `GET /`의 `nonce="..."` 값이 토큰이다.
  - POST에는 `X-Token`, `Origin: http://127.0.0.1:<포트>` 헤더가 필요하다. `GET /api/status`는 토큰이 필요 없다.
  - Git Bash에서 한글 JSON을 `--data-binary '...'`로 직접 넘기면 인코딩이 깨진다(400 오류). Python으로 UTF-8 파일을 만들어 `--data-binary @파일`로 보낸다.
  - 게시 패키지만 만들 때는 서버 없이 `publish.build(app.SOURCE, app.DATA, config)`를 호출해도 된다.

## 4. 새 구조 (`refactory_target/study/study-system`)
| 파일 | 역할 |
| --- | --- |
| `analyzer/sources.py` | 원본 폴더(`study/sourcefile`, 하위 폴더 제외)의 `.txt`·`.docx` 목록, 읽기(UTF-8 → CP949), SHA-256 |
| `analyzer/ccna.py` | CCNA v1.1 기반 분류표: 6개 분야, 21개 단원(보충 단원 포함). 기존 `curriculum.py`의 내용을 옮겼다 |
| `analyzer/analysis.py` | OpenAI Responses API를 1번 호출(strict JSON 형식). 모델 `gpt-6-luna`(기본), `gpt-6.1-sol`. 응답 형식을 검사하고, 근거 줄 번호를 원문 인용으로 바꾼다. 리다이렉트는 차단한다(API 키 보호) |
| `analyzer/records.py` | 결과 `data/results/<파일명>.json`, 게시 기록 `data/published.json`. 상태 판정: 새 자료 / 내용 변경 / 게시 대기 / 게시 완료 |
| `analyzer/publish.py` | Notion 페이지(홈, 분야 6개, 학습자료·개념·실습 목록, 자료 페이지), 미리보기, `GUIDE.md`(채팅 AI용 안내), `prompt.txt`, `manifest.json` 생성. 비밀번호 가림 |
| `analyzer/app.py`, `app.html` | 로컬 화면. 127.0.0.1만 허용하고, Host·Origin·토큰을 확인한다. 중복 실행은 `data/app/instance.lock`으로 막는다 |
| `analyzer/credentials.py` | 기존 그대로(Windows 자격 증명 관리자) |
| `config/notion.json` | 홈 페이지 제목과 주소 |
| `tests/test_flow.py` | 새 흐름 테스트 13개 |

**AI 응답 형식:** `summary`, `categories`(분류표 이름 중에서 선택), `concepts`, `sections[]`, `ccna_gaps[]`.
- `sections[]`의 각 단락: `title`, `points[]`(subject, content, evidence), `practice[]`(title, description, evidence), `comment`(정정/보충 또는 null)
- `ccna_gaps[]`의 각 항목: category, text

**게시 방식(A, 사용자 결정):**
1. 프로그램이 `data/publish/`에 게시 패키지를 만든다.
2. 사용자가 요청문을 채팅(Codex 또는 Claude Code)에 붙여 넣는다.
3. 채팅 AI가 `GUIDE.md`대로 게시한다.
   - 자료 페이지: '학습자료' 페이지 아래에서 제목이 파일명과 같은 페이지를 찾아 있으면 갱신하고, 없으면 만든다.
   - 링크: 본문의 `{{page:제목}}` 자리표시를 해당 페이지의 `<mention>` 링크로 바꾼다.
4. 채팅 AI가 `result.json`을 남기면, 프로그램이 이를 읽어 `published.json`에 합친다.
- 패키지에는 게시 대기 자료의 페이지만 넣는다. 목록 페이지는 현재 분석 결과 전체로 매번 다시 만든다.
- **실제 게시 순서(10-29):** 목록·분야 페이지를 빈 페이지로 먼저 만들어 주소를 얻는다 → 자료 페이지를 만든다 → 자리표시를 주소로 바꿔 나머지 본문을 채운다. 홈과 '학습자료'는 `replace_content`에 하위 `<page>` 태그를 함께 넣어 하위 페이지를 보존한다.

**Notion 표기:** 공식 규칙 문서(`notion://docs/notion-flavored-markdown-spec`)를 2026-10-28, 10-29에 확인했다.
- 접기는 `<toggle>`, 링크는 `<mention url>`을 쓴다. 블록 태그는 여는 태그 다음 줄이 제목이고, 빈 줄 뒤에 내용이 온다. 코드 블록은 들여쓰지 않는다.
- CommonMark 기준이라 백슬래시로 문장부호를 일반 글자로 만들 수 있다(`2\.`).
- 기존 코드가 쓰던 `<details>`, `<mention-page>`, 들여쓴 코드 블록은 지금 규칙과 맞지 않았다.

## 5. 결정 기록
| 날짜 | 결정 | 근거 |
| --- | --- | --- |
| 10-28 | 간소화 재설계로 전환. 저장 결과 재분석 허용 | 사용자 |
| 10-28 | 자료 구분 = 파일명 + 내용 해시 1개. 해시는 변경 감지에만 쓴다 | 사용자 |
| 10-28 | 기존 Notion 페이지는 파일명 기준으로 갱신(중복 생성 금지) | 사용자 |
| 10-28 | 코멘트 = AI가 CCNA 기준으로 부족한 점 지적 | 사용자 |
| 10-28 | **Notion DB를 쓰지 않고 보통 페이지로 새로 구성** | 화면은 DB 기능을 쓰지 않았다. DB 칸은 전송 점검용이었다. 사용자: 테스트 자료가 많아 새로 구성 |
| 10-28 | **게시 = 방식 A(프로그램이 패키지·요청문 생성 → 채팅 AI가 게시).** 나중에 자동 게시로 바꿀 예정 | 사용자 |
| 10-28 | **승인 단계 제거.** 분석 → 미리보기 → 게시 | 사용자 |
| 10-28 | **기존 Notion 자료·사본 실행 데이터 삭제** | 사용자: "기존 자료 없어도 된다", "전부 진행" |
| 10-28 | CCNA 분류는 AI가 분류표 이름 중에서 고른다(기존: 단어 일치) | Claude 기본값. 사용자에게 알렸다 |
| 10-28 | AI 출력 상한 6000 → 8000 토큰 | 코멘트가 추가됐기 때문. Claude 기본값. 사용자에게 알렸다 |
| 10-28 | Notion 자료 페이지에 PC 절대 경로를 넣지 않는다. 파일명·해시·분석 시각만 넣는다 | 기존 페이지에 ICT 경로가 노출돼 있었다 |
| 10-28 | 비밀번호 가림 규칙에 `username … pass 값` 형태 추가 | 기존 규칙이 놓쳐 Notion에 값이 노출돼 있었다(그 페이지는 삭제됨) |
| 10-28 | refactory_target 줄바꿈 규칙을 `text=auto eol=crlf` 하나로 단순화 | 학습자료 해시가 PC마다 같게 유지된다 |
| 10-29 | 첫 실제 시험을 화면 없이 `curl`로 진행(방식 B). 유료는 등록한 키 한정으로 승인 | 사용자 |
| 10-29 | `text()`: 숫자+점(`2. `)으로 시작하면 `2\.`로 적는다 | 게시 결과 "CCNA 분류" 목록이 글머리 안 번호 목록으로 저장됐다 |
| 10-29 | '개념 찾아보기'를 분류별 묶음 없이 개념당 한 줄로 바꿈 | 개념은 자료 전체에 붙어 있어 분류마다 같은 목록이 반복됐다(8개 × 3) |
| 11-06 | 자료의 비밀번호가 대부분 학습용 단순 값이므로, 요약 문장에 남아도 조치하지 않는다. 실제 계정·장비용 복잡한 값이 들어오면 그때 다시 판단한다 | 사용자 |
| 11-06 | 자동 게시는 A안(Notion 공식 API 직접 호출)을 검토 방향으로 한다. C안(MCP 직접 호출)은 로그인 처리가 번거롭고 A보다 이점이 없어 제외 | 조사 결과 기반 Claude 제안. 도입 여부는 사용자 결정 대기 |
| 11-06 | 테스트 결과 문서는 `Project_Refactor/test_result/`에 `날짜_테스트 내용 요약.md`로 둔다. 단계별 과정, 비용(토큰·시간), 이슈와 개선 방향을 넣는다 | 사용자 |

## 6. 확인한 사실 (Notion)
- Notion MCP(공식 서버)로 읽기·검색·생성·수정·삭제가 된다. 계정: 유승철 / "유승철님의 워크스페이스"(사용자가 의도한 계정임을 10-29에 확인).
- **10-28 삭제(휴지통, 복구 가능):** 예전 분야 페이지 6개, 개념 찾아보기, 학습자료, 실습 찾아보기, 학습 데이터 관리(DB 4개 포함). 예전 페이지는 DB 보기 블록 없이 글자와 멘션으로만 돼 있었고, DB의 숨긴 칸은 `verify.py` 전송 점검에만 쓰였다.
- **10-29 현재 구조:**
  - 홈 "Network 학습 자료" `3fb062cd-7cd1-80c6-ab73-d56d5fadc0a5`
  - 홈 아래: 학습자료 `408062cd-7cd1-8161-9f83-e64650ad8f6d`, 개념 찾아보기 `408062cd-7cd1-81ab-a4e5-c6d91fc8cc92`, 실습 찾아보기 `408062cd-7cd1-81d0-b957-ec393d49f940`, 분야 페이지 6개(`408062cd-7cd1-8136…`, `-817c…`, `-8120…`, `-8142…`, `-81be…`, `-81fa…`)
  - '학습자료' 아래: `2일차_원격접속.txt` `408062cd-7cd1-812b-931a-c580a333172d`
    - **11-06 추가('학습자료' 아래):** `12일차.docx` `410062cd-7cd1-8155-b802-dd88bba3d3b8`, `15일차 Dynamic routing_IGP.txt` `410062cd-7cd1-8130-9dd8-f805ad8b79c1`, `18일차.txt` `410062cd-7cd1-8128-abca-cd8ea02a608c`, `1일차_LAN구성.txt` `410062cd-7cd1-8159-8197-d64a774d1283`
  - 11-06 게시 뒤 '학습자료'를 다시 조회해 하위 페이지 5개, 같은 제목 중복 없음을 확인했다. 홈과 '학습자료' 본문 교체 때 하위 페이지 삭제 경고는 없었다.
- 무관한 "2026'Cloud Network 2기 공유 페이지"는 건드리지 않았다.
- Notion은 `<mention url>라벨</mention>`을 읽어 올 때 라벨 없이 `<mention url="..." />`로 돌려주는 경우가 있다. 화면에는 페이지 제목이 정상으로 보인다(추정, 화면 미확인).

## 7. 줄바꿈 (`.gitattributes`)
- 원본 앱(`gptgit/Project-StudyAutomanage`)은 기존 파일별 규칙을 유지한다(기존 지문 보호).
- 사본(`refactory_target/**`)은 `text=auto eol=crlf` 하나로 정했다.
- 학습자료 `.txt`는 CRLF로 꺼내진다. 내용 해시는 파일 바이트 기준이므로 줄바꿈이 바뀌면 '내용 변경'으로 표시된다.
- 10-29: ICT PC에서 pull한 뒤 `.txt` 10개 모두 CRLF로 유지된 것을 확인했다.

## 8. 검증
- 테스트 실행: `refactory_target/study/study-system`에서 Bash로 `PYTHONPATH="../../vendor;." py -3.14 -B -X utf8 -m unittest discover -s tests`. 결과 13개 OK(10-29, ICT PC).
- **테스트 범위:**
  - 원본 목록·CP949 읽기
  - 근거 줄 → 원문 인용 변환, 잘못된 응답 거부(분류 없음·분류표 밖 이름·JSON 아님·빈 단락·줄 번호 범위 밖·빈 줄)
  - OpenAI strict 형식 규칙 충족, 요청문에 줄 번호와 분류표 포함
  - 상태 변화(새 자료 → 게시 대기 → 게시 완료 → 내용 변경)
  - 게시 패키지 내용과 비밀번호 가림, 숫자+점 목록 표기, 개념 목록 중복 없음, 게시된 자료는 링크만 걸고 다시 게시하지 않음, 원본이 바뀐 자료 제외
  - 분석 작업의 성공·실패 기록, 예상 밖 오류가 키를 노출하지 않음, 토큰 없는 요청 403
- 10-29 추가한 두 검사가 고치기 전 `publish.py`에서 실패하는 것을 확인했다.
- **10-29 실제 시험(ICT PC):**
  - 분석: `2일차_원격접속.txt`, `gpt-6-luna`, 1회. 입력 4,210 / 출력 1,101(추론 184) 토큰. 형식 검사 통과. 분류 3개, 개념 8개, 단락 2개, 코멘트 1개, 보완점 3개.
  - 게시 패키지: 비밀번호 4곳 가림, PC 경로 없음.
  - Notion 게시: 접기·코드 블록·멘션·콜아웃이 의도대로 저장됐다. 홈과 '학습자료'의 하위 페이지가 보존됐다.
  - `result.json` → `published.json` 합치기, 상태 '게시 완료' 확인.
  - 재게시: 게시 기록을 지우고 패키지를 다시 만들어 기존 자료 페이지를 갱신했다. 검색 결과 같은 제목 페이지는 1개다.
- **11-06 게시 테스트(ICT PC):**
  - 대상: 자료 4개 신규 생성, 홈·개념·실습·학습자료·분야 6개 본문 교체(총 14개). 오류 0건.
  - 시간: 시계로 재지 않았다. `manifest.json` 생성(00:34:17 UTC)부터 마지막 Notion 확인(00:39:37 UTC)까지 약 5분 20초가 상한이다.
  - 토큰: 측정하지 않았다. 추산은 출력 약 5만~7만, 새 입력 약 4만이다. 비용 대부분은 AI가 자료 페이지 본문을 그대로 출력하는 데서 나온다.
  - 이번 세션에서 `test_flow.py`는 실행하지 않았다(코드 변경 없음).
- **미검증:** 브라우저 화면 조작, 긴 자료(예: `4일차 [ipv4].txt` 337줄)에서 출력 8000 토큰이 충분한지, `.docx` 실제 분석, 다른 채팅 AI(Codex)가 `GUIDE.md`대로 게시하는지.

## 9. 현재 변경 사항 (commit 전)
- 10-28 집 PC 변경은 커밋 `272106e`에 들어갔다.
- 10-29 변경:

| 파일 | 변경 |
| --- | --- |
| `Claudecode/Project_Refactor/CLAUDE.md` | "작업기록" = 이 파일이라는 규칙 추가 |
| `refactory_target/.../analyzer/publish.py` | `text()` 숫자+점 표기, `concepts_page()` 중복 제거 |
| `refactory_target/.../tests/test_flow.py` | 위 두 동작 검사 추가 |
| `refactory_target/.../data/` (추적 안 됨) | `results/2일차_원격접속.txt.json`, `published.json`, `publish/`. `data/app/`만 git 제외 |

- 11-06 변경(코드 변경 없음, 모두 commit 전):
  - `refactory_target/.../data/results/` 분석 결과 4개 추가(`12일차.docx`, `15일차 Dynamic routing_IGP.txt`, `18일차.txt`, `1일차_LAN구성.txt`), `2일차_원격접속.txt` 결과 변경
  - `refactory_target/.../data/publish/` 전체 재생성, `result.json` 새로 작성
  - `Project_Refactor/test_result/20261106_Notion게시_자료4개_게시테스트.md` 신규
  - `Project_Refactor/WORK_LOG.md` 이번 정리
- `data/publish/`에는 ICT PC 절대 경로가 든 `prompt.txt`가 있다. commit에 넣을지는 사용자가 정한다. 분석 결과(`data/results`)와 `published.json`은 PC 사이에 옮기는 것이 원래 의도다(`.gitignore` 주석).

## 10. 미확인 항목·남은 문제
- **이미 게시한 자료의 재게시 방법이 없다.** `build()`는 해시가 같은 게시 완료 자료를 패키지에서 뺀다. 표시 코드를 고쳐도 기존 자료 페이지는 바뀌지 않는다. 10-29에는 `published.json`을 비워 우회했다.
- 긴 자료에서 출력 상한 8000 토큰이 충분한지.
- Notion 멘션이 라벨 없이 저장될 때 화면 표시가 정상인지(§6).
- **11-06 게시 테스트에서 나온 것:**
  - `18일차.txt` 핵심 정리에 `password 1234`가 남아 있다(가림 규칙이 AI가 쓴 요약 문장에는 적용되지 않는다). 사용자 결정으로 무시한다(§5).
  - `2일차_원격접속.txt` 본문은 옛 분석 그대로여서, 새 기준으로 바뀐 홈·'학습자료' 요약과 내용이 다르다.
  - `result.json`의 `published_at`은 실제 시각이 아니라 근사값 `2026-11-06T01:00:00+00:00`이다.
  - 게시 비용이 자료 크기에 비례한다(자료 1개 약 10KB가 약 1만 토큰). 앞쪽 호출 2개는 한글을 `\uXXXX`로 보내 출력이 더 들었을 수 있다.
- **자동 게시(A안) 조사 결과, 모두 미확인 또는 미시험:**
  - Notion 공식 API는 `POST /v1/pages`의 `markdown` 필드와 `PATCH /v1/pages/{id}/markdown`을 지원한다고 문서에 나온다(검색 결과 요약, 직접 호출은 안 함). v2(Notion-flavored Markdown)가 지금 패키지 형식(`<toggle>`, `<callout>`, `<mention>`)을 그대로 받는지는 시험하지 않았다.
  - `PATCH /markdown`이 하위 페이지를 지우지 않는지는 시험하지 않았다.
  - 요청 한도는 연동당 분당 180회(Business 이상 600회), 요청당 블록 1,000개·500KB다(검색 결과 요약). 오류 429는 `Retry-After`만큼 기다린다.
  - 구성원 2명 이상인 무료 워크스페이스는 블록이 평생 1,000개로 제한된다(2026-09-08부터 내부 연동에도 적용, 검색 결과 요약). 우리 워크스페이스 플랜은 **미확인**이다.
  - API 사용 요금은 외부 사이트에서 "별도 요금 없음"이라고 하나 공식 확인은 하지 않았다.
  - C안(MCP 직접 호출)의 MCP 토큰은 Business·Enterprise용으로 보이고, 기본 인증은 브라우저 OAuth다(검색 1회 결과).

## 11. 이력 요약
- 10-28 오전(ICT): 구조 파악, 미사용 코드 1차 점검, import 2줄 삭제(커밋 dbf524c).
- 10-28 저녁(집): 줄바꿈 문제 해결, 커버리지·실패 원인 분석, 간소화 재설계로 전환.
- 10-28 밤(집): Notion 연결 확인, DB 필요성 점검, 모듈 정리안 확정, 새 프로그램 작성, 기존 코드·데이터·Notion 페이지 삭제(커밋 272106e).
- 10-29(ICT): Notion MCP 재연결, 무료 사전 점검(키 존재·테스트·줄바꿈), 첫 실제 분석·게시, 표시 문제 2개 수정, 재게시 확인.
- 11-06(ICT): 사용자가 자료 4개 분석 테스트 → 게시 패키지를 Notion에 게시(성공, 오류 0) → 테스트 결과 문서 작성 → 자동 게시 방식 3가지(A 공식 API 직접 호출 / B AI 대신 호출 / C MCP 직접 호출) 비교·조사.

## 12. 사용량 기록
- 10-28 오전(ICT): 1구간(Sonnet 5.5) 13:55~13:59, 2구간(Opus 5.5) 14:00~14:09.
- 10-28 저녁·밤(집 PC, Opus 5.5): 유료 OpenAI 호출 없음.
- 10-29(ICT, Opus 5.5): 유료 OpenAI 호출 1회(`gpt-6-luna`, 총 5,311 토큰).
- 11-06(ICT, Sonnet 5.5): Claude가 한 유료 OpenAI 호출은 없다. 분석 테스트 4건은 사용자가 별도로 진행했고 호출 내역은 확인하지 못했다. 게시 토큰은 추산값만 있다(§8).
- Claude 토큰·비용은 세션 안에서 읽을 수 없다. 사용자가 `/cost` 또는 `/usage`로 확인해 기록한다: ______

# project_hermes_test 작업 기록 — 보관

> 2026-11-19 `WORK_LOG.md`에서 분리했다. 현재 작업(위키 반영·서버 운영)과 직접 관계없는 이력이다. 내용은 기록 당시 그대로이며 필요할 때만 읽는다.

## 1. 사용자 결정(이전 목적·초기 설계, 2026-11-11~16)
- 2026-11-11: 신규 스킬은 만들지 않고 `work-log`만 사용한다. 평가 기록 용도로 충분하다고 판단했다.
- 2026-11-11: `/init` 없이 평가 목적 중심 초안으로 `CLAUDE.md`를 만든다.
- 2026-11-11: 메신저는 Telegram으로 먼저 연결한다(Slack은 설정이 복잡해 보류).
- 2026-11-11: 예약 작업은 웹 검색 도구 동작을 확인한 뒤 만든다.
- 2026-11-11: LLM은 구독 사용량 방식을 우선하고, 불가능하면 OpenAI API 키로 비용을 최소화한다.
- 2026-11-11: 서버는 개인 자동화 용도(뉴스, 날씨, 영수증 처리)로 검토한다.
- 2026-11-11: 클라우드 이전은 진행한다. 이전 단계 중 Telegram `/sethome`·예약 작업·영수증 테스트·사용량 기록은 이번에는 건너뛰고 클라우드 이전부터 시작한다.
- 2026-11-11: AWS 고급 기능 활성화는 보류한다. 문서에 되돌릴 수 없고 지출 한도가 제거된다고 되어 있어, 리전 선택과 MFA 메뉴 때문에 안전장치를 포기하지 않는다.
- 2026-11-11: 서버 리전은 시드니(ap-southeast-2)로 한다. 고급 기능 없이는 이 리전만 쓸 수 있었다.
- 2026-11-11: 서버 플랜은 월 $12(2GB). 크레딧 적용은 가정이며 첫 청구 때 확인한다.
- 2026-11-11: 학습 목적과 이식성을 이유로 Docker 방식 B(Hermes 자체를 컨테이너로 실행)를 채택한다. Docker 백엔드(컨테이너 안에서 컨테이너)는 쓰지 않고 `Keep current (local)`을 선택했다.
- 2026-11-11: Docker는 PC에서 먼저 테스트하고 이후 서버에 올린다. 서버에서는 PC 볼륨을 옮기지 않고 `setup`을 새로 한다(`.env` 키 전송 회피).
- 2026-11-12: PC를 옮겨 현재 PC에 이미지가 없으므로 PC Docker 재시험은 건너뛰고 서버로 바로 진행한다.
- 2026-11-12: 웹 터미널이 느려 PowerShell의 SSH로 서버에 접속한다.
- 2026-11-12: RAM 1.9GB에 스왑이 없어 OOM 방지용으로 2GB 스왑 파일을 만든다.
- 2026-11-12: `setup`에서 terminal backend는 `Keep current (local)`, 브라우저·이미지 생성·TTS는 Skip(현재 목적에 불필요하고 메모리·비용 부담), 웹 검색은 `OpenAI Native Web Search (Codex Responses)`를 선택했다.
- 2026-11-12: gateway는 채팅 플랫폼만 쓰므로 포트 8642를 열지 않는다. `docker` 그룹 추가는 하지 않고 `sudo`를 쓴다.
- 2026-11-13: 프로젝트 목적을 평가에서 "역할별 Hermes 인스턴스 생성·관리·배포 프로세스 구축"으로 바꾼다. 같은 폴더에서 목적만 갱신한다.
- 2026-11-13: 생성 단위는 역할별 인스턴스(컨테이너·데이터 폴더·봇 토큰 1세트), 배포 대상은 여러 서버·클라우드(Ubuntu 24.04 + SSH 기준, 서버 생성 IaC는 범위 밖).
- 2026-11-13: 정식 메신저는 Slack. Telegram은 테스트 용도였다. 배포 소스 수정은 사용자가 요청할 때만 한다(계획 먼저).
- 2026-11-13: 첫 역할은 Research. 처음엔 에이전트 1개로 시작하고 단계(스킬·예약 작업)로 나눈다. 인스턴스 분리는 권한·위험 차이, 맥락 오염, 일정·비용 차이가 생길 때 한다.
- 2026-11-13: 수집은 웹·RSS부터, SNS(지정 인물의 주기 추적)는 필수. 영상·음성은 보류. 문서 위주라 용량 위험은 낮다고 판단했다.
- 2026-11-13: wiki는 PC 로컬 Obsidian. 서버→PC raw 전송은 git 방식으로 확정(이력 보존, 기존 도구 재사용).
- 2026-11-13: 분류 방식은 새로 만들기보다 기존 LLM wiki 스킬(Ingest·Query·Lint) 활용을 검토한다. 필요 항목으로 표시만 하고 수집 파이프라인부터 구축한다.
- 2026-11-13: 근거는 지속가능성. 사용자 액션은 지시(인물 추가, 질문, URL 전달) 수준으로 최소화한다.
- 2026-11-13: 분류 스키마에 work/hobby 같은 고정 축은 필수가 아니다. "분류를 명확하게"는 LLM wiki에 비현실적인 요구로 보고, llmwiki식(concepts·entities·tags로 자라는 구조)을 받아들인다. Lint는 llmwiki 것을 그대로 쓴다.
- 2026-11-13: 참고 자료로 Hermes 자동화 후기 글(토픽 분리, llmwiki, qmd, 하위 질문 분해 리서치 등)을 받았다. 참고만 한다. 웹 GPT UI 자동화·결제 자동화 방식은 따르지 않는다(약관·보안 위험).
- 2026-11-13: llmwiki PoC는 A안(`llmwiki open` 상시 실행)으로 진행하기로 했다가, Python 3.14 설치 실패 후 사용자가 중단을 지시했다. Slack 창구 연결을 먼저 한다.
- 2026-11-13: Slack은 새 인스턴스가 아니라 서버의 기존 `hermes` 컨테이너에 먼저 붙인다(배포 소스 수정 없이 가장 작은 변경).
- 2026-11-13: 에이전트 2명 추가, 기본 프로필 수정, 카테고리별 채널 설정까지 해 두기로 했다. 과정이 길어 가이드 문서화가 필요하다고 판단했다.
- 2026-11-16: 비용 테스트는 ChatGPT가 아니라 Claude Code 하위 모델(Haiku 5.5)로 한다. 범위는 raw 수집 → 위키 정리까지. 리서치(요미코)는 요청 시에만 하므로 비용 산정에서 뺀다.
- 2026-11-16: 로컬 시험 데이터(HOME PC `llmwiki-local`)는 남겨 두고 사용자가 직접 처리한다. `docs/guide.md` 3-4는 추가 검토 후 결정.

## 2. 확인한 사실(설치·평가·조사 2026-11-11~16, qmd 임베딩 모델 시험 2026-11-18)
- `iex ... | iex --include-desktop` 형태는 `ParameterBindingException`으로 실패했다(사용자 실행 결과). `--include-desktop`은 bash용 옵션이고 PowerShell 옵션 이름은 `-IncludeDesktop`이라고 공식 문서에 있다. `iex (irm ...)`로 옵션을 넘기는 방법은 문서에 없다.
- PC 네이티브 CLI 설치는 완료됐다(사용자 보고). 텔레메트리는 끈 상태다.
- 모델 선택 목록에 mini 표기가 없었고, 사용자는 `gpt-6-luna`를 선택했다.
- 채팅 대화가 정상 동작했다. 날씨와 뉴스 3건 요청에 출처 링크가 붙어 응답이 왔다(사용자 확인). 별도 검색 설정 없이 동작했다.
- 2026-11-11 ChatGPT 사용량이 차감되는 것을 사용자가 확인했다.
- Telegram 연결과 응답 확인을 사용자가 마쳤다.
- AWS 계정(사용자 확인, `settings.aws.com/billing`): 무료 플랜, 남은 일수 182일, 크레딧 $100.
- AWS 공식 발표(2026-09-16)와 Builder Center 글(비공식)로 확인: 새 가입은 Free/Paid 플랜 구조이고 Free plan은 6개월 또는 크레딧 소진 시 계정이 닫히며 90일 안에 업그레이드하면 복구할 수 있다. 크레딧 만료일은 자료마다 다르다.
- 고급 기능 활성화 문서(`docs.aws.amazon.com/accounts/latest/reference/activate-advanced-features.html`): 되돌릴 수 없고, 지출 한도가 제거되며, Builder ID를 ID 소스로 다시 쓸 수 없다. 사용자 화면에서는 IAM 보안 자격 증명(MFA)과 시드니 외 리전이 이 기능 뒤에 막혀 있었다.
- Budgets 화면은 열렸고 사용자가 예산을 1개 만들었다(유형은 보고되지 않음). 화면 문구상 Budgets는 알림용이며 하드 지출 한도가 아니다.
- Lightsail은 무료 플랜 계정에서 열렸고 인스턴스를 생성했다. 서울 리전은 선택할 수 없고 시드니만 가능했다.
- 인스턴스 생성 후 Running 확인, 고정 IP 연결, 방화벽은 SSH(TCP 22)만 남김(IPv4 `0.0.0.0/0`, IPv6 동일). 브라우저 SSH 연결은 사용자가 확인했다. 자동 스냅샷은 끄는 쪽으로 안내했다.
- 이 PC의 Docker(직접 실행): 클라이언트 29.9.2, Compose v5.6.1, 엔진 29.9.3 실행 중, Docker 메모리 약 8GB. 받은 이미지 `nousresearch/hermes-agent:latest`는 4.56GB.
- PC Docker 테스트(사용자 보고, CLI 환경, `docker run -it --rm -v hermes-data:/opt/data nousresearch/hermes-agent`):
  - 컨테이너를 완전히 종료하고 재실행해도 테스트 코드를 기억했다(통과).
  - 재실행 때 ChatGPT 구독 로그인을 다시 요구하지 않았다(통과).
  - 컨테이너 안에서 웹 검색 결과를 받았다(통과).
  - `setup`에서 terminal backend는 `Keep current (local)`을 선택했다.
- 현재 PC(직접 실행, 2026-11-12): Docker 29.9.3이 있고 `docker images nousresearch/hermes-agent`, `docker volume ls` 결과가 비어 있었다. 이전 PC의 이미지·볼륨은 따라오지 않는다.
- 서버 사양(사용자 출력, 2026-11-12): Ubuntu 24.04.5 LTS, RAM 1.9Gi, 스왑 0B, 디스크 58G 중 56G 여유. 스왑 생성 후 `free -h`에서 Swap 2.0Gi를 확인했다.
- 서버 Docker 설치: 공식 apt 저장소 방식(Docker 공식 문서 확인), `sudo docker run hello-world`가 `Hello from Docker!`를 출력했다(사용자 보고). 이미지 `nousresearch/hermes-agent:latest`를 서버에서 받았다(사용자 보고).
- 서버 `setup`: `sudo docker run -it --rm -v ~/.hermes:/opt/data nousresearch/hermes-agent setup`. Telegram은 기존 봇 토큰과 사용자 ID를 입력했다(값은 기록하지 않는다).
- 서버 gateway: `sudo docker run -d --name hermes --restart unless-stopped -v ~/.hermes:/opt/data nousresearch/hermes-agent gateway run`.
- Telegram 응답(사용자가 붙인 대화, 2026-11-12): 테스트 메시지에 응답했고, 경기도 광주 날씨 질문에 기온이 포함된 답이 왔다. 이 답에는 출처 링크가 없었다. 작업 폴더를 묻자 `/opt/data`라고 답했다. 모델 표기는 `Codex gpt-6-luna`였다.
- `sudo docker restart hermes` 후 당일 질문 내용이 기억에 남아 있고 메시지도 정상 수신했다(사용자 확인).
- 메모리(사용자 출력, 대기 상태 1회 측정): 서버 사용 832Mi, available 1.0Gi, 스왑 사용 52Ki. 컨테이너 338.1MiB(한도 1.861GiB의 17.74%), CPU 0.93%, 프로세스 39개.
- `docker logs`를 `sudo` 없이 실행하면 `permission denied ... docker.sock`이 난다(사용자가 docker 그룹에 없음). gateway 문제가 아니다.
- 공식 문서 확인(2026-11-12, `hermes-agent.nousresearch.com/docs/user-guide/docker`, `/docs/reference/cli-commands`): setup·gateway 명령은 위와 같다. Docker 가이드의 바인드 마운트 DB 손상 경고는 Docker Desktop for Windows 같은 환경 이야기다. `hermes setup`은 `model|tts|terminal|gateway|tools|agent` 하위 명령과 `--quick`(빠진 항목만 묻기) 옵션이 있다. 문서에서 "Quick setup"/"Full setup" 모드 설명은 찾지 못했다.
- 공식 문서(조사 시점 2026-11-11)에 있는 내용:
  - 예약 작업은 gateway가 실행 중이어야 동작한다.
  - gateway는 허용 목록에 없는 사용자를 기본 차단한다.
  - ChatGPT 구독 로그인은 기기 코드 방식을 지원한다.
  - Docker 가이드: 이미지 `nousresearch/hermes-agent`, 상태는 `/opt/data`(호스트 `~/.hermes` 또는 named volume) 한 곳, gateway는 `gateway run`과 `--restart unless-stopped`, 포트 8642는 채팅 플랫폼만 쓰면 선택 사항, Windows 바인드 마운트는 SQLite DB 손상 위험이 있어 named volume 권장, 같은 데이터 폴더로 gateway 컨테이너를 둘 이상 띄우지 않는다.
- 배포 소스(2026-11-13 작성, `Claudecode/project_hermes_test/`): `deploy/compose.yaml`(변수: `AGENT_NAME`, `IMAGE`, `DATA_DIR`, `MEM_LIMIT` 기본 600m, 컨테이너명 `hermes-<name>`), `deploy/hermes-agent.sh`(서버 데이터 `~/.hermes-agents/<name>`, 서버 파일 `~/hermes-deploy/`), `agents/example.env.example`, `targets/example.env.example`, `.gitignore`(`agents/*.env`, `targets/*.env`, `backups/`, 키 파일 제외). `CLAUDE.md` 목적·원칙 절을 새 목적으로 갱신했다.
- PC 검증(직접 실행, 2026-11-13): `bash -n` 통과. `new demo-news test`로 env 생성, `docker compose config` 치환 정상(`hermes-demo-news`, mem_limit 600m). 변수 없으면 필수값 오류. 잘못된 이름 거부, 대상 파일 없으면 오류. 임시 파일은 지웠다. `shellcheck`는 PC에 없어 실행하지 않았다.
- Hermes Slack 문서(2026-11-13, `hermes-agent.nousresearch.com/docs/user-guide/messaging/slack`, 하위 에이전트 조사로 일부는 요약 기반 읽기):
  - Socket Mode라 공개 URL·인바운드 포트 불필요. 토큰은 Bot `xoxb-`와 App-Level `xapp-`(`connections:write`).
  - `hermes slack manifest --agent-view --write`로 매니페스트 생성 후 api.slack.com/apps에 붙여넣기. App Home Messages Tab 활성화 필요, scope·이벤트 변경 후 재설치 필요.
  - 설정은 `hermes gateway setup` 또는 `.env`. 필수 env `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_ALLOWED_USERS`(미설정 시 전부 거부). `SLACK_ALLOWED_CHANNELS`로 채널 제한.
  - cron `deliver: slack` / `slack:<채널ID>` / `slack:<사용자ID>`. 봇 간 메시지는 `allow_bots: mentions` 권장, `all`은 루프 위험.
- X 게시물 URL을 WebFetch로 가져오면 `HTTP 402 Payment Required`, 본문 없음(2026-11-13, 이 PC의 Claude Code 도구 기준).
- X API 공식 문서(2026-11-13, `docs.x.com/x-api/getting-started/pricing`, `/fundamentals/rate-limits`):
  - 구독 없는 종량제(크레딧 선구매). 게시물 읽기 $0.005/건, 사용자 읽기 $0.010/건. 월 300만 건 상한(초과는 Enterprise).
  - UTC 하루 단위 중복 과금 제외(soft guarantee). 지출 한도 설정 가능, 도달 시 다음 주기까지 차단. 사용량은 `GET /2/usage/tweets`.
  - `GET /2/users/:id/tweets`: 앱 10,000회/15분, 사용자 900회/15분.
  - 비용 추정(계산값, 미검증): 10명 × 하루 10건이면 월 약 $15.
- Slack 연결(사용자 확인, 2026-11-13): 서버에서 매니페스트 생성 → Slack 앱 생성(Socket Mode, 토큰 2개) → `hermes` 컨테이너 stop 후 `gateway setup`으로 설정 → start. DM 응답 정상, 채널 초대 후 멘션 응답 정상, 멘션 없는 채널 메시지는 무응답(문서상 기본 동작). 토큰·Member ID 값은 기록하지 않는다.
- `tobi/qmd`(하위 에이전트 조사, 2026-11-13, README 뒷부분은 요약 기반): CLI + MCP 서버 + Claude Code 플러그인, MIT, v2.8.3, Node 22+. BM25·벡터·하이브리드+재순위, 모델은 로컬 GGUF(합계 약 2GB, 최초 HuggingFace 다운로드). 컬렉션 단위 색인, `qmd update` 증분, 갱신 전 훅(`git pull` 등). 기본 임베딩은 영어 최적화, 다국어는 `QMD_EMBED_MODEL`로 Qwen3-Embedding. HTTP 모드는 인증 없음(localhost 전용). Windows 공식 지원 문구는 못 찾음.
- `lucasastorian/llmwiki`(하위 에이전트 코드 조사 + 일부 직접 확인, 커밋 `4d887e8` 2026-11-09, Apache-2.0):
  - 구성: Python MCP 서버, FastAPI API(watcher 포함), Next.js 웹, Chrome 확장. 로컬 모드 필수 외부 키 없음.
  - Ingest: `mcp/tools/guide.py`에 "Discuss key takeaways with the user" 단계가 있으나 README Routine 프롬프트("Find everything added to the workspace since your last run")는 무인 실행을 의도. Ingest 코드엔 LLM 호출 없음, 위키 작성은 연결된 Claude가 MCP 도구로 한다. 지난 실행 마커는 없다.
  - Lint: 20개 점검, 보고만 하고 자동 수정 없음(uncited-source, orphan-page, dangling-link, stale-page 등). 인용은 각주 `[^1]: 파일명, p.N`.
  - 위험: `edit`/`append`가 md·txt 소스를 수정 가능, `delete`가 소스 파일을 unlink(이슈 #93). 링크는 표준 마크다운만 파싱(`[[wikilink]]` 미지원). FTS5 `porter unicode61`라 한국어 조사 붙은 형태 검색에 약할 것(추정). Windows 11 + Claude Code stdio timeout 이슈 #46 open.
  - 직접 확인(코드 읽기): `llmwiki mcp`는 `index.db`가 없을 때만 init 색인하고 `local_server.py`에 watcher가 없다 → MCP 단독으론 새로 pull한 raw가 색인되지 않음. `reindex`는 `document_references`까지 삭제해 반영 기록이 사라짐. CLI 색인(`_index_existing_files`)은 chunk를 안 만들어 FTS 검색 불가(FTS는 `document_chunks` 기준). 로컬 외부 호출은 Mistral OCR(`PDF_BACKEND=mistral`일 때)뿐.
- Hermes 프로필·성격·채널 문서(하위 에이전트 조사, 2026-11-13, 긴 페이지 뒷부분은 요약 기반; `/docs/user-guide/profiles`, `/multi-profile-gateways`, `/features/personality`, `/messaging/slack`, `/docker`):
  - 프로필 = 별도 Hermes 홈(`~/.hermes/profiles/<name>/`, 컨테이너 `/opt/data/profiles/<name>/`). 각자 `config.yaml`, `.env`, `SOUL.md`, 메모리, 세션, 스킬, cron을 가진다. 샌드박스는 아니다.
  - `hermes profile create|list|use|show|rename|delete`, `hermes -p <name> ...`. `--clone`은 config·.env·SOUL·skills·memories를 복사하지만 봇 토큰·allowlist는 복사하지 않는다(`hermes -p <name> setup`으로 따로 설정).
  - `gateway.multiplex_profiles` 기본 true: gateway 하나가 모든 프로필을 서비스. 토큰 하나는 프로필 하나만(중복 시 `duplicate_credential`로 정지). Docker 권장은 "one container hosting all profiles", 같은 데이터 폴더에 gateway 컨테이너 2개 금지.
  - `SOUL.md`는 `HERMES_HOME`에서만 읽고 시스템 프롬프트 맨 앞에 들어간다. 새 세션부터 적용. 프로젝트 규칙은 `AGENTS.md` 권장. `/personality`로 세션 단위 덮어쓰기 가능.
  - Slack 채널 설정(`config.yaml` `platforms.slack`): `allowed_channels`, `channel_prompts`, `channel_skill_bindings`, `free_response_channels`, `require_mention`(기본 true), `strict_mention`, `allow_bots`(none/mentions/all, mentions 권장). `SLACK_HOME_CHANNEL`은 cron·알림용. `group_sessions_per_user` 기본 true(공유 채널에서 사용자별 세션).
- PC 환경(직접 실행, 2026-11-13): Python 3.14.8만 있음, Node v26.13.0, npm 11.20.0, git 2.56.0, uv·gh 없음. llmwiki 의존성 설치 중 `watchfiles==1.1.0`이 Python 3.14 wheel이 없어 소스 빌드(Rust/maturin) 실패. clone과 venv는 세션 스크래치패드에 있어 세션 종료 시 사라진다.
- llmwiki 3.14 실패 원인(직접 확인, 2026-11-16): `api/requirements.txt` 21행 `watchfiles==1.1.0` 고정(2025-06-15 릴리스). PyPI에 cp314 wheel은 Linux·macOS용만 있고 Windows는 cp39~cp313까지 → sdist 빌드에 Rust/maturin 필요 → PC에 `rustc`·`cargo`·`maturin` 없음. `pip download --only-binary=:all:`로 1.1.0은 "No matching distribution", 1.3.0(2026-09-21)은 `cp310-abi3-win_amd64` wheel을 받았다. 다른 컴파일 고정 패키지(asyncpg, cryptography, lxml, pyyaml)는 Windows cp314/abi3 wheel이 있다. `uvicorn[standard]`는 `watchfiles>=0.20`만 요구하므로 1.1.0 고정은 llmwiki 자체 제약이다.
- Linux x86_64(PyPI 메타데이터만 확인): 위 5개 고정 패키지 모두 manylinux x86_64 cp314 또는 abi3 wheel이 있다. 실제 설치·실행은 하지 않았다.
- notebooklm-py(하위 에이전트 조사, 2026-11-16, README·installation·mcp-guide·SKILL.md·PyPI, 긴 문서 뒷부분은 요약 기반): 비공식("undocumented Google APIs", "Not affiliated with Google"), MIT, 0.8.6(2026-10-29), Python ≥3.10. NotebookLM은 2026-07 Gemini Notebook으로 리브랜딩. 인증은 Playwright 로그인/브라우저 쿠키/마스터 토큰. 쿠키는 다른 활성 클라이언트가 있으면 약 10분 내 대체됨, 마스터 토큰은 계정 전체 권한이며 비밀번호 변경 후에도 유지, 설치 문서에 "ToS-grey". 기능: 노트북·소스 추가·`ask`·`source add-research --mode deep`(15~30분+)·오디오/영상/보고서 생성. agent skill(`notebooklm skill install`)과 실험적 MCP(도구 38개) 제공. 소스 수 상한은 계정 등급에 따름(수치 미확인).
- PC 설치(직접 실행, 2026-11-16): `winget install astral-sh.uv` → uv 0.13.8, `uv python install 3.12` → CPython 3.12.16. 기본 `python`은 3.14.8 유지. llmwiki를 저장소 밖 `%USERPROFILE%\llmwiki-local\app`에 clone(커밋 `4d887e8`, 기본 브랜치 `master`), `uv venv --python 3.12` + `uv pip install -r api/requirements.txt -r mcp/requirements.txt` 성공(watchfiles 1.1.0).
- 로컬 위키 시험(직접 실행, 2026-11-16, 작업 폴더 `%USERPROFILE%\llmwiki-local\wiki`, `git init`·`.gitignore`(`.llmwiki/`)만, commit 없음):
  - `llmwiki init`이 색인 후 `✓` 출력에서 `UnicodeEncodeError`(cp949 콘솔). DB는 출력 전에 commit되어 결과 영향 없음. `PYTHONIOENCODING`/`PYTHONUTF8`로 회피.
  - MCP(stdio, 자체 Python 클라이언트): initialize 약 2초, tools/list 14개 0.0초. `read`, `search`(list/references), `create`, `lint` 동작. `create`는 frontmatter를 자동 추가하며 한글 제목은 `"프..."` 이스케이프로 저장(영문은 그대로).
  - 색인: `init`은 chunk를 만들지 않아 raw가 키워드 검색에 안 잡힘. MCP `create`로 만든 위키 페이지는 chunk가 생겨 검색됨. API(`uvicorn main:app`) 기동 시 reconcile이 기존 문서 chunk를 채움. reconcile은 새 파일을 찾지 않으므로 API가 꺼져 있을 때 들어온 파일은 수정 이벤트가 있어야 색인됨.
  - watcher 버그(재현): `domain/watcher.py` `_load_ignore_patterns`가 `.gitignore`를 인코딩 없이 `read_text()` → 한글 주석이 있으면 cp949에서 `UnicodeDecodeError`, 백그라운드 task라 로그 없이 watcher 정지. `PYTHONUTF8=1`로 실행하면 새 파일·수정 파일이 8초 안에 chunk까지 색인됨.
  - 한국어 검색: `샌드박스`·`토큰`·`종량제`는 0건, 조사가 붙은 원문 형태(`샌드박스가`·`토큰은`·`종량제다`)만 일치. `credential`, `allow_bots` 같은 일부 영문 식별자도 불일치(원인 미확인).
  - raw 파일은 MCP 작업 전후 mtime 변화 없음.
- Claude Code MCP 등록(직접 실행, 2026-11-16): `claude mcp add llmwiki-wiki -s local -e PYTHONUTF8=1 -- <venv python> <llmwiki> mcp <wiki>` → `~/.claude.json`의 Aigit 프로젝트 항목, `claude mcp get` `✔ Connected`. 세션 재시작 후 도구 14개 로드(Windows 이슈 #46 미재현). `ping`, `list_knowledge_bases`, `search`(list·search·references), `read`, `create`(`/wiki/entities/x-api.md`), `lint` 정상. 인용한 raw는 Lint의 uncited-source에서 빠짐. 해제: `claude mcp remove llmwiki-wiki -s local`.
- 산출물(2026-11-16): `Claudecode/project_hermes_test/agents/souls/{annie,yomiko,kaguya}.SOUL.md`, `docs/guide.md` 3장 재구성(3-3 단계 0~7·되돌리기, 3-4~3-6).
- HOME PC 환경(직접 실행, 2026-11-16): uv 있음, Python 3.12 없음 → `uv python install 3.12` = 3.12.15. llmwiki를 `%USERPROFILE%\llmwiki-local\app`에 clone(`4d887e8`), `uv venv --python 3.12` + 의존성 설치 성공. ICT PC의 로컬 환경은 이 PC에 없다.
- llmwiki 코드 확인(직접 읽기, `4d887e8`):
  - `mcp/tools/guide.py`: `guide` 도구는 상태 없이 매번 같은 본문(측정 29,626자)을 돌려준다. LLM 대상 문서다(“You are connected…”, `GUIDE_TEXT`는 도구와 단위 테스트에서만 쓰임). 필수 frontmatter `title`·`description`·`date`·`tags`(2개 이상), H1 금지, 허브 `overview.md`, 수동 활동 기록 금지, 원문 1건당 5~15페이지, Ingest에 "Discuss key takeaways with the user" 단계, 사용자 하이라이트(`[matched: note]`)는 원문 주장이 아님.
  - `mcp/local_server.py`: MCP 서버 `instructions`에 "Call the `guide` tool first".
  - `mcp/tools/lint.py`: `title`·`tags` 없으면 오류, `description`·`date` 없거나 태그 2개 미만이면 경고. 시각 요소·H1은 검사하지 않는다.
  - stale(`vaultfs/sqlite.py`, `tools/write.py`): 위키 페이지 X를 쓰면 X를 `links_to`하는 페이지가 stale, stale 페이지를 수정하면 해제. 서로 링크한 페이지는 경고가 계속 생긴다.
  - `read` 도구 설명: glob 읽기를 권장하며 최대 12만 자까지 읽는다.
- 테스트 스크립트(직접 실행): `test/mcp_call.py --list`로 도구 15개와 스키마 확인. `raw_save.py`: 추적 파라미터 제거 후 id `55385d89`, 끝 `/`가 붙은 위키백과 URL은 404 → 트레이스백 대신 `error=fetch_failed` 한 줄로 수정. 한글 제목은 slug가 비어 meta의 영문 `slug`를 받게 수정.
- 색인(직접 재현): MCP만 켠 상태에서는 새 raw가 안 보인다. API(`uvicorn main:app`, `MODE=local`, `WORKSPACE_PATH`, `PYTHONUTF8=1`)를 켜도 기존 새 파일은 찾지 않고, 파일 수정 이벤트(mtime 갱신, 내용 동일)로 색인됐다. API를 켠 상태에서 저장한 2차 raw는 바로 색인됐다.
- Haiku 5.5 테스트(Claude Code 하위 에이전트, 2026-11-16, 알림의 토큰 수 기준):
  - 1차(지침 문서 읽힘, 위키백과 "검색 증강 생성" 원문 14,807자): 애니 53,183토큰·도구 7회·18초, 카구야 80,130토큰·16회·238초, 페이지 3개 생성, Lint 오류 0.
  - 2차(SOUL + 스킬만 읽힘, "환각 (인공지능)" 2,055자): 애니 50,731토큰·9회·27초, 카구야 68,612토큰·29회·146초, 1개 생성·2개 수정(링크 추가), Lint 오류 0·stale 경고 4, uncited 0. 기존 `rag-limitations`와 대상이 다르다고 보고 새 페이지를 만들었다(병합 미발생).
  - 2차 호출 증가 원인(에이전트 보고): `create`·`edit` 인자 이름이 스킬에 없어 오류로 맞춤, 검색 3배. 테스트 방식상 도구 1회 = JSON 쓰기 + Bash로 호출이 2배가 된다.
  - 각주 `raw/2026/11/<파일>, 절` 형식은 Lint `no matching source` 오류, 파일명만 쓰면 해소.
  - 1차 원문 중 각주·참고문헌 이후 꼬리가 6,939자(47%).
  - 하위 에이전트 기록 파일이 0바이트라 턴별 usage는 얻지 못했다. Haiku 5.5 단가($0.10/$0.50 per MTok, claude-api 참조 2026-11-03 캐시)로 환산하면 건당 약 $0.01~0.17(누적값인지 마지막 컨텍스트인지에 따른 범위, 캐시 할인 미반영).
  - 테스트 중 위키 폴더에 `.obsidian/`이 생기고 페이지 4개가 LF→CRLF로 바뀌었다(내용 diff 0). 이 변경은 2차 위키 커밋 `e69f030`에 섞였다. 2차 raw는 `git status`에 M으로 보였으나 내용·줄바꿈 변화 없음.
- Hermes 스킬 문서(하위 에이전트 조사, 2026-11-16, `/docs/user-guide/features/skills` 뒷부분은 요약 기반, `/docs/developer-guide/creating-skills`): 스킬 = `<이름>/SKILL.md` + 선택 `scripts/`·`references/`, agentskills.io 호환. frontmatter `name`·`description`·`version`·`metadata.hermes.tags/category` 등(필수 여부 명시 없음). 본문 권장 구성 When to Use/Quick Reference/Procedure/Pitfalls/Verification. 점진 로딩(`skills_list` → `skill_view`), 스킬별 슬래시 명령, `${HERMES_SKILL_DIR}` 치환, 스크립트는 `terminal` 도구로 실행. 기본 위치 `~/.hermes/skills/`. 에이전트는 `skill_manage`로 스킬을 만들고 고칠 수 있다. 대화 중 추가한 스킬은 다음 메시지부터 반영, 슬래시 명령은 `/reload-skills`.
- qmd README(하위 에이전트 조사, 2026-11-16, 뒷부분 요약 기반): 기본 모델 임베딩 약 300MB + 재순위 약 640MB + 쿼리 확장 약 1.1GB. `QMD_EMBED_MODEL`로 Qwen3-Embedding-0.6B(CJK용) 지정 후 `qmd embed -f`. 기본 로컬 실행에 API 키 불필요. "LLM models stay loaded". RAM 요구량 명시 없음.
- Lightsail 요금(공식 페이지, 2026-11-16): Linux IPv4 $12(2GB), $24(4GB), $44(8GB), 모두 2 vCPU. 시드니는 전송량 허용치가 절반. 리전별 인스턴스 가격 차이는 표기 없음.
- 산출물(2026-11-16, HOME PC): `agents/common/{raw-spec,wiki-rules,README}.md`, `agents/skills/{raw-save,wiki-ingest,wiki-lint-weekly}/`, `test/mcp_call.py`, SOUL 3개 개정(우선순위 절, qmd 사용 구분). 스킬 frontmatter YAML 파싱 확인. 개정 후 지침 분량: 애니 SOUL+스킬 약 2,600자, 카구야 약 3,400자.
- qmd 임베딩 모델 조사(2026-11-18, `tobi/qmd` README·`src/llm.ts` 원문과 HuggingFace API를 직접 읽음, 모델은 실행하지 않고 읽기만):
  - 임베딩 모델은 `QMD_EMBED_MODEL`(`hf:<저장소>/<파일>.gguf`)로 바꾸고, 바꾼 뒤 `qmd embed -f`로 다시 임베딩한다(벡터 비호환). 원격 OpenAI 호환 임베딩 서버도 지정할 수 있다. README가 밝힌 지원 모델군은 embeddinggemma(기본, 영어 최적화, 약 300MB)와 Qwen3-Embedding(119개 언어)뿐이다.
  - 소스: 모델 이름에 `qwen`과 `embed`가 함께 있을 때만 Qwen 형식, 그 외는 embeddinggemma용 접두어(`task: search result | query:`)를 붙인다. 원격 임베딩은 접두어 없음. 기본 모델 3개는 임베딩 약 300MB, 재순위 약 640MB, 쿼리 확장 약 1.1GB. 소스 주석: Qwen3-0.6B Q8의 임베딩 컨텍스트 약 1190MB(VRAM 실측 기준, #799), 모델은 유휴에도 해제하지 않고(`disposeModelsOnInactivity=false`) 컨텍스트만 5분 유휴 뒤 해제.
  - 후보(한국어 특화, 파인튜닝 허용, 오픈소스): KURE-v1(`nlpai-lab/KURE-v1`, bge-m3 파인튜닝, MIT, GGUF `mykor/KURE-v1-gguf`·`Bingsu/KURE-v1-Q8_0-GGUF`), BGE-m3-ko(`dragonkue/BGE-m3-ko`, Apache-2.0, GGUF `CHKH01/BGE-m3-ko-GGUF`). KURE README 표에서 BGE-m3-ko가 원본 bge-m3보다 약간 높음(top1 recall 0.524 대 0.518). `Day1Kim/*-Korean`은 한국 건설 기준 문서로 학습해 제외(라이선스 표기·GGUF 없음).
- qmd 서버 시험(직접 실행, 서버 시각 2026-11-17 23:46~2026-11-18 00:44, Qwen3-Embedding-0.6B와 KURE-v1 Q8_0, 위키 4문서·28KB):
  - 서버 시작 상태: 메모리 1905MB 중 available 839MB, 스왑 19MB 사용, 2 vCPU(AVX2·AVX512), 디스크 여유 48G, OOM 이력 없음. 호스트에 node가 없어 `node:22-slim` 컨테이너에 `@tobilu/qmd` 2.8.3을 설치(앱 857MB). 방법: 별도 컨테이너, `--memory-swap`=한도(스왑 없음), uid 10000, 1초 간격 cgroup anon/file·호스트 available·스왑 기록과 자동 중단.
  - 첫 실행(한도 1GB, 병렬도 기본): Qwen3 74초·anon 최대 889MB·컨테이너 1023MB(한도 도달)·호스트 available 최저 417MB. KURE 51초·anon 735MB·available 최저 600MB. 둘 다 OOM 없음, 중단 기준 미발동.
  - **부작용:** Qwen3 첫 실행 중 호스트 스왑이 316MB→586MB로 늘었고 `hermes` 컨테이너 보고 메모리가 503MB→약 105MB로 줄었다(컨테이너 스왑은 없는데 호스트가 다른 프로세스를 스왑으로 보냄). 서비스는 계속 Up이었다. 이후 시험에서는 스왑 증가가 없었다(`pswpout` 변화 거의 없음). 응답 지연은 측정하지 않았다.
  - 서빙(HTTP 상시 서버, 한도 700MB, 병렬도 1, `--network none`, `vec` 쿼리·`rerank:false`):

    | 항목 | Qwen3-0.6B | KURE-v1 Q8_0 |
    |---|---|---|
    | 첫 쿼리 | 9.8초 | 8.5초 |
    | 연속 쿼리(warm) | 약 3.85초 | 약 0.33초 |
    | 연속 쿼리 anon / file | 466MB / 약 230MB | 413MB / 약 280MB |
    | 유휴 6분 후 anon | 199MB로 감소 | 약 380MB(감소 거의 없음) |
    | 유휴 후 첫 쿼리 / 다음 | 6.9초 / 3.9초 | 7.5초 / 1.0초 |
    | 유휴 후 anon 최대 | 528MB | 545MB |
    | 호스트 available 최저(서빙) | 740MB | 758MB |

    쿼리 11개의 1순위 문서가 두 모델에서 같았다(문서 4개라 변별력 약함). 가중치는 anon이 아니라 file 페이지로 올라갔다(크기가 모델 파일과 비슷, mmap 정황).
  - 검증 시험(KURE, 한국어·영어 질의 12개, `lex` 대 `vec`): `lex`는 정답 문서 11/12(응답 약 70ms), 조사가 붙은 "옵시디언으로"만 0건. `vec`는 정답 문서가 12/12 top-3에 있었지만(4문서라 의미 약함) 1순위 정답은 7/12 — "Dataview", "PARA", "discernment", "옵시디언으로", "지식베이스" 같은 정확 용어는 `lex`가 맞히고 `vec`는 1순위를 놓쳤다. `lex`+`vec` 융합(`rerank:false`)은 정답 1순위(461ms).
  - 임베딩 한도: 700MB·병렬도 1에서는 OOM 종료(`oomkilled=true`, anon 655MB), 1GB·병렬도 1에서는 31초에 통과(anon 684MB, 호스트 available 최저 606MB). 서빙은 700MB로 충분(anon 약 410MB).
  - 평문 호출 동작(재순위·확장 모델 파일 없음, 네트워크 차단): REST `POST /query`에 평문 `query`는 즉시 400("Missing required field: searches"). REST `searches`에서 `rerank` 미지정(기본 true), MCP `/mcp`의 `query` 도구(평문 또는 `searches`)는 모두 120초 타임아웃으로 멈췄고 오류 없음. 컨테이너 메모리 변화 없음, OOM 아님, 이후 정상 `vec` 쿼리 254ms로 응답.
  - 정리(2026-11-18): 시험 컨테이너 4개와 5번째 `qmd-vsrv`, `/srv/qmd-test`(앱·모델·인덱스·로그), `~/qmd-scripts`, 이미지 `node:22-slim`을 서버에서 삭제했다. 수치는 위 표가 유일한 기록이다(로그 원본 삭제). `hermes`·`llmwiki-api`는 계속 Up, 디스크 9.7G 사용(시험 전과 같음).

## 3. 미확인 항목(이전 목적·초기 조사 관련)
- 구독 플랜 자격 조건, 사용량 한도와 차감 방식(문서에 "not currently documented"로 표기됨).
- `gpt-6-luna`가 mini급 저비용 모델인지.
- 크레딧 $100이 Lightsail 요금에 적용되는지, 만료일, Lightsail 3개월 무료 혜택 여부(비공식 출처에만 있음).
- 중지한 Lightsail 인스턴스에 요금이 계속 부과되는지와 고정 IP 요금 조건. 서버의 실제 중지·삭제 여부.
- Free plan 상태에서 계정 spend limit 설정이 있는지와 동작.
- 서버에서 ChatGPT 구독 사용량이 차감되는지, 구독 로그인을 서버에서 쓰는 것이 약관상 문제없는지. 서버 응답은 오지만 로그인 방식과 차감은 확인하지 못했다.
- 서버의 OpenAI Native Web Search가 실제로 호출됐는지와 날씨 답의 정확도(출처 링크가 없었다).
- 서버·컨테이너 시간대. 서버 재부팅 후 컨테이너 자동 복구. 예약 작업 동작.
- 서버 `docker logs`의 내용(에러 반복 여부). 예약 작업·긴 대화 중 메모리 최대치.
- 서버 월 요금이 실제로 $12 정액인지(공식 요금 페이지 미확인).
- 서울 대비 시드니 리전의 지연 시간과 가격 차이.
- 영수증 사진·파일 처리 가능 여부.
- Haiku 테스트 알림의 토큰 수가 누적 사용량인지 마지막 컨텍스트 크기인지. 건당 실제 비용. Hermes(gpt-6-luna)에서의 토큰 규모.
- 테스트 중 생긴 `.obsidian/`·CRLF 변경의 원인(Obsidian으로 연 것으로 추정).
- 이 세션 PC를 HOME PC로 기록했다. llmwiki 환경이 없던 점으로 판단한 추정이다.
- `hermes desktop` 동작 여부.
- Hermes 컨테이너 볼륨 백업·이전의 공식 절차.
- `hermes-agent.sh`의 SSH·scp·`docker compose run/up` 실제 동작(서버 미실행). `SSH_KEY`에 `~`를 쓰면 풀리지 않을 수 있다.
- 서버 2GB에 인스턴스 여러 개를 띄울 때 작업 중 최대 메모리(대기 1회 약 340MiB만 측정).
- 한 Slack 워크스페이스에 앱 여러 개로 인스턴스를 따로 운영하는 공식 절차. Docker gateway에서 Slack 사용 시 별도 요구사항.
- Hermes CLI 배치 실행 가능 여부, 수집용 일회성 컨테이너 실행 가능 여부. (2026-11-17 해소: 컨테이너 안 git commit 가능·push는 키가 없어 불가(의도), `web_extract`는 OpenAI Native 백엔드에서 불가 — §2)
- 서버 Hermes 웹 도구로 X에 접근되는지(Claude Code 도구에서는 402).
- X API: Developer Console의 실제 단가, 빈 응답 과금 여부, 요청당 최대 결과 수, 답글·리트윗 제외 옵션, 개인·비상업 용도 약관(`developer.x.com` 제품 페이지는 402로 못 읽음).
- 다른 SNS(Reddit, Bluesky, YouTube 등) 수집 경로와 약관·비용.
- llmwiki를 Python 3.12에서 설치·실행했을 때의 동작 전부(Windows tools/list 이슈 #46, watcher 색인, 무인 Ingest, 한국어 검색, Obsidian 표시). Claude Code의 MCP elicitation 지원(delete 승인), opendataloader의 Java 필요 여부, 이슈 #47 최신 상태.
- qmd의 한국어 검색 품질과 Windows 동작.
- Slack 채널·스레드 단위 세션 분리. (2026-11-17 해소: 프로필 기능 지원, `slack manifest`·`docker run ... gateway setup`의 `-p` 적용, SOUL 변경은 재시작 없이 `/new`로 반영, `install`로 맞춘 SOUL을 컨테이너가 읽음 — §2)
- llmwiki: Obsidian 표시(한글 frontmatter 이스케이프, 각주 인용), 웹 UI(`npm install` 미실행), Linux·Python 3.12 서버에서의 동작, 한국어 검색 개선 방법, 영문 식별자 검색 불일치 원인, 무인 Ingest 품질.
- notebooklm-py: 실제 설치·로그인, 서버 헤드리스 인증 유지, 소스 수 상한(`docs/quota-limits.md` 미확인), 약관상 개인 용도 허용 범위.

# AI 창 재사용과 명시적 대화 재개

> 버전 0.5 | 2026-11-02 | Codex 경로 탐색 개선. 과거 연결 시험의 후속 결과는 최신 작업기록 참조

## 경계와 저장

[시작 제어 모듈](../../tools/agent_sessions.psm1)은 프로젝트 경로·역할별로 대화를 기록하고 현재 herdr 상태와 대조한다. 로컬 기록은 관리 프로젝트의 `.local/agent-sessions/`에 저장하며 Git 전송 대상이 아니다. 경로 해시로 프로젝트를 구분하고 master=Codex, producer=Claude로 역할을 고정한다. 창 번호는 과거 관측값이며 명령 전송 대상의 현재 근거로 쓰지 않는다.

사용자가 전달한 내부 검증 결과는 source=user_report로 저장했다. 실제 작업 경로·herdr 세션·역할·대화 ID·당시 창·근거 설명·기록 시각을 보관한다. Desktop이 직접 검증한 live_verified로 바꾸지 않는다. 기록 시각은 내부 시험의 정확한 실행 시각을 뜻하지 않는다. 원문 도구 출력 파일은 제공되지 않았다. 스킬 등록 확인은 스킬의 실제 작업 수행 검증이 아니다.

기본 틀의 `.project-management.json`은 개설 정보만 맡으며 그 안의 빈 conversation_sessions를 실제 대화 연결로 사용하지 않는다. 실행 대화 기록의 원본은 위 로컬 저장소 하나다. 다른 PC·폴더 이동 시 기존 경로를 임의 치환해 재개하지 않고 위치·대화 존재를 다시 대조해야 한다.

## 시작 판정

| 현재 상태 | 동작 |
| --- | --- |
| 같은 프로젝트·AI 종류의 창 1개, idle/done/working/blocked | reuse 반환. 창 유지, 명령·프롬프트 전송 없음 |
| 경로 불명·unknown·시작 중·판독 생략·동일 역할 여러 창 | 차단. 추측해 새 창을 만들지 않음 |
| 기존 창 없음, 검증 근거가 있는 대화 기록 있음 | 명시적 ResumeSaved가 있어야 정확한 ID로 재개 |
| 기존 창 없음, 대화 기록 없음 | 구독 인증 후 현재 빈 셸에서 새 AI 시작 |
| 저장 대화와 현재 응답의 UUID ID가 충돌 | 재개 옵션과 무관하게 차단. 실행 중 대화를 교체하지 않음 |

### 창 유지와 대화 ID 검증의 분리

상태 확인기 출력 schema_version은 2다. 기존 action은 시작기 제어용으로 유지하고 decision에 다음을 추가했다.

| 필드 | 의미 |
| --- | --- |
| window_check.status | reusable: 기존 창 유지 가능, absent: 창 없음, unconfirmed: 상태·경로·목록 등의 확인 부족 |
| window_check.preserve_existing | 기존 창을 종료·교체하지 않는 정책. 창이 있다는 주장과 구분 |
| conversation_check.status | matched / mismatch / unverified / no_saved_record |
| conversation_check.source | 실제 UUID를 제공한 herdr_snapshot 또는 none |
| conversation_check.observed_id | 현재 herdr 응답에서 확인한 UUID. 없으면 null |
| conversation_check.saved_id / saved_source | 비교할 저장 ID와 과거 기록의 근거 출처. 현재 관측값으로 사용하지 않음 |
| automatic_prompt_allowed | 항상 false. 이 검사는 새 작업 전송을 허가하지 않음 |
| restore_verified | 항상 false. ID 비교·재개 계획은 실제 복원 성공 시험이 아님 |

현재 창이 유지 가능해도 agent_session이 null이면 action=reuse, window_check.status=reusable, conversation_check.status=unverified, source=none으로 반환한다. path 참조나 올바르지 않은 UUID도 불일치로 단정하지 않고 미확인으로 표시한다. 올바른 현재 UUID가 저장값과 다르면 window_check는 창 유지 가능 여부를 보존하면서 action=blocked·conversation_check.status=mismatch를 반환한다. matched여도 working·승인 대기 중인 창에 새 작업을 전송하지 않는다.

저장 기록만 조회하는 기본 모드는 verification.window와 verification.conversation을 not_checked로 표시한다. 이 모드는 현재 창·대화를 조회하지 않는다. 검사기는 CODEX_THREAD_ID를 자동 보조 근거로 사용하지 않는다. 현재 환경변수가 어느 창·프로젝트의 것인지 대조하는 기능 없이 GPT 값을 다른 창이나 Claude의 실시간 근거로 확대하지 않기 위해서다. 별도로 사용자가 보고한 환경변수·과거 /status 결과는 이 검사기의 실시간 판정과 구분한다.

현재 살아 있는 창을 재사용할 때는 새 대화 ID를 기록에 자동 덮어쓰지 않는다. 새 대화로 시작한 뒤 그 ID를 추측해 저장하지 않으며, 실제 ID와 프로젝트·역할을 확인한 근거로 Save-RoleRecord를 호출해야 한다. 저장은 배타 잠금과 임시 파일의 원자적 교체를 사용하고 이전 연결 기록을 history에 보존한다.

동일 프로젝트·역할의 시작 과정은 배타 파일 잠금으로 직렬화하고 직접 시작한 AI가 종료될 때까지 유지한다. 프로세스가 끝나면 파일 핸들이 해제되므로 남은 빈 lock 파일을 삭제할 필요가 없다. 잠금을 얻지 못하면 다른 시작을 진행하지 않는다. 이 잠금은 이 시작기를 이용하는 실행에만 적용하며 수동 CLI·다른 도구의 동시 실행까지 통제하지 않는다.

## 실행 연결과 조회

[마스터 시작기](../../tools/start_master.ps1)와 [Claude 시작기](../../tools/start_claude.ps1)는 기존 구독 인증 검사를 유지한다. herdr 내부에서 시작 제어를 수행하고, 재개 시 각각 `codex resume <정확한 ID>`와 `claude --resume <정확한 ID>`를 사용한다. `--last`·`--continue`로 임의의 최근 대화를 선택하지 않는다. 재개 실패 시 새 대화로 자동 대체하지 않는다. 초기 작업 프롬프트는 자동 제출하지 않는다.

두 시작기에 `-ResumeSaved`가 추가됐다. 재개해도 Claude 전용 문서·설정·보류 자료 보호는 기존 시작기 경로로 다시 적용한다. `-CheckOnly`는 인증·설정 검사이며 실제 창 재사용·복원 시험이 아니다. Claude의 `-InspectOnly`는 도구 없는 별도 로딩 검사이며 재개와 함께 사용할 수 없다.

[상태 확인기](../../tools/check_agent_sessions.ps1)는 기본 실행에서 저장된 근거만 출력한다. `-Live`는 실제 herdr 내부에서만 현재 상태를 읽어 역할별 판정을 반환한다. 읽기 전용이며 AI 시작·명령 입력·모델 호출을 하지 않는다. 판정은 그 순간의 결과이며 나중의 시작을 허용하는 인증표가 아니다. 실제 시작기는 잠금을 잡은 뒤 새로 조회한다.

HERDR_ENV·HERDR_PANE_ID·HERDR_SESSION이 없는 Desktop에서는 현재 세션 조회·제어를 하지 않는다. 환경변수를 위조하지 않는다. 이번 개발에서 조회한 API schema와 CLI 도움말은 정적 명령 형식이며 현재 세션 상태를 조회한 것이 아니다. 지원 형식은 확인한 herdr 0.9.5 / protocol 22로 제한하고 다른 버전은 재검증 전 차단한다.

### Codex 업데이트·PC 변경 시 시작기 — 2026-11-02

`start_master.ps1`은 `codex_launcher.psm1`로 실행 파일을 선택한다. 명시한 `-CodexPath` → PATH의 독립 CLI(.exe/.cmd) → 앱의 버전별 실행 파일 순서다. 앱 후보는 LOCALAPPDATA와 USERPROFILE/AppData/Local 및 PATH에서 확인하며 파일 수정 시각 기준으로 최신 후보를 선택한다. 이는 설치 관리자의 활성 버전 판정이 아니므로 잘못된 후보는 버전 검사 오류로 멈추고 명시 경로로 확인한다. 이전 PATH에 남은 앱 버전이 독립 CLI나 최신 앱 후보보다 우선하지 않는다.

- `-CheckOnly`: 실행 파일·버전·ChatGPT 로그인·herdr 파일 존재와 선택 모드를 표시한다. herdr 상태 조회·AI 시작·프롬프트 전송은 하지 않는다.
- `-LoginCodex`: 명시적 ChatGPT 로그인만 수행한다. 자동 로그인·자동 설치는 하지 않는다.
- `-NoDaemon`: 사용자가 선택한 경우에만 공유 서버 없이 실행한다. 기본은 일반 실행이며 실패 후 자동 재시도하지 않는다.
- `-CodexPath`: 비표준 설치의 실제 .exe/.cmd 경로를 명시한다. 경로가 없거나 실행 불가하면 다른 후보로 조용히 바꾸지 않는다.
- 기존 역할 판정·중복 시작 방지·명시적 대화 재개 조건은 유지한다. 사용자/시스템 PATH를 수정하지 않으며 실행 중 임시 PATH와 작업 폴더는 종료 시 복원한다.

사용자 절차는 [PC별 시작 가이드](../../guide_docs/herdr_Codex_PC별_시작_가이드.html)를 따른다. 이미 실행 중인 Codex가 있다는 사용자 확인과 변경된 시작기로 실제 대화 화면까지 연 검증은 구분한다. 이 변경은 다른 프로젝트의 시작기 일반화나 기존 창 교체가 아니다.

## 검증과 남은 범위

### 시작 화면의 요청과 내부 처리

시작 화면의 ‘관리 AI 연결·재개 요청’은 [요청 도구](../../tools/workspace_request.psm1)로 `.local/workspace-connect/request.json`을 저장하고 관리 herdr 세션을 연다. 요청에는 project-management 경로·세션·정확한 요청 ID·저장 대화 재개 선택이 들어간다. Desktop은 창을 조회하거나 명령을 보내지 않는다. 기존 ‘관리 환경 열기’는 연결 요청 없이 화면만 연다. 신규 프로젝트의 자동 연결은 이번 대상이 아니다.

[내부 실행기](../../tools/connect_workspace_agents.ps1)는 기본 실행에서 요청과 현재 역할별 판정을 읽기 전용으로 출력한다. 실제 처리에는 herdr 내부에서 `-Apply`를 지정한다. 요청 파일을 저장하는 것만으로 수신기가 시작되지는 않는다. 아래 수신기를 herdr 내부에서 실행한 동안에는 새 요청이 자동 전달된다. OS 예약·시스템 시작 등록은 하지 않았다.

현재 좌우 창을 유지하는 검사에는 `-Apply -ReuseOnly`를 사용한다. 두 역할 모두 reuse일 때 요청 처리 기록만 갱신하고, 역할이 없어지거나 상태가 바뀌면 창 생성·인증·시작 없이 중단한다. 기본 실행의 읽기 전용 계획 확인과 달리 이 모드는 로컬 요청 상태를 변경한다.

- 양쪽 창이 있으면 둘 다 보존하고 요청을 processed로 표시한다. processed는 요청 처리 종료이며 AI 복원·전체 자동화 완료가 아니다.
- 없는 역할이 있으면 변경 전에 해당 역할의 기존 시작기로 구독 인증을 검사한다. 인증 실패 시 새 창을 만들지 않는다.
- 역할을 시작하기 직전에 상태를 다시 확인한다. 새 역할 창만 오른쪽에 생성하고 기존 창의 포커스·배치를 임의 변경하지 않는다. 마스터가 있으면 그 오른쪽에 Claude를 생성한다. 둘 다 없으면 기존 제어 창을 남기고 새 GPT, 그 오른쪽 Claude를 생성한다. 기존 Claude만 있는 배치까지 자동 재정렬하는 기능은 포함하지 않는다.
- 새 창에서 실제 전경 프로세스가 PowerShell 셸 하나인지 확인한 뒤에만 시작기 명령을 넣는다. 다른 셸·불명 상태는 차단한다. 시작기 자체도 기존 역할 재조회·중복 시작 잠금을 수행한다.
- 시작 명령을 전달했다는 응답과 실제 AI 창 감지를 구분한다. AI가 감지돼도 대화 ID 미확인이면 그대로 표시하며 restore_verified는 false다. 작업 프롬프트는 보내지 않는다.
- 요청 처리에 배타 잠금을 사용한다. pending 요청의 중복 클릭은 같은 ID를 반환한다. 변이 전에 상태를 저장하고, 중간 실패·시간 초과는 uncertain으로 남겨 자동 재전송하지 않는다. 이미 만든 창을 임의 종료하지 않는다. uncertain/processing 상태의 수동 해제는 실제 창·명령 전달 여부를 확인한 별도 복구 작업으로 남긴다.

[요청·경계 검사](../../tools/test_workspace_request.ps1) 9개와 기존 역할 판정 35개를 통과했다. 내부 실행기의 실제 herdr 생성·전달·감지 경로는 실행하지 않았으며, 해당 전체 경로를 모의 시험으로 검증했다고 주장하지 않는다. 구문 검사는 통과했다.

### 자동 요청 수신

[수신기](../../tools/watch_workspace_requests.ps1)는 실제 project-management herdr의 별도 PowerShell 7 창에서 실행한다. 기존 GPT·Claude 입력창에 셸 명령을 보내거나 그 프로세스를 교체하지 않는다. Desktop에서는 수신기를 시작하지 않으며 HERDR_ENV를 위조하거나 외부의 분리 프로세스로 현재 창을 제어하지 않는다.

- 기본 실행은 2초 간격으로 로컬 요청 파일만 확인한다. 새 pending 요청이 있을 때만 내부 연결 실행기를 `-Apply -ReuseOnly`로 호출한다. 대기 중에는 모델·herdr 상태를 반복 조회하지 않는다.
- 같은 요청의 전달 이력을 실행 전에 저장한다. 전달 이후 중단된 요청은 자동 재전송하지 않는다. 실행 전 실패는 blocked, 실행 중 결과 미확인은 uncertain으로 남긴다. 새 버튼 클릭은 blocked/processed 이후에만 새 요청을 만들며 uncertain/processing/claimed 요청은 확인 없이 대체하지 않는다.
- 수신기별 배타 잠금으로 중복 실행을 막는다. 실행기에는 ExpectedRequestId를 전달하여 확인한 요청과 다른 요청을 처리하지 않게 한다.
- 기본 모드는 기존 창 유지다. 새 역할 시작은 `-AllowStartMissing`로 수신기를 명시 실행할 때만 허용한다. 이 옵션은 아직 실사용 검증하지 않았으며 현재 세션을 유지하는 단계에서 사용하지 않는다.
- 시작 화면은 로컬 요청·수신기 상태 파일을 읽어 대기·처리·완료·차단·결과 불명확을 표시한다. 90초 안의 수신기 상태는 ‘최근 응답 있음’으로만 표현하며 현재 프로세스 생존이나 실제 복원 성공으로 단정하지 않는다.
- 수신기 종료는 해당 서비스 창의 Ctrl+C다. 강제 종료 시 마지막 상태 파일이 남아도 시간이 지나면 화면에서 최근 응답 없음으로 표시한다. 기존 AI 세션을 종료하지 않는다. 권한 오류는 실행 정책을 완화해 우회하지 않으며, 실제 내부 실행에서 필요한 권한을 확인한다.

[수신 처리 모듈](../../tools/workspace_listener.psm1)과 [모의 검사](../../tools/test_workspace_listener.ps1)를 추가했다. 요청 없음·실행 전 전달 이력·한 번만 처리·완료 요청 무시·중단 후 재전송 방지·사전 실패/중간 실패 구분·모드 표시·외부 실행 차단 10개 검사를 통과했다. 실행기는 모의 콜백으로 대체했고 실제 herdr 조회·제어·AI 호출은 하지 않았다. 요청·경계 9개 회귀 검사와 변경 스크립트 구문 검사도 통과했다.

[모의 시험](../../tools/test_agent_sessions.ps1)은 저장·역할/프로젝트 분리·정확한 ID 선택·중복/불명 상태 차단·동시 기록 보호·외부 실행 차단을 검사한다. 실제 HERDR_ENV를 변경하지 않고 모의 snapshot만 판정 함수에 제공한다. 모의 검사는 현재 창 조회나 AI 호출을 하지 않는다.

사용자 전달 근거로 이전 버전의 내부 Live 조회는 PowerShell 7.6.5에서 최초 권한 오류 후 동일 검사 성공(exit 0), master=reuse/working, producer=reuse/idle였다. 두 역할의 agent_session은 null이었으므로 당시 결과를 실시간 대화 ID 일치 검증으로 해석하지 않는다. master 환경변수 일치는 사용자 별도 확인, producer ID는 이전 /status 근거이며 이번 실시간 재확인은 아니었다. 원문 로그 파일은 제공되지 않았다.

v0.2 변경 출력은 사용자 전달 근거로 PowerShell 7.6.5에서 내부 Live 검사 성공(exit 0)했다. schema_version=2, 두 역할 reuse/reusable 및 unverified/none, observed_id=null, automatic_prompt_allowed=false, restore_verified=false를 확인했다고 보고받았다. agent_session 자체는 그 출력에 없었으므로 그 검사에서 직접 null을 확인한 것으로 기록하지 않는다. Desktop에서 재검증하지 않았다.

v0.3의 `-Apply -ReuseOnly` 실행은 사용자 전달 근거로 최초 권한 오류 후 동일 명령 성공(exit 0), processed, master w3:p1·producer w3:p2 preserved였다. 두 역할의 대화 ID는 unverified/observed_id=null, restore_verified=false, prompts_sent=0이며 새 AI 시작·메시지 전송·창 생성/종료·재시작 없이 로컬 요청 상태만 변경했다고 보고받았다. 이 성공 시험은 반복 대상이 아니다.

v0.4 수신기는 Desktop에서 실행하지 않았다. 실제 내부 기동 후 화면 버튼→수신→ReuseOnly 자동 처리 확인은 남아 있다. 실제 창 생성·빈 셸 시작·대화 재개, 종료 후 복원, 폴더 이동 시 재연결은 계속 미검증이다. 현재 좌우 창을 종료하지 않았다. 다른 프로젝트 일반화와 신규 프로젝트 실사용 검증은 사용자 추후 수행 조건을 따른다.

Claude 훅 비활성화와 herdr 공식 자동 복원의 호환성을 해결했다고 주장하지 않는다. 이번 명시적 재개는 공식 훅 자동 복원을 대체하는 완료 판정이 아니다. 가이드 제작·자료 전송 보류, 추가 API 비용·재시작·commit·push 금지를 유지한다.

## 변경 이력

- 0.1: 프로젝트·역할별 대화 저장, 창 재사용·중복 시작 방지, 명시적 재개 연결.
- 0.2: 창 유지와 대화 ID 검증을 별도 필드로 분리. UUID 부재·불일치·저장 기록 없음·저장 기록 전용 조회를 구분하고 모의 검사를 보강.
- 0.3: 관리 화면의 연결 요청 저장·중복 방지와 herdr 내부의 역할 보존·누락 역할 시작 실행기 추가. 실제 시작·복원 미검증을 유지.
- 0.4: 내부 요청 수신기와 GUI 상태 표시, 전달 이력·중복 수신 방지, 기본 ReuseOnly 처리 추가. 내부 수신기 실제 기동은 미수행.

- 0.5: Codex 경로 선택·버전 점검·로그인·선택적 NoDaemon, 환경 복원과 PC별 안내 추가.


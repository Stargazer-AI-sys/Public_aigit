# 자동화 기반 구현 검증

> 버전: 0.3 | 확인일: 2026-10-27 (한국 시간) | 전체 자동화 상태: 미완료
>
> 아래 본문은 초기 설치·재시작 전 검증 및 상대경로 재검증 당시의 근거다. 이후 Docker 컨테이너 시험 통과, 사용자 보고의 herdr 전달·회수 성공, Hermes 설치, 가이드 화면 승인·기획 완료, Claude 운영 폴더 분리·로딩 확인은 [최신 관리 작업기록](../04_records/management_log.md) 마지막 인계를 따른다. 아래 ‘미완료’ 목록을 현재 할 일로 그대로 반복하지 않는다. 가이드 정식 제작은 사용자 보류이며 전체 자동화는 여전히 미완료다. v0.3에서는 최신 인계 연결만 추가했고 과거 시험 근거는 변경하지 않았다.

## 실제 결과

| 항목 | 확인한 결과 | 근거 |
| --- | --- | --- |
| 로컬 상태·증거 도구 | 24개 시험 통과, 종료 코드 0. 호스트 Python에서 실행 | [시험 로그](automation-evidence/unit-tests.txt), [소스 해시](automation-evidence/source-hashes.json) |
| 별도 GPT QA | 초기 18개 시험과 실패 QA·재작업 재현 확인. 최종 24개와 구분 | [독립 QA 원문](automation-evidence/gpt-qa-initial.md) |
| Claude 교차 검토 | Pro 구독에서 정적 읽기 검토. 수정 후 로컬 엔진 PASS, 남은 필수 결함 없음 | [최초 검토](automation-evidence/claude-review-initial.md), [수정 후 검토](automation-evidence/claude-review-final.md) |
| 설치 파일 | herdr 0.9.5, Claude Code 2.1.308 공식 SHA256 검증 및 버전 출력 확인 | [재현 가능한 설치기](../../tools/install_local_agents.ps1) |
| 로그인 | Codex ChatGPT 로그인, Claude authMethod=claude.ai·subscriptionType=pro 확인 | 이 작업의 CLI 직접 실행. 인증정보는 저장하지 않음 |
| 가이드 제작 | Claude 세션 0152c8ed-f404-4c27-8d1a-50f4f3b276aa에서 초안 작성. GPT 내용 대조 | [가이드 초안](../../guide_docs/AI_작업_요청과_재개_가이드.html) |
| 가이드 구조 | simple-user-guide 공유 원본 적용. HTML 지정 1회, exit 0. 상대 링크 3·목차 4·ID 4, 문제 0·제외 0 | 기존 check_project_docs.ps1 직접 실행 |
| 가이드 화면 | 일반 PC 및 390px 설정의 좁은 화면에서 확인. 실제 문서폭/내용폭 모두 375px, 페이지 가로 넘침 없음 | [PC](automation-evidence/guide-desktop.png), [좁은 화면](automation-evidence/guide-mobile.png) |
| Docker·WSL 설치 | WSL 3.0.3 MSI exit 0, 필수 기능 각각 3010(재시작 필요), Docker 4.97.0 사용자 설치 exit 0 | [Windows 설치 결과](automation-evidence/platform-install-result.json), [Docker 설치 로그](automation-evidence/docker-install-log.txt) |

## 수행한 시험

초기 검증 당시 호스트 프로젝트 폴더에서 `WORKFLOW_TEST_TMP`를 `.local/test-tmp` 절대경로로 지정하고
`python -B -X utf8 -m unittest discover -s tools -p test_workflow.py -v`를 실행했다.
초기 기본 임시폴더 권한 오류로 시험 준비가 실패했으며 프로젝트 내부 임시폴더로 바꾼 후 실행했다.
이는 당시 수행 사실이며 현재 권장 절차가 아니다. 이후 사용자 지시에 따라 상대경로를 우선하고, 경로 실패는 원인을 해결하며 권한 부족은 사용자에게 권한을 요청하도록 [운영 기준](../02_design/management_workflow.md)을 변경했다. 과거 기본 임시폴더의 권한 문제를 해결한 것으로 판정하지 않는다.
16개 초기 시험 → 별도 QA의 필수 결함 수정 후 18개 → Claude 지적 보완 후 24개가 통과했다.
기존 도구의 전체 회귀 시험은 변경하지 않았으므로 반복 실행하지 않았다.

주요 검증은 중복 요청 방지, 선행 단계·자기 승인 차단, 검토 후 변경 감지, 실패 QA 기록,
후속 승인 무효화·재작업, 반복 결함 재평가, 증거 스냅샷, 인증 문자열 복사 차단,
중단·재개, 경로 탈출·동시 쓰기 잠금이다. 도구는 신고된 모델 신원을 인증하거나 검토 내용의 진실성을 판정하지 않는다.

Claude 최초 검토의 필수 결함은 로컬 엔진에 반영하고 재검토했다. 가이드 기획 G1(선행 초안의 취급 불명확)은
[실행계획](../workflows/guide-prototype/01-planning/plan.md)에 '대표 화면 확인용 선행 초안'으로 정정했다.
이 정정의 Claude 재검토와 사용자 대표 화면 승인은 아직 하지 않았다. 따라서 가이드 프로토타입은 완료하지 않는다.

## 상대경로 기준 재검증 — 2026-10-27

프로젝트 루트에서 아래 상대경로 설정으로 기존 시험을 재실행했다. 24개 시험 통과, 종료 코드 0, 실행 시간 10.324초를 직접 확인했다. 소스는 변경하지 않았고 기존 시험 로그·소스 해시는 초기 검증 증거로 유지한다. 이번 실행에는 권한 오류나 추가 권한 요청이 없었으며, 초기 기본 임시폴더의 권한 문제 해결을 뜻하지 않는다.

```powershell
$env:WORKFLOW_TEST_TMP = '.local/test-tmp'
python -B -X utf8 -m unittest discover -s tools -p test_workflow.py -v
```

## 설치와 검증을 구분

- Docker 최초 사용자 설치는 VirtualMachinePlatform 미활성으로 exit 1이었다. DISM `/norestart`로 WSL·가상 머신 기능을 설치하고 WSL MSI를 `/norestart REBOOT=ReallySuppress`로 설치했다. 이후 Docker 사용자 설치는 성공했다.
- 사용자는 재시작 없이 설치까지만 진행하고 검증은 작업기록에 남기도록 요청했다. 재시작·Docker 시작·컨테이너 실행을 하지 않았다. Docker 첫 실행의 약관 확인도 아직 하지 않았다.
- Docker 파일은 공식 사이트에서 받고 Docker Inc 유효 서명을 확인했다. WSL MSI는 공식 릴리스 SHA256과 대조했다. 배포 주소는 [Docker 공식 설치 안내](https://docs.docker.com/desktop/setup/install/windows-install/)와 [Microsoft WSL 릴리스](https://github.com/microsoft/WSL/releases)에서 확인했다.
- 시작기의 `forced_login_method=chatgpt`는 [공식 인증 문서](https://learn.chatgpt.com/docs/auth)에 있는 설정이다. 시작기 밖의 임의 CLI 실행·사용자 설정까지 통제하는 과금 방화벽은 아니다. Claude CLI 출력의 비용 추정치를 실제 API 청구로 해석하지 않는다.
- 가이드 미리보기의 최초 로컬 접속은 시간 초과였고 제한 밖의 localhost 미리보기 서버로 재시도해 화면을 확인했다. HTTP 테스트 서버는 가이드 폴더만 제공했으므로 문서 링크 존재 검증은 로컬 구조 점검 결과를 사용했다. 외부 서비스에 공개하지 않았다.

## 미완료와 다음 검증

1. 사용자 재시작 뒤 Docker Desktop 시작·필요한 약관 확인, WSL2 상태, `docker compose run --rm verify` 확인. 이미지 첫 다운로드와 실제 격리 동작을 구분한다.
2. herdr 안에서 마스터 시작, Claude 작업 전달·상태·결과 회수 시험. 현재 Claude 교차 호출은 Codex가 CLI로 수행했으며 herdr 연결 시험이 아니다.
3. Hermes 설치·구독 인증·MCP 연결의 무추가비용 경로 확인. pstack은 필요한 기능의 호환성 확인 후 선택 도입.
4. 가이드 대표 화면 사용자 검토와 기획 재검토 후 정식 제작·별도 QA·wiki 검토를 기록한다. 현재 HTML은 검토용 초안이다.
5. 실제 모델 사용 가능 목록·난이도별 선택, 자동 전달·수집·판정 루프, 화면 실패 증거, 중단 후 실제 에이전트 재개를 연결한다. 로컬 도구 시험을 이 항목들의 완료로 대체하지 않는다.

최신 재개 위치는 [관리 작업기록](../04_records/management_log.md)이다. Git commit·push는 수행하지 않았다.

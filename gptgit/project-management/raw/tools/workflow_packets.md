# 워크플로 입력 안내

도구는 로컬 기록·검사기이며 LLM을 직접 호출하지 않는다. 사용자가 아니라 마스터가 입력 파일을 준비한다.
모든 입력 경로는 프로젝트 상대경로, 문자 인코딩은 UTF-8이다. 프로젝트 루트에서 실행하고 `--root`를 지정할 때도 `--root .`처럼 현재 폴더 기준 상대경로를 사용한다. 실패 시 절대경로로 바꾸지 않고 [경로·권한 진단 기준](../docs/02_design/management_workflow.md)에 따라 원인을 해결한다.
`docs/workflows/guide-prototype/00-request/input.json`은 실제 승인 요청으로 시작한 실행의 입력이다.
아래의 세션·모델·증거 이름은 형식 예시이며 실제 수행 결과로 바꿔야 한다.

```powershell
python -X utf8 tools/workflow.py init --id guide-prototype --packet docs/workflows/guide-prototype/00-request/input.json
python -X utf8 tools/workflow.py status --id guide-prototype
```

상태 변경 공통 형식은 `COMMAND --id 실행ID --stage 단계 --packet 입력파일 --op 작업ID`이다.
같은 작업 재시도는 같은 작업ID와 동일 입력을 사용한다. 같은 ID에 다른 입력은 거절한다.

## 단계별 입력

| 명령 | JSON 필수 항목 |
| --- | --- |
| start | session, provider, model, task. wiki에서 Claude 대체 시 fallback_reason |
| submit | session, spec_version, summary, self_test, limitations 배열, artifacts 경로 배열 |
| review | session, provider, model, spec_version, summary, verdict(pass/fail), criteria(ID 배열), defects 배열, suggestions 배열, evidence 경로 배열 |
| complete | role(master), session, reason |
| block | reason |
| resume | role(master), session, reason. 일반 차단 해소 후 이전 상태로 복귀 |
| reassess | role(master), session, reason, resolution. 반복 결함 재평가 후 현재 회차 카운터 초기화, 전체 이력 유지 |
| reopen | role(master), session, reason. 지정 단계와 이후 승인 무효화·재작업. 과거 기록·증거 스냅샷 유지 |

제공자 값은 gpt·claude·hermes다. 기획은 GPT→Claude 검토, 제작은 Claude→GPT 검토,
QA는 별도 GPT→GPT 또는 Claude 검토, wiki는 Hermes(불가 시 사유를 기록한 Claude)→GPT 검토다.
이 값은 신고된 역할이며 도구가 인증한 모델 신원은 아니다.

```json
{
  "session": "실제-기획-세션-ID",
  "provider": "gpt",
  "model": "실제-실행-모델",
  "task": "R1~R4에 대응하는 가이드 실행계획 작성"
}
```

검토 필수 결함은 `{"id":"D1","reason":"누락 이유","reproduce":"재현 절차"}` 형태다.
선택적 제안은 suggestions에 둔다. pass는 필수 결함 0개일 때만 허용한다.
QA submit에는 scenarios 배열도 필요하다. 정상(normal)·예상 오류(expected_error)를 포함하고 모든 완료 조건을 덮어야 한다.

```json
{
  "id": "QA-1",
  "kind": "normal",
  "criterion": "R1",
  "conditions": "시험 버전·환경·입력",
  "expected": "예상한 결과",
  "actual": "직접 확인한 결과",
  "passed": false,
  "evidence": ["실제-증거-상대경로"]
}
```

실패 QA도 제출해 기록한다. 실패가 남으면 pass·완료는 차단한다. 제작 결함이면 마스터가 02-development를 reopen한다.
증거 원본은 제출 시 내용 해시로 저장한 스냅샷을 함께 보존한다. 완료 후 원본이 달라지면 완료 판정은 무효다.
변경 전 reopen으로 재작업을 기록한다. 새 명세는 기존 승인 기록을 덮지 않고 새 실행 ID로 시작한다.

## 검사·복구

`report`는 JSON 완료 보고를 출력한다. `timeline`은 state.json에서 색인을 복구한다.
state.json을 직접 수정하거나 .lock을 실행 중에 지우지 않는다. 프로세스가 비정상 종료하여 잠금이 남으면
마스터가 잠금 파일의 PID와 실제 프로세스 종료를 확인한 뒤 해당 잠금 파일만 제거한다.
raw에는 제출한 JSON만 자동 수집되며 채팅·CLI 원문은 별도 캡처가 필요하다. 인증정보는 제출하지 않는다.

## 로컬 시험과 Docker

```powershell
$env:WORKFLOW_TEST_TMP = '.local/test-tmp'
python -B -X utf8 -m unittest discover -s tools -p test_workflow.py -v
```

프로젝트 루트에서 실행한다. 임시 시험 자료는 지정 폴더 안에서 생성·정리된다. 이 경로는 재현 가능한 시험 설정이며 권한 오류가 발생하면 다른 위치로 우회하지 않고 필요한 권한을 요청한다. Docker가 준비된 환경에서는 `docker compose run --rm verify`로 같은 시험을 실행한다.
이미지를 처음 받는 네트워크 접근과 Docker 설치는 별도 준비다. 현재 Docker 실행은 미검증이다.

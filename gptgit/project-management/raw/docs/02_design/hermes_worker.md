# Hermes 제한형 기록 worker

> 버전: 0.1 | 최종 수정: 2026-10-28 | 범위: ENV-01 작업 전달·결과 회수

[역할 기준](../00_rules/roles.md)의 Hermes 운영 역할을 [hermes_worker.py](../../tools/hermes_worker.py)로 호출한다. 마스터가 명시적으로 준비한 작업을 새 세션에 전달하고 기록 요약 또는 wiki **초안**을 회수한다. 원본 수정·최종 승인·독립 QA·전체 프로토타입 완료 판정은 수행하지 않는다. 승인 상태 관리와 분리되어 기존 `state.json`·timeline을 수정하지 않는다.

## 입력과 실행

프로젝트 루트에서 실행한다. Python 3.12 이상 표준 라이브러리로 전달기를 실행하고 구독 검사는 기존 Hermes 설치의 Python·인증 모듈을 사용한다. 현재 설치 경로는 코드의 `RUNTIME`에 고정되어 있으며 다른 PC·업데이트 시 실제 설치를 확인하여 변경해야 한다. 자동 설치·기본 모델 변경은 없다.

```powershell
python -X utf8 tools/hermes_worker.py --packet docs/workflows/실행ID/worker-packet.json --validate-only
python -X utf8 tools/hermes_worker.py --packet docs/workflows/실행ID/worker-packet.json
python -X utf8 -m unittest discover -s tools -p test_hermes_worker.py
```

명시 packet 예시(예시 경로는 실행 전 실제로 작성해야 한다):

```json
{
  "run_id": "environment-setup",
  "task_id": "ENV-01-summary",
  "purpose": "record-summary",
  "instruction": "다음 합성 기록을 요약하라: 연결 시험 통과. 독립 QA와 전체 프로토타입은 미검증.",
  "sources": []
}
```

`purpose`는 `record-summary` 또는 `wiki-draft`다. 기본 `sources: []`이면 프로젝트 문서를 자동으로 읽어 보내지 않고 packet과 고정 역할 지시만 전달한다. 마스터는 비밀정보와 보류 자료를 inline instruction에 복사하지 않는다. 알려진 인증 패턴 검사는 임의 형식 비밀정보 탐지를 보장하지 않는다.

현재 추가 source 허용 목록은 `README.md`, `docs/00_rules/roles.md`, `docs/02_design/automation_workflow.md` 세 파일이다. 각 항목은 `{"path":"README.md","sha256":"실제 원본 전체 바이트 SHA-256","start_line":1,"end_line":10}` 형식으로 고정해야 하며 해시가 달라지면 전송하지 않는다. 1부터 세는 시작·끝 행을 모두 포함하며 파일당 최대 200행만 보낸다. 목록 확대는 별도 검토·코드 변경이 필요하다. 가이드 HTML, `guide-prototype` 실행 기록, 상위 가이드 스킬 원문은 허용 목록에 없다. 파일 참조는 승인 범위를 넓히지 않는다.

## 호출·비용 경계

매 호출 직전에 기존 Nous 인증으로 `/models`를 조회하여 `openai/gpt-6-luna`의 `billing_mode=subscription`을 확인한다. 실패·누락·다른 과금 모드이면 모델 요청을 보내지 않는다. 인증값·원문 인증 응답은 기록하지 않으며 예외 메시지도 수집하지 않는다. 조회 시 기존 인증 모듈의 정상 토큰 갱신은 가능하다. 새 로그인·유료 API 대체·모델 fallback은 구현하지 않는다.

Hermes 명령은 `chat --safe-mode --provider nous --model openai/gpt-6-luna --toolsets '' --reasoning none --max-turns 1 --oneshot --quiet --format stream-json --query-file ...`로 고정한다. shell을 거치지 않아 빈 toolsets 인자가 유지된다. 새 세션만 만들고 resume를 사용하지 않는다. isolated 빈 작업 폴더에서 실행하며 기존 사용자 세션을 종료하지 않는다. 이 제한은 OS 수준 격리를 뜻하지 않는다. 설치 버전에 따른 실제 세션 도구 목록 검증이 필요하며 CLI 플래그만으로 도구 없는 실행을 입증했다고 보고하지 않는다.

구독 사전 확인은 그 시점의 제공자 응답 근거이며, 이후 계정 상태 변경이나 제공자 과금 정책을 강제하는 장치는 아니다. 런타임 설정·버전 변경 시 연결과 실제 도구 목록을 다시 확인한다.

## 결과·중단·재전송

`docs/workflows/<run_id>/raw/hermes-<task_id>/`를 원자적으로 생성하여 작업을 선점한다. 보류 실행 `guide-prototype`에는 기록하지 않으며 연결·junction 경로도 거절한다. 같은 ID가 이미 있으면 성공·실패·중단 여부와 무관하게 다시 보내지 않는다. 각 파일은 exclusive-create로 한 번만 작성하며 기존 파일을 덮어쓰지 않는다. 이는 도구의 덮어쓰기 방지이며 운영체제의 변조 불가 저장을 의미하지 않는다.

- `00-claimed.json`: packet·request 해시, 모델, source 해시, 시간.
- `packet.json`, `request.txt`: 명시 입력과 실제 전달 내용.
- `01-subscription.json`: 모델·구독 과금 사전 확인.
- `02-dispatched.json`: 호출 인자와 전달 시작 시간.
- `stdout.jsonl`, `stderr.txt`: CLI 원문 출력. 알려진 인증 패턴이 있으면 저장하지 않고 누락 사실을 outcome에 남긴다.
- `result.txt`, `99-outcome.json`: 회수된 초안, 실제 세션 ID·토큰 정보·결과 해시 또는 차단/실패/불명확 상태.

종료 코드 0에 더해 유일한 terminal result, 성공 상태, 비어 있지 않은 세션 ID·본문을 확인한다. 도구 실행 이벤트가 나타나면 성공으로 취급하지 않는다. `returned_draft`는 전달·회수 성공을 뜻하며 내용 검토 합격이나 프로젝트 완료를 뜻하지 않는다. 마스터가 원문·해시·출력 내용을 검토한 후 기존 승인 절차로 넘긴다.

180초 제한은 해당 CLI 자식만 대상으로 하며 별도 gateway 작업 종료를 보장하지 않는다. timeout·오류·중단 후에는 실제 세션을 확인한다. 기존 receipt를 삭제하여 재전송하거나 자동 반복하지 않는다. 재시도 필요성·실제 요청 도달 여부·원래 작업 근거를 마스터가 확인한 뒤 새로운 명시 작업 ID로 전달한다. 동시에 같은 packet을 요청하면 최초 선점만 실행한다.

## 검증 범위

[오프라인 시험](../../tools/test_hermes_worker.py)은 합성 packet과 가짜 호출로 정상 회수, 승인 상태 보존, 중복 방지, 구독 검사 실패, timeout, source 변경·비허용 경로, 인증 패턴, 결과 오류를 확인한다. 실제 Hermes 연결 시험과 별개다. 전체 프로토타입·교차 제공자 검토·독립 QA는 [자동화 워크플로](automation_workflow.md)의 별도 완료 조건을 따른다.

2026-10-28 오프라인 시험 13개 통과 후 부모 마스터가 합성 packet으로 실제 호출을 수행했다. [회수 결과](../workflows/environment-setup/raw/hermes-ENV-01-hermes-smoke/result.txt)는 `HERMES_WORKER_OK`, [outcome](../workflows/environment-setup/raw/hermes-ENV-01-hermes-smoke/99-outcome.json)은 `returned_draft`다. 입력 1,293·출력 10·총 1,303토큰이며 승인 판단은 `not_performed`다. [구독 사전 확인](../workflows/environment-setup/raw/hermes-ENV-01-hermes-smoke/01-subscription.json)과 [실제 호출 인자](../workflows/environment-setup/raw/hermes-ENV-01-hermes-smoke/02-dispatched.json)를 원문으로 보존했다.

실제 세션 `local-b543eb32945c1ab5d2271c8742548ab765a57eba07a23cdb5ed5fc4d468e0b65`를 로컬 `state.db`에서 읽기 전용으로 대조했다. `sessions.tool_names`가 참조하는 `system_prompts` 레코드는 `{"tools":[],"version":"0.22.5"}`, `tool_call_count=0`, `parent_session_id=null`, 모델은 `openai/gpt-6-luna`였다. 이 실행의 실제 도구 목록이 빈 목록임을 확인했다. DB의 `billing_mode`는 null이므로 과금 확인 근거는 DB가 아닌 호출 직전 구독 조회 결과다.

[명시 packet](../workflows/environment-setup/raw/hermes-ENV-01-hermes-smoke/packet.json)의 `sources=[]`와 [전달 요청](../workflows/environment-setup/raw/hermes-ENV-01-hermes-smoke/request.txt)을 대조했다. 실제 저장된 system prompt에서도 프로젝트 규칙 제목·관리 프로젝트명·보류 가이드명·`guide-prototype` 표지가 검출되지 않았다. 이는 이 합성 실행의 입력·도구 제한 확인이며 모든 버전의 자동 문맥 수집 부재를 보장하는 일반 검증은 아니다. 실제 기록 요약의 내용 품질, 독립 QA, 전체 프로토타입 완주는 별도 검증 대상으로 남는다.

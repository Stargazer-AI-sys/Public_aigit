---
name: process-debug
description: Toggle process_debug On or Off for an approved project workflow and append a compact per-response summary of task sessions, referenced document ranges and observed or estimated usage. Use for process inspection, not for changing task approval or billing settings.
---

# 프로세스 점검

> 버전: 0.1 | 2026-10-28 | 프로젝트 전용 공유 원본

사용자 명령은 `process_debug On` / `process_debug Off`다. `precess_debug`는 같은 요청의 오타로 이해한다. 이 스킬의 식별자는 `process-debug`다.

## 활성화와 집계

- [점검 도구](../../tools/process_debug.py)를 프로젝트 루트에서 실행한다. `python -X utf8 tools/process_debug.py --help`와 필요한 명령의 도움말만 확인한다. 기존 실행 ID를 재사용하며 On/Off는 실행 단위로 유지한다. 다른 실행에 자동 확대하지 않는다.
- `on/off/status --run 실행ID`로 상태를 다룬다. 사용자 요청 하나마다 고유 response ID를 지정하고, 활성화 중 `bind`로 세션 별칭·실제 세션 ID·작업명세 Task ID·제공자를 연결한다. Task ID가 없으면 아직 계획 미분해라고 표시하고 과거 명세 번호를 꾸며내지 않는다.
- 시작·종료에 `snapshot`을 수집한다. Codex는 공식 사용량 이벤트가 연결돼 있으면 우선 사용하고 그렇지 않으면 해당 세션의 JSONL token_count만 읽는다. 다른 제공자는 확인 가능한 사용량만 `--manual` 입력으로 전달한다. 세션 전체 대화나 인증정보를 점검 파일에 복사하지 않는다.
- 문서 조회에는 `read`로 해당 세션과 필요한 줄 범위·절 제목·읽는 이유를 연결한다. 제목 검색 후 필요한 절만 읽으며, 전체 작업기록을 점검 목적으로 다시 읽지 않는다. 일반 도구로 조회한 자료는 자동 수집되지 않았음을 표시한다. 출력이 잘렸다면 요청 범위 전체를 모델이 받았다고 표현하지 않는다.
- 부모 대화 이력을 복사하지 않는 새 담당 세션에 목표·Task ID·기존 결정·관련 원본의 절·쓰기 범위·보류·완료 조건·debug 상태를 전달한다. 세션 종료 전 결과·근거·미해결 사항을 받는다. 상세 원문은 기존 raw/에 연결하고 마스터에는 요약을 반환한다.

## 답변에 붙이는 결과

- On일 때 답변 마지막에 `report --run 실행ID --response 응답ID` 결과에서 **세션 / Task / 참조 문서·절 / 사용 규모**만 간략히 정리한다. 완료·실패·대기 중 작업을 모두 포함한다. 표현 형식은 프로토타입 검증에서 조정할 수 있다.
- Off면 점검 요약을 붙이지 않는다. 기존 작업 대화·인계·실행·검토 근거와 raw/timeline/state 기록은 계속 유지한다. Off에서 발생한 작업을 나중에 On으로 바꾸어 측정된 것처럼 소급 작성하지 않는다.
- 입력·캐시 입력·출력 토큰과 현재 컨텍스트를 구분한다. 캐시는 입력의 일부, 추론 토큰은 제공자에 따라 출력의 일부이므로 다시 합산하지 않는다. 누적 사용량의 시작/끝 차이만 해당 기간의 사용량으로 보고하고, 리셋·소스 변경·동일 세션 중첩 집계·수집 누락은 제한으로 남긴다.
- 컨텍스트는 최근 관측값 및 관측 최대값이지 순간별 실제 최대값이 아니다. 구독 전체 사용률 변화는 다른 채팅이 섞일 수 있어 이 Task 비용으로 환산하지 않는다. 문서 단독 기여 비용이나 정확한 금액은 추정하지 않는다. 적음/중간/많음은 잠정적인 작업 규모 지표이며 근거와 추정 여부를 보존한다.
- 수집 불가 항목은 `미측정`으로 둔다. 마지막 모델 호출의 사용량이 아직 도착하지 않았다면 종료 시점의 관측 범위를 명시한다. 점검 자체의 사용량도 숨기지 않는다.

기존 역할·기록 책임·재개 조건은 [자동화 워크플로](../../docs/02_design/automation_workflow.md)를 따른다. 읽기 기록은 이해의 증거가 아니므로 결과에 어떤 결정·판단의 근거로 사용했는지 짧게 연결한다. 스킬 설치·대화 목록 등록·전체 자동수집 완료는 별도로 확인해야 한다.

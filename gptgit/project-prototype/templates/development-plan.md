# 개발기획서 양식

> 양식이며 기획 검토·실행 완료 근거가 아니다.

- 기준 작업명세서 ID·버전·경로:
- 설계 선택과 요구사항 대응:
- 인터페이스·데이터·실패 처리:

| Task | 요구사항 | 담당 역할 | 입력 파일·범위 | 출력·쓰기 파일 | 의존 Task | 완료·시험 조건 |
| --- | --- | --- | --- | --- | --- | --- |
| 작성 필요 | | | | | | |

- 병렬로 분리 가능한 Task와 단일 파일 소유자:
- Codex 기획 통합 담당:
- Claude 기획 검토 결과·수정 회차·마스터 판정:
- 개발·독립 QA 세션 분리와 고정 산출물 버전:
- QA 시험용 출력 파일(`.local/qa/<task_id>/` 하위 명시 파일만, 입력·원본과 분리):
- 반복 결함 재평가 조건:
- 문서화 입력·출력과 마스터 근거 대조:
- 인계·중단·재개·중복 요청 확인:

담당자는 이 문서의 지정 Task와 관련 소스로 작업한다. 누락 입력은 마스터에게 요청하며 전체 기록 탐색으로 임의 복원하지 않는다. 실제 세션 ID는 관측 후 기록한다.

Task packet의 `session.provider`는 master/planner/qa=`codex`, planning-reviewer/developer=`claude`, documenter=`hermes`로 지정한다. 실제 ID는 관측 전 `null`이다. planning-reviewer·qa의 `write_scope`는 빈 목록이며, QA만 별도 `test_write_scope`에 `.local/qa/<task_id>/` 하위 시험 출력 파일을 지정할 수 있다. 입력 파일 덮어쓰기는 금지한다. Hermes 문서 초안은 `docs/workflows/<run>/drafts/<file>`에만 쓰며 원본 반영은 마스터가 맡는다.

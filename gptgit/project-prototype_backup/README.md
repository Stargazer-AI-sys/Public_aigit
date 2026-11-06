# 자동화 프로세스 프로토타입

> 버전 0.2 | 2026-11-04 | 개선된 프로세스를 독립적으로 적용·시험하는 프로젝트

사용자와 확정한 작업명세서를 바탕으로 기획·개발·검증·문서화를 수행한다. 이 폴더에는 적용할 프로세스, 자체 실행 도구와 양식, 이 프로젝트에서 수행한 작업의 근거만 둔다.

## 시작과 문서 책임

| 문서 | 역할 |
| --- | --- |
| [AGENTS](AGENTS.md) | 승인·행동·기록 경계 |
| [프로세스 적용 조건](docs/requirements.md) | 실행에 필요한 입력과 수락 기준 |
| [실행 설계 기준](docs/development-plan.md) | Task 분해·역할·입출력·검토 설계 |
| [프로세스](docs/workflow.md) | 기획 검토·개발 QA·문서화 순서 |
| [컨텍스트와 담당 운영](docs/context-and-agents.md) | 최소 자료 전달·병렬 작업·인계 |
| [실행 환경](docs/runtime.md) | 이 프로젝트의 CLI·herdr 연결 |
| [도구 목록](docs/tool-inventory.md) | 포함된 도구와 지원 범위 |
| [작업기록](docs/records/work_log.md) | 자체 작업의 현재 상태·다음 행동 |
| [wiki](wiki/index.md) | 설명과 근거 탐색 |

새 작업은 [작업명세서 양식](templates/work-spec.md)으로 합의하고 [개발기획서 양식](templates/development-plan.md)으로 실행을 설계한다. 사용자 창구는 마스터이며 담당 실행·전달·회수도 마스터가 수행한다.

docs/workflows에는 실행별 상태·증거를, docs/records에는 짧은 최신 인계를 둔다. tools·tests·templates는 실행 도구·시험·입력 양식이다. config에는 이 프로젝트의 실행 환경만 설정한다. 실제 연결과 전체 루프의 완료는 자체 실행 근거로 판정한다.

# 프로젝트 도구 목록

> 버전 0.2 | 2026-11-04 | 현재 포함된 도구의 책임과 한계

| 도구 | 책임 | 한계 |
| --- | --- | --- |
| [start_role.ps1](../tools/start_role.ps1) | 마스터·기획·검토·개발·QA 역할 시작과 구독 검사 | CheckOnly는 인수 구성만 확인. 실제 CLI·인증·도구 적용 별도 확인 |
| [dispatch_task.py](../tools/dispatch_task.py) | Task 검사·herdr 신규 pane 전달·중복 선점 방지 | submitted_unverified는 접수. 자동 결과 회수·재사용 판단은 미구현 |
| [task_packet.py](../tools/task_packet.py) | 필수 입력·경로·역할 제공자·쓰기 범위 검사 | 사용자 승인·실제 모델·독립성은 인증하지 않음 |
| [workflow.py](../tools/workflow.py) | 실행 상태·증거·재평가·중복 operation 관리 | 모델을 호출하거나 루프를 자체 실행하지 않음 |
| [check_structure.py](../tools/check_structure.py) | 필수 파일·Markdown 상대 링크 검사 | 내용 품질·실제 연결·화면 품질은 판정하지 않음 |

tests에는 원장·packet·dispatcher 시험이 있다. 각 변경의 실제 시험 결과는 해당 실행 근거로 기록한다. [원장 입력 방법](../tools/workflow_packets.md)을 따른다.

Hermes adapter는 아직 포함되어 있지 않다. 문서화 역할 계약과 초안 경로만 정의되어 있다. 실제 호출·구독 확인·응답 회수·중복 요청 처리를 구현·검증하기 전에는 문서화 자동 연결 완료로 표시하지 않는다.

# 프로젝트 도구 목록

> 버전 0.4 | 2026-11-06 | 현재 포함된 도구의 책임과 한계

| 도구 | 책임 | 한계 |
| --- | --- | --- |
| [start_role.ps1](../tools/start_role.ps1) | 마스터·기획·검토·개발·QA 역할 시작·공유 모델 검사·구독 검사 | CheckOnly는 모델 정책과 인수 구성을 확인. 실제 CLI·인증·도구 적용 별도 확인 |
| [dispatch_task.py](../tools/dispatch_task.py) | Task 검사·herdr 새 탭의 root pane 시작·중복 선점 방지 | 모델 확인 전 Task 미전달. submitted_unverified는 시작 명령 접수. 자동 결과 회수·재사용 판단은 미구현 |
| [task_packet.py](../tools/task_packet.py) | 필수 입력·경로·역할 제공자·쓰기 범위 검사 | 사용자 승인·실제 모델·독립성은 인증하지 않음 |
| [workflow.py](../tools/workflow.py) | 실행 상태·증거·재평가·중복 operation 관리 | 모델을 호출하거나 루프를 자체 실행하지 않음 |
| [check_structure.py](../tools/check_structure.py) | 필수 파일·Markdown 상대 링크 검사 | 내용 품질·실제 연결·화면 품질은 판정하지 않음 |

tests에는 원장·packet·dispatcher 시험이 있다. 각 변경의 실제 시험 결과는 해당 실행 근거로 기록한다. [원장 입력 방법](../tools/workflow_packets.md)을 따른다.

Hermes adapter는 아직 포함되어 있지 않다. 문서화 역할 계약과 초안 경로만 정의되어 있다. 실제 호출·구독 확인·응답 회수·중복 요청 처리를 구현·검증하기 전에는 문서화 자동 연결 완료로 표시하지 않는다.


## 위키 편집 도구

[check_wiki.py](../skills/wiki-editor/scripts/check_wiki.py)는 명시한 지식 문서의 YAML·허용값·날짜·출처·상대 경로·H1·코드 펜스·구조 도식 존재를 읽기 전용으로 검사한다. [스키마](../skills/wiki-editor/references/schema.md)가 단일 형식 기준이고 [회귀 시험](../skills/wiki-editor/scripts/test_check_wiki.py)은 임시 fixture에서 정상·예상 결함을 확인한다. 실행기는 [실행 환경](runtime.md)을 따른다.

기존 check_structure.py의 기본 프로젝트 구조 점검은 유지한다. 새 검사기는 외부 URL 접근·앵커·Mermaid 문법/렌더링·사실/최신성·중복/상충을 판정하지 않는다. 두 도구의 검사 대상·완료 의미를 구분한다.

## 변경 이력

| 날짜 | 버전 | 내용 |
| --- | --- | --- |
| 2026-11-06 | 0.3 | 위키 형식 검사기·회귀 시험·기존 구조 검사와의 경계 연결 |
| 2026-11-06 | 0.4 | 모델 검사와 새 탭 시작·확인 후 전달 경계 |

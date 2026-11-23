---
updated: 2026-11-18
status: current
sources: [../../tools/dispatch_task.py, ../../tools/start_role.ps1, ../../tools/task_packet.py]
---
# 담당 실행 기능

마스터가 입력·쓰기 범위와 모델을 지정하면 dispatcher가 검사하고 별도 담당 탭을 준비한다. 시작기는 초기 사용자 프롬프트 없이 CLI를 연다. 실제 모델·권한 확인 뒤 Task를 한 번 전달한다. `submitted_unverified`는 시작 접수이며 작업 성공이 아니다.

기획·QA·위키는 Codex 담당, 기획 검토·개발은 Claude다. QA와 기획 검토는 원본을 수정하지 않는다. `.local/dispatch`의 영수증과 해시는 같은 Task 중복 시작을 막는다. 파일별 범위 검사가 OS 수준 접근 격리는 아니므로 실제 변경은 마스터가 확인한다.

2026-11-09 기록상 Claude 시작·모델 확인·Task 전달·응답 회수 시험이 완료됐다. 상세 시험 자료는 2026-11-18 사용자 요청으로 삭제했다. 자동 결과 수집·세션 재사용 판단·Hermes 연결·전체 개발 프로세스 완주는 미완료다. 이번 문서 정리에서는 실제 연결을 재시험하지 않았다.

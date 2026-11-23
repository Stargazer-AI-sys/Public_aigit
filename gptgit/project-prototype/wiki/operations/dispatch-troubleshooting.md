---
updated: 2026-11-18
status: current
sources: [../../tools/dispatch_task.py]
---
# 담당 연결 문제 해결

- 응답이 불명확하면 기존 pane·세션의 도달 상태부터 확인한다. 같은 시작·Task를 자동 재전송하거나 ID를 바꿔 중복 방지를 피하지 않는다.
- 새 pane 정보가 미완성인 경우 dispatcher는 최대 세 번 조회한다. pane ID·셸·프로세스·작업 폴더 불일치는 정상 준비로 취급하지 않는다.
- herdr의 pane run은 exit 0과 정확히 빈 stdout일 때 접수로 처리한다. 조회 명령에는 JSON이 필요하며 잘못된 JSON·공백 출력·실패 종료를 성공으로 간주하지 않는다.
- PC를 옮기면 실행 경로·구독·실제 herdr 맥락을 확인한다. `HERDR_ENV=1`만 수동 설정해 내부 실행으로 위장하지 않는다.

실제 시작에 필요한 설정은 [실행 환경](../../docs/runtime.md)에 있다. 요청한 연결 문제만 확인하며 전체 프로세스 시험을 추가하지 않는다.

# 독립 로컬 QA 결과

검증일: 2026-10-27 (한국 시간)
담당: 별도 GPT 세션 /root/qa. Claude 교차 검토 또는 실제 서비스 연결 검증 아님.
검토 대상: tools/workflow.py, tools/test_workflow.py, tools/start_master.ps1, compose.yaml, docs/02_design/automation_workflow.md.

## 실행 결과

- Python unittest 18개 통과, 종료 코드 0 (수정 전 16개 별도 통과 후 발견 결함에 맞춰 18개 재실행).
- 추가 독립 재현: 실패 QA 시나리오 제출 기록, 실패 QA pass 검토 차단, 마스터 reopen으로 개발/하위 단계 재검토, 과거 실패 QA 기록 보존, 재개 뒤 소스 수정·제작 시작 모두 통과.
- 소스 파일 직접 변경 없음. 시험은 .local/qa-tmp 하위 임시 파일만 사용.

## 발견 및 수정 확인

1. 최초 구현은 passed:false QA 제출을 거절하여 실패 증거가 기록되지 않음. 부모 수정 후 실패 제출은 기록되고 통과 승인은 차단됨을 확인.
2. 최초 구현은 개발 완료 뒤 QA 결함을 발견해도 수정 재개 경로가 없었음. 부모가 reopen을 추가한 뒤 개발 revision, 하위 단계 waiting 및 실패 이력 보존을 확인.

## 별도 확인 필요

- 마스터 시작기의 구독 전용 인증 가드: 최초 검토 시 Codex 존재만 검사. 이후 부모 변경 여부는 이 보고 시점에 미검증.
- 과거 증거 파일은 경로/해시 참조이며 덮어쓰기 시 원래 바이트를 복원할 수 없음. 회차별 별도 경로 또는 증거 스냅샷이 필요.
- raw 하위폴더 외부 junction 쓰기 가능성은 정적 검토 사항. 시험 환경의 junction 생성이 권한 오류로 거절되어 재현하지 못함.
- Docker 실행, 브라우저 화면, herdr 내 작업 전달, Claude/Hermes 인증·실제 호출은 미검증.

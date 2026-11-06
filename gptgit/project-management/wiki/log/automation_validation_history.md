---
type: concept
tags: [이력, 자동화, 검증]
created: 2026-11-05
updated: 2026-11-05
confidence: medium
source_status: reviewed
status: historical
sources:
  - ../../raw/docs/03_verification/automation_validation.md
  - ../../raw/docs/03_verification/automation-evidence/gpt-qa-initial.md
  - ../../raw/docs/03_verification/automation-evidence/claude-review-final.md
  - ../../raw/docs/03_verification/automation-evidence/unit-tests.txt
  - ../../raw/docs/workflows/environment-setup/timeline.md
  - ../../raw/docs/workflows/environment-setup/raw/hermes-ENV-01-hermes-smoke/result.txt
  - ../../raw/docs/04_records/management_history_2026-10-13_2026-11-02.md
  - ../../docs/04_records/management_log.md
---

# 2026-10-27~28 자동화 검증 이력

이 페이지는 당시 시험과 검토를 시간과 출처별로 묶은 기록이다. 자동화 운영은 현재 관리 프로젝트의 기능이 아니며, 과거 결과를 현행 환경의 성공이나 전체 프로토타입 완주로 보지 않는다. 판정의 일반적인 차이는 [과거 검증의 판정 범위](../operations/automation_validation.md), 현재 보류와 프로젝트 역할은 [최신 인계](../../docs/04_records/management_log.md)에 있다.

## 10월 27일: 로컬 원장과 독립 검토

호스트 원장 시험은 최초 16개, 별도 GPT QA가 발견한 필수 결함을 고친 뒤 18개, 이후 Claude 검토 지적을 반영한 최종 24개로 발전했다. **18개와 24개는 서로 다른 실행**이다. GPT QA는 실패 QA 증거가 제출되지 않던 문제와 개발 재개 경로 부재를 재현하고 수정 후 확인했다. junction은 당시 생성 권한이 없어 재현하지 못했다. [별도 GPT QA 원문](../../raw/docs/03_verification/automation-evidence/gpt-qa-initial.md), [초기 최종 24개 로그](../../raw/docs/03_verification/automation-evidence/unit-tests.txt)

Claude 교차 검토는 코드를 바꾸지 않은 정적 검토였고 직접 시험을 재실행하지 않았다. 수정 후 로컬 오프라인 원장 범위의 PASS와 남은 필수 결함 없음을 보고했지만, 당시 로그만으로는 명령·시각·소스 해시가 없어 현재 소스의 실행을 증명할 수 없다고 명시했다. 선언된 세션 신원 검증과 나머지 비차단 관찰도 구분한다. [Claude 재검토 원문](../../raw/docs/03_verification/automation-evidence/claude-review-final.md)

최초 기본 임시폴더 권한 오류 뒤 프로젝트 내부 절대경로로 시험한 이력이 있으며, 이후 사용자 지시에 따라 상대경로를 우선하고 실패 원인을 해결하도록 기준을 바꾸었다. 별도 상대경로 재실행은 24개 통과·종료 코드 0·10.324초로 기록됐고, 최초 기본 임시폴더 권한 문제가 해결됐다는 뜻은 아니다. [검증 원문 v0.3](../../raw/docs/03_verification/automation_validation.md)

## 10월 27일: 설치와 후속 환경 확인

처음에는 WSL·가상 머신 기능 활성화가 각각 재시작 필요 상태였고 WSL MSI와 Docker 사용자 설치가 완료됐다. 그 시점에는 사용자 지시로 재시작·Docker 시작·컨테이너 시험을 하지 않았다. 이후 사용자가 재시작·설치 복구와 Docker 서버 출력을 제공했고, AI가 컨테이너 24개 시험 및 읽기 전용 마운트 등 제한을 직접 확인했다. 설치 성공과 이후 실제 컨테이너 시험은 별개다. [당시 관리 이력](../../raw/docs/04_records/management_history_2026-10-13_2026-11-02.md)

herdr의 Claude 전달·회수는 사용자 전달 보고였으며 이 채팅의 직접 창 제어가 아니다. Claude 교차 검토와 가이드 대표 화면 초안이 있었지만 정식 제작은 별도 단계였고, 후속 사용자 결정으로 가이드 제작과 자료 전송이 보류됐다. Hermes는 설치 후에도 모델 연결·추론이 처음에는 미검증이었다. 같은 날 OAuth 시도는 브라우저 승인 대기에서 중단돼 로그인 성공을 뜻하지 않았다. 인증값은 기록하지 않는다.

## 10월 28일: 개별 도구와 Hermes 실제 회수

환경 구축 기록에 따르면 process-debug 자체 13개 시험과 별도 결함 재현, Hermes worker의 **다른 13개 오프라인 시험**이 각각 통과했다. 사용자가 포털의 공유 상태를 확인했고, 마스터는 구독 경로를 확인한 뒤 제한된 실제 합성 입력을 전달해 응답을 회수했다. 이는 전체 프로토타입 완주가 아니다. [환경 구축 실행 기록](../../raw/docs/workflows/environment-setup/timeline.md), [회수 결과 원문](../../raw/docs/workflows/environment-setup/raw/hermes-ENV-01-hermes-smoke/result.txt)

해당 단일 호출의 기록상 입력 1,293·출력 10·총 1,303토큰은 환경 구축 전체 사용량이나 금액이 아니다. 같은 날 herdr 내부 GPT·Claude·Hermes 화면 응답은 사용자가 전달한 내부 보고에 근거하며, herdr의 Hermes 작업 시작 감지 실패와 화면에서 응답 회수 성공은 별개다. process-debug의 당시 On 지침은 현재 종료됐다. [당시 관리 이력](../../raw/docs/04_records/management_history_2026-10-13_2026-11-02.md)

## 한계와 후속 정정

초기 가이드 구조 검사·화면 확인, 교차 검토, 설치, 로컬 시험과 실제 한 번의 모델 응답은 각각의 범위에서만 읽어야 한다. 인증·청구 전체, 자동 재개, 독립 QA를 포함한 전체 제작부터 문서화까지의 완주는 이들만으로 증명되지 않는다. 11월 2일의 별도 함수 시험 및 Hermes 대화 창 실패는 [관리 이력](management_history_2026-10-13_2026-11-02.md)에 정리한다. 실제 결과와 당시 원문을 검토했으나 모든 시험의 재실행이나 증거 진위·최신성 검증은 이번 문서 작업 범위 밖이다.

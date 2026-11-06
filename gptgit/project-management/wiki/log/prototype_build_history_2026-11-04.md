---
type: concept
tags: [이력, 프로토타입, 검증]
created: 2026-11-04
updated: 2026-11-05
confidence: medium
source_status: reviewed
status: historical
sources:
  - ../../raw/docs/04_records/prototype_build_history_2026-11-04.md
  - ../../docs/04_records/management_log.md
---

# 2026-11-04 프로토타입 0.1 구축 이력

## 요청과 후속 정정

당시 새 `project-prototype`에 개선 프로세스를 구성하면서 문서·도구를 분류하고, 기획↔Claude 검토와 개발↔독립 QA를 구축 대상으로 삼았다. 문서 담당 `process_design`은 README·AGENTS·명세·프로세스·세션 기준과 wiki 진입점을 작성했다. 원본에는 개선의 수정 원본도 프로토타입으로 옮긴다는 서술이 있으나 **같은 날 사용자 정정으로 폐기됐다**. 개선 논의·설계·조정·검증·기록 원본은 project-management, 독립 적용 시험은 project-prototype이다. [구축 원문](../../raw/docs/04_records/prototype_build_history_2026-11-04.md), [최신 인계](../../docs/04_records/management_log.md)

## 구축과 검토

최종 배치 전 staging에서 작성했고, 전체 부모 대화를 받은 Codex 내장 담당이 문서를 만들었다. 따라서 이후 목표인 최소 Task 입력 방식의 실증이나 새 herdr Claude/Hermes 실행으로 볼 수 없다. 시작기는 역할별 CLI·구독 검사·읽기 전용 QA 구성을 다루고, dispatcher는 Task 선점과 시작 전달을 구현했으나 결과 자동 수집과 Hermes adapter는 미구현이었다.

독립 Codex 검토는 기록 경로 분열, 역할·제공자 미대조, QA 쓰기 경계를 지적했고 담당이 이를 수정했다. 원장 단위시험 24개가 통과했고 packet은 14개 중 13개 통과·Windows symlink 생성 권한 부재로 1개 제외였다. dispatcher 모의 시험은 8개 통과했다. 별도 검토와 모의 시험을 실제 모델 연결로 간주하지 않는다. [구축 원문](../../raw/docs/04_records/prototype_build_history_2026-11-04.md)

2026-11-04 최종 배치 후 staging 대비 SHA-256 일치, 필수 구조·상대 링크·시작기 구문·CheckOnly·Python 구문 검사를 보고했다. CheckOnly는 모델·인증 호출을 하지 않았으며 실제 Claude/Hermes 호출, 기획·개발 전체 루프와 GUI 표시는 미검증이었다. 과거 다른 프로젝트의 함수 시험을 이 프로토타입의 실연결 근거로 승계하지 않는다. 현재 남은 업무와 보류는 [최신 인계](../../docs/04_records/management_log.md)를 따른다.

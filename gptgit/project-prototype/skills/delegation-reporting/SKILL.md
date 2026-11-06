---
name: delegation-reporting
description: Apply project-prototype role, read-only QA and existing run-record rules when using shared gptgit delegation. Does not create management-style date reports.
---

# 프로토타입 위임·기록 연결

> 버전 0.2 · 2026-11-06

공통 준비·명시 모델·실제 모델 확인·담당 전용 새 탭·전달·회수는 [공유 위임 스킬](../../../skills/delegation-reporting/SKILL.md)을 따른다. 역할·권한은 [AGENTS](../../AGENTS.md), 최소 입력은 [담당 운영](../../docs/context-and-agents.md), 시작 도구·권한은 [실행 환경](../../docs/runtime.md)을 따른다.

Astra 마스터, Luna·Terra Codex 기획/QA 담당을 사용한다. 기존 Claude 기획 검토·개발 및 Hermes 문서화 계약은 유지한다. 모델 정책을 이유로 다른 제공자 역할로 임의 대체하지 않는다. QA 원본 read-only·명시 시험 출력 범위와 Claude 기획 검토의 읽기 전용을 유지하며 승인 심사를 우회하지 않는다. Hermes adapter 구현 완료를 주장하지 않는다.

날짜별 담당·요청/실제 모델·확인 방법·tab/pane/session·Task·전달/회수·파일·시험·미확인은 기존 `docs/workflows/<run_id>/`에 기록한다. 인계·완료 요약은 [공식 작업기록](../../docs/records/work_log.md)에 연결한다. 실행 원장에 등록하지 않은 규칙 적용 작업은 그 사실을 구분해 공식 작업기록에 남긴다. 관리 프로젝트의 report_docs를 만들거나 상세 기록을 복제하지 않는다.

일반 논의·승인 밖 실행의 자동 저장 권한은 없다. 구독·보류·Git·다른 프로젝트 권한을 유지한다. 입력 전송·실행·결과 회수·내용 통과·최종 판정을 구분하며 모호한 요청을 자동 재전송하지 않는다.

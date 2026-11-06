---
name: delegation-reporting
description: Apply project-management reporting and authorization rules when using the shared gptgit delegation workflow. Does not impose these report paths on other projects.
---

# 관리 프로젝트의 위임·보고 연결

> 버전 0.4 · 2026-11-06 · 공통 절차는 상위 공유 원본으로 통합

담당 준비·모델 제한·새 탭·전달·회수·검증은 [공유 위임 스킬](../../../skills/delegation-reporting/SKILL.md)을 읽고 따른다. 모델 정책은 [공통 AGENTS](../../../AGENTS.md), 업무·권한은 [프로젝트 AGENTS](../../AGENTS.md)를 따른다. 같은 절차를 이 파일에 복제하지 않는다.

이 프로젝트의 Astra 마스터는 판단·지시·검토·통합을 맡는다. 하위 단순 작업은 Luna, 복잡한 작업·독립 검토는 Terra가 기본이며 프로젝트에서 허용한 Claude 역할을 유지한다. 일반 Codex는 자동 승인 심사를 사용하고 검토·QA의 원본 읽기 전용을 지킨다.

사용자가 지속 승인한 날짜 보고는 한국 날짜별 `report_docs/YYYY-MM-DD.md`다. 기존 내용을 보존하며 담당별 요청/실제 모델·확인 방법·tab/pane/session·Task·전달/회수·검증·미확인과 마스터 판정을 누적한다. 기존 기록을 읽고 중복 상세 사본을 만들지 않는다. 실제 구현·검증과 제안을 구분한다.

이 기록 승인은 관리 프로젝트의 날짜 보고에만 적용한다. 다른 문서·프로젝트·Git·외부 작업의 권한을 추가하지 않으며 일반 대화를 자동 저장하지 않는다. 사용자 지정 테스트 결과 경로는 해당 요청 범위에서만 사용한다. 개인 설치·앱 등록을 의미하지 않는다.

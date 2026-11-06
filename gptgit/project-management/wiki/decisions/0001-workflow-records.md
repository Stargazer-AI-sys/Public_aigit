---
type: decision
tags: [기록, 책임, ADR]
created: 2026-10-27
updated: 2026-11-05
confidence: medium
source_status: reviewed
status: historical
sources:
  - ../../raw/wiki/adr/0001-workflow-records.md
  - ../../docs/04_records/management_log.md
  - ../../AGENTS.md
---

# ADR-0001 — 실행 기록과 현재 설명의 책임 분리

## 2026-10-27의 배경과 채택

당시 사용자가 승인한 관리 자동화 개선안은 같은 요구사항과 상세 상태를 여러 문서에 복사할 때 버전이 어긋나거나 요약에서 실패·조건이 빠지는 문제를 다뤘다. 그래서 합의한 명세와 AI 실행계획을 요구사항 번호로 연결하되 책임을 나누고, 작은 작업은 한 문서의 두 부분으로 합치기로 했다. [당시 ADR 원본](../../raw/wiki/adr/0001-workflow-records.md)

당시 설계에서 실행별 `state.json`은 도구 상태, `timeline.md`는 사건·판정·근거, 실행별 `raw/`는 수집된 원문을 담당했다. wiki는 당시의 현재 설명, 가이드는 사용자 절차, ADR은 중요한 선택 이유를 맡고, wiki 단계 폴더에는 갱신과 검토 증거만 남기기로 했다. Obsidian은 별도 복제본이 아닌 같은 Markdown을 보는 창구로 정했다. 원문 접근과 판정 근거를 추적할 수 있다는 장점은 있으나, 버전·링크를 관리하고 보류·실패·예외·미검증을 요약에서도 보존해야 한다.

## 현재 적용할 때의 경계

이 결정은 **2026-10-27에 채택된 과거 자동화 설계**다. 그때의 특정 경로와 절차를 현행 자동화 기능으로 확정하지 않는다. 현재 관리 프로젝트에서 자동화 운영은 현행 기능이 아니며, wiki에는 과거 설계와 이력도 설명한다. 공식 기록과 현재 권한은 [최신 인계](../../docs/04_records/management_log.md)와 [루트 AGENTS](../../AGENTS.md)를 따른다. 프로젝트 루트의 보관용 `raw/`와 당시 실행별 `raw/`도 목적과 경로가 서로 다르다.

같은 사실을 여러 곳에 중복 유지하지 않고 원본에 연결하는 책임 구분은 현재 기록을 읽을 때도 유용하다. 그러나 이 ADR만으로 원문 자동 수집, Obsidian·LLM 연결, 다른 프로젝트 일괄 적용 또는 외부 서비스·Git 실행 권한을 인정할 수 없다. 상세 이력은 [검증 기록](../log/automation_validation_history.md)을 본다.

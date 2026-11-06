---
name: automation-handoff
description: Return a concise evidence-based handoff to the master GPT after an assigned automation task or read-only review. Use for task result handoff, not for autonomous project execution.
---

# 마스터에게 작업 결과 반환

1. 마스터가 지정한 작업 ID·역할·입력 버전·수정 허용 범위를 결과와 대조한다.
2. 실제 변경 파일, 실행한 검증과 결과, 근거 위치, 미해결 결함·미검증을 구분한다. 검토 역할이면 원본 무변경 여부를 명시한다.
3. 실제 세션 식별자와 종료 코드는 수집된 값만 적는다. 미수집은 미수집으로 남기며 완료 상태를 꾸미지 않는다.
4. 마스터에게 다음 행동과 필요한 결정을 반환한다. 인계만으로 새 작업·Git 실행·파일 기록 갱신을 시작하지 않는다.

권장 반환 순서: 작업 ID / 역할·세션 / 결과 / 검증·근거 / 미검증·차단 / 다음 행동.

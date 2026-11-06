# 학습내용정리 프로젝트

> 문서 연결 기준일: 2026-10-16. README는 자료 위치와 역할을 안내하며 상세 규칙·설계·작업기록을 대신하지 않는다.

원본 학습자료를 보존하면서 내용을 수집·추출하고 AI로 분석·재구성한 뒤 사용자 승인 후 Notion에 반영하는 시스템을 구축한다. AI는 기존 소스의 개발·수정·검증을 담당한다.

## 시작과 확인 순서

1. 이 문서에서 기준 자료의 위치를 확인한다.
2. `AGENTS.md`와 `docs/00_rules/Study_rule.md`의 현재 작업에 적용되는 규칙을 확인한다.
3. [프로젝트 재개 조회 기준](docs/00_rules/Study_rule.md#프로젝트-재개-조회-범위)에 따라 공식 작업기록의 최신 인계에서 작업 위치·실행 제약·다음 작업부터 확인한다. 작업별 추가 조회 대상은 해당 기준의 표에서 선택한다.

같은 작업에서 확인한 자료는 변경·누락·충돌이 있을 때만 다시 확인한다. 모든 문서를 매번 순서대로 읽지 않는다.

## 문서별 기준과 위치

| 자료 | 담당 내용 | 확인하는 경우 |
| --- | --- | --- |
| [AGENTS.md](AGENTS.md) | AI의 역할·수정 원칙·참조 순서 | AI 작업 시작 |
| [Study_rule.md](docs/00_rules/Study_rule.md) | 상세 작업·가이드·문서 반영 규칙 | 해당 작업 규칙 확인 |
| [학습내용정리 시스템 요구사항 정의서 v1.0.md](docs/01_requirements/%ED%95%99%EC%8A%B5%EB%82%B4%EC%9A%A9%EC%A0%95%EB%A6%AC%20%EC%8B%9C%EC%8A%A4%ED%85%9C%20%EC%9A%94%EA%B5%AC%EC%82%AC%ED%95%AD%20%EC%A0%95%EC%9D%98%EC%84%9C%20v1.0.md) | 목표·범위·요구사항 | 설계·기능 변경 |
| [학습내용정리_작업기록.md](docs/04_records/%ED%95%99%EC%8A%B5%EB%82%B4%EC%9A%A9%EC%A0%95%EB%A6%AC_%EC%9E%91%EC%97%85%EA%B8%B0%EB%A1%9D.md) | 확정 인터페이스·구현·검증·다음 작업 | 현재 상태·새 채팅 인계 |
| [Schema v0.2](output/study_material_analysis_schema_v0.2.json) | 기본 실행의 최종 분석 JSON 구조. [v0.1](output/study_material_analysis_schema_v0.1.json)·[v0.2 초안](output/study_material_analysis_schema_v0.2_draft.json)은 과거 결과 호환용 | 출력 수정·검증 |
| [guide_docs](guide_docs) | 사용자 실행·결과 검토 방법 | 실행 안내·가이드 갱신 |
| [review_docs](review_docs) | 사용자 열람용 작업 리뷰·개선 근거 | 반복 작업·자동화 개선점 확인 |
| [학습 분류·승인 실행기](tools/run_classification_review.cmd) | 공식 학습 범위 기반 탐색과 승인·보류 화면. 단계 내 사용자 수정 없음 | 기본 저장소는 `study/study-system/output/knowledge_base/` |
| [학습자료 통합 관리 실행기](tools/run_study_manager.cmd) | 실행·승인 대기·게시·설정 탭. API 키는 Windows 자격 증명 관리자에 보관 | 신규·변경 분석부터 게시 준비까지 웹 화면에서 진행. 실제 전송은 채팅 중계 유지 |

요구사항 문서의 초기 예시나 과거 구현 설명을 최신 구현으로 간주하지 않는다. 확정 구조는 Schema와 작업기록의 인터페이스를, 실제 동작은 지정된 최신 소스와 실행 증빙을 함께 확인한다. 충돌하면 관련 근거를 확인해 해결한다.

## 현재 인계 기준과 소스

- **개발용:** 기존 `study/study-system/`과 루트 `tools/`·`test_file/`을 유지한다. 테스트·샘플·성능 측정·패키지 생성 및 검증 도구는 이쪽에서 관리한다.
- **일반 사용자용:** [user_app](user_app/)은 개발용 검증 파일을 제외한 별도 실행 복사본이다. [프로그램 실행](user_app/프로그램_실행.cmd)으로 열고 `user_app/study/sourcefile/`에 자료를 넣는다. 생성 시점의 승인·게시 이력을 보존하며 이후 두 폴더의 데이터는 자동 동기화하지 않는다. 현재 PC의 Windows Python 3.14와 `vendor/`의 실행 라이브러리를 사용한다.
- 개발용 [생성 도구](tools/build_user_distribution.py)는 기존 사용자 폴더를 덮어쓰지 않으며, [독립 실행 검증](tools/verify_user_distribution.py)·[시작/종료 검증](tools/verify_user_startup.py) 도구로 복사본을 확인한다.

- 최신 구현·검증·다음 작업의 기준은 공식 작업기록의 최신 인계다. 2026-10-16 갱신 기준 20절이 최신이며 19절 이하는 당시 이력이다. 이후에는 기록의 더 최신 인계를 확인한다.
- 현재 개발·실행 원본은 [study/study-system](study/study-system/)의 로컬 수정본이다. 기존 ZIP·외부 study_branch 폴더로 덮어쓰지 않는다. 기록상 구현·테스트 결과를 현재 PC에서 다시 검증한 것으로 표현하지 않는다.
- [과거 자료 보관 폴더](archive/)에서 이전 소스·압축본(`versions/`), 이전 분석 결과(`analysis_samples/`), 임시 시험 파일(`test_artifacts/`)을 구분한다. [study_analyzer_v0.5.zip](archive/versions/study_analyzer_v0.5.zip)은 이관 기준 보관본이며 현재 수정본의 대체물이 아니다. 이동 전 위치와 파일 검증값은 [이동 목록](archive/manifest.json)에 보관한다.
- 실행 Python·가상환경·API 예산은 PC별로 확인한다. 과거 외부 가상환경 경로가 새 PC에서도 존재한다고 가정하지 않는다. 예산은 최신 사용자 결정과 실제 `budget` 조회를 기준으로 확인하며, 과거 인계의 한도 소진을 현재 상태로 자동 승계하거나 확인 목적의 유료 재실행을 하지 않는다.
- 기본 실행 Schema와 선택 초안의 적용 범위, 실제 복구 결과·대표 자료 검토·미구현 기능은 최신 작업기록과 실제 코드·저장 결과를 대조한다. 요구사항의 초기 예시는 구현 완료 근거가 아니다.

진행 흐름: 최신 인계·실제 소스 확인 → 저장 자료·로컬 검증 우선 → 범위 내 수정·관련 회귀 확인 → 사용자 내용 검토 → 요청된 가이드·작업기록 반영. 공통 재개 절차는 [공통 작업 흐름](../docs/common_workflow.md)을 따른다.

## 사용자 가이드

- [학습_분류_승인_가이드.html](guide_docs/학습_분류_승인_가이드.html) — 학습 분류·승인·로컬 저장·Notion 미리보기와 실제 게시 (기본 Schema v0.2)

- [Collector_실행_가이드.html](guide_docs/Collector_%EC%8B%A4%ED%96%89_%EA%B0%80%EC%9D%B4%EB%93%9C.html) — 환경 준비·자료 수집·CSV 확인
- [OpenAI_API_Key_발급_및_호출_테스트_가이드.html](guide_docs/OpenAI_API_Key_%EB%B0%9C%EA%B8%89_%EB%B0%8F_%ED%98%B8%EC%B6%9C_%ED%85%8C%EC%8A%A4%ED%8A%B8_%EA%B0%80%EC%9D%B4%EB%93%9C.html) — 과거 API 실행 참고. 현재 한도·작업 흐름은 최신 분류·승인 가이드 우선
- [AI_JSON_Schema_v0.1_가이드.html](guide_docs/AI_JSON_Schema_v0.1_%EA%B0%80%EC%9D%B4%EB%93%9C.html) — 과거 Schema v0.1 결과 참고. 기본 실행은 v0.2

## 문서 배치와 갱신

- README와 AGENTS는 프로젝트 최상위에 유지한다. 상세 규칙은 `docs/00_rules/`, 요구사항은 `docs/01_requirements/`, 공식 작업기록은 `docs/04_records/`에 배치한다. 기존 문서의 내용은 분리하지 않았다.
- `docs/02_design/`과 `docs/03_verification/`에는 아직 독립 MD 문서가 없다. 확정 설계·인터페이스와 검증 이력은 공식 작업기록의 관련 절을 참조하고, 정확한 출력 구조는 기존 `output/`의 Schema를 확인한다.
- 과거 초안·백업·ZIP은 이력용으로 구분하고 README·AGENTS·공식 작업기록과 동일 역할의 사본을 기준으로 추가하지 않는다.
- 사용자 가이드와 공식 작업기록은 사용자의 명시적인 반영 요청 때만 요청한 문서를 갱신한다.
- 문서 이동·이름 변경 시 README의 위치표와 AGENTS 및 관련 문서의 연결을 함께 갱신한다. 동일 역할의 사본을 기준 문서로 추가하지 않는다.
- Library에서 작업할 때는 전체 경로로 파일을 식별한다. 로컬 도구가 규칙을 읽게 하려면 실제 작업 폴더에도 AGENTS와 참조 문서를 배치한다. 문서 보관 폴더와 소스 실행 폴더의 `output/`을 혼동하지 않는다.

## 변경 이력

| 날짜 | 내용 |
| --- | --- |
| 2026-10-16 | 재개 시 최신 인계의 필수 소절부터 조회하도록 상세 규칙에 연결 |
| 2026-10-16 | 오래된 15절·ZIP 실행 기준을 최신 인계·프로젝트 내부 수정본으로 정정. 기술 구현·실행은 변경하지 않음 |

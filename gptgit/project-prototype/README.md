# 자동화 프로세스 프로토타입

> 버전 0.4 | 2026-11-06 | 개선된 프로세스를 독립적으로 적용·시험하는 프로젝트

사용자와 확정한 작업명세서를 바탕으로 기획·개발·검증·문서화를 수행한다. 이 폴더에는 적용할 프로세스, 자체 실행 도구와 양식, 이 프로젝트에서 수행한 작업의 근거만 둔다.

## 시작과 문서 책임

| 문서 | 역할 |
| --- | --- |
| [AGENTS](AGENTS.md) | 승인·행동·기록 경계 |
| [프로세스 적용 조건](docs/requirements.md) | 실행에 필요한 입력과 수락 기준 |
| [실행 설계 기준](docs/development-plan.md) | Task 분해·역할·입출력·검토 설계 |
| [프로세스](docs/workflow.md) | 기획 검토·개발 QA·문서화 순서 |
| [컨텍스트와 담당 운영](docs/context-and-agents.md) | 최소 자료 전달·병렬 작업·인계 |
| [실행 환경](docs/runtime.md) | 이 프로젝트의 CLI·herdr 연결 |
| [도구 목록](docs/tool-inventory.md) | 포함된 도구와 지원 범위 |
| [작업기록](docs/records/work_log.md) | 자체 작업의 현재 상태·다음 행동 |
| [wiki](wiki/index.md) | 설명과 근거 탐색 |

새 작업은 [작업명세서 양식](templates/work-spec.md)으로 합의하고 [개발기획서 양식](templates/development-plan.md)으로 실행을 설계한다. 사용자 창구는 마스터이며 담당 실행·전달·회수도 마스터가 수행한다.

docs/workflows에는 실행별 상태·증거를, docs/records에는 짧은 최신 인계를 둔다. tools·tests·templates는 실행 도구·시험·입력 양식이다. config에는 이 프로젝트의 실행 환경만 설정한다. 실제 연결과 전체 루프의 완료는 자체 실행 근거로 판정한다.


## 위키와 스킬

위키는 원문을 주제별로 설명하며 실행 기록·프로세스 원본을 복제하지 않는다. [전체 색인](wiki/index/README.md), [편집 기준](wiki/AGENTS.md), [스키마](skills/wiki-editor/references/schema.md)에서 목적별 진입점과 형식을 확인한다.

```text
wiki/
    index.md
    AGENTS.md
    features/       # 기능과 사용 조건
    architecture/   # 구성 관계와 도식
    decisions/      # 선택 이유와 영향
    index/          # 탐색
    log/            # 사건과 결과
    operations/     # 운영 조건과 확인 방법
skills/
    wiki-editor/            # 편집·스키마·템플릿·검사기
    delegation-reporting/   # herdr 담당 위임과 기존 기록 연결
```

폴더별 AGENTS를 갖췄으며 기존 상세 docs는 원래 위치에 유지한다. 틀과 스킬 적용은 지식 페이지 작성·자동화 실행·모델 연결 완료를 뜻하지 않는다. [위키 편집 스킬](skills/wiki-editor/SKILL.md)은 이 프로젝트 내부 자원으로 실행하고, [위임 스킬](skills/delegation-reporting/SKILL.md)은 기존 역할·QA 읽기 전용·실행 기록을 따른다. 검사 의존성과 실행은 [실행 환경](docs/runtime.md)을 본다.

공통 운영과 스킬은 [상위 README](../README.md), [상위 AGENTS](../AGENTS.md)를 참조한다. 공유 원본을 이 폴더에 중복 복사하거나 개인 설치·앱 등록을 수행한 것은 아니다.

## 변경 이력

| 날짜 | 버전 | 내용 |
| --- | --- | --- |
| 2026-11-06 | 0.3 | 여섯 위키 분류와 로컬 스킬·검사 진입점 연결 |

| 2026-11-06 | 0.4 | 공통 위임 스킬·모델 검사·새 담당 탭·보조 훅 진입점 연결 |

## 공통 담당 관리 도구

[공유 위임 스킬](../skills/delegation-reporting/SKILL.md)은 모델 검사·담당 전용 새 탭·전달·회수 절차를 제공한다. 역할과 날짜별 기록 위치·권한은 각 프로젝트 규칙이 유지한다. 훅 등록과 사용자 신뢰·실제 작동 확인은 구분한다.

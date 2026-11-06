# 위키 페이지 스키마

이 문서는 이 스킬의 메타데이터와 검사 기준의 단일 원본이다. 내용 분류는 대상의 `wiki/AGENTS.md`를 따른다. `type`은 원본 자료 종류가 아니라 작성하는 위키 문서의 유형이다. 이 스키마는 신규·변경 지식 문서에 적용하며 기존 문서를 일괄 변환하지 않는다. README, AGENTS, index 같은 운영 파일은 대상에서 제외한다. 아래 필드는 모두 필수다. 날짜는 `YYYY-MM-DD`, 태그와 출처는 문자열 배열이다. 빈 태그는 허용한다. 출처가 없으면 빈 배열을 쓰고 본문에 이유를 밝히며 `confidence: unknown`, `source_status: unreviewed`, `status: unknown` 또는 `draft`로 둔다.

필수 필드 외의 추가 키는 허용하지만 필수 필드의 의미를 덮어쓰지 않는다. 검사기는 추가 키의 값을 검증하지 않는다.

```yaml
---
type: concept
tags: []
created: 2026-11-05
updated: 2026-11-05
confidence: unknown
source_status: unreviewed
status: unknown
sources: []
---
```

| 필드 | 허용값·의미 |
| --- | --- |
| type | `concept`, `architecture`, `decision`, `operation` |
| confidence | `unknown`, `low`, `medium`, `high`: 근거에 대한 판단. 추정 근거와 한계를 본문에 설명한다. |
| source_status | `unreviewed`, `reviewed`, `verified`: 원문 검토 상태. `verified`는 실제 대조한 범위를 본문에 밝힌다. |
| status | `current`, `historical`, `superseded`, `draft`, `unknown`: 내용의 상태. 현행 여부가 불명확하면 `unknown`. |
| sources | 실제 확인한 로컬 파일의 문서 기준 상대경로 문자열을 우선한다. `https://` 또는 `http://` URL도 가능하나 검사기는 접근하지 않는다. 허구의 출처를 넣지 않는다. |

값은 주장별로 다를 수 있으므로 페이지 값만으로 모든 주장이 검증되었다고 표현하지 않는다. `high`와 `verified`는 자동으로 추정하지 않는다. 날짜는 페이지 생성·수정일이며 원문의 날짜와 구분한다.

Markdown 링크와 로컬 sources는 **현재 문서가 있는 폴더 기준** 상대경로이며 실제 파일명을 쓴다. `[제목](../path/file.md)`을 사용한다. `[[위키링크]]`는 검사기가 지원하지 않으므로 오류다. 표준 인라인 링크의 경로 존재만 검사한다. 구조 페이지는 Mermaid 코드 블록이 하나 이상 필요하며, 존재는 내용의 정확성을 뜻하지 않는다.

검사기는 명시된 파일만 읽어 YAML 중복 키, 필드·값·날짜, H1, 코드 펜스 닫힘, 로컬 sources와 인라인 Markdown 경로, 구조 도식의 존재를 확인한다. 경로는 프로젝트 루트 밖을 허용하지 않는다. 앵커, 외부 URL 접근, 참조형 링크, 복잡한 중첩 링크, Mermaid 문법·렌더링, 도식의 정확성, 고아·중복·상충, 사실·최신성 및 원문 조건 보존은 검사하지 않는다. 원문과 수동 대조한다. 검사기는 파일을 수정하지 않는다.

---
name: commit
description: '이 저장소의 메시지 형식(날짜_장소_내용)으로 관련 변경만 골라 Git commit한다. 사용자가 commit이나 push를 직접 요청했을 때 사용한다(예: "커밋해줘", "commit 해", "커밋하고 푸시해"). 작업이 끝났다는 이유만으로 사용하지 않는다.'
---

# Git commit

commit과 push는 사용자가 요청하면 Claude가 한다. 요청이 없으면 하지 않는다. 사용자가 PC 사이에서 이 저장소를 옮겨 가며 작업하므로, 메시지 형식이 같아야 언제 어디서 한 작업인지 이력에서 찾을 수 있다.

## 순서
1. 저장소 루트에서 `git status --short`, `git diff`, `git diff --cached`, `git log -5 --format=%s`를 확인한다. 저장소 루트는 `Project_*`가 아니라 `Aigit`이다.
2. 이번 작업과 관련된 파일만 경로를 지정해 `git add <경로>`로 올린다. `git add -A`는 쓰지 않는다. 사용자가 작업 중인 무관한 변경까지 들어갈 수 있기 때문이다. 어떤 변경을 넣을지 판단할 수 없으면 묻는다.
3. 올릴 내용에 비밀값이 없는지 본다. `.env`, 키, 자격 증명이 있으면 올리지 않고 값은 적지 않은 채 위치만 알린다. 작업 기록에 "commit할지 사용자가 정한다"고 적힌 파일도 먼저 묻는다.
4. 아래 형식으로 commit한다.
5. `git status --short`와 `git log -1 --format=%h`로 결과를 확인하고 해시와 포함한 파일을 짧게 보고한다.

## 메시지 형식
`YYYYMMDD_장소_간단한 내용`

- **날짜:** 오늘 날짜.
- **장소:** 작업 경로의 사용자 폴더로 정한다. `C:\Users\ICT` 아래면 `ICTwork`, `C:\Users\Stargazer` 아래면 `HOMEwork`. 다른 경로면 사용자에게 묻는다.
- **내용:** 영어 소문자와 밑줄로 프로젝트와 변경을 짧게 적는다.
- 환경에서 지정한 `Co-Authored-By` 줄이 있으면 본문 끝에 넣는다.

예시:
- `20261103_ICTwork_dev_env_setup_herdr`
- `20261102_HOMEwork_webportfolio_mdx_darkmode_gptgit_launcher`

## push와 안전
- push는 "푸시해"처럼 요청에 포함됐을 때만 한다. commit 요청을 push 요청으로 넓혀 해석하지 않는다.
- 요청 없이 브랜치를 바꾸거나 새로 만들지 않는다.
- 새 commit을 만든다. `--amend`, 강제 push, `--no-verify`는 사용자가 명시적으로 요청할 때만 쓴다.
- 훅이 실패하면 우회하지 않고 원인을 고치거나 사용자에게 알린다.

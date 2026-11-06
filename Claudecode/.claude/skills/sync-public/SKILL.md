---
name: sync-public
description: 'private 저장소(Aigit)의 커밋된 변경을 public 저장소(Public_aigit)에 동기화한다. 사용자가 "public 동기화", "퍼블릭에 반영", "public에도 올려줘"처럼 요청했을 때 사용한다. private commit·push를 요청한 것만으로는 사용하지 않는다.'
---

# Public 저장소 동기화

private(`Stargazer-AI-sys/Aigit`)의 이력은 공개하지 않는다. public(`Stargazer-AI-sys/Public_aigit`)에는 **커밋된 파일 내용만 복사**하고, public에서 따로 commit한다. 원격을 추가해 직접 push하지 않는다. 과거 커밋, 지운 파일, 커밋 메시지가 함께 공개되기 때문이다.

## 준비물 (PC마다 따로 있다)
- 스크립트: `$HOME\tools\sync-public.ps1` (저장소 밖, public에 올라가지 않는다)
- public 클론: `$HOME\Public_aigit` (OneDrive 밖, `core.longpaths=true`). 스크립트의 `-PublicRepo` 기본값도 이 경로다.
- 둘 중 하나라도 없으면(예: ICT PC) 실행하지 말고 사용자에게 알린다. 새로 만들 때는 클론에 `git clone -c core.longpaths=true`를 쓰고, 스크립트는 사용자 확인을 받은 뒤 저장소 밖에 둔다. 이 저장소에는 경로가 긴 파일이 있어 longpaths가 없으면 checkout이 실패한다.

## 스크립트가 하는 일
- `git ls-files`에 있는 파일만 대상으로 한다. `.gitignore`에 걸린 파일과 추적하지 않는 파일은 복사하지 않는다.
- 내용 해시로 비교해 public에 없거나 다른 파일만 복사하고, public에만 남은 파일은 삭제 대상으로 보여 준다. 줄바꿈 변환(`autocrlf`)의 영향을 받지 않는다.
- 아래 폴더는 항상 제외한다(2026-11-06 사용자 결정). 제외 목록을 바꾸려면 스크립트의 `$Excluded`를 고치고, 바꾼 내용을 사용자에게 알린다.
  - `Claudecode/Project_webportfolio/img/`
  - `Claudecode/Project_dev_env_setup/`
  - `Claudecode/Project_director/`
  - `gptgit/Pnetlab/`
  - `gptgit/사용자 확인 필요/`
  - `gptgit/재취업 이력서/`
- 폴더로 기록된 항목(gitlink)은 건너뛴다.
- 기본은 미리보기다. `-Apply`를 줄 때만 복사·삭제한다. commit과 push는 하지 않는다.

## 순서
1. private 저장소에 커밋하지 않은 변경이 있는지 `git status --short`로 본다. 있으면 동기화 대상에서 빠진다고 알리고, 먼저 commit할지 묻는다. 이 스킬이 대신 commit하지 않는다.
2. public 클론을 최신으로 맞춘다: `git -C <public 클론> pull --ff-only`. 실패하면(public에 따로 생긴 커밋 등) 중단하고 알린다.
3. 미리보기: `& "$HOME\tools\sync-public.ps1"` (private 저장소 루트에서 실행). 복사·삭제 목록을 사용자에게 보여 준다.
4. **삭제 대상이 있거나 변경이 평소보다 많으면 적용 전에 멈추고 사용자에게 확인한다.** 새로 추가되는 파일은 이름을 훑어 민감해 보이는 것(`.env`, 키, 인증, 이력서, 개인정보)이 없는지 본다. 내용은 필요한 만큼만 열고 값은 응답에 옮기지 않는다.
5. 확인된 뒤 `-Apply`로 실행하고, `git -C <public 클론> status --short`와 `diff --stat`로 결과를 보여 준다.
6. **public commit·push는 사용자가 요청했을 때만 한다.** public은 누구나 보는 저장소라 push 전에 한 번 더 확인한다. commit 메시지는 가능하면 private의 해당 커밋 메시지(`git log -1 --format=%s`)를 그대로 쓰고, 환경에서 지정한 `Co-Authored-By` 줄이 있으면 본문 끝에 넣는다. 관련 변경만 경로를 지정해 `git add`한다.
7. 해시와 포함한 파일을 짧게 보고한다. private 쪽 커밋 해시와 대응시켜 알리면 이력을 찾기 쉽다.

## 하지 않는 것
- private 저장소를 public 원격에 직접 push하거나 원격을 추가하지 않는다.
- `--force` push, 이력 재작성, `--no-verify`는 사용자가 명시적으로 요청할 때만 쓴다.
- 스크립트 출력만 믿고 적용하지 않는다. 미리보기 목록을 읽은 뒤 적용한다.
- 비밀값이나 개인정보가 보이면 올리지 않고, 값은 적지 않은 채 위치만 알린다.

# 담당 실행

버전 0.7 · 2026-11-18. 담당을 실제 시작할 때만 읽는다.

- `config/runtime.local.json`에 이 프로젝트 또는 시스템 공용 CLI 경로를 설정한다. 예시는 `config/runtime.example.json`이다. 인증값은 저장하지 않으며 구독에서 API 결제로 전환하지 않는다.
- `tools/task_packet.py`는 입력·쓰기 범위·역할을 검사한다. `work_spec`과 `development_plan`에는 같은 한 문서 기획서를 지정할 수 있다. 실행 packet은 `.local`에 필요한 동안만 두고 docs/workflows에 사본을 만들지 않는다.
- `tools/start_role.ps1`은 명시한 모델을 공유 검사기로 확인한다. `-CheckOnly`는 실제 모델 호출 없이 인수를 검사한다. 담당 CLI는 초기 사용자 프롬프트 없이 열고 실제 모델·권한 확인 뒤 Task를 보낸다.
- `tools/dispatch_task.py`는 검사 후 `--apply`에서 herdr의 새 담당 탭을 연다. 마스터 탭을 분할하지 않는다. 실제 herdr가 제공한 환경과 pane·cwd·프로세스를 확인하며 환경변수만 만들어 내부 실행으로 위장하지 않는다.
- `.local/dispatch` JSON과 해시는 같은 Task의 중복 시작 방지용 실행 영수증이다. 문서 산출물이 아니므로 리뷰·비용 자료로 복제하지 않는다. 동일 Task를 다시 보낼 가능성이 있는 동안 영수증을 지우지 않는다.
- `submitted_unverified`는 시작 접수일 뿐이다. 마스터가 herdr로 세션·응답을 확인한다. 모호하면 재전송 전에 도달 여부를 확인한다. 자동 결과 수집·세션 재사용 판정·Hermes adapter는 미구현이다.
- QA는 원본 read-only이며 지정 `.local/qa/<task_id>/` 출력만 허용한다. Claude 기획 검토는 Read/Grep/Glob만 사용한다. 승인 거절을 우회하지 않는다.

요청 결과에 필요한 검사만 실행한다. 현재 로컬 Python은 `.local/bin/python/python.exe`다. 문서 연결을 변경한 경우 `-B -X utf8 tools/check_structure.py`로 연결을 확인할 수 있다. 연결 검사 통과가 실제 모델·인증·전체 프로세스 검증은 아니다.

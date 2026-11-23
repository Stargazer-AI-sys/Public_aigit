# deploy/qmd

서버(AWS Lightsail Ubuntu 24.04)에서 qmd 위키 검색을 구성할 때 쓴 스크립트 사본이다. 2026-11-18 서버의 `~/qmd-ops/`에서 가져왔다. 구성과 운영 방법은 `docs/guide.md` 5장에 있다.

| 파일 | 서버 위치 | 용도 |
|---|---|---|
| `setup.sh` | `~/qmd-ops/setup.sh` | 처음 설치: qmd 설치(버전 고정), 모델 내려받기, 컬렉션 등록, 첫 색인. root(`sudo`)로 실행 |
| `monitor.sh` | `~/qmd-ops/monitor.sh` | 실행 중 메모리 감시. 호스트 가용 300MB 미만 또는 스왑 1.2GB 초과면 지정 컨테이너를 강제 종료 |
| `qmd-refresh.sh` | `/usr/local/sbin/qmd-refresh.sh` (원본 `~/qmd-ops/`) | 인덱스 갱신. 변경이 있을 때만 서버를 멈추고 색인. cron `0 17 * * *`(UTC, 한국 시간 02:00)에서 root로 실행 |

- `qmd-refresh.sh`는 `monitor.sh`를 `/home/ubuntu/qmd-ops/monitor.sh` 경로로 부른다. 같은 경로에 두거나 스크립트의 경로를 고친다.
- 스크립트의 폴더·경로(`/srv/qmd`, `/home/ubuntu/llmwiki`)는 이 프로젝트 서버 기준이다.
- 서버로 복사할 때 줄바꿈은 LF여야 한다(`.gitattributes`가 `*.sh`를 LF로 고정한다).
- 사본이므로 서버에서 스크립트를 고치면 여기도 같이 고친다. 2026-11-18 기준 `qmd-refresh.sh`는 서버에 설치된 것과 같다(`diff`로 확인).
- 확인한 것은 문법 검사(`bash -n`)와 서버에서의 수동 실행(`qmd-refresh.sh`)이다. `setup.sh`와 `monitor.sh`는 서버에서 실행해 쓴 것이다. 새 서버에 그대로 처음부터 다시 설치해 본 적은 없다.

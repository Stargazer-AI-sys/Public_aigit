#!/usr/bin/env bash
# 역할별 Hermes 인스턴스를 SSH로 서버에 만들고 관리한다. (bash + ssh + scp만 사용)
# 이 스크립트는 2026-11-13 작성했고 구문 검사만 했다. 서버에서는 아직 실행해 보지 않았다.
#
#   hermes-agent.sh new <name> <target>   agents/<name>.env 생성 (로컬 파일만 만든다)
#   hermes-agent.sh setup <name>          서버에 파일 전송 후 대화형 setup (봇 토큰·로그인은 서버 데이터 폴더에만 저장)
#   hermes-agent.sh up|down|status <name>
#   hermes-agent.sh logs <name> [줄수]
#   hermes-agent.sh update <name>         agents/<name>.env의 IMAGE를 pull하고 재시작
#   hermes-agent.sh backup <name>         컨테이너를 잠시 멈추고 데이터 폴더를 backups/에 tar.gz로 저장
#
# 비밀값은 repo에 두지 않는다. backups/ 파일에는 토큰·로그인 정보가 들어 있으니 공유하지 않는다.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_DIR='hermes-deploy'          # 서버의 $HOME 기준 상대 경로
NAME_RE='^[a-z0-9][a-z0-9-]{0,30}$' # 컨테이너명·경로에 그대로 쓰므로 엄격히 제한한다.

die() { echo "오류: $*" >&2; exit 1; }

check_name() { [[ "$1" =~ $NAME_RE ]] || die "이름은 소문자·숫자·하이픈만, 최대 31자: '$1'"; }

load_agent() {
  check_name "$1"
  AGENT_FILE="$ROOT/agents/$1.env"
  [ -f "$AGENT_FILE" ] || die "$AGENT_FILE 없음. 먼저 new를 실행한다."
  # 비밀 아닌 값만 든 파일이다. 서버와 같은 형식이라 그대로 source한다.
  # shellcheck disable=SC1090
  . "$AGENT_FILE"
  [ -n "${TARGET:-}" ] && [ -n "${IMAGE:-}" ] || die "$AGENT_FILE에 TARGET과 IMAGE가 필요하다."
  check_name "${AGENT_NAME:-}"
  [ "$AGENT_NAME" = "$1" ] || die "AGENT_NAME($AGENT_NAME)이 파일 이름($1)과 다르다."
  TARGET_FILE="$ROOT/targets/$TARGET.env"
  [ -f "$TARGET_FILE" ] || die "$TARGET_FILE 없음. targets/example.env.example을 복사해 만든다."
  # shellcheck disable=SC1090
  . "$TARGET_FILE"
  [ -n "${SSH_HOST:-}" ] && [ -n "${SSH_USER:-}" ] || die "$TARGET_FILE에 SSH_HOST와 SSH_USER가 필요하다."
  SSH_OPTS=(-p "${SSH_PORT:-22}")
  [ -n "${SSH_KEY:-}" ] && SSH_OPTS+=(-i "$SSH_KEY")
  DEST="$SSH_USER@$SSH_HOST"
  # sudo가 HOME을 바꿔도 경로가 흔들리지 않도록 데이터 경로를 변수로 직접 넘긴다.
  DATA_DIR_REL=".hermes-agents/$AGENT_NAME"
}

rssh() { ssh "${SSH_OPTS[@]}" "$@"; }

# 서버에서 docker compose를 실행하는 명령 문자열. $HOME은 서버에서 풀린다.
remote_compose() {
  echo "sudo env DATA_DIR=\"\$HOME/$DATA_DIR_REL\" docker compose -p hermes-$AGENT_NAME \
-f \$HOME/$REMOTE_DIR/compose.yaml --env-file \$HOME/$REMOTE_DIR/$AGENT_NAME.env $*"
}

push_files() {
  rssh "$DEST" "mkdir -p ~/$REMOTE_DIR && mkdir -p -m 700 ~/$DATA_DIR_REL"
  scp -P "${SSH_PORT:-22}" ${SSH_KEY:+-i "$SSH_KEY"} \
    "$ROOT/deploy/compose.yaml" "$DEST:$REMOTE_DIR/compose.yaml"
  scp -P "${SSH_PORT:-22}" ${SSH_KEY:+-i "$SSH_KEY"} \
    "$AGENT_FILE" "$DEST:$REMOTE_DIR/$AGENT_NAME.env"
}

cmd="${1:-}"; shift || true
case "$cmd" in
  new)
    [ $# -eq 2 ] || die "사용법: new <name> <target>"
    check_name "$1"; check_name "$2"
    mkdir -p "$ROOT/agents"
    f="$ROOT/agents/$1.env"
    [ ! -e "$f" ] || die "$f 이미 있다."
    sed -e "s/^AGENT_NAME=.*/AGENT_NAME=$1/" -e "s/^TARGET=.*/TARGET=$2/" \
      "$ROOT/agents/example.env.example" > "$f"
    echo "[ok] $f 생성. IMAGE 태그를 확인한 뒤 setup을 실행한다."
    ;;
  setup)
    [ $# -eq 1 ] || die "사용법: setup <name>"
    load_agent "$1"; push_files
    echo "대화형 setup을 시작한다. 봇 토큰은 이 인스턴스 전용으로 새로 쓴다(다른 인스턴스와 공유 금지)."
    rssh -t "$DEST" "$(remote_compose run --rm hermes setup)"
    echo "[ok] setup 끝. 다음: hermes-agent.sh up $AGENT_NAME"
    ;;
  up)
    [ $# -eq 1 ] || die "사용법: up <name>"
    load_agent "$1"; push_files
    rssh "$DEST" "$(remote_compose up -d)"
    ;;
  down)
    [ $# -eq 1 ] || die "사용법: down <name>"
    load_agent "$1"
    rssh "$DEST" "$(remote_compose down)"
    ;;
  status)
    [ $# -eq 1 ] || die "사용법: status <name>"
    load_agent "$1"
    rssh "$DEST" "$(remote_compose ps) && sudo docker stats --no-stream hermes-$AGENT_NAME"
    ;;
  logs)
    [ $# -ge 1 ] || die "사용법: logs <name> [줄수]"
    load_agent "$1"
    lines="${2:-50}"; [[ "$lines" =~ ^[0-9]+$ ]] || die "줄수는 숫자여야 한다."
    rssh "$DEST" "sudo docker logs --tail $lines hermes-$AGENT_NAME"
    ;;
  update)
    [ $# -eq 1 ] || die "사용법: update <name>"
    load_agent "$1"; push_files
    rssh "$DEST" "$(remote_compose pull) && $(remote_compose up -d)"
    ;;
  backup)
    [ $# -eq 1 ] || die "사용법: backup <name>"
    load_agent "$1"
    mkdir -p "$ROOT/backups"
    out="$ROOT/backups/$AGENT_NAME-$(date +%Y%m%d-%H%M%S).tar.gz"
    # SQLite가 쓰는 도중 복사하면 깨질 수 있어 잠시 멈춘다. 실패해도 재시작을 시도한다.
    trap 'rssh "$DEST" "$(remote_compose up -d)" >/dev/null || echo "경고: 재시작 실패. up을 직접 실행한다." >&2' EXIT
    rssh "$DEST" "$(remote_compose stop)"
    rssh "$DEST" "sudo tar czf - -C \$HOME/.hermes-agents $AGENT_NAME" > "$out"
    chmod 600 "$out"
    echo "[ok] $out (토큰·로그인 정보 포함, 공유 금지)"
    ;;
  *)
    sed -n '2,12p' "${BASH_SOURCE[0]}" >&2
    exit 1
    ;;
esac

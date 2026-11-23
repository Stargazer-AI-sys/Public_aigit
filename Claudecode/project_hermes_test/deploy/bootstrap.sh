#!/usr/bin/env bash
# Ubuntu 서버에 Hermes 실행 환경을 준비한다: 스왑, Docker, 이미지, 데이터 폴더.
# 2026-11-12 Lightsail(Ubuntu 24.04, RAM 1.9GB)에서 수동으로 검증한 절차를 옮긴 초안이며,
# 이 스크립트 자체는 아직 실행해 보지 않았다.
# 여러 번 실행해도 이미 된 단계는 건너뛴다. 비밀값은 다루지 않는다.
set -euo pipefail

SWAP_SIZE="${SWAP_SIZE:-2G}"
IMAGE="${HERMES_IMAGE:-nousresearch/hermes-agent:latest}"
DATA_DIR="${HERMES_DATA_DIR:-$HOME/.hermes}"

if [ "$(id -u)" -eq 0 ]; then
  echo "root가 아닌 일반 사용자로 실행한다. 데이터 폴더가 root 소유가 되는 것을 막기 위해서다." >&2
  exit 1
fi

# 1. 스왑: RAM이 부족해도 OOM kill로 컨테이너가 죽지 않게 하는 완충 장치.
if swapon --show --noheadings | grep -q .; then
  echo "[skip] 스왑이 이미 있다."
else
  sudo fallocate -l "$SWAP_SIZE" /swapfile
  sudo chmod 600 /swapfile          # 스왑에는 메모리 내용(비밀값 포함 가능)이 기록된다.
  sudo mkswap /swapfile
  sudo swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
  echo "[ok] 스왑 $SWAP_SIZE 생성"
fi

# 2. Docker: 공식 apt 저장소 방식(https://docs.docker.com/engine/install/ubuntu/).
if command -v docker >/dev/null 2>&1; then
  echo "[skip] Docker가 이미 설치돼 있다."
else
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo docker run --rm hello-world
  echo "[ok] Docker 설치"
fi

# 3. 이미지와 데이터 폴더. 폴더를 미리 만들지 않으면 Docker가 root 소유로 만든다.
sudo docker pull "$IMAGE"
mkdir -p "$DATA_DIR"
chmod 700 "$DATA_DIR"               # 이 폴더에 토큰·로그인 정보가 저장된다.

cat <<EOF

준비 완료. 다음 단계(대화형, 사람이 직접):
  sudo --preserve-env=HOME docker compose run --rm hermes setup
  sudo --preserve-env=HOME docker compose up -d
(compose.yaml이 있는 폴더에서 실행한다. ~/.hermes 경로가 HOME에 의존하므로 HOME을 유지한다.)
EOF

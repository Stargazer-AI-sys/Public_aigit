#!/bin/bash
# qmd 인덱스 갱신(하루 1회용). root로 실행. wiki/ 변경이 있을 때만 serve를 멈추고 인덱싱한다.
# 사용: qmd-refresh.sh [--force]    로그: /srv/qmd/log/refresh.log
set -u
L=/srv/qmd/log; LOG=$L/refresh.log; MARK=$L/last-indexed-fp
WIKI=/home/ubuntu/llmwiki/wiki; DB=/srv/qmd/home/.cache/qmd
MIN_AVAIL_MB=900        # serve 정지 후 가용 메모리가 이보다 작으면 건너뛴다
EMBED_TIMEOUT=2400      # 초
Q=/app/node_modules/.bin/qmd
M="hf:mykor/KURE-v1-gguf/KURE-v1-Q8_0.gguf"
log(){ echo "$(date '+%F %T') $*" >> $LOG; }

exec 9>/var/lock/qmd-refresh.lock
flock -n 9 || { log "skip: 다른 갱신이 실행 중"; exit 0; }

FP=$(find $WIKI -type f -name '*.md' -printf '%P %s %T@\n' | sort | sha256sum | cut -d' ' -f1)
if [ "${1:-}" != "--force" ] && [ "$FP" = "$(cat $MARK 2>/dev/null)" ]; then
  log "skip: 변경 없음"; exit 0
fi

STARTED=0; MON=
cleanup(){
  docker rm -f qmd-index >/dev/null 2>&1
  [ -n "$MON" ] && { touch $L/stop; wait $MON 2>/dev/null; }
  docker start qmd >/dev/null 2>&1
}
trap cleanup EXIT

T0=$(date +%s)
log "start: wiki 변경 감지(fp=${FP:0:8})"
docker stop -t 30 qmd >/dev/null 2>&1; sleep 3
AV=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)
if [ "$AV" -lt "$MIN_AVAIL_MB" ]; then log "skip: 가용 메모리 ${AV}MB < ${MIN_AVAIL_MB}MB, serve 재시작"; exit 1; fi

mkdir -p /srv/qmd/backup; cp -a $DB/index.sqlite /srv/qmd/backup/index.sqlite.prev
rm -f $DB/.qmd-embed.lock       # 강제 종료로 남은 락의 PID 오인 방지(flock으로 단독 실행 보장)
rm -f $L/stop $L/guard; echo refresh > $L/phase
/home/ubuntu/qmd-ops/monitor.sh qmd-index $L/refresh-mem.csv & MON=$!

OUT=$(timeout $EMBED_TIMEOUT docker run --name qmd-index --memory=1g --memory-swap=1g -u 10000:10000 \
  -e HOME=/qmdhome -e QMD_FORCE_CPU=1 -e QMD_EMBED_PARALLELISM=1 -e QMD_EMBED_MODEL=$M \
  -v /srv/qmd/app:/app:ro -v /srv/qmd/home:/qmdhome -v $WIKI:/wiki:ro node:22-slim \
  sh -c "$Q update 2>&1 | tail -3; $Q embed 2>&1 | tail -2; $Q cleanup 2>&1 | tail -2" 2>&1)
RC=$?
OOM=$(docker inspect -f '{{.State.OOMKilled}}' qmd-index 2>/dev/null)
echo "$OUT" | sed 's/\x1b\[[0-9;?]*[a-zA-Z]//g' | grep -E "Indexed|Embedded|embeddings|Done|rror|Skipping|Removed" | while read -r l; do log "  qmd: $l"; done
if [ "$RC" -ne 0 ] || [ "$OOM" = "true" ] || echo "$OUT" | grep -q "Skipping"; then
  log "fail: rc=$RC oom=$OOM guard=$([ -f $L/guard ] && echo YES || echo no). 마커 미갱신, serve 재시작"; exit 1
fi

docker rm -f qmd-index >/dev/null 2>&1
touch $L/stop; wait $MON 2>/dev/null; MON=
docker start qmd >/dev/null
OK=0
for i in $(seq 1 30); do
  sleep 2
  R=$(docker exec hermes python3 -c "
import urllib.request,json
r=urllib.request.Request('http://qmd:8181/query',json.dumps({'searches':[{'type':'lex','query':'wiki'}],'collections':['wiki'],'limit':1,'rerank':False}).encode(),{'Content-Type':'application/json'})
print(len(json.load(urllib.request.urlopen(r,timeout=20)).get('results',[])))" 2>/dev/null)
  [ -n "$R" ] && { OK=1; break; }
done
if [ "$OK" -ne 1 ]; then log "fail: serve 검색 확인 실패. 마커 미갱신"; exit 1; fi
echo "$FP" > $MARK
log "done: $(( $(date +%s) - T0 ))초, serve 검색 확인 OK, 최대 호스트 사용(최저 가용) $(sort -t, -k6 -n $L/refresh-mem.csv | sed -n 2p | cut -d, -f6)MB"

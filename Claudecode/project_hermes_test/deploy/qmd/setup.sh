#!/bin/bash
# step 1: install qmd (pinned), download KURE-v1, build index. No effect on hermes except host memory (guarded).
L=/srv/qmd/log; N=qmd-index; S=/home/ubuntu/qmd-ops
M="hf:mykor/KURE-v1-gguf/KURE-v1-Q8_0.gguf"
rm -f $L/setup-result.txt $L/setup-done $L/guard $L/stop
echo setup > $L/phase
$S/monitor.sh $N $L/setup-mem.csv & MON=$!
{
docker pull -q node:22-slim; echo "image=$(docker inspect -f "{{index .RepoDigests 0}}" node:22-slim 2>/dev/null) id=$(docker inspect -f "{{.Id}}" node:22-slim)"
docker rm -f $N >/dev/null 2>&1
docker run --name $N --memory=700m --memory-swap=700m -u 10000:10000 -e HOME=/tmp -e npm_config_cache=/tmp/npmcache -v /srv/qmd/app:/app -w /app node:22-slim sh -c "npm init -y >/dev/null && npm install @tobilu/qmd@2.8.3 2>&1 | tail -2"
echo "npm exit=$? oom=$(docker inspect -f {{.State.OOMKilled}} $N)"
docker rm -f $N >/dev/null 2>&1
echo phase-index > $L/phase
docker run --name $N --memory=1g --memory-swap=1g -u 10000:10000 -e HOME=/qmdhome -e QMD_FORCE_CPU=1 -e QMD_EMBED_PARALLELISM=1 -e QMD_EMBED_MODEL=$M \
  -v /srv/qmd/app:/app:ro -v /srv/qmd/home:/qmdhome -v /home/ubuntu/llmwiki/wiki:/wiki:ro node:22-slim \
  sh -c "Q=/app/node_modules/.bin/qmd; \$Q --version; \$Q collection add /wiki --name wiki && \$Q update && \$Q embed && \$Q status"
echo "index exit=$? oom=$(docker inspect -f {{.State.OOMKilled}} $N)"
docker rm -f $N >/dev/null 2>&1
ls -la /srv/qmd/home/.cache/qmd/models/; sha256sum /srv/qmd/home/.cache/qmd/models/*.gguf
du -sh /srv/qmd/app /srv/qmd/home
echo "guard=$([ -f $L/guard ] && echo YES || echo no)"
} > $L/setup-result.txt 2>&1
touch $L/stop; wait $MON; touch $L/setup-done

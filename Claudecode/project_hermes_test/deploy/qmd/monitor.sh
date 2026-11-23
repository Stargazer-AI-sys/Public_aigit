#!/bin/bash
# usage (sudo): monitor.sh <container> <outfile>; 1s sampling; kills container if host MemAvailable < 300MB or host swap > 1200MB
C=$1; OUT=$2; L=/srv/qmd/log
echo "ts,phase,cg_cur_mb,cg_anon_mb,cg_file_mb,host_avail_mb,swap_used_mb" > $OUT
rm -f $L/stop $L/guard
while true; do
  ID=$(docker inspect -f "{{.Id}}" $C 2>/dev/null)
  AV=$(awk "/MemAvailable/{print int(\$2/1024)}" /proc/meminfo)
  SW=$(awk "/SwapTotal/{t=\$2}/SwapFree/{f=\$2}END{print int((t-f)/1024)}" /proc/meminfo)
  PH=$(cat $L/phase 2>/dev/null)
  D=/sys/fs/cgroup/system.slice/docker-$ID.scope
  if [ -n "$ID" ] && [ -d $D ]; then
    CUR=$(( $(cat $D/memory.current)/1048576 )); AN=$(awk "/^anon /{print int(\$2/1048576)}" $D/memory.stat); FI=$(awk "/^file /{print int(\$2/1048576)}" $D/memory.stat)
  else CUR=-;AN=-;FI=-; fi
  echo "$(date +%T),$PH,$CUR,$AN,$FI,$AV,$SW" >> $OUT
  if [ "$AV" -lt 300 ] || [ "$SW" -gt 1200 ]; then echo "$(date +%T),GUARD kill avail=$AV swap=$SW" >> $OUT; docker kill $C >/dev/null 2>&1; touch $L/guard; fi
  [ -f $L/stop ] && break
  sleep 1
done

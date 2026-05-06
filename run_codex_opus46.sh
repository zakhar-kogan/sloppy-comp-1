#!/bin/bash
set -euo pipefail

WORKDIR="/Users/zakhar/benchmark/codex-opus46"
RESULTS="/Users/zakhar/benchmark/results/codex-opus46.csv"
OUTPUT_LOG="/tmp/codex_opus46_output.log"
PROMPT="$(cat /Users/zakhar/benchmark/prompt.md)"
INTERVAL=2
DURATION=900
ITERATIONS=$((DURATION / INTERVAL))

echo "timestamp,pid,rss_kb,mem_pct,cpu_pct" > "$RESULTS"

cd "$WORKDIR"
codex exec \
  -p omniroute-opus \
  --dangerously-bypass-approvals-and-sandbox \
  "$PROMPT" > "$OUTPUT_LOG" 2>&1 &
PID=$!
echo "PID: $PID"

for i in $(seq 1 "$ITERATIONS"); do
  ts=$(date +%H:%M:%S)
  if kill -0 "$PID" 2>/dev/null; then
    read -r rss mem cpu <<< "$(ps -o rss=,%mem=,%cpu= -p "$PID" 2>/dev/null)"
    if [ -n "${rss:-}" ]; then
      echo "$ts,$PID,$rss,$mem,$cpu" >> "$RESULTS"
    else
      echo "$ts,$PID,0,0,0" >> "$RESULTS"
    fi
  else
    echo "$ts,DONE,0,0,0" >> "$RESULTS"
    break
  fi
  sleep "$INTERVAL"
done

wait "$PID" 2>/dev/null || true
cat "$OUTPUT_LOG"

#!/bin/bash
set -euo pipefail

WORKDIR="/Users/zakhar/benchmark/omp-opus46"
RESULTS="/Users/zakhar/benchmark/results/omp-opus46.csv"
OUTPUT_LOG="/tmp/omp_opus46_output.log"
PROMPT="$(cat /Users/zakhar/benchmark/prompt.md)"
INTERVAL=2
DURATION=900
ITERATIONS=$((DURATION / INTERVAL))

echo "timestamp,pid,rss_kb,mem_pct,cpu_pct" > "$RESULTS"

cd "$WORKDIR"
omp -p --model "quotio/kiro-claude-opus-4-6" "$PROMPT" > "$OUTPUT_LOG" 2>&1 &
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

wait "$PID"
cat "$OUTPUT_LOG"

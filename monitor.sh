#!/bin/bash
# Usage: ./monitor.sh <process_name> <output_csv> [duration_seconds]
# Example: ./monitor.sh opencode results/opencode.csv 300

PROC_NAME="${1:?Usage: ./monitor.sh <process_name> <output_csv> [duration_seconds]}"
OUTPUT="${2:?Provide output CSV path}"
DURATION="${3:-300}"
INTERVAL=2
ITERATIONS=$((DURATION / INTERVAL))

echo "timestamp,pid,rss_kb,mem_pct,cpu_pct" > "$OUTPUT"

echo "Monitoring '$PROC_NAME' every ${INTERVAL}s for ${DURATION}s -> $OUTPUT"

for i in $(seq 1 "$ITERATIONS"); do
  ts=$(date +%H:%M:%S)
  # Find the main process (not children)
  pid=$(pgrep -f "^${PROC_NAME}$" | head -1)
  if [ -z "$pid" ]; then
    # Try broader match
    pid=$(pgrep -f "$PROC_NAME" | head -1)
  fi
  if [ -n "$pid" ]; then
    read rss mem cpu <<< $(ps -o rss=,%mem=,%cpu= -p "$pid" 2>/dev/null)
    echo "$ts,$pid,$rss,$mem,$cpu" >> "$OUTPUT"
  else
    echo "$ts,NONE,0,0,0" >> "$OUTPUT"
  fi
  sleep "$INTERVAL"
done

echo ""
echo "=== Summary ==="
awk -F',' 'NR>1 && $2!="NONE" {
  count++; rss_sum+=$3; cpu_sum+=$5
  if($3>rss_max) rss_max=$3
  if($5>cpu_max) cpu_max=$5
  if(NR==2) rss_min=$3
  if($3<rss_min) rss_min=$3
} END {
  printf "Samples: %d\n", count
  printf "RSS (MB): min=%.1f avg=%.1f max=%.1f\n", rss_min/1024, rss_sum/count/1024, rss_max/1024
  printf "CPU %%:    avg=%.1f max=%.1f\n", cpu_sum/count, cpu_max
}' "$OUTPUT"

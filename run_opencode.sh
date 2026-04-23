#!/bin/bash
# Wrapper that launches opencode run, captures its PID, and monitors it
OUTPUT_CSV="/Users/zakhar/benchmark/results/opencode.csv"
INTERVAL=2

echo "timestamp,pid,rss_kb,mem_pct,cpu_pct" > "$OUTPUT_CSV"

# Launch opencode run in background, capture PID
opencode run -m "quotio/gpt-5.4" "$(cat /Users/zakhar/benchmark/prompt.md)" &
OC_PID=$!
echo "Tracking opencode PID: $OC_PID"

# Monitor until process exits
while kill -0 "$OC_PID" 2>/dev/null; do
  ts=$(date +%H:%M:%S)
  read rss mem cpu <<< $(ps -o rss=,%mem=,%cpu= -p "$OC_PID" 2>/dev/null)
  if [ -n "$rss" ]; then
    echo "$ts,$OC_PID,$rss,$mem,$cpu" >> "$OUTPUT_CSV"
  fi
  sleep "$INTERVAL"
done

echo ""
echo "Process exited. Results in $OUTPUT_CSV"
echo ""
echo "=== Summary ==="
awk -F',' 'NR>1 && $3>0 {
  count++; rss_sum+=$3; cpu_sum+=$5
  if($3>rss_max) rss_max=$3
  if($5>cpu_max) cpu_max=$5
  if(count==1) rss_min=$3
  if($3<rss_min) rss_min=$3
} END {
  printf "Samples: %d\n", count
  printf "RSS (MB): min=%.1f avg=%.1f max=%.1f\n", rss_min/1024, rss_sum/count/1024, rss_max/1024
  printf "CPU %%:    avg=%.1f max=%.1f\n", cpu_sum/count, cpu_max
}' "$OUTPUT_CSV"

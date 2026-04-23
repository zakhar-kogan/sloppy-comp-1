#!/bin/bash
# Wrapper that launches claude -p and monitors its actual PID
WORKDIR="/Users/zakhar/benchmark/claude-code"
RESULTS="/Users/zakhar/benchmark/results/claude-code.csv"
PROMPT="$(cat /Users/zakhar/benchmark/prompt.md)"
INTERVAL=2
DURATION=600
ITERATIONS=$((DURATION / INTERVAL))

echo "timestamp,pid,rss_kb,mem_pct,cpu_pct" > "$RESULTS"

cd "$WORKDIR"
claude -p --model sonnet --dangerously-skip-permissions "$PROMPT" > /tmp/claude_output.log 2>&1 &
CLAUDE_PID=$!
echo "Claude PID: $CLAUDE_PID"

for i in $(seq 1 "$ITERATIONS"); do
  ts=$(date +%H:%M:%S)
  if kill -0 "$CLAUDE_PID" 2>/dev/null; then
    read rss mem cpu <<< $(ps -o rss=,%mem=,%cpu= -p "$CLAUDE_PID" 2>/dev/null)
    if [ -n "$rss" ]; then
      echo "$ts,$CLAUDE_PID,$rss,$mem,$cpu" >> "$RESULTS"
    else
      echo "$ts,$CLAUDE_PID,0,0,0" >> "$RESULTS"
    fi
  else
    echo "$ts,DONE,0,0,0" >> "$RESULTS"
    break
  fi
  sleep "$INTERVAL"
done

wait "$CLAUDE_PID" 2>/dev/null

echo ""
echo "=== Summary ==="
awk -F',' 'NR>1 && $2!="DONE" && $3>0 { count++; rss_sum+=$3; cpu_sum+=$5; if($3>rss_max) rss_max=$3; if($5>cpu_max) cpu_max=$5; if(count==1) rss_min=$3; if($3<rss_min) rss_min=$3 } END { printf "Samples: %d\n", count; printf "RSS (MB): min=%.1f avg=%.1f max=%.1f\n", rss_min/1024, rss_sum/count/1024, rss_max/1024; printf "CPU %%:    avg=%.1f max=%.1f\n", cpu_sum/count, cpu_max }' "$RESULTS"

echo ""
echo "=== Claude Output ==="
cat /tmp/claude_output.log

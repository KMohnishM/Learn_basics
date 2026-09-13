#!/bin/bash
set -e

THRESHOLD=80
# Use absolute path for cron jobs because cron runs in a restricted environment
LOG_FILE="/tmp/system_monitor.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Notice the 'while true' loop is gone. We only run this once.
top -b -n 1 | awk -v threshold="$THRESHOLD" -v time="$TIMESTAMP" '
  NR>7 && $9+0 > threshold {
    printf "[%s] WARNING: High CPU! Process: %s (PID: %s), CPU: %s%%, MEM: %s%%\n", time, $12, $1, $9, $10
  }
' >> "$LOG_FILE"

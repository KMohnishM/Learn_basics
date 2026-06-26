#!/bin/bash

# ==============================================================================
# DevOps Guided Lab: Process Monitoring Script
# Objective: Learn how to use bash, awk, and standard linux utilities to 
#            monitor system performance automatically.
# ==============================================================================

# Exit immediately if a command exits with a non-zero status.
# This is a DevOps best practice for bash scripts to prevent cascading failures.
set -e

# Define variables
THRESHOLD=80
LOG_FILE="system_monitor.log"

echo "Starting system monitor... (Press Ctrl+C to stop)"
echo "Logging CPU warnings to $LOG_FILE if usage exceeds $THRESHOLD%"

# Infinite loop to continuously monitor
while true; do
  # Get the current date and time
  TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

  # We use 'top' to get process info.
  # -b: Batch mode (output to text, not interactive UI)
  # -n 1: Only run 1 iteration
  # We pipe (|) the output into 'awk' to parse the text.
  
  # awk logic:
  # NR>7: Skip the first 7 lines of top output (which are headers)
  # $9+0 > THRESHOLD: Check if column 9 (CPU%) is greater than our threshold.
  # print: Format the output string.
  
  top -b -n 1 | awk -v threshold="$THRESHOLD" -v time="$TIMESTAMP" '
    NR>7 && $9+0 > threshold {
      # $1=PID, $2=USER, $9=CPU%, $10=MEM%, $12=COMMAND
      printf "[%s] WARNING: High CPU! Process: %s (PID: %s), CPU: %s%%, MEM: %s%%\n", time, $12, $1, $9, $10
    }
  ' >> "$LOG_FILE"

  # Sleep for 5 seconds before checking again
  sleep 5
done

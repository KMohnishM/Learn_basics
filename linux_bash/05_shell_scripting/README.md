# Module 5: Shell Scripting

This module covers shell scripting in Bash in deep technical detail.

## 1. Script Fundamentals

A bash script is a text file containing a series of commands. When executed, the commands are run in order.

### The Shebang

The first line of a bash script should be a shebang. A shebang indicates which interpreter should execute the file.
```bash
#!/usr/bin/env bash
```
Using `/usr/bin/env bash` is preferred over `#!/bin/bash` because bash might be installed in a different location (like `/usr/local/bin/bash` on macOS or FreeBSD). `env` searches the `PATH` environment variable for the `bash` executable.

### Execution Permissions

To run a script, it needs execute permissions.
```bash
chmod +x script.sh
./script.sh
```
Without execute permissions, you must run it by passing it to the interpreter:
```bash
bash script.sh
```

### The Unofficial Bash Strict Mode (set -euo pipefail)

To make your scripts robust and secure, always start with:
```bash
set -euo pipefail
```
Let's break this down:

#### set -e (errexit)
Causes the script to exit immediately if any command returns a non-zero exit status (indicates failure).
Without `-e`, bash will continue to the next command even if a command fails, which can cause catastrophic failures downstream.
Exceptions: The script will not exit if the command is part of an `if` statement, connected with `&&` or `||`, or if its exit status is being inverted with `!`.

#### set -u (nounset)
Causes bash to exit with an error when attempting to use an undefined variable.
Without `-u`, undefined variables are treated as empty strings, which can lead to disastrous commands like `rm -rf /$UNDEFINED_VAR/bin`.

#### set -o pipefail
By default, the exit status of a pipeline is the exit status of the last command in the pipe.
If you have a pipeline like `command1 | command2`, and `command1` fails but `command2` succeeds, the overall exit status is 0 (success).
`set -o pipefail` changes this behavior so the exit status of a pipeline is the rightmost non-zero exit status, or zero if all commands succeeded.

#### IFS (Internal Field Separator)
Often included with strict mode is changing the Internal Field Separator:
```bash
IFS=$'\n\t'
```
This prevents word splitting on spaces, which is a common source of bugs when dealing with filenames containing spaces.

## 2. Variables and Data Types

In bash, there are no strict data types by default. Everything is a string, but depending on the context, strings can be evaluated as integers or arrays.

### Variable Assignment
No spaces are allowed around the equals sign.
```bash
NAME="John Doe"
AGE=30
```

### Local Variables
In functions, always use `local` to avoid polluting the global namespace.
```bash
my_func() {
  local temp_dir="/tmp/work"
}
```

### String Operations
Bash has built-in string manipulation capabilities (Parameter Expansion).

#### Default Values
- `${VAR:-default}`: If VAR is unset or null, evaluate to "default".
- `${VAR:=default}`: If VAR is unset or null, set VAR to "default" and evaluate to it.
- `${VAR:+alt}`: If VAR is set and not null, evaluate to "alt" (otherwise empty).
- `${VAR:?error_message}`: If VAR is unset or null, print "error_message" and exit.

#### Substring Extraction
`${STRING:offset:length}`
```bash
TEXT="Hello World"
echo "${TEXT:6:5}"  # Outputs: World
```

#### String Replacement
- `${STRING/pattern/replacement}`: Replace first match.
- `${STRING//pattern/replacement}`: Replace all matches.
- `${STRING/#pattern/replacement}`: Replace prefix.
- `${STRING/%pattern/replacement}`: Replace suffix.

#### String Length
`${#STRING}`
```bash
TEXT="Bash"
echo "${#TEXT}" # Outputs: 4
```

### Indexed Arrays
Arrays in bash are zero-indexed.

```bash
# Declaration
declare -a MY_ARRAY=("apple" "banana" "cherry")

# Accessing elements
echo "${MY_ARRAY[0]}"      # apple
echo "${MY_ARRAY[@]}"      # All elements

# Number of elements
echo "${#MY_ARRAY[@]}"     # 3

# Adding elements
MY_ARRAY+=("date")

# Iterating
for fruit in "${MY_ARRAY[@]}"; do
  echo "Fruit: $fruit"
done
```

### Associative Arrays (Dictionaries)
Requires Bash 4.0+.

```bash
# Declaration
declare -A CAPITALS
CAPITALS=([France]="Paris" [Italy]="Rome" [Japan]="Tokyo")

# Accessing
echo "${CAPITALS[France]}" # Paris

# All keys
echo "${!CAPITALS[@]}"     # France Italy Japan

# Iterating
for country in "${!CAPITALS[@]}"; do
  echo "$country's capital is ${CAPITALS[$country]}"
done
```

## 3. Control Flow — Complete Reference

### if / elif / else
Bash uses `[` (which is a synonym for the `test` command) or `[[` (the newer, advanced test command). Always prefer `[[ ]]` in Bash.

```bash
USER_ID=$(id -u)

if [[ "$USER_ID" -eq 0 ]]; then
  echo "Running as root."
elif [[ "$USER_ID" -eq 1000 ]]; then
  echo "Running as standard user."
else
  echo "Running as other user."
fi
```

### Test Conditions in `[[ ]]`
- String equality: `[[ "$a" == "$b" ]]` (or `=` )
- String inequality: `[[ "$a" != "$b" ]]`
- Empty string: `[[ -z "$a" ]]`
- Non-empty string: `[[ -n "$a" ]]`
- Integer equality: `[[ "$a" -eq "$b" ]]`
- Integer operations: `-ne` (not equal), `-gt` (greater than), `-ge` (greater or equal), `-lt` (less than), `-le` (less or equal)
- File exists: `[[ -e "$file" ]]`
- File is regular file: `[[ -f "$file" ]]`
- File is directory: `[[ -d "$file" ]]`
- File is executable: `[[ -x "$file" ]]`
- Regex matching: `[[ "$string" =~ ^[0-9]+$ ]]`

### for loops

Iterating over a list:
```bash
for item in "apple" "banana" "cherry"; do
  echo "Item: $item"
done
```

Iterating over files (globbing):
```bash
for file in *.txt; do
  [[ -e "$file" ]] || continue # Guard against empty matches
  echo "Processing $file"
done
```

C-style for loop:
```bash
for ((i = 0; i < 5; i++)); do
  echo "i = $i"
done
```

### while loops

```bash
count=0
while [[ $count -lt 5 ]]; do
  echo "Count: $count"
  ((count++))
done
```

Reading a file line by line:
```bash
while IFS= read -r line; do
  echo "Line: $line"
done < "input.txt"
```

### case statement

Used for multiple branches based on a pattern match.
```bash
ACTION="start"

case "$ACTION" in
  start|START)
    echo "Starting service..."
    ;;
  stop|STOP)
    echo "Stopping service..."
    ;;
  restart)
    echo "Restarting service..."
    ;;
  *)
    echo "Unknown action: $ACTION"
    exit 1
    ;;
esac
```

### select statement

Provides a simple menu for user input.
```bash
PS3="Select an environment: "
select env in "dev" "staging" "prod" "quit"; do
  case "$env" in
    dev|staging|prod)
      echo "Deploying to $env..."
      break
      ;;
    quit)
      echo "Exiting."
      break
      ;;
    *)
      echo "Invalid selection."
      ;;
  esac
done
```

## 4. Functions

Functions encapsulate code into reusable blocks.

### Definition
```bash
# Recommended syntax
my_function() {
  local arg1="$1"
  local arg2="$2"
  echo "Executing function with $arg1 and $arg2"
}

# Also valid, but less standard
function my_function2 {
  echo "Another function"
}
```

### Return Values
Bash functions do not return strings or complex data structures. They return an exit status (0-255).
To "return" a string, print it to stdout and capture it using command substitution.

```bash
get_hostname() {
  cat /etc/hostname
  return 0 # Exit status
}

HOST=$(get_hostname)
```

### Error Handling in Functions
If `set -e` is active, a function failing will exit the script.
```bash
check_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "Error: File $file not found" >&2
    return 1
  fi
}
```

### Recursion
Bash supports recursion, but be wary of the depth as it can lead to a stack overflow or excessive memory usage since variables need to be tracked.
```bash
factorial() {
  local num="$1"
  if [[ "$num" -le 1 ]]; then
    echo 1
  else
    local prev
    prev=$(factorial $((num - 1)))
    echo $((num * prev))
  fi
}
```

## 5. Error Handling and Robustness

### The `trap` Command
`trap` catches signals (like SIGINT when you press Ctrl+C) or special conditions (like EXIT or ERR) and executes a command.

```bash
cleanup() {
  echo "Cleaning up temporary files..."
  rm -rf /tmp/my_script_tmp_$$
}

# Execute cleanup on script exit (success or failure)
trap cleanup EXIT
```

### Retry Loops
When interacting with network services or resources that might temporarily fail, implement a retry loop.

```bash
max_retries=5
delay=2
attempt=1

while [[ $attempt -le $max_retries ]]; do
  if curl -sSf https://api.example.com/health; then
    echo "API is up!"
    break
  fi
  echo "Attempt $attempt failed. Retrying in $delay seconds..."
  sleep "$delay"
  ((attempt++))
done

if [[ $attempt -gt $max_retries ]]; then
  echo "Failed after $max_retries attempts."
  exit 1
fi
```

### Input Validation
Always validate inputs to your script.
```bash
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <source_dir> <dest_dir>" >&2
  exit 1
fi

SRC="$1"
DEST="$2"

if [[ ! -d "$SRC" ]]; then
  echo "Error: Source directory $SRC does not exist." >&2
  exit 1
fi
```

## 6. Input / Output Handling

### The `read` Command
Used to prompt the user or read from standard input.

```bash
read -r -p "Enter your name: " name
echo "Hello, $name"
```
Use `-r` to prevent backslashes from acting as escape characters.
Use `-s` to hide input (useful for passwords).

### Logging
Create a robust logging function.

```bash
log() {
  local level="$1"
  shift
  local msg="$*"
  local timestamp
  timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  echo "[$timestamp] [$level] $msg" >&2
}

log INFO "Script started."
log ERROR "File not found."
```
By redirecting to `>&2` (standard error), logs don't interfere with command substitution or standard output if the script's output is being piped.

## 7. Cron and Scheduled Jobs

Cron is a time-based job scheduler.
Edit the crontab with `crontab -e`.

### Cron Syntax
```
* * * * * command to execute
┬ ┬ ┬ ┬ ┬
│ │ │ │ │
│ │ │ │ └─── Day of week (0 - 7) (Sunday=0 or 7)
│ │ │ └────── Month (1 - 12)
│ │ └──────── Day of month (1 - 31)
│ └────────── Hour (0 - 23)
└──────────── Minute (0 - 59)
```

### Cron Best Practices
1. **Absolute Paths**: Always use absolute paths for commands (`/usr/bin/rsync` instead of `rsync`) and files. The PATH in cron is minimal.
2. **Redirect Output**: Cron emails output to the user. To prevent spam, redirect output to a log file or `/dev/null`.
   ```cron
   0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
   ```
3. **Environment Variables**: Cron runs in a minimal environment. Source your profile or declare variables explicitly if needed.
   ```cron
   0 3 * * * . /etc/profile; /opt/scripts/job.sh
   ```

## 8. A Complete Production Script Example (deploy.sh)

Below is an extensive, robust example incorporating best practices.

```bash
#!/usr/bin/env bash

# deploy.sh
# Deploys application artifacts to production servers.

set -euo pipefail
IFS=$'\n\t'

# Constants
readonly APP_NAME="myapp"
readonly DEPLOY_DIR="/var/www/${APP_NAME}"
readonly BACKUP_DIR="/var/backups/${APP_NAME}"
readonly TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
readonly LOG_FILE="/var/log/${APP_NAME}_deploy.log"

# Global state
LOCK_FILE="/tmp/${APP_NAME}_deploy.lock"

# --- Functions ---

log() {
    local level="$1"
    shift
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] [$level] $*" | tee -a "$LOG_FILE" >&2
}

cleanup() {
    log INFO "Cleaning up lock file..."
    rm -f "$LOCK_FILE"
}

aquire_lock() {
    if ! mkdir "$LOCK_FILE" 2>/dev/null; then
        log ERROR "Deploy is already running or lock file is stale ($LOCK_FILE)."
        exit 1
    fi
    trap cleanup EXIT
}

check_dependencies() {
    local deps=("rsync" "systemctl" "tar")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            log ERROR "Required command not found: $dep"
            exit 1
        fi
    done
}

backup_current() {
    log INFO "Creating backup of current deployment..."
    mkdir -p "$BACKUP_DIR"
    if [[ -d "$DEPLOY_DIR" ]]; then
        tar -czf "${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz" -C "$DEPLOY_DIR" .
        log INFO "Backup created at ${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"
    else
        log INFO "No existing deployment found at $DEPLOY_DIR. Skipping backup."
    fi
}

deploy_new() {
    local artifact_path="$1"
    log INFO "Deploying $artifact_path to $DEPLOY_DIR..."
    
    mkdir -p "$DEPLOY_DIR"
    rsync -avz --delete "${artifact_path}/" "$DEPLOY_DIR/"
    
    log INFO "Deployment files copied."
}

restart_service() {
    log INFO "Restarting $APP_NAME service..."
    if ! systemctl restart "$APP_NAME"; then
        log ERROR "Failed to restart service."
        exit 1
    fi
    log INFO "Service restarted successfully."
}

health_check() {
    local max_attempts=10
    local attempt=1
    local delay=3
    local endpoint="http://localhost:8080/health"

    log INFO "Starting health check..."
    while [[ $attempt -le $max_attempts ]]; do
        if curl -sSf "$endpoint" >/dev/null 2>&1; then
            log INFO "Health check passed!"
            return 0
        fi
        log INFO "Attempt $attempt/$max_attempts failed. Waiting $delay seconds..."
        sleep "$delay"
        ((attempt++))
    done

    log ERROR "Health check failed after $max_attempts attempts."
    exit 1
}

usage() {
    echo "Usage: $0 -a <artifact_directory>"
    echo "Options:"
    echo "  -a    Path to the artifact directory to deploy"
    echo "  -h    Show this help message"
}

# --- Main Script ---

main() {
    local artifact_dir=""

    while getopts "a:h" opt; do
        case "$opt" in
            a) artifact_dir="$OPTARG" ;;
            h) usage; exit 0 ;;
            *) usage; exit 1 ;;
        esac
    done

    if [[ -z "$artifact_dir" ]]; then
        log ERROR "Artifact directory must be specified with -a"
        usage
        exit 1
    fi

    if [[ ! -d "$artifact_dir" ]]; then
        log ERROR "Artifact directory does not exist: $artifact_dir"
        exit 1
    fi

    # Require root for deployment
    if [[ $(id -u) -ne 0 ]]; then
        log ERROR "Deployment script must be run as root."
        exit 1
    fi

    aquire_lock
    check_dependencies
    backup_current
    deploy_new "$artifact_dir"
    restart_service
    health_check

    log INFO "Deployment completed successfully."
}

# Execute main function
main "$@"
```

## 9. Advanced Scripting Patterns

### Process Substitution
Process substitution lets you pass the output of a command to another command as if it were a file. It creates a temporary named pipe.
```bash
# Compare the output of two directories
diff <(ls -l dir1) <(ls -l dir2)

# Pass multiple streams to tee
echo "Hello World" | tee >(grep "Hello" > greetings.txt) >(wc -c > size.txt)
```

### Coprocesses
Coprocesses allow you to run a command in the background and establish a two-way communication channel (stdin and stdout) with it.
```bash
coproc MY_PROC { awk '{print "Processed: " $0; fflush()}'; }

echo "Data 1" >&"${MY_PROC[1]}"
read -r response <&"${MY_PROC[0]}"
echo "$response"

echo "Data 2" >&"${MY_PROC[1]}"
read -r response <&"${MY_PROC[0]}"
echo "$response"
```
This avoids creating named pipes manually and provides a clean way to delegate processing to a persistent background worker.

### Here Documents and Here Strings
Here documents (`<<`) are used to pass a multiline string to a command.
```bash
cat << 'EOF' > config.ini
[Server]
Host=127.0.0.1
Port=8080
EOF
```
Quoting `'EOF'` prevents variable expansion inside the block.

Here strings (`<<<`) pass a single string to a command's standard input.
```bash
grep "error" <<< "$LOG_OUTPUT"
```

### The `wait` Command
When you spawn background jobs using `&`, you can use `wait` to pause execution until they complete.
```bash
for file in *.mp4; do
    ffmpeg -i "$file" "${file%.mp4}.mkv" &
done

echo "Waiting for conversions to finish..."
wait
echo "All conversions completed."
```

### Bash Arithmetic and Math
Bash natively supports integer arithmetic using `$(( ... ))`.
```bash
# Addition and assignment
((counter++))
((counter += 5))

# Complex expressions
RESULT=$(( (10 + 5) * 2 / 3 ))
```
For floating-point math, you must rely on external tools like `bc` or `awk`.
```bash
FLOAT_RESULT=$(echo "scale=2; 10 / 3" | bc)
echo "Result: $FLOAT_RESULT" # 3.33
```

## 10. Debugging Bash Scripts

### Using `set -x`
The most common way to debug is to print each command before it executes.
```bash
set -x  # Enable tracing
command1
command2
set +x  # Disable tracing
```

### Trap DEBUG
You can use `trap` to execute a command before every single statement in your script.
```bash
trap 'echo "Executing line $LINENO..."' DEBUG
```

### Dry Runs
Design your scripts to support a "dry run" mode, where commands are printed but not executed.
```bash
DRY_RUN=1

run_cmd() {
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "[DRY RUN] $*"
    else
        "$@"
    fi
}

run_cmd rm -rf /var/www/myapp/tmp/*
```

## Conclusion
Mastering Bash means mastering the Linux operating system. By applying strict mode (`set -euo pipefail`), utilizing functions correctly with local variables, writing defensive and validated code, and understanding process handling, you elevate shell scripting from brittle command sequences to robust systems engineering.

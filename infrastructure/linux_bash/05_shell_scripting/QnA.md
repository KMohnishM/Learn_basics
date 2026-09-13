# Shell Scripting Q&A

**1. What does `set -euo pipefail` do and why is it recommended?**
The `set -euo pipefail` command configures bash to behave more strictly, making scripts robust.
The `-e` flag (errexit) causes the script to exit immediately if any command returns a non-zero exit status, stopping the script before failures cascade.
The `-u` flag (nounset) treats referencing an unset variable as an error, rather than substituting an empty string, which prevents disastrous bugs like `rm -rf /$UNSET_VAR`.
The `-o pipefail` option ensures that if any command in a pipeline fails, the entire pipeline fails, rather than just returning the exit status of the final command.
For example, without pipefail, `cat missing_file.txt | grep "error"` returns 1 because grep fails, but if grep matched something it might return 0 even though `cat` failed.
Applying these settings ensures that scripts fail fast and visibly, reducing silent bugs in production automation.

**2. What is the difference between `$@` and `$*` in bash?**
Both `$@` and `$*` expand to the positional parameters passed to the script or function.
However, their behavior changes significantly when enclosed in double quotes.
When using `"$*"`, it expands all parameters into a single word, separated by the first character of the `IFS` variable (usually a space).
For example, `"$*"` becomes `"arg1 arg2 arg3"`.
When using `"$@"`, each parameter expands to a separate word, preserving any embedded spaces within the arguments.
For example, `"$@"` becomes `"arg1" "arg2" "arg3"`.
In almost all cases, you should use `"$@"` when iterating over arguments in a `for` loop to ensure arguments with spaces are not split.
```bash
for arg in "$@"; do
  echo "Argument: $arg"
done
```

**3. Why is it important to use `local` when defining variables in a bash function?**
By default, all variables in bash are global, even if they are defined inside a function.
If you define a variable without `local` inside a function, it will overwrite any existing global variable with the same name.
This causes unexpected side effects and makes scripts extremely difficult to debug, especially in large codebases.
Using `local` restricts the scope of the variable to the function itself and its children.
```bash
function my_func() {
  local count=10 # Does not overwrite global $count
  echo $count
}
count=5
my_func
echo $count # Still outputs 5
```
Always use `local` for variables declared inside functions to ensure encapsulation.

**4. How do parameter expansion defaults (`:-`, `:=`, `:+`, `:?`) work?**
Bash provides parameter expansion to conditionally manipulate variable values.
`${VAR:-default}` substitutes "default" if VAR is unset or null, but does not modify VAR.
`${VAR:=default}` assigns "default" to VAR if it is unset or null, and then substitutes that value. This is useful for initializing defaults.
`${VAR:+alt}` substitutes "alt" if VAR is set and not null, otherwise substitutes nothing.
`${VAR:?message}` prints "message" to standard error and exits the script if VAR is unset or null.
```bash
echo "${USER_ID:-1000}" # Outputs 1000 if USER_ID is unset
${CONFIG_FILE:?"Configuration file must be provided"}
```
These features eliminate the need for verbose `if` statements just to handle default variable assignments.

**5. What is the difference between single bracket `[ ]` and double bracket `[[ ]]` tests?**
The single bracket `[ ]` is a POSIX standard command (equivalent to `test`), meaning it is compatible across many shells.
However, because it's a regular command, variable expansions inside it are subject to word splitting and globbing if not quoted.
The double bracket `[[ ]]` is a bash keyword that provides advanced testing capabilities.
It does not perform word splitting or filename expansion on its arguments, making it much safer.
Additionally, `[[ ]]` supports logical operators `&&` and `||` directly, unquoted pattern matching, and regular expression matching with `=~`.
```bash
# Safe regex match with double brackets
if [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$ ]]; then
  echo "Valid email"
fi
```
Always use `[[ ]]` in bash scripts unless you explicitly require POSIX compatibility for `sh`.

**6. How do you write a robust retry loop in bash?**
A retry loop attempts a command multiple times before failing, useful for network operations.
You need a loop, a counter, a delay, and a condition check.
```bash
max_retries=5
delay=10
attempt=1
while [[ $attempt -le $max_retries ]]; do
  if curl -sSf https://api.example.com/status > /dev/null; then
    echo "Success!"
    break
  fi
  echo "Attempt $attempt failed. Retrying in $delay seconds..."
  sleep $delay
  ((attempt++))
done
if [[ $attempt -gt $max_retries ]]; then
  echo "Operation failed after $max_retries attempts."
  exit 1
fi
```
This pattern ensures your script gracefully handles transient network errors instead of failing immediately.

**7. How and why do you use `trap cleanup EXIT`?**
The `trap` command allows you to catch signals and execute code when the script receives them.
Using `trap 'command' EXIT` ensures that the specified command runs when the script exits, regardless of whether it exits successfully or due to an error (like `set -e`).
This is crucial for robust scripting to guarantee that temporary files, network connections, or lock files are cleaned up.
```bash
TMP_DIR=$(mktemp -d)
cleanup() {
  echo "Cleaning up temporary directory..."
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT
# Script logic using TMP_DIR
```
Without `trap EXIT`, an unexpected error in the script could leave temporary files cluttering the filesystem permanently.

**8. What are the best practices for setting up cron jobs using bash scripts?**
Cron runs with a very restricted environment, so environment variables like `PATH` are often missing or minimal.
Therefore, you must use absolute paths for commands inside your script (e.g., `/usr/bin/rsync`) or explicitly set the `PATH` at the top of the script.
Additionally, cron sends all output to the user's local email. To prevent spam and capture logs, redirect standard output and standard error.
```cron
0 * * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```
It is also good practice to source the user profile (`. /etc/profile`) if the script relies on specific environment variables.
Finally, ensure the script is executable and uses an explicit shebang like `#!/usr/bin/env bash`.

**9. What are process substitution `<(cmd)` and `>(cmd)`?**
Process substitution allows the output or input of a command to be treated as a file.
It creates a temporary named pipe (`/dev/fd/<n>`) that commands expecting a file can read from or write to.
`<(cmd)` runs `cmd` and connects its output to a file descriptor, which is substituted on the command line.
`>(cmd)` runs `cmd` and connects its input to a file descriptor.
```bash
# Compare the output of two commands without creating temp files
diff <(ls dir1) <(ls dir2)

# Write output to multiple processes simultaneously
echo "Data" | tee >(grep "D" > result.txt) >(wc -c > count.txt)
```
This completely eliminates the need for temporary files when passing command outputs to tools that only accept file paths.

**10. What is `IFS` and why might you set `IFS=$'\n\t'`?**
`IFS` stands for Internal Field Separator, which bash uses for word splitting after expansion and for the `read` builtin.
By default, `IFS` contains space, tab, and newline.
This default causes problems when iterating over elements (like filenames) that contain spaces, as bash will split a single filename with spaces into multiple arguments.
Setting `IFS=$'\n\t'` restricts word splitting to only newlines and tabs, ignoring spaces.
```bash
IFS=$'\n\t'
for file in $(find . -type f -name "*.txt"); do
  # This loop safely handles filenames with spaces
  echo "Processing $file"
done
```
This is a core component of writing safe, predictable bash scripts that interact with the filesystem.

**11. How do you correctly read a file line by line without splitting on spaces?**
To read a file line by line safely, you should use a `while` loop combined with the `read` command.
Crucially, you must clear the `IFS` variable for the `read` command so it doesn't trim leading or trailing whitespace.
You also use the `-r` flag with `read` to prevent backslashes from being interpreted as escape characters.
```bash
while IFS= read -r line; do
  echo "Read: $line"
done < "input.txt"
```
This guarantees that the exact contents of each line are preserved exactly as they appear in the file, regardless of whitespace or special characters.

**12. How do associative arrays work in bash and how do you use them?**
Associative arrays (often called dictionaries or hash maps) map string keys to string values, introduced in Bash 4.0.
You must explicitly declare an associative array using `declare -A`.
```bash
declare -A server_roles
server_roles=([web]="nginx" [db]="postgresql" [cache]="redis")

# Accessing a value
echo "Web server is ${server_roles[web]}"

# Iterating over keys
for role in "${!server_roles[@]}"; do
  echo "Role: $role uses ${server_roles[$role]}"
done
```
They are invaluable for lookup tables and mapping configurations directly within a shell script without relying on external tools.

**13. How do you implement a simple lock file using `mkdir`?**
A lock file prevents multiple instances of a script from running simultaneously.
While `touch` is prone to race conditions, `mkdir` is an atomic operation in POSIX filesystems.
If `mkdir` succeeds, the directory was created and you hold the lock. If it fails, the directory exists and another instance holds the lock.
```bash
LOCK_DIR="/tmp/myscript.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "Script is already running."
  exit 1
fi
# Ensure lock is removed on exit
trap 'rm -rf "$LOCK_DIR"' EXIT
```
This is a standard, robust way to implement concurrency control purely using bash and filesystem semantics.

**14. Why should you use `command -v` instead of `which` in scripts?**
The `which` command is an external utility, not a shell builtin, and its behavior or even existence can vary across different Unix-like systems.
It might also behave unpredictably with shell aliases or functions.
`command -v` is a POSIX-compliant shell builtin designed specifically to locate commands.
```bash
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required but not installed." >&2
  exit 1
fi
```
Using `command -v` is faster (since it doesn't fork a new process) and far more reliable and portable than relying on `which`.

**15. How does the `select` built-in menu system work?**
The `select` construct provides an easy way to generate an interactive menu for the user.
It prints a numbered list of choices based on the provided arguments, prompts the user using the `PS3` variable, and stores the selected text in a variable.
```bash
PS3="Choose your deployment environment: "
select env in "Development" "Staging" "Production" "Quit"; do
  case $env in
    "Development"|"Staging"|"Production")
      echo "Deploying to $env..."
      break ;;
    "Quit")
      echo "Exiting."
      break ;;
    *) echo "Invalid choice. Please try again." ;;
  esac
done
```
It simplifies building interactive CLI tools directly in bash without needing complex input validation loops.

# Bash Scripting Cheatsheet

## Script Setup & Strict Mode
| Command / Syntax | Description |
| :--- | :--- |
| `#!/usr/bin/env bash` | Recommended shebang for portability. |
| `set -euo pipefail` | Unofficial strict mode. Fails on errors, unset vars, and pipe failures. |
| `IFS=$'\n\t'` | Prevents word splitting on spaces. |
| `chmod +x script.sh` | Make script executable. |

## Variables & Parameter Expansion
| Syntax | Description |
| :--- | :--- |
| `VAR="value"` | Variable assignment (no spaces!). |
| `local VAR="value"` | Define local variable in functions. |
| `${VAR:-default}` | Use "default" if VAR is unset/null. |
| `${VAR:=default}` | Assign "default" to VAR if unset/null. |
| `${VAR:?error}` | Exit with "error" if VAR is unset/null. |
| `${#VAR}` | Length of the string VAR. |
| `${VAR:2:4}` | Substring: start at index 2, length 4. |
| `${VAR/pattern/repl}` | Replace first match of pattern with repl. |
| `${VAR//pattern/repl}`| Replace all matches of pattern with repl. |

## Arrays & Dictionaries
| Operation | Syntax |
| :--- | :--- |
| Declare Array | `declare -a arr=("a" "b" "c")` |
| Add Element | `arr+=("d")` |
| All Elements | `"${arr[@]}"` |
| Array Length | `"${#arr[@]}"` |
| Declare Dict | `declare -A dict=([k1]="v1" [k2]="v2")` |
| Dict Value | `"${dict[k1]}"` |
| Dict Keys | `"${!dict[@]}"` |

## Conditional Tests `[[ ]]`
| Test | Condition |
| :--- | :--- |
| `[[ -z "$str" ]]` | String is empty. |
| `[[ -n "$str" ]]` | String is not empty. |
| `[[ "$a" == "$b" ]]` | Strings are equal. |
| `[[ "$a" != "$b" ]]` | Strings are not equal. |
| `[[ "$a" -eq "$b" ]]` | Integers are equal. |
| `[[ "$a" -gt "$b" ]]` | Integer `$a` is greater than `$b`. |
| `[[ -e "$file" ]]` | File exists. |
| `[[ -d "$dir" ]]` | Directory exists. |
| `[[ -x "$file" ]]` | File is executable. |
| `[[ "$str" =~ regex ]]`| String matches regular expression. |

## Control Flow
### If / Else
```bash
if [[ condition ]]; then
  # do something
elif [[ condition ]]; then
  # do something else
else
  # default action
fi
```

### For Loop (List)
```bash
for item in "apple" "banana"; do
  echo "$item"
done
```

### While Loop (Read File)
```bash
while IFS= read -r line; do
  echo "$line"
done < "file.txt"
```

### Case Statement
```bash
case "$VAR" in
  start|START) echo "Starting" ;;
  stop)        echo "Stopping" ;;
  *)           echo "Unknown" ;;
esac
```

## Functions
```bash
my_function() {
  local arg1="$1"
  local arg2="$2"
  echo "Processed $arg1 and $arg2"
  return 0 # Exit status
}

# Calling
my_function "val1" "val2"
```

## Error Handling & Traps
| Syntax | Description |
| :--- | :--- |
| `trap 'rm -f tmp' EXIT` | Run cleanup command when script exits. |
| `command >/dev/null 2>&1`| Discard standard output and error. |
| `echo "Error" >&2` | Write message to standard error. |
| `command -v util` | Check if a utility exists safely. |

## Process Substitution
| Syntax | Description |
| :--- | :--- |
| `<(command)` | Run command and treat output as a file. |
| `>(command)` | Run command and treat input as a file. |
| `diff <(ls dir1) <(ls dir2)` | Compare outputs without temp files. |

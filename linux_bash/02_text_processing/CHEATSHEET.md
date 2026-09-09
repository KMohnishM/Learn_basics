# CHEATSHEET: Linux Text Processing and Redirection

## Grep Flags Quick Reference

| Flag | Name | Description | Example |
| :--- | :--- | :--- | :--- |
| `-i` | Ignore Case | Case-insensitive matching | `grep -i "error" log.txt` |
| `-n` | Line Number | Precede output lines with line numbers | `grep -n "TODO" script.sh` |
| `-v` | Invert Match | Select non-matching lines | `grep -v "DEBUG" app.log` |
| `-E` | Extended Regex | Enable ERE (no escaping for `+?|()`) | `grep -E '(fail|error)' log.log` |
| `-P` | Perl Regex | Enable PCRE (lookarounds, advanced) | `grep -P '(?<=IP: )\d+' file.txt` |
| `-c` | Count | Print only a count of matching lines | `grep -c "Exception" app.log` |
| `-l` | Files With Matches| Print only names of files containing matches | `grep -l "password" conf/*` |
| `-L` | Files W/O Matches| Print only names of files *without* matches| `grep -L "secure" conf/*` |
| `-r` | Recursive | Search directories recursively | `grep -r "192.168" /etc/` |
| `-w` | Word Match | Force pattern to match only whole words | `grep -w "is" file.txt` |
| `-x` | Line Match | Force pattern to match the entire line | `grep -x "success" status.txt` |
| `-A n` | After Context | Print *n* lines of trailing context | `grep -A 3 "Error" log.txt` |
| `-B n` | Before Context | Print *n* lines of leading context | `grep -B 2 "Restart" log.txt` |
| `-C n` | Context | Print *n* lines of context before and after | `grep -C 3 "Crash" log.txt` |

## Sed Substitution Patterns

| Operation | Syntax / Example | Description |
| :--- | :--- | :--- |
| Basic Sub | `sed 's/foo/bar/'` | Replaces first instance of `foo` with `bar` per line |
| Global Sub | `sed 's/foo/bar/g'` | Replaces all instances of `foo` with `bar` |
| Case Insensitive | `sed 's/foo/bar/gI'` | Replaces all instances, ignoring case (GNU sed) |
| Diff Delimiter | `sed 's#/var/log#/mnt/log#g'` | Uses `#` as delimiter to avoid escaping slashes `/` |
| Backreferences | `sed -E 's/(.*) (.*)/\2 \1/'` | Swaps the first and second words (ERE syntax) |
| In-Place Edit | `sed -i.bak 's/A/B/g' file` | Modifies file on disk and creates a `.bak` backup |
| Specific Line | `sed '5s/A/B/'` | Substitutes only on line 5 |
| Deletion | `sed '/pattern/d'` | Deletes all lines matching `pattern` |

## Awk Built-In Variables

| Variable | Description |
| :--- | :--- |
| `$0` | Represents the entire current record (line) |
| `$1, $n` | Represents the 1st, or *n*th field of the current record |
| `NR` | Number of Records (global line number across all files) |
| `FNR` | File Number of Records (line number in the current file) |
| `NF` | Number of Fields in the current record (can be used to get last field: `$NF`) |
| `FS` | Field Separator (input delimiter, default is whitespace) |
| `OFS` | Output Field Separator (default is space) |
| `RS` | Record Separator (default is newline) |
| `ORS` | Output Record Separator (default is newline) |

## Redirection Operators

| Operator | Action | Example |
| :--- | :--- | :--- |
| `>` | Redirect stdout, overwrite file | `echo "text" > file.txt` |
| `>>` | Redirect stdout, append to file | `echo "more" >> file.txt` |
| `2>` | Redirect stderr to file | `ls /fake 2> errors.log` |
| `2>&1` | Redirect stderr to stdout (portable) | `script.sh > all.log 2>&1` |
| `&>` | Redirect stdout and stderr (Bash) | `script.sh &> all.log` |
| `<` | Redirect file contents to stdin | `sort < data.txt` |
| `<<` | Here Document (multi-line stdin) | `cat << EOF > new.sh ... EOF` |
| `<<<` | Here String (single string stdin) | `grep "foo" <<< "foobar"` |
| `\|` | Pipe stdout to next command's stdin | `cat log.txt \| grep "ERROR"` |
| `\|&` | Pipe stdout and stderr (Bash 4.0+) | `make \|& tee build.log` |

## Pipe Patterns

**Top N Items Frequency:**
```bash
cat file.txt | sort | uniq -c | sort -nr | head -n 10
```

**Extracting CSV Column and Summarizing (Summing):**
```bash
awk -F',' '{sum += $3} END {print sum}' data.csv
```

**Parallel Command Execution on Files:**
```bash
find . -name "*.jpg" | xargs -I{} -P 4 convert {} -resize 50% {}_small.jpg
```

**Viewing output while saving it to a file requiring sudo:**
```bash
echo "192.168.1.10 web.local" | sudo tee -a /etc/hosts
```

## Regex Metacharacters (BRE vs ERE vs PCRE)

| Feature | BRE (grep, sed) | ERE (grep -E, sed -E) | PCRE (grep -P) | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Any Char** | `.` | `.` | `.` | Matches any single character |
| **Zero/More**| `*` | `*` | `*` | Quantifier: 0 or more times |
| **One/More** | `\+` | `+` | `+` | Quantifier: 1 or more times |
| **Zero/One** | `\?` | `?` | `?` | Quantifier: 0 or 1 time |
| **OR logic** | `\|` | `|` | `|` | Logical alternation (OR) |
| **Grouping** | `\(\)` | `()` | `()` | Creates a capture group |
| **Bounds** | `\{n,m\}` | `{n,m}` | `{n,m}` | Matches exactly between n and m times |
| **Anchors** | `^`, `$` | `^`, `$` | `^`, `$` | Matches start `^` and end `$` of line |
| **Lookahead**| *N/A* | *N/A* | `(?=...)` | Positive Lookahead (matches if followed by) |
| **Lookbehind**| *N/A* | *N/A* | `(?<=...)` | Positive Lookbehind (matches if preceded by) |
| **Digit** | `[0-9]` | `[0-9]` | `\d` | Matches a number |
| **Word Char**| `[a-zA-Z0-9_]`| `[a-zA-Z0-9_]` | `\w` | Matches an alphanumeric char or underscore|

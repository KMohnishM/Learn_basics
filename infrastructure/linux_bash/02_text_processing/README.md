# Module 2: Text Processing and Redirection in Linux Bash

## 1. Introduction and Philosophy

The Unix philosophy, profoundly influential in Linux system administration, emphasizes a modular approach to software design. One of its core tenets is: "Write programs to handle text streams, because that is a universal interface." This principle has led to the development of numerous small, highly specialized utilities designed to perform one task exceptionally well. When these utilities are combined using pipes and redirection, they form a powerful text-processing engine capable of handling complex data manipulation tasks without the need for writing extensive scripts in languages like Python or Perl.

Text streams in Linux are simply sequences of characters. They can originate from files, hardware devices, or the output of other programs. By standardizing on plain text, Linux ensures that the output of one program can seamlessly become the input of another. This module explores the most essential of these utilities—grep, sed, awk, cut, sort, uniq, and tr—along with the mechanics of redirection and pipelines that bind them together.

Understanding these tools deeply is not just about memorizing syntax; it is about adopting a mindset where data is fluid, and complex transformations are just a pipeline away. We will delve into the historical context, edge cases, advanced flags, and practical scenarios for each tool, ensuring you are equipped to handle any text-processing challenge in a production environment.

When we talk about text processing, we are really talking about standard streams. Standard input (stdin), standard output (stdout), and standard error (stderr) are the foundational pillars of how Linux applications communicate. By mastering the redirection of these streams and applying regex-powered filtering through grep, sed, and awk, an engineer gains surgical precision over the OS.

## 2. Grep (Global Regular Expression Print)

### Historical Context
The name "grep" originates from the `ed` editor command `g/re/p`, which stands for "globally search for a regular expression and print matching lines." Since its inception in the early 1970s, grep has become indispensable for searching plain-text data sets for lines that match a regular expression. Over the decades, GNU grep has been highly optimized, employing algorithms like Boyer-Moore to skip characters and search massive files in milliseconds.

### Basic vs. Extended vs. Perl Regular Expressions
Grep supports different flavors of regular expressions, which determine how pattern matching is evaluated.

1. **Basic Regular Expressions (BRE):** The default behavior of `grep`. In BRE, metacharacters like `?`, `+`, `{`, `}`, `|`, and `()` lose their special meaning unless escaped with a backslash `\`. This makes BRE somewhat cumbersome for complex queries but ensures backward compatibility with ancient Unix scripts.
2. **Extended Regular Expressions (ERE):** Activated with `grep -E` (historically `egrep`). Here, metacharacters retain their special meaning without escaping. This makes complex patterns significantly easier to read and write. For example, `grep -E 'error|warning'` is far more legible than `grep 'error\|warning'`.
3. **Perl-Compatible Regular Expressions (PCRE):** Activated with `grep -P`. PCRE is the most feature-rich regex flavor, offering advanced capabilities like lookarounds (lookahead and lookbehind), non-greedy quantifiers, and complex character classes. This is crucial when you need to extract specific strings based on surrounding context without printing the context itself.

### Advanced Flags and Practical Examples

*   **`-i` (Ignore Case):** Matches both uppercase and lowercase characters.
    ```bash
    # Match Error, error, ERROR, eRrOr
    grep -i "error" /var/log/syslog
    ```

*   **`-n` (Line Number):** Prefixes each matching line with its line number within the file. Crucial for debugging source code or logs.
    ```bash
    # Find where the variable is defined and get the exact line
    grep -n "MAX_RETRIES" config.py
    ```

*   **`-c` (Count):** Suppresses normal output and instead prints a count of matching lines for each input file.
    ```bash
    # How many times did a failed login happen?
    grep -c "Failed password" /var/log/auth.log
    ```

*   **`-l` (Files with Matches):** Suppresses normal output; instead, prints the name of each input file from which output would normally have been printed.
    ```bash
    # Find which config files define a specific database host
    grep -l "db.internal.corp" /etc/nginx/sites-available/*
    ```

*   **`-L` (Files without Matches):** The inverse of `-l`. Prints the names of files that do *not* contain the pattern.
    ```bash
    # Find scripts that are missing a shebang
    grep -L "^#!" /usr/local/bin/*.sh
    ```

*   **`-v` (Invert Match):** Inverts the sense of matching, to select non-matching lines. Often used to filter out noise.
    ```bash
    # View processes but exclude the grep process itself
    ps aux | grep "python" | grep -v "grep"
    ```

*   **`-r` or `-R` (Recursive):** Reads all files under each directory recursively. `-R` follows all symbolic links, while `-r` does not.
    ```bash
    # Search the entire /etc directory for a specific IP
    grep -r "192.168.1.50" /etc/
    ```

*   **`-w` (Word Regexp):** Selects only those lines containing matches that form whole words. It prevents substring matches.
    ```bash
    # Match the variable "count", but not "counter" or "discount"
    grep -w "count" script.sh
    ```

*   **`-x` (Line Regexp):** Selects only those matches that exactly match the whole line.
    ```bash
    # Only match if the line is exactly "status=OK" with no other characters
    grep -x "status=OK" health_check.log
    ```

*   **`-A NUM`, `-B NUM`, `-C NUM` (Context Control):** Prints NUM lines of trailing (`-A`), leading (`-B`), or both (`-C`) context after/before matching lines. Places a line containing a group separator (`--`) between contiguous groups of matches.
    ```bash
    # Show the line with the exception, plus the 5 lines of stack trace following it
    grep -A 5 "NullPointerException" app.log
    
    # Show 2 lines before the reboot event to see what triggered it
    grep -B 2 "systemd: Stopped" syslog
    
    # Show full context around a configuration block
    grep -C 3 "server_name" nginx.conf
    ```

*   **`-m NUM` (Max Count):** Stop reading a file after NUM matching lines. Useful for large files when you only need the first few occurrences.
    ```bash
    # Quickly verify if a giant SQL dump contains a specific table definition
    grep -m 1 "CREATE TABLE users" database.sql
    ```

### Edge Cases and Performance
When searching massive files (e.g., multi-gigabyte logs), grep can be bottlenecked by I/O and CPU context switching related to internationalization. Using `LC_ALL=C grep` can significantly speed up execution because it forces grep to use the standard C locale, bypassing complex UTF-8 character decoding if you only need ASCII matching.

```bash
# Up to 10x faster on huge ASCII log files
LC_ALL=C grep "pattern" huge_log.txt
```

Another edge case is searching binary files. By default, grep might complain "Binary file matches". Use `-a` or `--text` to force grep to treat the binary as text, or `-I` to explicitly ignore binary files.

```bash
# Ignore binary files completely during a recursive search
grep -rI "secret_key" /var/www/
```

## 3. Sed (Stream Editor)

### Architecture and Philosophy
Sed is a non-interactive stream editor. It receives text input (from a file or a pipe), performs specified operations on that text line by line, and outputs the result. Sed operates using two data buffers: the **pattern space** and the **hold space**. 

The pattern space is where the current line is read and modified. It is essentially a short-term memory buffer. The hold space is a secondary buffer for long-term storage across cycles, enabling sed to perform complex multi-line logic and stateful operations. Most basic operations only use the pattern space.

### Core Operations

#### Substitution (`s`)
The most common sed operation. It replaces occurrences of a regular expression with a replacement string.
Syntax: `s/regexp/replacement/flags`

```bash
# Replace the first occurrence of 'foo' with 'bar' on each line
sed 's/foo/bar/' file.txt

# Replace all occurrences (global flag 'g')
sed 's/foo/bar/g' file.txt

# Case-insensitive replacement (GNU sed flag 'I')
sed 's/foo/bar/gI' file.txt

# Use a different delimiter (e.g., '#' or '|') to avoid escaping slashes in paths
sed 's#/var/log#/var/opt/log#g' config.conf

# Using capture groups (backreferences) to rearrange data
# Swapping the first and second words on a line
sed -E 's/^([A-Za-z]+) ([A-Za-z]+)/\2 \1/' names.txt
```

#### Addressing
You can restrict sed commands to specific lines by using addresses before the command. Addresses can be line numbers or regular expressions.

```bash
# Substitute only on line 5
sed '5s/foo/bar/g' file.txt

# Substitute from line 10 to 20
sed '10,20s/foo/bar/g' file.txt

# Substitute on lines matching 'start'
sed '/start/s/foo/bar/g' file.txt

# Delete lines 5 through 10
sed '5,10d' file.txt

# Delete lines matching a pattern
sed '/DEBUG/d' file.txt

# Apply multiple commands to a specific block using braces
sed '/start_block/,/end_block/ { s/foo/bar/g; /ignore/d }' file.txt
```

#### Deletion (`d`), Insertion (`i`), Appending (`a`), and Printing (`p`)

*   **Deletion (`d`):** Deletes the pattern space and starts the next cycle.
    ```bash
    # Remove empty lines
    sed '/^$/d' file.txt
    
    # Remove lines consisting only of spaces or tabs
    sed '/^[[:space:]]*$/d' file.txt
    
    # Remove comments (lines starting with #)
    sed '/^#/d' config.ini
    ```

*   **Insertion (`i`):** Inserts text *before* the current line.
    ```bash
    # Insert a header before line 1
    sed '1i\ID,Name,Status' data.csv
    ```

*   **Appending (`a`):** Appends text *after* the current line.
    ```bash
    # Append a footer after the last line ('$')
    sed '$a\End of Report' report.txt
    ```

*   **Printing (`p`):** Prints the pattern space. Often used with `-n` (which suppresses automatic printing) to only print modified or specific lines.
    ```bash
    # Print only lines containing 'ERROR' (mimics grep)
    sed -n '/ERROR/p' log.txt
    
    # Print lines 10 through 20
    sed -n '10,20p' large_file.txt
    ```

### In-Place Editing (`-i`)
The `-i` flag modifies files in place, saving the output back to the original file instead of stdout. 
**Warning:** Always use a backup extension (`-i.bak`) to prevent accidental data loss, especially on macOS where BSD sed requires an extension (e.g., `-i ''` for no backup). Linux GNU sed allows `-i` without an argument, but doing this without a backup is risky in production.

```bash
# Safe in-place editing with backup
sed -i.bak 's/localhost/127.0.0.1/g' config.yml

# Check the diff before removing the backup
diff config.yml.bak config.yml
```

## 4. Awk (Aho, Weinberger, Kernighan)

### History and Structure
Awk is not just a command; it is a complete, Turing-complete programming language designed for text processing and data extraction. Named after its creators (Alfred Aho, Peter Weinberger, and Brian Kernighan), awk processes data line by line (records), breaking each line into fields based on a delimiter (whitespace by default).

An awk program consists of a sequence of `pattern { action }` statements. If the pattern matches the current record, the action is executed.

### Execution Flow: BEGIN and END
*   `BEGIN { ... }`: Executed exactly once *before* any input is read. Ideal for initializing variables, printing headers, or defining field separators explicitly.
*   `END { ... }`: Executed exactly once *after* all input has been processed. Ideal for printing summaries, calculating averages, or aggregating totals.

```awk
awk '
BEGIN { 
    print "Starting processing..."
    print "----------------------"
    total = 0 
}
{ 
    total += $1 
}
END { 
    print "----------------------"
    print "Total sum:", total 
}
' data.txt
```

### Field Printing and Custom Delimiters
Awk variables `$1`, `$2`, etc., refer to the first, second, etc., fields. `$0` refers to the entire record. 
Built-in variables:
*   `NF`: Number of Fields in the current record.
*   `NR`: Number of Records (line number) read globally.
*   `FNR`: Number of Records relative to the current file.
*   `FS`: Field Separator (default is space/tab).
*   `OFS`: Output Field Separator.

The `-F` flag sets the field separator from the command line.

```bash
# Print the 1st and 3rd fields of a CSV, separated by a dash
awk -F',' 'BEGIN {OFS="-"} {print $1, $3}' data.csv

# Print the last field of each line
awk '{print $NF}' file.txt

# Print the second-to-last field
awk '{print $(NF-1)}' file.txt
```

### Patterns, Relational Operators, and Arithmetic
Awk supports complex conditional logic using C-style operators (`==`, `!=`, `>`, `<`, `>=`, `<=`, `&&`, `||`).

```bash
# Print lines where the 3rd field is strictly greater than 100
awk '$3 > 100 {print $0}' data.txt

# Print lines matching a regex in the 2nd field
awk '$2 ~ /^[A-Z]+$/ {print $1, $2}' users.txt

# Do not print if the 1st field is empty
awk '$1 != "" {print $0}' data.txt

# Complex condition: field 1 is "root" AND field 3 is greater than 0
awk '$1 == "root" && $3 > 0 {print $0}' /etc/passwd
```

### String Functions
Awk provides built-in string manipulation.
*   `length(str)`: Returns the length of the string.
*   `substr(str, start, length)`: Extracts a substring.
*   `toupper(str)` / `tolower(str)`: Case conversion.
*   `gsub(regexp, replacement, target)`: Global substitution within a variable.

```bash
# Convert the first field to uppercase
awk '{print toupper($1), $2}' names.txt

# Remove all commas from the 2nd field before printing
awk '{ gsub(/,/, "", $2); print $1, $2 }' finances.txt
```

### Associative Arrays (Dictionaries)
Awk arrays are associative, meaning the keys can be strings. This is incredibly powerful for counting occurrences.

```bash
# Count frequency of each word in the first column
awk '{ count[$1]++ } END { for (word in count) print word, count[word] }' words.txt
```

### Practical Examples
**Extracting IP Addresses from an Apache Log:**
Assuming the IP is the first field:
```bash
awk '{print $1}' /var/log/apache2/access.log | sort | uniq -c | sort -nr | head -n 10
```

**Calculating Average of a Column in a CSV:**
```bash
awk -F',' '
NR > 1 { sum += $3; count++ } 
END { if (count > 0) print "Average:", sum/count }
' grades.csv
```
*(Notice `NR > 1` skips the header row!)*

## 5. Cut, Sort, Uniq, Tr

These utilities are the building blocks of most pipelines. While simple, their advanced flags unlock immense power.

### Cut
Used to remove sections from each line of files. It is faster than awk for simple column extraction but less flexible (cannot easily handle arbitrary amounts of whitespace).
*   `-d`: Delimiter (default is tab).
*   `-f`: Fields to extract.
*   `-c`: Characters to extract (useful for fixed-width data).

```bash
# Extract user and shell from /etc/passwd
cut -d':' -f1,7 /etc/passwd

# Extract characters 5 through 10
cut -c5-10 fixed_data.txt

# Extract fields 1, 3, and everything from 5 onwards
cut -d',' -f1,3,5- data.csv
```

### Sort
Sorts lines of text files. By default, it sorts lexicographically.
*   `-n`: Numeric sort (10 comes after 2, not before).
*   `-r`: Reverse output.
*   `-k`: Sort by a specific key (column).
*   `-t`: Field separator (default is whitespace).
*   `-u`: Unique sort (outputs only unique lines).
*   `-h`: Human-readable numeric sort (handles 1K, 2M, 3G correctly).

```bash
# Sort by the 3rd column numerically, descending, comma separated
sort -t',' -k3 -nr data.csv

# Sort sizes (e.g. from du -h output)
du -h /var/log | sort -h
```
**Locale Edge Case:** Sort behavior is heavily influenced by the `LC_ALL` environment variable. To force strict byte-value sorting (which is much faster and ignores language-specific collation rules), use `LC_ALL=C sort`.

### Uniq
Filters out adjacent matching lines. **Crucial detail:** Uniq only detects duplicates if they are adjacent. You must `sort` the input first!
*   `-c`: Prefix lines by the number of occurrences.
*   `-d`: Only print duplicate lines.
*   `-u`: Only print strictly unique lines (lines that appear exactly once).
*   `-i`: Ignore case when comparing lines.

```bash
# Count occurrences of each IP address
cat ips.txt | sort | uniq -c

# Find lines that appear more than once
sort data.txt | uniq -d
```

### Tr (Translate)
Translates, squeezes, or deletes characters from standard input. It operates on character sets, not regular expressions. It only reads from stdin, so you must redirect files into it or use a pipe.
*   `-d`: Delete characters.
*   `-s`: Squeeze multiple occurrences of a character into a single instance.
*   `-c`: Complement the set of characters.

```bash
# Convert lowercase to uppercase
cat file.txt | tr 'a-z' 'A-Z'

# Squeeze multiple spaces into a single space (great for preparing data for cut)
echo "This   is    spaced" | tr -s ' '

# Delete all carriage returns (DOS to Unix conversion)
tr -d '\r' < windows_file.txt > unix_file.txt

# Keep only alphanumeric characters and newlines
cat messy_data.txt | tr -cd '[:alnum:]\n'
```

## 6. Pipes and Redirection

Linux provides three standard file descriptors for every process:
0.  **Standard Input (stdin):** Where the program reads input.
1.  **Standard Output (stdout):** Where the program writes normal output.
2.  **Standard Error (stderr):** Where the program writes error messages.

### Redirection Operators
*   `>`: Redirects stdout to a file, overwriting the file.
    ```bash
    echo "Hello" > file.txt
    ```
*   `>>`: Redirects stdout to a file, appending to the file.
    ```bash
    echo "World" >> file.txt
    ```
*   `2>`: Redirects stderr to a file.
    ```bash
    ls /nonexistent 2> errors.log
    ```
*   `2>&1`: Redirects stderr to wherever stdout is currently pointing. This is the POSIX-compliant way to combine them. Order matters! `> output.log 2>&1` means point stdout to file, then point stderr to stdout.
    ```bash
    command > output.log 2>&1
    ```
*   `&>`: Bash-specific shorthand for redirecting both stdout and stderr to the same file.
    ```bash
    command &> output.log
    ```
*   `<`: Redirects stdin from a file.
    ```bash
    sort < input.txt
    ```
*   `<<` (Here Document): Redirects a block of text into stdin until a delimiter is found. Quotes around EOF (`'EOF'`) prevent variable expansion.
    ```bash
    cat << 'EOF' > script.sh
    #!/bin/bash
    echo "Generated script"
    echo "My path is $PATH"
    EOF
    ```
*   `<<<` (Here String): Redirects a single string into stdin.
    ```bash
    grep "root" <<< "This string contains root access"
    ```

### Pipes (`|`)
Pipes connect the stdout of one command directly to the stdin of another, allowing data to flow seamlessly between utilities.
```bash
dmesg | grep -i "usb" | less
```
Note that pipes only capture stdout. To pipe stdout and stderr, use `|&` (bash 4.0+) or `2>&1 |`.

### Tee
The `tee` command reads from stdin and writes to both stdout and one or more files. It creates a "T-junction" in a pipeline, which is invaluable for logging a long-running process while still monitoring it on the console.
*   `-a`: Append to the file instead of overwriting.

```bash
# View output on screen while also saving to a file
make build | tee build.log

# Append to a file requiring sudo privileges (since sudo > file doesn't work)
echo "127.0.0.1 db.local" | sudo tee -a /etc/hosts
```

### Xargs
Xargs reads items from stdin (separated by whitespace or newlines) and executes a command one or more times with those items as arguments. It bridges the gap for commands that don't read from stdin directly (like `rm`, `cp`, or `mkdir`).

*   `-I{}`: Defines a placeholder for the argument, allowing it to be placed anywhere in the command.
*   `-P`: Run commands in parallel up to a maximum number of processes.
*   `-0` or `--null`: Read null-terminated input, essential when file names contain spaces (usually paired with `find -print0`).

```bash
# Find all .tmp files and delete them safely (handling spaces in filenames)
find . -name "*.tmp" -print0 | xargs -0 rm -f

# Move multiple files to a directory
ls *.jpg | xargs -I{} mv {} /images/backup/

# Download URLs in parallel (4 workers)
cat urls.txt | xargs -n 1 -P 4 wget
```

### Process Substitution (`<()`, `>()`)
Process substitution allows the output of a command to be treated as a temporary file. This is useful when a command expects a file name argument, but you want to provide the output of another command without manually creating intermediate files.

```bash
# Diff the output of two commands directly
diff <(ls dir1) <(ls dir2)

# Pass output to two different tools at once using tee and process substitution
command | tee >(grep "ERROR" > errors.log) >(grep "WARN" > warnings.log) > all.log
```

## 7. Regular Expressions in Depth

Regular expressions are the theoretical backbone of text processing. A deep understanding of their syntax is non-negotiable for advanced Linux administration.

### Basic Regular Expressions (BRE)
Used by standard `grep` and `sed`.
*   `.`: Matches any single character except newline.
*   `*`: Matches zero or more occurrences of the preceding element.
*   `^`: Matches the start of a line (anchor).
*   `$`: Matches the end of a line (anchor).
*   `[abc]`: Matches any one character in the set (a, b, or c).
*   `[^abc]`: Matches any character NOT in the set.
*   `[a-z]`: Character range.

*Escaping required for extended features in BRE:*
*   `\+`: One or more occurrences.
*   `\?`: Zero or one occurrence.
*   `\|`: Alternation (OR).
*   `\(\)`: Grouping (for backreferences or applying quantifiers).
*   `\{n,m\}`: Range quantifier (between n and m times).

### Extended Regular Expressions (ERE)
Used by `grep -E` (egrep) and `sed -E` (or `sed -r` in GNU sed). Metacharacters `+`, `?`, `|`, `()`, and `{}` do *not* require escaping. This makes patterns readable.

**BRE Example:** `grep '\(error\|fail\)\+' log.txt`
**ERE Example:** `grep -E '(error|fail)+' log.txt`

### Perl-Compatible Regular Expressions (PCRE)
Used by `grep -P`. Offers immense power for complex pattern matching.
*   `\d`: Matches any digit (equivalent to `[0-9]`).
*   `\D`: Matches any non-digit.
*   `\w`: Matches any word character (`[a-zA-Z0-9_]`).
*   `\W`: Matches any non-word character.
*   `\s`: Matches whitespace (space, tab, newline).
*   `\S`: Matches non-whitespace.
*   `\b`: Word boundary (the transition between a word and non-word character).
*   `(?=pattern)`: Positive lookahead (matches only if followed by pattern, but doesn't consume the pattern).
*   `(?<=pattern)`: Positive lookbehind (matches only if preceded by pattern).

```bash
# Extract only the IP address using lookbehind and lookahead
grep -oP '(?<=Client IP: )\d{1,3}(\.\d{1,3}){3}(?=\s)' network.log

# Extract values inside quotes without extracting the quotes themselves
grep -oP '(?<=")[^"]+(?=")' config.json
```

## 8. Putting It All Together: Complex Pipelines

Real-world text processing often involves chaining multiple tools to transform unstructured text into structured, actionable data. Let's examine a few complex scenarios.

### Scenario 1: Analyzing Nginx Access Logs
Goal: Find the top 5 most frequently accessed URLs that returned a 404 Not Found error.

Log format snippet:
`192.168.1.10 - - [10/Oct/2023:13:55:36 -0700] "GET /missing_image.png HTTP/1.1" 404 123`

```bash
cat /var/log/nginx/access.log \
  | awk '$9 == 404 {print $7}' \
  | sort \
  | uniq -c \
  | sort -nr \
  | head -n 5
```
*Breakdown:*
1.  `cat`: Reads the file.
2.  `awk`: Checks if the 9th field (HTTP status) is 404. If so, prints the 7th field (the URL path).
3.  `sort`: Sorts the URLs alphabetically (required for uniq).
4.  `uniq -c`: Counts consecutive identical lines.
5.  `sort -nr`: Sorts the output numerically in reverse order (highest count first).
6.  `head -n 5`: Extracts the top 5 lines.

### Scenario 2: Refactoring Codebase Configurations
Goal: Find all `.conf` files containing the legacy domain `old-domain.com` and replace it with `new-domain.com`, creating backups.

```bash
find /etc/app/ -name "*.conf" -type f | xargs grep -l "old-domain.com" | xargs -I{} sed -i.bak 's/old-domain\.com/new-domain.com/g' {}
```
*Breakdown:*
1.  `find`: Locates all configuration files.
2.  `xargs grep -l`: Filters the list to only files that actually contain the string.
3.  `xargs sed -i.bak`: Executes the sed replacement in-place, creating a backup.

### Scenario 3: Monitoring Active Connections
Goal: List the remote IP addresses with the most active TCP connections to the server.

```bash
netstat -ntu | awk '$5 ~ /[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:/ {print $5}' | cut -d: -f1 | sort | uniq -c | sort -nr | head -n 10
```

## 9. Conclusion

The utilities covered in this module represent decades of software evolution, maintaining their relevance due to their uncompromising adherence to the Unix philosophy. While modern configuration management and observability tools offer graphical interfaces, the ability to dive into a terminal, parse raw logs, and manipulate data streams via bash remains an indispensable skill. Practice these commands, experiment with complex regular expressions, and embrace the power of the pipeline. They will save you countless hours and are the hallmark of a true Linux professional.

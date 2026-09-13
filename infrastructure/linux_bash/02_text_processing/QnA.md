# Questions and Answers: Text Processing and Redirection

**1. Explain the difference between grep, grep -E (egrep), and grep -P. When would you use each? Give an example of a pattern that requires PCRE.**
`grep` uses Basic Regular Expressions (BRE). It is universally available and highly backwards compatible, making it the default choice for simple string matching. However, in BRE, metacharacters like `+`, `?`, `|`, and `()` must be escaped with a backslash to function, which can make complex patterns unreadable.
`grep -E` (Extended Regular Expressions, formerly `egrep`) does not require escaping for these metacharacters. You would use `-E` when writing patterns with multiple logical ORs or grouping, such as `grep -E '(warning|error|critical)' log.txt`.
`grep -P` enables Perl-Compatible Regular Expressions (PCRE), which is the most powerful variant. You use `-P` when you need advanced features like lookarounds or non-greedy matching.
An example requiring PCRE is extracting an IP address without including the preceding text using lookbehinds:
```bash
grep -oP '(?<=Client: )\d{1,3}(\.\d{1,3}){3}' auth.log
```
This looks for "Client: " but only returns the IP portion.

**2. What does sed -i.bak do? What is the risk of sed -i without a backup extension on macOS vs Linux?**
The command `sed -i.bak` performs an in-place edit on a file and simultaneously creates a backup of the original file with the `.bak` extension. This ensures that if the regular expression is flawed and corrupts the text, the original data is easily recoverable.
On Linux (GNU sed), `-i` without an argument edits the file in-place with no backup. If the command breaks the file, data is permanently lost.
On macOS (BSD sed), running `-i` without an argument will actually throw an error. macOS requires an explicit extension argument. If you truly want no backup on macOS, you must use `-i ''` (with an empty string). The primary risk across both platforms is data destruction; an unverified sed substitution can easily ruin a critical configuration file without any recourse. Always use a backup extension in production environments.

**3. Explain awk's BEGIN and END blocks. Write an awk one-liner to calculate the average of a column in a CSV file.**
In `awk`, the `BEGIN` block is executed exactly once before the first line of the input file is read. It is typically used for initialization, such as defining variables, printing headers for reports, or explicitly setting the field separator variable (`FS`).
The `END` block is executed exactly once after the final line of the input has been processed. It is most commonly used to perform calculations on aggregated data, such as printing a final total sum, calculating averages, or generating a summary report.
To calculate the average of the 3rd column in a CSV file, skipping the header:
```bash
awk -F',' 'NR > 1 { sum += $3; count++ } END { if (count > 0) print "Average:", sum/count }' data.csv
```
This initializes the variables implicitly, sums the values of `$3` for every record past the first (header), and computes the average in the `END` block.

**4. What is the difference between 2>&1 and &>? Which is portable to all POSIX shells?**
The construct `2>&1` redirects file descriptor 2 (stderr) to whatever file descriptor 1 (stdout) is currently pointing to. It is the standard, POSIX-compliant way to merge standard error into standard output. It must be placed after the stdout redirection (e.g., `> file.log 2>&1`) because the shell evaluates redirections from left to right.
The construct `&>` is a shorthand specifically introduced in Bash (and zsh) that achieves the exact same result: it redirects both stdout and stderr to a file simultaneously. For example, `command &> file.log`.
`2>&1` is portable to all POSIX shells, including `sh`, `dash`, and `ash`. `&>` is a Bashism and will cause syntax errors if the script is executed by `sh` (which is often symlinked to `dash` on Ubuntu systems). Always use `2>&1` for scripts that need high portability.

**5. How does xargs work? What does the -I{} flag do? How do you parallelise xargs execution?**
`xargs` takes items from standard input (separated by whitespace or newlines) and passes them as arguments to a command. It is vital for connecting utilities that output data to stdout (like `find` or `ls`) to utilities that require arguments (like `rm` or `cp`).
The `-I{}` flag defines a placeholder string (in this case, `{}`). `xargs` will replace every occurrence of `{}` in the subsequent command with the current input item. This is crucial when the argument cannot just be appended to the end of the command.
```bash
ls *.jpg | xargs -I{} mv {} /backup/images/
```
To parallelize execution, you use the `-P` flag followed by the number of parallel workers (or 0 for as many as possible).
```bash
cat urls.txt | xargs -n 1 -P 4 wget
```
This command ensures that 4 instances of `wget` are running concurrently, significantly speeding up bulk operations.

**6. What is process substitution <(cmd)? Give two concrete examples where it is more elegant than a temp file.**
Process substitution allows the standard output of a command to be passed as a file argument to another command. The shell creates a temporary file descriptor (like `/dev/fd/63`) implicitly, runs the command, and passes the descriptor to the receiving program, bypassing the need to create, track, and clean up temporary files manually.
Example 1: Comparing the output of two commands without saving them to disk.
```bash
diff <(ls /dir1) <(ls /dir2)
```
Example 2: Passing dynamically generated configuration to a program that only accepts file paths.
```bash
mysqld --defaults-file=<(cat config.cnf | sed 's/port=3306/port=3307/')
```
In both scenarios, using process substitution keeps the filesystem clean and makes the commands atomic and easy to read.

**7. Explain sort | uniq -c | sort -rn pipeline. What does each stage do and what is the final output?**
This pipeline is a classic Linux idiom used to find the frequency of lines in a text stream and rank them from highest to lowest occurrences.
1. `sort`: `uniq` relies on identical lines being adjacent to each other. The first `sort` organizes the raw input alphabetically, ensuring all identical lines are grouped together.
2. `uniq -c`: This command collapses the adjacent duplicate lines into a single line, and the `-c` flag prefixes each output line with the numerical count of how many times it appeared.
3. `sort -rn`: This takes the output of `uniq -c` (which starts with numbers) and sorts it numerically (`-n`) and in reverse order (`-r`).
The final output is a frequency distribution table where the most common items are listed at the very top, descending to the least common items. It is frequently used for log analysis, like finding the top accessing IP addresses.

**8. How do you extract the 3rd column from a colon-delimited file using both cut and awk? When would you prefer one over the other?**
Using `cut`:
```bash
cut -d':' -f3 /etc/passwd
```
Using `awk`:
```bash
awk -F':' '{print $3}' /etc/passwd
```
You would prefer `cut` when dealing with simple, strictly delimited files where performance is critical. `cut` is a lightweight, dedicated C program that is extremely fast at character-level operations.
You would prefer `awk` when the data requires complex logic, when the delimiter might be a variable amount of whitespace (which `cut` struggles with), or when you need to manipulate the extracted field before printing it (e.g., converting to uppercase, performing math, or printing conditionally based on another column's value). `awk` is a full programming language.

**9. What does tee do? Why is it useful in a pipeline? Show how to use tee to log a long-running command's output to a file while still seeing it on screen.**
The `tee` command reads from standard input and writes simultaneously to standard output and to one or more files. It acts as a T-junction in a pipe network.
It is immensely useful because standard redirection (`>`) consumes standard output, meaning the terminal goes silent while the command runs. `tee` allows an administrator to monitor the progress of a script or build process in real-time on the console while simultaneously maintaining a persistent log on disk for later review.
To log a build command:
```bash
make clean install | tee build_output.log
```
If you need to capture stderr as well (using bash):
```bash
make clean install |& tee build_output.log
```

**10. Write a pipeline that: (a) finds all .log files in /var/log, (b) searches each for lines containing 'ERROR', (c) extracts just the timestamp from each line, (d) counts occurrences of each unique timestamp.**
Assuming the timestamp is the first 15 characters of the log line (e.g., standard syslog format "Oct 10 12:34:56"):
```bash
find /var/log -type f -name "*.log" \
  | xargs grep "ERROR" \
  | cut -c1-15 \
  | sort \
  | uniq -c
```
Alternatively, if using grep recursively directly:
```bash
grep -h -r "ERROR" --include="*.log" /var/log \
  | cut -c1-15 \
  | sort \
  | uniq -c
```
This pipeline locates the target files, filters for the error keyword, surgically extracts the date and time, groups identical timestamps together, and counts them to identify peak error periods.

**11. Explain the -A, -B, -C flags in grep. When is context output critical for debugging?**
The context flags in `grep` provide surrounding lines along with the matching line.
`-A NUM` (After) prints NUM lines of trailing context after the match.
`-B NUM` (Before) prints NUM lines of leading context before the match.
`-C NUM` (Context) prints NUM lines of both leading and trailing context.
Context output is critical when the matching line alone does not provide enough information to understand the problem. For example, a Java stack trace typically spans multiple lines. If you `grep "Exception"`, you will only see the exception name. By using `grep -A 20 "Exception"`, you capture the entire stack trace following the error. Similarly, using `-B` can help identify what specific operation was initiated immediately before a failure occurred.

**12. How do you do an in-place find-and-replace across 50 files using sed? How do you verify no accidental replacements happened?**
To perform an in-place find-and-replace across multiple files, you combine `find` (or globs) with `sed -i`:
```bash
find src/ -name "*.conf" | xargs sed -i.bak 's/old_server/new_server/g'
```
The `.bak` extension ensures that a backup of every modified file is created before the substitution occurs.
To verify that no accidental replacements happened, you can use the `diff` command to review the changes between the backups and the modified files:
```bash
for file in $(find src/ -name "*.conf"); do
  diff "${file}.bak" "$file"
done
```
If the diff output looks correct, you can safely delete the `.bak` files. If there was a mistake, you can quickly restore the `.bak` files using a loop or `rename`.

**13. What is the difference between BRE (Basic Regular Expressions) and ERE (Extended Regular Expressions)? Which metacharacters require escaping in BRE?**
The primary difference between BRE and ERE lies in how they handle special metacharacters that dictate grouping, alternation, and quantification.
In Extended Regular Expressions (ERE, enabled with `grep -E` or `sed -E`), characters like `?` (zero or one), `+` (one or more), `|` (logical OR), `()` (grouping), and `{}` (range quantifiers) function as special operators by default.
In Basic Regular Expressions (BRE, the default for `grep` and `sed`), these same characters are treated as literal text. To give them special meaning in BRE, they must be escaped with a backslash: `\?`, `\+`, `\|`, `\(\)`, and `\{\}`. ERE is generally preferred for complex patterns because it drastically reduces "backslash syndrome" and improves readability.

**14. Explain tr vs sed 's/./x/g'. When is tr more appropriate and more efficient?**
`tr` (translate) is a utility designed specifically to map or delete sets of characters, character-by-character. `sed 's/old/new/g'` evaluates regular expressions to replace strings.
```bash
# Convert a to x, b to y, c to z
tr 'abc' 'xyz' < file.txt
# Convert the literal string "abc" to "xyz"
sed 's/abc/xyz/g' file.txt
```
`tr` is vastly more appropriate and efficient when you need to perform 1-to-1 character transliteration (like changing case), squeezing repeated characters (`tr -s ' '`), or deleting specific characters (like removing carriage returns with `tr -d '\r'`). Because `tr` does not load a regex engine and operates purely on byte arrays, it is significantly faster than `sed` for these specific, simple character-level tasks.

**15. How do you extract all unique IP addresses from an Apache access log? Write the complete pipeline using grep, sort, and uniq.**
An Apache access log typically starts with the client IP address. To extract just the IPs, ensuring no duplicates:
```bash
grep -oP '^\d{1,3}(\.\d{1,3}){3}' /var/log/apache2/access.log | sort | uniq
```
Alternatively, if you know the IP is always the first space-delimited field, you can bypass `grep` and use `awk` or `cut`:
```bash
cut -d' ' -f1 /var/log/apache2/access.log | sort | uniq
```
The `cut` command isolates the first column (the IP), `sort` arranges them alphabetically, and `uniq` removes any adjacent duplicate entries, leaving you with a list of strictly unique IP addresses that have accessed the server.

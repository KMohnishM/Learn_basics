# Module 3: Linux Processes, Job Control, and System Resource Management

## 1. Process Concepts In-Depth

### What is a Process?
- In the Linux operating system, a process is fundamentally an executing instance of a program.
- It is the basic unit of execution and resource allocation within the operating system kernel.
- While a program is a static file residing on a storage medium, a process is dynamic.
- A process possesses a life cycle, a dedicated memory space, and an execution context.
- When you run a command, the Linux kernel creates a new process to handle the execution.
- The kernel tracks every process by assigning it a unique identifier known as a Process ID (PID).
- The PID is a positive integer that remains constant throughout the lifetime of the process.
- No two running processes can share the same PID at the exact same time.
- A process consists of several distinct memory components.
- The Text Segment contains the compiled machine code of the program being executed.
- The Data Segment contains global and static variables initialized by the programmer.
- The BSS Segment contains uninitialized global and static variables, initialized to zero.
- The Heap is memory allocated dynamically during process execution (e.g., using malloc).
- The Stack contains local variables, function parameters, and return addresses.
- When you type a command into your shell (like bash), the shell itself is a process.
- The shell asks the kernel to create a new process to run the command you typed.

### Process States Deep Dive
- A process in Linux transitions through various states during its lifecycle.
- Understanding these states is critical for system administration and troubleshooting.
- **Running or Runnable (R):**
- A process in this state is either currently executing on a physical CPU core.
- Or it is waiting in the run queue for its turn to get CPU time.
- The Completely Fair Scheduler (CFS) decides which 'Runnable' process executes next.
- **Interruptible Sleep (S):**
- Most processes on a healthy Linux system spend their time in this state.
- The process is sleeping, waiting for an event to occur.
- This event could be user input from a keyboard, or a network packet arriving.
- When the expected event occurs, the process wakes up instantly.
- Crucially, it can be interrupted by signals (e.g., SIGTERM, SIGKILL).
- **Uninterruptible Sleep (D):**
- This state is typically seen when a process is waiting for hardware I/O operations.
- Unlike Interruptible Sleep, a process in this state cannot be interrupted by signals.
- Even a forceful SIGKILL will not affect it until the I/O completes.
- A persistently high number of 'D' state processes indicates a storage bottleneck.
- **Stopped (T):**
- The process has been explicitly suspended and is no longer executing instructions.
- This happens when the process receives a SIGSTOP or SIGTSTP signal.
- The process remains in memory but uses zero CPU.
- It can be resumed later by sending it a SIGCONT signal.
- **Zombie (Z):**
- A zombie process has completed its execution and terminated.
- However, its entry still remains in the kernel's process table.
- This occurs because the parent process has not yet issued the wait() system call.
- Zombie processes consume practically no system resources (CPU or memory).
- But they do consume a PID slot.
- If too many zombies accumulate, the system might exhaust its PID space.

### Process Hierarchy, fork(), and exec()
- Linux processes are organized in a strict hierarchy, resembling an inverted tree structure.
- Every process (except the initial root process) has a parent process that created it.
- The identifier of the parent process is known as the Parent Process ID (PPID).
- The creation of a new process in Linux involves two fundamental system calls.
- **The fork() System Call:**
- The parent process calls fork() to create an exact duplicate of itself.
- This duplicate is the child process.
- It inherits a copy of the parent's memory layout, file descriptors, and variables.
- Linux employs a Copy-On-Write (COW) mechanism to optimize memory usage.
- Memory pages are shared between parent and child until one modifies a page.
- **The exec() System Call Family:**
- The child process often immediately calls an exec() family function.
- This replaces the child's current memory image with a new executable program.
- This allows the child to perform a completely different task than the parent.

### Orphaned and Zombie Processes Explained
- **Orphaned Processes:**
- If a parent process terminates before its child processes finish, the children are orphaned.
- The Linux kernel automatically re-parents orphaned processes to PID 1.
- Historically this was init; now it is usually systemd.
- PID 1 periodically reaps its adopted children to ensure they don't become permanent zombies.
- **Zombie Processes:**
- A zombie is a dead process waiting for its parent to acknowledge its death.
- You cannot 'kill' a zombie using kill -9 because it is already dead.
- To remove a persistent zombie, you must either fix the parent process, or kill the parent.
- Killing the parent makes the zombie an orphan, which is then reaped by PID 1.

## 2. Process Viewing Commands in Detail
- To effectively manage processes, you need to see exactly what is running.
- Linux provides several commands for inspecting the process table.

### ps (Process Status)
- The ps command captures a static snapshot of currently running processes.
- Because of its long history, ps supports three different syntax styles.
- 1. UNIX (POSIX) options: grouped and preceded by a single dash (e.g., -ef).
- 2. BSD options: grouped with no dash (e.g., aux).
- 3. GNU long options: preceded by two dashes (e.g., --forest).
- **Common usage (BSD style): ps aux**
- 'a': Show processes for all users, not just the current user.
- 'u': Display the user-oriented format with CPU/memory usage.
- 'x': Show processes that are not attached to a controlling terminal.
- **Columns explained for ps aux:**
- USER: The user account under which the process is running.
- PID: The unique Process ID.
- %CPU: Percentage of a single CPU core's time currently being used.
- %MEM: Percentage of physical RAM being used by the process.
- VSZ: Virtual Memory Size (total memory allocated, including swap/libs).
- RSS: Resident Set Size (actual physical memory in RAM occupied).
- TTY: The terminal associated with the process (? means no terminal).
- STAT: The process state (e.g., S, R, Z, T).
- START: Time or date the process was started.
- TIME: Total cumulative CPU time used by the process.
- COMMAND: The command line that started the process.
- **Common usage (UNIX style): ps -ef**
- '-e': Select all processes (similar to a and x combined).
- '-f': Do full-format listing (includes PPID).
- **To view the process tree:**
- ps -ejH or ps axjf (shows parent-child relationships using indentation).

### top and htop for Real-Time Monitoring
- While ps provides a static snapshot, top provides a dynamic, real-time view.
- It refreshes every 3 seconds by default, sorting processes by CPU usage.
- **Interactive commands in top:**
- Space: Force an immediate refresh of the screen.
- M: Sort processes by Memory usage instead of CPU.
- P: Sort processes by CPU usage (default).
- T: Sort processes by cumulative Time spent on the CPU.
- k: Kill a process (prompts for a PID and a signal number).
- r: Renice a process (prompts for a PID and a new nice value).
- c: Toggle between showing just command name and full arguments.
- 1: Toggle showing individual CPU cores at the top of the screen.
- q: Quit the program.
- **htop** is an enhanced, colorful, interactive version of top.
- It offers a user-friendly interface with vertical and horizontal scrolling.
- You can press F9 to kill a highlighted process.
- You can press F7/F8 to adjust its nice value easily.

### Finding PIDs with pgrep and pidof
- When you know the name of a program but need its exact PID, use pgrep and pidof.
- **pgrep** searches the process table for matching regex patterns.
- pgrep nginx: Returns PIDs of all processes matching 'nginx'.
- pgrep -u root sshd: Returns PIDs for sshd processes owned by root.
- pgrep -l nginx: Shows the process name alongside the PID.
- pgrep -f "python3 script.py": Searches the entire command line arguments.
- **pidof** finds the PIDs of programs given their exact, literal name.
- pidof bash: Returns all PIDs running the 'bash' executable.

## 3. Signals and the kill Command
- Signals are a primitive form of Inter-Process Communication (IPC).
- They are used by the kernel to notify processes of asynchronous events.
- When a process receives a signal, it can choose to ignore it.
- Or it can catch it and run a specific signal handler function.
- Or it can let the default kernel action occur (usually termination).

### Comprehensive Signal List
- **SIGHUP (1)**: Hangup. Originally used when a serial terminal disconnected.
- Today, it instructs daemons to reload config files without dropping connections.
- **SIGINT (2)**: Interrupt. Sent when a user presses Ctrl+C in the terminal.
- It gracefully interrupts the foreground process, allowing cleanup.
- **SIGQUIT (3)**: Quit. Sent when a user presses Ctrl+\.
- Causes the process to produce a core dump file for debugging.
- **SIGKILL (9)**: Kill. Forcibly and immediately terminates the process.
- The process cannot catch, block, or ignore this signal.
- Use this strictly as a last resort to prevent data corruption.
- **SIGTERM (15)**: Terminate. The default signal sent by the kill command.
- It politely requests the process to terminate gracefully.
- **SIGCONT (18)**: Continue. Resumes a process that was previously stopped.
- **SIGSTOP (19)**: Stop. Suspends a process immediately.
- Like SIGKILL, it cannot be caught or ignored.
- **SIGTSTP (20)**: Terminal Stop. Sent when a user presses Ctrl+Z.
- Suspends the foreground process. Can be caught or ignored.

### Mastering kill, killall, and pkill
- The kill command is used to send ANY signal to a process, not just terminate it.
- Usage: kill [options] PID
- kill 1234: Sends SIGTERM (15) to PID 1234.
- kill -9 1234: Sends SIGKILL (9) to PID 1234.
- kill -HUP 1234: Sends SIGHUP (1) to PID 1234 to reload config.
- kill -l: Lists all available signal names and their numeric values.
- **killall** sends a signal to all processes running a specific exact command name.
- killall nginx: Sends SIGTERM to all running instances of nginx.
- killall -9 python3: Forcibly kills all python3 processes system-wide.
- **pkill** is similar to killall but uses regular expressions.
- pkill -f "python3 script.py": Kills processes matching the full command line.
- pkill -u alice: Kills all processes owned by the user 'alice'.

## 4. Job Control in the Shell
- Job control is a built-in feature of modern interactive shells.
- It allows you to manage multiple executing processes within one terminal session.
- It enables you to suspend, resume, background, and foreground processes.

### Background and Foreground Execution Basics
- When you run a command normally in the shell, it runs in the foreground.
- It takes control of your terminal until it completes.
- To run a command in the background immediately, append an ampersand (&).
- tar -czf backup.tar.gz /home/user &
- The shell prints a job number and PID, e.g., [1] 5678, and returns the prompt.

### Interactive Terminal Shortcuts
- Ctrl+C: Sends SIGINT to the foreground process, requesting it to stop.
- Ctrl+Z: Sends SIGTSTP to the foreground process, suspending it to the background.
- Ctrl+\: Sends SIGQUIT to the foreground process (quits and dumps core).
- Ctrl+D: Sends an End-Of-File (EOF) marker, often causing interactive programs to exit.

### Managing Jobs with jobs, fg, bg
- The jobs command lists all jobs associated with the current shell session.
- jobs: Lists jobs with their state (Running, Stopped).
- jobs -l: Lists jobs including their underlying PIDs.
- bg %1: Resumes job number 1 in the background (sends SIGCONT).
- If you press Ctrl+Z, the job is completely stopped until you run bg.
- fg %1: Brings job number 1 to the foreground, giving it terminal control.

### Disown and Nohup Explained
- When a shell exits, it sends a SIGHUP signal to all its child background jobs.
- **disown**: Removes a job from the shell's internal job table.
- Start a job: sleep 600 &
- Run disown %1: The job is no longer tracked by the shell.
- If you close the terminal, the job will not receive SIGHUP and will keep running.
- **nohup**: Runs a command immune to hangups right from the start.
- nohup script.sh &
- Stdout and stderr are automatically redirected to nohup.out.
- This ensures you don't lose the logs when you disconnect.

### Terminal Multiplexers: screen and tmux
- For serious long-running tasks, tmux and GNU screen are far superior to nohup.
- They create virtual, persistent terminal sessions on the server.
- tmux: Starts a new session.
- Ctrl+b, then d: Detaches from the session, leaving processes running inside.
- tmux attach: Reattaches to the session from anywhere later.
- This allows seamless recovery from dropped network connections.

## 5. Process Priority and Scheduling
- Linux is a preemptive multitasking operating system.
- The kernel uses a complex scheduler to allocate finite CPU time.
- You can influence the scheduler using process priorities.

### The Nice Value Concept
- Every standard process has a 'nice' value, which acts as a hint to the scheduler.
- The nice value scale ranges from -20 to 19.
- -20 is the highest priority, least nice.
- 19 is the lowest priority, most nice.
- A high nice value yields CPU time willingly to other tasks.
- A negative nice value demands more CPU time at the expense of others.
- The default nice value for all new processes is 0.
- Normal, unprivileged users can only increase their nice value (make them lower priority).
- Only the root user can set a negative nice value or decrease a nice value.

### nice and renice Commands
- The nice command starts a new program with a modified scheduling priority.
- nice -n 10 tar -czf backup.tar.gz /var/log: Starts tar with lower priority.
- sudo nice -n -5 apt upgrade: Starts upgrade with higher priority.
- The renice command alters the priority of an already running process.
- renice -n 5 -p 1234: Changes the nice value of PID 1234 to 5.
- sudo renice -n -10 -u nginx: Changes priority of all nginx processes to -10.

### Disk I/O Priority with ionice
- While nice controls CPU priority, ionice controls I/O scheduling class.
- This is crucial for preventing heavy disk operations from starving interactive apps.
- Class 1 (Realtime): Gets first access to the disk. Highly dangerous.
- Class 2 (Best-effort): The default class (priority level 0 to 7).
- Class 3 (Idle): Only gets disk access when absolutely no other process requests it.
- Usage: ionice -c 3 -p 1234 (Sets PID 1234 to the Idle I/O class).

## 6. System Resource Monitoring Essentials
- Effective system administration requires monitoring resource consumption.

### Memory Monitoring with free
- The free command displays total, free, and used physical memory and swap.
- free -m (displays in megabytes) or free -h (human readable format).
- Always focus on the 'available' column, not the 'free' column.
- The 'available' column estimates memory available for starting new apps without swapping.
- The kernel aggressively caches disk data in unused RAM, making 'free' look artificially low.

### System Overview with vmstat
- vmstat reports high-level information about processes, memory, swap, and CPU.
- vmstat 1 5: Runs vmstat updating every 1 second, for 5 total times.
- Key columns to watch:
- r: Number of runnable processes waiting for CPU. High values mean CPU-bound.
- b: Number of processes in uninterruptible sleep. High values mean IO-bound.
- si / so: Swap in / Swap out. High values indicate severe thrashing.
- wa: CPU wait time. Percentage of time CPU is idle waiting for disk IO.
- Consistently high wait time means the disk is the primary bottleneck.

### IO Statistics with iostat and sar
- iostat reports CPU statistics and detailed IO statistics for block devices.
- iostat -xz 1 provides incredibly detailed, real-time disk utilization metrics.
- sar (System Activity Reporter) collects and saves historical system activity.
- sar -u shows CPU history, sar -r shows memory history.

### Inspecting Open Files with lsof
- In Linux, almost everything is a file, including network sockets.
- lsof (List Open Files) lists all open file descriptors and their processes.
- lsof -u root: List all files opened by the root user.
- lsof -p 1234: List all files and libraries opened by PID 1234.
- lsof -i :80: Find exactly which process is listening on TCP port 80.
- lsof +D /var/log: Find all open files within the /var/log directory tree.

### Deep Tracing with strace
- strace is an incredibly powerful diagnostic tool.
- It intercepts and records every system call made by a process.
- strace command: Runs the command and traces it from launch to exit.
- strace -p 1234: Attaches to an existing, already running process.
- strace -e openat,read -p 1234: Traces only specific system calls to reduce noise.
- strace -c ls: Provides a statistical summary table of system calls.

## 7. systemd and Modern Service Management
- Modern Linux distributions use systemd as the init system (PID 1).
- It manages system daemons throughout the system's uptime.

### Essential systemctl Commands
- systemctl start nginx: Starts the nginx service immediately.
- systemctl stop nginx: Stops the service immediately.
- systemctl restart nginx: Stops and starts the service, dropping active connections.
- systemctl reload nginx: Gracefully reloads configuration without dropping connections.
- systemctl status nginx: Provides status, active state, main PID, and recent logs.
- systemctl enable nginx: Configures the service to start automatically on system boot.
- systemctl disable nginx: Prevents the service from starting automatically at boot.
- systemctl mask nginx: Completely disables a service by linking to /dev/null.
- systemctl daemon-reload: Reloads all unit files from disk after you edit a .service file.

### Log Management with journalctl
- systemd centrally manages logs in a structured binary format called the journal.
- journalctl -u nginx: Shows logs specifically for the nginx service.
- journalctl -f: Follows the journal continuously in real-time (like tail -f).
- journalctl -b: Shows logs strictly since the most recent system boot.
- journalctl --since "1 hour ago": Filters logs by time (natural language).
- journalctl -p err: Filters logs by priority (errors, criticals, alerts).

### Anatomy of a systemd Unit File
- Services are defined by unit files, typically in /etc/systemd/system/.
- The [Unit] section contains metadata and dependencies (e.g., After=network.target).
- The [Service] section contains execution specifics (User=, ExecStart=).
- Restart=always instructs systemd to restart the service if it crashes.
- The [Install] section dictates boot behavior (WantedBy=multi-user.target).
- Mastering Linux processes and systemd is essential for a stable environment.

---

## 8. Advanced Process Monitoring with /proc

The `/proc` filesystem exposes live kernel data as readable files. No tools required — just `cat`.

```bash
# Per-process information
ls /proc/$$                    # files for current shell process
cat /proc/$$/status            # process status: name, PID, PPID, threads, memory
cat /proc/$$/cmdline           # command line (null-separated, use tr)
cat /proc/$$/cmdline | tr '\0' ' '
cat /proc/$$/environ           # environment variables (null-separated)
cat /proc/$$/fd/ | ls -la      # open file descriptors
ls -la /proc/$$/fd/            # list all open FDs for this process
cat /proc/$$/maps              # memory map (virtual address space)
cat /proc/$$/net/tcp           # TCP connections (hex format)
cat /proc/$$/limits            # resource limits (ulimit values)

# System-wide /proc files
cat /proc/cpuinfo              # CPU details (model, cores, flags)
cat /proc/meminfo              # memory stats (MemTotal, MemFree, MemAvailable, Buffers, Cached)
cat /proc/loadavg              # load averages: 1min 5min 15min + running/total processes + last PID
cat /proc/uptime               # seconds since boot + seconds spent idle
cat /proc/version              # kernel version string
cat /proc/sys/kernel/pid_max   # maximum PID value
cat /proc/net/dev              # network interface statistics
cat /proc/diskstats            # disk I/O statistics
cat /proc/mounts               # currently mounted filesystems

# Watching live
watch -n 1 cat /proc/loadavg   # live load average
watch -n 1 'cat /proc/meminfo | grep -E "MemAvailable|MemFree|Cached"'
```

Useful /proc patterns for debugging:
```bash
# Find which process has a file open
for pid in /proc/[0-9]*/fd; do
  ls -la "$pid" 2>/dev/null | grep 'target_file' && echo "PID: $(echo $pid | cut -d/ -f3)"
done

# Get full command line of any process by PID
tr '\0' ' ' < /proc/1234/cmdline; echo

# Check process start time
ls -la /proc/1234  # look at the directory creation time

# Count open file descriptors for a process
ls /proc/1234/fd | wc -l

# Check if process is multi-threaded
cat /proc/1234/status | grep Threads
```

## 9. ulimit — Resource Limits

Every process has resource limits set by the kernel. `ulimit` views and sets them for the current shell and child processes.

```bash
ulimit -a                      # show all current limits
ulimit -n                      # max open file descriptors (default: 1024)
ulimit -u                      # max user processes
ulimit -s                      # stack size (KB)
ulimit -v                      # virtual memory limit (KB)
ulimit -c                      # core file size (0 = disabled)
ulimit -t                      # CPU time limit (seconds)

# Setting limits
ulimit -n 65536                # increase open files limit to 65536
ulimit -n unlimited            # remove limit (if allowed)
ulimit -c unlimited            # allow core dumps for debugging

# Limits are per-shell-session — set in /etc/security/limits.conf for persistence:
# /etc/security/limits.conf
# alice    soft    nofile    65536
# alice    hard    nofile    131072
# *        soft    core      unlimited
# Format: user  type  resource  value
# soft = warning threshold (can be increased by user up to hard)
# hard = absolute maximum (only root can raise)

# Check limits for a running process
cat /proc/1234/limits

# Why this matters in production:
# A Node.js server hitting 1024 open file descriptors crashes with EMFILE
# nginx requires high nofile limits for handling many connections
# Check current usage: ls /proc/$$/fd | wc -l
```

## 10. Process Communication — IPC Mechanisms

```bash
# Signals (covered in section 3) are the simplest IPC

# Named pipes (FIFOs) — persistent pipe between unrelated processes
mkfifo /tmp/mypipe             # create named pipe
# Terminal 1 (writer):
echo 'hello from writer' > /tmp/mypipe    # blocks until reader opens
# Terminal 2 (reader):
cat /tmp/mypipe                            # receives the message
rm /tmp/mypipe                             # cleanup

# Shared memory — view with ipcs
ipcs                           # show all IPC resources (queues, semaphores, shared memory)
ipcs -m                        # shared memory segments only
ipcs -s                        # semaphore sets
ipcs -q                        # message queues
ipcrm -m <shmid>               # remove shared memory segment

# Unix domain sockets
# Listed in /proc/net/unix
cat /proc/net/unix | grep -v '^Num' | awk '{print $NF}' | head -20

# D-Bus — system message bus
dbus-monitor --system          # monitor system bus messages
dbus-send --system --print-reply --dest=org.freedesktop.hostname1 \
  /org/freedesktop/hostname1 org.freedesktop.DBus.Properties.GetAll \
  string:org.freedesktop.hostname1
```

## 11. Memory Deep Dive

```bash
# Understanding memory output
free -h
#               total        used        free      shared  buff/cache   available
# Mem:           15Gi       4.2Gi       8.1Gi       512Mi       2.7Gi       10.3Gi
# Swap:           2.0Gi          0           0

# Key concepts:
# - 'used': memory currently allocated to processes
# - 'buff/cache': kernel buffers + page cache (reclaimable)
# - 'available': actual free memory INCLUDING reclaimable cache
# Do NOT look at 'free' alone -- look at 'available'

# Check where memory is going
sudo smap_summary() { sudo cat /proc/$1/smaps_rollup 2>/dev/null || echo 'Not available'; }

# pmap -- memory map of a process
pmap -x 1234                   # detailed memory map with sizes
pmap 1234 | tail -1            # total memory usage

# smem -- more accurate memory usage per process
# (install: apt install smem)
smem -r -k                     # all processes sorted by RSS
smem -r -k -P nginx            # filter by process name
# PSS (Proportional Set Size) = fair share of shared memory + private memory
# More accurate than RSS for comparing processes that share libraries

# OOM Killer -- Out of Memory
# When system runs out of memory, kernel kills processes
# OOM score: 0 (never kill) to 1000 (kill first)
cat /proc/1234/oom_score       # current OOM score for PID 1234
cat /proc/1234/oom_score_adj   # adjustment: -1000 (protected) to 1000

# Protect a critical process from OOM killer:
echo -1000 > /proc/$(pgrep mysqld)/oom_score_adj

# Check if OOM killer triggered:
dmesg | grep -i 'oom\|killed process'
journalctl -k | grep -i 'oom\|killed process'
```

## 12. Background Job Patterns for Production

```bash
# Pattern 1: nohup with logging
nohup ./long_job.sh > /var/log/job.log 2>&1 &
echo "Job PID: $!"

# Pattern 2: tmux session (survives SSH disconnect, interactive)
tmux new-session -d -s etl_job './etl_pipeline.sh'
tmux list-sessions             # verify it's running
tmux attach -t etl_job         # reattach to see progress

# Pattern 3: systemd one-shot service (best for production)
# /etc/systemd/system/etl-pipeline.service
[Unit]
Description=ETL Pipeline Job
After=network.target postgresql.service

[Service]
Type=oneshot
User=etluser
WorkingDirectory=/opt/etl
ExecStart=/opt/etl/pipeline.sh
StandardOutput=journal
StandardError=journal
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target

# Run it:
systemctl start etl-pipeline.service
journalctl -f -u etl-pipeline  # follow logs

# Pattern 4: systemd timer (replaces cron)
# /etc/systemd/system/etl-pipeline.timer
[Unit]
Description=Run ETL pipeline daily

[Timer]
OnCalendar=*-*-* 02:00:00     # every day at 2am
Persistent=true                # run immediately if missed (e.g., system was off)

[Install]
WantedBy=timers.target

systemctl enable --now etl-pipeline.timer
systemctl list-timers          # show all active timers with next run time
```

## 13. Practical Debugging Scenarios

### Scenario 1: Process is using 100% CPU
```bash
top -b -n 1 | head -20        # find the culprit
PID=$(ps aux --sort=-%cpu | awk 'NR==2{print $1}')  # get highest CPU PID
cmd=$(cat /proc/$PID/cmdline | tr '\0' ' ')          # get its command
echo "High CPU process: PID $PID -- $cmd"
strace -p $PID -c -e trace=all -T  # profile syscalls for 5 seconds then Ctrl+C
```

### Scenario 2: Server is out of disk space but du shows plenty
```bash
df -h                         # shows 100% usage on /var
du -sh /var/*                 # but du shows only 20GB
# Explanation: a process has a file open that was deleted
# The file is still consuming space until the process releases it
lsof +L1                      # list files with 0 links (deleted but still open)
lsof +L1 | awk '{print $1, $2, $7, $NF}'  # process, PID, size, filename
# Fix: restart the process holding the deleted file open
```

### Scenario 3: Finding what's using port 8080
```bash
ss -tlnp | grep :8080         # shows the process name and PID
# or:
lsof -i :8080 -n -P           # more detail
# Kill it:
kill $(lsof -t -i :8080)
```

### Scenario 4: Process won't die
```bash
kill 1234                     # SIGTERM - try this first, wait 5 seconds
sleep 5
if kill -0 1234 2>/dev/null; then
  echo "Still alive, sending SIGKILL"
  kill -9 1234
fi
# If SIGKILL doesn't work:
# - process is in D state (disk wait) -- cannot be killed
# - check: ps aux | grep 1234 -- look for 'D' in STAT column
# - usually means stuck I/O, NFS hang, or kernel bug
# - must reboot to resolve D-state processes
cat /proc/1234/wchan           # shows what kernel function process is waiting on
```

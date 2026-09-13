# Q&A: Processes and Jobs

**1. What is a zombie process? How does it occur? Is it dangerous? How do you eliminate zombie processes without killing the parent?**
- A zombie process is essentially a remnant of a deceased process.
- When a process completes its execution, it exits.
- However, its exit status must be read by its parent.
- The operating system keeps the process entry in the process table.
- This state is known as the 'Zombie' state, or 'Z' in top/ps.
- Zombie processes consume absolutely no CPU.
- Zombie processes consume no physical memory (RAM).
- The only resource they consume is a Process ID (PID).
- Therefore, a few zombies are not immediately dangerous.
- However, if a parent process spawns thousands of children and never reaps them, PID exhaustion can occur.
- You cannot send a SIGKILL to a zombie because it is already dead.
- To eliminate a zombie without killing the parent, you can send a SIGCHLD signal to the parent.
- Alternatively, you can use a debugger like gdb to attach to the parent and manually invoke waitpid().

**2. What is the difference between SIGTERM and SIGKILL? Why should you always try SIGTERM before SIGKILL?**
- SIGTERM is signal number 15.
- It is the default signal sent by the kill command.
- SIGTERM politely requests a process to terminate.
- A process can catch SIGTERM and run a signal handler.
- This allows the process to close files, flush buffers, and cleanly disconnect from databases.
- SIGKILL is signal number 9.
- It is a forceful, immediate termination signal.
- The kernel handles SIGKILL directly; the process never sees it.
- The process is instantly removed from memory.
- No cleanup code is executed.
- You should always try SIGTERM first to prevent data corruption.
- Only use SIGKILL if a process is frozen and ignores SIGTERM.
- An example of SIGTERM is `kill 1234`.
- An example of SIGKILL is `kill -9 1234`.

**3. Explain job control: what does Ctrl+Z do, how does bg and fg work, and what is disown?**
- Job control is a feature of interactive shells like Bash.
- It allows you to manage multiple processes in one terminal.
- Pressing Ctrl+Z sends the SIGTSTP signal to the foreground process.
- This suspends the process and gives you back the shell prompt.
- The shell tracks this suspended process as a job, e.g., [1].
- The `bg` command (e.g., `bg %1`) resumes the process in the background.
- It sends a SIGCONT signal to the stopped job.
- The `fg` command (e.g., `fg %1`) brings a background job back to the foreground.
- It reconnects the job's standard input to your keyboard.
- The `disown` command removes a job from the shell's tracking table.
- If you run `disown %1`, the shell forgets about job 1.
- When you close the terminal, the shell will not send SIGHUP to the disowned job.
- This allows the job to keep running after you disconnect.

**4. What does lsof -i :8080 show? How would you find and kill whatever is listening on a specific port?**
- The `lsof` command stands for "list open files".
- In Linux, network sockets are treated as files.
- Therefore, `lsof` can view active network connections.
- The `-i` flag restricts the output to internet/network files.
- The `:8080` specifies the exact port to look for.
- It outputs the Command, PID, User, and file descriptor details.
- This is crucial for resolving "address already in use" errors.
- To kill the process listening on port 8080, you first need its PID.
- You can extract the PID manually from the lsof output.
- Alternatively, use `lsof -t -i :8080` to get just the PID.
- You can pass this directly to kill: `kill -9 $(lsof -t -i :8080)`.
- Another command for this is `fuser -k 8080/tcp`.
- Using these commands ensures your new service can bind to the port.

**5. Explain the process tree. What is PID 1? What happens to orphaned processes when their parent dies?**
- Every process in Linux is spawned by another process.
- This creates a parent-child relationship.
- This hierarchy forms a massive tree structure.
- At the root of this tree is PID 1.
- PID 1 is the first process started by the kernel after booting.
- Historically, PID 1 was SysV init.
- Today, PID 1 is almost always systemd.
- PID 1 is responsible for starting all other system services.
- An orphaned process occurs when a parent process dies before its child.
- The child process is left running without a parent.
- The Linux kernel immediately detects this situation.
- The kernel re-parents the orphaned process to PID 1.
- When the orphan eventually terminates, PID 1 cleans it up.

**6. What is a process's nice value? What is the range? Who can set negative nice values and why?**
- A nice value is a hint to the kernel's CPU scheduler.
- It determines how much CPU time a process receives relative to others.
- The range of nice values is from -20 to +19.
- A value of -20 is the highest possible priority.
- A value of +19 is the lowest possible priority.
- The default nice value for a new process is 0.
- A high nice value means the process is "nice" to others (yields CPU).
- Unprivileged users can only increase the nice value of their own processes.
- They can make their processes lower priority (0 to 19).
- Only the root user can set negative nice values (-1 to -20).
- This prevents regular users from monopolizing the CPU.
- It ensures critical system services always have priority.

**7. What does ps aux show? Explain each column: USER, PID, %CPU, %MEM, VSZ, RSS, TTY, STAT, START, TIME, COMMAND.**
- `ps aux` provides a snapshot of all processes on the system.
- USER indicates the account that started the process.
- PID is the unique integer Process ID.
- %CPU shows the percentage of a single CPU core being used.
- %MEM shows the percentage of physical RAM being used.
- VSZ is Virtual Memory Size, representing total allocated memory.
- RSS is Resident Set Size, representing actual physical memory used.
- TTY is the terminal associated with the process (? means no terminal).
- STAT indicates the current process state (e.g., S, R, Z, T).
- START shows the time or date the process was launched.
- TIME shows the cumulative CPU time the process has consumed.
- COMMAND shows the exact command line used to start the process.
- This command is fundamental for basic system troubleshooting.

**8. Explain the difference between VSZ and RSS memory in ps output. Which is more relevant when diagnosing a memory leak?**
- VSZ stands for Virtual Set Size.
- It represents the entire memory space mapped to a process.
- This includes shared libraries like glibc.
- It also includes memory that has been paged out to swap.
- It even includes allocated memory that hasn't been used yet.
- Therefore, VSZ is often a massively inflated number.
- RSS stands for Resident Set Size.
- It represents only the memory currently residing in physical RAM.
- It strictly excludes swapped-out memory.
- It excludes the shared portions of shared libraries.
- RSS is a much more accurate reflection of actual hardware usage.
- When diagnosing a memory leak, RSS is the relevant metric.
- A constantly growing RSS indicates the application is not freeing memory.

**9. How does nohup work? What is the alternative using tmux or screen, and why is tmux preferred for interactive sessions?**
- `nohup` stands for "no hangup".
- When a shell exits, it sends a SIGHUP signal to background jobs.
- `nohup` instructs the command to ignore the SIGHUP signal.
- This allows a background script to survive a terminal disconnect.
- `nohup` automatically redirects stdout and stderr to `nohup.out`.
- However, `nohup` does not provide an interactive terminal.
- `tmux` and `screen` are terminal multiplexers.
- They create persistent, virtual terminal sessions on the server.
- If your SSH connection drops, the tmux session stays alive.
- You can run `tmux attach` to resume exactly where you left off.
- `tmux` is preferred because you can interact with the running program.
- It also supports split panes, multiple windows, and scrollback buffers.
- For long-running administrative tasks, always prefer tmux over nohup.

**10. What is strace and when would you use it? Give a concrete debugging scenario where strace reveals the root cause.**
- `strace` intercepts and records system calls made by a process.
- It acts as an X-ray between the application and the Linux kernel.
- You use it when an application fails silently without helpful logs.
- Because all I/O requires system calls, strace sees everything.
- It logs file opens, network socket creations, and memory allocations.
- A concrete scenario: Nginx fails to start, but error.log is empty.
- You run `strace -e openat nginx` to trace file opens.
- The output shows: `openat("/etc/nginx/nginx.conf") = -1 EACCES`.
- This immediately reveals that Nginx lacks permission to read its config.
- The application failed to log this permission denied error.
- Without `strace`, you might spend hours guessing the root cause.
- With `strace`, the exact OS-level failure is immediately obvious.

**11. How does systemctl reload differ from systemctl restart? When is reload preferable for a production web server?**
- `systemctl restart` completely stops the service and starts a new one.
- The kernel sends SIGTERM, waits for exit, and executes the start command.
- The Process ID (PID) changes during a restart.
- All active network connections handled by the service are abruptly severed.
- `systemctl reload` asks the service to dynamically refresh its config.
- It does not stop the main process; the PID remains the same.
- It usually works by sending a SIGHUP signal to the daemon.
- The daemon reads the new config and gracefully phases out old workers.
- Active connections are maintained and allowed to finish.
- In a production web server (like Nginx), reload is massively preferable.
- It allows you to apply config changes (like new SSL certs) with zero downtime.
- Restarting a production server drops traffic; reloading does not.

**12. Explain the [Unit], [Service], and [Install] sections of a systemd unit file. What does Restart=always do?**
- A systemd unit file defines how a service is managed.
- It is separated into distinct structural sections.
- The `[Unit]` section contains metadata and dependencies.
- It uses directives like `After=network.target` to control boot order.
- The `[Service]` section defines how the process is actually executed.
- It includes `User=` to define the running account for security.
- It includes `ExecStart=` to define the absolute path to the binary.
- The `[Install]` section defines behavior when enabling the service.
- It uses `WantedBy=multi-user.target` to create boot symlinks.
- The `Restart=always` directive is placed in the `[Service]` section.
- It guarantees that systemd will restart the service if it dies.
- It will restart it whether it exits cleanly, crashes, or is killed by OOM.
- This is critical for maintaining high availability of production daemons.

**13. What does ionice -c 3 do? When would you use idle I/O class for a background process?**
- `ionice` modifies a process's scheduling class for disk I/O.
- It interacts directly with the kernel's block I/O scheduler.
- The `-c 3` flag assigns the process to the "Idle" scheduling class.
- The Idle class is the absolute lowest possible disk priority.
- A process in this class only gets disk access when no other process needs it.
- If any normal process requests disk read/write, the Idle process is paused.
- You use this for heavy, non-critical background jobs.
- Examples include daily rsync backups or locate database updates.
- Running `ionice -c 3 tar -czf backup.tar.gz /data` protects the system.
- It ensures the massive tar operation never starves production databases.
- It prevents latency spikes on the server's hard drives.
- This is crucial for maintaining responsiveness on shared hardware.

**14. What is vmstat output telling you? What do high wa (wait) values indicate?**
- `vmstat` provides a high-level summary of holistic system performance.
- It aggregates data across processes, memory, swap, IO, and CPU.
- You typically run it with an interval, like `vmstat 1`.
- The `procs` section shows runnable (r) and blocked (b) processes.
- The `memory` section shows swapped, free, buffered, and cached RAM.
- The `swap` section shows memory moving to (si) and from (so) disk.
- The `cpu` section breaks down time spent in user, system, idle, and wait.
- The `wa` (I/O wait) column is a critically important performance metric.
- It shows the percentage of time CPUs were completely idle.
- Crucially, they were idle because they were waiting for disk I/O to finish.
- Consistently high `wa` values (above 15%) indicate a severe storage bottleneck.
- It means the CPU is fast, but the hard drives are too slow to keep up.

**15. How do you check if a port is in use? Compare lsof -i :8080, ss -tulnp | grep 8080, and netstat -tulnp | grep 8080.**
- Checking network ports is a mandatory daily task for sysadmins.
- `netstat -tulnp` is the classic, legacy tool for this job.
- It parses the `/proc/net` files, which is slow and scales poorly.
- While deeply ingrained in sysadmin muscle memory, it is deprecated.
- `ss -tulnp` is the modern replacement from the iproute2 package.
- It queries the kernel's internal netlink API directly.
- This makes `ss` significantly faster and less resource-intensive.
- It is the recommended standard tool on modern Linux distributions.
- `lsof -i :8080` queries the file descriptor tables instead of network structs.
- It must scan the entire `/proc` directory for every running process.
- This makes `lsof` heavier and slower for pure network checks.
- However, `lsof` is highly versatile and can return bare PIDs (`-t`).
- Use `ss` for fast network state checks, and `lsof` for deep process inspection.

# CHEATSHEET: Processes, Signals, and Job Control

## 1. Process States (STAT column in ps)
| State | Letter | Detailed Description |
| :--- | :---: | :--- |
| **Running** | `R` | Actively executing on CPU or waiting in the run queue. |
| **Interruptible Sleep** | `S` | Sleeping, waiting for an event (I/O, timer, network). Can be awakened by signals. |
| **Uninterruptible Sleep** | `D` | Waiting on hardware disk I/O. Cannot be interrupted or killed (even with `kill -9`). |
| **Stopped** | `T` | Suspended via job control (`Ctrl+Z`) or signal (`SIGSTOP`/`SIGTSTP`). |
| **Zombie** | `Z` | Terminated process whose parent has not yet read its exit status via `wait()`. |
| **Session Leader** | `s` | Process is a session leader (e.g., bash). |
| **Foreground** | `+` | Process is in the foreground process group. |
| **High Priority** | `<` | Process has a negative nice value (high priority). |

## 2. Essential Signals (IPC)
| Signal Name | Num | Keyboard | Default Action | Common Use Case / Notes |
| :--- | :---: | :--- | :--- | :--- |
| **SIGHUP** | 1 | | Terminate | Ask daemons (Nginx/SSH) to **reload configuration** gracefully. |
| **SIGINT** | 2 | `Ctrl+C` | Terminate | Graceful interrupt from keyboard. Process can intercept/clean up. |
| **SIGQUIT** | 3 | `Ctrl+\\` | Core Dump | Quits and writes memory layout to a core file for debugging. |
| **SIGKILL** | 9 | | **Forced Kill** | Immediate kill handled by kernel. Cannot be blocked. Last resort. |
| **SIGTERM** | 15| | Terminate | Standard, polite termination request. Default sent by `kill`. |
| **SIGCONT** | 18| | Continue | Resumes a process that was previously stopped (`T` state). |
| **SIGSTOP** | 19| | Stop | Suspends process immediately. Cannot be intercepted. |
| **SIGTSTP** | 20| `Ctrl+Z` | Stop | Terminal stop. Pauses foreground process, puts in background. |

## 3. Job Control Shortcuts & Commands
| Command / Key | Action |
| :--- | :--- |
| `command &` | Start a command immediately in the background, freeing the prompt. |
| `Ctrl+Z` | Suspend the foreground job and return to shell prompt. |
| `Ctrl+C` | Interrupt (terminate) the foreground job gracefully. |
| `jobs` / `jobs -l` | List all current jobs in the shell session (add `-l` for PIDs). |
| `bg %1` | Resume job `[1]` executing in the background (sends SIGCONT). |
| `fg %1` | Bring job `[1]` to the foreground and attach to terminal standard input. |
| `disown %1` | Remove job `[1]` from shell's table so it survives terminal closure. |
| `nohup cmd &` | Run `cmd` immune to hangups, output redirected to `nohup.out`. |

## 4. `ps aux` Output Columns Explained
| Column | Meaning |
| :--- | :--- |
| `USER` | User account running the process. |
| `PID` | Process ID (unique integer). |
| `%CPU` | Percentage of a single CPU core used. |
| `%MEM` | Percentage of total physical RAM used. |
| `VSZ` | **Virtual Memory Size (KB)**: Total memory mapped (includes swap/libs). |
| `RSS` | **Resident Set Size (KB)**: Actual physical RAM occupied (find memory leaks here). |
| `TTY` | Terminal associated with process (`?` means daemon). |
| `STAT` | Process state code (e.g., `Ss`, `R+`, `Z`). |
| `START`| Time or date the process was launched. |
| `TIME` | Cumulative CPU time used since launch. |
| `COMMAND`| The exact command and arguments that started the process. |

## 5. Process Management & Priority Commands
| Command | Example | Description |
| :--- | :--- | :--- |
| `top` | `top` | Interactive real-time process viewer (press `M` for mem, `P` for cpu). |
| `htop` | `htop` | Colorful, scrollable top alternative (press `F9` to kill, `F7`/`F8` for nice). |
| `pgrep` | `pgrep -u root sshd` | Find PIDs matching a name or attribute. |
| `pidof` | `pidof bash` | Find exact PID of a running binary. |
| `kill` | `kill -15 1234` | Send a signal to a specific PID (default is 15/SIGTERM). |
| `killall` | `killall -9 nginx` | Send a signal to all processes with an exact name. |
| `pkill` | `pkill -f "script"` | Send a signal based on regex/pattern match of command line. |
| `nice` | `nice -n 10 tar...` | Launch a **new** command with modified CPU priority (-20 to 19). |
| `renice` | `renice -n 5 -p 1234`| Change CPU priority of an **existing** process. |
| `ionice` | `ionice -c 3 -p 1234`| Change I/O (disk) priority class (`-c 3` is Idle class for backups). |

## 6. systemd and Service Management (systemctl)
| Command | Action |
| :--- | :--- |
| `systemctl start svc` | Start service immediately. |
| `systemctl stop svc` | Stop service immediately. |
| `systemctl restart svc` | Stop then start service (drops active connections). |
| `systemctl reload svc` | Reload config gracefully (zero downtime, sends SIGHUP). |
| `systemctl status svc` | View current status, state, main PID, and recent logs. |
| `systemctl enable svc` | Set service to start automatically on system boot. |
| `systemctl disable svc`| Prevent service from starting automatically. |
| `systemctl mask svc` | Completely block service from starting (symlinks to `/dev/null`). |
| `systemctl daemon-reload`| **Required** after editing any `.service` file to apply changes. |

## 7. System Resource Monitoring
| Command | Example | Description |
| :--- | :--- | :--- |
| `free` | `free -h` | View physical RAM and Swap usage. Focus on "available". |
| `vmstat` | `vmstat 1` | System summary. High `wa` indicates severe disk bottlenecks. |
| `lsof` | `lsof -i :80` | List open files/network sockets. Finds process listening on port. |
| `strace` | `strace -p 1234` | Intercept/log system calls for deep debugging. |
| `ss` | `ss -tulnp` | Modern, fast replacement for `netstat` to view listening ports. |

## 8. journalctl Log Filtering Reference
| Command | Filters Logs By... |
| :--- | :--- |
| `journalctl -u nginx` | Specific service unit (`-u`). |
| `journalctl -f` | Real-time follow mode (like `tail -f`). |
| `journalctl -b` | Current boot session (`-b`). |
| `journalctl -p err` | Priority level (`error`, `warning`, `crit`, etc.). |
| `journalctl --since "1h"`| Timeframe (natural language: `"1 hour ago"`, `"yesterday"`). |

# CHEATSHEET: Docker Internals & Linux Primitives

## 1. Linux Namespaces Overview
Namespaces provide process-level isolation for global system resources.

| Namespace | CLI Flag  | Kernel Flag    | Resource Isolated                          |
| :-------- | :-------- | :------------- | :----------------------------------------- |
| **PID**   | `--pid`   | `CLONE_NEWPID` | Process ID numbers (PID 1 inside container) |
| **NET**   | `--net`   | `CLONE_NEWNET` | Network interfaces, IPs, routing tables    |
| **MNT**   | `--mount` | `CLONE_NEWNS`  | Filesystem mount points (`/`)              |
| **IPC**   | `--ipc`   | `CLONE_NEWIPC` | System V IPC, POSIX message queues         |
| **UTS**   | `--uts`   | `CLONE_NEWUTS` | Hostname and NIS domain name               |
| **USER**  | `--user`  | `CLONE_NEWUSER`| User and Group IDs (UID/GID mappings)      |
| **CGROUP**| `--cgroup`| `CLONE_NEWCGROUP`| View of `/sys/fs/cgroup` hierarchies       |

## 2. Low-Level CLI Commands

### Namespace Management (`unshare` / `nsenter`)
```bash
# Create a new environment with all namespaces isolated and launch bash
unshare --pid --net --mount --ipc --uts --user --fork --mount-proc /bin/bash

# Enter an existing namespace (find PID of container first)
nsenter --target <PID> --pid --net --mount /bin/bash

# View namespaces for a specific process
ls -l /proc/<PID>/ns/
```

### Filesystem Isolation
```bash
# Securely change root (preferred over chroot)
pivot_root /new_root /new_root/old_root

# Mount required pseudofilesystems inside container
mount -t proc proc /proc
mount -t sysfs sysfs /sys
```

## 3. Control Groups (cgroups v2)
Cgroups provide resource limiting, prioritization, and accounting.

**Path:** `/sys/fs/cgroup/`

| Controller | File | Purpose | Example |
| :--- | :--- | :--- | :--- |
| **Memory** | `memory.max` | Hard limit for RAM. Triggers OOM Killer. | `echo 50000000 > memory.max` (50MB) |
| **Memory** | `memory.high` | Soft limit. Triggers aggressive reclamation. | `echo 40000000 > memory.high` |
| **CPU** | `cpu.max` | Bandwidth control (quota period). | `echo "50000 100000" > cpu.max` (0.5 CPUs) |
| **CPU** | `cpu.weight` | Relative share of CPU during contention. | `echo 512 > cpu.weight` |
| **PIDs** | `pids.max` | Maximum number of processes allowed. | `echo 100 > pids.max` |
| **Core** | `cgroup.procs` | List of PIDs subject to these limits. | `echo $$ > cgroup.procs` |

## 4. OverlayFS Architecture (Union Filesystem)

OverlayFS merges multiple layers into a single view using Copy-on-Write (CoW).

```text
       +------------------------------------------+
       |           Merged View (Container)        |
       |  /app (from Up)   /etc (from Low)        |
       +------------------------------------------+
                           ^
                           | (mount -t overlay)
       +------------------------------------------+
       |   Upperdir (Read/Write)                  |
       |   (Container Layer - stores changes)     |
       +------------------------------------------+
       +------------------------------------------+
       |   Lowerdir (Read-Only)                   |
       |   (Image Layers - shared across containers)|
       +------------------------------------------+
```

### OverlayFS Core Mechanics
*   **Reads:** Searches `upperdir` first, then falls back to `lowerdir`.
*   **Writes (New File):** Created directly in `upperdir`.
*   **Writes (Modify File):** "Copy-up" - file is copied from `lowerdir` to `upperdir`, then modified.
*   **Deletes:** Creates a "Whiteout" file (character device 0/0) in `upperdir` to hide the `lowerdir` file.

## 5. The OCI Container Execution Flow

1.  **dockerd:** High-level API daemon. Receives `docker run`.
2.  **containerd:** High-level runtime. Pulls image, prepares OverlayFS.
3.  **containerd-shim:** Decouples container process from daemon. Handles I/O.
4.  **runc:** Low-level OCI runtime. Reads `config.json`.
5.  **runc -> kernel:** Calls `unshare`, configures `cgroups`, calls `pivot_root`.
6.  **runc exits:** Container application process is now running natively on host kernel.

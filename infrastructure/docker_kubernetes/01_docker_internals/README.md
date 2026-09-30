# Module 1: Docker Internals & Kernel Primitives

## Introduction: The Container Illusion

There is a pervasive myth in software engineering that a "container" is a lightweight virtual machine—a physical entity that boots up, hosts your application, and shuts down. This is fundamentally incorrect. If you log into a Linux host and examine the kernel, you will not find a data structure called a "container". 

A container does not exist. It is an illusion. 

What we refer to as a container is simply a standard Linux process. It is no different from running `nginx`, `python`, or `bash` directly on your laptop. However, this process has been heavily restricted, isolated, and jailed using three fundamental features of the Linux kernel:
1.  **Namespaces** (Isolation of vision)
2.  **Control Groups / cgroups** (Restriction of resources)
3.  **Union Filesystems** (Virtualization of storage)

Understanding how these low-level primitives function is the watershed moment between being a developer who knows Docker commands, and a platform engineer who can architect and debug distributed systems at cloud scale.

---

## 1. Virtual Machines vs. Containers Architectural Stack

To understand the value proposition of containers, we must first examine the hypervisor model they aim to replace.

### The Virtual Machine Stack (Hardware Virtualization)
Virtual Machines virtualize the physical hardware. A hypervisor (like VMware ESXi, KVM, or Hyper-V) intercepts calls to the CPU, memory, and disk, translating them for multiple guest operating systems.

```text
+-----------------------------------------------------+
|                     APP 1 (Java)                    |
+-----------------------------------------------------+
|                  Guest OS (Ubuntu)                  |
|    [Full Kernel, Init System, Background Daemons]   |
+-----------------------------------------------------+
|                   Hypervisor (KVM)                  |
+-----------------------------------------------------+
|                  Host OS (RHEL)                     |
+-----------------------------------------------------+
|                   Hardware (CPU, RAM)               |
+-----------------------------------------------------+
```
*Disadvantages:*
- **Overhead:** Every VM must boot a full kernel. This consumes hundreds of megabytes of RAM just for the OS to idle.
- **Speed:** Booting a kernel takes seconds to minutes.
- **Density:** You can only run a limited number of VMs on a server before exhausting memory.

### The Container Stack (OS-Level Virtualization)
Containers do not virtualize hardware. They virtualize the operating system. All container processes share the exact same underlying host kernel.

```text
+---------------------+ +---------------------+
|   APP 1 (Java)      | |   APP 2 (Node)      |
|  [Isolated Proc]    | |  [Isolated Proc]    |
+---------------------+ +---------------------+
|           Container Runtime (runc)          |
+---------------------------------------------+
|                  Host OS Kernel             |
|        (Namespaces, Cgroups, OverlayFS)     |
+---------------------------------------------+
|                   Hardware (CPU, RAM)       |
+---------------------------------------------+
```
*Advantages:*
- **Zero OS Overhead:** No guest kernels. The application runs natively on the host CPU.
- **Instant Boot:** A container starts as fast as the underlying process starts (milliseconds).
- **Extreme Density:** You can run thousands of containers on a single host.

---

## 2. Linux Namespaces: The Walls of the Jail

Namespaces are a Linux kernel feature that partitions kernel resources such that one set of processes sees one set of resources while another set of processes sees a different set of resources. There are 7 core namespaces.

### The 7 Core Namespaces

| Namespace | Subsystem Flag | Description |
|-----------|---------------|-------------|
| **Mount (mnt)** | `CLONE_NEWNS` | Isolates filesystem mount points. The process believes it has its own `/`, completely separate from the host's `/`. |
| **Process ID (pid)** | `CLONE_NEWPID` | Isolates the process ID number space. Your app becomes PID 1 inside the container, but maps to PID 14593 on the host. |
| **Network (net)** | `CLONE_NEWNET` | Isolates the network stack. Provides independent interfaces (`eth0`), routing tables, and `iptables` rules. |
| **Interprocess (ipc)** | `CLONE_NEWIPC` | Isolates System V IPC and POSIX message queues. Prevents processes from reading shared memory of other containers. |
| **UNIX Timesharing (uts)**| `CLONE_NEWUTS` | Isolates the hostname and NIS domain name. |
| **User (user)** | `CLONE_NEWUSER` | Maps UIDs/GIDs. Allows a process to have root privilege (UID 0) inside the container, but map to an unprivileged user (UID 1000) on the host. |
| **Control Group (cgroup)**| `CLONE_NEWCGROUP`| Isolates the cgroup root directory, preventing the container from seeing host cgroup topologies. |

### Hands-on: Breaking Abstractions with `unshare`
You can create namespaces without Docker using the `unshare` utility.
Run this on a Linux host (as root):
```bash
# Create a new UTS, PID, and Mount namespace, and run bash
unshare --uts --pid --mount --fork /bin/bash

# Inside the new environment:
hostname new-isolated-host

# Mount the proc filesystem to see only our isolated PIDs
mount -t proc proc /proc
ps aux
```
Notice that `bash` is now PID 1. You have manually created half of a container.

---

## 3. Linux Control Groups (Cgroups): Resource Metering

If namespaces dictate what a process can *see*, cgroups dictate what a process can *use*. 

### Cgroups v1 vs v2
- **v1:** Extremely complex. Every resource controller (memory, cpu, blkio) had its own independent hierarchy tree.
- **v2:** A unified hierarchy. A process belongs to a single group, and all resource controls are applied uniformly at that node in the tree. Kubernetes deprecated v1 entirely.

### Exploring the Cgroup Filesystem
Cgroups are exposed to the user via a virtual filesystem mounted at `/sys/fs/cgroup/`.

**1. The Memory Controller:**
When you set `resources.limits.memory: 512Mi` in Kubernetes, it writes to `memory.max`.
```bash
cat /sys/fs/cgroup/system.slice/docker-<id>.scope/memory.max
# Output: 536870912  (512 MB in bytes)
```
*The OOM Killer:* If the process attempts to allocate memory beyond this limit, the kernel intercepts the allocation and triggers the Out-Of-Memory (OOM) killer. It calculates an `oom_score` and sends a `SIGKILL` (signal 9) to the offending process.

**2. The CPU Controller:**
CPU is a compressible resource (unlike memory). It is managed by the Completely Fair Scheduler (CFS).
When you set a limit of 0.5 CPU cores, it configures:
- `cpu.max`: Contains two values: `quota` and `period`.
```bash
cat /sys/fs/cgroup/system.slice/docker-<id>.scope/cpu.max
# Output: 50000 100000
```
This means: Out of a 100,000 microsecond period, this container is allowed 50,000 microseconds of CPU time. Once it hits that quota, it is forcefully paused (CPU Throttled) until the next period.

---

## 4. Union Filesystems and OverlayFS

Containers must boot instantly. Copying a 1GB Ubuntu filesystem for every container is impossible. To solve this, containers use **Union Filesystems**, specifically **OverlayFS**.

OverlayFS allows you to stack directories on top of each other. 
1.  **Lowerdir (Read-Only):** The base image layers. Immutable. Shared by all containers using the image.
2.  **Upperdir (Read-Write):** A thin, empty layer created specifically for the running container.
3.  **Merged:** The unified view the container actually sees.

### Copy-on-Write (CoW) Penalty
If an application writes a new file, it lands in the `upperdir`.
If an application modifies an *existing* 1GB file located in the `lowerdir`, OverlayFS cannot modify it in place. The kernel must copy the entire 1GB file up into the `upperdir` before the application can edit it. This I/O bottleneck is why databases running in containers must use Volumes to bypass the Overlay filesystem.

### Whiteout Files (Handling Deletions)
How do you delete a file that exists in a read-only lower layer?
You create a **Whiteout File** in the upperdir. It is a character device node (`c 0 0`). When the kernel merges the directories, the whiteout file instructs the kernel to hide the underlying file from the container's view.

---

## 5. OCI Architecture and Runtimes

"Docker" is not a monolith. It is a stack of modular components standardized by the Open Container Initiative (OCI).

1.  **Dockerd:** The high-level daemon and API server.
2.  **Containerd:** The industry-standard high-level runtime. Pulls images, manages storage, configures namespaces.
3.  **Containerd-Shim:** A daemonless process that sits between containerd and runc. It acts as the parent to the container, holding open stdout/stderr pipes so `containerd` can be restarted without killing running workloads.
4.  **runc:** The low-level OCI runtime. A CLI tool that executes the kernel syscalls (`unshare`, `pivot_root`) to actually start the process, and then exits.

---

## 6. Lab: Building a Container from Scratch in Pure Bash

To prove that containers are just Linux primitives, we will build one using pure bash. No Docker daemon required.

```bash
#!/bin/bash
# 1. Download a minimal Alpine root filesystem tarball
mkdir -p /tmp/mycontainer/rootfs
wget https://dl-cdn.alpinelinux.org/alpine/v3.18/releases/x86_64/alpine-minirootfs-3.18.3-x86_64.tar.gz
tar -xzf alpine-minirootfs-3.18.3-x86_64.tar.gz -C /tmp/mycontainer/rootfs

# 2. Setup Cgroups v2 limits
CGROUP_PATH="/sys/fs/cgroup/mycontainer"
mkdir -p $CGROUP_PATH
# Restrict to 100MB of RAM
echo "104857600" > $CGROUP_PATH/memory.max
# Add our current bash PID to the cgroup
echo $$ > $CGROUP_PATH/cgroup.procs

# 3. Use unshare to create namespaces, and pivot_root to jail the filesystem
# This executes a new shell completely isolated from the host
unshare --mount --uts --ipc --net --pid --fork --root=/tmp/mycontainer/rootfs /bin/sh -c "
    hostname isolated-alpine
    mount -t proc proc /proc
    echo 'Welcome to the void.'
    /bin/sh
"
```
When you run this script as root, you will be dropped into a shell.
Run `ps aux`. You are PID 1.
Run `hostname`. You are `isolated-alpine`.
You have just recreated the core functionality of Docker using 15 lines of Bash.

## Summary & Next Steps
You now understand the mechanical reality of containers. They are strongly isolated processes bound by cgroups, constrained by namespaces, and reading from an OverlayFS stack. 
Proceed to the `QnA.md` file to test your knowledge aggressively, then advance to Module 2 to apply these principles to optimizing Dockerfile image builds.


---

## 7. Deep Dive: All 7 Namespaces and `/proc/<pid>/ns/`

The Linux kernel provides seven distinct namespaces. You can inspect the namespaces a process belongs to by looking at the `/proc/<pid>/ns/` directory. Each file in this directory is a special symlink. If two processes have the same inode number for a particular namespace symlink, they share that namespace.

```bash
ls -l /proc/$$/ns/
# Output similar to:
# cgroup -> cgroup:[4026531835]
# ipc -> ipc:[4026531839]
# mnt -> mnt:[4026531840]
# net -> net:[4026531992]
# pid -> pid:[4026531836]
# pid_for_children -> pid:[4026531836]
# user -> user:[4026531837]
# uts -> uts:[4026531838]
```

### Namespace Commands: `nsenter` and `unshare`

- `unshare`: Starts a program with some namespaces unshared from its parent.
- `nsenter`: Enters the namespaces of one or more existing processes.

To manually enter a running container's network namespace (assuming the container's PID on the host is 1234):

```bash
# Enter the network namespace of PID 1234
sudo nsenter --target 1234 --net /bin/bash

# Now, running 'ip addr' will show the container's network interfaces, not the host's.
ip addr
```

This is exactly what `docker exec` does under the hood: it uses the setns() syscall to attach a new process to the existing namespaces of the container.

---

## 8. Deep Dive: Cgroups v2 Hierarchy

Control Groups v2 (cgroupfs) provides a unified hierarchy mounted at `/sys/fs/cgroup/`. Unlike v1, where each controller (memory, cpu) had its own tree, v2 binds a process to a single node in the tree, and all controllers apply there.

### The Memory Controller

When a process is in a cgroup, its memory usage is tracked and constrained.
- `memory.max`: The hard limit for memory usage. If usage exceeds this, the OOM killer is invoked.
- `memory.current`: The current memory usage of the cgroup.
- `memory.oom.group`: A boolean flag (0 or 1). If set to 1, an OOM event will kill all processes in the cgroup simultaneously, ensuring atomic termination of a containerized application consisting of multiple processes.

```bash
# Set a memory limit of 500MB
echo 524288000 > /sys/fs/cgroup/my_container/memory.max
# Enable group OOM killing
echo 1 > /sys/fs/cgroup/my_container/memory.oom.group
```

### The CPU Controller (CFS)

The Completely Fair Scheduler (CFS) manages CPU time.
- `cpu.max`: Contains two values: quota and period. `100000 100000` means 100% of one CPU core. `50000 100000` means 50% of one core. `200000 100000` means 200% (two cores).
- `cpu.stat`: Contains throttling statistics. `nr_throttled` and `throttled_time` reveal how often and for how long the cgroup was paused because it exceeded its quota.

```bash
cat /sys/fs/cgroup/my_container/cpu.stat
# usage_usec 152345
# user_usec 100000
# system_usec 52345
# nr_periods 150
# nr_throttled 10
# throttled_usec 50000
```
High `nr_throttled` indicates the application is starving for CPU, even if overall host CPU usage is low.

### The IO Controller

Controls block device I/O.
- `io.max`: Sets limits on IOPS or bytes per second (bps) for read/write operations on specific block devices.

```bash
# Limit reads to 10MB/s on device 8:0 (sda)
echo "8:0 rbps=10485760" > /sys/fs/cgroup/my_container/io.max
```

---

## 9. OverlayFS Mount Walkthrough

OverlayFS creates a union of directories. Let's build a manual OverlayFS mount to demonstrate copy-up and whiteout mechanics.

### Step 1: Create Directories

```bash
mkdir -p /tmp/overlay/{lower1,lower2,upper,work,merged}

# Populate lower directories (simulating image layers)
echo "Base OS file" > /tmp/overlay/lower1/os_file.txt
echo "App dependency" > /tmp/overlay/lower2/dep.txt
```

### Step 2: Mount the Overlay

```bash
sudo mount -t overlay overlay \
    -o lowerdir=/tmp/overlay/lower2:/tmp/overlay/lower1,upperdir=/tmp/overlay/upper,workdir=/tmp/overlay/work \
    /tmp/overlay/merged
```

### Step 3: Trigger a Copy-Up

When we modify a file from the lower layer in the merged view, OverlayFS copies it to the upper layer.

```bash
# Modify lower1's file
echo "Modified" >> /tmp/overlay/merged/os_file.txt

# Inspect upper layer
cat /tmp/overlay/upper/os_file.txt
# It exists here now! The entire file was copied up.
```

### Step 4: Deleting Files (Whiteouts)

To delete a lower-layer file, OverlayFS creates a character device node (0/0) in the upper layer.

```bash
# Delete dep.txt in merged view
rm /tmp/overlay/merged/dep.txt

# Inspect upper layer for the whiteout
ls -la /tmp/overlay/upper/dep.txt
# Output: c--------- 1 root root 0, 0 Oct  1 10:00 /tmp/overlay/upper/dep.txt

# Alternatively, create a whiteout manually with mknod:
mknod /tmp/overlay/upper/manual_whiteout.txt c 0 0
```

---

## 10. OCI Container Bundle Structure

The Open Container Initiative (OCI) defines how to package and run containers. A container bundle is just a directory containing a `config.json` and a root filesystem.

### The `config.json` Schema

This file defines namespaces, cgroups, mounts, and the entrypoint.

```json
{
  "ociVersion": "1.0.2",
  "process": {
    "terminal": false,
    "args": ["/bin/bash"]
  },
  "root": {
    "path": "rootfs",
    "readonly": false
  },
  "linux": {
    "namespaces": [
      { "type": "pid" },
      { "type": "network" },
      { "type": "ipc" },
      { "type": "uts" },
      { "type": "mount" }
    ]
  }
}
```

### Using `runc`

With a bundle, you can use `runc` (the reference OCI runtime) to manage the container lifecycle.

```bash
# Create the container (processes namespaces, cgroups, mounts, but does not start the entrypoint)
runc create my_container

# View state
runc state my_container

# Start the entrypoint
runc start my_container

# Delete the container
runc delete my_container
```

---

## 11. Complete Pure Bash Container Implementation

This script demonstrates creating a full container environment in Bash, including networking (veth pairs, bridge), namespaces, cgroups, and `pivot_root`.

```bash
#!/bin/bash
set -e

CONTAINER_ID="c_$(head -c 4 /dev/urandom | xxd -p)"
ROOTFS="/tmp/containers/$CONTAINER_ID/rootfs"
CGROUP_DIR="/sys/fs/cgroup/containers/$CONTAINER_ID"

# 1. Prepare Root Filesystem (assuming Alpine minirootfs tarball exists)
mkdir -p "$ROOTFS"
tar -xzf alpine-minirootfs.tar.gz -C "$ROOTFS"

# 2. Setup Networking (Host Side)
# Create a veth pair
ip link add veth0 type veth peer name veth1
# Attach veth0 to an existing bridge (e.g., docker0 or custom bridge)
brctl addif docker0 veth0
ip link set veth0 up

# 3. Setup Cgroups v2
mkdir -p "$CGROUP_DIR"
echo "524288000" > "$CGROUP_DIR/memory.max" # 500MB
echo "50000 100000" > "$CGROUP_DIR/cpu.max" # 0.5 CPU

# 4. Unshare namespaces and execute container init
# We pass veth1 to the new network namespace.
unshare --pid --uts --ipc --mount --net --fork bash -c "
    # Put this new process in the cgroup
    echo \$\$ > $CGROUP_DIR/cgroup.procs

    # Networking (Container Side)
    # The host must move veth1 into this process's network namespace (done externally, simplified here)
    # ip link set veth1 netns \$\$
    ip link set lo up
    ip link set veth1 name eth0
    ip addr add 10.0.0.2/24 dev eth0
    ip link set eth0 up
    ip route add default via 10.0.0.1

    # Hostname
    hostname $CONTAINER_ID

    # Mounts
    mount -t proc proc $ROOTFS/proc
    mount -t sysfs sys $ROOTFS/sys
    mount -t devtmpfs dev $ROOTFS/dev

    # Pivot Root (Jailing)
    mkdir -p $ROOTFS/.oldroot
    pivot_root $ROOTFS $ROOTFS/.oldroot
    cd /
    umount -l /.oldroot
    rmdir /.oldroot

    # Execute application
    exec /bin/sh
"
```

This script constructs the isolation layers exactly as `runc` does, proving that containers are just configurations of native Linux kernel features.

## 12. Additional Deep Dive into Security Mechanisms

When deploying containers in production, isolation provided by namespaces and cgroups is often insufficient against advanced threats. Additional Linux security modules must be integrated.

### Seccomp (Secure Computing Mode)
Seccomp allows you to filter the system calls that a process can make to the kernel. A default Docker profile blocks roughly 44 out of 300+ syscalls, including dangerous ones like `kexec_load`, `open_by_handle_at`, and `init_module`.
By applying a custom seccomp profile, you can strictly allowlist only the syscalls your application requires, drastically minimizing the attack surface.

### AppArmor and SELinux
These Mandatory Access Control (MAC) systems provide an additional layer of policy enforcement.
- **AppArmor:** Uses file paths to define what a process can access. A profile can restrict a container from reading `/etc/shadow` even if the DAC (Discretionary Access Control) permissions would allow it.
- **SELinux:** Uses labels assigned to processes and files. If the labels do not match the defined policy (e.g., `container_t` trying to write to `shadow_t`), access is denied, regardless of user privileges.

By stacking namespaces, cgroups, OverlayFS, seccomp, and MAC policies, a container transforms from a simple process into a highly secure, restricted environment.

---
## 13. Deep Dive into Network Namespaces and Routing
Understanding how network namespaces interoperate is crucial for debugging complex container networks.
When a container is created, it gets a fresh, completely isolated network stack. This means no interfaces, no routing tables, and no iptables rules.

### Building the Network Stack from Scratch
To provide connectivity, the container runtime must orchestrate several steps:
1.  **Veth Pair Creation:** A virtual ethernet cable is created.
2.  **Namespace Injection:** One end of the cable is pushed into the container's network namespace (`ip link set veth1 netns <PID>`).
3.  **IP Assignment:** An IP address is assigned to the container's interface (`ip addr add 172.17.0.2/16 dev eth0`).
4.  **Routing Configuration:** A default route is established, pointing traffic out of the container (`ip route add default via 172.17.0.1`).
5.  **Host Bridge Attachment:** The other end of the cable is attached to a virtual bridge on the host (`brctl addif docker0 veth0`).
6.  **NAT Configuration:** iptables rules are injected on the host to translate the container's private IP to the host's public IP using masquerading (`iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE`).

Mastering these low-level networking concepts enables you to troubleshoot connectivity issues that higher-level abstractions often obscure.

---
## 14. Advanced Debugging Techniques
When a container fails to start, or exhibits unexpected behavior, standard debugging tools might not be available within the container image (especially in distroless environments).

### Sidecar Debugging
Instead of attempting to install tools like `curl`, `netstat`, or `strace` into a production image, you can run a temporary debugging container that shares the namespaces of the problematic container.

```bash
# Run a debug container that shares the target container's network namespace
docker run -it --rm --network container:<target_id> nicolaka/netshoot

# Run a debug container that shares the target container's process namespace
docker run -it --rm --pid container:<target_id> busybox
```
This technique allows you to inspect the isolated environment without modifying the immutable application image, preserving security and reducing bloat.

### strace and Kernel Inspection
For profound issues, inspecting the actual syscalls being made by the container process is necessary. By identifying the target process PID on the host, you can attach `strace` to trace its execution and identify failing syscalls, missing files, or denied permissions.

```bash
# Attach strace to the container's main process
sudo strace -p <host_pid> -f -e trace=openat,read,write
```
This level of visibility is impossible with virtual machines without specialized hypervisor tooling, highlighting the transparency and debuggability of OS-level virtualization.

---
## 15. The Realities of cgroups v1 vs v2 Migration

While cgroups v2 is conceptually superior, the transition has caused significant ecosystem friction.
For a long time, Kubernetes components like `kubelet` hardcoded paths to cgroups v1 structures (e.g., `/sys/fs/cgroup/memory/...`).
When a host OS upgrades to cgroups v2 by default (like Ubuntu 21.10+ or Fedora 31+), Kubernetes nodes would fail to boot or report resources correctly.

To identify if a host is running v1 or v2:
```bash
# If this returns 'cgroup2', you are on v2.
stat -f -c %T /sys/fs/cgroup
```
Understanding this migration path is critical for infrastructure engineers upgrading legacy clusters, as it often requires reconfiguring container runtimes (like instructing containerd to use the `systemd` cgroup driver instead of `cgroupfs`) to maintain stability.

---

## 16. Further Exploration: eBPF and Container Observability
As environments scale, traditional debugging tools like `strace` or `tcpdump` become too heavy or invasive for production containers. Extended Berkeley Packet Filter (eBPF) provides a modern alternative.

### What is eBPF?
eBPF allows you to run sandboxed programs directly within the Linux kernel without changing kernel source code or loading modules. For containers, this means you can observe network traffic, file access, and system calls with near-zero overhead.

### Container Context
Because all containers share the same kernel, an eBPF program attached to a kernel tracepoint can observe events from all containers simultaneously. However, because containers use PID and Network namespaces, the raw kernel data can be confusing (e.g., seeing multiple processes with PID 1).

Modern eBPF tools like Cilium and Tetragon automatically map low-level kernel events back to Kubernetes Pods and Container IDs by correlating the cgroup and namespace IDs.

```bash
# Example: Tracing TCP connections across all containers using bpftrace
sudo bpftrace -e 'kprobe:tcp_v4_connect { printf("PID %d attempting connect\n", pid); }'
```
This observability paradigm is rapidly replacing traditional sidecar-based monitoring in cloud-native infrastructure, further highlighting why understanding the shared kernel architecture of containers is indispensable.

---

## 17. Conclusion & Wrap-Up

Mastering Docker internals is not merely an academic exercise. It is the fundamental difference between hoping a system works and knowing exactly how it functions at the kernel level.
By understanding namespaces, you can diagnose complex routing failures.
By understanding cgroups, you can prevent cascading out-of-memory failures across your clusters.
By understanding OverlayFS, you can design storage strategies that do not cripple your database performance.

The abstractions provided by Docker and Kubernetes are incredibly powerful, but they are still just abstractions over these core Linux primitives. When the abstractions leak or break under production load, it is your knowledge of `/proc`, `unshare`, and `nsenter` that will allow you to restore service and build resilient infrastructure.

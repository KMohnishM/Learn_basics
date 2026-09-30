# Module 1: Docker Internals & Kernel Primitives - QnA

## Q1: What are the primary kernel primitives that create the illusion of a container?
The illusion of a container is constructed using three fundamental Linux kernel features.
First, Namespaces provide isolation of vision.
This ensures that a process only sees its own independent set of resources.
These resources include Process IDs (PIDs), network interfaces, mount points, and hostnames.
Second, Control Groups (cgroups) enforce limits on resource consumption.
They prevent a single process from monopolizing CPU time.
They also restrict memory allocation and disk I/O throughput.
Third, Union Filesystems provide a layered and virtualized storage mechanism.
Specifically, systems like OverlayFS allow multiple containers to share base image layers.
This happens efficiently while maintaining isolated read-write upper layers.
By combining these three features, a standard Linux process is restricted.
It functions identically to what we perceive as a container.
This is achieved without requiring hardware virtualization.
These primitives are baked directly into the Linux kernel.
They are accessed via standard system calls.

## Q2: How do containers architecturally differ from Virtual Machines (VMs)?
Virtual Machines utilize hardware virtualization.
A hypervisor (like KVM or VMware) sits above the host hardware.
It creates distinct virtualized hardware environments.
Each VM requires its own complete guest operating system.
This includes a full kernel, init system, and background daemons.
This leads to significant overhead in the system architecture.
Each VM consumes hundreds of megabytes of RAM just to idle.
Furthermore, it takes seconds or minutes to boot.
Containers, conversely, utilize OS-level virtualization.
They do not run a guest kernel.
Instead, all containerized processes share the single, underlying host OS kernel.
The container runtime uses namespaces and cgroups to isolate the processes.
Because there is no hardware virtualization, overhead is minimal.
Containers start in milliseconds.
This allows thousands of containers to run densely on a single host.

## Q3: Describe the mechanics of the PID namespace and the significance of PID 1.
The Process ID (PID) namespace isolates the process ID number space.
When a new PID namespace is created, the first process inside it is assigned PID 1.
From the perspective of the container, this process is the root.
It acts much like the init system (e.g., systemd) on a standard Linux host.
However, from the perspective of the host operating system, this process is different.
It is assigned a standard, large PID (e.g., 14593) on the host.
PID 1 inside a container has special responsibilities.
Most notably, it must handle signal processing and zombie process reaping.
If PID 1 does not properly handle SIGTERM, the container will not shut down gracefully.
Furthermore, child processes may terminate and become zombies.
PID 1 must wait() on them to clear their entries from the process table.
If the application running as PID 1 is not designed to handle these tasks, problems arise.
Resource leaks or ungraceful terminations will occur.
This is why specialized init processes like tini are often used.

## Q4: What is the primary architectural difference between cgroups v1 and cgroups v2?
Control Groups v1 (cgroups v1) was developed organically over time.
This resulted in a complex and fragmented architectural model.
In v1, every resource controller maintained its own independent hierarchy tree.
This included controllers for memory, cpu, and blkio.
This allowed a process to exist in completely different locations across trees.
This led to synchronization issues and severe complexities in management.
It also created difficulties when coordinating limits across different resource types.
Cgroups v2 introduced a much-needed unified hierarchy model.
In v2, there is a single, unified tree structure for all processes.
A process belongs to a single node within this unified hierarchy.
All resource controllers (memory, cpu, io, etc.) apply their limits uniformly there.
This unified approach simplifies administration significantly.
It enables safer and more consistent resource tracking.
It avoids the structural conflicts inherent in the v1 design.
Consequently, Kubernetes has deprecated v1 entirely.

## Q5: How does the Completely Fair Scheduler (CFS) calculate CPU quota and period for containers?
The CPU controller in cgroups manages access to CPU cycles.
It uses the Completely Fair Scheduler (CFS) to accomplish this.
When a CPU limit is set (e.g., 0.5 cores), it is implemented using two parameters.
These are cpu.max in v2 (or cpu.cfs_quota_us and cpu.cfs_period_us in v1).
The 'period' defines the length of a time window.
This is typically 100,000 microseconds, or 100ms.
The 'quota' defines how much time within that period the container is allowed to execute.
For a limit of 0.5 cores, the quota would be 50,000 microseconds.
This is allocated per 100,000 microsecond period.
If the container consumes its entire 50,000 microsecond quota before the period ends, it stops.
The kernel forcefully pauses (throttles) the container's execution.
It waits until the start of the next 100ms period.
This ensures strict enforcement of CPU limits.
If a container needs 2 full cores, the quota is set to 200,000 microseconds.
This means it can run concurrently on two separate CPU cores.

## Q6: Explain the mechanics of the kernel Out-Of-Memory (OOM) killer in relation to cgroups.
The memory controller in cgroups enforces hard limits on RAM usage.
This is configured via the memory.max file in cgroups v2.
Unlike CPU, memory is an incompressible resource.
If a process needs memory and none is available, it cannot simply be paused.
When a container attempts to allocate memory beyond its limit, the kernel intervenes.
The kernel intercepts the memory allocation request.
It then invokes the Out-Of-Memory (OOM) killer specific to that cgroup.
The OOM killer evaluates the processes within the cgroup.
It typically sends a SIGKILL (signal 9) to the highest memory consumer.
This terminates the offending process immediately to free RAM.
In cgroups v2, a feature called memory.oom.group can be enabled.
If this flag is set to 1, the behavior changes dramatically.
An OOM event will forcefully terminate every single process within the cgroup.
This happens simultaneously across the container.
This prevents scenarios where a multi-process application is left corrupted.

## Q7: Detail the four directory components used in an OverlayFS mount.
OverlayFS constructs a unified filesystem view using four specific directories.
The first directory is the lowerdir.
This represents the read-only base layers (e.g., the downloaded image layers).
Multiple lowerdirs can be stacked on top of each other.
The second directory is the upperdir.
This is a read-write directory created specifically for the running container.
Any new files created or modifications made by the container are written here.
The third directory is the workdir.
This is an empty, hidden directory on the same filesystem as the upperdir.
OverlayFS uses it as a staging area for atomic file operations.
This ensures that copy-up operations are safe before moving files into the upperdir.
The fourth component is the merged directory.
This is not a physical directory on the disk.
It is the mount point that presents the unified, composite view.
The application reads from and writes to this merged view.

## Q8: Why does the Copy-on-Write (CoW) mechanism incur a performance penalty on large files?
In a Union Filesystem like OverlayFS, the base layers are read-only.
The lowerdir cannot be modified directly by the container.
When an application attempts to modify a file in the lowerdir, things get complex.
OverlayFS cannot modify the file in place.
Instead, it must utilize a Copy-on-Write (CoW) mechanism.
Before the application can write its changes, a full copy is required.
The kernel must physically copy the entire file from the lowerdir to the upperdir.
If the file is small, this operation is negligible and fast.
However, if the file is massive (e.g., a 10GB database file), the penalty is huge.
The kernel must copy all 10GB into the upper layer before a single byte is modified.
This creates a massive I/O bottleneck on the host disk.
It causes severe latency spikes for the application.
This is why I/O-heavy applications must never write to the root filesystem.
They must use explicitly mounted Volumes, which bypass OverlayFS entirely.

## Q9: Differentiate between the OCI image-spec and the OCI runtime-spec.
The Open Container Initiative (OCI) defines standard specifications.
These specifications prevent vendor lock-in within the container ecosystem.
The specifications are split into two primary components.
The first is the OCI image-spec.
This defines the exact format of a container image.
It specifies how the filesystem layers are serialized as tarballs.
It dictates how the image manifest and configuration JSON files are structured.
It guarantees that an image built by Docker can be read by Podman.
The second component is the OCI runtime-spec.
This defines how a container should be executed on disk.
It specifies the layout of a container bundle (rootfs and config.json).
It details the exact lifecycle commands (create, start, state, kill, delete).
A low-level runtime must implement these commands precisely.
This ensures that a bundle can be executed interchangeably by runc or crun.

## Q10: Explain the distinct roles of dockerd, containerd, containerd-shim, and runc.
The modern Docker architecture is highly modular and distributed.
Dockerd is the high-level daemon that exposes the Docker API.
It manages networking (bridge creation) and handles volume orchestration.
Containerd is the industry-standard runtime manager below dockerd.
It communicates with registries to pull image layers down.
It unpacks those layers into OverlayFS and manages container lifecycles.
Containerd-shim is a tiny, daemonless process created for every container.
It sits directly between containerd and the low-level runtime.
Its primary purpose is to hold open the container's stdout/stderr pipes.
It allows the main containerd process to restart without killing containers.
Finally, runc is the low-level OCI runtime.
It is a simple CLI tool that reads an OCI bundle.
It executes the complex kernel syscalls (unshare, pivot_root) to isolate the process.
It starts the entrypoint, and then immediately exits to save resources.

## Q11: Why is the containerd-shim necessary for zombie reaping and daemon restarts?
In a robust infrastructure, the primary daemon must be resilient.
Containerd must be capable of being updated or restarted on the fly.
This must happen without taking down all running production workloads.
If containerd directly started the container process, a parent-child link forms.
If containerd died, the container would be orphaned or forcefully killed.
To solve this, containerd spawns a containerd-shim process for each container.
The shim becomes the direct parent of the container process.
The shim is designed to be completely decoupled from containerd.
It holds the file descriptors for the container's standard I/O streams.
Furthermore, it handles process management if PID 1 fails.
If the container's PID 1 fails to reap zombie child processes, the shim steps in.
The shim acts as a subreaper to clean them up automatically.
This prevents PID exhaustion on the host node over time.

## Q12: How do User Namespaces facilitate the execution of rootless containers?
Running a container daemon as root presents a significant security risk.
If a vulnerability allows an attacker to escape, they gain host root access.
Rootless containers mitigate this risk by utilizing User Namespaces.
The User Namespace maps user and group IDs inside the container.
It maps them to completely different UIDs/GIDs on the host system.
For example, the container's root user (UID 0) is mapped to a high UID.
It maps to an unprivileged user on the host (e.g., UID 1000).
The process operates under the illusion that it has full root privileges.
It can run package managers and bind to ports inside its isolated environment.
However, if the process escapes the container's boundaries, reality sets in.
The host kernel recognizes the escaped process as UID 1000.
It possesses absolutely no administrative privileges on the host system.
This drastically reduces the blast radius of any container escape vulnerability.

## Q13: Detail the process of inspecting container namespaces via /proc and nsenter.
Every process on a Linux system is represented in the /proc pseudo-filesystem.
To inspect the namespaces of a running container, you must find its PID.
First, determine its PID on the host OS using ps or docker inspect.
Next, examine the /proc/<pid>/ns/ directory.
You will see a list of symlinks representing the 7 namespaces.
These include ipc, mnt, net, pid, user, uts, and cgroup.
Each symlink points to a unique inode number in the kernel.
If two processes share the same inode number for a namespace, they are linked.
They exist in the exact same namespace context.
To interact with these namespaces, you can use the nsenter utility.
By running 'nsenter --target <pid> --net /bin/bash', magic happens.
The kernel executes a new bash shell on the host.
However, it attaches the shell to the existing network namespace of the target PID.
This is the underlying mechanism powering the 'docker exec' command.

## Q14: How does a Union Filesystem handle file deletions using whiteout files?
The lower layers of a Union Filesystem are immutable and read-only.
Because of this, it is impossible to physically delete a file located within them.
When a process inside a container attempts to delete a file, a trick is used.
OverlayFS employs a technique called a whiteout file.
The kernel intercepts the deletion request from the application.
It creates a special character device node in the read-write upperdir.
This node specifically has major/minor numbers set to 0/0.
It uses the exact same filename as the deleted file.
When OverlayFS constructs the merged view, it scans the layers from top to bottom.
Upon encountering the whiteout character device in the upperdir, it stops.
It instructs the kernel to explicitly hide any underlying files with that name.
The containerized application perceives the file as permanently deleted.
Meanwhile, the original file remains perfectly intact in the immutable image layer.

## Q15: Describe the role of veth pairs and Linux bridge networking in container connectivity.
Containers need network connectivity without exposing physical host interfaces.
To provide this, Linux relies on Virtual Ethernet (veth) pairs and software bridges.
A veth pair acts like a virtual ethernet cable with two ends.
When a container starts, the runtime creates a fresh veth pair.
One end (e.g., eth0) is placed inside the container's isolated network namespace.
This provides the container with an interface and an IP address.
The other end (e.g., veth1234) remains in the host's default network namespace.
The host end must be connected to a network to route traffic.
It is attached to a virtual Layer 2 switch, called a Linux Bridge (such as docker0).
The bridge connects all the host-side veth interfaces together.
This allows containers on the same host to communicate via Ethernet framing.
The host's routing table and iptables rules then manage external traffic.
They route packets from the bridge out to the physical network using NAT.

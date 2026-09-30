# Docker & Kubernetes Engineering Curriculum

## Overview
Welcome to the definitive curriculum for Containerization and Orchestration. This track is designed for senior infrastructure engineers, platform engineers, and developers who need to understand exactly what happens at the kernel level when a container runs, and how to orchestrate thousands of these isolated processes at cloud scale.

Containers do not exist as physical kernel entities. Instead, they are an illusion created by combining low-level Linux primitives. To master modern infrastructure, you must move beyond high-level Docker commands and understand namespaces, control groups (cgroups), union filesystems (OverlayFS), and the Open Container Initiative (OCI) runtime specifications. From there, the curriculum scales up to Kubernetes, treating it as a declarative distributed database that reconciles state loops.

Understanding these internals is not optional for production engineering. When a pod is CrashLoopBackOff due to an OOMKill, or a network policy drops packets silently, or an image build takes 20 minutes instead of 20 seconds, the abstraction leaks. Engineers who understand the bottom layers can debug rapidly and architect robustly.

## Module Map

| Module | Core Topics | Learning Objectives |
|--------|-------------|---------------------|
| **01: Docker Internals** | Namespaces, cgroups v1/v2, OverlayFS, OCI, runc, pivot_root | Build a container from scratch using pure Bash and kernel syscalls. |
| **02: Dockerfile Best Practices** | Caching, Multi-stage builds, BuildKit, Security hardening, Distroless | Optimize a 1GB image down to 15MB securely and efficiently. |
| **03: Container Networking** | veth pairs, bridge networks, iptables, NAT, CNI basics | Manually wire two isolated network namespaces together without Docker. |
| **04: Kubernetes Architecture** | etcd, kube-apiserver, kubelet, Controller Manager, Scheduler | Understand the control plane components and the reconciliation loop. |
| **05: K8s Workloads & Scheduling** | Pods, Deployments, StatefulSets, DaemonSets, Taints/Tolerations | Architect resilient deployments with correct pod disruption budgets. |
| **06: K8s Networking & Services** | ClusterIP, NodePort, LoadBalancer, Ingress, CoreDNS, NetworkPolicies | Route external traffic into a cluster and secure pod-to-pod communication. |
| **07: Storage & State** | PV, PVC, StorageClasses, CSI, Stateful Workloads | Persist data reliably across pod restarts and node failures. |

## Why This Matters

Declarative infrastructure has won the orchestration war. But declarative systems are built on imperative realities.
When you specify `resources.limits.memory: "512Mi"` in a Kubernetes Pod spec, you are ultimately writing to `/sys/fs/cgroup/memory/kubepods/pod<id>/memory.limit_in_bytes`.
If you do not know how cgroups enforce these limits, you cannot effectively troubleshoot out-of-memory (OOM) issues or CPU throttling.
If you do not understand OverlayFS, you will unknowingly bloat your images via copy-on-write penalties.
If you do not understand namespaces, you will struggle to debug networking failures or rootless container privilege escalations.

## Prerequisites

Before beginning this curriculum, ensure you possess the following baseline knowledge:

1. **Linux Command Line Interface (CLI):**
   - Fluency in navigating the filesystem and managing processes.
   - Familiarity with core utilities: `grep`, `awk`, `sed`, `strace`, `top`, `htop`, `ps`, `netstat`, `ss`, `ip`, `lsns`, `nsenter`.
   - Understanding of standard streams (stdin, stdout, stderr) and file descriptors.
   - Comfortable reading and manipulating text streams using pipes and redirections.

2. **Networking Basics:**
   - Understanding of the OSI model, TCP/IP stack, subnets, and routing tables.
   - Familiarity with DNS resolution, `/etc/resolv.conf`, `/etc/hosts`, and basic firewall concepts (`iptables`, `nftables`).
   - Basic knowledge of HTTP protocols, TLS handshakes, SNI, and load balancing concepts.
   - Understanding of NAT (Network Address Translation) and how masquerading works in Linux.

3. **System Architecture:**
   - High-level knowledge of how an operating system kernel interacts with hardware.
   - Understanding of CPU scheduling, virtual memory, page faults, system calls (syscalls), and process states.
   - Awareness of virtualization concepts (hypervisors, VT-x/AMD-V) vs. host kernel sharing.
   - Familiarity with systemd and init systems (PID 1 responsibilities, zombie process reaping).

## Study Path and Hands-On Labs

Theoretical knowledge without practical application is fragile. This curriculum is heavily focused on hands-on labs designed to break abstractions and force you into the kernel layer.
- **Read deeply:** The `README.md` in each module directory contains exhaustive explanations. Do not skim.
- **Test your understanding:** Use the `QnA.md` files. We recommend writing out your answers in a text editor before checking the solutions. Active recall builds permanent neural pathways.
- **Quick Reference:** Keep the `CHEATSHEET.md` files open while doing labs for rapid command lookups.
- **Manual Execution:** Do NOT copy-paste lab commands blindly. Type them out. Understand what every flag and argument does. Use `man` pages frequently.

### Suggested Schedule

- **Week 1-2:** Modules 01 and 02. Deep dive into Linux kernel primitives (Namespaces, Cgroups, OverlayFS). Master multi-stage Docker builds, BuildKit, and image security.
- **Week 3-4:** Module 03 and 04. Bridge the gap between local containers and distributed systems. Construct container networks from scratch. Understand the Kubernetes control plane architecture.
- **Week 5-6:** Modules 05, 06, and 07. Deploy, network, and persist real-world applications on a Kubernetes cluster. Master the workload APIs, services, ingresses, and storage abstractions.

By the end of this curriculum, you will possess the specialized knowledge required to troubleshoot the most complex infrastructure failures and architect highly scalable, resilient cloud-native platforms. Let's begin. Proceed to `01_docker_internals/` and explore the fundamental reality of containerization.

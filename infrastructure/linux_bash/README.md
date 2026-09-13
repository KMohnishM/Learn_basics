# Linux Bash Curriculum

Welcome to the definitive Linux Bash Curriculum. This guide is designed for systems engineers, DevOps architects, and backend developers who require a deep, uncompromising understanding of the Linux environment. It is not a beginner's primer; it is a rigorous exploration of system internals, command-line utilities, and automation techniques.

## What This Curriculum Covers

This curriculum focuses on the core pillars of Linux systems engineering. It bypasses graphical abstractions, focusing entirely on the command line interface, POSIX-compliant shell scripting, and the underlying kernel interfaces that govern the operating system. Mastery of these topics is non-negotiable for anyone managing production Linux infrastructure.

You will learn:
- Linux internals and the Virtual Filesystem (VFS) architecture
- Advanced shell navigation, inode mechanics, and file operations
- Complex data wrangling using stream editors and text processing pipelines
- Process lifecycle management, POSIX signals, and kernel job control
- System resource monitoring, bottleneck identification, and optimization
- Service management and daemon lifecycle via systemd

## Module Map

| Module | Focus Area | Key Concepts Covered |
|---|---|---|
| **01** | **Filesystem Navigation** | FHS, Navigation Commands, File Operations, Permissions Model, Disk Usage Analysis, Compression, Archives |
| **02** | **Text Processing** | Regular Expressions, Grep, Sed Stream Editing, Awk Data Processing, Cut, Sort, Uniq, Tr, Pipes, Redirection |
| **03** | **Processes and Jobs** | Process States, Fork/Exec, Signals, Job Control, Priority (Nice/Renice), Resource Monitoring, systemd |
| **04** | **Networking (Upcoming)** | TCP/IP Stack, Sockets, Netfilter/iptables, DNS Resolution, Routing Tables, Network Diagnostics |
| **05** | **Advanced Scripting (Upcoming)** | Bash Internals, Signal Traps, Associative Arrays, Functions, Error Handling, Automation Patterns |

## How to Practice

To get the most out of this curriculum, you must practice these commands in a real Linux environment. Theoretical knowledge without practical application will not translate into engineering competence. You must build muscle memory for these commands and their flags.

Acceptable environments for this curriculum:
1. **WSL2 on Windows**: The Windows Subsystem for Linux version 2 provides a real Linux kernel running via a lightweight Hyper-V utility VM. It is excellent for local development and file manipulation.
2. **Native Linux VM**: Use VirtualBox, VMware Workstation, or Hyper-V to run a dedicated virtual machine. This provides better isolation and allows you to practice snapshotting and low-level disk operations.
3. **Cloud VPS**: A small compute instance on cloud providers like DigitalOcean, AWS EC2 (Free Tier), or Linode provides a realistic remote server experience, forcing you to rely entirely on SSH.

## Recommended Distribution

We strongly recommend **Ubuntu 22.04 LTS (Jammy Jellyfish)** for learning and executing the commands in this curriculum. 

While the concepts taught here are universally applicable to any modern Linux distribution (such as RHEL, Debian, or Arch Linux), Ubuntu 22.04 provides a stable, widely supported baseline. It features predictable package versions, standard systemd configurations, and extensive community documentation. The tools and flags demonstrated assume a GNU userland, which is standard on Ubuntu.

## Key Manual Page Usage

The manual is the definitive source of truth on any Linux system. You must become comfortable consulting it rather than immediately searching the web. The answers to flag combinations and configuration syntax are built into the operating system.

- `man command`: Opens the manual page for the specified command (e.g., `man ls`). Use `/` to search within the pager, and `n` to jump to the next match.
- `man -k keyword`: Searches the short descriptions and manual page names for the keyword (e.g., `man -k "process monitor"`). This is functionally equivalent to the `apropos` command.
- `man 1 command`: Opens the manual page in a specific section. The manual is divided into sections: section 1 (User Commands), section 5 (File Formats and Conventions, like `man 5 passwd`), and section 8 (System Administration Commands).
- `tldr command`: If installed (via `apt install tldr`), this utility provides a community-driven summary of common command usages, stripping away the dense technical specification for immediate, practical reference.

Remember: The Unix philosophy dictates that tools should do one thing well. The manual pages explain precisely what that one thing is and how to modify its behavior. Read them constantly.

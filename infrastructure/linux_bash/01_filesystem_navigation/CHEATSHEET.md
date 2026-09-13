# Linux Filesystem and Navigation Cheatsheet

## The Filesystem Hierarchy Standard (FHS)
| Directory | Description | Example Contents |
|-----------|-------------|------------------|
| `/` | The root directory. The highest level of the filesystem. | All other directories |
| `/bin` | Essential command binaries available to all users. | `ls`, `cp`, `cat` |
| `/sbin` | Essential system binaries, usually requiring root privileges. | `fdisk`, `reboot`, `iptables` |
| `/etc` | Host-specific system-wide configuration files. | `fstab`, `passwd`, `nginx.conf` |
| `/home` | User home directories containing personal files and configurations. | `/home/alice`, `/home/bob` |
| `/root` | The home directory for the root user. | `/root/.bashrc`, `/root/.ssh` |
| `/var` | Variable data that changes frequently during system operation. | `/var/log`, `/var/spool`, `/var/tmp` |
| `/tmp` | Temporary files created by applications or users. Cleared on boot. | `/tmp/session123` |
| `/proc` | Virtual filesystem detailing process and kernel information. | `/proc/cpuinfo`, `/proc/1234` |
| `/sys` | Virtual filesystem for interacting with hardware and kernel subsystems. | `/sys/class/net` |
| `/dev` | Device nodes representing physical and virtual hardware. | `/dev/sda`, `/dev/null` |
| `/usr` | Multi-user utilities and applications. | `/usr/bin`, `/usr/share`, `/usr/local` |
| `/lib` | Essential shared libraries and kernel modules. | `/lib/modules`, `libc.so` |
| `/boot` | Files needed to boot the system (kernel, initramfs, bootloader). | `vmlinuz`, `grub/` |
| `/mnt` | Temporary mount point for filesystems. | `/mnt/usb`, `/mnt/backup` |
| `/media` | Mount points for removable media (automatically mounted). | `/media/cdrom`, `/media/alice/USB` |
| `/opt` | Add-on application software packages. | `/opt/google/chrome` |
| `/srv` | Data for services provided by the system. | `/srv/www`, `/srv/ftp` |

## Navigation Commands
| Command | Action | Common Flags / Examples |
|---------|--------|-------------------------|
| `pwd` | Print working directory. | `pwd -P` (resolve symlinks) |
| `cd` | Change directory. | `cd -` (previous), `cd ~` (home) |
| `ls` | List directory contents. | `ls -la` (all, long format), `ls -lh` (human readable) |
| `tree` | List contents in a tree-like format. | `tree -d` (directories only), `tree -L 2` (depth 2) |

## File Operations
| Command | Action | Common Flags / Examples |
|---------|--------|-------------------------|
| `touch` | Create an empty file or update timestamps. | `touch newfile.txt`, `touch -d "yesterday" file` |
| `mkdir` | Create directories. | `mkdir -p /path/to/dir` (create parents) |
| `cp` | Copy files or directories. | `cp -r` (recursive), `cp -a` (archive/preserve attributes) |
| `mv` | Move or rename files. | `mv oldname newname`, `mv file /dest/` |
| `rm` | Remove files or directories. | `rm -r` (recursive), `rm -f` (force), `rm -rf` (both) |
| `ln` | Create links between files. | `ln source hardlink`, `ln -s source softlink` |

## File Content Commands
| Command | Action | Common Flags / Examples |
|---------|--------|-------------------------|
| `cat` | Concatenate and print files. | `cat file1 file2`, `cat -n file` (number lines) |
| `less` | View file contents interactively. | `less /var/log/syslog`, `/pattern` (search) |
| `more` | View file contents (legacy pager). | `more file.txt` |
| `head` | Output the first part of files. | `head -n 20 file.txt` (first 20 lines) |
| `tail` | Output the last part of files. | `tail -f file.log` (follow), `tail -n 50 file` |
| `wc` | Print newline, word, and byte counts. | `wc -l` (lines), `wc -w` (words), `wc -c` (bytes) |

## Search and Locate Commands
| Command | Action | Common Flags / Examples |
|---------|--------|-------------------------|
| `find` | Search for files in a directory hierarchy. | `find /var -name "*.log"`, `find . -type d` |
| `locate` | Find files by name using a prebuilt database. | `locate passwd`, `locate -i` (case insensitive) |
| `which` | Locate a command binary in PATH. | `which bash`, `which ls` |
| `whereis` | Locate the binary, source, and manual page files. | `whereis python` |
| `type` | Describe a command (builtin, alias, file). | `type cd`, `type ll` |

## Permissions and Ownership
### Octal Permissions Table
| Octal | Binary | Permissions | Representation | Meaning |
|-------|--------|-------------|----------------|---------|
| 0 | 000 | none | `---` | No access |
| 1 | 001 | execute | `--x` | Execute only |
| 2 | 010 | write | `-w-` | Write only |
| 3 | 011 | write, execute | `-wx` | Write and execute |
| 4 | 100 | read | `r--` | Read only |
| 5 | 101 | read, execute | `r-x` | Read and execute |
| 6 | 110 | read, write | `rw-` | Read and write |
| 7 | 111 | read, write, execute | `rwx` | Full access |

### Common Permission Commands
| Command | Action | Common Flags / Examples |
|---------|--------|-------------------------|
| `chmod` | Change file mode bits (permissions). | `chmod 755 script.sh`, `chmod u+x script.sh` |
| `chown` | Change file owner and group. | `chown user:group file`, `chown -R root:root dir/` |
| `chgrp` | Change group ownership. | `chgrp staff file.txt` |
| `umask` | Set default file creation mask. | `umask 022` (default 644 for files, 755 for dirs) |

### Special Permissions
| Permission | Symbol | Octal | Meaning |
|------------|--------|-------|---------|
| SetUID (SUID) | `s` (user) | 4000 | Execute with the privileges of the file owner. |
| SetGID (SGID) | `s` (group) | 2000 | Execute with group privileges; new files inherit dir group. |
| Sticky Bit | `t` (other) | 1000 | Only the file owner or root can delete files within the dir. |

## Disk Usage and Space
| Command | Action | Common Flags / Examples |
|---------|--------|-------------------------|
| `df` | Report filesystem disk space usage. | `df -h` (human readable), `df -T` (print fs type) |
| `du` | Estimate file space usage. | `du -sh /var` (summary human readable) |
| `ncdu` | NCurses disk usage (interactive). | `ncdu /` |
| `lsblk` | List block devices. | `lsblk -f` (show filesystems and UUIDs) |
| `fdisk` | Manipulate disk partition table. | `fdisk -l` (list partitions), `fdisk /dev/sda` |
| `blkid` | Locate/print block device attributes. | `blkid /dev/sda1` |
| `mount` | Mount a filesystem. | `mount /dev/sdb1 /mnt`, `mount -a` (mount all in fstab) |

## Compression and Archives
### Formats Comparison
| Extension | Tool | Characteristics |
|-----------|------|-----------------|
| `.tar` | `tar` | Archive only, no compression. Bundles multiple files. |
| `.gz` | `gzip` | Fast compression, widely supported, single file only. |
| `.bz2` | `bzip2` | Better compression than gzip, slower. |
| `.xz` | `xz` | Very high compression ratio, resource-intensive. |
| `.zip` | `zip` | Cross-platform archive and compression. |

### Archive Commands
| Action | `tar` Command | Example |
|--------|---------------|---------|
| Create Archive | `tar -cvf archive.tar dir/` | `tar -cvf backup.tar /etc` |
| Create Gzip | `tar -czvf archive.tar.gz dir/` | `tar -czvf backup.tar.gz /var/log` |
| Create Bzip2 | `tar -cjvf archive.tar.bz2 dir/` | `tar -cjvf backup.tar.bz2 /home` |
| Create XZ | `tar -cJvf archive.tar.xz dir/` | `tar -cJvf backup.tar.xz /usr/local` |
| Extract | `tar -xvf archive.tar` | `tar -xzvf archive.tar.gz -C /mnt` |
| List contents | `tar -tvf archive.tar` | `tar -tvf backup.tar.gz` |

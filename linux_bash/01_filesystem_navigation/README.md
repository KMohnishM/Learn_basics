# Module 1: Linux Filesystem Navigation and Management

The Linux filesystem is the foundational layer of interaction for any system administrator, DevOps engineer, or developer. Unlike operating systems that use drive letters (like `C:` and `D:`), Linux unifies all storage and hardware devices under a single inverted tree hierarchy, starting at the root directory (`/`). 

This comprehensive module will dive deep into the architecture of the filesystem, the commands required to navigate it effortlessly, file manipulation, permission models, disk space management, and archiving utilities. By mastering these concepts, you transition from simply using Linux to truly commanding it.

---

## 1. The Filesystem Hierarchy Standard (FHS)

The Filesystem Hierarchy Standard (FHS) is the guiding architecture for Linux and UNIX-like operating systems. It dictates exactly where specific types of files should be located. This predictability ensures that software installers, scripts, and administrators always know where to find configuration files, binaries, and logs, regardless of whether they are on Ubuntu, RHEL, Alpine, or Arch Linux.

Understanding the FHS is critical for system troubleshooting and administration. The structure is carefully maintained so that you do not put configurations where binaries belong or logs where user data resides.

### Core Directories Deep Dive

#### `/` (Root)
The absolute pinnacle of the filesystem tree. Every single file, directory, and mounted device on a Linux system is a descendant of the root directory. Only the `root` user has the privilege to write directly into this directory. It is essential not to clutter the root directory with loose files. The root directory only contains standard subdirectories like `/bin`, `/etc`, and `/var`. 

#### `/bin` and `/usr/bin` (Essential Binaries)
The `/bin` directory contains the essential executable binaries (programs) required for the system to boot and run in single-user mode, and utilities accessible to all users. Commands you use daily, such as `ls`, `cp`, `cat`, and `bash`, reside here.
In modern Linux distributions (via the `UsrMerge` movement), `/bin` is often a symbolic link pointing to `/usr/bin`. This unification simplified package management and system architecture, bringing all binaries into a single, unified `/usr` prefix.
Historically, the split between `/bin` and `/usr/bin` was because early UNIX systems ran out of space on their primary hard drives, forcing administrators to put some binaries on a second disk mounted at `/usr`. Today, this split is mostly legacy.

#### `/sbin` and `/usr/sbin` (System Binaries)
Similar to `/bin`, but these directories contain administrative executables that typically require `root` privileges to execute. These tools are used for system maintenance, network configuration, and disk management. Examples include `fdisk`, `iptables`, `sysctl`, and `reboot`.
A standard user can often see these binaries and even run some (like `ip a`), but they will be denied permission to make any changes to the system. The `s` in `/sbin` stands for "system" or "superuser".

#### `/etc` (Configuration Files)
The nerve center for system configuration. The FHS strictly states that `/etc` should only contain static configuration files, not executable binaries. 
- `/etc/passwd`: User account information. Contains usernames, UIDs, GIDs, home directories, and default shells.
- `/etc/shadow`: Contains the encrypted passwords for users. It is strictly readable only by the root user to prevent offline cracking.
- `/etc/fstab`: Filesystem table, detailing how and where disk partitions are mounted automatically at boot.
- `/etc/ssh/sshd_config`: The configuration file for the SSH daemon. This dictates port numbers, allowed authentication methods, and security rules.
- `/etc/systemd/`: Systemd service unit files and configuration.
- `/etc/hostname`: The simple text file containing the system's hostname.
- `/etc/hosts`: Local DNS resolution file overriding standard DNS.

#### `/var` (Variable Data)
Files that are expected to grow and change dynamically during the operation of the system are stored in `/var`. This directory needs to have sufficient disk space allocated because logs and cache files can grow rapidly.
- `/var/log/`: System and application log files. For example, `/var/log/syslog` (or `/var/log/messages` on RedHat systems) is the main system log. `/var/log/auth.log` (or `secure`) tracks all authentication attempts.
- `/var/cache/`: Application cache data (like `apt` or `dnf` package manager caches). These can be safely cleared if disk space is low.
- `/var/spool/`: Queues for print jobs, cron jobs, and mail. When you schedule a job with `at`, it waits here.
- `/var/lib/`: State information for applications. Databases like MySQL often store their raw database files in `/var/lib/mysql/`.

#### `/tmp` and `/var/tmp` (Temporary Files)
Both are scratch spaces for temporary files.
- `/tmp` is wiped clean on every system reboot. Many modern systems mount `/tmp` as a `tmpfs` (RAM disk), meaning data stored here lives entirely in memory and is extremely fast to access but inherently volatile. Programs should expect files placed here to disappear.
- `/var/tmp` is used for larger temporary files that need to persist across reboots. For instance, if an editor like vim creates a recovery file, it might place it here so that it survives an unexpected power loss. `systemd-tmpfiles` regularly cleans these up based on age (e.g., 30 days untouched).

#### `/home` and `/root` (User Directories)
- `/home` contains the personal directories for standard users (e.g., `/home/alice`). It stores personal files, desktop settings, and user-specific configurations (often hidden dotfiles like `.bashrc`, `.ssh/`, or `.config/`). `home` is often mounted on its own partition so that if users fill up the disk, they don't crash the core OS.
- `/root` is the specific home directory for the root user. It is kept separate from `/home` to ensure that root can access its configurations even if the partition hosting `/home` fails to mount due to corruption or malicious user activity.

#### `/proc` and `/sys` (Virtual Filesystems)
These are not real directories on your hard drive; they are illusions created by the Linux kernel in memory. They act as interfaces to the kernel itself.
- `/proc` provides a real-time window into running processes and system resources. For example, reading `/proc/cpuinfo` gives you hardware details directly from the kernel. Every running process has a directory here named after its Process ID (PID). For example, `ls -l /proc/1/exe` will show you exactly what binary started process 1.
- `/sys` (sysfs) exposes a hierarchical view of the system's hardware tree and device drivers. You can interact with hardware, like changing screen brightness or CPU scaling governors, by echoing values into specific files in `/sys/class/backlight` or `/sys/devices/system/cpu`.

#### `/dev` (Device Nodes)
In Linux, "everything is a file," including hardware. The `/dev` directory contains special character and block device files representing physical hardware. Software interacts with hardware by reading from and writing to these files.
- `/dev/sda`, `/dev/nvme0n1`: Represent the physical hard drives.
- `/dev/tty1`: Represents a virtual console terminal.
- `/dev/null`: Is the bit bucket; any data written here vanishes instantly. Useful for discarding output.
- `/dev/zero`: Produces an infinite stream of zero bytes. Useful for zeroing out drives or creating empty files.
- `/dev/random` and `/dev/urandom`: Provide random data generated from system entropy.

#### `/boot`, `/lib`, `/mnt`, `/media`, `/opt`, `/srv`
- `/boot`: Contains the Linux kernel (`vmlinuz`), the initial RAM disk (`initramfs`), and bootloader configurations (like GRUB). Do not touch this unless you know what you are doing. If you delete the kernel, the system will not boot.
- `/lib` and `/lib64`: Essential shared libraries (like `.dll` files in Windows or `.dylib` in macOS) required by binaries in `/bin` and `/sbin`. It also houses kernel modules inside `/lib/modules/` which are dynamically loaded drivers for hardware.
- `/mnt` and `/media`: Directories used for mounting filesystems. `/mnt` is traditionally for temporary, manual mounts by administrators (e.g., `mount /dev/sdb1 /mnt/backup`). `/media` is used by desktop environments to automatically mount removable media like USB drives and CD-ROMs on a per-user basis (e.g., `/media/alice/USB_DRIVE`).
- `/opt`: Used for installing self-contained, third-party software packages (like Google Chrome, JetBrains IDEs, or enterprise database software) that do not split their files across the standard FHS. Everything for the app goes into `/opt/appname/`.
- `/srv`: Data specifically served by the system. If you run a web server, the web root might be in `/srv/www/`. If you run an FTP server, the files might be in `/srv/ftp/`. It logically separates server data from system configuration and variable states.

---

## 2. Navigation Commands

Navigating the command line efficiently requires mastering a few core commands and understanding the fundamental difference between relative and absolute paths.
- **Absolute Path**: Starts from the very root of the filesystem `/` and provides the full explicit path (e.g., `/var/log/nginx/access.log`). An absolute path works flawlessly regardless of your current working directory.
- **Relative Path**: Starts from your current directory. It uses special directory notations: `.` (representing the current directory) and `..` (representing the parent directory). If you are in `/var/log`, the relative path to the nginx logs is simply `nginx/access.log`.

### `pwd` (Print Working Directory)
The first rule of navigation is knowing exactly where you are located. It is easy to get lost in complex directory structures.
```bash
$ pwd
/home/developer/projects
```
*Advanced flag:* `pwd -P` resolves all symbolic links. If `/var/www/html` is actually a symlink to `/srv/web/public_html`, typing `cd /var/www/html` followed by `pwd` will show `/var/www/html`. But `pwd -P` will reveal the true physical location: `/srv/web/public_html`.

### `cd` (Change Directory)
Moves your shell's current working directory to a new location in the FHS. It is the most fundamental navigation command.
```bash
$ cd /etc/ssh         # Absolute path: reliably jumps straight to /etc/ssh from anywhere.
$ cd ../../var/log    # Relative path: moves up two levels, then down into /var/log.
$ cd ~                # Returns you to your home directory (expands to /home/user).
$ cd -                # Toggles you back to the exact directory you were in immediately prior. Excellent for jumping back and forth.
$ cd                  # Running cd with no arguments also returns you home.
```

### `ls` (List Directory Contents)
The command you will use hundreds of times a day. It displays the files and directories contained within a location.
```bash
$ ls                  # Basic bare-bones listing. Just names.
$ ls -l               # Long listing format. Critical for seeing permissions, ownership, sizes, and modification dates.
$ ls -a               # Show all files, including hidden dotfiles (like .bashrc or .git folders).
$ ls -lh              # Human-readable sizes (converts byte counts into K, M, G).
$ ls -lrt             # Sort by modification time in reverse order. This puts the newest, most recently modified files at the very bottom of your screen, right above your prompt.
$ ls -F               # Appends an indicator to file names: '*' for executables, '/' for directories, '@' for symlinks.
$ ls -1               # Forces output to be one file per line, useful for scripting loops.
```

### `tree`
A powerful utility that outputs a visual, depth-indented hierarchy of files and directories. It helps you grasp the structure of an unknown project instantly.
```bash
$ tree /etc/systemd -L 2 -d
# -L 2: Restrict output to a maximum depth of 2 levels deep, preventing the command from outputting thousands of lines.
# -d: List only directories, completely ignoring standard files.
# -a: Include hidden files in the tree.
# --charset=ascii: Use ASCII characters for the tree lines if your terminal has font rendering issues.
```

---

## 3. File Operations

Creating, moving, copying, and deleting files and directories is the core of system management. Linux handles these operations securely and predictably.

### `touch`
Originally designed to update the modification and access timestamps of an existing file (hence "touching" it). However, its most common modern use is to rapidly create empty placeholder files.
```bash
$ touch new_script.sh
$ touch file1.txt file2.txt file3.txt
$ touch -m -d "2023-01-01 12:00:00" old_file.txt # Spoof the modification time to a date in the past.
$ touch -a -t 202401011200 old_file.txt          # Change only the access time.
```
If `new_script.sh` does not exist, `touch` creates a 0-byte file. If it does exist, it simply updates the timestamp to the current clock time without altering the contents.

### `mkdir` (Make Directory)
Creates new directories on the filesystem.
```bash
$ mkdir project_alpha
$ mkdir data logs config
$ mkdir -p app/src/main/java   # The -p (parents) flag creates parent directories if they don't exist, preventing "No such file or directory" errors. It also suppresses errors if the directory already exists.
$ mkdir -m 700 secret_dir      # Creates a directory and instantly sets its permissions to 700 (rwx------) for security.
```

### `cp` (Copy)
Copies files and directories from a source to a destination.
```bash
$ cp source.txt dest.txt
$ cp file1.txt file2.txt /backup/dir/  # Copy multiple files into a target directory.
$ cp -r /var/log/nginx /home/backup/   # -r recursively copies directories and their entire contents.
$ cp -a /etc/ /backup/etc/             # -a (archive) copies recursively while preserving ALL permissions, ownership, timestamps, and symbolic links. Crucial for reliable system backups.
$ cp -i file.txt /dest/                # -i (interactive) prompts for confirmation before overwriting an existing file.
$ cp -v source.txt dest.txt            # -v (verbose) prints exactly what is being copied.
```

### `mv` (Move / Rename)
Moves a file or directory to a new location. Since moving a file to the same directory with a new name is the definition of renaming, `mv` elegantly handles both actions.
```bash
$ mv old_name.txt new_name.txt         # Renaming a file in place.
$ mv data.csv /var/lib/myapp/          # Moving a file to a new directory.
$ mv dir1 dir2 /target/                # Moving multiple directories at once.
$ mv -i file.txt /dest/                # -i prompts before overwriting, preventing accidental data loss.
$ mv -n file.txt /dest/                # -n (no clobber) refuses to overwrite any existing file.
```

### `rm` (Remove)
Deletes files or directories permanently. **Linux does not have a trash can by default on the CLI.** Once a file is removed via `rm`, it is gone and can only be recovered through complex forensic tools if the disk sectors haven't been overwritten.
```bash
$ rm unused_file.txt
$ rm file1 file2 file3
$ rm -i script.sh          # -i prompts for confirmation before every single deletion.
$ rm -r old_project/       # Recursively delete a directory and all of its contents.
$ rm -f lockfile.lock      # Force deletion, ignoring non-existent files and never prompting for confirmation.
$ rm -rf /tmp/scratch/     # Danger: Recursively and forcefully delete. Be extremely careful when using -rf, especially as root.
```

### `ln` (Links)
Links allow a single file to be accessible from multiple locations in the filesystem, saving disk space and simplifying administration.
- **Hard Links**: Create a new directory entry pointing to the exact same inode (physical data location) on the disk. They cannot cross filesystem partitions (you cannot hard link a file from `/dev/sda1` to `/dev/sdb1`) and they cannot link directories. If you delete the original file, the hard link still retains the data because the inode link count is still > 0.
  ```bash
  $ ln /path/to/original.txt /path/to/hardlink.txt
  ```
- **Symbolic (Soft) Links**: Create a new, tiny file whose sole purpose is to contain the text path to the target. They act like Windows shortcuts. They can cross partitions and link entire directories. If the original target is deleted, the symlink becomes a "dangling" or "broken" link.
  ```bash
  $ ln -s /usr/share/nginx/html/ /var/www/html
  $ ln -sf /new/target /var/www/html   # -f forces the link creation, overwriting the existing link.
  ```

---

## 4. File Content Commands

Reading, analyzing, and evaluating text files directly from the terminal without needing a graphical text editor.

### `cat` (Concatenate)
Dumps the entire contents of a file to standard output. Excellent for small files, but terrible for 5GB log files.
```bash
$ cat /etc/hostname
$ cat file1.txt file2.txt > combined.txt  # Concatenate two files and redirect into a third.
$ cat -n /etc/passwd       # -n numbers all output lines, making it easier to reference.
$ cat -E /script.sh        # -E shows a '$' at the end of every line, helping spot trailing whitespace.
```

### `less` and `more` (Pagers)
For viewing large files, pagers read the file chunk by chunk, allowing you to scroll without overwhelming your memory or terminal buffer.
- `more` is the legacy utility. It only allows forward scrolling.
- `less` is the modern standard. "Less is more." It allows forward/backward scrolling, searching, and advanced navigation.
```bash
$ less /var/log/syslog
# While inside the less interface:
# Press 'Space' or 'f' to page down, 'b' to page up.
# Use arrow keys for line-by-line scrolling.
# Type '/' followed by a word to search forward (e.g., /ERROR). Press 'n' to find the next match, 'N' for previous.
# Type '?' to search backward.
# Press 'q' to quit and return to the terminal.
```

### `head` and `tail`
Display only the absolute beginning or the very end of a file.
```bash
$ head -n 15 /var/log/messages    # Print the first 15 lines. Default is 10.
$ head -c 100 /dev/urandom        # Print exactly the first 100 bytes.
$ tail -n 50 /var/log/syslog      # Print the last 50 lines.
```
**Crucial flag for administration:** `tail -f` (follow) continuously monitors a file and outputs new data directly to the screen as it is appended. Essential for live log monitoring.
```bash
$ tail -f /var/log/nginx/access.log
```
*Advanced:* `tail -F` tracks by file name, not by inode. This means if a log rotation tool renames `access.log` to `access.log.1` and creates a brand new `access.log`, `tail -F` will seamlessly switch to the new file, whereas `tail -f` will get stuck watching the old, renamed file.

### `wc` (Word Count)
Calculates essential metrics about a file: lines, words, and byte counts.
```bash
$ wc script.py                    # Prints lines, words, and characters.
$ wc -l script.py                 # Print only the line count.
$ wc -w script.py                 # Print only the word count.
$ wc -c data.bin                  # Print only the byte count.
$ cat /etc/passwd | grep "/bin/bash" | wc -l  # Highly common pipeline: count how many users have bash as their shell.
```

---

## 5. Finding Files and Commands

Locating files efficiently across thousands of directories is a required skill. You cannot always rely on remembering where you put things.

### `find`
The most powerful and complex search tool in Linux. It searches the live filesystem in real-time based on extensive, highly specific criteria. Because it scans the actual disk, it is perfectly accurate, though it can be slow on massive filesystems.
```bash
$ find /var/log -name "*.log"                     # Find all files ending in .log. Use quotes to prevent shell expansion.
$ find / -type d -name "config"                   # Find only directories (-type d) named config.
$ find /tmp -type f -mtime +7                     # Find files (-type f) modified more than 7 days ago.
$ find /data -size +500M                          # Find files strictly larger than 500 Megabytes.
$ find /home -user alice -group staff             # Find files owned by user alice and group staff.
$ find /var/spool -type f -empty -delete          # Find empty files and directly execute deletion (safest and fastest method).
```
You can also execute arbitrary commands directly on the results using the `-exec` action:
```bash
$ find /var/log -name "*.gz" -exec rm -f {} \;    # Deletes all found .gz files. The {} is replaced by the file name, and \; terminates the command.
$ find /etc -type f -exec grep -H "192.168.1.1" {} + # Grep for an IP in all files. The + is more efficient as it bundles arguments.
```

### `locate`
Searches a pre-built database (typically updated daily by a cron job running `updatedb`) rather than scanning the live disk. It is incredibly fast—returning results instantly—but it may not show files created in the last few hours, and might list files that were recently deleted.
```bash
$ locate httpd.conf
$ locate -i shadow       # -i ignores case sensitivity (finds Shadow, SHADOW, etc).
$ locate -b '\syslog'    # -b (basename) matches only the file name itself, not the directory path.
```

### `which`, `whereis`, `type`
Tools to locate executable commands and understand how the shell interprets them.
- `which bash`: Searches your `$PATH` environment variable directories (like `/usr/bin`, `/usr/local/bin`) and returns the exact absolute path to the binary that would be executed if you typed `bash`.
- `whereis python3`: Returns not just the binary, but also the location of the source code (if installed) and the manual pages. Example output: `/usr/bin/python3 /usr/share/man/man1/python3.1.gz`.
- `type cd`: Tells you exactly how the shell itself interprets a command. 
  - `type cd` -> `cd is a shell builtin` (handled internally by bash).
  - `type ls` -> `ls is aliased to ls --color=auto` (handled via alias).
  - `type grep` -> `grep is /usr/bin/grep` (an external binary file).

---

## 6. Permissions and Ownership

Linux is fundamentally a multi-user operating system. The permission model is its core security mechanism, preventing users from reading each other's data or modifying system files. Every file is owned by a specific User and a specific Group. Permissions dictate what the User, the Group, and Everyone Else (Others) can do.

### The Permission Triad
When you run `ls -l`, you see a 10-character string like `-rwxr-xr--`.
- **Position 1**: File type indicator. `-` for a standard file, `d` for a directory, `l` for a symbolic link, `c` for a character device.
- **Positions 2-4 (User/Owner)**: Permissions for the file's creator/owner. `rwx` (Read, Write, Execute).
- **Positions 5-7 (Group)**: Permissions for users who are members of the file's group. `r-x` (Read, Execute).
- **Positions 8-10 (Other/World)**: Permissions for absolutely everyone else on the system. `r--` (Read only).

For directories, "Execute" (`x`) has a special meaning: it is the permission to *enter* the directory (`cd` into it). Read (`r`) is the permission to *list* the contents (`ls`), and Write (`w`) is the permission to create or delete files inside it.

### Octal Notation
Permissions are commonly calculated and applied using binary/octal numbers for speed and precision.
- Read (`r`) = 4
- Write (`w`) = 2
- Execute (`x`) = 1
Add these values together for each category:
- `rwx` = 4 + 2 + 1 = **7** (Full access)
- `rw-` = 4 + 2 + 0 = **6** (Read and Write)
- `r-x` = 4 + 0 + 1 = **5** (Read and Execute)
- `r--` = 4 + 0 + 0 = **4** (Read only)
- `---` = 0 + 0 + 0 = **0** (No access)

Therefore, `755` translates to `rwxr-xr-x`. `644` translates to `rw-r--r--`.

### `chmod` (Change Mode)
The command used to modify file permissions. It accepts both octal and symbolic modes.
```bash
$ chmod 755 script.sh          # Octal: Sets exactly rwxr-xr-x.
$ chmod 644 document.txt       # Octal: Sets exactly rw-r--r--.
$ chmod 700 private_key.pem    # Octal: Sets rwx------ (Owner full access, everyone else locked out).
$ chmod u+x script.sh          # Symbolic: Adds (+) execute (x) permission for the User (u).
$ chmod go-w config.yaml       # Symbolic: Removes (-) write (w) permission from Group (g) and Other (o).
$ chmod a+r readme.md          # Symbolic: Adds read to All categories (User, Group, Other).
```

### `chown` and `chgrp`
Changes the ownership of a file. Usually, only root can arbitrarily change file ownership to other users.
```bash
$ chown root:staff daemon.conf # Sets the user owner to 'root' and the group owner to 'staff'.
$ chown alice file.txt         # Changes only the user owner to alice.
$ chown -R nginx:nginx /var/www/ # Recursively changes owner and group for an entire directory tree.
$ chgrp developers project_doc # Changes only the group ownership.
```

### Special Permissions: SUID, SGID, and Sticky Bit
These are advanced permissions that alter standard execution and ownership behavior.
- **SUID (SetUID - Octal 4000)**: Displayed as an `s` in the user execute position (e.g., `rwsr-xr-x`). If an executable binary has SUID set, it executes with the privileges of the file's owner, not the user launching it. The classic example is `/usr/bin/passwd`, owned by root. It has SUID so a normal user can execute it as root in order to modify the highly secure `/etc/shadow` file to change their password. It is incredibly dangerous if applied to insecure scripts.
- **SGID (SetGID - Octal 2000)**: Displayed as an `s` in the group execute position. When set on a binary, it runs with group privileges. When set on a directory (e.g., `rwxrwsr-x`), any new files created inside that directory will automatically inherit the group ownership of the directory itself, rather than the primary group of the user creating the file. This is the cornerstone of creating shared, collaborative team folders.
- **Sticky Bit (Octal 1000)**: Displayed as a `t` in the other execute position (e.g., `rwxrwxrwt`). When applied to a directory, it restricts deletion. A user can only delete or rename files within the directory if they are the explicit owner of the file (or root). It is set on `/tmp` by default (`chmod 1777 /tmp`), ensuring everyone can write to `/tmp`, but Alice cannot delete Bob's temporary files.

### `umask`
The `umask` (user file-creation mode mask) defines the default permissions applied to newly created files and directories. It works by subtracting (masking) permission bits from a starting base value.
The absolute base starting point for a directory is `777` (`rwxrwxrwx`), and for a file is `666` (`rw-rw-rw-`). Linux never creates files as executable by default for security.
If your configured umask is `022` (the standard on most systems):
- New directories: `777` minus `022` equals `755` (`rwxr-xr-x`).
- New files: `666` minus `022` equals `644` (`rw-r--r--`).
```bash
$ umask       # View current umask
0022
$ umask 027   # Highly restrictive setting for secure environments. 
# New directories become 750 (rwxr-x---).
# New files become 640 (rw-r-----), completely locking out the "Other" category.
```

---

## 7. Disk Usage and Space Management

Monitoring storage capacity and understanding disk layouts is vital for preventing system crashes. A server with a 100% full root partition will often fail catastrophically.

### `df` (Disk Free)
Reports filesystem disk space usage. It looks at the mounted partitions and queries the filesystem directly.
```bash
$ df -h              # Human-readable output (converts sizes to Megabytes/Gigabytes).
$ df -T              # Include the filesystem type column (e.g., ext4, xfs, btrfs, tmpfs).
$ df -i              # View inode usage. A filesystem has a finite number of inodes (file records). A disk can be 100% full of inodes (due to millions of tiny 1-byte files) while still having 500GB of free block space. If inode usage hits 100%, you cannot create new files.
$ df -Th /var        # Check the specific mount point for /var.
```

### `du` (Disk Usage)
Estimates space used by specific files or directory trees by recursively scanning and summing file sizes.
```bash
$ du -sh /var/log    # Summary (-s) and human-readable (-h) size of the entire directory.
$ du -h --max-depth=1 /home | sort -hr   # Calculate sizes of user home directories, outputting only the top level, and sort them largest to smallest. Excellent for finding storage hogs.
```
*Tip: `ncdu` (NCurses Disk Usage) is a fantastic interactive, terminal-based alternative to `du`. It provides a navigable interface to rapidly explore and delete files consuming disk space.*

### `lsblk` (List Block Devices)
Displays a clean, tree-like overview of all block devices (physical disks, partitions, logical volumes) attached to the system, regardless of whether they are mounted.
```bash
$ lsblk
$ lsblk -f           # Shows filesystems types, UUIDs (Universally Unique Identifiers), and mount points.
$ lsblk -p           # Prints absolute paths to the device nodes (e.g., /dev/sda1).
```

### `fdisk` and `blkid`
- `fdisk -l`: Lists detailed partition tables across all attached disks (requires root privileges). It shows sectors, cylinders, and partition types (Linux, swap, EFI).
- `blkid`: Outputs the UUID and filesystem type of block devices. The UUID is critical; it is the modern standard for identifying disks in `/etc/fstab`, ensuring that even if `/dev/sda` becomes `/dev/sdb` after a reboot, the system still mounts the correct partition.

### `mount` and `umount`
Attaches a filesystem found on a block device into the live FHS hierarchy, making its data accessible.
```bash
$ mount /dev/sdb1 /mnt/data    # Manually mount the sdb1 partition to the /mnt/data directory.
$ mount -t nfs 192.168.1.50:/share /mnt/nfs  # Mount a remote Network File System.
$ mount -a                     # Read /etc/fstab and attempt to mount all filesystems listed within it. Often used after editing fstab.
$ umount /mnt/data             # Unmount (detach) the filesystem safely, flushing caches to disk.
$ umount -l /mnt/data          # Lazy unmount. Detaches immediately, cleans up references later. Useful if a network drive hangs.
```

---

## 8. Compression and Archives

Linux relies heavily on command-line archiving to bundle files together and compress them for backup, distribution, and log management.

### Understanding `tar` (Tape Archive)
The `tar` utility is historically designed for writing data sequentially to magnetic tapes. Critically, `tar` **does not compress data** on its own. It merely bundles multiple files and directory structures into a single, contiguous archive file (a "tarball", ending in `.tar`).
Compression is achieved by passing the resulting tarball through a dedicated compression utility (like gzip or bzip2).
```bash
# Create an uncompressed archive
$ tar -cvf config_backup.tar /etc/nginx /etc/ssh
# Breakdown:
# -c: Create a new archive.
# -v: Verbose. List the files being processed to the screen.
# -f: File name of the archive follows immediately.
```

### Compression Algorithms Compared
Linux offers several compression algorithms, representing a trade-off between speed and compression ratio.
- **gzip (`.gz`)**: The standard, fast compression tool. Widely supported, fast to compress and decompress, with decent ratios. It is the default for almost everything.
- **bzip2 (`.bz2`)**: Achieves a tangibly better compression ratio than gzip, but is considerably slower.
- **xz (`.xz`)**: Employs the LZMA algorithm. Provides maximum compression ratio, making files incredibly small. However, it is highly CPU and memory intensive, taking a long time to compress. Used heavily for distributing Linux kernel sources and OS images.

### Using `tar` with Transparent Compression
Modern versions of GNU `tar` handle compression transparently via specific flags, eliminating the need to pipe output through gzip manually.
```bash
# Gzip (Most common for source code, backups, and logs)
$ tar -czvf archive.tar.gz /home/user/docs     # Create with gzip (-z)
$ tar -xzvf archive.tar.gz -C /restore/path/   # Extract (-x) and optionally decompress to a specific target directory (-C)

# Bzip2
$ tar -cjvf backup.tar.bz2 /var/www            # Create with bzip2 (-j)
$ tar -xjvf backup.tar.bz2                     # Extract

# XZ (Excellent for highly compressible text or system images)
$ tar -cJvf system.tar.xz /bin                 # Create with xz (-J)
$ tar -xJvf system.tar.xz                      # Extract
```
*Pro Tip: When extracting, modern `tar` automatically detects the compression algorithm based on the file signature. Therefore, `tar -xvf archive.tar.xz` or `tar -xvf archive.tar.gz` works perfectly without explicitly needing the `-z`, `-j`, or `-J` flags!*

### `zip` and `unzip`
While `tar.gz` is the Linux standard, the `.zip` format is required for seamless cross-platform compatibility with Windows and macOS users. The `zip` utility handles both bundling and compression simultaneously.
```bash
$ zip -r project_archive.zip /path/to/project_folder      # Recursively (-r) zip an entire folder structure.
$ unzip project_archive.zip -d /target/directory          # Extract to a specified directory (-d).
$ unzip -l project_archive.zip                            # List (-l) the contents of the zip file without extracting.
```

### Advanced Archiving: `rsync`
While not strictly compression, `rsync` is the industry standard tool for transferring and backing up files. It uses a delta-transfer algorithm, meaning if you sync a 10GB file and change 1MB of it, `rsync` only transfers the 1MB change over the network.
```bash
$ rsync -av --progress /source/directory/ /destination/directory/
# -a: Archive mode (equals -rlptgoD), preserving all permissions and symlinks perfectly.
# -v: Verbose output.
# --progress: Shows a progress bar during transfer.
```

---

## 9. Advanced Filesystem Concepts

For those aiming for mastery, understanding the lower-level structures that manage data on a Linux filesystem is crucial. This goes beyond commands and into how the kernel actually stores bytes on disks.

### Inodes (Index Nodes)
When you create a file on a Linux filesystem (like ext4 or xfs), the system creates two things: the actual data blocks that contain the file's content, and an **inode**. The inode is a metadata record that stores everything *about* the file, except its name and its actual data.
An inode contains:
- The file's size.
- Device ID.
- User ID (UID) of the file's owner.
- Group ID (GID).
- The file's permissions (read, write, execute).
- Time stamps (creation, modification, and access).
- Pointers to the physical data blocks on the hard drive where the file's content is actually stored.

The filename itself is stored in the **directory file** (which maps the filename string to the inode number). This is why renaming a file is instant; you are simply updating the text mapping in the directory, not moving the data or altering the inode. This is also how hard links work: two different filenames in a directory mapping to the same single inode number. 
If your filesystem runs out of inodes (e.g., due to creating millions of zero-byte files), you will receive a "No space left on device" error, even if you have terabytes of free disk space. Use `df -i` to monitor this.

### The Superblock
The superblock is the most critical piece of metadata for a filesystem. It sits at the very beginning of the partition and contains the master configuration for that specific filesystem. 
It records:
- The total size of the filesystem.
- How many blocks and inodes are total, free, and used.
- The block size (e.g., 4KB).
- The filesystem's mount time and state (clean or dirty).
If the primary superblock is corrupted, the filesystem cannot be mounted. Because of its critical nature, Linux filesystems maintain multiple backup copies of the superblock distributed across the disk.

### Journaling Filesystems
Modern filesystems like **ext4** and **xfs** are "journaling" filesystems. Before a journaling filesystem commits a change to the actual data blocks or inodes, it first writes a log of what it intends to do in a dedicated area called the journal.
If a power failure or kernel panic occurs during a write operation, the system does not need to perform a slow, comprehensive scan of the entire disk (like `fsck` used to do on ext2) on the next boot. Instead, it simply reads the journal, replays any incomplete transactions, and restores the filesystem to a consistent state within seconds. This dramatically improves reliability and recovery time.

### Virtual Filesystem Switch (VFS)
Linux supports dozens of different filesystems (ext4, btrfs, xfs, fat32, ntfs, nfs). The kernel achieves this seamlessly using a layer of abstraction called the Virtual Filesystem Switch (VFS).
When you run `cp file.txt /mnt/usb`, the `cp` command talks to the VFS using standard system calls. The VFS determines that `/mnt/usb` is formatted as FAT32, and it translates the standard system calls into the specific low-level operations required by the FAT32 driver. This allows user-space programs to remain completely ignorant of the underlying disk formatting.

### Special File Types Deep Dive
Linux extends the concept of a file far beyond simple text or binary data.
- **Named Pipes (FIFOs):** A mechanism for inter-process communication (IPC). Created using the `mkfifo` command. They appear as files on the disk (with a `p` in the `ls -l` output). If Process A writes to the FIFO, it blocks until Process B reads from it. The data passes through memory, never hitting the actual disk platters.
- **Sockets:** Used for advanced, bidirectional network and local IPC. They appear as files (with an `s` in `ls -l`). For example, MySQL might create a local socket file `/var/run/mysqld/mysqld.sock`. Local clients connect to this file instead of using TCP/IP, which is significantly faster.
- **Device Nodes (Character and Block):** As mentioned in the `/dev` section, these files are interfaces to device drivers. Block devices (like `/dev/sda`) buffer data in fixed-size blocks and are used for storage. Character devices (like `/dev/tty` or `/dev/urandom`) stream data character-by-character unbuffered.

### Mount Namespaces and Containers
Understanding mount namespaces is the key to understanding modern containerization (like Docker or Kubernetes).
A mount namespace isolates the list of mount points seen by the processes within it. In a standard system, all processes share the same mount namespace; if you mount a USB drive to `/mnt`, every process can see it.
When a container engine starts a container, it creates a new mount namespace for it. Inside this namespace, it mounts a completely new, minimal root filesystem (`/`). To the processes inside the container, they appear to be running on their own dedicated Linux machine with its own FHS. They cannot see the host's `/home` or `/dev` directories unless explicitly bound into the container's namespace. This is the foundation of container security and isolation.

---

## 10. Advanced Filesystem Administration Topics

Continuing the deep dive into system internals, this section explores network filesystems, advanced permission models, and data security mechanisms.

### Network Filesystems (NFS and SSHFS)
While local storage relies on block devices, Network Filesystems abstract storage over network protocols.
- **NFS (Network File System):** A classical UNIX standard for sharing directories over a local network. A server exports a directory (defined in `/etc/exports`), and a client mounts it. For the client, interacting with the NFS mount feels exactly like interacting with local disk storage. 
  ```bash
  $ mount -t nfs 10.0.0.5:/var/nfs_share /mnt/shared_data
  ```
- **SSHFS (SSH Filesystem):** A remarkably secure and easy alternative to NFS. It uses the SFTP protocol over a standard SSH connection to mount a remote directory. It requires no special server setup—if you can SSH into a machine, you can mount its filesystem using SSHFS.
  ```bash
  $ sshfs user@remote-host:/remote/path /local/mountpoint
  ```

### Access Control Lists (ACLs)
Standard Linux permissions (User, Group, Other) are sometimes too restrictive. What if you want to give Alice read/write access and Bob read-only access to a file owned by Charlie, without creating a new specialized group? You use Access Control Lists (ACLs).
ACLs provide granular control, allowing you to specify permissions for specific users and groups beyond the traditional triad.
- View ACLs using `getfacl filename`.
- Set ACLs using `setfacl -m u:alice:rw filename`.

### SELinux and AppArmor
Beyond standard permissions and ACLs, modern enterprise Linux distributions employ Mandatory Access Control (MAC) systems like SELinux (Red Hat family) or AppArmor (Debian/Ubuntu family).
Even if a process runs as `root`, a MAC system can restrict its actions. For example, SELinux can enforce a policy stating that the `httpd` process can only read files labeled with the `httpd_sys_content_t` context. If the web server is compromised, the attacker cannot read `/etc/shadow` because the MAC policy explicitly denies it, overriding the standard discretionary file permissions. Understanding file contexts is a critical advanced administration skill.

---

## 11. Real-World Troubleshooting Scenarios

As a systems engineer, you will often need to debug filesystem-related issues. Here are a few common scenarios and the commands used to resolve them.

### Scenario A: "No space left on device" (But df shows 50% free)
You try to create a file and get a "No space left on device" error. You run `df -h` and see plenty of free gigabytes.
- **Diagnosis:** Your filesystem has run out of inodes. This happens when applications create millions of tiny files (like PHP sessions or an out-of-control mail queue).
- **Solution:** Run `df -i` to confirm 100% inode usage. Then use a tailored `find` or `du` command to locate directories with massive file counts:
  ```bash
  $ find / -xdev -type d -exec sh -c 'echo "$(ls -1 "{}" | wc -l) {}"' \; | sort -rn | head -n 10
  ```
  Once you identify the offending directory, delete the unneeded files to free up inodes.

### Scenario B: A Deleted File is Still Consuming Space
You have a 50GB log file. You run `rm /var/log/huge.log`. However, `df -h` still shows the disk is completely full.
- **Diagnosis:** A process (like a web server or database) still has an open file handle on `huge.log`. In Linux, the file's directory entry is removed by `rm`, but the actual data blocks on disk are not freed until the file's link count is 0 *and* all open file descriptors point to it are closed.
- **Solution:** Use the `lsof` (List Open Files) command to find the process holding the ghost file open.
  ```bash
  $ lsof +L1
  ```
  Look for files marked as `(deleted)`. Note the PID of the process holding it open. You must restart that service (e.g., `systemctl restart nginx`) or kill the process to force the kernel to release the disk blocks.
  - **Pro-tip:** To avoid this in the future, don't use `rm` on active logs. Instead, truncate them: `> /var/log/huge.log`. This shrinks the file to 0 bytes without breaking the file handle.

---

## 12. Conclusion and Best Practices

Navigating and managing the Linux filesystem is a skill that requires practice and respect for the underlying architecture.
- **Respect Permissions:** Never arbitrarily run `chmod -R 777` to fix a "Permission denied" error. It creates catastrophic security vulnerabilities. Understand the FHS, use `chown` to fix ownership issues, or use precision `find` commands to set `644`/`755` selectively.
- **Use the Right Tools:** Treat `/dev/null` as your best friend for silencing noisy scripts or cron job emails.
- **Log Management:** Understand the critical difference between `tail -f` and `tail -F` if you ever manage log files that undergo rotation.
- **Defensive Scripting:** Always use the `-p` flag with `mkdir` in scripts to prevent execution failure if parent directories are missing.
- **Backup Integrity:** When copying critical system data, configurations, or performing migrations, `cp -a` is absolutely non-negotiable to maintain metadata integrity.

End of Module 1. You are now equipped with the fundamental commands and architectural understanding required to operate Linux systems securely and efficiently. Proceed to the `QnA.md` document for practical reinforcement of these concepts.

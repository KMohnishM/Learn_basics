# Questions and Answers: Linux Filesystem Navigation and Management

## 1. Explain the Linux Filesystem Hierarchy Standard. What lives in /etc, /var, /proc, /dev, and /usr? Why is /proc special?

The Linux Filesystem Hierarchy Standard (FHS) is a convention that defines the directory structure and directory contents in Unix-like operating systems. It ensures predictability across different Linux distributions.
- `/etc`: Contains system-wide configuration files and startup scripts. You will find files like `/etc/passwd`, `/etc/fstab`, and application-specific configurations like `/etc/nginx/nginx.conf`.
- `/var`: Holds variable data that changes during the normal operation of the system. This includes log files (`/var/log`), spool files for mail and printing (`/var/spool`), and temporary files preserved between reboots (`/var/tmp`).
- `/proc`: A virtual filesystem that acts as a window into the running kernel and processes. It is completely memory-based and does not occupy disk space.
- `/dev`: Contains device nodes, which are special files representing hardware devices and pseudo-devices (like `/dev/sda` for a hard drive or `/dev/null` for the bit bucket).
- `/usr`: Contains the majority of multi-user utilities, applications, and libraries. It includes `/usr/bin` for user commands, `/usr/lib` for libraries, and `/usr/share` for architecture-independent data.
`/proc` is special because it does not exist on a physical storage device. The files within it are generated dynamically by the Linux kernel when they are read. For instance, reading `/proc/cpuinfo` triggers the kernel to gather and present CPU hardware details. Modifying files in `/proc` (specifically `/proc/sys`) can alter kernel parameters on the fly without rebooting.

## 2. What is the difference between a hard link and a symbolic (soft) link? What happens to each when the original file is deleted?

A hard link creates an additional directory entry that points directly to the same underlying inode (index node) as the original file on the filesystem. A symbolic (soft) link, on the other hand, is a distinct file with its own inode whose data block contains a text string representing the path to the target file.
Because hard links point to the same inode, they must reside on the same filesystem partition as the target. They also cannot be created for directories (to prevent infinite filesystem loops). Soft links can cross filesystem boundaries and can link to directories.
When the original file is deleted:
- **Hard Link**: The data remains intact and accessible via the hard link. The file's link count in the inode is decremented by one. The data on disk is only truly freed when the link count reaches zero and no processes have the file open.
- **Symbolic Link**: The link becomes "broken" or "dangling." The path it points to no longer exists. Attempting to read the soft link will result in a "No such file or directory" error, even though the soft link file itself still exists on the disk.

## 3. Explain Linux file permissions in full. What does chmod 755 mean in both symbolic and octal notation? What is the setuid bit and why is it dangerous?

Linux file permissions dictate who can read, write, or execute a file. Permissions are divided into three categories: User (owner), Group, and Other (everyone else). Each category has three basic permissions: Read (r, value 4), Write (w, value 2), and Execute (x, value 1).
`chmod 755` sets the permissions to:
- User: 7 (4+2+1 = Read, Write, Execute)
- Group: 5 (4+1 = Read, Execute)
- Other: 5 (4+1 = Read, Execute)
In symbolic notation, this is equivalent to `chmod u=rwx,go=rx` and is displayed in directory listings as `rwxr-xr-x`.
The SetUID (SUID) bit is a special permission that allows an executable file to run with the privileges of the file's owner, rather than the privileges of the user who launched it. It is represented by an `s` in the user execute position (e.g., `rwsr-xr-x`). It is dangerous because if a binary owned by root has the SUID bit set, any user running it effectively becomes root for the duration of that process. If the SUID binary contains a security vulnerability (like a buffer overflow or shell injection flaw), a standard user could exploit it to execute arbitrary commands as root, leading to total system compromise.

## 4. What is umask? How does it determine default file and directory permissions? If umask is 027, what permissions do new files and directories get?

The `umask` (user file-creation mode mask) is a setting that controls the default permissions assigned to newly created files and directories. It works by "masking out" or subtracting specific permission bits from a base starting permission.
The base permission for new directories is `777` (`rwxrwxrwx`), and for new files, it is `666` (`rw-rw-rw-`), as files are not created executable by default for security reasons. The umask value is subtracted from these base permissions to determine the final permissions.
If the umask is set to `027`:
- **For directories**: Base `777` minus `027` equals `750`. The permissions will be `rwxr-x---`. The owner has full access, the group can read and enter the directory, and others have no access whatsoever.
- **For files**: Base `666` minus `027` equals `640`. (Note: you do not carry over subtraction; it's a bitwise NOT AND operation. Masking out the write bit (2) from write (2) leaves 0. Masking out all bits (7) from rw (6) leaves 0). The permissions will be `rw-r-----`. The owner can read and write, the group can read, and others have no access.
This umask (`027`) is commonly used in secure environments to restrict access to the creator and their immediate group, completely locking out the rest of the system.

## 5. Explain the difference between find and locate. When would you use each? Show a find command that deletes files older than 30 days.

The `find` and `locate` commands are both used to search for files, but they operate fundamentally differently.
`find` searches the live filesystem in real-time by traversing directory structures starting from a specified path. It evaluates every file against a set of complex criteria (name, size, modification time, permissions, owner). Because it reads the actual disk, it is always perfectly accurate and up-to-date, but it can be slow on large filesystems.
`locate` searches a prebuilt index database (usually generated daily by a cron job running `updatedb`). It only searches by file path/name. It is incredibly fast, returning results almost instantly, but it is not real-time. Files created after the last database update will not be found, and files deleted recently might still show up in the results.
You use `locate` for quick, general queries when you know roughly what a file is called but forget where it is (e.g., `locate httpd.conf`). You use `find` when you need precision, when searching for files based on metadata (like size or age), or when you want to execute actions on the results.
A `find` command to delete files older than 30 days:
`find /var/log/app -type f -mtime +30 -exec rm -f {} \;`
Alternatively, the more efficient version using the built-in delete action:
`find /var/log/app -type f -mtime +30 -delete`

## 6. What does tail -F do that tail -f does not? Why does the distinction matter for log files that get rotated?

Both `tail -f` and `tail -F` are used to output the last lines of a file and continuously monitor it, printing new data as it is appended. The critical difference lies in how they track the file when its underlying inode or metadata changes.
`tail -f` (lowercase f) tracks the file by its file descriptor (inode). If the file is renamed, deleted, or replaced while `tail` is running, `tail -f` will continue to track the original inode. It will completely ignore any new file created with the original name.
`tail -F` (uppercase F, which implies `--follow=name --retry`) tracks the file by its name rather than its inode. It periodically checks if a new file with the monitored name has been created. If the original file disappears or is replaced, `tail -F` will automatically detach from the old inode, open the new file, and continue printing new lines.
This distinction is absolutely vital for monitoring system logs. Log rotation utilities (like `logrotate`) manage disk space by taking the active log (e.g., `syslog`), renaming it (to `syslog.1`), and creating a brand new, empty `syslog` file for the daemon to write to. If you are using `tail -f syslog`, you will silently stop receiving updates because you are now tailing the rotated, inactive file (`syslog.1`). By using `tail -F syslog`, the command detects the rotation, switches to the newly created `syslog` file, and seamlessly continues displaying incoming log entries.

## 7. How do you find the 10 largest directories in /var? Write the exact command pipeline.

Finding the largest directories in a specific location requires estimating space usage, sorting the output numerically, and extracting the top results. The standard approach utilizes a pipeline of `du`, `sort`, and `head`.
To find the 10 largest directories in `/var`, you would run the following command pipeline:
`du -h /var 2>/dev/null | sort -hr | head -n 10`
Here is the breakdown of what each component does:
- `du -h /var`: The Disk Usage command estimates file space usage. The `-h` flag makes the output human-readable (e.g., 1K, 234M, 2G). The `2>/dev/null` redirects standard error to the bit bucket, suppressing "Permission denied" messages that occur when attempting to read directories restricted to root.
- `sort -hr`: The sort command orders the output. The `-h` flag tells it to sort based on human-readable numbers (so 2G is correctly placed above 500M), and the `-r` flag reverses the sort, putting the largest values at the very top.
- `head -n 10`: The head command simply takes the first 10 lines of the sorted output, providing the top 10 largest directories.
An alternative, slightly different approach that limits the depth to only immediate subdirectories in `/var` is:
`du -sh /var/* 2>/dev/null | sort -hr | head -n 10`

## 8. What is the sticky bit? On which directory is it commonly set by default and why?

The sticky bit is a special permission bit on Linux directories that enforces a strict deletion policy. When the sticky bit is applied to a directory, it restricts the ability to delete or rename files within that directory. Specifically, a user can only delete or rename a file if they are the owner of the file, the owner of the directory itself, or the root user.
The sticky bit is represented by the letter `t` in the executable position for "others" in symbolic permissions (e.g., `rwxrwxrwt`), or by adding a `1` to the thousands position in octal notation (e.g., `1777`).
The most common and critical directory that has the sticky bit set by default is `/tmp`. The `/tmp` directory is designed to be a scratch space where any user or application on the system can write temporary files, meaning its base permissions must be world-writable (`chmod 777 /tmp`).
Without the sticky bit, the world-writable permissions would allow any user to delete any other user's files. For example, User A could maliciously or accidentally delete temporary socket files owned by User B or a critical system service. By setting the sticky bit (`chmod 1777 /tmp`), the system ensures that while everyone can write to `/tmp`, Alice can only delete Alice's files, and Bob can only delete Bob's files, providing essential isolation in a shared environment.

## 9. Explain the difference between cp -a and cp -r. What additional attributes does -a preserve?

Both the `cp -a` and `cp -r` (or `-R`) commands are used to copy directories recursively, copying a directory and all of its contents, subdirectories, and files to a new location. However, they handle file attributes and metadata very differently.
`cp -r` is a standard recursive copy. It reads the data from the source files and creates entirely new files at the destination. The newly created files will be owned by the user executing the `cp` command, and their timestamps (creation/modification) will be set to the exact moment the copy occurred. Symbolic links are generally dereferenced, meaning the actual file data they point to is copied, rather than the link itself.
`cp -a` stands for "archive" mode. It is essentially equivalent to `cp -dR --preserve=all`. The goal of `cp -a` is to create an exact, faithful replica of the source hierarchy.
The additional attributes preserved by `cp -a` include:
- **Ownership**: The user (UID) and group (GID) of the files are preserved (assuming the executing user has root privileges to change ownership).
- **Timestamps**: The original modification time (mtime) and access time (atime) are retained, not updated to the current time.
- **Permissions**: Exact standard permissions are maintained.
- **Links**: Symbolic links are copied as symbolic links, not followed/dereferenced. Hard link structures between copied files are also maintained.
- **Contexts**: SELinux security contexts and extended attributes (xattrs) are preserved where possible. You use `cp -a` for system backups and migrations where metadata integrity is paramount.

## 10. What are /dev/null, /dev/zero, and /dev/random? Give a practical use case for each.

These are special character device files in the Linux virtual filesystem that provide unique input/output behaviors.
- `/dev/null`: Known as the "bit bucket" or "black hole." Any data written to `/dev/null` is immediately discarded by the system, and reading from it immediately returns an End of File (EOF) character.
  - **Use Case**: Suppressing unwanted output from a command. For instance, running a script silently in a cron job by redirecting standard output and error: `./script.sh > /dev/null 2>&1`.
- `/dev/zero`: A device that produces an infinite stream of null characters (bytes with the value zero, `0x00`) when read. Writes to it are discarded.
  - **Use Case**: Creating a large, empty file of a specific size, often used as a loopback filesystem or swap file. Example using `dd` to create a 1GB file filled with zeros: `dd if=/dev/zero of=swapfile bs=1M count=1024`. It is also used to securely wipe disks by writing zeros over all sectors.
- `/dev/random`: A cryptographically secure pseudo-random number generator (CSPRNG). It gathers environmental noise from device drivers (keyboard timing, mouse movements, disk latency) into an entropy pool to generate highly unpredictable random bits.
  - **Use Case**: Generating cryptographic keys, certificates, or secure passwords. Example: generating a 32-character random alphanumeric password: `tr -dc A-Za-z0-9 < /dev/random | head -c 32`. (Note: modern Linux systems often prefer `/dev/urandom` for non-blocking behavior, but `/dev/random` provides the highest quality entropy).

## 11. How do you recursively change all files in a directory to 644 permissions and all directories to 755, using a single find command (not chmod -R)?

Using `chmod -R 755 /path` is dangerous and incorrect because it makes all files executable, not just directories. To apply different permissions to files and directories securely, you must use the `find` command to filter by file type and apply `chmod` selectively.
You can achieve this in a single `find` command by using compound expressions and the `-exec` action. The exact command is:
`find /path/to/directory -type d -exec chmod 755 {} + -o -type f -exec chmod 644 {} +`
Here is a breakdown of how this complex command operates:
- `find /path/to/directory`: Starts the search at the specified directory path.
- `-type d`: Filters the search to match only directories.
- `-exec chmod 755 {} +`: For all matches of the preceding filter (directories), execute `chmod 755`. The `+` terminator is crucial; it appends multiple directory paths to a single `chmod` execution, making it incredibly fast compared to using `\;` (which runs `chmod` once per directory).
- `-o`: The logical OR operator. If the first part of the expression (is it a directory?) evaluates to false, it moves to the second part.
- `-type f`: Filters to match only regular files.
- `-exec chmod 644 {} +`: For all file matches, execute `chmod 644`, again using `+` for batch efficiency.
This single traversal of the directory tree correctly applies secure baseline permissions to the entire hierarchy.

## 12. What is lsblk output telling you? How do you identify which partition is mounted as root?

The `lsblk` command (List Block Devices) reads the `sysfs` virtual filesystem and `udev` databases to gather information about all available or specified block devices (hard drives, SSDs, USB drives, loop devices, and LVM logical volumes). It formats this data into a highly readable, tree-like structure.
When you run `lsblk`, the output typically shows several columns:
- **NAME**: The device name (e.g., `sda` for the first SATA drive, `nvme0n1` for an NVMe drive) and its partitions (`sda1`, `sda2`). The tree structure visually indicates parent-child relationships (a partition under a disk).
- **MAJ:MIN**: The major and minor device numbers used by the kernel to identify the driver and specific device instance.
- **RM**: Removable device flag (1 if removable like a USB, 0 if fixed).
- **SIZE**: The total capacity of the device or partition.
- **RO**: Read-only flag (1 if read-only, 0 if writable).
- **TYPE**: Identifies if the block is a `disk`, a `part` (partition), an `lvm` volume, a `loop` device, or a `crypt` device.
- **MOUNTPOINT**: Shows exactly where in the Linux filesystem hierarchy the device is currently mounted.
To identify which partition is mounted as the root filesystem, you simply look at the **MOUNTPOINT** column. Scan down the column until you find a single forward slash (`/`). The corresponding device or partition on that row (e.g., `sda2` or a specific LVM volume like `ubuntu-vg-ubuntu-lv`) is the root filesystem where the core operating system is installed and running.

## 13. How do you view a file without loading it entirely into memory? When is less preferable to cat?

To view a file without loading the entire contents into system memory, you use a pager utility like `less`.
The `cat` (concatenate) command is designed to read the entire file sequentially and dump it immediately to the standard output (the terminal). If you use `cat` on a 10-gigabyte log file, it will attempt to read all 10 gigabytes from disk and blast it onto your screen, flooding your terminal buffer, consuming CPU and memory, and making it impossible to read the beginning of the file.
The `less` command is a sophisticated pager that solves this problem. It only reads the specific portion of the file required to fill your terminal screen. As you scroll down (using arrow keys or Page Down), `less` dynamically reads the next chunk from the disk. This makes it capable of instantly opening files of virtually unlimited size with minimal memory overhead.
`less` is preferable to `cat` in almost all interactive scenarios involving files larger than a few dozen lines. Specific advantages include:
- **Instant Opening**: Immediate access to massive files without waiting for the entire file to read.
- **Search Capability**: You can search forward by typing `/pattern` and backward using `?pattern`, which `cat` cannot do on its own.
- **Navigation**: You can scroll backward as well as forward. (The older `more` utility only allowed forward scrolling).
- **Live Monitoring**: Using Shift+F in `less` enables "follow" mode, mimicking the behavior of `tail -f`, allowing you to watch logs live and exit back to normal viewing mode seamlessly.

## 14. Explain the Linux permission model for a file with permissions rwsr-xr-x owned by root. What happens when a regular user runs this file?

The permission string `rwsr-xr-x` reveals a specific and potentially high-risk configuration. Let's break it down into the standard triad:
- **User (Owner - root)**: `rws` -> Read, Write, and the SetUID (s) bit is active (which implies Execute).
- **Group**: `r-x` -> Read and Execute.
- **Other**: `r-x` -> Read and Execute.
Normally, when a regular user (let's say 'alice') executes a program, the program runs as a process with Alice's User ID (UID) and her associated privileges. The program can only access files and resources that Alice is permitted to access.
However, the presence of the `s` in the owner's execute position indicates the **SetUID (SUID)** bit is set. Because the owner of this file is `root`, the SUID bit fundamentally changes the execution context.
When Alice runs this file, the operating system kernel temporarily elevates the privileges of that process to match the file's owner. The program executes with an Effective User ID (EUID) of 0 (`root`), rather than Alice's UID.
This means the program can read, write, and execute anything that root can, regardless of Alice's actual privileges. This mechanism is necessary for certain core utilities; for example, the `/usr/bin/passwd` command has these exact permissions, allowing standard users to update their passwords by writing to the highly restricted `/etc/shadow` file. However, if a custom or vulnerable script is given these permissions, a regular user could exploit it to execute arbitrary commands as root, bypassing all security controls.

## 15. What is the difference between /tmp and /var/tmp? How does systemd manage their cleanup?

Both `/tmp` and `/var/tmp` are designated directories for storing temporary files created by applications and users, but they serve different operational purposes and have distinct retention policies.
- `/tmp`: This directory is intended for highly ephemeral, short-lived temporary files. System components and applications use it for data that is only needed for the immediate session or process execution. Crucially, `/tmp` is expected to be wiped clean every time the system reboots. On many modern Linux distributions, `/tmp` is not even a physical directory on the hard drive; it is mounted as a `tmpfs` (a RAM disk). This makes access incredibly fast but guarantees data volatility.
- `/var/tmp`: This directory is intended for temporary files that need to persist across system reboots. Applications use `/var/tmp` for larger temporary data sets, cached states, or recovery files that are expensive to regenerate and should survive a crash or a power cycle. It is backed by physical disk storage.
Modern Linux systems rely on `systemd` (specifically the `systemd-tmpfiles` service) to manage the lifecycle and cleanup of these directories based on configured rules in `/usr/lib/tmpfiles.d/`.
- For `/tmp`, systemd is typically configured to delete files and directories that have not been accessed, modified, or changed in the last 10 days, in addition to the automatic wipe on boot.
- For `/var/tmp`, the retention policy is much longer. Systemd is generally configured to delete files only after they have been untouched for 30 days. This automated housekeeping prevents temporary files from indefinitely consuming disk space while respecting the persistence requirements of `/var/tmp`.

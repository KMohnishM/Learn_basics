# Module 7: File Systems

---

## 1. What is a File?

From the user's perspective: a named collection of related information stored on disk.

From the OS's perspective: a logical storage unit — a sequence of bytes with associated metadata. The OS abstracts away the physical storage details (which disk sectors, which blocks) and presents a uniform interface.

**File attributes** (stored in directory entry or inode):
- **Name**: Human-readable identifier (the only attribute stored in human-readable form)
- **Identifier**: Unique number (inode number in Unix)
- **Type**: Inferred from content or extension (`.txt`, `.exe`), or explicit type field
- **Location**: Pointer to the file's data on disk
- **Size**: Current size in bytes
- **Protection**: Access control (who can read/write/execute)
- **Timestamps**: Creation, last modified, last accessed
- **Owner/Group**: For permission checking

---

## 2. File Types

Unix represents everything as a file:

| Type | Symbol (ls) | Description |
|------|-------------|-------------|
| Regular file | `-` | Contains data (text, binary) |
| Directory | `d` | Lists files (special regular file) |
| Symbolic link | `l` | Pointer to another file |
| Block device | `b` | Disk, USB — block-sized I/O |
| Character device | `c` | Terminal, serial port — byte-at-a-time I/O |
| FIFO (named pipe) | `p` | Inter-process communication |
| Socket | `s` | Network / Unix domain socket endpoint |

---

## 3. File Operations

The OS provides a system call interface for file operations. The kernel maintains an **open file table** for each process and a global open file table.

**Key operations:**
- `create`: Allocate inode, add directory entry.
- `open`: Find the file's inode, create an entry in the process's file descriptor table, return a file descriptor (integer).
- `read(fd, buffer, n)`: Read n bytes from current position into buffer, advance position.
- `write(fd, buffer, n)`: Write n bytes from buffer, advance position, mark inode dirty.
- `seek(fd, offset)`: Move the current file position (without I/O). Enables random access.
- `close(fd)`: Remove from process's file descriptor table. Decrement open count. If count reaches 0, release resources.
- `delete`: Remove directory entry, decrement inode link count. If link count = 0, free inode and data blocks.
- `truncate`: Remove file content, set size to 0 (or specified size), keep inode and directory entry.

**File descriptor table**: Per-process table of open files. Inherited by children via `fork()`. Entries 0, 1, 2 are stdin, stdout, stderr by convention.

---

## 4. File Access Methods

**Sequential Access**: Read/write from current position, advance sequentially. Like reading a tape. Works for most processing (logs, data streams).
```
read next
write next
reset (go to beginning)
```

**Direct (Random) Access**: Specify the record/block number to read/write. `seek(position)` then `read/write`. Required for databases.
```
read n        (read block n)
write n
seek n
```

**Indexed Access**: An index file lists keys and their positions. To find a record, search the index (fast, fits in memory), then do a direct access to the actual data file. Used in database index structures (B-trees are a form of this).

---

## 5. Directory Structure

Directories organize files. They are implemented as special files that contain a mapping of filenames to file identifiers.

### Single-Level Directory
One directory for all files in the entire system. Simplest.
**Problem**: Name collision — two users can't have files with the same name.

### Two-Level Directory
User File Directory (UFD) per user. Master File Directory (MFD) maps usernames to UFDs.
**Problem**: No subdirectories — all of a user's files still in one flat namespace.

### Tree-Structured Directory
The modern hierarchical structure. Directories can contain files and other directories. Each process has a **current working directory** (CWD). Paths:
- **Absolute**: Start from root (`/home/user/documents/file.txt`)
- **Relative**: Start from CWD (`documents/file.txt`)
- `.` = current directory, `..` = parent directory

**Problem**: Cannot easily share files (a file can only be in one directory at a time — there is only one "path" to it).

### Acyclic Graph Directory
Allows sharing: a directory entry can point to a file (or subdirectory) that also appears in another directory.

**Hard link**: Two directory entries pointing to the same inode. The inode has a **link count**. When the link count drops to 0, the inode and data are freed.
```
ln /home/user/file.txt /shared/file.txt
# Both entries point to the same inode
# Deleting one doesn't delete the data
```

**Symbolic (soft) link**: A new file whose content is the path of the target. If the target is deleted → dangling pointer (the symlink points to nothing).
```
ln -s /home/user/file.txt /shared/link.txt
# /shared/link.txt is a new inode containing the string "/home/user/file.txt"
```

**Problem with acyclic graph**: How do we ensure we don't create cycles (especially with directory links)? Hard links to directories are generally disallowed. Symbolic links to directories can create cycles.

### General Graph Directory
Allows cycles. Requires **garbage collection** to detect and free unreachable files. Traversal algorithms must handle cycles (visited set). Not used in practice — OSes prevent directory hard links.

---

## 6. Hard Links vs Symbolic Links

| Property | Hard Link | Symbolic Link |
|----------|-----------|---------------|
| Points to | Inode number | File path (string) |
| File deletion | Data survives until all hard links removed | Target can be deleted (dangling link) |
| Cross-filesystem | ❌ (inodes are per-filesystem) | ✅ |
| Directory links | ❌ (prevented to avoid cycles) | ✅ (allowed, with care) |
| Shows up as | Same as original | `lrwxrwxrwx` in ls |
| Link count effect | Increments inode link count | No effect on target's link count |
| After target moved | Still works (inode unchanged) | Breaks (path no longer valid) |

---

## 7. File System Implementation — On-Disk Layout

A disk partition formatted with a filesystem has this general layout:

```
┌──────────────┬─────────────┬──────────────┬──────────────────────┐
│  Boot Block  │  Superblock │  Inode Table │     Data Blocks      │
└──────────────┴─────────────┴──────────────┴──────────────────────┘
```

**Boot Block** (Block 0): Contains the boot loader (MBR on legacy systems). Every filesystem has this even if not bootable (wasted space otherwise).

**Superblock**: Critical metadata about the entire filesystem:
- Magic number (filesystem type identifier)
- Total blocks
- Number of free blocks and free inodes
- Block size
- Inode count
- Mount state (was it cleanly unmounted?)

**Inode Table**: Fixed-size array of inodes, one per file. The inode number IS the index into this table.

**Data Blocks**: The actual file content and directory content.

---

## 8. Inode Structure — Unix/Linux Deep Dive

An **inode** (index node) stores all metadata about a file EXCEPT the filename. The filename → inode mapping is stored in the directory.

**Inode fields:**
- File type (regular, directory, symlink, device, ...)
- Permissions (rwxrwxrwx + setuid, setgid, sticky)
- Link count (number of hard links)
- Owner UID, group GID
- File size (bytes)
- Timestamps: atime (last access), mtime (last modification), ctime (last inode change)
- Number of disk blocks used
- **Block pointers** (the key data structure)

### inode Block Pointers

A Unix inode has a fixed number of block pointer fields (originally 15 in traditional Unix):

```
Direct Pointers      [0-11]  : 12 pointers, each pointing directly to a data block
Single Indirect      [12]    : Points to a block of pointers (to data blocks)
Double Indirect      [13]    : Points to a block of pointers to blocks of pointers
Triple Indirect      [14]    : Points to a block → block → block → data
```

**Max file size calculation** (assuming 4KB blocks, 4-byte pointers):

- Pointers per indirect block = 4KB / 4B = **1024**

| Level | Blocks reachable | Size |
|-------|-----------------|------|
| 12 direct | 12 | 48KB |
| Single indirect | 1024 | 4MB |
| Double indirect | 1024² = 1,048,576 | 4GB |
| Triple indirect | 1024³ = 1,073,741,824 | 4TB |
| **Total** | | **~4TB** |

**The clever design**: Most files are small (< 48KB) — only direct pointers are needed (fast, no extra indirection). Large files pay the cost of indirection only when needed.

ext4 on Linux uses **extents** instead (a range of contiguous blocks described by start + length), which is more efficient for large files.

---

## 9. File Allocation Methods

How does the OS store a file's data blocks on disk?

### Contiguous Allocation

Each file occupies a set of contiguous blocks on disk. The directory entry stores: starting block + length.

```
File A: starts at block 5, length 3 → occupies blocks 5, 6, 7
File B: starts at block 10, length 5 → occupies blocks 10-14
```

**Advantages:**
- Simple: `disk_address = start + offset / block_size`
- **Fast sequential access**: Blocks are adjacent on disk → no head movement between blocks.
- **Fast random access**: Block N is at `start + N` → O(1) computation.
- Excellent for read-only storage (CD-ROM, DVD).

**Disadvantages:**
- **External fragmentation**: Over time, as files are created and deleted, holes form. Contiguous space for large files becomes scarce.
- **File size must be known at creation**: How much space to allocate? If a file grows beyond its allocation, it might not have adjacent free blocks.

### Linked Allocation

Each block contains a pointer to the next block. The directory entry stores: first block number.

```
File A: Block 5 → Block 9 → Block 3 → Block 15 → NULL
```

**Advantages:**
- No external fragmentation (any free block can be the next block).
- File can grow freely (just append a block anywhere).
- No wasted space due to preallocated size.

**Disadvantages:**
- **Random access is O(n)**: To access block n, must follow n pointers from the beginning.
- **Reliability**: A single corrupted pointer loses the rest of the file.
- **Pointer overhead**: Each block loses a few bytes to the next-block pointer.

### FAT (File Allocation Table) — Improved Linked Allocation

FAT is a clever variation: move all the pointers OUT of the data blocks into a table in memory.

```
FAT Table (indexed by block number):
  Block 5:  → 9    (File A: first block=5)
  Block 9:  → 3
  Block 3:  → 15
  Block 15: → EOF

  Block 7:  → 12   (File B: first block=7)
  Block 12: → EOF
```

**Advantages over linked allocation:**
- FAT is cached in memory → random access is possible without disk seeks (follow the chain in RAM).
- Pointer corruption is less likely (FAT is separate, often duplicated).

**Disadvantages:**
- FAT can be large: FAT32 with 32GB disk and 4KB clusters → 8M entries × 4 bytes = 32MB FAT. Must fit in memory.
- Fragmentation still occurs (non-contiguous blocks).

FAT is used on USB drives, memory cards, and embedded systems. FAT16, FAT32, exFAT are all variations.

### Indexed Allocation (Unix inode style)

Each file has an **index block** containing all its block pointers. The directory entry points to the index block.

**Advantages:**
- Random access is O(1) for direct blocks, O(2) for single indirect, etc.
- No external fragmentation.
- File can grow dynamically.

**Disadvantages:**
- Small files waste space (index block allocated even for a 1-byte file).
- Very large files need multiple levels of indirection.

This is essentially what Unix inodes implement, with the optimization of direct pointers for small files.

---

## 10. Free Space Management

The OS must track which blocks are free.

### Bit Vector (Bitmap)

One bit per block: 0 = free, 1 = allocated. Stored on disk, often cached in memory.

```
Block 0: 1 (used)
Block 1: 0 (free)  ← allocate this
Block 2: 1 (used)
...
```

**Advantages:**
- Simple to find a free block (find a 0 bit).
- On modern CPUs with bit-manipulation instructions (e.g., `BSF` — Bit Scan Forward), scanning is fast.
- Good locality: the bitmap for contiguous free blocks is also contiguous → can find contiguous blocks easily.

**Disadvantages:**
- Must keep entire bitmap in memory for efficiency. For a 1TB disk with 4KB blocks: 1TB/4KB = 256M blocks → 256M bits = **32MB bitmap**.

### Linked List of Free Blocks

Free blocks linked together via pointers (similar to FAT chains). Head pointer stored in superblock.

**Advantages:** No extra space for bitmap — uses free blocks themselves.

**Disadvantages:** Random access O(n), poor performance (must read each block to find the next free block). Not practical.

### Grouping

Store addresses of n free blocks in the first free block. The last of these n addresses points to another block containing n more free addresses.

Improvement over linked list: can find n free blocks with fewer disk reads.

### Counting

Since contiguous free blocks often appear together (after deletion of a large file), store `(starting_block, count)` pairs. More efficient when free space is in contiguous runs.

---

## 11. Virtual File System (VFS)

Linux supports dozens of filesystems: ext4, NTFS, FAT32, Btrfs, NFS, procfs, tmpfs, etc. Without VFS, each application would need to know which filesystem type it's talking to.

**VFS** provides an abstract layer that presents a uniform interface to applications, regardless of the underlying filesystem:

```
User application
     ↓  open(), read(), write(), close() syscalls
   VFS layer (kernel)
     ↓         ↓         ↓
   ext4       NTFS      NFS
  driver     driver    driver
     ↓         ↓         ↓
  local      local     remote
  disk       disk       server
```

**VFS objects (Linux):**
- **superblock object**: Represents a mounted filesystem instance. Operations: `read_super`, `write_super`, `put_super`.
- **inode object**: Represents an individual file. Operations: `create`, `lookup`, `link`, `unlink`, `mkdir`, `rmdir`, `rename`.
- **dentry (directory entry) object**: Represents a path component (directory entry). Cached in the **dentry cache** (dcache) for fast path lookups.
- **file object**: Represents an open file (per open-fd, not per inode). Operations: `read`, `write`, `seek`, `mmap`, `release`.

Each filesystem driver implements the VFS interface (fills in function pointers). The VFS calls the driver's functions without knowing which filesystem type it is.

---

## 12. Journaling Filesystems

**Problem**: Disk writes are not atomic. If power fails mid-write (e.g., while writing inode + data block + directory entry), the filesystem is in an inconsistent state:
- Half-written inode (shows file as larger than its data)
- Orphaned blocks (data written but inode not updated to point to them)
- Directory entry pointing to a freed inode

Traditional fix (`fsck` — filesystem check): Scan the entire filesystem on next boot. For a 1TB filesystem, `fsck` can take 30+ minutes. **Unacceptable**.

**Journaling** (write-ahead logging):
Before modifying the filesystem, the OS writes the intended operations to a **journal** (a circular log on disk). Once the journal entry is complete (committed), the actual filesystem modifications are made.

**Recovery**: If power fails:
- Journal entry NOT committed → incomplete operation. Ignore it (original state preserved).
- Journal entry committed, but modifications not applied → **replay** the journal entry. Deterministic and fast.
- Journal entry committed AND modifications applied → **complete** (journal entry discarded).

**Journal modes (ext4):**

| Mode | What's journaled | Data safety | Speed |
|------|-----------------|-------------|-------|
| **data=journal** | Both data and metadata | Best | Slowest |
| **data=ordered** | Metadata only; data written before metadata | Good (default) | Fast |
| **data=writeback** | Metadata only; data may be written after metadata | Risk of stale data | Fastest |

`data=ordered` (ext4 default) guarantees that data blocks are written to disk before the metadata pointing to them is committed to the journal. This prevents the case where a journal replay writes metadata pointing to garbage data blocks.

**fsck with journaling**: If the journal is clean (committed), just replay it. Takes seconds, not minutes.

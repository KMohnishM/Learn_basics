# Q&A — File Systems

---

## 🟢 Easy

**Q1. What is an inode and what does it contain?**

An **inode** (index node) is a Unix/Linux data structure that stores all metadata about a file — except its name. The name-to-inode mapping is stored in the directory.

An inode contains: file type, permissions (rwxrwxrwx), owner UID + group GID, file size, link count (number of hard links), timestamps (atime, mtime, ctime), number of disk blocks used, and **block pointers** (12 direct, 1 single-indirect, 1 double-indirect, 1 triple-indirect — pointing to the actual data blocks).

---

**Q2. What is the difference between a hard link and a symbolic link?**

**Hard link**: A second directory entry pointing to the same inode. Both names refer to the same file. Deleting one doesn't delete the data — data is freed only when the link count (all directory entries) drops to 0. Cannot cross filesystem boundaries (inodes are per-filesystem). Cannot hard-link directories.

**Symbolic link**: A separate file whose content is a path string pointing to the target. If the target is deleted, the symlink becomes a dangling pointer (points to nothing). Can cross filesystem boundaries. Can link to directories. Shows as `l` in `ls -l`.

---

**Q3. What are the three main file allocation methods?**

1. **Contiguous**: File occupies consecutive disk blocks. Fast sequential and random access. External fragmentation; file size must be known upfront.

2. **Linked**: Each block contains a pointer to the next. No external fragmentation. Sequential access only — random access is O(n). FAT improves this by putting the pointer chain in a table in memory.

3. **Indexed (inode)**: An index block (or inode) holds all block pointers. Random access O(1) for small files. No external fragmentation. Multi-level indirection for large files.

---

**Q4. What is a journaling filesystem? Why was it needed?**

A journaling filesystem writes intended changes to a **journal** (write-ahead log) before making the actual changes. On crash, the OS replays the committed journal entries to restore consistency.

It was needed because without journaling, a power failure mid-write leaves the filesystem inconsistent (half-written metadata). Recovery required running `fsck` — a full disk scan taking minutes or hours on large disks. With journaling, recovery takes seconds (just replay the log).

---

**Q5. What information is stored in a directory entry?**

In traditional Unix: just the **filename** and the **inode number**.

All other metadata (permissions, size, owner, timestamps, block locations) is in the inode. Modern filesystems (ext4) may cache some metadata in the directory entry for performance, but the authoritative copy is always in the inode.

---

## 🟡 Medium

**Q6. Calculate the maximum file size for a filesystem with 4KB blocks, 4-byte pointers, and a traditional Unix inode (12 direct, 1 single, 1 double, 1 triple indirect).**

Pointers per block = 4096 / 4 = **1024**.

| Pointer type | Blocks accessible | Size |
|-------------|-------------------|------|
| 12 direct | 12 | 12 × 4KB = **48KB** |
| 1 single indirect | 1024 | 1024 × 4KB = **4MB** |
| 1 double indirect | 1024² = 1,048,576 | 1M × 4KB = **4GB** |
| 1 triple indirect | 1024³ = 1,073,741,824 | 1G × 4KB = **4TB** |
| **Total** | | **≈ 4TB + 4GB + 4MB + 48KB** |

Effective maximum ≈ **4TB** (triple indirect dominates).

---

**Q7. Compare contiguous, linked, and indexed allocation for sequential access, random access, and fragmentation.**

| Criteria | Contiguous | Linked | Indexed (inode) |
|----------|-----------|--------|-----------------|
| **Sequential access** | ⭐ Excellent (adjacent blocks) | ⭐ Good (follow pointers) | ⭐ Good |
| **Random access (block n)** | ⭐ O(1) — start + n | ❌ O(n) — follow n pointers | ⭐ O(1) for small files |
| **External fragmentation** | ❌ Yes | ✅ None | ✅ None |
| **File size known upfront?** | ❌ Required | ✅ Not required | ✅ Not required |
| **Overhead per block** | None | Pointer (4-8 bytes) | Index block |
| **Reliability** | High | Low (one bad pointer = lost rest) | High |
| **Used in** | CD-ROM, old DOS | FAT filesystems | Unix/Linux (ext2/3/4) |

---

**Q8. What is the VFS (Virtual File System) and how does it work?**

VFS is an abstraction layer in the kernel that provides a uniform system call interface (`open`, `read`, `write`, `close`) for all filesystem types — ext4, FAT32, NTFS, NFS, procfs, tmpfs, etc.

How it works:
1. Each filesystem driver registers itself with VFS by providing function pointers for inode operations, file operations, and superblock operations.
2. When a user calls `read(fd, ...)`, VFS looks up the file's inode via the dentry cache, then calls `inode->i_fop->read(...)` — which the specific filesystem driver implemented.
3. The driver performs the actual disk I/O (or network I/O for NFS, or memory read for tmpfs).

Key VFS objects: superblock (mounted filesystem), inode (file metadata), dentry (pathname component, cached for fast lookup), file (per-open-fd state).

---

**Q9. What is the dentry cache and why is it important?**

The **dentry cache** (dcache) is an in-memory cache of directory entries (name → inode mappings). Path resolution (`/home/user/documents/file.txt`) requires looking up each path component in a directory — 4 directory reads without caching.

With dcache: if `/home`, `/home/user`, `/home/user/documents` have been recently accessed, all three are in the dcache. Only the final file lookup might need a disk read.

The dcache is a global LRU cache. On a busy server, most pathname lookups are entirely in memory (hot cache). This is one of the biggest performance wins in Linux VFS.

---

**Q10. What is the difference between `data=journal`, `data=ordered`, and `data=writeback` in ext4?**

These are ext4 journaling modes controlling what is written to the journal:

**`data=journal`**: Both data blocks and metadata are written to the journal before being committed to disk. Safest — zero data loss even if power fails mid-write. Slowest — all writes go to journal first.

**`data=ordered`** (default): Only metadata is journaled. But data blocks are guaranteed to be written to disk before the corresponding metadata is committed to the journal. If power fails, you might lose the latest data, but you won't see metadata pointing to garbage data blocks.

**`data=writeback`**: Only metadata is journaled. Data blocks may be written after metadata. Fastest, but after a crash, you might see metadata pointing to stale data (old or garbage content). Risk of showing old file contents for recently-written data.

---

## 🔴 Hard

**Q11. A file system has 1TB of storage, 4KB block size. Calculate the size of a bitmap for free space management. Is keeping it in memory practical?**

Total blocks = 1TB / 4KB = (2^40) / (2^12) = **2^28 = 268,435,456 blocks**.

Bitmap size = 268,435,456 bits / 8 = **33,554,432 bytes = 32MB**.

32MB for the bitmap — Yes, keeping it in memory is practical for a desktop or server (modern systems have gigabytes of RAM). Linux keeps the block bitmap in memory (as part of ext4's block group descriptors and cached buffer cache).

However, for very large storage systems (100TB NAS), the bitmap becomes 3.2GB — too large to keep fully in RAM. Enterprise filesystems use more sophisticated structures (b-trees of extents, as in Btrfs and XFS) that don't require a full in-memory bitmap.

---

**Q12. How does the OS handle a `write()` call to completion in ext4 with `data=ordered` journaling? Walk through every step.**

Application calls `write(fd, buffer, 10240)` (10KB write to a file):

**1. VFS layer**:
- Looks up the file's inode via fd → file table → inode.
- Calls ext4's `write` implementation.

**2. Page Cache**:
- Linux doesn't write directly to disk. It writes to the **page cache** (kernel memory pages backing the file).
- The write updates the appropriate pages in the page cache, marking them **dirty**.
- Returns to the application immediately (write returns to user space). The data is NOT yet on disk.

**3. Background writeback (pdflush/writeback threads)**:
- Kernel threads periodically write dirty pages to disk (or `fsync()` forces immediate write).
- Before writing metadata (inode + block group bitmap + possibly a new block allocation), ext4 must write data blocks first (`data=ordered`).

**4. Data blocks to disk**:
- The dirty data pages are submitted to the block device layer as block I/O requests.
- The scheduler (I/O scheduler) may reorder/merge these requests for efficiency.
- Disk controller DMA transfers data to disk platters.
- Interrupt fires when complete.

**5. Journal write (metadata)**:
- After data blocks are on disk, ext4 writes a **journal transaction** containing: updated inode (new size, new mtime, possibly new block pointer), updated block group bitmap (newly allocated blocks marked used).
- The journal transaction is committed (a commit block is written to the journal).

**6. Checkpoint**:
- Eventually, the journal transaction is checkpointed: the actual filesystem locations (inode table on disk, block group descriptor on disk) are updated to match the journal.
- The journal transaction is freed (space in the circular journal log reused).

---

**Q13. What happens to inode link count in each scenario below? Starting link count = 1.**

**a) User runs `ln file.txt link1.txt` (hard link)**:
Link count becomes **2**. Two directory entries now point to the same inode. Deleting either one decrements count to 1 — data survives.

**b) User runs `ln -s file.txt symlink.txt` (symbolic link)**:
file.txt's link count **stays at 1**. symlink.txt is a new, separate inode with link count 1. The symlink stores the string "file.txt". No change to the original inode's link count.

**c) User runs `mkdir newdir` (creates directory)**:
newdir's link count is **2**: one from the parent directory (the `newdir` entry) and one from `.` (the self-reference inside newdir). The parent directory's link count increases by 1 (because `..` inside newdir points to the parent).

**d) User deletes file.txt when link count is 2**:
Link count becomes **1**. The data blocks and inode are NOT freed — the other hard link still refers to them. The file is only truly deleted (inode and blocks freed) when the last directory entry is removed (link count reaches 0).

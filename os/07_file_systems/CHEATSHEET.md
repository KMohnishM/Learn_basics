# Cheat Sheet — File Systems

## On-Disk Layout
```
┌──────────┬──────────────┬──────────────┬──────────────────────────┐
│Boot Block│  Superblock  │  Inode Table │       Data Blocks        │
└──────────┴──────────────┴──────────────┴──────────────────────────┘

Boot Block:   Boot loader (always present, even on non-bootable FSes)
Superblock:   Total blocks, free count, inode count, block size, magic number
Inode Table:  Fixed array — inode number = index into this table
Data Blocks:  File data + directory contents
```

## Inode Block Pointers (Traditional Unix, 4KB blocks, 4B pointers)
```
12 Direct pointers     → 12 × 4KB = 48KB
1  Single indirect     → 1024 × 4KB = 4MB
1  Double indirect     → 1024² × 4KB = 4GB
1  Triple indirect     → 1024³ × 4KB = 4TB
─────────────────────────────────────────
Total max file size    ≈ 4TB (triple indirect dominates)

Pointers per block = block_size / pointer_size = 4096 / 4 = 1024
```

## Inode Fields
| Field | Description |
|-------|-------------|
| File type | regular/dir/symlink/device/... |
| Permissions | rwxrwxrwx + setuid/setgid/sticky |
| Link count | # of hard links (file freed when = 0) |
| UID / GID | Owner and group |
| Size | File size in bytes |
| atime | Last access time |
| mtime | Last modification time |
| ctime | Last inode change time |
| Blocks | Disk block count |
| Block pointers | 12 direct + 3 indirect levels |

## Hard Link vs Symbolic Link
| | Hard Link | Symbolic Link |
|-|-----------|---------------|
| Points to | Inode number | Path string |
| Link count | Incremented | No change to target |
| Cross-filesystem | ❌ | ✅ |
| Directories | ❌ | ✅ |
| After target deleted | Data survives | Dangling pointer |
| `ls -l` shows | Normal file | `l` type |

## File Allocation Methods
| Method | Random Access | External Frag | Size Known? | Used In |
|--------|:------------:|:-------------:|:-----------:|---------|
| Contiguous | O(1) | ✅ Yes | Required | CD-ROM |
| Linked | O(n) | ❌ No | Not needed | (legacy) |
| FAT (linked+table) | O(n) in RAM | ❌ No | Not needed | USB, SD cards |
| Indexed (inode) | O(1)–O(3) | ❌ No | Not needed | Linux ext2/3/4 |

## Free Space Management
| Method | Pros | Cons |
|--------|------|------|
| Bitmap | Fast contiguous search, simple | Large (32MB per 1TB at 4KB blocks) |
| Linked list | No extra space | Slow (O(n) traversal) |
| Grouping | Better than linked | Still multiple reads |
| Counting | Efficient for contiguous runs | Complex |

## Bitmap Size Formula
```
Blocks = Disk_size / Block_size
Bitmap = Blocks / 8 bytes
Example: 1TB disk, 4KB blocks → 2^28 blocks → 32MB bitmap
```

## VFS Object Hierarchy
```
superblock → represents a mounted filesystem
  └─ inode → represents one file/directory
       └─ dentry → represents one pathname component (cached)
            └─ file → represents one open file descriptor
```

## Directory Structure Types
| Type | Sharing | Subdirs | Problem |
|------|:-------:|:-------:|---------|
| Single-level | ❌ | ❌ | Name collision |
| Two-level | ❌ | ❌ | No subdirs |
| Tree | ❌ | ✅ | Cannot share |
| Acyclic graph | ✅ | ✅ | Dangling ptrs |
| General graph | ✅ | ✅ | Cycles → GC needed |

## Link Count Rules
```
create file         → link count = 1
ln file link        → link count + 1 (hard link)
ln -s file symlink  → link count unchanged (symlink is separate inode)
mkdir newdir        → link count of newdir = 2 (. and parent entry)
                    → parent link count + 1 (because newdir/.. points to parent)
delete directory entry → link count - 1
link count == 0     → inode + data blocks FREED
```

## Journaling Modes (ext4)
| Mode | What journaled | Safe? | Speed |
|------|---------------|-------|-------|
| data=journal | Data + metadata | Best | Slowest |
| data=ordered | Metadata only; data first | Good | Fast (default) |
| data=writeback | Metadata only; data anytime | Risk stale data | Fastest |

## File Types (Unix `ls -l` first char)
```
-  regular file
d  directory
l  symbolic link
b  block device (disk)
c  character device (terminal)
p  named pipe (FIFO)
s  socket
```

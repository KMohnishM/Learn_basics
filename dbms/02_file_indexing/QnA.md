# Q&A — File Structures & Indexing

---

## 🟢 Easy

**Q1. Describe the slotted-page architecture. Why is it used?**

The **slotted-page architecture** is a page layout strategy used to store variable-length records in a page.
- **How it works**:
  - The **page header** is at the beginning of the page.
  - A **slot directory** starts at the top and grows downwards. Each entry (slot) stores a pointer (offset) to the start of the record and the length of the record.
  - The actual **records** are written from the bottom of the page growing upwards.
  - Free space resides in the middle.
- **Why it is used**: It handles variable-length records and deletions cleanly. When a record is deleted, we just mark its slot offset as empty. New records can reuse this space. If fragmentation occurs, records can be shifted around (compacted) within the page without changing their external identifiers (since external pointers refer to the stable slot indices, e.g., `Page_ID:Slot_ID`, not raw offsets).

---

**Q2. Compare Clustered and Unclustered Indexes.**

- **Clustered Index**:
  - The physical order of rows in the data file is the **same** as the logical order of the index.
  - Since physical rows can only be stored in one sort order, a table can have **only one** clustered index.
  - InnoDB automatically clusters tables by the Primary Key.
- **Unclustered Index**:
  - The physical order of data rows is **independent** of the index order.
  - The leaf nodes of the index contain pointers to the actual data rows (or to the primary key values, which are then used to look up rows in the clustered index).
  - A table can have multiple unclustered indexes.

---

**Q3. What is the difference between a dense index and a sparse index?**

- **Dense Index**: An index record is created for **every single search-key value** in the data file.
- **Sparse Index**: Index records are created for only **some** of the search-key values (typically one index record per physical page/block of the data file). The data file must be sorted by the search key for a sparse index to work. Sparse indexes use less memory but take slightly longer to locate records (must find the block pointer, load the block, and scan sequentially within the block).

---

## 🟡 Medium

**Q4. Why are B+ Trees preferred over Binary Search Trees (BSTs) or AVL Trees in database storage engines?**

1. **Disk I/O Minimization (Height)**:
   - Databases store indexes on disk. Every node traversal during search requires reading a disk block.
   - BSTs and AVL trees are binary (fan-out = 2). A database with $10^7$ rows in an AVL tree would have a height of $\approx 24$. This means up to 24 disk reads.
   - B+ Trees have a high fan-out (e.g., $p = 100$ or $200$). A B+ Tree with fan-out 100 needs a height of only $\log_{100}(10^7) \approx 4$. That is only 4 disk reads — a massive performance win.
2. **Cache Coherency / Block Transfer**:
   - A single disk read loads an entire page (e.g., 16KB).
   - In a B+ Tree, a node fits exactly in one page. Loading a node brings dozens of sorted keys into RAM at once. Binary tree nodes are scattered, resulting in poor cache locality and one page load per key.
3. **Efficient Range Scans**:
   - Leaf nodes of a B+ Tree are linked sequentially. Range queries only need to find the first key, then traverse the leaf pointers directly. BSTs require complex tree traversals (in-order) going up and down parent pointers.

---

**Q5. Explain the difference between "copy up" and "push up" during B+ Tree splits.**

During a B+ Tree node split:
- **Copy Up** (Leaf Node Split):
  - When a leaf node overflows and splits, the smallest key of the right-hand child node is **copied** to the parent node.
  - The key **remains** in the leaf node because leaf nodes must contain the actual data pointers for all keys in the database.
- **Push Up** (Non-Leaf Node Split):
  - When a non-leaf node overflows and splits, the middle key is **pushed up** to the parent node.
  - The key is **removed** from the child nodes and exists only in the parent. This is because non-leaf nodes only act as routers; they do not need to contain data pointers for every key.

---

## 🔴 Hard

**Q6. A database block size is $B = 512$ bytes. We want to construct a B+ Tree index. The keys are $V = 8$ bytes, child pointers are $P = 4$ bytes, and data pointers in the leaves are $P_r = 6$ bytes. Find:**
1. **The maximum order $p$ of a non-leaf node.**
2. **The maximum order $p_{leaf}$ of a leaf node.**

#### Part 1: Order $p$ of a non-leaf node
A non-leaf node contains $p$ child pointers and $p - 1$ keys.
The total size must not exceed the block size $B$:
$$(p \cdot P) + ((p - 1) \cdot V) \le B$$
Substitute the values ($P = 4, V = 8, B = 512$):
$$(p \cdot 4) + ((p - 1) \cdot 8) \le 512$$
$$4p + 8p - 8 \le 512$$
$$12p \le 520$$
$$p \le \frac{520}{12} \approx 43.33$$

Since order must be an integer, the maximum order of a non-leaf node is **$p = 43$**.

#### Part 2: Order $p_{leaf}$ of a leaf node
A leaf node contains $p_{leaf}$ keys, $p_{leaf}$ data pointers, and 1 pointer to the next leaf node ($P = 4$ bytes):
$$(p_{leaf} \cdot V) + (p_{leaf} \cdot P_r) + P \le B$$
Substitute the values ($V = 8, P_r = 6, P = 4, B = 512$):
$$(p_{leaf} \cdot 8) + (p_{leaf} \cdot 6) + 4 \le 512$$
$$14p_{leaf} + 4 \le 512$$
$$14p_{leaf} \le 508$$
$$p_{leaf} \le \frac{508}{14} \approx 36.28$$

The maximum order of a leaf node is **$p_{leaf} = 36$**.

---

**Q7. A B+ Tree of order $p = 100$ (non-leaf) and $p_{leaf} = 100$ (leaf) stores $N = 1,000,000$ records. Find:**
1. **The minimum height of the tree (excluding root-to-leaf paths, i.e., count levels).**
2. **The maximum height of the tree.**

The height $h$ is defined as the number of levels from root to leaf.

#### Part 1: Minimum Height (Best Case - Max Occupancy)
For minimum height, every node is completely full:
- Root has $p$ pointers.
- Non-leaf nodes have $p$ pointers.
- Leaf nodes contain $p_{leaf}$ records.

At level $h$ (the leaf level), the maximum number of records we can store is:
$$N_{max} = p^{h-1} \cdot p_{leaf}$$
Substitute $p = 100, p_{leaf} = 100, N = 1,000,000$:
$$1,000,000 = 100^{h-1} \cdot 100$$
$$10,000 = 100^{h-1}$$
Since $10,000 = 100^2$:
$$h - 1 = 2 \implies h = 3$$

The minimum height of the tree is **$h = 3$** levels (Root $\rightarrow$ Level 2 $\rightarrow$ Leaves).

#### Part 2: Maximum Height (Worst Case - Min Occupancy)
For maximum height, every node is minimally filled:
- Root has at least 2 pointers.
- Non-leaf nodes have at least $\lceil p/2 \rceil = \lceil 100/2 \rceil = 50$ pointers.
- Leaf nodes contain at least $\lceil p_{leaf}/2 \rceil = 50$ records.

The minimum number of records at level $h$ is:
$$N_{min} = 2 \cdot (\lceil p/2 \rceil)^{h-2} \cdot \lceil p_{leaf}/2 \rceil$$
Substitute $N = 1,000,000$:
$$1,000,000 = 2 \cdot 50^{h-2} \cdot 50$$
$$1,000,000 = 100 \cdot 50^{h-2}$$
$$10,000 = 50^{h-2}$$
Take log base 50:
$$h - 2 = \log_{50}(10,000) = \frac{\log(10,000)}{\log(50)} \approx \frac{4}{1.6989} \approx 2.35$$
$$h \approx 4.35$$

Since $h$ must be an integer, we must check if $h=4$ or $h=5$ is the worst-case boundary.
Let's calculate capacity for $h = 4$:
$$N_{min} = 2 \cdot 50^2 \cdot 50 = 250,000 \text{ records}$$
Since $1,000,000 > 250,000$, height must be larger than 4 to accommodate 1,000,000 records.

Let's calculate capacity for $h = 5$:
$$N_{min} = 2 \cdot 50^3 \cdot 50 = 12,500,000 \text{ records}$$
Since $1,000,000 \le 12,500,000$, a height of 5 is sufficient.

The maximum height of the tree is **$h = 5$** levels.

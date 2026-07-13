# Module 2: File Structures & Indexing (B+ Trees)

---

## 1. Physical Storage & Page Layout

Databases do not read and write data byte-by-byte. The smallest unit of database I/O is a **Page** (in memory) or **Block** (on disk), typically 4KB or 8KB in size (MySQL's InnoDB uses a default page size of 16KB). 

### Slotted-Page Architecture
To store variable-length records on a page without leaving fragmented gaps, databases use the **slotted-page** architecture:

```
┌──────────────────────────────────────────────────────────────┐
│ Page Header                                                  │
│ ├─ Number of slots (records)                                 │
│ ├─ Pointer to end of free space                              │
│ └─ Transaction/LSN metadata                                  │
├──────────────────────────────────────────────────────────────┤
│ Slot Directory (grows downwards)                             │
│ ├─ Slot 0: [Offset = 1205, Length = 150]                     │
│ ├─ Slot 1: [Offset = 1000, Length = 205]                     │
│ └─ Slot 2: [Offset = Free, Length = 0]                       │
├──────────────────────────────────────────────────────────────┤
│                      ◄─── FREE SPACE ───►                    │
├──────────────────────────────────────────────────────────────┤
│ Record 1 (grows upwards)                                     │
├──────────────────────────────────────────────────────────────┤
│ Record 0 (grows upwards)                                     │
└──────────────────────────────────────────────────────────────┘
```

- **Header**: Tracks page metadata.
- **Slot Directory**: Array of entries containing the offset and length of each record on the page. Grows from top to bottom.
- **Records**: Stored from bottom to top. 
- **Deletions**: If a record is deleted, its slot entry is marked deleted. The record's space is marked free. The database periodically defragments pages (compacts records to remove gaps).

---

## 2. File Organization

A file is a collection of pages. How those pages are structured determines query performance.

1. **Heap File Organization**:
   - Records are placed in pages wherever there is free space. Unordered.
   - **Insert**: $O(1)$ (find a page with free space, write).
   - **Search**: $O(N)$ (requires scanning every block in the file).
2. **Sequential File Organization**:
   - Records are physically ordered by a search-key attribute.
   - **Search**: Fast for range queries on the search-key. Binary search on blocks takes $O(\log N)$ I/Os.
   - **Insert**: $O(N)$ (inserting in the middle requires shifting records or maintaining overflow chains, which degrades performance over time).
3. **Hash File Organization**:
   - A hash function is applied to a search key to determine the bucket (page) where the record belongs.
   - **Search**: $O(1)$ average.
   - **Range Queries**: Terribly slow (requires full table scan because hash functions do not preserve order).

---

## 3. Database Indexing Concepts

An **Index** is an auxiliary data structure used to speed up retrieval of records. It maps search keys to physical record pointers.

### Clustered (Index) vs. Unclustered Index
- **Clustered Index (Primary Index)**:
  - The physical order of data records in the file is the **same** as the logical order of the index.
  - A table can have **only one** clustered index because physical records can only be sorted in one way.
  - InnoDB (MySQL) automatically clusters tables by their Primary Key.
- **Unclustered Index (Secondary Index)**:
  - The physical order of data records is **different** from the index order.
  - The leaf nodes of the index contain pointers to the actual data blocks (or to the primary key, in InnoDB).
  - A table can have multiple unclustered indexes.

### Dense vs. Sparse Index
- **Dense Index**: An index record exists for **every** search-key value in the data file.
- **Sparse Index**: Index records exist for only **some** of the search-key values (typically one entry per physical data block). Requires the data file to be sorted by that search-key.

```
Dense Index:                         Sparse Index (Block-level):
Key   Pointer                        Key   Block Pointer
[10] ───► Row 10 (Block 1)           [10] ───► Block 1 (starts with 10)
[20] ───► Row 20 (Block 1)           [30] ───► Block 2 (starts with 30)
[30] ───► Row 30 (Block 2)
[40] ───► Row 40 (Block 2)
```

---

## 4. B-Trees vs. B+ Trees

A **B-Tree** is a self-balancing search tree. A **B+ Tree** is a variation designed specifically for database storage engines.

```
B-Tree Node:                         B+ Tree Non-Leaf Node (Router):
┌───────────┬───────────┐            ┌───────────┬───────────┐
│ Key 10    │ Key 20    │            │ Key 10    │ Key 20    │
├───────────┼───────────┤            ├───────────┼───────────┤
│ Data Ptr  │ Data Ptr  │ (Present)  │ Child Ptr │ Child Ptr │ (Only pointers to children)
└───────────┴───────────┘            └───────────┴───────────┘

                                     B+ Tree Leaf Node:
                                     ┌───────────┬───────────┬──────────────┐
                                     │ Key 10    │ Key 20    │ Next Leaf Ptr│
                                     ├───────────┼───────────┼──────────────┤
                                     │ Data Ptr  │ Data Ptr  │              │ (Data pointers present)
                                     └───────────┴───────────┴──────────────┘
```

### Differences & Why B+ Trees Are Preferred:
1. **Data Placement**:
   - In a **B-Tree**, keys and data pointers are stored in all nodes (both leaf and non-leaf).
   - In a **B+ Tree**, data pointers (or actual records) are stored **only in leaf nodes**. Non-leaf nodes store only keys and child pointers.
2. **Fan-out (Node Capacity)**:
   - Because B+ Tree non-leaf nodes do not store data pointers/records, they are much smaller. 
   - A single 16KB page can fit far more keys and pointers. This results in a higher **fan-out** (factor $p$).
   - A higher fan-out means a shorter tree height ($h$), reducing the number of disk reads for searches.
3. **Range Queries**:
   - In a B+ Tree, all leaf nodes are linked sequentially (usually as a doubly-linked list).
   - To do a range query (`WHERE age BETWEEN 20 AND 30`), the B+ Tree searches for 20, then traverses the leaf nodes horizontally until it hits 30. This takes $O(\log N)$ to find the start, then $O(1)$ per block.
   - A B-Tree requires performing an expensive in-order traversal (moving up and down the tree branches).

---

## 5. B+ Tree Internals & Math

A B+ Tree of order $p$ (maximum child pointers) has specific structural properties.

### Node Structure Constraints

Let $p$ be the order of non-leaf nodes, and $p_{leaf}$ be the order of leaf nodes.

#### Non-Leaf Nodes
- **Maximum child pointers**: $p$
- **Maximum keys**: $p - 1$
- **Minimum child pointers**: $\lceil p/2 \rceil$ (except the root node, which can have a minimum of 2 pointers).
- **Minimum keys**: $\lceil p/2 \rceil - 1$

#### Leaf Nodes
- **Maximum data pointers**: $p_{leaf}$
- **Maximum keys**: $p_{leaf}$
- **Minimum keys/data pointers**: $\lceil p_{leaf}/2 \rceil$ (except the root if it is a leaf).
- Has a pointer to the next leaf node.

### Node Size Calculation
Suppose a database block is $B$ bytes. 
Let:
- $V$ = size of a key (bytes)
- $P_r$ = size of a record/data pointer (bytes)
- $P$ = size of a child node pointer (bytes)

For a **non-leaf node** to fit in a single block:
$$(p \cdot P) + ((p - 1) \cdot V) \le B$$
$$p(P + V) - V \le B \implies p \le \frac{B + V}{P + V}$$

For a **leaf node** containing keys and data pointers:
$$(p_{leaf} \cdot P_r) + (p_{leaf} \cdot V) + P \le B$$
$$p_{leaf}(P_r + V) + P \le B \implies p_{leaf} \le \frac{B - P}{P_r + V}$$

---

## 6. B+ Tree Operations

### Search
1. Start at the root node.
2. Binary search the keys in the current node to find the smallest key greater than the search key.
3. Follow the corresponding child pointer.
4. Repeat until reaching a leaf node.
5. Search the leaf node for the key. If found, retrieve the record; else, the key does not exist.

### Insertion (Splitting)
1. Perform search to find the correct leaf node $L$.
2. If $L$ has space (keys $< p_{leaf}$), insert the key in sorted order.
3. If $L$ is full (overflows), split $L$ into two nodes, $L_1$ and $L_2$:
   - Copy the first $\lceil (p_{leaf} + 1)/2 \rceil$ values to $L_1$, and the rest to $L_2$.
   - **Copy up** the smallest key of $L_2$ into the parent node.
4. If the parent node overflows, split the parent node:
   - **Push up** the middle key to its parent (do not copy it in the child split).
5. Repeat splits upward if necessary. If the root splits, create a new root with 2 children.

### Deletion (Redistribution & Merging)
1. Find leaf node $L$ containing the key. Delete the key.
2. If $L$ has at least $\lceil p_{leaf}/2 \rceil$ keys, update any parent routing keys if necessary and stop.
3. If $L$ has fewer keys (underflow):
   - **Redistribution (Borrow)**: If a sibling has extra keys, borrow the nearest key. Update the parent routing key.
   - **Merging (Coalescing)**: If no sibling has extra keys, merge $L$ with its sibling. Delete the separating key from the parent.
4. If a parent node underflows, apply the same logic (borrow or merge non-leaf nodes). If the root is left with only 1 child pointer after a merge, make that child the new root.

---

## 7. Index Scan Types

MySQL/MariaDB query execution plans show different scan patterns:

1. **Sequential Scan (Full Table Scan - `ALL` in EXPLAIN)**:
   - Reads every page of the data file from disk. Used if no index matches the query filters, or if the filter matches a large percentage of the table (optimizer decides scanning is cheaper than index random I/O).
2. **Index Scan (`index` in EXPLAIN)**:
   - Reads the entire index tree sequentially (leaf nodes). Useful if the query can be satisfied entirely by index attributes, or for ordering.
3. **Index Only Scan (`Using index` in Extra column)**:
   - The index contains **all** the columns requested by the query (covering index). The database reads the leaf nodes of the index and returns the result **without ever reading the actual data pages** from disk. Extremely fast.
4. **Point Lookup (`const` or `eq_ref` in EXPLAIN)**:
   - Searches for a unique key (primary key or unique index). Resolves in $h$ disk accesses (typically 3-4 reads).

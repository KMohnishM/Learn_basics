# Cheat Sheet — File Structures & Indexing

## Slotted-Page Layout
```
┌────────────────────────────────────────────────────────┐
│ Page Header                                            │
├────────────────────────────────────────────────────────┤
│ Slot Directory (offset, length)                        │
│   ├── Slot 0  ──┐ (grows downwards)                    │
│   └── Slot 1  ──┼┐                                     │
├─────────────────┼┼─────────────────────────────────────┤
│                 ▼▼    ◄── FREE SPACE ──►               │
├────────────────────────────────────────────────────────┤
│   Record 1 ◄────┘ (grows upwards)                      │
├────────────────────────────────────────────────────────┤
│   Record 0 ◄────┘                                      │
└────────────────────────────────────────────────────────┘
```

---

## B+ Tree Occupancy Rules

Let $p$ = max child pointers (non-leaf order), $p_{leaf}$ = max keys/data pointers (leaf order).

| Node Type | Minimum Keys | Maximum Keys | Minimum Pointers | Maximum Pointers |
|-----------|--------------|--------------|------------------|------------------|
| **Root (Non-Leaf)** | 1 | $p - 1$ | 2 | $p$ |
| **Non-Leaf** | $\lceil p/2 \rceil - 1$ | $p - 1$ | $\lceil p/2 \rceil$ | $p$ |
| **Leaf** | $\lceil p_{leaf}/2 \rceil$ | $p_{leaf}$ | — | — |

---

## B+ Tree Calculations

### Max Node Order Formulas
Given block size $B$, key size $V$, child pointer size $P$, and data pointer size $P_r$:

- **Non-Leaf Node Max Order ($p$):**
  $$p \cdot P + (p - 1) \cdot V \le B \implies p \le \frac{B + V}{P + V}$$

- **Leaf Node Max Order ($p_{leaf}$):**
  $$p_{leaf} \cdot V + p_{leaf} \cdot P_r + P \le B \implies p_{leaf} \le \frac{B - P}{P_r + V}$$
  *(Note: $P$ represents the pointer to the next leaf node).*

### Tree Height Limits ($h$)
To store $N$ records in a B+ Tree:

- **Minimum Height ($h_{min}$):**
  $$h_{min} = \lceil \log_{p}(N / p_{leaf}) \rceil + 1$$
  *(Assumes all nodes are 100% full).*

- **Maximum Height ($h_{max}$):**
  $$h_{max} = \lceil \log_{\lceil p/2 \rceil} (N / (2 \cdot \lceil p_{leaf}/2 \rceil)) \rceil + 2$$
  *(Assumes all nodes are at minimum 50% occupancy).*

---

## Index Scan Patterns in MySQL

| Type | EXPLAIN Name | I/O Pattern | Best For |
|------|--------------|-------------|----------|
| **Full Table Scan** | `ALL` | Sequential reads of entire table | Scanning table, small tables, unmatched queries |
| **Index Scan** | `index` | Sequential scan of index leaf nodes | Sorting, queries covered entirely by index |
| **Index Only Scan** | `Using index` (Extra) | Reads index leaves ONLY (zero data file reads) | Covering indexes (extremely fast) |
| **Range Scan** | `range` | Traverse index to start key, scan leaf chain | `BETWEEN`, `>`, `<` queries on indexed keys |
| **Point Lookup** | `const` / `eq_ref` | Traverse index path directly to leaf | Unique key searches (3-4 I/Os) |

---

## Split and Merge Rules

### Node Splits (Overflow)
- **Leaf Split**: Split keys into $\lceil (p_{leaf}+1)/2 \rceil$ in left and rest in right. **Copy up** the smallest key of the right node to the parent.
- **Non-Leaf Split**: Split keys. **Push up** the middle key to the parent (remove it from children).

### Node Merges (Underflow)
- **Borrowing (Redistribution)**: Take a key from a sibling node. Update parent routing key.
- **Merging (Coalescing)**: Merge node with sibling. Delete separating key from parent. If parent underflows, repeat recursively.

# Q&A — Query Processing & Optimization

---

## 🟢 Easy

**Q1. What is Relational Algebra? Name three fundamental operations.**

Relational Algebra is a procedural query language that operates on relations (tables) to produce new relations. It defines the mathematical execution model for SQL databases.
- **Selection ($\sigma$)**: Selects rows matching a predicate.
- **Projection ($\pi$)**: Selects specific columns, discarding duplicates.
- **Cartesian Product ($\times$)**: Combines every row of table A with every row of table B.

---

**Q2. List the MySQL `EXPLAIN` join types from best to worst performance.**

1. `system` / `const`: Table has at most one matching row (e.g., Primary Key lookup).
2. `eq_ref`: Primary Key/Unique index lookup used in a join.
3. `ref`: Non-unique index lookup.
4. `range`: Index range scan (e.g., `>`, `<`, `BETWEEN`).
5. `index`: Full index scan (scans the index leaf pages in memory/disk).
6. `ALL`: Full table scan (sequential scan of all data pages on disk — worst performance).

---

**Q3. What does `Using filesort` mean in a MySQL `EXPLAIN` output? How do you fix it?**

- **Meaning**: MySQL had to perform an extra pass to sort the retrieved rows because it could not use an index to return the rows in sorted order. It might sort in memory (quicksort) or on disk (external merge sort) depending on the size of the result set.
- **How to fix**: Create an index on the column(s) used in the `ORDER BY` clause. If the query has a `WHERE` and `ORDER BY`, create a **composite index** covering both the filter column and the sort column (e.g., `INDEX(status, created_at)` for `WHERE status = 'active' ORDER BY created_at`).

---

## 🟡 Medium

**Q4. Explain the cost-benefit of "pushing down selection" in query trees.**

- **Concept**: Pushing down selection means applying filtering operations ($\sigma$) as early as possible in the query execution tree (closer to the base tables, before joins or projections).
- **Cost-benefit**:
  - Joins ($R \bowtie S$) are computationally expensive. Their cost is proportional to the size of the inputs.
  - By applying a selection filter on $R$ first, we reduce the size of $R$ from $N$ rows to a much smaller subset $K$.
  - The join algorithm now only processes $K \times S$ instead of $N \times S$.
  - This reduces disk I/O (fewer intermediate blocks are written/read) and memory utilization.

---

**Q5. Contrast Block Nested Loop Join and Index Nested Loop Join.**

- **Block Nested Loop Join**:
  - Compares tables block-by-block. For each outer block, it loads the entire inner table block-by-block into memory.
  - Used when no index is available on the join attribute.
  - Cost: $b_r + b_r \cdot b_s$ block transfers (very high for large tables).
- **Index Nested Loop Join**:
  - For each tuple in the outer table, it performs a lookup using an index (e.g., B+ Tree) on the inner table.
  - Used when the inner table has an index on the join column.
  - Cost: $b_r + t_r \cdot (\text{index lookup cost})$.
  - Far more efficient because it avoids scanning the inner table blocks sequentially.

---

## 🔴 Hard

**Q6. Consider two relations $R$ and $S$.**
- **$R$ has $b_r = 1000$ blocks and $t_r = 20,000$ tuples.**
- **$S$ has $b_s = 500$ blocks and $t_s = 10,000$ tuples.**
- **The database buffer pool has $M = 102$ memory pages.**

**Calculate the total number of disk block transfers required to compute the join $R \bowtie S$ using Block Nested Loop Join if:**
1. **$R$ is the outer relation.**
2. **$S$ is the outer relation.**

*Formula*: For Block Nested Loop Join with $M$ buffer pages, we use $M-2$ pages to buffer the outer relation, 1 page for the inner relation, and 1 page for output.
$$\text{Total Block Transfers} = b_{\text{outer}} + \left( \lceil \frac{b_{\text{outer}}}{M - 2} \right\rceil \cdot b_{\text{inner}} )$$

#### Part 1: $R$ is the outer relation ($b_{\text{outer}} = 1000$, $b_{\text{inner}} = 500$, $M - 2 = 100$)
1. We divide $R$ into chunks of 100 blocks. Number of chunks = $\lceil 1000 / 100 \rceil = 10$ chunks.
2. For each of the 10 chunks:
   - Read the chunk of $R$ into memory (100 blocks).
   - Read the entire inner relation $S$ page-by-page (500 blocks).
3. Calculation:
   $$\text{Transfers} = 1000 + (10 \cdot 500)$$
   $$\text{Transfers} = 1000 + 5000 = 6000 \text{ block transfers}$$

#### Part 2: $S$ is the outer relation ($b_{\text{outer}} = 500$, $b_{\text{inner}} = 1000$, $M - 2 = 100$)
1. We divide $S$ into chunks of 100 blocks. Number of chunks = $\lceil 500 / 100 \rceil = 5$ chunks.
2. For each of the 5 chunks:
   - Read the chunk of $S$ into memory (100 blocks).
   - Read the entire inner relation $R$ page-by-page (1000 blocks).
3. Calculation:
   $$\text{Transfers} = 500 + (5 \cdot 1000)$$
   $$\text{Transfers} = 500 + 5000 = 5500 \text{ block transfers}$$

**Conclusion**: Choosing the smaller relation ($S$) as the outer relation is more efficient (5500 vs 6000 transfers).

---

**Q7. Calculate the disk I/O cost (in block transfers) to sort a relation $R$ containing $b_r = 10,000$ blocks using an External Merge Sort with $M = 11$ buffer pages.**

*Formula for External Merge Sort cost:*
$$\text{Total Cost} = 2b_r \cdot (\text{Number of passes})$$
$$\text{Number of passes} = \text{Pass}_0 \text{ (Initial Run Generation)} + \text{Merge Passes}$$
$$\text{Merge Passes} = \lceil \log_{M-1}( \lceil b_r / M \rceil ) \rceil$$

#### Step 1: Initial Run Generation (Pass 0)
- Read $M = 11$ blocks at a time, sort them in memory, write back.
- Number of initial sorted runs = $\lceil b_r / M \rceil = \lceil 10,000 / 11 \rceil = 910$ runs.
- Cost of Pass 0: read 10,000 blocks and write 10,000 blocks = $20,000$ transfers.

#### Step 2: Merge Passes
- We merge $M - 1 = 10$ runs at a time.
- Number of merge passes:
  $$\text{Merge Passes} = \lceil \log_{10}(910) \rceil$$
  Since $10^2 = 100$ and $10^3 = 1000$:
  $$\log_{10}(910) \approx 2.96 \implies \lceil 2.96 \rceil = 3 \text{ merge passes}$$

#### Step 3: Calculate Total Cost
- Total passes = $1 \text{ (Pass 0)} + 3 \text{ (Merge Passes)} = 4$ passes.
- Every pass reads all 10,000 blocks and writes all 10,000 blocks.
  $$\text{Total Cost} = 2 \cdot 10,000 \cdot 4 = 80,000 \text{ block transfers}$$

*Verify using direct formula:*
$$\text{Cost} = 2b_r \left( \lceil \log_{M-1}(b_r / M) \rceil + 1 \right)$$
$$\text{Cost} = 20,000 \left( \lceil \log_{10}(910) \rceil + 1 \right) = 20,000 (3 + 1) = 80,000 \text{ transfers}$$
**Answer**: **$80,000$ block transfers**.

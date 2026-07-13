# Module 6: Query Processing & Optimization

---

## 1. Relational Algebra

Relational Algebra is a procedural query language that takes one or more relations as input and produces a new relation as output. It forms the mathematical foundation of SQL query compilation and optimization.

### Fundamental Operations

#### 1. Selection ($\sigma$)
Selects a subset of tuples from a relation that satisfy a given predicate $p$.
$$\sigma_p(r) = \{t \mid t \in r \text{ and } p(t) \text{ is true}\}$$
- *Example*: $\sigma_{\text{salary} > 50000}(\text{Employee})$

#### 2. Projection ($\pi$)
Selects specific columns (attributes) from a relation and discards the rest. Duplicates are eliminated (mathematically).
$$\pi_{A_1, A_2, \dots, A_k}(r)$$
- *Example*: $\pi_{\text{name, salary}}(\text{Employee})$

#### 3. Cartesian Product ($\times$)
Combines information from any two relations. If $r$ has $n$ tuples and $s$ has $m$ tuples, $r \times s$ has $n \cdot m$ tuples.
$$r \times s$$

#### 4. Rename ($\rho$)
Renames a relation or its attributes.
$$\rho_{x(A_1, A_2, \dots, A_n)}(r)$$
Renames relation $r$ to $x$, and its attributes to $A_1, A_2, \dots, A_n$.

#### 5. Set Operations
- **Union ($\cup$)**: Combines tuples from two relations. Relations must be **union-compatible** (same number of attributes, corresponding domains are identical).
- **Set Difference ($-$)**: Finds tuples present in the first relation but not in the second. Must be union-compatible.
- **Intersection ($\cap$)**: Finds tuples common to both relations.

### Joined Relations

#### 1. Natural Join ($\bowtie$)
Associates tuples from two relations that agree on all common attributes, and automatically projects out the duplicate common columns.
$$r \bowtie s = \pi_{\text{unique\_attributes}}(\sigma_{r.A_1 = s.A_1 \land r.A_2 = s.A_2}(r \times s))$$

#### 2. Theta Join ($\bowtie_\theta$)
A Cartesian product followed by a selection condition $\theta$.
$$r \bowtie_\theta s = \sigma_\theta(r \times s)$$

---

## 2. Query Evaluation & Cost Models

Query processing translates SQL queries into relational algebra expressions, compiles them into **query execution trees**, and estimates their cost to pick the most efficient plan.

### Disk I/O Cost Model
Because memory access is orders of magnitude faster than disk access, query cost is measured primarily in terms of **disk block transfers**:
- $b_r$: Number of blocks containing tuples of relation $R$.
- $t_r$: Number of tuples in relation $R$.
- $f_r$: Blocking factor (number of tuples of $R$ that fit in a single block).
- $M$: Number of memory buffer pages available for query execution.

---

## 3. Join Algorithms & Cost Estimation

To join two tables $R$ (outer relation) and $S$ (inner relation) on a join attribute:

### 1. Block Nested Loop Join
For each block of the outer relation $R$, read it into memory. For each block of the inner relation $S$, read it into memory and compare all tuples.

#### Disk I/O Cost:
- **Worst Case** (only 1 page buffer for $R$ and 1 for $S$):
  $$\text{Total Block Transfers} = b_r + (b_r \cdot b_s)$$
- **Best Case** (the smaller relation, say $R$, fits completely in memory: $b_r < M - 2$):
  $$\text{Total Block Transfers} = b_r + b_s$$

---

### 2. Index Nested Loop Join
If there is an index (B+ Tree) on the join attribute of the inner relation $S$:
- For each tuple in the outer relation $R$, search the index of $S$ to retrieve the matching tuples.

#### Disk I/O Cost:
$$\text{Total Block Transfers} = b_r + t_r \cdot c$$
Where $c$ is the cost of searching the index and retrieving all matching tuples of $S$ for a single key. For a B+ Tree, $c \approx \text{height of B+ Tree} + \text{blocks containing matching records}$.

---

### 3. Sort-Merge Join
1. Sort both relations $R$ and $S$ on the join attribute (if they are not already sorted).
2. Scan both sorted files in parallel to merge and join matching tuples.

#### Disk I/O Cost (excluding sorting cost):
$$\text{Total Block Transfers} = b_r + b_s$$

#### External Merge Sort Cost (for sorting a relation $R$ using $M$ buffers):
$$\text{Sort Cost}(R) = 2b_r \left( \lceil \log_{M-1}(b_r / M) \rceil + 1 \right)$$
*(Each pass reads and writes all blocks; $+1$ is for the initial run generation pass).*

---

### 4. Hash Join
1. **Build Phase**: Partition the outer relation $R$ into buckets by hashing the join attribute.
2. **Probe Phase**: Partition the inner relation $S$ using the same hash function. For each tuple in $S$, hash it and search the corresponding bucket of $R$ in memory.

#### Disk I/O Cost (assuming no bucket overflow):
$$\text{Total Block Transfers} = 3(b_r + b_s)$$
- $2(b_r + b_s)$ block transfers to read and write both relations to disk during the partitioning phase.
- $1(b_r + b_s)$ block transfers to read all partitions back into memory during the probe phase.

---

## 4. Query Optimization & Equivalence Rules

A query optimizer transforms a logical query tree into an equivalent, more efficient tree using mathematical rules.

### Core Equivalence Rules
1. **Commutativity of Joins**:
   $$r \bowtie s \equiv s \bowtie r$$
2. **Associativity of Joins**:
   $$(r \bowtie s) \bowtie t \equiv r \bowtie (s \bowtie t)$$
3. **Pushing Selection ($\sigma$) Down**:
   If predicate $p$ only involves attributes of $R$:
   $$\sigma_p(R \bowtie S) \equiv \sigma_p(R) \bowtie S$$
   *Why*: Reduces the number of tuples *before* performing the expensive join operation.
4. **Pushing Projection ($\pi$) Down**:
   If list $L$ only contains attributes present in $R$ and $S$:
   $$\pi_L(R \bowtie S) \equiv \pi_L(\pi_{L_1}(R) \bowtie \pi_{L_2}(S))$$
   *Why*: Discards unused columns early, reducing block sizes of intermediate tables.

### Optimization Example
Consider query: `SELECT R.name, S.salary FROM R JOIN S ON R.id = S.id WHERE R.age > 30`

```
   Naive Query Tree (Late Filter)           Optimized Query Tree (Early Filter/Pushdown)
             Project [name, salary]                         Project [name, salary]
                      │                                              │
               Filter [age > 30]                              Join [R.id = S.id]
                      │                                      ┌───────┴───────┐
                Join [id = id]                       Filter [age > 30]       S
               ┌──────┴──────┐                               │
               R             S                               R
```

In the optimized tree, the filter `age > 30` is applied directly to $R$ first, reducing the number of rows that must be joined with $S$.

---

## 5. MySQL EXPLAIN & EXPLAIN ANALYZE

In MySQL (using InnoDB), prepend `EXPLAIN` or `EXPLAIN ANALYZE` to a query to see the optimizer's execution plan.

### Key EXPLAIN Columns
- **select_type**: Type of query (e.g., `SIMPLE`, `PRIMARY`, `SUBQUERY`, `DERIVED`).
- **table**: The table being accessed.
- **type**: The join type (ordered from best to worst performance):
  - `system`/`const`: Table has at most one matching row (e.g., primary key lookup).
  - `eq_ref`: Primary key or unique index lookup for a join.
  - `ref`: Non-unique index lookup.
  - `range`: Index range scan (e.g., `BETWEEN`, `>`, `<`).
  - `index`: Full index scan (reads index leaves).
  - `ALL`: Full table scan (sequential read of all data pages on disk).
- **possible_keys**: Indexes the optimizer *could* use.
- **key**: The index the optimizer *actually* chose.
- **rows**: Estimate of the number of rows MySQL must examine.
- **Extra**: Additional details (e.g., `Using index` = Index Only Scan; `Using filesort` = sorting in memory/disk instead of using index, bad for performance; `Using temporary` = temp table needed).

### EXPLAIN ANALYZE (MySQL 8.0+)
Runs the query and outputs the actual execution times and row counts for each step in the tree:
```sql
EXPLAIN ANALYZE SELECT * FROM users JOIN orders ON users.id = orders.user_id WHERE users.age > 30;
```
Outputs:
- **Actual time to first row** (start) and **time to last row** (end) in milliseconds.
- **Actual number of loops** executed.
- **Actual number of rows** returned by each node.
This is the ultimate tool for debugging query bottlenecks.

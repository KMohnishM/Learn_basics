# Cheat Sheet — Query Processing & Optimization

## Relational Algebra Symbols

| Operation | Symbol | Syntax | Purpose |
|-----------|:------:|--------|---------|
| **Selection** | $\sigma$ | $\sigma_p(R)$ | Select rows matching predicate $p$ |
| **Projection** | $\pi$ | $\pi_{A_1, A_2}(R)$ | Select specific columns, drop duplicates |
| **Cartesian Product**| $\times$ | $R \times S$ | Cross-combine all rows |
| **Rename** | $\rho$ | $\rho_{x}(R)$ | Rename table to $x$ |
| **Natural Join** | $\bowtie$ | $R \bowtie S$ | Join on matching common columns |
| **Theta Join** | $\bowtie_\theta$ | $R \bowtie_\theta S$ | Cartesian product then filter $\theta$ |
| **Union** | $\cup$ | $R \cup S$ | Combine rows (union-compatible) |
| **Difference** | $-$ | $R - S$ | Rows in $R$ but not in $S$ |
| **Intersection** | $\cap$ | $R \cap S$ | Rows in both $R$ and $S$ |

---

## Join Cost Models (Disk I/O Block Transfers)

Let $R$ be the outer relation, $S$ be the inner relation.
$b_r, b_s$ = blocks, $t_r, t_s$ = tuples, $M$ = memory buffer pages.

### 1. Block Nested Loop Join
- **Worst Case** (1 block buffer for $R$ and 1 for $S$):
  $$\text{Cost} = b_r + (b_r \cdot b_s)$$
- **Standard case** (using $M-2$ pages for outer relation $R$):
  $$\text{Cost} = b_r + \left( \lceil \frac{b_r}{M - 2} \rceil \cdot b_s \right)$$
- **Best Case** (outer relation $R$ fits in memory: $b_r < M - 2$):
  $$\text{Cost} = b_r + b_s$$

### 2. Index Nested Loop Join
- Index on join column of inner relation $S$ (search cost = $c$):
  $$\text{Cost} = b_r + t_r \cdot c$$

### 3. Sort-Merge Join (after sorting)
- **Cost**: $b_r + b_s$

### 4. Hash Join (assuming no overflow)
- **Cost**: $3(b_r + b_s)$
  *(2 passes to partition, 1 pass to probe).*

---

## External Merge Sort Cost Formula

To sort a relation $R$ of $b_r$ blocks using $M$ buffer pages:
$$\text{Total Cost} = 2b_r \cdot (\text{Number of passes})$$
$$\text{Number of passes} = 1 \text{ (Pass 0: run generation)} + \lceil \log_{M-1}( \lceil b_r / M \rceil ) \rceil$$

---

## Query Tree Equivalence Rules
- **Pushing Selection down**: $\sigma_p(R \bowtie S) \equiv \sigma_p(R) \bowtie S$ (if $p$ only involves $R$)
- **Pushing Projection down**: $\pi_{A}(R \bowtie S) \equiv \pi_{A}(\pi_{A \cap R}(R) \bowtie \pi_{A \cap S}(S))$
- **Join Commutativity**: $R \bowtie S \equiv S \bowtie R$
- **Join Associativity**: $(R \bowtie S) \bowtie T \equiv R \bowtie (S \bowtie T)$

---

## MySQL EXPLAIN Join Type Matrix

| type | Speed | Description | Example |
|------|:-----:|-------------|---------|
| `const` | ⭐⭐⭐⭐⭐ | Single row match | Primary key lookup |
| `eq_ref` | ⭐⭐⭐⭐ | Unique index lookup in join | Join on primary key |
| `ref` | ⭐⭐⭐ | Non-unique index lookup | Join on foreign key |
| `range` | ⭐⭐ | Index range scan | `WHERE id > 10` |
| `index` | ⭐ | Full index scan (leaves only) | Scans index, no table read |
| `ALL` | ❌ | Full table scan (entire disk file) | Scans all rows on disk |

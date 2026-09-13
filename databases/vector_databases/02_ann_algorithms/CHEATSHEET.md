# CHEATSHEET: ANN Algorithms

## 1. ANN Algorithm Decision Matrix

| Requirement | Dataset Size | Recommended Algorithm | Rationale |
| :--- | :--- | :--- | :--- |
| **Highest Recall, Low Latency** | Small to Medium (< 10M) | **HNSW** | Unbeatable recall and latency, but consumes massive memory. Ideal if RAM is not a bottleneck. |
| **Strict Memory Limits** | Massive (10M to 1B+) | **IVF-PQ** | Compresses vectors heavily. Sacrifices some recall and latency but fits billion-scale data in reasonable RAM. |
| **MIPS (Dot Product) Focus** | Any | **SCaNN** | Anisotropic quantization specifically optimized for maximum inner product search. Superior for cosine/dot-product embeddings. |
| **100% Exact Results needed** | Very Small (< 100K) | **FLAT (Exact)** | No accuracy loss. Brute force scan is faster than traversing ANN structures for tiny datasets. Fits in cache. |
| **High Update/Delete Rate** | Any | **IVF-Flat** | Easier to update than HNSW. Changing a vector just means reassigning it to a cluster list. Graph repair in HNSW is expensive. |

---

## 2. HNSW Parameter Tuning Guide

HNSW has three critical parameters that govern the build time, search speed, and memory trade-offs.

### `M` (Max Connections)
- **What it is**: Maximum number of bidirectional links created for every new element. Determines the density of the graph.
- **Typical Range**: `16` to `64`
- **Tuning**:
  - Increase `M` for high-dimensional data or when extremely high recall is required.
  - Higher `M` = Higher Memory consumption and Slower Build Time.

### `ef_construction` (Construction Search Depth)
- **What it is**: Size of the dynamic candidate list during index build. 
- **Rule of Thumb**: Must be at least `M`.
- **Typical Range**: `100` to `500`
- **Tuning**:
  - Higher `ef_construction` = Better graph quality (higher recall ceiling) but significantly longer build times.
  - Set it as high as your infrastructure allows during the build phase. It does not affect query latency.

### `ef_search` (Query Search Depth)
- **What it is**: Size of the dynamic candidate list during querying.
- **Rule of Thumb**: Must be at least `k` (the number of neighbors requested).
- **Typical Range**: `50` to `200`
- **Tuning**:
  - This is your primary lever for adjusting QPS vs Recall at runtime.
  - Higher `ef_search` = Higher Recall, Lower QPS.
  - Lower `ef_search` = Lower Recall, Higher QPS.

---

## 3. IVF Parameter Tuning Guide

### `nlist` (Number of Centroids)
- **What it is**: How many clusters the dataset is partitioned into.
- **Rule of Thumb**: For a dataset of size $N$, a common starting point is $nlist = \sqrt{N}$ or $4 \times \sqrt{N}$.

### `nprobe` (Clusters to Search)
- **What it is**: The number of closest clusters to search during query time.
- **Tuning**: 
  - Primary knob for trading QPS for Recall.
  - Usually set to a small fraction of `nlist` (e.g., $1\%$ to $5\%$ of `nlist`).
  - Higher `nprobe` = Higher Recall, Lower QPS.

---

## 4. Memory Reduction Calculation Formulas

### 4.1 FLAT / Exact Memory
Memory required for raw vectors (assuming float32, which is 4 bytes).
$$\text{Memory}_{FLAT} = N \times D \times 4 \text{ bytes}$$
*(Where $N$ = number of vectors, $D$ = dimensions)*

### 4.2 HNSW Memory
Memory required for raw vectors plus graph overhead.
$$\text{Memory}_{HNSW} = (N \times D \times 4) + (N \times M \times 4) \text{ bytes}$$
*(Where $M$ = max connections parameter. 4 bytes per connection pointer)*

### 4.3 PQ (Product Quantization) Memory
Memory required after quantization.
$$\text{Memory}_{PQ} = N \times M_{sub} \text{ bytes}$$
*(Where $M_{sub}$ = number of sub-vectors the original vector is split into. Assuming $K=256$ centroids, so 1 byte per sub-vector ID)*

### 4.4 Example Calculation
- $N = 1,000,000$ (1 million vectors)
- $D = 768$ (dimensions)
- HNSW $M = 32$
- PQ $M_{sub} = 64$

1. **FLAT**: $1M \times 768 \times 4 = 3.07 \text{ GB}$
2. **HNSW**: $3.07 \text{ GB} + (1M \times 32 \times 4) = 3.07 \text{ GB} + 0.128 \text{ GB} = 3.19 \text{ GB}$
3. **PQ**: $1M \times 64 = 64 \text{ MB}$

*Note: PQ memory savings in this example is ~97.9% compared to FLAT.*

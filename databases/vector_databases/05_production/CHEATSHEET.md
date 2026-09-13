# Production Vector Database Cheatsheet

## Capacity Planning Calculator Formulas

Predicting infrastructure requirements is crucial to prevent Out-Of-Memory (OOM) errors.

**Raw Vector Memory ($M_v$):**
$$ M_v = N_{vectors} \times Dimensions \times 4 \text{ bytes (for FP32)} $$

**HNSW Graph Overhead ($M_{hnsw}$):**
$$ M_{hnsw} \approx N_{vectors} \times M \times 2 \times 8 \text{ bytes} $$
*(Assuming max connections $M=16$ and 64-bit pointers)*

**Total RAM Requirement ($RAM_{total}$):**
$$ RAM_{total} = (M_v + M_{hnsw}) \times (1 + \text{OS Buffer Overhead}) $$
*(Standard OS Buffer Overhead is ~0.20 or 20%)*

**Example (1M vectors, 1536 dims):**
- $M_v = 1,000,000 \times 1536 \times 4 = 6.14 \text{ GB}$
- $M_{hnsw} = 1,000,000 \times 16 \times 2 \times 8 = 0.25 \text{ GB}$
- $RAM_{total} = (6.14 + 0.25) \times 1.20 = 7.66 \text{ GB}$

---

## Filtering Strategies Comparison

| Strategy | Execution Flow | Pros | Cons | Ideal Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Pre-Filtering** | Metadata Filter $\rightarrow$ Allowed List $\rightarrow$ Vector Search | 100% accurate filter matches. | Massive performance drop if filter results in sparse dataset (brute force fallback). | When filters match >20% of the entire database. |
| **Post-Filtering** | Vector Search (Top N) $\rightarrow$ Metadata Filter $\rightarrow$ Result | Extremely fast graph traversal. | "Missing K" problem. Returns fewer than requested results if matches are filtered out. | Prototyping, or when filters are purely aesthetic and not restrictive. |
| **Single-Stage** | Filter evaluated *during* graph traversal | Guarantees K results, maintains $O(\log N)$ speed. | Complex engine implementation (handled by modern vendors). | **Production standard.** Use whenever supported. |

---

## Semantic Cache Flow Diagram

```text
       [ User Query ]
             |
             v
     ( Embedding Model )
             |
      Query Vector (Eq)
             |
    +-------------------+
    |  SEMANTIC CACHE   |  <-- In-memory Vector Index (Threshold = 0.95)
    +-------------------+
             |
      Match > 0.95?
      /           \
   [YES]         [NO]
     |             |
     |             v
     |      +--------------+
     |      | Main Vector  |  <-- Retrieve context documents
     |      |   Database   |
     |      +--------------+
     |             |
     |             v
     |      +--------------+
     |      |     LLM      |  <-- Generate expensive response (R)
     |      +--------------+
     |             |
     |             +---------> [ Write Eq + R to Cache ]
     v             |
 [ Cached ]    [ Fresh ]
 [Response]    [Response]
       \          /
        v        v
      [ Return to User ]
```

---

## Production Readiness Checklist

### Infrastructure & Sizing
- [ ] RAM sized appropriately for Vector + HNSW graph overhead.
- [ ] High-Availability (HA) replica sets deployed across Availability Zones.
- [ ] Disk persistence enabled with Write-Ahead Logs (WAL).

### Ingestion Pipeline
- [ ] Application utilizes batch upsert APIs (e.g., batches of 500-1000).
- [ ] Backpressure / Exponential backoff implemented for Rate Limit (429) handling.
- [ ] Vector normalization applied at ingestion if using Cosine Similarity.

### Query Optimization
- [ ] Queries utilize Single-Stage / In-Payload filtering.
- [ ] Shared index multi-tenancy configured correctly via `tenant_id` filters.
- [ ] Semantic caching layer deployed for high-volume endpoints.

### Monitoring & Operations
- [ ] P99 Query Latency dashboards established.
- [ ] Background index compaction / optimization jobs scheduled.
- [ ] Nightly Recall Drift tracking jobs implemented.
- [ ] Daily snapshots to cold storage configured.

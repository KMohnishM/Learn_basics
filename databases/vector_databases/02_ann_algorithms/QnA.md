# Vector Databases: ANN Algorithms QnA

## Q1: Explain HNSW's hierarchical layer structure. How does the formula `l = floor(-ln(uniform(0,1)) × m_L)` ensure most nodes appear only in layer 0? What property does this create?

Hierarchical Navigable Small World (HNSW) graphs construct a multi-layered structure of proximity graphs where each layer contains a subset of nodes from the layer below it. The bottom layer (layer 0) contains all elements in the dataset. As we move up the layers, the number of nodes decreases exponentially, creating a skip-list-like structure. During a search, the algorithm starts at the top layer, greedily finds the nearest node, and drops down to the next layer using that node as the starting point. This continues until it reaches layer 0, where a localized search yields the final nearest neighbors.

The formula `l = floor(-ln(uniform(0,1)) × m_L)` dictates the maximum layer `l` at which a newly inserted node will appear. Here, `uniform(0,1)` generates a random float between 0 and 1, and `m_L` is a normalization factor typically set to `1 / ln(M)`. Because the natural logarithm of a number between 0 and 1 is negative, the negative sign makes it positive. The exponential decay property of the `-ln(x)` distribution guarantees that large values of `l` are exceedingly rare. For example, if `m_L = 0.5`, the probability of a node being assigned to layer `l` halves for each increment of `l`.

This probabilistic assignment ensures that the vast majority of nodes are only present in layer 0, with progressively fewer nodes in higher layers. This creates a "small world" property across the hierarchy. The top layers provide long-range "expressway" links that allow logarithmic time traversal across the global data space, while the dense bottom layer ensures high local recall. Without this exponential decay, higher layers would be too dense, destroying the O(log N) search complexity and vastly increasing memory overhead.

## Q2: What are M, ef_construction, ef_search in HNSW? Explain the precise effect of doubling each on recall, memory consumption, build time, and single-query latency.

In HNSW, `M` defines the maximum number of bi-directional links (edges) created for every new node during insertion at layer 0 (higher layers have `M_max = M`, layer 0 has `M_max0 = 2*M`). `ef_construction` is the size of the dynamic candidate list evaluated during index construction. `ef_search` is the size of the dynamic candidate list maintained during the search phase.

Doubling `M` (e.g., from 16 to 32) significantly increases memory consumption because each node stores twice as many integer pointers (each edge is 4 bytes). Build time increases quadratically because more distance computations are required to evaluate and prune the denser edge lists. Single-query latency increases because more neighbors are evaluated at each step. However, recall generally improves, especially for high-dimensional or clustered data, as the graph becomes better connected, reducing the chance of getting stuck in local optima.

Doubling `ef_construction` (e.g., from 100 to 200) drastically increases the build time because the index evaluates twice as many candidates when inserting each node. It has absolutely zero impact on memory consumption or single-query latency. The primary benefit is a better-quality graph with more optimal edges, which leads to higher recall for a given `ef_search` value later on.

Doubling `ef_search` (e.g., from 50 to 100) has no effect on memory consumption or build time, as it is strictly a query-time parameter. It directly increases single-query latency, often linearly, because the search algorithm expands and evaluates a larger pool of candidates before stopping. The precision and recall increase asymptotically, as a larger `ef_search` explores a wider neighborhood in layer 0, guaranteeing better retrieval of the true nearest neighbors.

## Q3: Explain Product Quantization end-to-end: sub-vector splitting, codebook training, encoding, and Asymmetric Distance Computation. Why does ADC outperform symmetric code-to-code comparison?

Product Quantization (PQ) is a lossy compression technique that drastically reduces memory footprint while enabling fast approximate distance calculations. End-to-end, the process begins by splitting the original high-dimensional vectors into `m` smaller, equal-sized sub-vectors. For instance, a 1536-dimensional vector can be split into `m=96` sub-vectors, each of 16 dimensions.

Next, a codebook is trained for each of the `m` sub-spaces independently using k-means clustering. Typically, `k=256` centroids are generated per sub-space, meaning each centroid can be represented by a single 8-bit integer (1 byte). During the encoding phase, every vector in the dataset is transformed by replacing each of its `m` sub-vectors with the ID (0-255) of the nearest centroid in that sub-space's codebook. Our 1536-dim vector of 32-bit floats (6144 bytes) is thus compressed down to just 96 bytes.

Asymmetric Distance Computation (ADC) is the method used to compute distances between an uncompressed query vector and a PQ-compressed database vector. When a query arrives, it is also split into `m` sub-vectors. Before scanning the database, the system pre-computes a lookup table containing the exact distances between each query sub-vector and all 256 centroids of the corresponding sub-space. 

ADC vastly outperforms symmetric distance computation (where the query is also quantized, and distance is calculated between two quantized codes). In ADC, the query retains full precision. The distance approximation error comes solely from the quantization of the database vector, not the query. By doing the lookup table pre-computation (which takes minimal time, e.g., 96 x 256 distance calculations), ADC achieves near-exact scanning speeds by just summing up pre-calculated floating-point values from the lookup table, while delivering significantly higher recall than symmetric comparisons.

## Q4: Compare IVF+PQ to HNSW for a 100M-vector, 1536-dim dataset. Calculate memory estimates for each. At what nprobe does IVF-PQ match HNSW recall, and what is the QPS trade-off?

IVF+PQ (Inverted File with Product Quantization) and HNSW represent two opposite ends of the ANN trade-off spectrum: IVF+PQ prioritizes extreme memory efficiency, while HNSW prioritizes ultra-low latency and high recall at the cost of massive memory overhead.

For 100M vectors at 1536 dimensions (float32):
Raw data size: 100,000,000 × 1536 × 4 bytes = ~614 GB.
**HNSW Memory**: HNSW must store the raw vectors (or rely on an external key-value store, though in-memory is standard for low latency) plus the graph structure. Assuming `M=32`, layer 0 has 64 edges per node, plus higher layers. Graph overhead is roughly `(64 + 32) × 4 bytes = 384 bytes` per node. Total memory = `614 GB + (100M × 384 B) = ~652 GB`.
**IVF+PQ Memory**: Using `m=96` (96 bytes per vector for PQ codes) and `nlist=65536`. The memory includes the IVF posting lists (8 bytes per ID + 96 bytes per code) = 104 bytes per vector. Total memory = `100M × 104 B = ~10.4 GB`. (Centroids take negligible space).

To match HNSW's typical >95% recall, IVF+PQ requires an exceptionally high `nprobe` (the number of IVF clusters visited). Given `nlist=65536`, IVF partitions the space aggressively. To achieve 95% recall, you might need to set `nprobe` to 1024 or even 2048, meaning you scan 1.5% to 3% of the dataset per query. 

The QPS trade-off is brutal. HNSW can achieve 10,000+ QPS on this dataset because graph traversal evaluates only a few hundred candidates (O(log N)). IVF+PQ with `nprobe=2048` must compute distances against ~3 million PQ codes per query. Even with optimized ADC and SIMD, IVF+PQ will max out at a few hundred QPS (often 50-200 QPS) on standard CPU hardware to achieve the same recall, making it an order of magnitude slower than HNSW.

## Q5: What is DiskANN? What RAM and disk resources does it require for 1B vectors at 1536 dims? How does beam search + prefetching reduce effective SSD latency?

DiskANN is an ANN search algorithm specifically designed to scale to billion-scale datasets on a single workstation by leveraging fast NVMe SSDs instead of relying purely on expensive RAM. It extends the Vamana graph algorithm (a variant of HNSW-like navigable graphs) but intelligently separates the index storage: compressed representations sit in RAM, while the full graph structure and raw vectors reside on disk.

For 1B vectors at 1536 dims:
Raw data size = 1,000,000,000 × 1536 × 4 bytes = ~6.14 TB.
**Disk Resources**: The SSD must store the full graph and the raw vectors. The Vamana graph overhead (with `R=64` degree) is about `64 × 4 bytes = 256 bytes` per node. Total disk required = `6.14 TB (data) + 256 GB (graph) = ~6.4 TB`.
**RAM Resources**: DiskANN keeps a highly compressed PQ version of the vectors in memory to route queries without touching the disk until necessary. Using `m=64` bytes per vector, the memory footprint is `1B × 64 bytes = 64 GB`, plus a few gigabytes for the top-level navigational nodes. This easily fits into an affordable 128GB RAM machine.

DiskANN overcomes SSD IO latency (which is ~50-100 microseconds, orders of magnitude slower than RAM) using beam search combined with aggressive asynchronous prefetching. In standard HNSW, you fetch one node, evaluate its neighbors, and then fetch the next best node. Doing this sequentially on an SSD would yield abysmal latency (e.g., 100 hops × 100µs = 10ms just in IO wait). 

Instead, DiskANN uses a beam search with a beam width (e.g., `W=4` or `W=8`). It identifies a batch of promising candidate nodes using the in-memory PQ vectors, issues asynchronous parallel read requests to the NVMe drive for all those nodes simultaneously, and processes them together. By overlapping the SSD IO wait times, DiskANN hides the hardware latency, maintaining search latencies under 5-10ms for billion-scale datasets.

## Q6: Derive the Scalar Quantization (SQ8) formula for a single dimension. What is the maximum quantization error? How does SIMD integer arithmetic make SQ8 queries faster than float32?

Scalar Quantization (SQ8) maps continuous 32-bit floating-point values into discrete 8-bit integers (0 to 255) independently for each dimension. To derive the formula, we first find the minimum (`min_val`) and maximum (`max_val`) values across a specific dimension for the entire dataset.

The quantization formula is:
```python
range_val = max_val - min_val
scale = 255.0 / range_val
quantized_x = round((x - min_val) * scale)
```
Where `quantized_x` is bounded between 0 and 255 and cast to an `uint8`. The dequantization formula used during asymmetric distance computation is:
```python
approx_x = (quantized_x / scale) + min_val
```

The maximum quantization error for a single dimension is half the step size between discrete integer bins. Since the total range is divided into 255 intervals, the maximum error is `(max_val - min_val) / 510`. If `max_val = 1.0` and `min_val = -1.0`, the max error per dimension is `2.0 / 510 ≈ 0.0039`.

SIMD (Single Instruction, Multiple Data) makes SQ8 extremely fast because modern CPUs (using AVX2 or AVX-512) can process many 8-bit integers in a single clock cycle. While an AVX-512 register can hold sixteen 32-bit floats, it can hold sixty-four 8-bit integers. During an L2 or Inner Product distance calculation, the CPU uses specialized SIMD instructions (like `VPMADDUBSW` in x86) that multiply and add 8-bit integers into 16-bit or 32-bit accumulators in a single instruction. This results in a theoretical 4x memory bandwidth reduction and a massive boost in arithmetic throughput compared to float32 operations.

## Q7: Why has LSH been superseded by HNSW for dense embedding retrieval? What specific similarity metric still benefits from LSH (MinHash), and why can HNSW not be used for it?

Locality Sensitive Hashing (LSH) was historically popular for approximate nearest neighbor search. It works by projecting vectors through multiple random hash functions (like random hyperplanes) such that similar vectors fall into the same hash buckets with high probability. However, for dense embeddings (like those from BERT or OpenAI models), LSH suffers from the "curse of dimensionality" much more severely than graph-based methods. To achieve high recall with dense vectors, LSH requires an exponential number of hash tables, completely blowing up memory and query times. HNSW superseded it because graph traversal natively follows the local manifold of the dense vector space, achieving O(log N) lookup time and >95% recall with much less memory overhead.

Despite this, LSH—specifically MinHash—remains the gold standard for Jaccard similarity on sparse, high-dimensional sets (e.g., document deduplication based on n-gram overlapping). In MinHash, a document is represented as a set of token hashes. MinHashing computes the minimum hash value across multiple random permutations, creating a signature where the probability of two signatures matching exactly equals their Jaccard similarity.

HNSW cannot be used effectively for Jaccard similarity of sets because Jaccard similarity does not behave like a continuous metric space distance (like L2 or Cosine). In sparse boolean vector spaces (where dimensionality can be in the millions, but with few non-zeros), graph structures become incredibly disconnected or overwhelmingly dense. MinHash LSH handles this sparsity naturally, allowing rapid O(1) bucket lookups to find overlapping sets, completely bypassing the need to traverse a continuous geometric space.

## Q8: What is recall@K? Write a Python function to compute it. What recall@10 threshold is considered production-ready for a RAG system, and what justifies accepting lower recall?

Recall@K measures the proportion of relevant ground-truth neighbors that are successfully retrieved in the top K results returned by the approximate nearest neighbor algorithm. If the exact brute-force search returns a set of K true nearest neighbors, and the ANN index returns a set of K approximate neighbors, recall@K is the size of the intersection of these two sets divided by K.

```python
def compute_recall_at_k(exact_results, ann_results, k=10):
    """
    exact_results: list of lists, ground truth indices for N queries
    ann_results: list of lists, ANN predicted indices for N queries
    """
    total_recall = 0.0
    num_queries = len(exact_results)
    
    for exact, ann in zip(exact_results, ann_results):
        # Take top K from both sets
        exact_k = set(exact[:k])
        ann_k = set(ann[:k])
        
        # Calculate intersection
        intersection = exact_k.intersection(ann_k)
        total_recall += len(intersection) / k
        
    return total_recall / num_queries
```

For a typical Retrieval-Augmented Generation (RAG) system, a recall@10 threshold of 90% to 95% is considered production-ready. 

Accepting lower recall (e.g., 75-80%) is justified in multi-stage retrieval pipelines. In these systems, the vector database serves only as the first-stage retriever (L1). The L1 retriever fetches a larger candidate pool (e.g., top 100), and a slower, more accurate cross-encoder (L2 reranker) re-scores them. Since the vector embeddings themselves are imperfect representations of semantic intent, prioritizing extreme ANN recall has diminishing returns. Lowering the recall target allows for massive cost savings (using IVF+PQ instead of HNSW, or reducing `ef_search`), while the LLM or reranker compensates for the missing 5-10% of mathematically closest vectors.

## Q9: Explain ScaNN's anisotropic vector quantization. What is the mathematical decomposition of quantization error into parallel and perpendicular components? Why does minimizing parallel error matter more for MIPS?

ScaNN (Scalable Nearest Neighbors), developed by Google, introduces Anisotropic Vector Quantization to solve a critical flaw in standard Product Quantization when using Maximum Inner Product Search (MIPS). Standard PQ uses k-means, which minimizes the overall Mean Squared Error (MSE) between the original vector and its quantized centroid. However, for inner product, not all errors are equal.

Mathematically, the quantization error vector `e = x - x_tilde` (where `x` is the true vector and `x_tilde` is the quantized vector) can be decomposed into two orthogonal components relative to `x`:
1. The parallel error `e_parallel`: The projection of the error vector onto the direction of `x`.
2. The perpendicular error `e_perp`: The component of the error orthogonal to `x`.

When computing the inner product with a query `q`, the error in the dot product is `dot(q, e)`. If `q` is roughly aligned with `x` (which is true when `x` is a true top-k neighbor of `q`), the magnitude of `x_tilde` dramatically impacts the inner product score. Standard PQ often selects a centroid that minimizes total distance but shrinks the vector's magnitude, destroying its inner product rank. 

ScaNN's anisotropic loss function explicitly penalizes `e_parallel` much more heavily than `e_perp`. By doing so, it forces the quantized vector `x_tilde` to retain the original magnitude and directional norm of `x`. Minimizing parallel error matters more for MIPS because the inner product is highly sensitive to vector length. Preserving the exact magnitude ensures that when a query aligns with the vector, the dot product isn't artificially deflated, allowing ScaNN to achieve much higher recall for MIPS workloads than standard PQ.

## Q10: How do you select nlist and nprobe for an IVF index? Give the sqrt(N) rule of thumb. Show the recall-QPS trade-off equation: what fraction of the dataset is scanned at a given nprobe?

In an Inverted File (IVF) index, the vector space is partitioned into `nlist` Voronoi cells (clusters). During a search, the query is compared against the centroids of these cells, and only the vectors within the top `nprobe` cells are scanned.

The standard rule of thumb for choosing `nlist` is the square root of the dataset size `N`. 
`nlist = floor(sqrt(N))`
For a dataset of 1,000,000 vectors, `nlist` should be roughly 1,000. This balances the overhead of comparing the query to the centroids (which is O(nlist)) with the time spent scanning the contents of the clusters (which is O(N/nlist)). If `nlist` is too small, clusters are massive, acting like a brute-force search. If `nlist` is too large, the index takes too long to identify the nearest centroids, and memory overhead for empty clusters grows.

The fraction of the dataset scanned is deterministically governed by `nprobe / nlist`. If `nlist = 1000` and `nprobe = 10`, you are scanning `10 / 1000 = 1%` of the total vectors.

The recall-QPS trade-off is directly tied to `nprobe`. 
Increasing `nprobe` linearly increases the number of distance computations: `Cost = O(nlist) + O((N/nlist) * nprobe)`. 
As `nprobe` goes up, QPS drops proportionally, but recall increases asymptotically. However, the recall gain diminishes rapidly. Moving `nprobe` from 1 to 10 might boost recall from 40% to 85%, while moving it from 10 to 100 might only boost it from 85% to 95%, costing 10x the compute for a 10% gain.

## Q11: Explain binary quantization for vectors. Write the numpy binarization code. Calculate the Hamming distance via XOR+POPCOUNT. Why is a two-stage (binary retrieval + float re-rank) approach necessary?

Binary Quantization (BQ) is the most extreme form of vector compression. It converts 32-bit floating-point vectors into a sequence of bits by thresholding them, usually around zero. If a floating-point value is greater than 0, it becomes a 1; if less than or equal to 0, it becomes a 0. A 1536-dimensional float32 vector (6144 bytes) is thus compressed into 1536 bits (192 bytes), achieving a 32x compression ratio.

```python
import numpy as np

def binarize_vectors(vectors):
    """
    vectors: numpy array of shape (N, D)
    Returns packed uint8 arrays
    """
    # Threshold at 0, resulting in boolean array
    boolean_mask = vectors > 0
    
    # Pack 8 booleans into a single uint8
    packed_bits = np.packbits(boolean_mask, axis=-1)
    return packed_bits
```

Distance between binary vectors is calculated using the Hamming distance, which counts the number of differing bits. At the hardware level, this is heavily optimized using an XOR operation followed by a POPCOUNT (population count). XORing two bitstrings yields a 1 where the bits differ, and POPCOUNT efficiently counts those 1s. A modern CPU can execute POPCOUNT on 64-bit or 256-bit registers in a single cycle, resulting in tens of billions of distance computations per second.

A two-stage approach (binary retrieval + float re-rank) is absolutely necessary because BQ destroys magnitude and fine-grained directional information. BQ alone typically yields catastrophic recall (e.g., recall@10 around 30-50%). In a two-stage system, BQ is used to rapidly scan millions of vectors and retrieve an oversized candidate pool (e.g., top 1000). Then, the original uncompressed float32 vectors for those 1000 candidates are fetched from memory and re-ranked using exact Cosine or L2 distance. This provides the best of both worlds: ultra-fast scanning and high final recall.

## Q12: How does HNSW handle concurrent inserts in a production system? What graph invariants must be maintained? Why do deletions require special handling?

Handling concurrent inserts in HNSW requires careful synchronization because the graph topology is constantly mutating. In a production system (like Milvus or Qdrant), HNSW typically implements fine-grained locking (e.g., read-write spinlocks at the node level) rather than a global lock. When a new vector is inserted, the algorithm searches for the nearest neighbors to form connections. The search phase is lock-free or read-locked. Once neighbors are identified, write locks are acquired exclusively on the new node and the target neighbor nodes to update their adjacency lists.

Several graph invariants must be maintained. First, the bidirectional nature of the edges must be preserved (if A points to B, B points to A) unless memory optimizations dictate a directed graph. Second, the maximum degree constraints (`M` and `M_max0`) must be strictly enforced. If connecting a new node causes an existing node's edge list to exceed `M`, the existing node must apply a pruning heuristic (maintaining the diversity of its connections) and discard its worst edge. This pruning operation must be atomic.

Deletions require special handling because simply removing a node severs paths through the graph, potentially destroying the "navigable small world" property. If a central hub node is deleted, search algorithms might get stuck in isolated clusters (graph partitioning). Therefore, production HNSW implementations rarely do physical deletion immediately. Instead, they use a "tombstone" boolean flag (soft delete). During a search, tombstoned nodes are used for routing but excluded from the final result set. A background garbage collection process periodically rebuilds or restructures the graph to physically remove tombstones and patch the broken edges, ensuring graph integrity is maintained.

## Q13: Given a p99 latency SLA of 50ms for ANN search on 5M HNSW vectors, how would you choose ef_search? Describe the benchmarking methodology: measurement setup, percentile calculation, load simulation.

To guarantee a p99 latency SLA of 50ms, tuning `ef_search` requires empirical benchmarking, as latency is hardware and dataset-dependent. `ef_search` linearly scales query time, so the goal is to find the maximum `ef_search` that keeps the 99th percentile of query latencies under 50ms, maximizing recall without breaching the SLA.

**Benchmarking Methodology:**
1. **Measurement Setup:** Deploy the vector database on production-equivalent hardware (same CPU architecture, memory bandwidth, network topology). Load the exact 5M HNSW vectors and ensure the index is fully built and loaded into RAM to avoid cold-start page faults. Disable caching, as cache hits artificially deflate tail latency.
2. **Load Simulation:** Use a concurrent load testing tool (like `ghz` for gRPC or a custom multi-threaded Python script) to simulate the expected production query volume (e.g., 500 QPS). The queries used must be a representative holdout set of real user embeddings, not random noise, as random vectors traverse the graph differently.
3. **Execution and Percentile Calculation:** Run the test for several minutes for a given `ef_search` (e.g., start at `ef_search=50`). Record the end-to-end latency of every single request. Sort the latency array and extract the 99th percentile value (the latency at index `0.99 * len(latencies)`). 
4. **Tuning Loop:** If the p99 latency is 20ms, increase `ef_search` to 100. If it climbs to 60ms, step it down to 80. By performing a binary search on the `ef_search` parameter under sustained load, you identify the exact threshold (e.g., `ef_search=85`) that stabilizes at a p99 of ~45ms, leaving a 5ms buffer for network jitter.

## Q14: When is GPU-accelerated brute-force search preferable to CPU HNSW? Calculate the GPU throughput for batch=1000 queries on A100 at 5M float32 1536-dim vectors.

GPU-accelerated brute-force search (often using exact flat indices like FAISS `IndexFlatL2`) is preferable to CPU HNSW when:
1. 100% absolute perfect recall is strictly required (e.g., medical diagnoses, cryptographic matching).
2. The query workload naturally arrives in massive batches (offline batch processing, re-indexing).
3. The dataset is relatively small (< 10-20 million vectors) and fits entirely within the GPU VRAM.

For 5M float32 vectors at 1536 dimensions, the database takes `5,000,000 × 1536 × 4 bytes ≈ 30.7 GB`, which comfortably fits into the 40GB or 80GB VRAM of an NVIDIA A100.

**Throughput Calculation:**
A single brute force search requires calculating the distance between the query and all 5M database vectors. For a batch of 1000 queries, this is a massive matrix multiplication (GEMM).
Query matrix (1000 × 1536) multiplied by Database matrix (1536 × 5,000,000).
Total floating-point operations (FLOPs) = `1000 × 1536 × 5,000,000 × 2` (multiply and add) = ~15.36 Trillion FLOPs (15.36 TFLOPs).

An NVIDIA A100 SXM4 delivers roughly 19.5 TFLOPS of standard FP32 throughput (and up to 156 TFLOPS if using Tensor Cores with TF32).
Assuming standard FP32 and ~70% achievable utilization (due to memory bandwidth overheads in GEMM), the effective compute is `19.5 × 0.7 = 13.65 TFLOPS/sec`.
Time to process the batch = `15.36 TFLOPs / 13.65 TFLOPS/sec ≈ 1.12 seconds`.
Throughput = `1000 queries / 1.12 seconds ≈ 892 QPS`.
While HNSW on CPU might achieve higher single-query QPS with lower latency, the GPU perfectly executes the math with zero indexing overhead and 100% recall.

## Q15: What is the build time complexity of HNSW: O(N × M × log N)? Explain why doubling M more than doubles build time. What is the memory breakdown of a complete HNSW index?

The theoretical build time complexity of HNSW is often stated as `O(N × log N)` for a fixed `M`, but fully expanded, it is heavily dependent on `M` and `ef_construction`. A more accurate representation is `O(N × ef_construction × log N)`. 

Doubling `M` more than doubles the build time due to the heuristic pruning process that occurs during insertion. When a node is inserted, it finds candidates up to `ef_construction`. Then, it must select `M` edges from these candidates. HNSW uses a specialized spatial diversity heuristic to pick these edges, which involves computing distances between the candidates themselves, not just the query. As `M` increases, the edge lists of existing nodes fill up faster. When an existing node's connections exceed `M_max`, it must trigger a re-evaluation of its entire adjacency list to prune an edge, causing a cascading effect of expensive distance calculations. Thus, the relationship between `M` and build time is super-linear.

**Memory Breakdown of a Complete HNSW Index (N=1M, D=128 float32, M=16):**
1. **Raw Vector Data:** 1,000,000 × 128 dims × 4 bytes = 512 MB.
2. **Layer 0 Graph:** Each node has up to `2*M = 32` edges. 32 edges × 4 bytes (integer node IDs) = 128 bytes per node. Total = 128 MB.
3. **Higher Layers Graph:** Due to the exponential decay `exp(-ml)`, the total number of edges in all higher layers combined is roughly equivalent to `M` edges per node in the dataset. 16 edges × 4 bytes = 64 bytes per node. Total = 64 MB.
4. **Metadata (Locks, state flags, level arrays):** ~24 bytes per node. Total = 24 MB.
Total memory footprint is ~728 MB, where the graph topology itself consumes about ~216 MB (nearly 40% of the raw data size).

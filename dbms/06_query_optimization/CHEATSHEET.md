# Query Optimization Cheatsheet

## EXPLAIN ANALYZE Fields

| Field | Description | Formula / Note |
|---|---|---|
| cost | Planner's estimate of the plan cost | `startup_cost .. total_cost` |
| rows | Estimated/Actual number of rows | Planner vs Execution actuals |
| width | Average width of rows in bytes | Affects memory and network |
| loops | Number of times a node is executed | Multiply actual rows/time by loops |
| time | Actual time spent (ms) | `startup_time .. total_time` |
| buffers | Memory/Disk block usage | 1 block = 8KB (usually). Hits vs Reads. |

## Join Algorithms

| Algorithm | Complexity | Best For | Requirement |
|---|---|---|---|
| Nested Loop | O(N * M) | Small outer relation, indexed inner | Fast inner index lookup |
| Hash Join | O(N + M) | Unsorted large sets | `work_mem` > Hash table size |
| Merge Join | O(N log N + M log M) | Large pre-sorted relations | Equi-joins, sortable data types |

## Optimization Rules
1. Never use functions on indexed columns (Non-SARGable)
2. Use Keyset Pagination instead of OFFSET/LIMIT
3. Use Covering Indexes (INCLUDE) to enable Index-Only Scans
4. Fix N+1 queries by using JOINs
5. Always run ANALYZE after massive data changes

## work_mem and Spilling

- **work_mem**: Maximum amount of memory to be used by query operations (sorts, hash tables) before writing to temporary disk files.
- **Temp Files**: When `work_mem` is exceeded, operations spill to disk (temp files).
- **Formula**: `Max Memory per Connection = work_mem * (concurrent sorts/hashes)`

## Common Slow Query Patterns and Fixes

| Anti-Pattern | Solution |
|---|---|
| Non-SARGable predicates (e.g., `WHERE YEAR(date) = 2023`) | SARGable predicates (e.g., `WHERE date >= '2023-01-01'`) |
| OFFSET/LIMIT pagination | Keyset pagination (`WHERE id > last_id`) |
| Missing covering index | Add `INCLUDE` columns to index |
| Uncorrelated subqueries causing N+1 | Rewrite as `JOIN` or `EXISTS` |
| Corrupt statistics | Run `ANALYZE` or adjust `default_statistics_target` |

## Partitioning Types

1. **Range**: Partition by continuous ranges (e.g., dates).
2. **List**: Partition by discrete values (e.g., region codes).
3. **Hash**: Partition by a modulus and remainder.

## Cost Model Parameters

- `seq_page_cost`: 1.0 (default)
- `random_page_cost`: 4.0 (default, lower to 1.1 on SSD)
- `cpu_tuple_cost`: 0.01 (default)
- `cpu_index_tuple_cost`: 0.005 (default)
- `cpu_operator_cost`: 0.0025 (default)

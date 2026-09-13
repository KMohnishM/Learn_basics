# Producers Cheatsheet

## Key Producer Configurations

| Configuration | Default | Description |
|---|---|---|
| `bootstrap.servers` | N/A | List of broker host:port pairs to establish initial connection. |
| `acks` | `all` (since v3.0) | `0` (none), `1` (leader only), `all` (leader + ISR). Controls durability. |
| `retries` | `MAX_INT` | Number of times to retry transient errors. |
| `enable.idempotence`| `true` (since v3.0) | Ensures exactly-once delivery per partition during retries. |
| `batch.size` | `16384` (16KB) | Max size of a batch in bytes. Larger = better compression. |
| `linger.ms` | `0` | Milliseconds to wait before sending a partially filled batch. |
| `compression.type` | `none` | Options: `gzip`, `snappy`, `lz4`, `zstd`. |
| `buffer.memory` | `33554432` (32MB)| Total memory used by RecordAccumulator to buffer outgoing data. |
| `max.block.ms` | `60000` (60s) | How long `send()` blocks if buffer is full or metadata is unavailable. |
| `delivery.timeout.ms`| `120000` (120s)| Max time a message has to be successfully delivered (includes retries). |
| `key.serializer` | N/A | Class used to serialize the key to bytes. |
| `value.serializer` | N/A | Class used to serialize the value to bytes. |

## Batching and Compression Trade-offs

| Scenario | `linger.ms` | `batch.size` | Compression | Result |
|---|---|---|---|---|
| **Low Latency** (e.g., stock trades) | `0` | Default | None / Snappy | Messages sent immediately. Low throughput, high network IO. |
| **High Throughput** (e.g., logs, analytics) | `5` to `100` | `65536` or higher | Zstd / LZ4 | Messages heavily batched. Excellent network efficiency, lower storage costs, slight latency penalty. |

## Producer Flow

1. **`send(record)`**: Application calls send.
2. **Serialization**: Key and Value are converted to byte arrays.
3. **Partitioning**: 
   - Has Key? -> Hash(Key) % num_partitions
   - No Key? -> Sticky Partitioning (stays on one partition until batch is full).
4. **RecordAccumulator**: Message is appended to a batch for the target partition.
5. **Sender Thread**: Background thread wakes up when batch is full OR `linger.ms` expires.
6. **Network IO**: Batch is sent to the target Broker (Leader for that partition).
7. **Callback/Future**: Success or Exception is returned to the application.

# Kafka Consumer Cheatsheet

## Key Consumer Configurations

| Property | Default | Description |
| :--- | :--- | :--- |
| `group.id` | "" | Unique string identifying the consumer group. Mandatory for offset management. |
| `bootstrap.servers` | "" | Comma-separated list of broker host:port pairs. |
| `enable.auto.commit` | `true` | If true, offsets are committed periodically in the background. |
| `auto.commit.interval.ms` | `5000` | Frequency of auto-commits if `enable.auto.commit` is true. |
| `auto.offset.reset` | `latest` | Action when no initial offset exists: `earliest`, `latest`, `none`. |
| `fetch.min.bytes` | `1` | Minimum amount of data the broker should return for a fetch request. |
| `fetch.max.wait.ms` | `500` | Maximum time broker waits to fill `fetch.min.bytes` before responding. |
| `max.partition.fetch.bytes` | `1048576` (1MB) | Maximum amount of data per partition the server will return. |
| `session.timeout.ms` | `45000` | Time coordinator waits for a heartbeat before marking consumer dead. |
| `heartbeat.interval.ms` | `3000` | Frequency of heartbeats. Should be <= 1/3 of `session.timeout.ms`. |
| `max.poll.interval.ms` | `300000` (5m) | Max time between `poll()` calls before consumer proactively leaves group. |
| `max.poll.records` | `500` | Maximum number of records returned in a single call to `poll()`. |
| `partition.assignment.strategy` | `RangeAssignor` | Class name of the partition assignor strategy. |

---

## Rebalance Strategies Comparison

| Strategy | Logic | Balance | Rebalance Impact | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Range (Default)** | Divides partitions for each topic separately. | Poor (if multiple topics) | High (Eager) | Simple use cases, single topic. |
| **RoundRobin** | Distributes all partitions across all topics evenly. | Excellent | High (Eager) | Multiple topics, uniform consumption. |
| **Sticky** | Balances like RoundRobin, minimizes movement. | Excellent | Medium (Eager) | Reducing state teardown/rebuild. |
| **CooperativeSticky**| Uses Incremental Cooperative protocol. | Excellent | Low (Incremental) | Production default. No stop-the-world. |

---

## Commit API Summary

```java
// 1. Synchronous Commit (Blocking)
consumer.commitSync();

// 2. Asynchronous Commit (Non-Blocking)
consumer.commitAsync();

// 3. Asynchronous Commit with Callback
consumer.commitAsync(new OffsetCommitCallback() {
    @Override
    public void onComplete(Map<TopicPartition, OffsetAndMetadata> offsets, Exception exception) {
        if (exception != null) {
            log.error("Commit failed for offsets {}", offsets, exception);
        }
    }
});

// 4. Committing Specific Offsets
Map<TopicPartition, OffsetAndMetadata> currentOffsets = new HashMap<>();
currentOffsets.put(new TopicPartition("topic", 0), new OffsetAndMetadata(100L));
consumer.commitSync(currentOffsets);
```

---

## Troubleshooting Consumer Lag

1. **Check consumer state:** Are consumers actively polling? Check logs for heartbeat failures or rebalance loops.
2. **Review `max.poll.interval.ms`:** If processing takes too long, consumers will be kicked out, causing endless rebalances and lag.
3. **Analyze processing time:** Profile your application to ensure message processing isn't the bottleneck.
4. **Scale out:** Add more consumer instances (up to the partition count).
5. **Check network/resources:** Ensure the consumer machine has adequate CPU, memory, and network bandwidth.

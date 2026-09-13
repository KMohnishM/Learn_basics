# CHEATSHEET: Messaging, Queues, and Streaming

## SQS Quick Reference

| Parameter | Default | Min / Max | Description |
|---|---|---|---|
| **Visibility Timeout** | 30 sec | 0 sec / 12 hours | Time message is hidden while being processed. |
| **Message Retention** | 4 days | 1 min / 14 days | Time message stays in queue if not deleted. |
| **WaitTimeSeconds** | 0 sec | 0 sec / 20 sec | Long polling duration. (>0 = Long Polling). |
| **Delivery Delay** | 0 sec | 0 sec / 15 min | Delay before message becomes visible. |

## SQS Standard vs FIFO

| Feature | Standard Queue | FIFO Queue (`.fifo`) |
|---|---|---|
| **Ordering** | Best-effort | Strict order (in message group) |
| **Delivery** | At-least-once (duplicates possible)| Exactly-once (deduplication) |
| **Throughput** | Unlimited | 300/s (3,000/s with batching) |

## Event Routing Decision Matrix

| Service | Best For | Architecture Model | Key Features |
|---|---|---|---|
| **SQS** | Worker queues, task offloading | Point-to-Point (Pull) | DLQ, visibility timeout, batching |
| **SNS** | High throughput fan-out, SMS/Email | Pub/Sub (Push) | Massive scale, simple attribute filters |
| **EventBridge**| Complex routing, SaaS integration | Event Bus (Push) | JSON payload filtering, Schema registry |
| **Kinesis** | Real-time big data, replayability | Stream (Pull/Push) | Shards, partition keys, 24h+ retention |

## Fan-Out Architecture (ASCII)

```text
                  +---> SQS Queue (Inventory) ---> Lambda Worker
                  |
Publisher ---> SNS Topic ---> SQS Queue (Billing) ---> ECS Task
                  |
                  +---> SQS Queue (Shipping) ---> EC2 Worker
```
*Why? Provides decoupled, durable buffer for downstream services.*

## Kinesis Data Streams vs Firehose

| Feature | Kinesis Data Streams | Kinesis Data Firehose |
|---|---|---|
| **Real-time?** | Yes (~70ms latency) | Near real-time (min 60s buffer) |
| **Management** | Manage Shards (capacity planning) | Fully managed (auto-scales) |
| **Data Storage** | Retained 1-365 days (replayable) | None (routes data to destination) |
| **Destination** | Custom code (KCL, Lambda) | S3, Redshift, OpenSearch, Splunk |

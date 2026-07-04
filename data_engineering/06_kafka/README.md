# Module 6: Event Streaming with Apache Kafka

Unlike traditional message queues (which delete messages once read), Kafka is an **immutable, distributed commit log**.
Events are appended to the end of a log. Consumers read the log. The log is kept on disk for a retention period (e.g., 7 days).

## 1. Core Architecture
- **Broker**: A single Kafka server. A Kafka cluster consists of multiple brokers.
- **Topic**: A logical category of events (like a database table). e.g., `user_clicks`.
- **Partition**: Topics are split into Partitions. This allows a single topic to be hosted across multiple brokers for massive scale. If `user_clicks` has 3 partitions, Broker A might host Partition 0, Broker B hosts Partition 1, etc.
- **Replica**: For fault tolerance, partitions are copied to multiple brokers. One broker is the "Leader" for a partition, others are "Followers".

## 2. Producers
Producers send data to topics. 
By default, Kafka uses a round-robin algorithm to distribute messages across partitions. 
However, if you provide a **Message Key** (e.g., `user_id`), Kafka guarantees that all messages with the same key will ALWAYS go to the same partition. This is critical for ordering (e.g., ensuring a user's "checkout" event is processed after their "add_to_cart" event).

## 3. Consumers and Consumer Groups
Consumers read from partitions. 
A **Consumer Group** is a set of consumers cooperating to consume a topic. 
- Rule: **One partition can only be read by ONE consumer in a group at a time.**
- If a topic has 4 partitions, and your group has 4 consumers, each gets 1 partition.
- If your group has 5 consumers, 1 will sit completely idle. (You cannot scale consumers beyond the number of partitions).

## 4. Offsets
How does a consumer know where it left off? Kafka assigns a sequential ID called an **Offset** to every message in a partition.
When a consumer reads a message, it "commits" its offset back to Kafka (essentially saving its progress). If the consumer crashes, the new consumer looks up the last committed offset and resumes from there.

## 5. Kafka vs RabbitMQ
- **RabbitMQ**: Smart broker, dumb consumers. The broker tracks who got what message. Good for complex routing.
- **Kafka**: Dumb broker, smart consumers. The broker just appends bytes to disk very fast. The consumers are responsible for tracking their own offsets. Unbeatable for high throughput (millions of messages per second).

---
## Next Steps
Go to `labs/` to spin up a Kafka cluster and write your first streaming Producer and Consumer!

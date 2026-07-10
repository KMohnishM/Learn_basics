# Module 5: Message Queues & Event Streaming

When Services A and B talk directly via HTTP (Synchronous communication), you have a problem:
If Service B goes down, Service A fails. If Service B is slow, Service A hangs. If traffic spikes 100x, Service B is crushed.

The solution is **Asynchronous Communication** using an intermediary: a Message Queue or an Event Stream.

## 1. Message Queues (RabbitMQ, SQS)
A Message Queue is like an email inbox.
- **Producer** sends a message to the queue.
- **Consumer** reads the message from the queue, processes it, and then *acknowledges* it.
- Once acknowledged, the message is **DELETED** from the queue forever.
- Great for: Task distribution (e.g., sending emails, processing video uploads). If you have 5 consumers, the queue will round-robin the tasks so each consumer gets a fair share of the work.

## 2. Event Streams (Apache Kafka)
An Event Stream is like a distributed log file on disk.
- **Producer** appends an event to the log.
- **Consumers** read from the log.
- Crucially, reading a message **DOES NOT DELETE IT**. The message stays on disk for a configured retention period (e.g., 7 days).
- Because messages aren't deleted, multiple different consumer groups can read the exact same data at their own pace.
- Great for: Streaming analytics, system-wide state replication, event sourcing.

## 3. Delivery Guarantees
- **At-most-once**: Fire and forget. Fast, but messages might be lost.
- **At-least-once**: The standard. If a consumer crashes halfway through processing, the message is put back on the queue to be tried again. This guarantees delivery, but means a message might be processed twice. *Your consumers MUST be idempotent to handle this.*
- **Exactly-once**: The holy grail. Extremely hard to achieve. Requires distributed transactions (e.g., Kafka Transactions).

## 4. Dead Letter Queues (DLQ)
What happens if a user submits an invalid order, and your consumer crashes every time it tries to process it?
Because of "At-least-once" delivery, the queue will retry the message forever, blocking all other messages. This is a "Poison Pill".
**Solution**: A DLQ. If a message fails 5 times, route it to a special "Dead Letter Queue". The main queue keeps moving, and an engineer can manually inspect the DLQ later to see why the message failed.

## 5. The Outbox Pattern
Imagine an e-commerce checkout. You must:
1. Save the order to your Postgres DB.
2. Publish an "OrderCreated" event to RabbitMQ.
If step 1 succeeds but step 2 fails, your system is inconsistent. (Dual-write problem).

**Solution (The Outbox Pattern)**:
1. Save the order to the `orders` table AND save the event to an `outbox` table in the *same Postgres transaction*. (Atomic).
2. A separate background process constantly polls the `outbox` table and publishes those events to RabbitMQ.

---
## Next Steps
Go to `labs/` to spin up RabbitMQ and build a producer/consumer architecture!

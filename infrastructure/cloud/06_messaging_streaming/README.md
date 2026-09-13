# Module 6: Messaging, Queues, and Streaming

## SQS (Simple Queue Service)
Fully managed message queuing service for decoupling distributed systems and microservices. Uses a polling model (consumers pull messages).

### Queue Types
1.  **Standard Queue:**
    *   **Throughput:** Nearly unlimited API calls per second.
    *   **Delivery:** At-least-once delivery (messages might occasionally be delivered more than once).
    *   **Ordering:** Best-effort ordering (messages might arrive out of order).
2.  **FIFO (First-In-First-Out) Queue:**
    *   **Throughput:** 3,000 messages per second with batching (300 without).
    *   **Delivery:** Exactly-once processing (automatic deduplication).
    *   **Ordering:** Strict ordering. Messages are processed in the exact order they were sent.
    *   **Name requirement:** Queue name must end in `.fifo`.

### Key SQS Parameters
*   **Visibility Timeout:** When a consumer polls a message, the message becomes "invisible" to other consumers for this duration (default 30s, max 12 hours). 
    *   If the consumer processes the message successfully, it must call `DeleteMessage`.
    *   If the consumer crashes, the timeout expires, the message becomes visible again, and another consumer will process it.
    *   If processing takes longer than expected, the consumer can call `ChangeMessageVisibility` to extend the time.
*   **Message Retention Period:** How long SQS keeps the message if it's not deleted (1 min to 14 days; default 4 days).
*   **Delivery Delay:** Delay the initial visibility of a message when it enters the queue (0 to 15 minutes).
*   **Max Message Size:** 256 KB. If you need larger messages, use the Amazon SQS Extended Client Library, which stores the payload in S3 and puts a reference pointer in the SQS message.

### Polling Mechanisms
*   **Short Polling:** Returns immediately, even if the queue is empty. Costs money for empty API calls.
*   **Long Polling (`WaitTimeSeconds` 1-20s):** The SQS API waits up to 20 seconds for a message to arrive before returning an empty response. **Always prefer Long Polling.** It drastically reduces empty receives, saving money and reducing CPU cycles on the consumer.

### Dead Letter Queue (DLQ)
*   If a message repeatedly fails to process (e.g., due to a code bug throwing an exception), it will continuously reappear in the queue.
*   You configure a `maxReceiveCount`. Once a message is received this many times without being deleted, it is automatically moved to a DLQ.
*   **DLQ Redrive:** After fixing the bug, you can use DLQ Redrive to push the failed messages back to the source queue for reprocessing.
*   A Standard queue must use a Standard DLQ. A FIFO queue must use a FIFO DLQ.

### FIFO Message Deduplication
FIFO guarantees exactly-once processing using a 5-minute deduplication window.
*   **Content-Based Deduplication:** AWS creates a SHA-256 hash of the message body. If an identical body is sent within 5 mins, it's rejected.
*   **MessageDeduplicationId:** You provide a unique ID in the API call. Useful if the message body changes slightly but represents the same logical event.

---

## SNS (Simple Notification Service)
Fully managed Pub/Sub (Publish/Subscribe) service. Uses a push model.

*   **Pub/Sub Model:** A publisher sends *one* message to an SNS Topic. The topic immediately fans out (pushes) that message to *many* subscribers simultaneously.
*   **Supported Protocols (Subscribers):** SQS queues, Lambda functions, HTTP/HTTPS endpoints, Email, SMS text messages, Mobile Push (APNs, GCM), Kinesis Data Firehose.
*   **Message Filtering:** By default, a subscriber receives every message sent to the topic. With Subscription Filter Policies, the subscriber specifies rules (e.g., `{"status": ["error"]}`). SNS evaluates the message attributes and only pushes the message if it matches the filter. This offloads filtering logic from your downstream compute.
*   **FIFO Topics:** Similar to SQS FIFO, provides strict ordering and deduplication. *Limitation:* The only supported subscribers for an SNS FIFO topic are SQS FIFO queues.

### The SNS + SQS Fan-Out Pattern
A critical architectural pattern. 
1.  An event occurs (e.g., "Order Placed").
2.  The application publishes a single message to an SNS Topic.
3.  Multiple SQS queues are subscribed to the topic (e.g., InventoryQueue, ShippingQueue, BillingQueue).
4.  SNS pushes a copy of the message to all queues reliably.
5.  Independent worker services poll their respective queues at their own pace.
*Benefit:* Fully decoupled, highly resilient, and allows adding new downstream services (like a FraudDetectionQueue) without modifying the publisher code.

---

## EventBridge (formerly CloudWatch Events)
A serverless event bus that makes it easier to build event-driven applications at scale.

*   **Event Buses:**
    *   **Default Bus:** Receives events from AWS services (e.g., EC2 state change, S3 object creation).
    *   **Custom Bus:** Receives custom events published by your applications.
    *   **Partner Bus:** Receives events from SaaS providers (e.g., Datadog, Zendesk, Stripe) directly into your AWS account without webhooks.
*   **Rules:** You create rules that match incoming events using JSON patterns.
*   **Targets:** If an event matches a rule, it is routed to a target. Supports many more targets than SNS (Lambda, SQS, SNS, Step Functions, ECS tasks, Kinesis, API Gateway, cross-account/cross-region event buses).
*   **Schema Registry:** Can infer the schema of events traveling through the bus and generate strongly typed code bindings (Java, Python, TS) for your application, preventing parsing errors.
*   **EventBridge vs SNS:** EventBridge is preferred for complex routing, deep AWS integration, partner SaaS integrations, and advanced content filtering. SNS is preferred for high-throughput, simple fan-out, and human notifications (Email/SMS).

---

## Kinesis (Streaming Data)
Designed for collecting, processing, and analyzing real-time streaming data at massive scale.

### Kinesis Data Streams (KDS)
*   **Real-time streaming:** Data is available in milliseconds.
*   **Shards:** The base throughput unit. You must provision shards.
    *   1 Shard = 1 MB/sec or 1,000 records/sec IN (Write).
    *   1 Shard = 2 MB/sec OUT (Read).
*   **Retention:** Data is stored for 24 hours by default (up to 365 days). Consumers can replay data (go back in time), which SQS cannot do.
*   **Ordering:** Ordering is guaranteed *at the shard level* using a Partition Key.
*   **Consumers:** Can use Lambda, Kinesis Client Library (KCL) on EC2, or Kinesis Data Analytics.
*   **Enhanced Fan-Out:** Normally, consumers share the 2 MB/sec read limit per shard. With Enhanced Fan-Out, each consumer gets a dedicated 2 MB/sec pipe via HTTP/2 push, eliminating polling overhead and read throttling.

### Kinesis Data Firehose
*   **Near real-time (Not true real-time):** It buffers data before delivering it.
*   **Purpose:** Loads streaming data into data lakes, data stores, and analytics services (S3, Redshift, Amazon OpenSearch, Splunk, Datadog).
*   **Fully Managed:** No shards to manage, scales automatically.
*   **Transformation:** Can trigger a Lambda function to transform data (e.g., CSV to JSON) before loading it into the destination.
*   **Buffering:** Configured by size (1 - 128 MB) or time (60 - 900 seconds).

---

## AWS Step Functions
Serverless visual workflow orchestration service. Used to coordinate distributed components into a unified state machine.

*   **States:** Task (do work via Lambda/ECS), Choice (if/then branching), Wait (delay), Parallel (branch execution), Map (dynamic parallel loops), Succeed, Fail.
*   **Standard Workflows:** For long-running processes (up to 1 year). Exactly-once execution. Complete audit trail in console. Slower state transitions (2,000/sec).
*   **Express Workflows:** For high-volume, short-duration event processing (max 5 minutes). At-least-once execution. Logs to CloudWatch instead of keeping visual history. Fast (100,000/sec).
*   **Use Cases:** Saga pattern for distributed transactions, ETL orchestration, multi-step machine learning pipelines.

## GCP Equivalents

| AWS Service | GCP Equivalent |
| :--- | :--- |
| SQS | Cloud Pub/Sub (Pull subscription) |
| SNS | Cloud Pub/Sub (Push subscription) |
| EventBridge | Eventarc |
| Kinesis Data Streams | Cloud Pub/Sub / Dataflow |
| Step Functions | Workflows |

# QnA: Messaging, Queues, and Streaming

1. **What is SQS visibility timeout? What happens if your consumer crashes while processing a message?**
   Visibility timeout is a period during which a message polled by a consumer is "invisible" to other consumers in the queue. If a consumer crashes without deleting the message, the visibility timeout will eventually expire. Once it expires, the message becomes visible in the queue again, allowing another healthy consumer instance to poll and process it, ensuring messages are not lost.

2. **What is the difference between SQS Standard and FIFO queues? When must you use FIFO?**
   Standard queues offer at-least-once delivery, best-effort ordering, and massive throughput. FIFO (First-In-First-Out) queues offer exactly-once processing (deduplication), strict message ordering, and lower throughput (3,000/sec with batching). You must use FIFO for financial transactions or inventory updates where processing a message twice or out of order would corrupt the database state.

3. **What is the SNS + SQS fan-out pattern? Draw the architecture and explain why it's better than SNS alone.**
   The fan-out pattern involves a single SNS topic pushing messages to multiple SQS queues.
   `Publisher -> SNS Topic -> [SQS Queue A, SQS Queue B, SQS Queue C]`
   It is better than SNS alone because if downstream Service B goes offline, its SQS Queue B will safely hold the messages until the service comes back online. If you used SNS directly to HTTP endpoints without SQS, messages sent while the service was down would be permanently lost after retries are exhausted.

4. **What is SQS long polling and why is it preferred over short polling?**
   Short polling returns immediately, even if the queue is empty, resulting in high API costs and CPU overhead for empty responses. Long polling (`WaitTimeSeconds` > 0, up to 20s) tells the SQS API to hold the connection open until a message arrives or the timeout expires. It is heavily preferred because it drastically reduces empty API responses, lowering AWS costs and improving efficiency.

5. **What happens when a message fails processing repeatedly in SQS? How do you configure this behavior?**
   If a message repeatedly fails, the consumer code will error out, the visibility timeout will expire, and the message will return to the queue. This creates an infinite loop (a "poison pill"). You configure a Dead Letter Queue (DLQ) and set a `maxReceiveCount` (e.g., 3). If a message is received 3 times without being deleted, SQS automatically moves it to the DLQ for manual inspection and later redrive.

6. **What is the difference between SNS message filtering and processing all messages in the Lambda consumer?**
   If you process all messages in the Lambda consumer, your Lambda function is invoked for every event, and you pay for the compute time to execute `if (event.type !== 'target') return;`. By using SNS Subscription Filter Policies, the SNS service filters the messages based on attributes *before* delivery. Your Lambda is only invoked for relevant messages, significantly reducing Lambda costs and concurrent executions.

7. **When would you use EventBridge instead of SNS? What extra capabilities does it provide?**
   Use EventBridge when you need advanced content-based filtering (inspecting the actual JSON payload, not just attributes), when integrating with third-party SaaS applications (Partner Event Buses like Datadog/Stripe), or when building complex event-driven routing rules. SNS is better for simple, ultra-high throughput fan-out or when you need to send human-readable notifications (SMS/Email).

8. **What is Kinesis Data Streams vs Kinesis Data Firehose? Which is truly real-time?**
   Kinesis Data Streams (KDS) is truly real-time (milliseconds). You manage shards, write consumer code (KCL/Lambda), and can replay data. Kinesis Data Firehose is *near real-time* (buffered by time or size, e.g., minimum 60 seconds). Firehose is a fully managed delivery service designed specifically to load streaming data into destinations like S3, Redshift, or OpenSearch without writing consumer code.

9. **What is Kinesis enhanced fan-out and what problem does it solve?**
   Normally, all consumers sharing a Kinesis shard must share the 2 MB/sec read throughput limit, and they poll for data (which adds latency). Enhanced fan-out provides each registered consumer with its own dedicated 2 MB/sec read pipe, and AWS *pushes* data to the consumer using HTTP/2. It solves read throttling issues when multiple independent applications need to process the same stream in real time.

10. **When would you choose Kinesis over SQS for a streaming use case?**
    Choose Kinesis when you need to process a firehose of big data (e.g., clickstreams, IoT telemetry), require strict ordering at scale (via partition keys), need multiple independent consumers reading the exact same data, or require the ability to "replay" data from the past 24 hours. Choose SQS for standard worker-queue task offloading where messages are deleted after processing.

11. **What is an SQS DLQ? How does DLQ Redrive work?**
    A Dead Letter Queue (DLQ) isolates messages that cannot be processed successfully. DLQ Redrive is a feature that allows you to manage the lifecycle of these failed messages. Once you fix the code bug that caused the failure, you use the DLQ Redrive task in the console (or API) to automatically move the messages from the DLQ back to their original source queue to be reprocessed.

12. **Explain how EventBridge rules work. What is a partner event bus?**
    EventBridge rules use JSON event patterns to match incoming events on a bus and route them to one or more targets. A Partner Event Bus allows external SaaS platforms (like Zendesk, Auth0, Datadog) to publish events directly into your AWS account securely, without you having to build, host, and secure public-facing API Gateway webhooks to receive them.

13. **What are Step Functions Standard Workflows vs Express Workflows? When would you use each?**
    *   **Standard Workflows:** Max duration 1 year, exactly-once execution, full visual audit history. Use for long-running processes (e.g., manual approval steps, multi-day ETL jobs).
    *   **Express Workflows:** Max duration 5 minutes, at-least-once execution, logs to CloudWatch. Use for high-volume, short-duration orchestrations (e.g., IoT data ingestion, microservice coordination).

14. **Design a system where an S3 file upload triggers multiple independent downstream processing pipelines.**
    S3 Event Notifications do not support fanning out to multiple queues directly. I would configure the S3 bucket to send an Event Notification to a single **SNS Topic** (or an EventBridge Event Bus). I would then subscribe multiple **SQS Queues** (one for each independent pipeline, e.g., ImageResizerQueue, MetadataExtractorQueue) to that SNS topic. Independent Lambda functions or ECS tasks would then poll their respective SQS queues.

15. **What is the SQS deduplication window for FIFO queues and how does content-based deduplication work?**
    The SQS FIFO deduplication window is exactly 5 minutes. If content-based deduplication is enabled, SQS automatically calculates a SHA-256 hash of the message body. If a message with the exact same hash arrives within the 5-minute window, SQS assumes it is a retry duplicate and safely discards it, ensuring exactly-once processing.

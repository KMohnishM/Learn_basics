# Inter-Service Communication QnA

## 1. What is temporal coupling in synchronous communication? Give a concrete scenario where an Order Service synchronously calling a Payment Service causes a cascading failure during a traffic spike.
Temporal coupling occurs when two or more systems must be available and responsive at the exact same time to complete a transaction. Synchronous communication protocols, like HTTP/REST or gRPC, inherently introduce temporal coupling because the caller blocks and waits for the responder.
Consider an e-commerce platform during Black Friday. A user places an order. The Order Service synchronously makes an HTTP POST call to the Payment Service to authorize the credit card. During a massive traffic spike, the Payment Service's database slows down, increasing response times from 100ms to 5 seconds. Because of the temporal coupling, the Order Service's worker threads are now blocked for 5 seconds waiting for responses. The Order Service quickly runs out of available threads to handle new incoming requests. Consequently, the Order Service goes down, even though its own database and logic are fine. The failure in the Payment Service cascades upstream, resulting in a total system outage, illustrating the danger of synchronous calls in critical paths.

## 2. Why is gRPC preferred over REST for internal microservice communication? What specific features of Protocol Buffers and HTTP/2 make it faster? What are gRPCs limitations for public APIs?
gRPC is often preferred over REST for internal microservice-to-microservice communication due to its significant performance advantages, strict typing, and auto-generated client/server stubs. 
It achieves high performance primarily through two technologies: Protocol Buffers (protobuf) and HTTP/2. Protobuf is a highly efficient binary serialization format; unlike JSON text, it compresses data into small binary payloads, drastically reducing network bandwidth and CPU serialization/deserialization overhead. HTTP/2 provides multiplexing, allowing multiple concurrent requests and responses to be sent over a single persistent TCP connection, eliminating the latency of repeated TCP handshakes and head-of-line blocking found in HTTP/1.1.
However, gRPC has limitations for public APIs. Browsers do not natively support direct HTTP/2 framing required by gRPC, necessitating proxies like Envoy and gRPC-Web adapters. Furthermore, the binary payloads are not human-readable, making debugging via browser DevTools difficult compared to inspecting JSON payloads. Therefore, REST/JSON remains the standard for public-facing internet APIs.

## 3. What is the difference between a message queue (RabbitMQ/SQS) and event streaming (Kafka)? Give a specific use case where each is the better choice. What happens to a message after consumption in each?
Message queues (like RabbitMQ or AWS SQS) are designed for point-to-point asynchronous task distribution. They typically follow a "smart broker, dumb consumer" model. When a consumer reads a message from a queue and acknowledges it, the broker deletes the message. It is ephemeral. A classic use case is image processing: a web server drops a background task onto SQS; an idle worker pulls the task, processes the image, and acknowledges it. Once processed, the message is gone.
Event streaming platforms (like Apache Kafka) are designed for continuous, high-throughput log processing. They follow a "dumb broker, smart consumer" model. Kafka stores messages persistently in an append-only log on disk for a configured retention period (e.g., 7 days). Consumers track their own read position (offset). Multiple independent consumer groups can read the same stream of events at their own pace without destroying the data. A classic use case is user clickstream analytics or event sourcing, where multiple microservices need to react to the exact same stream of `UserClicked` events independently.

## 4. What is the Circuit Breaker pattern? Describe the three states (Closed, Open, Half-Open) with state transition conditions. What is the fallback strategy when the circuit is open?
The Circuit Breaker pattern prevents a system from repeatedly trying to execute an operation that is likely to fail, protecting failing downstream services from being overwhelmed and allowing them time to recover.
It operates in three distinct states:
1. Closed: Operations are executed normally. The circuit breaker monitors failures. If the failure rate (e.g., timeouts, 5xx errors) exceeds a predefined threshold within a specific time window, it transitions to the Open state.
2. Open: All requests are immediately rejected with an exception (fast-failure), without even attempting to call the downstream service. A timer is started.
3. Half-Open: When the timer expires, the circuit breaker allows a limited number of test requests to pass through to check if the downstream service has recovered. If these requests succeed, it transitions back to Closed. If they fail, it immediately returns to Open and resets the timer.
When the circuit is Open, a fallback strategy should be employed. Depending on the context, the fallback could be returning a cached response, returning a default empty value, or queuing the request for later asynchronous processing.

## 5. Explain retry with exponential backoff. Why is jitter important? What is the thundering herd problem that jitter prevents? Show a Python decorator implementing this.
Retry with exponential backoff is a strategy for handling transient network failures. Instead of retrying immediately, the client waits for a progressively longer delay between attempts (e.g., 1s, 2s, 4s, 8s). This prevents hammering a struggling server.
Jitter is the addition of randomness to the backoff duration. It is critical to prevent the "thundering herd" problem. If a downstream service drops offline, hundreds of clients might fail simultaneously and begin their retries at the exact same exponential intervals. Without jitter, they will all retry concurrently at 1s, then all at 2s, overwhelming the server the moment it comes back up. Jitter scatters the retries.
```python
import time
import random
import functools

def retry_with_backoff(retries=3, base_delay=1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        raise e
                    # Exponential backoff with jitter
                    sleep_time = delay + random.uniform(0, 0.5)
                    time.sleep(sleep_time)
                    delay *= 2
        return wrapper
    return decorator
```

## 6. What is an idempotency key? Why is it critical for payment APIs? Show a complete Python implementation using Redis to make a POST /payments/charge endpoint idempotent.
An idempotency key is a unique identifier provided by a client when making an API request. It guarantees that if the client sends the exact same request multiple times (e.g., due to network timeouts causing retries), the server will only process the operation once. This is absolutely critical for payment APIs. If a user clicks "Pay" and the network drops the response, their browser might retry the request. Without idempotency, the user's credit card would be charged twice.
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def charge_payment(request, idempotency_key):
    # 1. Check if we have already processed this key
    cached_response = redis_client.get(f"idempotency:{idempotency_key}")
    if cached_response:
        # Return the saved successful response immediately
        return json.loads(cached_response)

    # 2. Acquire a lock to prevent race conditions from concurrent identical requests
    lock_key = f"lock:{idempotency_key}"
    if not redis_client.set(lock_key, "locked", nx=True, ex=10):
        return {"error": "Concurrent request processing"}, 409

    try:
        # 3. Perform the actual business logic (charge the card via Stripe, etc.)
        payment_result = execute_payment_gateway(request)
        
        # 4. Save the result with an expiration (e.g., 24 hours)
        redis_client.setex(
            f"idempotency:{idempotency_key}", 
            86400, 
            json.dumps(payment_result)
        )
        return payment_result
    finally:
        redis_client.delete(lock_key)
```

## 7. What is the difference between Event Notification and Event-Carried State Transfer? What are the trade-offs of fat events (all data included) vs thin events (just IDs)?
Event Notification is a pattern where an event simply notifies consumers that something happened, carrying very little data. It's a "thin event." For example: `{"event": "CustomerUpdated", "customer_id": "123"}`. The consumer must then make a synchronous API call back to the producer to fetch the updated customer details.
Event-Carried State Transfer passes the complete state needed by consumers within the event itself. It's a "fat event." For example: `{"event": "CustomerUpdated", "customer_id": "123", "name": "Alice", "email": "alice@test.com"}`. 
Trade-offs: Thin events keep messaging queues lightweight and ensure consumers always fetch the most up-to-date state. However, they create temporal coupling and increase load on the producer's API, potentially causing bottlenecks. Fat events decouple systems entirely—consumers don't need to query the producer at all, enabling offline processing and CQRS. However, fat events use more bandwidth, risk data staleness if messages are delayed, and leak the producer's internal schema into the message contract.

## 8. What is service discovery? Compare client-side discovery (Consul) with server-side discovery (Kubernetes DNS). Which is simpler in a Kubernetes-native environment and why?
In microservices, instances dynamically scale up, scale down, and change IP addresses. Service discovery is the mechanism that allows one service to find the network location (IP and port) of another dynamically.
In client-side discovery (e.g., using HashiCorp Consul or Netflix Eureka), the calling service directly queries a service registry to obtain a list of available IP addresses for the target service. The client then implements its own load balancing algorithm (like round-robin) to choose an instance and makes the request directly.
In server-side discovery (e.g., Kubernetes DNS and Services), the client simply makes a request to a static hostname (e.g., `http://payment-service`). A router or load balancer intercepts this request, queries the registry, and forwards the traffic to an available instance.
Server-side discovery is much simpler in a Kubernetes-native environment. Kubernetes provides built-in DNS and `Service` resources that act as internal load balancers. Developers don't need to import complex discovery SDKs or write client-side load balancing logic; they simply rely on standard DNS resolution provided natively by the infrastructure.

## 9. What is the Bulkhead pattern? What resource exhaustion problem does it solve? How do separate connection pools or thread pools implement bulkheading in Python?
The Bulkhead pattern is a resilience strategy inspired by the watertight compartments (bulkheads) of a ship. If one compartment floods, the bulkheads prevent the entire ship from sinking. In software, it isolates elements of an application into pools so that if one fails or slows down, the others continue to function.
It solves the resource exhaustion problem. If a single microservice handles both critical user authentication requests and low-priority reporting requests, a slow database query in the reporting module could consume all available worker threads or database connections. This would cause authentication to fail, crashing the whole system.
In Python, this is implemented using isolated connection pools or thread pools.
```python
from concurrent.futures import ThreadPoolExecutor
import requests

# Bulkheading: Isolate pools based on criticality
critical_auth_pool = ThreadPoolExecutor(max_workers=20)
low_priority_report_pool = ThreadPoolExecutor(max_workers=5)

def handle_auth(user):
    # Guaranteed to have threads available even if reports are slow
    future = critical_auth_pool.submit(requests.post, "http://auth-service", data=user)
    return future.result()

def handle_report(query):
    # Limited to 5 threads; cannot exhaust the system
    future = low_priority_report_pool.submit(requests.get, "http://report-service", params=query)
    return future.result()
```

## 10. What is the difference between at-most-once, at-least-once, and exactly-once delivery semantics? Which is the default in Kafka? How do you achieve exactly-once with Kafka transactions?
These define the reliability guarantees of a message broker.
At-most-once (Fire and Forget): Messages are sent once and not retried on failure. Messages may be lost, but are never duplicated.
At-least-once: The producer waits for an acknowledgment. If it fails or times out, it retries. Messages are never lost, but may be delivered multiple times (duplicates).
Exactly-once: The holy grail of messaging. Messages are never lost and processed exactly once, regardless of network failures or crashes.
By default, Kafka provides at-least-once semantics. Producers retry on failure, and consumers commit offsets only after processing.
To achieve exactly-once semantics in Kafka, you must use the Kafka Transactions API. This allows a consumer-producer application (a stream processor) to atomically consume a message from a topic, process it, produce a result to an output topic, and commit the consumer offset, all within a single distributed transaction. If the application crashes midway, the entire transaction is aborted, preventing duplicate processing.

## 11. How does REST API versioning work in microservices? Compare URL versioning (/v1/orders), header versioning (Accept: application/vnd.api.v2+json), and query parameter versioning. Which is most widely used and why?
API versioning allows microservices to introduce breaking changes without breaking existing clients.
1. URL Versioning (URI Routing): The version is explicitly part of the path, e.g., `https://api.example.com/v1/orders`. This is the most widely used approach because it is incredibly explicit, cache-friendly, easy to implement in standard API gateways, and allows clients to easily inspect the version in browser network tabs.
2. Header Versioning (Content Negotiation): The version is passed via standard or custom HTTP headers, e.g., `Accept: application/vnd.mycompany.v2+json`. REST purists prefer this because the URL represents the resource, and the resource hasn't changed, only its representation. However, it is harder to cache at the CDN level and difficult to test via a simple browser URL bar.
3. Query Parameter Versioning: The version is passed as a query string, e.g., `https://api.example.com/orders?version=2`. This is easy to implement but often frowned upon as query parameters are typically used for filtering or pagination, not defining resource structures.
URL versioning remains the pragmatic industry standard due to its simplicity and robust tooling support.

## 12. What is a Dead Letter Queue (DLQ)? When does a message end up in a DLQ in RabbitMQ? How do you safely process DLQ messages without causing infinite retry loops?
A Dead Letter Queue (DLQ) is a secondary queue used to isolate messages that cannot be processed successfully after a defined number of attempts. It prevents "poison messages" from blocking a queue forever and impacting the processing of healthy messages.
In RabbitMQ, a message ends up in a DLQ if: (1) The consumer explicitly rejects it with `requeue=False`, (2) The message's TTL (Time-To-Live) expires, or (3) The primary queue reaches its maximum length limit.
To safely process DLQ messages without infinite loops, you should not automatically route them back to the primary queue. Instead, you need human intervention or a separate administrative process. A typical workflow involves:
1. Alerting engineers when the DLQ depth > 0.
2. Engineers inspect the message payload and the consumer logs to understand the failure (e.g., a schema validation error).
3. The underlying bug in the consumer code is fixed and deployed.
4. An administrative script (or tool like Shovel) replays the fixed messages from the DLQ back into the primary queue for reprocessing.

## 13. What is the health check endpoint pattern? What is the difference between a liveness probe and a readiness probe in Kubernetes? What should each check?
The health check endpoint pattern requires every microservice to expose standard HTTP endpoints (like `/health`) that monitoring systems can poll to determine the service's status.
In Kubernetes, these are formalized into two distinct probes:
1. Liveness Probe: Determines if the container is running or if it is stuck in a deadlocked state. If the liveness probe fails, Kubernetes will aggressively kill and restart the container. Therefore, a liveness probe should be lightweight—it should only check if the application process is responsive, NOT its external dependencies. Checking database connectivity here is dangerous; a slow database could cause Kubernetes to restart all your pods simultaneously.
2. Readiness Probe: Determines if the container is ready to accept incoming network traffic. If it fails, Kubernetes stops sending HTTP traffic to this pod, but does NOT restart it. This probe SHOULD check downstream dependencies. If the service cannot connect to its database or cache, it is not "ready" to handle requests, so the readiness probe should fail until the connection is restored.

## 14. What is the difference between a saga-based async request-reply and a direct synchronous call? Show the correlation ID pattern that enables async request-reply.
A direct synchronous call (like an HTTP POST) blocks the client thread until the server processes the request and returns the final result over the same network connection. 
An asynchronous request-reply decouples this. The client sends a message to a queue and immediately receives an HTTP 202 Accepted. The server processes the request asynchronously. To get the result, the client must use a Correlation ID.
The pattern works as follows: The client generates a unique `correlation_id` (UUID) and sends the request message containing this ID. The client then listens on a separate reply queue (or polls an endpoint). When the server finishes processing, it publishes a response message that includes the exact same `correlation_id`. The client uses this ID to match the asynchronous response back to the original request context.
```python
# Client side pseudo-code
import uuid

def place_order_async(order_data):
    corr_id = str(uuid.uuid4())
    message = {
        "order": order_data,
        "reply_to": "client_responses_queue",
        "correlation_id": corr_id
    }
    rabbitmq.publish("orders_queue", message)
    
    # Block on an internal map waiting for the async listener to resolve this future
    response = wait_for_response(corr_id, timeout=30) 
    return response

# Listener thread
def on_message_received(msg):
    # Match the incoming response to the waiting client thread using the correlation ID
    resolve_future(msg.correlation_id, msg.payload)
```

## 15. What is the Timeout pattern? What are the risks of missing timeouts between microservices? Why should connect_timeout and read_timeout always be configured separately?
The Timeout pattern involves setting strict time limits on how long a service will wait for a response from a downstream dependency. 
The risk of missing timeouts is catastrophic cascading failure. If Service A calls Service B without a timeout, and Service B silently hangs (e.g., due to a database deadlock), Service A will wait indefinitely. Service A's thread pool will eventually fill up with blocked threads, causing Service A to become unresponsive, which then crashes Service C that depends on it. Timeouts act as circuit breakers for thread starvation.
`connect_timeout` and `read_timeout` must always be configured separately because they represent entirely different network phases.
- `connect_timeout` limits the time taken to establish the initial TCP handshake. This should be very short (e.g., 50ms-200ms). If a server is down, you want to fail fast.
- `read_timeout` limits the time waiting for the server to process the request and send back the data payload after the connection is established. This needs to be tailored to the specific business logic (e.g., 2 seconds for a fast query, 10 seconds for a complex report). Mixing them up causes premature failures or dangerous delays.

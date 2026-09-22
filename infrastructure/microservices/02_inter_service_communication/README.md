# Module 2: Inter-Service Communication in Microservices

## 1. Synchronous vs Asynchronous Communication

When designing a microservices architecture, one of the most critical decisions is how services will communicate with each other. This is fundamentally divided into synchronous and asynchronous communication. The choice affects the system's coupling, resilience, scalability, and complexity.

### 1.1 Synchronous Communication

In synchronous communication, the client sends a request to the server and blocks its execution thread until it receives a response. This follows the traditional request-response model. The most common protocols for this are HTTP (REST) and gRPC.

#### Characteristics
- Immediate Response: The client knows immediately if the operation succeeded or failed.
- Conceptual Simplicity: It is easy to reason about and debug.
- Temporal Coupling: Both the client and the server must be available at the exact same time. If the server is down, the client request fails immediately.
- Performance Bottleneck: If a request involves multiple microservices calling each other synchronously, the overall response time is the sum of all individual response times.

#### Sequence Diagram (ASCII)
```text
+----------+                                      +----------+
| Client   |                                      | Server   |
+----------+                                      +----------+
     |                                                 |
     | -------- 1. HTTP GET /api/v1/resource --------> |
     |                                                 |
  (Wait for                                     (Process Request,
  response)                                      query DB, etc.)
     |                                                 |
     | <------- 2. HTTP 200 OK (JSON Payload) -------- |
     |                                                 |
+----------+                                      +----------+
```

### 1.2 Asynchronous Communication

In asynchronous communication, the client sends a message and continues its work without waiting for a response. The message is typically placed in a message broker or event stream.

#### Characteristics
- Loose Coupling: Services do not need to know about each other's existence or availability. The message broker acts as an intermediary.
- High Resilience: If the receiving service is down, the message remains in the broker until the service comes back online.
- Eventual Consistency: Changes take time to propagate through the system, leading to temporary inconsistencies.
- Complex Error Handling: Determining what went wrong and how to fix it requires distributed tracing and potentially compensation transactions (Sagas).

#### Sequence Diagram (ASCII)
```text
+----------+               +----------------+               +----------+
| Producer |               | Message Broker |               | Consumer |
+----------+               +----------------+               +----------+
     |                             |                             |
     | --- 1. Publish Event -----> |                             |
     |                             |                             |
(Continues                 (Stores Event)                        |
  Work)                            |                             |
     |                             | ---- 2. Deliver Event ----> |
     |                             |                             |
                                                             (Process)
```

## 2. REST API Design for Microservices

Representational State Transfer (REST) over HTTP is the most ubiquitous communication style for external-facing APIs and is still widely used internally. However, designing REST APIs for microservices requires discipline to ensure maintainability and backward compatibility.

### 2.1 API Versioning

As services evolve independently, breaking changes are inevitable. Versioning ensures that clients relying on older contracts do not break when the service is updated.

There are three main approaches to versioning:

1. URI Versioning:
   - Example: `GET /api/v1/customers/123`
   - Pros: Explicit, easy to route using API Gateways.
   - Cons: Violates the REST principle that a URI should represent a resource, not a version.

2. Header Versioning (Custom Headers):
   - Example: `GET /api/customers/123` with header `X-API-Version: 1`
   - Pros: Keeps URIs clean.
   - Cons: Harder to test in a browser, requires HTTP client manipulation.

3. Media Type (Accept Header) Versioning:
   - Example: `GET /api/customers/123` with header `Accept: application/vnd.mycompany.customer.v1+json`
   - Pros: Most RESTful, allows versioning individual representations.
   - Cons: Complex to implement and document.

### 2.2 Response Envelopes

A response envelope provides a consistent structure for all API responses, making it easier for clients to parse results, handle errors, and manage pagination.

#### Example Envelope Design (JSON)
```json
{
  "meta": {
    "status": 200,
    "request_id": "req_abc123",
    "timestamp": "2023-10-27T10:00:00Z"
  },
  "data": {
    "customer_id": 123,
    "name": "Jane Doe"
  },
  "pagination": {
    "next_cursor": "cXdlcnR5",
    "has_more": true
  },
  "errors": null
}
```

#### Code Example: FastAPI with Envelopes

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

app = FastAPI()

T = TypeVar('T')

class Meta(BaseModel):
    status: int
    request_id: str
    
class ErrorDetail(BaseModel):
    code: str
    message: str

class Envelope(BaseModel, Generic[T]):
    meta: Meta
    data: Optional[T] = None
    errors: Optional[List[ErrorDetail]] = None

class Customer(BaseModel):
    id: int
    name: str

@app.get("/api/v1/customers/{customer_id}", response_model=Envelope[Customer])
async def get_customer(customer_id: int):
    if customer_id == 123:
        return Envelope(
            meta=Meta(status=200, request_id="req_1"),
            data=Customer(id=123, name="Alice")
        )
    raise HTTPException(status_code=404, detail="Customer not found")
```

## 3. gRPC for Internal Service Communication

gRPC (gRPC Remote Procedure Calls) is an open-source, high-performance framework developed by Google. It is particularly well-suited for inter-service communication within a microservices architecture.

### 3.1 Protobuf (Protocol Buffers)

gRPC uses Protocol Buffers (protobuf) as its interface definition language (IDL) and underlying message interchange format. Protobuf is a strongly typed, binary serialization format.

#### Advantages of Protobuf:
- Compact Size: Binary serialization makes payloads much smaller than JSON.
- Fast Parsing: Deserializing binary data is significantly faster than parsing JSON text.
- Strong Typing: The schema acts as a strict contract, generating client and server stubs in multiple languages.

### 3.2 Defining a Service

A gRPC service is defined in a `.proto` file.

```protobuf
syntax = "proto3";

package payment;

// The payment service definition.
service PaymentService {
  // Processes a payment request synchronously
  rpc ProcessPayment (PaymentRequest) returns (PaymentResponse) {}
}

// The request message
message PaymentRequest {
  string order_id = 1;
  double amount = 2;
  string currency = 3;
}

// The response message
message PaymentResponse {
  bool success = 1;
  string transaction_id = 2;
  string error_message = 3;
}
```

### 3.3 Python gRPC Implementation

After compiling the `.proto` file (using `grpc_tools.protoc`), you implement the server and client.

#### Server (Python)
```python
import grpc
from concurrent import futures
import payment_pb2
import payment_pb2_grpc

class PaymentServicer(payment_pb2_grpc.PaymentServiceServicer):
    def ProcessPayment(self, request, context):
        print(f"Processing payment for order {request.order_id}")
        if request.amount > 10000:
            return payment_pb2.PaymentResponse(
                success=False, 
                error_message="Amount exceeds limit"
            )
        return payment_pb2.PaymentResponse(
            success=True, 
            transaction_id="txn_8899"
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(PaymentServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
```

#### Client (Python)
```python
import grpc
import payment_pb2
import payment_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = payment_pb2_grpc.PaymentServiceStub(channel)
        response = stub.ProcessPayment(payment_pb2.PaymentRequest(
            order_id="ord_123", amount=50.0, currency="USD"
        ))
        print("Payment success:", response.success)
        print("Transaction ID:", response.transaction_id)

if __name__ == '__main__':
    run()
```

## 4. Message Queues vs Event Streaming

For asynchronous communication, the two primary paradigms are message queues and event streaming platforms.

### 4.1 Message Queues (e.g., RabbitMQ, ActiveMQ)

Message queues are designed for point-to-point communication or publish/subscribe with transient messages. Once a message is consumed and acknowledged by a worker, it is deleted from the queue.

#### Core Concepts in RabbitMQ:
- Producer: Sends messages.
- Exchange: Routes messages to queues based on bindings and routing keys.
- Queue: A buffer that stores messages.
- Consumer: Receives and processes messages.

#### Code Example: RabbitMQ with Pika (Python)

```python
# Producer
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)

message = "Process Image ID: 55"
channel.basic_publish(
    exchange='',
    routing_key='task_queue',
    body=message,
    properties=pika.BasicProperties(
        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
    ))
print(f" [x] Sent {message}")
connection.close()
```

```python
# Consumer
import pika
import time

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)

def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    time.sleep(body.count(b'.'))
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
```

### 4.2 Event Streaming (e.g., Apache Kafka, Amazon Kinesis)

Event streams are immutable, append-only logs. Messages (events) are not deleted when consumed; they are retained for a configurable period. Consumers track their own progress using "offsets". This allows multiple independent consumers to read the same stream at their own pace.

#### Core Concepts in Kafka:
- Producer: Writes events to topics.
- Topic: A category or feed name.
- Partition: Topics are divided into partitions for scalability.
- Offset: A unique identifier for a record within a partition.
- Consumer Group: A group of consumers cooperating to read a topic.

#### Code Example: Kafka with confluent-kafka (Python)

```python
# Producer
from confluent_kafka import Producer
import json

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

event = {"order_id": "123", "status": "CREATED"}
producer.produce(
    'orders_topic', 
    key=str(event['order_id']), 
    value=json.dumps(event), 
    callback=delivery_report
)
producer.flush()
```

## 5. Event-Driven Architecture Patterns

When using messaging, how you design the payload is crucial. Two common patterns exist: Event Notification and Event-Carried State Transfer.

### 5.1 Event Notification

In this pattern, the event carries minimal data, just enough to notify consumers that something happened. If a consumer needs more details, it must make a synchronous API call back to the originating service.

- Example Payload: `{"event": "CustomerUpdated", "customer_id": "456"}`
- Pros: Small messages, simple event structure.
- Cons: Increases network traffic (consumers call back), creates temporal coupling for the follow-up request.

### 5.2 Event-Carried State Transfer

Here, the event contains all the state changes. Consumers cache this data locally, meaning they don't need to query the source system later.

- Example Payload: 
```json
{
  "event": "CustomerUpdated",
  "customer_id": "456",
  "new_state": {
    "email": "new@email.com",
    "address": "123 New St"
  }
}
```
- Pros: Consumers are completely autonomous; high performance (reads are local).
- Cons: Data duplication across services, eventual consistency complexities.

## 6. Service Discovery

In microservices architectures, instances of a service come and go due to scaling, deployments, and failures. Hardcoding IP addresses is impossible. Service Discovery solves this by providing a dynamic registry of available service instances.

### 6.1 Server-Side vs Client-Side Discovery

- Client-Side Discovery: The client queries the service registry (e.g., Consul, Eureka) to get the IP of an instance and performs load balancing itself.
- Server-Side Discovery: The client calls a Load Balancer or API Gateway, which queries the registry and forwards the request. (e.g., Kubernetes Services).

### 6.2 Service Discovery with Kubernetes

In Kubernetes, Service Discovery is native. When you create a `Service` resource, Kubernetes assigns it a DNS name (e.g., `my-svc.my-namespace.svc.cluster.local`). CoreDNS automatically resolves this name to the IP of the service, which then load balances traffic to the underlying Pods.

## 7. Resilience Patterns

Distributed systems fail. Network partitions, timeouts, and crashed instances are common. Resilience patterns protect the system from cascading failures.

### 7.1 Circuit Breaker

The Circuit Breaker pattern prevents an application from repeatedly trying to execute an operation that is likely to fail. 

#### States:
1. Closed: Normal operation. Requests flow through. If failures exceed a threshold, transition to Open.
2. Open: Requests are immediately rejected without calling the external service. A timer starts.
3. Half-Open: After the timer expires, a limited number of test requests are allowed through. If they succeed, transition to Closed. If they fail, transition back to Open.

#### ASCII Diagram: Circuit Breaker
```text
           (Success)
      +----------------+
      |                v
+----------+      +----------+
|  CLOSED  | ---> |   OPEN   |
+----------+      +----------+
  (Failures)        |      ^
                    |      | (Timeout expires)
                    v      |
                +----------+
                | HALF-OPEN|
                +----------+
                  |      ^
       (Success)--+      +--(Failure)
```

### 7.2 Retry with Exponential Backoff and Jitter

Simple retries can overwhelm a struggling service (thundering herd problem). Exponential backoff increases the wait time between retries (e.g., 1s, 2s, 4s, 8s). Jitter adds a random delay to prevent multiple clients from retrying at the exact same moment.

#### Code Example: Tenacity (Python)
```python
from tenacity import retry, wait_exponential, stop_after_attempt, wait_random_exponential
import requests

# Retries up to 5 times. 
# Waits 2^x * 1 second between each retry, with added randomness.
@retry(
    wait=wait_random_exponential(multiplier=1, max=10), 
    stop=stop_after_attempt(5)
)
def call_flaky_service():
    print("Attempting to call service...")
    response = requests.get("http://flaky-service/api/data", timeout=2)
    response.raise_for_status()
    return response.json()
```

### 7.3 Bulkhead

The Bulkhead pattern isolates elements of an application into pools so that if one fails, the others will continue to function. For example, assigning different database connection pools to different endpoints.

## 8. Idempotency — Critical for Microservices

Because network requests can fail after execution but before the response is received, clients often retry. Therefore, operations must be Idempotent—meaning executing them multiple times has the same effect as executing them once.

### 8.1 Idempotency Keys

Clients generate a unique `Idempotency-Key` (usually a UUID) for mutations (POST, PATCH). The server checks if it has seen this key.

- If new: Process the request, store the result with the key.
- If seen and processing: Return HTTP 409 Conflict.
- If seen and completed: Return the cached HTTP response.

#### Code Example: Redis for Idempotency

```python
import redis
import json
from fastapi import FastAPI, Header, HTTPException, Response

app = FastAPI()
cache = redis.Redis(host='localhost', port=6379, db=0)

@app.post("/payments")
def create_payment(amount: float, idempotency_key: str = Header(None)):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")
        
    # Check cache
    cached_response = cache.get(f"idemp:{idempotency_key}")
    if cached_response:
        # Return cached exact response
        return json.loads(cached_response)
        
    # Set a lock to prevent concurrent requests with same key
    lock_acquired = cache.setnx(f"lock:{idempotency_key}", "locked")
    if not lock_acquired:
        raise HTTPException(status_code=409, detail="Request already in progress")
        
    try:
        # Simulate processing payment
        transaction_id = f"txn_{int(amount*100)}"
        response_data = {"status": "success", "transaction_id": transaction_id}
        
        # Save response
        cache.setex(f"idemp:{idempotency_key}", 86400, json.dumps(response_data))
        return response_data
    finally:
        # Release lock
        cache.delete(f"lock:{idempotency_key}")
```

---
*End of Module 2. Make sure you understand the nuances of when to apply synchronous versus asynchronous patterns, as this is the foundational bedrock of stable microservice architectures.*

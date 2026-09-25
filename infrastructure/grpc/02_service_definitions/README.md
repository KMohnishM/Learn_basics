# Module 2: gRPC Service Definitions & Implementation

Welcome to Module 2. Now that you understand the underlying serialization
mechanics of Protocol Buffers from Module 1, we will move to the network
layer. In this module, you will learn how to define gRPC services, build
production-grade servers and clients in both Python and Go, handle rich
error metadata, and transmit out-of-band context using headers and
trailers.

---

## 1. Defining Services & Unary RPCs

A gRPC service consists of a collection of RPC (Remote Procedure Call)
methods. You define the interface in a `.proto` file, and the `protoc`
compiler generates abstract base classes (for the server) and stubs (for
the client).

### The `service` Definition Syntax

Services are defined using the `service` keyword. A Unary RPC is the
simplest type: the client sends a single request and the server responds
with a single response.

```protobuf
syntax = "proto3";

package ecom.v1.orders;

import "google/protobuf/timestamp.proto";
```

### Best Practice: Dedicated Request/Response Messages

**Critical Rule:** Every single RPC method should take a dedicated
`<MethodName>Request` message and return a dedicated `<MethodName>Response`
message.

Do **NOT** reuse generic messages (like an `Order` message) directly in the
RPC signature. If you use `rpc GetOrder(Order) returns (Order);`, you
completely break backward compatibility the moment you need to add
pagination parameters, authentication tokens, or metadata that applies to
the request but not the actual data model.

```protobuf
// Good API Design
service OrderService {
  // A simple Unary RPC
  rpc GetOrder (GetOrderRequest) returns (GetOrderResponse);

  // Another Unary RPC
  rpc CreateOrder (CreateOrderRequest) returns (CreateOrderResponse);
}

// Dedicated request wrapper
message GetOrderRequest {
  string order_id = 1;
}

// Dedicated response wrapper
message GetOrderResponse {
  Order order = 1;
}

// Dedicated request wrapper
message CreateOrderRequest {
  string user_id = 1;
  repeated string item_ids = 2;
}

// Dedicated response wrapper
message CreateOrderResponse {
  string order_id = 1;
  google.protobuf.Timestamp created_at = 2;
}

// The core business entity (independent of RPC mechanics)
message Order {
  string id = 1;
  string user_id = 2;
  string status = 3;
}
```

---

## 2. Building a Production gRPC Server in Python

Implementing a server in Python involves inheriting from the generated
`Servicer` class and attaching it to a configured `grpc.server` instance
running atop a thread pool.

### Generating the Code
Assuming the file is named `order.proto`:
```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. order.proto
```
This generates `order_pb2.py` (data structures) and `order_pb2_grpc.py`
(networking stubs).

### Implementing the Servicer Class

The business logic resides in a class that extends `OrderServiceServicer`.

```python
import time
import grpc
from concurrent import futures
import logging

# Import generated code
import order_pb2
import order_pb2_grpc
from google.protobuf import timestamp_pb2

class OrderServiceServicer(order_pb2_grpc.OrderServiceServicer):
    def __init__(self):
        # Simulated database
        self.db = {
            "order-123": {"user": "alice", "status": "SHIPPED"}
        }

    def GetOrder(self, request, context):
        """
        Unary RPC implementation.
        request: The GetOrderRequest object.
        context: Server context for metadata, errors, and cancellation checking.
        """
        logging.info(f"Received request for order: {request.order_id}")

        # Check if client cancelled the request to save CPU
        if context.is_active() is False:
            logging.warning("Client cancelled request.")
            return order_pb2.GetOrderResponse()

        order_data = self.db.get(request.order_id)

        if not order_data:
            # Setting standard status codes
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Order {request.order_id} not found in database.")
            return order_pb2.GetOrderResponse()

        # Build and return the response
        response = order_pb2.GetOrderResponse()
        response.order.id = request.order_id
        response.order.user_id = order_data["user"]
        response.order.status = order_data["status"]
        return response
```

### Configuring and Starting the Server

The server must bind to a port and manage a pool of worker threads.

```python
def serve():
    # 1. Create a thread pool. Size depends on CPU cores and I/O bound nature of tasks.
    # For highly I/O bound tasks (like querying a DB), this can be high.
    thread_pool = futures.ThreadPoolExecutor(max_workers=10)

    # 2. Instantiate the gRPC server
    server = grpc.server(thread_pool)

    # 3. Register the Servicer with the server
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderServiceServicer(), server)

    # 4. Bind to a port (insecure for internal microservices, secure for public)
    port = "[::]:50051"
    server.add_insecure_port(port)
    logging.info(f"Starting server on {port}")

    # 5. Start the server (non-blocking)
    server.start()

    try:
        # Keep the main thread alive
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
        # Grace period allows in-flight requests to finish
        server.stop(grace_period=5.0)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()
```

---

## 3. Building a gRPC Client in Python

A client uses a `Channel` to connect to the server, and a `Stub` to execute
RPCs.

### Channel Management
**Critical Rule:** Channels are expensive to create because they initiate
underlying HTTP/2 TCP connections. They are thread-safe. You should create
**one** channel when your application starts and share it across all
threads/requests. Do not create a new channel per request.

```python
import grpc
import order_pb2
import order_pb2_grpc

def run_client():
    # 1. Create a long-lived channel
    # Use grpc.secure_channel(target, credentials) for TLS
    target = 'localhost:50051'
    with grpc.insecure_channel(target) as channel:

        # 2. Instantiate the stub (the client interface)
        stub = order_pb2_grpc.OrderServiceStub(channel)

        # 3. Create a request object
        request = order_pb2.GetOrderRequest(order_id="order-123")

        try:
            # 4. Execute the RPC (Synchronous blocking call)
            # Timeout is highly recommended to prevent resource exhaustion
            response = stub.GetOrder(request, timeout=3.0)
            print(f"Success! Order Status: {response.order.status}")

        except grpc.RpcError as rpc_error:
            # Handle gRPC specific errors
            print(f"RPC failed with code {rpc_error.code()}")
            print(f"Details: {rpc_error.details()}")

if __name__ == '__main__':
    run_client()
```

### Asynchronous Client Invocations (`grpc.aio`)
Modern high-performance Python (like FastAPI apps) uses `asyncio`. Standard
`grpc` blocks the event loop. You must use `grpc.aio` for asynchronous
contexts.

```python
import asyncio
import grpc
import order_pb2
import order_pb2_grpc

async def run_async_client():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = order_pb2_grpc.OrderServiceStub(channel)
        request = order_pb2.GetOrderRequest(order_id="order-123")

        try:
            # Await the RPC call
            response = await stub.GetOrder(request, timeout=3.0)
            print(f"Async Success: {response.order.status}")
        except grpc.RpcError as e:
            print(f"Async Error: {e.code()} - {e.details()}")

if __name__ == '__main__':
    asyncio.run(run_async_client())
```

---

## 4. Building gRPC Server and Client in Go

Go is arguably the most native language for gRPC, offering phenomenal
performance and concurrency out of the box using goroutines.

### The Go Server

```go
package main

import (
	"context"
	"log"
	"net"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	// Import generated protobuf code
	pb "ecom/v1/orders/generated"
)

// server implements the OrderServiceServer interface
type server struct {
	pb.UnimplementedOrderServiceServer
	db map[string]string
}

// GetOrder implements the RPC method
func (s *server) GetOrder(ctx context.Context, req *pb.GetOrderRequest) (*pb.GetOrderResponse, error) {
	log.Printf("Received request for order: %s", req.GetOrderId())

	statusVal, exists := s.db[req.GetOrderId()]
	if !exists {
		// Return standard gRPC errors using the status package
		return nil, status.Errorf(codes.NotFound, "Order %s not found", req.GetOrderId())
	}

	return &pb.GetOrderResponse{
		Order: &pb.Order{
			Id:     req.GetOrderId(),
			UserId: "alice",
			Status: statusVal,
		},
	}, nil
}

func main() {
	// 1. Open a TCP listener
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	// 2. Create the gRPC server instance
	s := grpc.NewServer()

	// 3. Register our implementation
	myServer := &server{
		db: map[string]string{"order-123": "SHIPPED"},
	}
	pb.RegisterOrderServiceServer(s, myServer)

	log.Printf("server listening at %v", lis.Addr())

	// 4. Start serving (blocks indefinitely)
	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
```

### The Go Client

```go
package main

import (
	"context"
	"log"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "ecom/v1/orders/generated"
)

func main() {
	// 1. Dial the server (creates connection pool)
	conn, err := grpc.DialContext(
		context.Background(),
		"localhost:50051",
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(), // Wait until connection is established
	)
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	defer conn.Close() // Ensure connection is cleaned up on exit

	// 2. Instantiate the stub
	c := pb.NewOrderServiceClient(conn)

	// 3. Create a context with a timeout (CRITICAL for microservices)
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*3)
	defer cancel()

	// 4. Call the RPC
	r, err := c.GetOrder(ctx, &pb.GetOrderRequest{OrderId: "order-123"})
	if err != nil {
		log.Fatalf("could not get order: %v", err)
	}
	log.Printf("Order Status: %s", r.GetOrder().GetStatus())
}
```

---

## 5. gRPC Error Handling & Status Codes

gRPC does not use HTTP status codes (like 200, 404, 500) natively at the
application layer. Instead, it defines its own taxonomy of 16 specific
status codes.

### Standard Status Codes
- `OK` (0): Success.
- `INVALID_ARGUMENT` (3): Client specified an invalid parameter (e.g.,
negative amount). (Maps to HTTP 400).
- `DEADLINE_EXCEEDED` (4): Operation took too long. (Maps to HTTP 504).
- `NOT_FOUND` (5): Resource not found. (Maps to HTTP 404).
- `ALREADY_EXISTS` (6): Resource already exists. (Maps to HTTP 409).
- `PERMISSION_DENIED` (7): Caller does not have permission. (Maps to HTTP 403).
- `UNAUTHENTICATED` (16): Missing or invalid authentication token. (Maps to
HTTP 401).
- `RESOURCE_EXHAUSTED` (8): Rate limiting or quota exceeded. (Maps to HTTP 429).
- `UNIMPLEMENTED` (12): The server doesn't implement this RPC. (Maps to
HTTP 501).
- `INTERNAL` (13): Unexpected server error (like a DB crash). (Maps to HTTP
500).
- `UNAVAILABLE` (14): Service is down or restarting. (Maps to HTTP 503).

### Python Error Handling (Abort vs set_code)
You can return errors in Python in two ways:
1. `context.set_code(grpc.StatusCode.NOT_FOUND)` and return an empty response.
2. `context.abort(grpc.StatusCode.NOT_FOUND, "Not found")` which
immediately raises an exception to halt execution.

### The Google Rich Error Model (`google.rpc.Status`)
Sometimes, a simple string error message isn't enough. If a request is
`INVALID_ARGUMENT`, the client needs to know *which* fields were invalid.

Google provides the `google.rpc.Status` message which allows you to attach
arbitrary protobuf messages as metadata to an error. Common attachments
include:
- `ErrorInfo`: Machine readable reason, domain, and metadata.
- `BadRequest.FieldViolation`: List of specific fields that failed validation.
- `RetryInfo`: Tells the client how many milliseconds to wait before retrying.

**Implementing Rich Errors in Go:**
```go
import (
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	errdetails "google.golang.org/genproto/googleapis/rpc/errdetails"
)

func (s *server) CreateOrder(ctx context.Context, req *pb.CreateOrderRequest) (*pb.CreateOrderResponse, error) {
	if len(req.GetItemIds()) == 0 {
		st := status.New(codes.InvalidArgument, "Request parameters invalid")

		// Attach detailed FieldViolation payload
		v := &errdetails.BadRequest_FieldViolation{
			Field:       "item_ids",
			Description: "Order must contain at least one item.",
		}

		br := &errdetails.BadRequest{}
		br.FieldViolations = append(br.FieldViolations, v)

		st, err := st.WithDetails(br)
		if err != nil {
			// fallback if attaching details fails
			return nil, status.Error(codes.Internal, "Internal error")
		}
		return nil, st.Err() // Returns the rich error to the client
	}
    // ...
}
```

---

## 6. gRPC Metadata (Headers and Trailers)

Metadata provides out-of-band context. It is the gRPC equivalent of HTTP
headers. Metadata is represented as a list of key-value pairs (strings).

### Initial vs Trailing Metadata
- **Initial Metadata (Headers)**: Sent from client to server (e.g., Auth
tokens, trace IDs), or from server to client before the response body
begins.
- **Trailing Metadata (Trailers)**: Sent exclusively from server to client
*after* the RPC is complete, usually containing final status information or
rate-limit consumption stats.

### Binary Metadata
If you need to send binary data in metadata (like a raw encrypted token or
serialized protobuf), the key **MUST** end with the `-bin` suffix (e.g.,
`auth-token-bin`). gRPC automatically base64-encodes/decodes keys ending in
`-bin` for safe transport over HTTP/2 headers.

### Sending Metadata in Python Client
```python
# Pass metadata as a list of tuples
metadata = (
    ('authorization', 'Bearer my-jwt-token'),
    ('x-trace-id', '1234567890'),
)
response = stub.GetOrder(request, metadata=metadata)
```

### Reading Metadata in Python Server
```python
def GetOrder(self, request, context):
    # Retrieve metadata tuple list
    metadata = context.invocation_metadata()
    auth_token = None
    for key, value in metadata:
        if key == 'authorization':
            auth_token = value

    if not auth_token:
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing token")

    # Send trailing metadata back to client
    context.set_trailing_metadata((
        ('x-rate-limit-remaining', '99'),
    ))
```

This concludes Module 2. You now possess the skills to build robust,
production-ready microservices using gRPC. Move on to
`02_service_definitions/QnA.md` and `02_service_definitions/CHEATSHEET.md`.

---

## Appendix: Interceptors (Middleware)

To build truly production-ready systems, you must handle cross-cutting concerns (like logging, authentication, and metrics) without polluting your business logic handlers. In gRPC, this is achieved using **Interceptors**.

Interceptors act exactly like middleware in a REST framework (like Express or Django). They wrap the incoming request and the outgoing response, allowing you to execute logic before and after the core handler runs.

### Types of Interceptors
1. **Unary Server Interceptor**: Intercepts unary RPCs on the server.
2. **Stream Server Interceptor**: Intercepts streaming RPCs on the server.
3. **Unary Client Interceptor**: Intercepts unary RPCs before they are sent from the client.
4. **Stream Client Interceptor**: Intercepts streaming RPCs on the client.

### Building a Logging Interceptor in Go

Below is a complete implementation of a Unary Server Interceptor in Go that automatically logs the start time, end time, execution duration, and final status code for every single RPC request that hits your server.

```go
package main

import (
	"context"
	"log"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/status"
)

// LoggingInterceptor creates a unary server interceptor for request logging.
func LoggingInterceptor() grpc.UnaryServerInterceptor {
	return func(
		ctx context.Context,
		req interface{},
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (interface{}, error) {
		
		// 1. Pre-processing: Record start time
		start := time.Now()
		
		// Extract trace ID from incoming metadata (if available)
		// ... logic to read md from context ...
		
		log.Printf("--> Intercepted request to %s", info.FullMethod)

		// 2. Invoke the actual RPC handler
		resp, err := handler(ctx, req)

		// 3. Post-processing: Calculate duration and log outcome
		duration := time.Since(start)
		
		// Check if the handler returned an error
		if err != nil {
			st, _ := status.FromError(err)
			log.Printf("<-- Failed %s in %v. Code: %s, Msg: %s", 
				info.FullMethod, duration, st.Code().String(), st.Message())
		} else {
			log.Printf("<-- Succeeded %s in %v", info.FullMethod, duration)
		}

		// 4. Return the original response and error back to the gRPC framework
		return resp, err
	}
}

// How to register this interceptor when starting the server:
func main() {
	// Open TCP listener
	// lis, err := net.Listen("tcp", ":50051")
	
	// Register the interceptor by passing it as a ServerOption
	serverOptions := []grpc.ServerOption{
		grpc.UnaryInterceptor(LoggingInterceptor()),
	}
	
	// Create the gRPC server with the options applied
	grpcServer := grpc.NewServer(serverOptions...)
	
	// pb.RegisterMyServiceServer(grpcServer, &myImplementation{})
	// grpcServer.Serve(lis)
}
```

By using interceptors, you guarantee that every single endpoint in your system receives consistent logging and telemetry, radically simplifying the maintainability of your gRPC services.
  
## Appendix B: Advanced Deployment Strategies

Running gRPC in production requires specific architectural considerations, primarily due to HTTP/2 multiplexing.

### 1. Load Balancing (L4 vs L7)
Because gRPC multiplexes all requests onto a single long-lived HTTP/2 TCP connection, traditional L4 (Network Layer) load balancers (like AWS NLB or default Kubernetes Services) fail completely. An L4 balancer simply routes the TCP connection to a single backend pod. All thousands of multiplexed requests will hit that exact same pod, while the other 9 pods sit completely idle.

To fix this, you must use an L7 (Application Layer) load balancer that understands HTTP/2 frames.
- **Client-Side Load Balancing**: The gRPC client resolves multiple IP addresses via DNS or xDS (Envoy), and internally creates a connection pool, round-robining individual RPC frames across all backend connections.
- **Proxy Load Balancing**: Use a service mesh proxy like **Envoy**, **Linkerd**, or **Nginx**. The client maintains one connection to Envoy. Envoy terminates the HTTP/2 connection, inspects the individual RPC frames, and sprays them evenly across the backend fleet over multiple connections.

### 2. Timeouts (Deadlines) and Context Propagation
Distributed systems fail cascades occur when a frontend waits indefinitely for a backend, which is waiting for a database. gRPC solves this natively using **Deadlines**.

When a client initiates a request, it specifies an absolute timeout (e.g., `3 seconds`). This deadline is serialized into the HTTP/2 headers as `grpc-timeout`.
When the server receives the request, the `context` object inherits this deadline. If the server makes a downstream call to another microservice, it passes the same context.
If the 3 seconds expire, the original client cancels the request. Automatically, the context on the server is canceled, and any downstream requests the server made are immediately aborted. This prevents zombie requests from consuming resources across the entire cluster.
**Rule:** ALWAYS set a deadline on every single gRPC client call.

### 3. Health Checking
Kubernetes needs to know if your pod is healthy. Since gRPC is not HTTP/1.1 REST, Kubernetes cannot simply hit `/healthz`.
Instead, implement the standard `grpc.health.v1.Health` service.
Kubernetes natively supports `grpc` probes since v1.24.
```yaml
livenessProbe:
  grpc:
    port: 50051
  initialDelaySeconds: 5
```
Your server must register the health check implementation, which allows you to dynamically mark individual services within your pod as `SERVING` or `NOT_SERVING`.

### 4. Connection Keep-Alive
In cloud environments, idle TCP connections are aggressively killed by firewalls or NAT gateways (often after 5 minutes). When a client attempts to use a killed connection, the RPC hangs until a TCP timeout occurs, causing massive tail latency spikes.
To prevent this, configure gRPC **Keep-Alive**.
The client will periodically send an HTTP/2 PING frame to the server to ensure the connection is active and to reset the firewall's idle timer.
```go
// Go client KeepAlive configuration
var kacp = keepalive.ClientParameters{
	Time:                10 * time.Second, // Send pings every 10 seconds if idle
	Timeout:             time.Second,      // Wait 1 second for ping ack
	PermitWithoutStream: true,             // Send pings even without active streams
}
conn, _ := grpc.DialContext(ctx, addr, grpc.WithKeepaliveParams(kacp))
```
These deployment practices ensure your gRPC infrastructure is resilient, scalable, and responsive under high load.

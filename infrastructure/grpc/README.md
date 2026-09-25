# gRPC Infrastructure Curriculum

## Introduction to gRPC

gRPC is a modern, open-source, high-performance Remote Procedure Call (RPC)
framework that can run in any environment. It can efficiently connect
services in and across data centers with pluggable support for load
balancing, tracing, health checking, and authentication. It is the default
standard for inter-service communication in microservice architectures.

Why gRPC has become the default:
1. **Performance**: Built on HTTP/2, allowing multiplexed streams and
binary payloads.
2. **Polyglot**: Native bindings for C++, Java, Python, Go, Ruby, C#,
Node.js, and more.
3. **Strong Contracts**: API specifications are written in Protocol
Buffers, creating a single, statically typed source of truth.
4. **Streaming**: First-class support for client, server, and bidirectional
streaming.
5. **Ecosystem**: Integrates seamlessly with cloud-native tools like
Kubernetes, Envoy, Prometheus, and OpenTelemetry.

---

## gRPC vs REST/JSON Architectural Comparison

| Feature | REST with JSON | gRPC with Protobuf |
|---------|----------------|--------------------|
| **Serialization** | Text-based (JSON), CPU intensive parsing | Binary (Protobuf), extremely fast parsing |
| **Payload Size** | Large (keys repeated every message) | Small (keys replaced by field tags) |
| **Transport** | HTTP/1.1 (typically) | HTTP/2 (always) |
| **Connection** | One request per TCP connection (usually) | Multiplexed (many requests on one TCP connection) |
| **Streaming** | Limited (WebSockets, SSE required) | First-class (Bidirectional, client, server) |
| **Contract** | Optional (OpenAPI/Swagger) | Mandatory (.proto files) |
| **Browser Support**| Universal | Requires gRPC-Web proxy (Envoy) |

---

## Module Map

This curriculum is structured into the following deep-dive modules:

| Module Path | Core Topics | Learning Objectives |
|-------------|-------------|---------------------|
| `01_protobuf/` | Protocol Buffers, Wire Format, Schema Evolution | Master the `.proto` syntax, binary serialization mechanics, and strict compatibility rules. |
| `02_service_definitions/` | Unary RPCs, Python/Go implementations, Error Handling, Metadata | Build production-ready clients and servers in Python and Go, handling rich errors and headers. |
| `03_streaming/` | Server, Client, and Bidirectional Streaming, Flow Control | (Future) Understand HTTP/2 streams and build real-time reactive APIs. |
| `04_advanced/` | Interceptors, Authentication (TLS/JWT), Load Balancing | (Future) Secure and scale gRPC services using middleware and proxies. |

---

## HTTP/2 Foundations

Understanding gRPC requires understanding its transport layer, HTTP/2:

### 1. Binary Framing Layer
HTTP/2 divides all data into smaller messages and frames, each of which is
encoded in binary format. This makes parsing significantly more efficient
for machines compared to the text-delimited protocols of HTTP/1.1.

### 2. Multiplexing over a Single TCP Connection
HTTP/2 allows multiple concurrent requests and responses to be in flight
simultaneously over a single TCP connection. This eliminates the head-of-
line blocking problem of HTTP/1.1 and drastically reduces connection
overhead, which is critical for microservices making thousands of RPCs per
second.

### 3. Streams and Frames
A stream is an independent, bidirectional sequence of frames exchanged
between the client and server within an HTTP/2 connection. gRPC maps a
single RPC call to a single HTTP/2 stream.

### 4. HPACK Header Compression
HTTP/1.1 sends headers as plain text, often repeating the same headers per
request. HTTP/2 uses HPACK compression, which maintains a stateful
dictionary on both the client and server to compress header sizes, vastly
reducing overhead.

---

## Prerequisites and Study Path

**Prerequisites:**
- Basic understanding of networked applications (TCP/IP, HTTP).
- Familiarity with Python and Go programming languages.
- A terminal environment with `protoc` and `buf` installed.

**Study Path:**
1. Start with `01_protobuf/README.md` to learn how data is structured and
serialized.
2. Review the `01_protobuf/QnA.md` and memorize the `CHEATSHEET.md`.
3. Proceed to `02_service_definitions/README.md` to build the actual services.
4. Complete the exercises and verify implementations.

Welcome to the world of high-performance microservices!
# Module 2: Transport Layer

## What is the Transport Layer?
In the Model Context Protocol (MCP), the transport layer is responsible for the actual delivery of JSON-RPC 2.0 messages between the client and the server. Because MCP defines a clear separation between the message format (JSON-RPC) and the transmission mechanism, developers can choose the transport that best fits their deployment model—whether that is a local, secure subprocess or a remote, cloud-hosted API.

## Core Transport Types

### 1. stdio Transport
The `stdio` (Standard Input/Output) transport is the most common for local MCP servers. The client spawns the server as a child process and communicates by writing to the server's `stdin` and reading from its `stdout`.
- **Pros**: Extremely secure (no network ports opened), zero network latency, simple to deploy locally.
- **Cons**: Cannot be accessed remotely; the client must have the environment to run the server's binary or runtime.
- **Message Framing**: Messages are separated by newlines (`\n`).

### 2. HTTP + SSE Transport
For remote deployments, MCP uses Server-Sent Events (SSE) combined with standard HTTP POST requests. Because HTTP is fundamentally uni-directional (client requests, server responds), SSE is used to allow the server to push messages (like notifications or responses to server-initiated requests) to the client.
- **Pros**: Ideal for cloud-hosted servers, easily integrates with existing load balancers and API gateways.
- **Cons**: Higher latency than stdio, requires network configuration and authentication mechanisms.
- **How it works**: 
  1. Client connects to the `/sse` endpoint.
  2. Server responds with a continuous SSE stream and assigns an endpoint URL for the client to send messages.
  3. Client sends its JSON-RPC messages via HTTP POST to the assigned endpoint.
  4. Server sends its JSON-RPC messages down the SSE stream.

### 3. WebSocket Transport (Draft/Extensions)
While stdio and SSE are the primary standard transports, WebSockets are often used in custom implementations for full-duplex remote communication, bypassing the need for separate POST requests.

## Connection Lifecycle at the Transport Level

1. **Process/Connection Start**: For stdio, the child process is spawned. For SSE, the initial HTTP GET to `/sse` is established.
2. **Message Framing**: Raw bytes are buffered and parsed into distinct JSON objects based on the transport rules (e.g., newline delimiters).
3. **Graceful Shutdown**: The client sends an `exit` JSON-RPC notification. The server should flush buffers and terminate. The transport connection is then closed.

## Python Code Example: stdio Server

Using the official `mcp` Python SDK:

```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Initialize the server
app = Server("local-math-server")

@app.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

async def main():
    # stdio_server provides the read and write streams
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## Python Code Example: HTTP/SSE Server

Using `mcp` with `Starlette` for HTTP/SSE:

```python
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server import Server
from mcp.server.sse import SseServerTransport

app = Server("remote-math-server")
sse_transport = SseServerTransport("/messages")

@app.tool()
async def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

async def handle_sse(request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as endpoint:
        await app.run(endpoint.read_stream, endpoint.write_stream, app.create_initialization_options())

async def handle_messages(request):
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)

starlette_app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse),
    Route("/messages", endpoint=handle_messages, methods=["POST"])
])

if __name__ == "__main__":
    uvicorn.run(starlette_app, host="0.0.0.0", port=8000)
```

## Error Handling at the Transport Layer

Transport errors are distinct from JSON-RPC errors. 
- **JSON-RPC Errors**: Malformed request, tool execution failure (returned cleanly inside a JSON-RPC response with an `error` object).
- **Transport Errors**: Process crash, broken pipe, network timeout.
If the transport layer fails, the client must assume the connection is dead, handle the disconnection gracefully, and optionally attempt a restart.

## Choosing the Right Transport

| Scenario | Recommended Transport | Why? |
|----------|-----------------------|------|
| Personal IDE extension | `stdio` | Simple, secure, no networking needed |
| Enterprise database access | `HTTP + SSE` | Centralized deployment, IP allowlisting |
| Claude Desktop local tools | `stdio` | Seamless integration, zero configuration |
| Multi-tenant SaaS integration | `HTTP + SSE` | Standard web infrastructure compatibility |

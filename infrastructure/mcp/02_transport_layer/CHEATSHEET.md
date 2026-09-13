# CHEATSHEET: MCP Transport Layer

## Transport Comparison Table

| Feature | `stdio` | `HTTP + SSE` |
|---------|---------|--------------|
| **Environment** | Local (same machine) | Remote (networked) |
| **Connection** | Child process spawning | HTTP GET (SSE) + POST |
| **Directionality** | Full duplex streams | Server push (SSE) / Client push (POST) |
| **Framing** | Newline (`\n`) delimited | HTTP body / SSE event data |
| **Security** | Inherently secure (OS level) | Requires Auth/TLS over network |

## Message Framing Examples

**stdio:**
```json
{"jsonrpc":"2.0","id":1,"method":"ping"}\n
{"jsonrpc":"2.0","id":1,"result":{}}\n
```
*(Must be strictly one line per message)*

**SSE (Server to Client):**
```text
event: message
data: {"jsonrpc": "2.0", "id": 1, "result": {}}

```

**POST (Client to Server):**
```http
POST /messages HTTP/1.1
Content-Type: application/json

{"jsonrpc":"2.0","method":"ping"}
```

## Setup Code Snippets (Python)

**stdio Server:**
```python
from mcp.server.stdio import stdio_server
async with stdio_server() as (read, write):
    await app.run(read, write, options)
```

**SSE Server (Starlette):**
```python
from mcp.server.sse import SseServerTransport
sse = SseServerTransport("/messages")

# Route 1: GET /sse -> sse.connect_sse(...)
# Route 2: POST /messages -> sse.handle_post_message(...)
```

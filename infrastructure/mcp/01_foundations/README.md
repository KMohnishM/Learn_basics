# Module 1: MCP Foundations

## What is the Model Context Protocol (MCP)?
The Model Context Protocol (MCP) is an open standard that enables developers to build secure, two-way connections between data sources and AI models. Before MCP, integrating AI models with external data required custom, brittle integrations for each data source and model pair. MCP standardizes this process, creating a universal protocol for AI context provision.

MCP is built on JSON-RPC 2.0 and operates over various transport mechanisms (like stdio or HTTP/SSE). It establishes a client-server architecture where AI models act as clients requesting context, and data sources act as servers providing that context.

## History and Motivation
As Large Language Models (LLMs) evolved, their utility became constrained by their training data cutoff and inability to interact with real-time or proprietary systems. The industry initially responded with custom plugins, vector databases, and ad-hoc API integrations. However, this resulted in an m x n integration problem: m models connecting to n data sources required m * n custom integrations. 

MCP was introduced to reduce this to an m + n problem. By implementing MCP, a single data source can instantly connect to any MCP-compliant model, and vice versa.

## Core Architecture

```text
+-------------------+                          +-------------------+
|                   |       JSON-RPC 2.0       |                   |
|   MCP Client      | <======================> |   MCP Server      |
| (AI Application)  |     (stdio / HTTP)       |  (Data Provider)  |
|                   |                          |                   |
+--------+----------+                          +---------+---------+
         |                                               |
         |                                               |
         v                                               v
+--------+----------+                          +---------+---------+
|                   |                          |                   |
|    LLM Engine     |                          |   Local/Remote    |
| (e.g., Claude)    |                          |   Data Source     |
|                   |                          |                   |
+-------------------+                          +-------------------+
```

The architecture consists of:
1. **MCP Host/Client**: The application hosting the AI model (e.g., Claude Desktop, IDE extensions). It manages connections to multiple servers.
2. **MCP Server**: A lightweight process that securely exposes data and tools to the client.
3. **Transport Layer**: The communication channel (stdio for local, HTTP/SSE for remote).

## The Four Primitives of MCP

MCP defines four core primitives that a server can expose to a client:

1. **Resources**: Read-only data representing context. Analogous to a file system. Resources have URIs (e.g., `file:///logs/app.log` or `postgres://db/schema`).
2. **Prompts**: Pre-defined templates for interactions. They help guide the LLM on how to use the server's capabilities or structure a specific task.
3. **Tools**: Executable functions that the LLM can invoke to perform actions or retrieve dynamic data (e.g., `search_web`, `query_database`, `restart_service`). Tools require human-in-the-loop approval in many client implementations.
4. **Sampling (Client-side)**: A capability allowing the server to request completions from the client's underlying model, enabling agentic loops where the server orchestrates complex tasks using the LLM.

## JSON-RPC 2.0 Deep Dive

MCP uses JSON-RPC 2.0 as its message format. A JSON-RPC 2.0 message has three primary types:

### 1. Request
Expects a response. Contains an `id` field.
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list",
  "params": {}
}
```

### 2. Response
Matches the `id` of the request. Contains either a `result` or an `error`.
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resources": [
      {
        "uri": "file:///example.txt",
        "name": "Example File"
      }
    ]
  }
}
```

### 3. Notification
Does not expect a response. Lacks an `id` field.
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "file:///example.txt"
  }
}
```

## MCP vs Alternatives

| Feature | MCP | Custom REST APIs | OpenAI Plugins |
|---------|-----|------------------|----------------|
| Standardization | Universal protocol | Ad-hoc | Vendor-specific |
| Communication | Bi-directional (JSON-RPC) | Uni-directional (HTTP) | Uni-directional (HTTP) |
| Core Abstractions | Resources, Tools, Prompts | Endpoints | Endpoints (OpenAPI spec) |
| Transport | stdio, HTTP/SSE | HTTP | HTTP |
| Focus | Context provision | General data transfer | ChatGPT integration |

## Capability Negotiation

When a client connects to a server, they must negotiate capabilities to ensure compatibility. This happens during the `initialize` phase.

The client sends its capabilities (e.g., supporting sampling, roots).
The server responds with its capabilities (e.g., providing tools, resources, logging).

If a server declares support for `tools`, the client knows it can send `tools/list` requests.

## The MCP Lifecycle

The connection lifecycle consists of:
1. **Initialization**: Client sends `initialize`, server responds. Client sends `notifications/initialized`.
2. **Discovery**: Client queries available primitives (e.g., `tools/list`, `resources/list`).
3. **Operation**: Client reads resources, calls tools, or uses prompts based on user interactions.
4. **Termination**: Client sends `exit` notification and closes the transport.

### Real JSON Example: Initialization

**Client Request (`initialize`)**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": {
      "name": "Claude Desktop",
      "version": "1.0.0"
    },
    "capabilities": {
      "roots": { "listChanged": true },
      "sampling": {}
    }
  }
}
```

**Server Response**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "Local Database Server",
      "version": "0.1.0"
    },
    "capabilities": {
      "tools": { "listChanged": true },
      "resources": { "subscribe": true }
    }
  }
}
```

**Client Notification (`initialized`)**
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized",
  "params": {}
}
```

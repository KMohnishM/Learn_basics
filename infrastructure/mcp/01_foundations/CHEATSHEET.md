# CHEATSHEET: MCP Foundations

## Architecture Diagram
```text
[ AI App / Client ] <--- JSON-RPC 2.0 (stdio/HTTP) ---> [ MCP Server ]
```

## The 4 Primitives
| Primitive | Type | Purpose | Example |
|-----------|------|---------|---------|
| **Resources** | Server-side | Read-only context provision | `file:///logs/error.log` |
| **Tools** | Server-side | Executable actions / dynamic data | `query_database(sql)` |
| **Prompts** | Server-side | Templated instructions | `explain_schema_prompt` |
| **Sampling** | Client-side | AI completion requests from server | Orchestrating an agent |

## JSON-RPC 2.0 Structure
**Request (has `id`)**
```json
{"jsonrpc": "2.0", "id": 1, "method": "...", "params": {}}
```
**Response (matches `id`)**
```json
{"jsonrpc": "2.0", "id": 1, "result": {}} // or "error": {}
```
**Notification (no `id`)**
```json
{"jsonrpc": "2.0", "method": "...", "params": {}}
```

## Connection Lifecycle Steps
1. **Initialize Request** (`client -> server`): Sends protocol version and client capabilities.
2. **Initialize Response** (`server -> client`): Sends server capabilities.
3. **Initialized Notification** (`client -> server`): Acknowledges setup.
4. **Discovery** (`client -> server`): `tools/list`, `resources/list`.
5. **Operation** (Bi-directional): `tools/call`, `resources/read`.
6. **Exit Notification** (`client -> server`): Client shuts down connection.

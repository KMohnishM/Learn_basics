# Module 6: Sampling and Roots in MCP

## Introduction

This module covers two advanced and powerful capabilities in the Model Context Protocol: **Sampling** and **Roots**.
While Tools, Resources, and Prompts represent data flowing *from* the server *to* the client, Sampling reverses the traditional flow of LLM execution, and Roots provide foundational boundary configuration for server operations.

## Sampling: Server-Initiated LLM Execution

Traditionally, the Client (which hosts the LLM) drives the interaction, deciding when to call Server tools. **Sampling** flips this dynamic.
If a Client advertises the `sampling` capability, the Server can ask the Client to generate LLM completions (sample from the model) on its behalf.

### Why does Sampling exist?
1.  **Agentic Servers**: A server might contain complex logic that requires AI reasoning to proceed. Instead of requiring the server developer to manage their own OpenAI API keys and LLM dependencies, the server delegates the reasoning task back to the client's configured LLM.
2.  **Autonomous Workflows**: A server tool might trigger a background job. During that job, the server needs to summarize a document. It can use sampling to ask the client for that summary.
3.  **Cost and Context Sharing**: It centralizes token usage, billing, and model preference management in the Client.

### The `sampling/createMessage` Request

The server sends a `sampling/createMessage` request to the client. It provides:
*   `messages`: The conversation history or prompt.
*   `modelPreferences`: Hints about what kind of model is needed.
*   `systemPrompt`: Optional system instructions.
*   `maxTokens`: Generation limit.

```json
{
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Summarize this error: java.lang.NullPointerException at..."
        }
      }
    ],
    "modelPreferences": {
      "costPriority": 0.1,
      "speedPriority": 0.9,
      "intelligencePriority": 0.5
    },
    "maxTokens": 200
  }
}
```

### Model Preferences
The server cannot force the client to use a specific model (e.g., "gpt-4o"). Instead, it provides floats between 0 and 1 indicating priorities:
*   `costPriority`: High value means "use a cheap model".
*   `speedPriority`: High value means "use a fast model".
*   `intelligencePriority`: High value means "use the smartest model available".

The client interprets these and selects the appropriate local or remote model.

### Sampling Security
Sampling is a security boundary. A server asking the client to generate text could be an attempt to exfiltrate data or phish the user. Clients typically implement strict human-in-the-loop (HITL) approval for sampling requests, or run them in highly isolated contexts.

## Full Python Example: Server Auto-Generating Summaries

In this example, a server provides a tool to fetch server logs. It uses sampling to ask the client to summarize the logs before returning them to the main conversation.

*(Note: The mcp Python SDK supports sending sampling requests via the `session` object).*

```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("sampling-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_summarized_logs",
            description="Fetches logs and uses the LLM to summarize them.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "get_summarized_logs":
        raise ValueError("Unknown tool")

    # 1. Fetch raw data (simulated)
    raw_logs = "ERROR: DB Connection failed. RETRY: Success. WARN: Memory high."

    # 2. Ask the client to sample (summarize)
    # This requires access to the active request context/session
    request_context = app.request_context
    
    if not request_context or not request_context.session:
        return [TextContent(type="text", text=f"Raw logs (sampling unavailable): {raw_logs}")]

    try:
        sampling_result = await request_context.session.create_message(
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text", 
                        "text": f"Summarize these logs concisely: {raw_logs}"
                    }
                }
            ],
            model_preferences={
                "speedPriority": 0.8,
                "intelligencePriority": 0.2
            },
            max_tokens=100
        )
        
        summary_text = sampling_result.content.text
        return [TextContent(type="text", text=f"Log Summary:\n{summary_text}")]
        
    except Exception as e:
         return [TextContent(type="text", text=f"Failed to summarize logs: {str(e)}")]

if __name__ == "__main__":
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    asyncio.run(main())
```
*Note: Depending on the specific MCP SDK version, accessing the session for sampling requires being within the active request context.*

## Roots: Defining Boundaries

**Roots** define the operational boundaries for an MCP server. They tell the server which directories, files, or URIs it is permitted to access.

If a client advertises the `roots` capability, the server can request the list of approved roots via `roots/list`.

### Roots Negotiation
1.  Server sends `roots/list` to Client.
2.  Client returns a list of `Root` objects.

```json
{
  "method": "roots/list",
  "result": {
    "roots": [
      {
        "uri": "file:///Users/jane/projects/backend",
        "name": "Backend Repository"
      }
    ]
  }
}
```

### Practical Roots Usage
Roots are essential for security. A file-system tool server *must not* allow tools to read `/etc/shadow` or write to `C:\Windows`.
By requesting roots, the server restricts its operations solely to the paths provided by the client.
If a tool request asks to modify a file outside the provided roots, the server should explicitly reject the request.

### Dynamic Roots Updates
Clients can change roots mid-session (e.g., if a user opens a new workspace).
The client sends a `notifications/roots/list_changed` notification. The server responds by re-fetching `roots/list` and updating its internal boundary validation logic.

## Capability Flags

Both Sampling and Roots rely on Client Capabilities. During the initial `initialize` handshake, the client sends its capabilities:

```json
"capabilities": {
  "sampling": {},
  "roots": {
    "listChanged": true
  }
}
```
A robust server must check these flags. If a client does not provide the `sampling` capability, the server must either degrade gracefully or refuse to operate tools that depend on it.

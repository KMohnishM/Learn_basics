# Module 8: MCP Integrations and Clients

Once an MCP server is built, it must be integrated with an MCP client to be useful. Clients range from desktop applications and IDEs to custom scripts. This module covers integrating servers with popular clients and building your own custom client.

## Claude Desktop Integration

Claude Desktop natively supports connecting to local MCP servers. Configuration is managed via a JSON file.

**Configuration Path**:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration Structure**:
The configuration defines the command to execute and the environment variables required.

```json
{
  "mcpServers": {
    "weather-server": {
      "command": "uvx",
      "args": ["mcp-weather-server"],
      "env": {
        "WEATHER_API_KEY": "your_api_key_here"
      }
    },
    "postgres-db": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"]
    }
  }
}
```

Upon launching Claude Desktop, it spawns these processes, establishes `stdio` connections, and retrieves their capabilities. The tools and resources are then seamlessly available to the LLM during conversation.

## Cursor IDE Integration

Cursor, an AI-powered code editor, supports MCP servers to give the AI context about the local environment or external APIs.

**Configuration**:
1. Open Cursor Settings.
2. Navigate to Features -> MCP.
3. Click "Add New MCP Server".
4. Select the transport type (usually `stdio`).
5. Provide the command (e.g., `uvx mcp-server-git`).

Cursor specifically benefits from tools that analyze codebase structure, interact with linters, or pull tickets from Jira/Linear.

## MCP Inspector

The MCP Inspector is a critical debugging tool. It acts as an interactive web-based client, allowing developers to test their servers manually without invoking an LLM.

**Running the Inspector**:
```bash
# General syntax
npx @modelcontextprotocol/inspector <command> <args>

# Example: Testing a Python server
npx @modelcontextprotocol/inspector uv run src/server.py
```

The inspector launches a local web application where you can:
- View all exposed tools, resources, and prompts.
- Execute tools with arbitrary JSON payloads and view the raw results.
- Inspect the JSON-RPC traffic for debugging protocol errors.

## Building a Custom Client

Sometimes you need to integrate MCP into your own application or agent framework. You can build a client using the SDK.

### Minimal Python Client Example

Below is a complete, minimal client that connects to an MCP server, lists its tools, and calls one.

```python
# client.py
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_client():
    # Define how to start the server
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env=None
    )

    # Establish the stdio connection
    async with stdio_client(server_params) as (read, write):
        # Initialize the session
        async with ClientSession(read, write) as session:
            # Perform protocol handshake
            await session.initialize()
            
            print("Connected to server.")
            
            # List available tools
            tools_response = await session.list_tools()
            print("\nAvailable Tools:")
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")
                
            # Example: Call a tool (assuming a 'get_weather' tool exists)
            tool_name = "get_weather"
            if any(t.name == tool_name for t in tools_response.tools):
                print(f"\nCalling {tool_name}...")
                try:
                    result = await session.call_tool(
                        name=tool_name, 
                        arguments={"location": "san_francisco"}
                    )
                    
                    # Process the result
                    for content in result.content:
                        if content.type == "text":
                            print(f"Result: {content.text}")
                except Exception as e:
                    print(f"Error calling tool: {e}")

if __name__ == "__main__":
    asyncio.run(run_client())
```

## Connecting to Remote Servers

While `stdio` is standard for local tools, `SSE` (Server-Sent Events) is used for remote servers over HTTP.

To connect a client to an SSE server:
1. The server exposes an HTTP endpoint (e.g., `/mcp/sse`).
2. The client uses `sse_client(url)` instead of `stdio_client(params)`.
3. The server pushes messages over SSE, and the client posts JSON-RPC messages to a designated HTTP POST endpoint.

## Popular Public MCP Servers

Integrating community servers can rapidly expand capabilities:
-   **`@modelcontextprotocol/server-postgres`**: Execute read-only SQL queries.
-   **`@modelcontextprotocol/server-github`**: Manage issues, PRs, and read repositories.
-   **`@modelcontextprotocol/server-slack`**: Read channels and post messages.
-   **`mcp-server-sqlite`**: Interact with local SQLite databases.

## Multi-Server Setups

Advanced clients connect to multiple servers simultaneously. The client merges the tools and resources from all servers into a single context pool for the LLM. 
-   **Conflict Resolution**: If two servers expose a tool with the same name, the client must namespace them (e.g., `github_create_issue` vs `linear_create_issue`) or reject the duplicate.

## Troubleshooting Guide

1.  **Connection Closed Instantly**: The server process exited or crashed on startup. Check the command and arguments. Ensure the server script is executable.
2.  **JSON Parse Error**: The server printed non-JSON data to `stdout`. Ensure all standard logging is routed to `stderr`.
3.  **Command Not Found**: The binary (like `uvx`, `npx`, or `python`) is not in the system PATH of the client application (common when launching Claude Desktop via GUI rather than terminal). Provide absolute paths in the configuration.
4.  **Timeout**: The tool logic is blocking the event loop or taking too long. Optimize the tool or implement progress notifications.

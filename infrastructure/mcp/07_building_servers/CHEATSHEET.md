# Module 7: Building MCP Servers - Cheatsheet

## FastMCP Decorator Reference (Python)

```python
from mcp.server.fastmcp import FastMCP

app = FastMCP("my-server")

# Define a tool
@app.tool()
async def calculate(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y

# Define a static resource
@app.resource("config://app.json")
async def get_config() -> str:
    return '{"debug": true}'

# Define a dynamic resource template
@app.resource("file:///{filepath}")
async def read_file(filepath: str) -> str:
    return open(filepath).read()

# Define a prompt template
@app.prompt()
def review_code(repo: str) -> str:
    return f"Review the code in {repo}"

# Lifecycle hooks
@app.on_startup
async def setup():
    pass

@app.on_shutdown
async def teardown():
    pass

# Run the server
if __name__ == "__main__":
    app.run()
```

## SDK Class Hierarchy (TypeScript)

-   `Server`: Main class representing the MCP Server.
-   `StdioServerTransport`: Transport implementation for stdin/stdout communication.
-   `SSEServerTransport`: Transport implementation for Server-Sent Events over HTTP.
-   **Schemas**:
    -   `ListToolsRequestSchema`: Client requests list of tools.
    -   `CallToolRequestSchema`: Client invokes a tool.
    -   `ListResourcesRequestSchema`: Client requests list of resources.
    -   `ReadResourceRequestSchema`: Client reads a specific resource.
    -   `ListPromptsRequestSchema`: Client requests list of prompts.
    -   `GetPromptRequestSchema`: Client requests a specific prompt.

## TypeScript Setup Snippet

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server({ name: "my-server", version: "1.0.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{ name: "ping", description: "Replies with pong", inputSchema: { type: "object", properties: {} } }]
}));

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
main();
```

## Testing Commands

**Python (pytest)**
```bash
# Test FastMCP functions directly
pytest tests/
```

**MCP Inspector (Test server interactively)**
```bash
# Run inspector against a python server
npx @modelcontextprotocol/inspector uv run server.py

# Run inspector against a node server
npx @modelcontextprotocol/inspector node dist/index.js
```

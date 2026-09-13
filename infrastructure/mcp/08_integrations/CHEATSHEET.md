# Module 8: Integrations and Clients - Cheatsheet

## Claude Desktop Configuration Template

**File Location**:
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Win: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-python-server": {
      "command": "uv",
      "args": [
        "run",
        "--manifest-path",
        "/absolute/path/to/pyproject.toml",
        "server.py"
      ],
      "env": {
        "MY_API_KEY": "sk-12345"
      }
    },
    "my-node-server": {
      "command": "node",
      "args": ["/absolute/path/to/build/index.js"]
    }
  }
}
```

## Cursor IDE Configuration

1. Settings -> Features -> MCP
2. Click **+ Add New MCP Server**
3. Type: `command`
4. Name: `my-server`
5. Command: `node /absolute/path/to/server.js`

## MCP Inspector Commands

Run against a local script:
```bash
npx @modelcontextprotocol/inspector python server.py
```

Run an npx-executable server:
```bash
npx @modelcontextprotocol/inspector npx @modelcontextprotocol/server-postgres postgresql://localhost/db
```

## Python Custom Client Snippet

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command="python", args=["server.py"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List Tools
            tools = await session.list_tools()
            
            # Call Tool
            result = await session.call_tool(
                name="my_tool", 
                arguments={"arg1": "value"}
            )
            print(result.content[0].text)

asyncio.run(main())
```

## Debugging Checklist

1. **Process exits immediately?** Check paths in command/args. Use absolute paths.
2. **JSON parse error?** Ensure the server is NOT printing logs to `stdout`.
3. **No tools showing up?** Restart the client (Claude/Cursor) to force a re-initialization.
4. **Environment variable missing?** Define it in the `env` block of the config file.

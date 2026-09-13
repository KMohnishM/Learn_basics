# Module 3: Tools in MCP

## What is an MCP Tool?
In the Model Context Protocol, a **Tool** is an executable function exposed by the server that the AI client can invoke. While Resources provide read-only context, Tools provide the AI with agency—the ability to act upon the world or retrieve dynamically parameterized data (like running a specific SQL query).

## Tool Definition Anatomy
When a client asks for available tools via `tools/list`, the server responds with a list of tool definitions. A tool definition consists of:
1. `name`: Unique identifier for the tool.
2. `description`: Human and AI-readable explanation of what the tool does (critical for the LLM to understand when to use it).
3. `inputSchema`: A strict JSON Schema defining the expected arguments.

## JSON Schema for Inputs
MCP relies heavily on JSON Schema to ensure the LLM structures its tool call arguments correctly.

```json
{
  "name": "search_database",
  "description": "Searches the customer database by email.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "email": {
        "type": "string",
        "description": "The customer's exact email address"
      },
      "limit": {
        "type": "integer",
        "default": 10
      }
    },
    "required": ["email"]
  }
}
```

## Tool Handler Patterns
When the AI decides to use a tool, the client sends a `tools/call` request. The server must route this request to the corresponding handler function, parse the arguments, execute the logic, and return the result formatted as specific Content Types.

### Content Types
A tool response can contain a list of content objects, allowing mixed-media responses.
- `text`: Plain text or markdown.
- `image`: Base64 encoded image data.
- `resource`: Embedded resource data.

## Full Python Example: Providing Tools

Using the `mcp` SDK, creating tools is highly streamlined using decorators and Python type hints (which auto-generate the JSON schema).

```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

app = Server("utility-tools")

# Example 1: Data Retrieval Tool
@app.tool()
async def search_database(query: str, limit: int = 5) -> list[TextContent]:
    """
    Search the internal knowledge base.
    
    Args:
        query: The search term or keywords.
        limit: Maximum number of results to return.
    """
    # Simulated database lookup
    results = f"Simulated results for '{query}' (max {limit})"
    
    return [
        TextContent(
            type="text",
            text=results
        )
    ]

# Example 2: Action Tool
@app.tool()
async def create_file(filename: str, content: str) -> list[TextContent]:
    """
    Create a new text file on the server's local disk.
    
    Args:
        filename: Name of the file (e.g., 'notes.txt')
        content: The text content to write to the file.
    """
    try:
        with open(filename, "w") as f:
            f.write(content)
        return [TextContent(type="text", text=f"Successfully created {filename}")]
    except Exception as e:
        # It is best practice to return errors as text content so the LLM can read them
        return [TextContent(type="text", text=f"Failed to create file: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

## Pagination
For servers exposing hundreds of tools, the `tools/list` endpoint supports pagination. The client sends a `cursor` parameter, and the server returns a `nextCursor` in its response if more tools are available.

## Tool Best Practices
1. **Descriptive Names**: Use clear, action-oriented names (e.g., `get_user_profile` instead of `user`).
2. **Verbose Descriptions**: The description is the prompt for the LLM. Explain *when* to use it, what it returns, and any edge cases.
3. **Graceful Error Handling**: Do not crash the server on invalid inputs. Catch exceptions and return a text response explaining the error so the LLM can self-correct.
4. **Human-in-the-loop**: For destructive actions (like `delete_database`), be aware that well-designed clients will prompt the user for confirmation before sending the `tools/call` request.

## Common Mistakes
- Returning raw strings instead of an array of Content objects (e.g., `TextContent`).
- Failing to mark required fields in the JSON schema, leading to the LLM omitting crucial arguments.
- Making tool descriptions too brief, causing the LLM to hallucinate tool usage.

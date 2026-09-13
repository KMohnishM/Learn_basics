# CHEATSHEET: MCP Tools

## Tool Definition Template (JSON)
```json
{
  "name": "calculate_tax",
  "description": "Calculates sales tax. Use this when the user asks for total pricing.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "amount": { "type": "number", "description": "Base price" },
      "state": { "type": "string", "description": "2-letter US state code" }
    },
    "required": ["amount", "state"]
  }
}
```

## Content Type Reference
Tools return an array of these objects:

**Text:**
```json
{
  "type": "text",
  "text": "The tax is $4.50"
}
```

**Image:**
```json
{
  "type": "image",
  "data": "iVBORw0KGgo...", 
  "mimeType": "image/png"
}
```

## Python SDK Annotation Cheatsheet
The `mcp` Python SDK automates schema generation via decorators.

```python
from mcp.server import Server
from mcp.types import TextContent

app = Server("my-server")

@app.tool()
async def read_file(path: str) -> list[TextContent]:
    """
    Docstring becomes the tool description.
    Args become the inputSchema properties.
    """
    with open(path, 'r') as f:
        return [TextContent(type="text", text=f.read())]
```

## Quick Best Practices
- ✏️ **Always type-hint** your Python arguments to generate accurate schemas.
- 📝 **Write verbose docstrings**; this is the LLM's only instruction manual.
- 🛡️ **Return errors as text** (don't throw uncaught exceptions) so the LLM can self-correct.
- 📄 **Use pagination** (`cursor`/`nextCursor`) if you have more than 50 tools.

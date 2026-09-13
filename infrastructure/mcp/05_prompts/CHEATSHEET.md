# Module 5: Prompts Cheatsheet

## Anatomy of a Prompt Request/Response
1.  **List**: Client asks `prompts/list`. Server returns Prompt definitions (name, description, arguments).
2.  **Get**: Client asks `prompts/get` with Name + Arguments. Server returns array of `PromptMessage`.

## Argument Definition
```json
{
  "name": "filepath",
  "description": "Path to the target file",
  "required": true
}
```

## PromptMessage Structure
```json
{
  "role": "user",      // or "assistant"
  "content": [         // Array of content blocks
    {
      "type": "text",
      "text": "Analyze this data."
    }
  ]
}
```

## Embedded Resource Syntax
Use `type: "resource"` to inject context directly into the prompt content array.
```json
{
  "type": "resource",
  "resource": {
    "uri": "file:///var/log/syslog",
    "mimeType": "text/plain",
    "text": "[ERROR] Server crashed..."
  }
}
```

## Python SDK Quick Ref

**List Prompts:**
```python
@app.list_prompts()
async def list_p():
    return [
        Prompt(
            name="debug_log",
            description="Analyze a log file",
            arguments=[PromptArgument(name="path", required=True)]
        )
    ]
```

**Get Prompt:**
```python
@app.get_prompt()
async def get_p(name: str, args: dict[str, str] | None):
    path = args.get("path")
    return mcp.types.GetPromptResult(
        messages=[
            PromptMessage(
                role="user",
                content=[
                    TextContent(type="text", text="Fix this log:"),
                    EmbeddedResource(
                        type="resource",
                        resource=TextResourceContents(
                            uri=f"file://{path}",
                            mimeType="text/plain",
                            text="log data here"
                        )
                    )
                ]
            )
        ]
    )
```

## Best Practices
*   **Keep arguments simple**: strings only.
*   **Use Embedded Resources**: Instead of pasting massive strings into the `text` field, use the formal Embedded Resource structure for cleaner client parsing.
*   **UI Focus**: Remember that clients render these as menus (e.g., `/debug_log <path>`). Keep descriptions clear.

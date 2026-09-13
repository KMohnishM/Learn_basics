# Module 5: Prompts in MCP

## Introduction

In the Model Context Protocol (MCP), **Prompts** provide a way for servers to supply pre-defined, parameterized prompt templates to clients. This allows server developers to encode domain-specific expertise, workflows, and context structures into reusable prompts that users (or autonomous agents) can easily invoke.

By exposing Prompts, an MCP server essentially says: "I know the best way to ask the LLM to process my specific data. Here is a template for that request."

This module covers what prompts are, how they differ from other concepts, how to define and parameterize them, and how to embed resources directly into prompt responses.

## Prompts vs. System Prompts vs. Tool Descriptions

It is critical to distinguish MCP Prompts from other LLM concepts:

1.  **System Prompts**: Global instructions given to an LLM governing its overall behavior, persona, and constraints across a whole conversation. MCP Prompts *do not* configure system prompts.
2.  **Tool Descriptions**: Metadata sent to the LLM explaining what a tool does so the LLM can decide when to call it autonomously.
3.  **MCP Prompts**: User-facing templates (often presented in a client UI, like slash commands in an IDE) that generate a specific list of messages (user/assistant) to append to the conversation. They are a way to *bootstrap* or *steer* a specific interaction.

## Prompt Definition

An MCP Prompt is defined by a name, a description, and a list of arguments. When a client wants to discover available prompts, it calls `prompts/list`.

```json
{
  "method": "prompts/list",
  "result": {
    "prompts": [
      {
        "name": "code_review",
        "description": "Performs a thorough code review of a specific file.",
        "arguments": [
          {
            "name": "filepath",
            "description": "Absolute path to the file to review",
            "required": true
          }
        ]
      }
    ]
  }
}
```

## Prompt Response Structure

When a client wants to use a prompt, it calls `prompts/get`, passing the prompt name and any required arguments. The server responds with a `PromptMessage` array.

A `PromptMessage` contains:
*   `role`: Either `user` or `assistant`.
*   `content`: An array of content blocks (Text or Embedded Resources).

```json
{
  "method": "prompts/get",
  "params": {
    "name": "code_review",
    "arguments": {
      "filepath": "/app/main.py"
    }
  },
  "result": {
    "description": "Review of /app/main.py",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Please review the following code for security vulnerabilities and performance issues. Focus on the database connection logic."
          }
        ]
      }
    ]
  }
}
```

## Embedded Resources in Prompts

One of the most powerful features of MCP Prompts is the ability to embed resources directly into the prompt response. Instead of just sending text, the server can fetch a resource and attach it as context.

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "Review this file:"
    },
    {
      "type": "resource",
      "resource": {
        "uri": "file:///app/main.py",
        "mimeType": "text/x-python",
        "text": "def connect():\n  pass"
      }
    }
  ]
}
```
This guarantees the LLM receives the exact, up-to-date context required for the prompt.

## Full Python Example: Code Review Prompt

This server exposes a `code_review` prompt that takes a filepath argument, reads the file from the local disk, and constructs a multi-message prompt containing the file's content as an embedded resource.

```python
import asyncio
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent, EmbeddedResource, TextResourceContents

app = Server("prompt-server")

@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="code_review",
            description="Generate a comprehensive code review request for a file",
            arguments=[
                PromptArgument(
                    name="filepath",
                    description="Absolute path to the file",
                    required=True
                ),
                PromptArgument(
                    name="focus",
                    description="Specific area to focus on (e.g., security, performance)",
                    required=False
                )
            ]
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> mcp.types.GetPromptResult:
    if name != "code_review":
        raise ValueError(f"Unknown prompt: {name}")
        
    args = arguments or {}
    filepath = args.get("filepath")
    
    if not filepath:
        raise ValueError("filepath argument is required")
        
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    with open(filepath, "r", encoding="utf-8") as f:
        code_content = f.read()
        
    focus = args.get("focus", "general quality and readability")
    
    instruction = f"Please act as a senior engineer and review this code. Focus heavily on: {focus}."
    
    messages = [
        PromptMessage(
            role="user",
            content=[
                TextContent(type="text", text=instruction),
                EmbeddedResource(
                    type="resource",
                    resource=TextResourceContents(
                        uri=f"file://{filepath}",
                        mimeType="text/plain",
                        text=code_content
                    )
                )
            ]
        )
    ]
    
    return mcp.types.GetPromptResult(
        description=f"Code review for {os.path.basename(filepath)}",
        messages=messages
    )

if __name__ == "__main__":
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    asyncio.run(main())
```

## Dynamic Prompts and Chaining

Because `prompts/get` runs server-side Python code, prompts can be highly dynamic. A prompt could:
1.  Query a database to fetch live schema information.
2.  Make an API call to a ticketing system to embed bug context.
3.  Synthesize multiple files into a single context window.

**Prompt Chaining**: While MCP does not explicitly enforce chaining, you can design prompts that ask the LLM to output specific structures, which a client script then parses to trigger subsequent prompts or tool calls.

## UX Considerations

When designing prompts:
1.  **Keep Arguments Simple**: Use primitive string arguments. If you need complex data, use the arguments as keys to fetch that data server-side.
2.  **Clear Descriptions**: Clients often surface prompts in UI command palettes (e.g., `/code_review`). The prompt description must be clear and concise.
3.  **Role Usage**: Usually, you only need the `user` role. Avoid overly complex `assistant` role pre-filling unless you are strictly forcing a specific output format.

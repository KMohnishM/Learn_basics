# QnA: MCP Tools

**1. What is the primary function of a Tool in MCP?**
**Answer**: A tool allows the AI model to execute functions on the server, enabling it to retrieve dynamic data or perform actions, unlike Resources which provide static, read-only data.

**2. What three properties define an MCP Tool in a `tools/list` response?**
**Answer**: `name`, `description`, and `inputSchema`.

**3. Why is the `description` field of a tool critical?**
**Answer**: The description acts as the prompt instructions for the AI model. It is the sole source of truth the LLM uses to decide *when* and *how* to invoke the tool.

**4. What standard is used to define tool arguments in the `inputSchema`?**
**Answer**: JSON Schema.

**5. How does a client execute a tool?**
**Answer**: By sending a `tools/call` JSON-RPC request containing the tool's name and the required arguments.

**6. What format must the result of a tool execution take?**
**Answer**: The result must be an array of Content objects (such as `TextContent` or `ImageContent`).

**7. Can a single tool return both text and an image?**
**Answer**: Yes, the result is an array of Content objects, so a server can return a `TextContent` object followed by an `ImageContent` object in the same response.

**8. In Python MCP SDKs, how is the JSON schema typically generated?**
**Answer**: The SDK automatically infers and generates the JSON schema from the Python function's type hints and docstrings.

**9. What is the recommended way to handle execution errors within a tool?**
**Answer**: Catch the exception and return a `TextContent` response describing the error in plain English. This allows the LLM to read the error, understand what went wrong, and attempt to self-correct and call the tool again.

**10. How does a client discover available tools?**
**Answer**: By sending a `tools/list` request to the server.

**11. How is pagination handled for a large number of tools?**
**Answer**: The `tools/list` request accepts an optional `cursor` string. The response returns a list of tools and optionally a `nextCursor` string, which the client can use in subsequent requests to fetch the next page.

**12. What distinguishes a tool from a resource in terms of state mutation?**
**Answer**: Resources are strictly read-only and should never mutate state. Tools are designed for agency and can mutate state (e.g., writing files, sending emails).

**13. Do tools execute directly on the client's machine?**
**Answer**: No, tools execute on the MCP Server. The client merely sends a request to execute them.

**14. What should a developer consider regarding destructive tools (e.g., deleting files)?**
**Answer**: Developers should assume that client implementations will require explicit human approval before executing tools. The tool description should clearly state the destructive nature of the action.

**15. If an LLM frequently calls a tool with missing required arguments, what is the likely cause?**
**Answer**: The tool's `inputSchema` likely failed to mark those properties as `required` in the JSON Schema definition, leading the LLM to believe they were optional.

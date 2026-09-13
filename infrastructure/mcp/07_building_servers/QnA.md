# Module 7: Building MCP Servers - Q&A

1. **Question**: What is the primary advantage of using FastMCP over the low-level Python SDK?
**Answer**: FastMCP provides a high-level, decorator-based framework that automatically infers JSON schemas for tools and resources from Python type hints and docstrings. This significantly reduces boilerplate and prevents schema drift compared to the low-level API where schemas must be defined manually in JSON format.

2. **Question**: When writing an MCP server that communicates over `stdio`, why must you avoid using `print()` (Python) or `console.log()` (TypeScript)?
**Answer**: When using `stdio` transport, standard output (`stdout`) is strictly reserved for the JSON-RPC messages used by the MCP protocol. Printing normal text or logs to `stdout` will corrupt the JSON payload, causing the client to fail parsing the message and crash the connection. Logs should be sent to `stderr` or a file.

3. **Question**: How does an MCP server signify to the client that a tool execution encountered a handled error that the LLM should know about?
**Answer**: The server should catch the exception and return a standard tool response object, but set the `isError` flag to `true`. The content of the response should contain the error message. This allows the LLM to read the error and attempt to fix its input, rather than crashing the server.

4. **Question**: In the TypeScript SDK, what library is commonly used in conjunction with the Server class to validate incoming tool arguments?
**Answer**: Zod is the standard library used in the TypeScript SDK ecosystem to define schemas, generate JSON Schema definitions for the client, and validate the runtime arguments passed in `CallToolRequestSchema`.

5. **Question**: What is the purpose of the `@app.on_startup` decorator in FastMCP?
**Answer**: It registers a lifecycle hook that executes an asynchronous function before the server begins processing client requests. It is used to initialize database connections, load large models into memory, or validate environment variables.

6. **Question**: How do Resource Templates differ from standard Resources?
**Answer**: Standard Resources represent a single, static entity with a fixed URI. Resource Templates use URI patterns (like `file:///{path}`) allowing a server to expose an infinite or highly dynamic set of resources without having to explicitly list all of them in a `ListResources` request.

7. **Question**: If you want to expose a Python function as an MCP tool using FastMCP, what must you include in the function definition for it to work correctly?
**Answer**: You must include precise type hints for all arguments and a descriptive docstring. FastMCP relies on these elements to generate the description and JSON schema that the LLM uses to understand how and when to call the tool.

8. **Question**: What transport protocol is most commonly used for local MCP server development and execution?
**Answer**: `stdio` (Standard Input/Output) is the most common transport. The client spawns the server as a subprocess and communicates by writing to its `stdin` and reading from its `stdout`.

9. **Question**: Can a single MCP server expose tools, resources, and prompts simultaneously?
**Answer**: Yes, an MCP server can expose any combination of capabilities. It declares which capabilities it supports during the initial handshake with the client.

10. **Question**: In TypeScript, how do you register the handler that responds to a client asking "what tools do you have"?
**Answer**: You call `server.setRequestHandler(ListToolsRequestSchema, async () => { ... })` and return an object containing an array of tool definitions with their schemas.

11. **Question**: How can you unit test a FastMCP tool function in Python?
**Answer**: Because FastMCP tools are standard Python functions decorated with `@app.tool()`, you can import the underlying function directly into a `pytest` file and call it with mock arguments, entirely bypassing the MCP JSON-RPC layer.

12. **Question**: What does the `capabilities` object do in the initialization of a TypeScript `Server`?
**Answer**: It explicitly tells the client which MCP features the server supports. For instance, setting `capabilities: { tools: {}, resources: {} }` informs the client it can send `ListTools` and `ListResources` requests.

13. **Question**: Why might you choose the low-level Python SDK over FastMCP?
**Answer**: You would use the low-level SDK if you need to dynamically register or unregister tools at runtime based on external factors, if you are integrating with a legacy codebase lacking type hints, or if you need granular control over the raw JSON-RPC message lifecycle.

14. **Question**: What is the recommended way to distribute a Python-based MCP server?
**Answer**: The recommended way is to package the server using a `pyproject.toml` file so it can be installed globally via `pipx` or `uv tool install`, allowing the client to execute the command directly.

15. **Question**: What happens if an MCP server takes too long to respond to a `CallTool` request?
**Answer**: The client typically implements a timeout. If the server exceeds this timeout, the client will abort the request and inform the user/LLM that the tool call failed due to a timeout. The server process itself might continue running the task in the background unless it handles cancellation tokens.

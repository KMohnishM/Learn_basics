# Module 8: Integrations and Clients - Q&A

1. **Question**: Where is the configuration file located for connecting servers to Claude Desktop on Windows?
**Answer**: On Windows, the configuration file is located at `%APPDATA%\Claude\claude_desktop_config.json`.

2. **Question**: In a Claude Desktop configuration, what are the `command` and `args` fields used for?
**Answer**: They define how Claude Desktop should launch the MCP server as a subprocess. The `command` is the executable (like `npx` or `python`), and `args` is an array of arguments passed to that executable (like `["-y", "mcp-server"]`).

3. **Question**: What is the primary purpose of the MCP Inspector?
**Answer**: The MCP Inspector is an interactive web-based debugging tool that allows developers to connect to an MCP server, view its capabilities, execute tools manually, and inspect the raw JSON-RPC traffic without needing an LLM.

4. **Question**: When building a custom Python client, what object manages the protocol handshake and state?
**Answer**: The `ClientSession` object manages the state and protocol details. You invoke `.initialize()` on it to perform the handshake.

5. **Question**: How do you pass API keys to an MCP server running in Claude Desktop?
**Answer**: You define them in the `env` object within the server's entry in `claude_desktop_config.json`. For example: `"env": { "API_KEY": "value" }`.

6. **Question**: If a server takes too long to respond to an initialization request, what usually happens?
**Answer**: The client will typically time out, kill the subprocess, and report a connection failure.

7. **Question**: What transport protocol should be used when building an MCP server that will be hosted in the cloud and accessed by remote clients?
**Answer**: SSE (Server-Sent Events) over HTTP should be used for remote communication, as `stdio` only works for local subprocesses.

8. **Question**: Why might an MCP server work perfectly in the terminal but fail to start in Claude Desktop?
**Answer**: This is often a PATH issue. GUI applications like Claude Desktop might not inherit the same environment variables (like PATH modifications for `npm` or `uv`) as your terminal. Using absolute paths for the `command` can resolve this.

9. **Question**: How does a client handle tool name collisions if it connects to two servers that both expose a tool named `search`?
**Answer**: The client is responsible for handling collisions. It typically namespaces the tools internally (e.g., prefixing them with the server name) before presenting them to the LLM, or it may reject the overlapping tools.

10. **Question**: What command launches the MCP Inspector to test a Node-based server in `build/index.js`?
**Answer**: `npx @modelcontextprotocol/inspector node build/index.js`

11. **Question**: In the Cursor IDE, how are MCP servers configured?
**Answer**: They are configured through the GUI in the Cursor Settings under Features -> MCP, where you can add the command and transport type.

12. **Question**: Can an MCP client dynamically add and remove servers during a session?
**Answer**: Yes, a client application can manage subprocesses dynamically, establishing new `ClientSession`s and injecting the newly discovered tools into the LLM's context on the fly.

13. **Question**: What Python library provides the `stdio_client` context manager for building clients?
**Answer**: The official `mcp` library (specifically `mcp.client.stdio`).

14. **Question**: What is a common architectural pattern for building an AI agent that uses MCP?
**Answer**: The agent loop retrieves the list of tools from the MCP Client, passes the tool schemas to the LLM, receives a tool call request from the LLM, passes it to the MCP Client to execute on the server, and returns the result back to the LLM.

15. **Question**: If an MCP server crashes while Claude Desktop is running, what does the client do?
**Answer**: The client detects the `stdio` stream closure. Well-designed clients will remove the server's tools from the active context, notify the user of the failure, and optionally attempt to restart the server process.

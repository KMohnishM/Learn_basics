# QnA: MCP Transport Layer

**1. What is the responsibility of the transport layer in MCP?**
**Answer**: The transport layer is responsible for the reliable delivery of JSON-RPC 2.0 messages between the MCP client and the MCP server.

**2. What are the two primary standard transports defined by MCP?**
**Answer**: stdio (Standard Input/Output) and HTTP + SSE (Server-Sent Events).

**3. How does the `stdio` transport work?**
**Answer**: The client spawns the server as a local child process. The client writes JSON-RPC messages to the server's standard input (`stdin`) and reads messages from the server's standard output (`stdout`).

**4. What is the primary security advantage of the `stdio` transport?**
**Answer**: It does not open any network ports, eliminating the risk of external network attacks and making it highly secure for local execution.

**5. How are messages separated in the `stdio` transport?**
**Answer**: Messages are framed using newline characters (`\n`). Each valid JSON-RPC object must be contained on a single line.

**6. Why is HTTP alone insufficient for MCP, requiring the use of SSE?**
**Answer**: HTTP is inherently uni-directional (client initiates request, server responds). MCP requires bi-directional communication (e.g., servers sending notifications or making sampling requests to the client). SSE allows the server to push messages asynchronously to the client.

**7. In the HTTP + SSE transport, how does the client send messages to the server?**
**Answer**: The client sends JSON-RPC messages via standard HTTP POST requests to a specific endpoint provided by the server during the SSE connection setup.

**8. In the HTTP + SSE transport, how does the server send messages to the client?**
**Answer**: The server streams JSON-RPC messages down the open Server-Sent Events (SSE) connection established by the client.

**9. What must a client do if the transport connection abruptly drops?**
**Answer**: The client should treat all pending requests as failed, clean up local state for that connection, and optionally implement a retry or restart mechanism to recover the server.

**10. What is a common use case for the `stdio` transport?**
**Answer**: Desktop applications like Claude Desktop or IDE extensions connecting to local utilities (like local file system access or local git repositories).

**11. What is a common use case for the HTTP + SSE transport?**
**Answer**: Connecting a local AI application to a remote, cloud-hosted data source or enterprise internal service.

**12. Can a single MCP server support both `stdio` and `SSE`?**
**Answer**: Yes, the core server logic is independent of the transport. Using SDKs, you can wrap the same server logic in either a `stdio` stream handler or an HTTP application framework.

**13. In Python, which context manager is used to initialize a stdio server?**
**Answer**: The `stdio_server()` context manager from `mcp.server.stdio`.

**14. What URL endpoint does a client typically connect to first when using the SSE transport?**
**Answer**: The client typically makes a GET request to the `/sse` endpoint to establish the stream.

**15. If a tool execution fails due to a bad SQL query, is this a transport error or a JSON-RPC error?**
**Answer**: This is a JSON-RPC error. The transport successfully delivered the message, but the application logic failed. The server will return a JSON-RPC response containing an `error` object over the healthy transport.

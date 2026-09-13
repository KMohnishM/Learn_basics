# QnA: MCP Foundations

**1. What specific problem does the Model Context Protocol (MCP) solve?**
**Answer**: MCP solves the "m x n" integration problem between AI models and data sources. Instead of writing custom integrations for every AI model to connect to every data source, MCP provides a universal standard. This reduces the problem to "m + n", where writing one MCP server makes the data available to all MCP-compliant clients.

**2. What underlying message protocol does MCP use?**
**Answer**: MCP uses JSON-RPC 2.0 as its underlying message protocol for all communications between clients and servers.

**3. What are the three message types in JSON-RPC 2.0 used by MCP?**
**Answer**: 
- **Requests**: Messages that expect a response and contain an `id`.
- **Responses**: Messages that reply to a request, matching its `id`, containing either a `result` or an `error`.
- **Notifications**: One-way messages that do not expect a response and do not contain an `id`.

**4. Name the four core primitives of MCP.**
**Answer**: Resources, Prompts, Tools, and Sampling.

**5. How do Resources differ from Tools in MCP?**
**Answer**: Resources are read-only data sources that provide static or dynamic context (like reading a file or database schema). Tools are executable functions that allow the AI to perform actions or retrieve parameterized data (like running a database query or writing to a file).

**6. What is the purpose of Prompts in MCP?**
**Answer**: Prompts are server-defined templates that help structure interactions. They provide the AI with pre-defined context, instructions, and structure for specific tasks related to the server's domain.

**7. Describe the "Sampling" primitive.**
**Answer**: Sampling is a client-side capability that allows the server to request AI completions from the client. This reverses the typical flow, enabling the server to orchestrate complex agentic tasks by leveraging the client's underlying LLM.

**8. What is the first message sent in the MCP lifecycle?**
**Answer**: The `initialize` request, sent from the client to the server.

**9. What must the client send immediately after receiving the initialization response?**
**Answer**: The client must send a `notifications/initialized` notification to acknowledge that initialization is complete.

**10. How does capability negotiation work in MCP?**
**Answer**: During the `initialize` request, the client sends its supported capabilities (e.g., sampling, roots). The server responds with its own supported capabilities (e.g., tools, resources). Both sides use this information to determine which features they can safely use during the session.

**11. Contrast MCP with OpenAI Plugins.**
**Answer**: OpenAI Plugins are vendor-specific and rely on OpenAPI specifications over HTTP, designed specifically for ChatGPT. MCP is an open, vendor-agnostic standard using bi-directional JSON-RPC over various transports (stdio, HTTP/SSE), focusing holistically on context provision.

**12. What role does the "Client" play in the MCP architecture?**
**Answer**: The Client (or Host) is the application that interfaces with the AI model (e.g., Claude Desktop or an IDE). It manages connections to MCP servers, negotiates capabilities, and translates AI intents into MCP requests.

**13. What is a URI in the context of MCP Resources?**
**Answer**: A URI (Uniform Resource Identifier) uniquely identifies a specific resource exposed by the server. It follows standard URI formatting, such as `file:///path/to/file` or `postgres://database/schema/table`.

**14. If a server does not declare support for `tools` during initialization, what should the client do?**
**Answer**: The client should not send `tools/list` or `tools/call` requests to the server, as the server has indicated it does not support the tools capability.

**15. Can an MCP connection operate locally without network access?**
**Answer**: Yes. MCP supports a `stdio` transport layer, which allows the client to spawn the server as a local subprocess and communicate securely over standard input and output streams without any network exposure.

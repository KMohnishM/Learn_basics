# Module 4: Resources QnA

**1. What is the primary purpose of an MCP Resource?**
**Answer:** An MCP Resource is designed to expose read-only data and content from the server to the client. It provides context to an LLM without causing any side effects or mutating state.

**2. How does a Resource differ from a Tool in MCP?**
**Answer:** A Resource is for idempotent, read-only data retrieval (e.g., reading a file or database row). A Tool is for executing actions that may have side effects (e.g., writing a file, creating a database entry, or performing a complex computation based on parametric input).

**3. What format is used to uniquely identify a resource in MCP?**
**Answer:** Resources are uniquely identified using standard IETF RFC 3986 URIs (e.g., `file:///path/to/file.txt` or `db://customers/123`).

**4. When should a server use a Resource Template instead of a static Resource?**
**Answer:** A Resource Template should be used when the dataset is too large to enumerate entirely (like a large database or deep filesystem). It allows the server to specify a URI pattern (e.g., `db://users/{id}`) that the client can dynamically construct and request.

**5. How does a client determine what static resources are available on a server?**
**Answer:** The client sends a `resources/list` request to the server, which responds with an array of available static resources, including their URIs, names, and MIME types.

**6. What are the two types of resource contents that an MCP server can return?**
**Answer:** An MCP server can return `TextResourceContents` (containing a UTF-8 string in the `text` field) or `BlobResourceContents` (containing base64-encoded binary data in the `blob` field).

**7. Why is providing a MIME type important when returning a resource?**
**Answer:** The MIME type (e.g., `application/json` or `image/png`) tells the client and the underlying LLM how to parse, interpret, and present the data being returned.

**8. What method does a client use to actually fetch the contents of a resource?**
**Answer:** The client uses the `resources/read` JSON-RPC method, passing the specific `uri` of the resource as a parameter.

**9. How does an MCP client get notified if a resource changes?**
**Answer:** If the server supports it, the client can use the `resources/subscribe` method on a specific URI. When the resource updates, the server sends a `notifications/resources/updated` notification to the client.

**10. In Python using the official MCP SDK, which decorator is used to handle resource read requests?**
**Answer:** The `@app.read_resource()` decorator is used to register a function that handles reading a resource.

**11. In a resource template like `github://repo/{owner}/{name}/issues`, what format is used for the template syntax?**
**Answer:** MCP resource templates use the URI Template syntax defined in IETF RFC 6570.

**12. If a server receives a `resources/read` request for a URI it does not recognize, what should it do?**
**Answer:** It should return an appropriate JSON-RPC error or raise an exception in the SDK (such as `ValueError` or `FileNotFoundError`) which the SDK will translate into an error response indicating the resource does not exist.

**13. Why might a server choose NOT to expose an entire SQL database as static resources?**
**Answer:** Exposing an entire database as static resources would require generating a URI for every single row/table upfront, which is computationally expensive, uses massive amounts of memory, and produces a list too large to transmit or process effectively.

**14. Does reading a resource require the LLM to provide complex JSON arguments like a tool?**
**Answer:** No. Reading a resource only requires the URI. The LLM does not construct a JSON argument payload for a resource read; it merely asks the client to resolve the URI.

**15. What encoding is required for binary files returned by a resource read?**
**Answer:** Binary data must be encoded in base64 and returned within the `blob` field of the response.

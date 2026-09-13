# Module 6: Sampling and Roots QnA

**1. What is the fundamental concept of Sampling in MCP?**
**Answer:** Sampling allows the MCP Server to ask the Client to run an LLM prompt and generate a completion (sample) on behalf of the server. It reverses the standard Client->Server command flow.

**2. Why would a server use Sampling instead of calling the OpenAI API itself?**
**Answer:** Sampling allows the server to leverage the Client's existing LLM configuration, billing setup, API keys, and context window. It removes the need for the server developer to manage AI infrastructure and credentials.

**3. What JSON-RPC method does the server use to request a sample?**
**Answer:** The server sends a `sampling/createMessage` request to the client.

**4. Can a server specify that the client MUST use "gpt-4" for a sampling request?**
**Answer:** No. Servers cannot mandate specific model names. They can only express `modelPreferences` using priority floats (0 to 1) for cost, speed, and intelligence.

**5. What is the purpose of the `maxTokens` parameter in a sampling request?**
**Answer:** It allows the server to restrict the maximum length of the generated response, preventing the client from spending excessive tokens on a simple task.

**6. From a security perspective, why are clients cautious about sampling requests?**
**Answer:** A malicious server could use sampling to trick the LLM into revealing sensitive information from the user's context window or perform actions the user did not intend. Clients often enforce human approval for sampling.

**7. What are Roots in the Model Context Protocol?**
**Answer:** Roots are URIs (typically file paths) provided by the Client that define the security and operational boundaries within which the Server is permitted to act.

**8. How does a server discover the approved Roots?**
**Answer:** The server sends a `roots/list` request to the client.

**9. If a server receives a tool call to write to `/usr/bin/python`, but the only root provided is `file:///home/user/project`, what should happen?**
**Answer:** The server must validate the path against the provided roots and reject the tool call with an error (e.g., "Permission Denied: Path outside approved roots").

**10. How does a server know if the Client supports Sampling?**
**Answer:** During the `initialize` handshake, the Client passes a `capabilities` object. The server must check if `capabilities.sampling` exists.

**11. How does a client inform a server that the user has changed their workspace directory?**
**Answer:** The client sends a `notifications/roots/list_changed` notification, prompting the server to fetch the updated roots list.

**12. Does a root URI have to be a local `file://` path?**
**Answer:** Not necessarily, though it is the most common use case. Roots can use any URI scheme that establishes a boundary relevant to the server's domain.

**13. In the Python SDK, how do you typically send a sampling request from within a tool handler?**
**Answer:** By accessing the active request context's session object (`app.request_context.session.create_message(...)`), provided the SDK version supports session context passing.

**14. What happens if a server relies heavily on sampling but the client's capability block does not include it?**
**Answer:** The server should degrade gracefully, either by disabling the specific tools that require sampling or by returning clear error messages instructing the user that the client does not support required features.

**15. Can a sampling request include system prompts?**
**Answer:** Yes, the `sampling/createMessage` request allows the server to include a `systemPrompt` field alongside the array of `messages` to guide the LLM's behavior during generation.

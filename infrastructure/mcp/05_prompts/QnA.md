# Module 5: Prompts QnA

**1. What is an MCP Prompt?**
**Answer:** An MCP Prompt is a pre-defined, parameterizable template provided by the server to help clients and users quickly generate well-structured requests for the LLM.

**2. How does an MCP Prompt differ from an LLM System Prompt?**
**Answer:** A System Prompt dictates the global behavior and persona of the LLM for the entire session. An MCP Prompt is a specific, user-facing template that injects one or more messages (usually user messages) into the conversation context at a specific moment.

**3. What method does a client call to discover available prompts on a server?**
**Answer:** The client calls the `prompts/list` method, which returns an array of prompt definitions.

**4. What fields define a prompt argument?**
**Answer:** A prompt argument is defined by a `name`, a `description`, and a boolean `required` flag.

**5. How does a client execute or fetch a prompt?**
**Answer:** The client sends a `prompts/get` request containing the `name` of the prompt and an `arguments` object containing key-value pairs for the prompt's parameters.

**6. What is the structure of the data returned by `prompts/get`?**
**Answer:** It returns an array of `messages`. Each message has a `role` (user or assistant) and `content` (an array of text blocks or embedded resources).

**7. Can a single prompt return multiple messages?**
**Answer:** Yes, a single `prompts/get` response can return an array of multiple messages, potentially mixing `user` and `assistant` roles to pre-fill conversation history.

**8. What is an Embedded Resource in the context of a prompt?**
**Answer:** An Embedded Resource allows a server to attach raw data (like file contents or database records) directly into the prompt's message content alongside text instructions, ensuring the LLM has the exact context it needs.

**9. In the Python SDK, which decorator registers a function to handle prompt lists?**
**Answer:** The `@app.list_prompts()` decorator.

**10. In the Python SDK, which decorator registers a function to generate prompt content?**
**Answer:** The `@app.get_prompt()` decorator.

**11. Why is it advantageous to compute a prompt on the server rather than just sending a static string to the client?**
**Answer:** Server-side computation allows the prompt to be highly dynamic. The server can fetch live data from a database, read current file states, or make API calls to construct rich, up-to-the-second context based on simple user arguments.

**12. If a client provides an argument that is not marked as `required`, how should the server handle it?**
**Answer:** The server should provide a sensible default behavior or omit that specific contextual detail from the resulting message.

**13. Are prompts meant to be executed autonomously by the LLM (like tools)?**
**Answer:** No. Prompts are typically user-driven (e.g., selected from a UI menu or slash command). Tools are what the LLM chooses to execute autonomously.

**14. What are the valid roles for a `PromptMessage`?**
**Answer:** The valid roles are `"user"` and `"assistant"`.

**15. If a required argument is missing from a `prompts/get` request, what should the server do?**
**Answer:** The server should reject the request and return an error (or raise a `ValueError` in the Python SDK) indicating that a required argument is missing.

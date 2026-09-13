# QnA: Real World Projects (Capstone)

1. **Question:** In the Database Explorer project, how is SQL injection prevented?
**Answer:** The primary defense is enforcing read-only access at the database user level. Additionally, the tool validates the query structure using regex (`^(?i)\s*SELECT\b`) to ensure it only begins with SELECT.

2. **Question:** Why use `asyncpg` instead of synchronous drivers in a FastMCP application?
**Answer:** FastMCP runs on FastAPI, which is asynchronous. Using `asyncpg` prevents database calls from blocking the event loop, allowing the server to handle multiple concurrent requests efficiently.

3. **Question:** In the GitHub Bot project, why restrict the tool to return only a specific number of issues (e.g., `limit=5`)?
**Answer:** To prevent overflowing the LLM's context window. LLMs have a maximum token limit, and returning hundreds of issues could cause errors or dilute the model's focus.

4. **Question:** How does the Filesystem Knowledge Base prevent path traversal attacks?
**Answer:** It uses `os.path.abspath` to resolve the requested path and then checks if the resulting absolute path `startswith()` the designated base directory. If it doesn't, the request is rejected.

5. **Question:** What is the advantage of using stdio over SSE for a local-only tool like the GitHub bot?
**Answer:** Stdio is lightweight, requires no network port binding, and is ideal for single-user desktop applications or CLI tools where the client and server run on the same machine.

6. **Question:** How does the Slack Notification Server handle API errors?
**Answer:** It catches the `SlackApiError` exception and returns a formatted string containing the error message back to the LLM. This allows the LLM to understand the failure and potentially retry or inform the user.

7. **Question:** If the database schema changes, how does the Database Explorer inform the LLM?
**Answer:** The LLM can use the `get_schema` tool to dynamically retrieve the latest column names and data types, ensuring its generated queries are accurate without needing server restarts.

8. **Question:** Why is it necessary to decode the file content in the GitHub project (`decoded_content.decode('utf-8')`)?
**Answer:** The GitHub API returns file contents encoded in base64. The application must decode this back into a standard UTF-8 string before returning it to the LLM.

9. **Question:** What scope should the Slack Bot Token have to only send messages?
**Answer:** The token should only have the `chat:write` scope. Granting broader scopes like `channels:read` is a violation of the principle of least privilege if not needed.

10. **Question:** How can you improve the search efficiency in the Filesystem Knowledge Base for large datasets?
**Answer:** Instead of a linear regex search across all files, you could integrate a vector database (like Chroma or FAISS) to perform semantic search based on embeddings.

11. **Question:** What is a common way to test MCP servers without connecting an LLM?
**Answer:** You can use tools like the MCP CLI Inspector or write unit tests that directly invoke the tool functions and validate the JSON/string outputs.

12. **Question:** Why return strings instead of complex objects from MCP tools?
**Answer:** The protocol expects text-based or standard JSON representations. LLMs consume text, so converting database records or API responses to formatted strings or JSON strings ensures compatibility.

13. **Question:** How can the Slack Notification Server format messages using blocks?
**Answer:** The tool could be updated to accept an arguments schema that includes a `blocks` array, passing that directly to the `chat_postMessage` API for rich formatting.

14. **Question:** What environmental variables are critical for the Database Explorer?
**Answer:** The `DB_DSN` (Data Source Name) or database connection string, which contains the host, port, user, and password.

15. **Question:** In a production environment, where should the Filesystem Knowledge Base store its index if using a vector DB?
**Answer:** The index should be stored on persistent storage (like an attached volume in Docker or Kubernetes) to avoid rebuilding it every time the container restarts.

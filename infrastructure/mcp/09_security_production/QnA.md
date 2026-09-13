# QnA: Security and Production Deployment

1. **Question:** What is the primary security risk associated with connecting an LLM to an MCP server that executes shell commands?
**Answer:** The primary risk is prompt injection, where an attacker crafts input that tricks the LLM into generating malicious shell commands. If the MCP server executes these without validation, it leads to Remote Code Execution (RCE).

2. **Question:** How should you authenticate clients connecting to a public-facing MCP server?
**Answer:** You should use robust authentication mechanisms such as API keys passed securely via headers, OAuth 2.0 for scoped delegation, or Mutual TLS (mTLS) to cryptographically verify the client's identity.

3. **Question:** What is the principle of least privilege in the context of MCP tools?
**Answer:** The principle of least privilege dictates that an MCP server should only have the exact permissions necessary to perform its intended functions. For example, a database tool should use read-only credentials if it only needs to query data.

4. **Question:** How can you mitigate the risk of data exfiltration via an MCP server?
**Answer:** Mitigations include strict access controls, output filtering (redacting sensitive data before sending it back to the LLM), and limiting the scope of what the server can query.

5. **Question:** Why is input validation critical for MCP tools?
**Answer:** Input validation ensures that the arguments passed by the LLM match expected formats and constraints, preventing attacks like SQL injection, path traversal, or unexpected application behavior.

6. **Question:** What is a Human-in-the-Loop (HITL) pattern?
**Answer:** HITL is a security pattern where critical or destructive actions proposed by the LLM require explicit approval from a human user before the MCP server executes them.

7. **Question:** How does Mutual TLS (mTLS) enhance MCP server security?
**Answer:** mTLS requires both the client and the server to authenticate each other using certificates, preventing unauthorized clients from connecting even if they have network access.

8. **Question:** Why should you avoid logging the full payload of tool arguments in audit logs?
**Answer:** Full payloads might contain sensitive information, PII, or credentials passed by the user. Audit logs should capture metadata (like tool name, execution time, and argument keys) without storing sensitive values.

9. **Question:** What is the purpose of rate limiting on an MCP server?
**Answer:** Rate limiting prevents Denial of Service (DoS) attacks, manages resource utilization, and controls costs by restricting the number of requests a client can make within a specific timeframe.

10. **Question:** How should secrets be managed in a containerized MCP server?
**Answer:** Secrets should never be hardcoded in the source code or Dockerfile. They should be injected at runtime using environment variables from a secure vault or secrets manager.

11. **Question:** Why is running the MCP server container as a non-root user important?
**Answer:** Running as a non-root user limits the potential damage if the container is compromised. The attacker will have restricted permissions, making it harder to escape the container or modify the host system.

12. **Question:** What information should a `/health` endpoint provide?
**Answer:** A `/health` endpoint should indicate whether the application is running and verify the status of critical dependencies, such as database connections or external API availability.

13. **Question:** How can you protect against path traversal attacks in a filesystem MCP tool?
**Answer:** Validate all requested paths to ensure they resolve to a location within a designated, restricted directory (e.g., using `os.path.abspath` and checking the prefix).

14. **Question:** In an SSE-based MCP architecture, how does the client authenticate?
**Answer:** The client typically authenticates during the initial HTTP request to establish the SSE connection, often passing an API key or Bearer token in the HTTP headers.

15. **Question:** What metrics are crucial for monitoring an MCP server in production?
**Answer:** Crucial metrics include request rate, error rate, latency/execution time per tool, resource utilization (CPU/Memory), and the number of active client connections.

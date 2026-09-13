# MCP Security and Production Cheatsheet

## Security Checklist
- [ ] **Authentication:** Require API keys, OAuth, or mTLS for all incoming connections.
- [ ] **Least Privilege:** Run the process/container as a non-root user.
- [ ] **Data Access:** Scope database and API credentials to the minimum required actions.
- [ ] **Input Validation:** Use strict schemas (e.g., Pydantic) for all tool arguments.
- [ ] **Path Traversal:** Validate and sandbox file system access.
- [ ] **Rate Limiting:** Implement limits per client/IP to prevent DoS.
- [ ] **Audit Logging:** Log tool invocations (timestamp, tool, client), avoiding sensitive payload data.
- [ ] **Secrets Management:** Use environment variables or a vault; do not hardcode secrets.
- [ ] **HITL:** Require human approval for destructive operations.

## Authentication Patterns Comparison

| Pattern | Complexity | Best For | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **API Key** | Low | Internal tools, simple setups | Easy to implement | Keys can leak, hard to rotate gracefully |
| **OAuth 2.0** | High | Multi-tenant SaaS, granular scopes | Fine-grained access, revocable | High implementation overhead |
| **mTLS** | Medium | Zero-trust networks, server-to-server | Very secure, cryptographic proof | Requires PKI infrastructure |

## Docker Deployment Template

```dockerfile
# Use a slim base image
FROM python:3.11-slim

# Create a dedicated user for security
RUN useradd -m -s /bin/bash mcpuser

WORKDIR /app

# Install dependencies securely
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/

# Switch to the non-root user
USER mcpuser

# Expose the application port
EXPOSE 8000

# Run the application (example using Uvicorn for FastMCP)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Common Run Command
```bash
docker run -d \
  --name mcp-server \
  -p 8000:8000 \
  -e MCP_API_KEY="your-secure-key" \
  -e DATABASE_URL="postgresql://user:pass@host/db" \
  my-mcp-server:latest
```

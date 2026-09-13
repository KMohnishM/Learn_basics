# Module 9: Security and Production Deployment for MCP Servers

## Introduction
Deploying Model Context Protocol (MCP) servers to production requires a rigorous approach to security, access control, and observability. Because MCP servers bridge Large Language Models (LLMs) with internal infrastructure, databases, and APIs, they introduce unique attack vectors such as prompt injection and privilege escalation. This module covers the MCP threat model, authentication patterns, input validation, rate limiting, and production deployment strategies.

## MCP Threat Model
Before deploying an MCP server, it is crucial to understand the threat landscape:
1.  **Prompt Injection / Indirect Prompt Injection:** A malicious user or an untrusted external document could contain instructions that trick the LLM into invoking MCP tools with unintended parameters.
2.  **Data Exfiltration:** If an MCP server has broad read access, an attacker might extract sensitive data (e.g., source code, PII) and leak it via the LLM's output channel.
3.  **Privilege Escalation:** If the MCP server runs with elevated privileges, compromised or manipulated tool calls could modify infrastructure or access restricted data.
4.  **Denial of Service (DoS):** Unbounded resource consumption or excessive tool calls from the client can overwhelm the server.

### Mitigation Strategies
-   **Least Privilege:** Limit the server's permissions to the absolute minimum required.
-   **Human-in-the-Loop (HITL):** Require explicit user approval for destructive actions.
-   **Input Validation:** Validate all parameters against strict schemas before executing any logic.
-   **Rate Limiting:** Enforce quotas on the number of requests per client.

## Authentication Patterns

### 1. API Key Authentication
API keys are a simple and common method for authenticating clients.

```python
import os
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from mcp.server.fastapi import FastMCP

API_KEY = os.getenv("MCP_API_KEY")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate credentials")

app = FastAPI()
mcp_server = FastMCP("SecureServer")

@app.post("/mcp")
async def handle_mcp(request: Request, api_key: str = Depends(get_api_key)):
    # Handle MCP protocol over HTTP
    return await mcp_server.handle_request(request)
```

### 2. OAuth 2.0
For environments requiring granular scopes and delegated access, OAuth 2.0 is preferred. The MCP client must obtain a Bearer token from an Authorization Server.

### 3. Mutual TLS (mTLS)
mTLS ensures that both the client and the server authenticate each other using cryptographic certificates. This is highly recommended for zero-trust environments.

```nginx
# NGINX configuration for mTLS
server {
    listen 443 ssl;
    server_name mcp.internal.example.com;

    ssl_certificate /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    
    # Require client certificate
    ssl_client_certificate /etc/nginx/certs/ca.crt;
    ssl_verify_client on;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-SSL-Client-Verify $ssl_client_verify;
        proxy_set_header X-SSL-Client-Subject $ssl_client_s_dn;
    }
}
```

## Input Validation
Never trust input from the client (and by extension, the LLM). Use Pydantic or similar libraries to enforce strict schemas.

```python
from pydantic import BaseModel, Field, constr
from typing import Literal

class DatabaseQueryArgs(BaseModel):
    # Only allow SELECT queries, prevent DROP/DELETE
    query_type: Literal["SELECT"]
    table_name: constr(pattern=r'^[a-zA-Z0-9_]+$')
    limit: int = Field(default=10, ge=1, le=100)

@mcp.tool()
def safe_query(args: DatabaseQueryArgs) -> str:
    # Execution logic here
    pass
```

## Rate Limiting
Prevent DoS attacks and control costs by implementing rate limiting.

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/mcp")
@limiter.limit("5/minute")
async def mcp_endpoint(request: Request):
    return await mcp_server.handle_request(request)
```

## Secrets Management
Never hardcode secrets. Use environment variables or a secrets manager like AWS Secrets Manager or HashiCorp Vault.

```python
import boto3
import json

def get_secret(secret_name: str) -> dict:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])
```

## Audit Logging
Log every significant action for forensic analysis. Do not log sensitive data (e.g., API keys, passwords).

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger("mcp_audit")
logger.setLevel(logging.INFO)

def log_tool_invocation(client_id: str, tool_name: str, args: dict):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "client_id": client_id,
        "tool": tool_name,
        "args_schema": list(args.keys()) # Log keys, not necessarily values
    }
    logger.info(json.dumps(log_entry))
```

## Production Deployment (Docker)
Containerize your MCP server for consistent deployments.

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -s /bin/bash mcpuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/

# Switch to non-root user
USER mcpuser

# Expose port for SSE/HTTP
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Health Checks and Monitoring
Provide endpoints for orchestration tools (like Kubernetes) to monitor the server's health.

```python
@app.get("/health")
async def health_check():
    # Verify DB connections, external API reachability, etc.
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
```

Monitor metrics such as tool execution time, error rates, and request volume using Prometheus or Datadog.

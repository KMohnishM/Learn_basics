# Capstone Projects Cheatsheet

## Project Architectures

### 1. Database Explorer
`LLM Client` <--(SSE/HTTP)--> `FastMCP Server` <--(asyncpg)--> `PostgreSQL DB`
**Key Patterns:** Regex validation, dynamic schema discovery.

### 2. GitHub Bot
`LLM Client` <--(stdio)--> `StdioServer` <--(PyGithub/HTTPS)--> `GitHub API`
**Key Patterns:** Pagination limiting, base64 decoding.

### 3. Filesystem Knowledge Base
`LLM Client` <--(SSE/HTTP)--> `FastMCP Server` <--(Local I/O)--> `Markdown Files`
**Key Patterns:** Path sanitization (`os.path.abspath`), text globbing.

### 4. Slack Notifier
`LLM Client` <--(SSE/HTTP)--> `FastMCP Server` <--(slack_sdk/HTTPS)--> `Slack API`
**Key Patterns:** Error handling feedback loops, single-purpose scoping.

## Integration Patterns

| Integration Type | Communication | Authentication Strategy | Primary Risk |
| :--- | :--- | :--- | :--- |
| **Database (SQL)** | TCP/Sockets | Read-only DB User | SQL Injection, Data Leakage |
| **SaaS APIs (REST)** | HTTPS | Bearer Token / PAT | API Rate Limits, Token Leakage |
| **Local Filesystem** | Local OS Calls | OS File Permissions | Path Traversal |
| **Message Queues/Chat**| HTTPS/WebSockets| Bot Token | Spam, Phishing via LLM |

## SDK Quick Reference (Python)

### Defining a FastMCP Tool
```python
from mcp.server.fastapi import FastMCP
from pydantic import BaseModel

mcp = FastMCP("ServerName")

class ArgsSchema(BaseModel):
    param1: str

@mcp.tool()
def my_tool(args: ArgsSchema) -> str:
    return f"Processed {args.param1}"
```

### Path Sanitization Snippet
```python
import os

def sanitize(requested_path: str, base_dir: str) -> str:
    target = os.path.abspath(os.path.join(base_dir, requested_path))
    if not target.startswith(base_dir):
        raise ValueError("Security error: Path Traversal")
    return target
```

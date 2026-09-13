# Module 10: Real World Projects

## Introduction
This module provides complete walkthroughs of four production-grade Model Context Protocol (MCP) servers. These projects demonstrate how to integrate various systems—databases, version control, file systems, and communication platforms—with LLMs securely and efficiently.

---

## Project 1: Database Explorer MCP Server
This server allows an LLM to safely query a PostgreSQL database, analyze schemas, and generate reports.

### Architecture
- **Framework:** FastMCP
- **Database:** PostgreSQL
- **ORM/Driver:** SQLAlchemy / asyncpg
- **Security:** Read-only database user, query structure validation.

### Implementation
```python
from mcp.server.fastapi import FastMCP
from pydantic import BaseModel, constr
import asyncpg
import os

mcp = FastMCP("DatabaseExplorer")
DB_DSN = os.getenv("DB_DSN")

class QueryArgs(BaseModel):
    query: constr(pattern=r'^(?i)\s*SELECT\b') # Ensure read-only

@mcp.tool()
async def execute_select(args: QueryArgs) -> str:
    """Execute a SELECT query against the database."""
    conn = await asyncpg.connect(DB_DSN)
    try:
        records = await conn.fetch(args.query)
        return str([dict(r) for r in records])
    except Exception as e:
        return f"Error executing query: {str(e)}"
    finally:
        await conn.close()

@mcp.tool()
async def get_schema(table_name: str) -> str:
    """Retrieve the schema for a specific table."""
    conn = await asyncpg.connect(DB_DSN)
    query = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = $1
    """
    try:
        records = await conn.fetch(query, table_name)
        return str([dict(r) for r in records])
    finally:
        await conn.close()
```

---

## Project 2: GitHub Repository Bot
A server that interacts with GitHub to read issues, review pull requests, and search code.

### Architecture
- **Framework:** stdio-based MCP
- **API:** PyGithub
- **Security:** Scoped Personal Access Token (PAT).

### Implementation
```python
import sys
from mcp.server.stdio import StdioServer
from github import Github
import os

github_client = Github(os.getenv("GITHUB_TOKEN"))
server = StdioServer("GitHubBot")

@server.tool()
def list_open_issues(repo_name: str, limit: int = 5) -> str:
    """List recent open issues in a repository."""
    repo = github_client.get_repo(repo_name)
    issues = repo.get_issues(state='open')[:limit]
    result = []
    for issue in issues:
        result.append(f"#{issue.number} - {issue.title}")
    return "\n".join(result)

@server.tool()
def read_file_content(repo_name: str, file_path: str, branch: str = "main") -> str:
    """Read the contents of a file in the repository."""
    repo = github_client.get_repo(repo_name)
    file_content = repo.get_contents(file_path, ref=branch)
    return file_content.decoded_content.decode('utf-8')

if __name__ == "__main__":
    server.run()
```

---

## Project 3: Filesystem Knowledge Base
A local file system reader that indexes Markdown files and provides semantic search capabilities to the LLM.

### Architecture
- **Framework:** FastMCP
- **Components:** Local file I/O, regex matching.
- **Security:** Sandbox directory restriction.

### Implementation
```python
import os
import glob
from mcp.server.fastapi import FastMCP

mcp = FastMCP("FilesystemKB")
BASE_DIR = os.path.abspath("./knowledge_base")

def safe_path(target_path: str) -> str:
    full_path = os.path.abspath(os.path.join(BASE_DIR, target_path))
    if not full_path.startswith(BASE_DIR):
        raise ValueError("Path traversal detected")
    return full_path

@mcp.tool()
def search_kb(keyword: str) -> str:
    """Search knowledge base files for a keyword."""
    results = []
    for filepath in glob.glob(f"{BASE_DIR}/**/*.md", recursive=True):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if keyword.lower() in content.lower():
                rel_path = os.path.relpath(filepath, BASE_DIR)
                results.append(f"Match found in: {rel_path}")
    return "\n".join(results) if results else "No matches found."

@mcp.tool()
def read_kb_file(file_path: str) -> str:
    """Read a specific file from the knowledge base."""
    safe_target = safe_path(file_path)
    if os.path.exists(safe_target):
        with open(safe_target, 'r', encoding='utf-8') as f:
            return f.read()
    return "File not found."
```

---

## Project 4: Slack Notification Server
An integration allowing the LLM to post summaries and notifications to Slack channels.

### Architecture
- **Framework:** FastMCP
- **API:** Slack SDK (`slack_sdk`)
- **Security:** Bot token with `chat:write` scope only.

### Implementation
```python
import os
from mcp.server.fastapi import FastMCP
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

mcp = FastMCP("SlackNotifier")
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

@mcp.tool()
def post_message(channel: str, text: str) -> str:
    """Post a message to a specific Slack channel."""
    try:
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text
        )
        return f"Message sent successfully to {channel}. Message TS: {response['ts']}"
    except SlackApiError as e:
        return f"Failed to send message: {e.response['error']}"
```

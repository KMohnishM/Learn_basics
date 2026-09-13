# Module 4: Resources in MCP

## Introduction

In the Model Context Protocol (MCP), a **Resource** provides a standardized way for servers to expose read-only data and content to clients. Unlike tools, which represent executable actions and can have side effects, resources represent state or information. They are the primary mechanism through which an LLM can be given access to documents, database records, file systems, API responses, or any other structured or unstructured data.

Resources in MCP are identified by URIs and can return text or binary data. They support both static definitions and dynamic templates, allowing a server to expose an unbounded set of resources based on parameters. Additionally, MCP supports resource subscriptions, enabling clients to be notified when a resource's content changes.

This module provides a deep technical dive into MCP resources, including URI design, resource types, reading mechanisms, and full Python implementations for real-world scenarios.

## Resource vs Tool

The distinction between resources and tools is foundational to designing an effective MCP server:

*   **Resource**:
    *   **Purpose**: Exposing read-only data (e.g., file contents, database rows, configuration).
    *   **Side Effects**: None. Reading a resource is idempotent.
    *   **Data Types**: Returns raw text or binary data (base64 encoded).
    *   **Client Behavior**: Clients can read resources on demand, or servers can attach them as context.
    *   **Example**: `file:///app/config.json`, `db://users/123`.

*   **Tool**:
    *   **Purpose**: Executing actions, performing computations, or mutating state.
    *   **Side Effects**: Often has side effects (e.g., writing a file, creating a database record, triggering an API call).
    *   **Data Types**: Accepts JSON arguments, returns JSON results or textual output.
    *   **Client Behavior**: Clients (LLMs) explicitly decide to call tools based on their descriptions.
    *   **Example**: `writeFile(path, content)`, `queryDatabase(sql)`.

**Rule of Thumb**: If the operation changes state or requires complex parametric input that dictates an action, use a Tool. If it merely fetches existing data predictably, use a Resource.

## Resource URI Design

Every resource in MCP is identified by a unique URI. Proper URI design is crucial for clarity and scalability. A resource URI typically follows standard IETF RFC 3986 syntax:

`scheme://authority/path?query#fragment`

### Examples of Good Resource URIs

1.  **File System**: `file:///Users/jane/docs/report.pdf`
2.  **Database Row**: `mysql://crm-db/customers/9876`
3.  **Application Config**: `config://production/features.json`
4.  **Log Stream**: `logs://service-a/latest`

Servers are free to invent their own URI schemes (like `mysql://` or `logs://`), provided the client can resolve them by calling `resources/read` on that server.

## Resource Types and MIME Types

When a client reads a resource, the server must respond with the resource's content and its MIME type (`mimeType`). The MIME type informs the client (and the underlying LLM) how to interpret the data.

### Supported Data Types
Resources can return:
1.  **Text**: `text` field in the response containing UTF-8 string data.
2.  **Blob**: `blob` field in the response containing base64 encoded binary data.

### Common MIME Types
*   `text/plain`: Standard text files.
*   `application/json`: JSON data.
*   `text/markdown`: Markdown documents.
*   `text/csv`: Comma-separated values.
*   `image/png`, `image/jpeg`: Images (sent as blob).
*   `application/pdf`: PDF documents (sent as blob).

## Static Resources vs Dynamic Resources

### Static Resources

Static resources are explicitly defined and their URIs are fixed. The server returns a complete list of these resources when the client calls `resources/list`.

```json
{
  "method": "resources/list",
  "result": {
    "resources": [
      {
        "uri": "config://app/settings.json",
        "name": "Application Settings",
        "mimeType": "application/json",
        "description": "Global application settings and feature flags."
      }
    ]
  }
}
```

### Dynamic Resources via Templates

For data sources with millions of potential records (e.g., a database or an entire file system), listing every possible URI is impossible. MCP provides **Resource Templates** for this.

A resource template defines a URI pattern using URI Template syntax (RFC 6570).

```json
{
  "method": "resources/templates/list",
  "result": {
    "resourceTemplates": [
      {
        "uriTemplate": "db://customers/{customerId}",
        "name": "Customer Profile",
        "mimeType": "application/json",
        "description": "Retrieve customer profile by ID."
      }
    ]
  }
}
```

The client knows it can construct a URI like `db://customers/123` and read it.

## Resource Reading

To fetch the content of a resource, the client sends a `resources/read` request with the URI.

**Request:**
```json
{
  "method": "resources/read",
  "params": {
    "uri": "config://app/settings.json"
  }
}
```

**Response:**
```json
{
  "result": {
    "contents": [
      {
        "uri": "config://app/settings.json",
        "mimeType": "application/json",
        "text": "{\n  \"theme\": \"dark\",\n  \"max_users\": 1000\n}"
      }
    ]
  }
}
```

Note that `contents` is an array. While typically containing one item, a single URI might theoretically resolve to multiple resource chunks or representations, though standard practice is one item per URI.

## Resource Subscriptions

MCP supports real-time updates via subscriptions. If a server advertises the `subscribe` capability, a client can subscribe to a resource.

1.  Client sends `resources/subscribe` with a URI.
2.  Server acknowledges.
3.  When the resource changes, the server sends a `notifications/resources/updated` notification.
4.  The client can then re-read the resource.

## Full Python Example: File-System Resource

This example demonstrates an MCP server exposing a specific directory as resources.

```python
import asyncio
import os
import mimetypes
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, ResourceTemplate, TextResourceContents, BlobResourceContents
import base64

app = Server("filesystem-resources")

BASE_DIR = "/var/log/myapp"

@app.list_resources()
async def list_resources() -> list[Resource]:
    resources = []
    # Only list top-level files as static resources
    if os.path.exists(BASE_DIR):
        for filename in os.listdir(BASE_DIR):
            filepath = os.path.join(BASE_DIR, filename)
            if os.path.isfile(filepath):
                mime_type, _ = mimetypes.guess_type(filepath)
                resources.append(
                    Resource(
                        uri=f"file://{filepath}",
                        name=filename,
                        mimeType=mime_type or "text/plain"
                    )
                )
    return resources

@app.read_resource()
async def read_resource(uri: str) -> list[TextResourceContents | BlobResourceContents]:
    if not uri.startswith("file://"):
        raise ValueError(f"Unsupported URI scheme: {uri}")
    
    filepath = uri.replace("file://", "")
    
    if not os.path.abspath(filepath).startswith(os.path.abspath(BASE_DIR)):
        raise PermissionError("Access denied")
        
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    mime_type, _ = mimetypes.guess_type(filepath)
    mime_type = mime_type or "text/plain"

    is_text = mime_type.startswith("text/") or mime_type == "application/json"

    if is_text:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return [TextResourceContents(uri=uri, mimeType=mime_type, text=content)]
    else:
        with open(filepath, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf-8")
        return [BlobResourceContents(uri=uri, mimeType=mime_type, blob=content)]

if __name__ == "__main__":
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    asyncio.run(main())
```

## Full Python Example: Database Resource with Templates

This example shows how to use Resource Templates to expose database rows without listing every single ID.

```python
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import ResourceTemplate, TextResourceContents

app = Server("db-resources")

# Mock database
DB = {
    "101": {"name": "Alice", "role": "Admin", "status": "active"},
    "102": {"name": "Bob", "role": "User", "status": "inactive"}
}

@app.list_resource_templates()
async def list_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            uriTemplate="db://users/{userId}",
            name="User Record",
            mimeType="application/json",
            description="Fetch a user record by their ID"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> list[TextResourceContents]:
    prefix = "db://users/"
    if not uri.startswith(prefix):
        raise ValueError("Unknown resource URI")
    
    user_id = uri[len(prefix):]
    
    if user_id not in DB:
        raise ValueError(f"User {user_id} not found")
        
    data = json.dumps(DB[user_id], indent=2)
    
    return [
        TextResourceContents(
            uri=uri,
            mimeType="application/json",
            text=data
        )
    ]

if __name__ == "__main__":
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    asyncio.run(main())
```

## Performance Considerations

When exposing resources, especially large files or databases:
1.  **Size Limits**: Be mindful of the size of the text or blob being returned. LLMs have context window limits. For large files, consider returning a summary or requiring a Tool to search/paginate the file.
2.  **Laziness**: Only load resource content into memory inside the `read_resource` handler, not during `list_resources`.
3.  **Caching**: If database queries are expensive, implement a caching layer in your MCP server before handling `read_resource`.
4.  **Binary Data**: Base64 encoding adds about 33% overhead to binary data size. Keep this in mind for transport over standard I/O.

# Module 7: Building MCP Servers

Building servers using the Model Context Protocol (MCP) requires understanding the SDKs, server lifecycle, and patterns for structuring functionality. This module explores the Python and TypeScript SDKs, covering high-level abstractions like FastMCP, testing, logging, and deployment strategies.

## Python MCP SDK

The Python SDK provides tools to implement MCP servers efficiently. It is built on asyncio, ensuring non-blocking operations suitable for complex workloads.

### FastMCP vs Low-Level API

The Python SDK exposes two primary ways to write a server:
1.  **Low-Level API**: Directly managing the server instance, defining tool metadata in JSON schema, and handling request callbacks.
2.  **FastMCP**: A high-level, decorator-based framework inspired by FastAPI, which abstracts away JSON schema generation and boilerplate. FastMCP automatically infers tool schemas from Python type hints and docstrings.

#### When to use FastMCP
FastMCP is recommended for 90% of use cases. It accelerates development by reducing boilerplate and enforcing type safety.
#### When to use the Low-Level API
The low-level API is suitable when you need precise control over the JSON-RPC lifecycle, dynamic tool registration at runtime without relying on type hints, or integration with legacy codebases where type inference is unreliable.

### Full FastMCP Example

Below is a robust example of a FastMCP server implementing multiple tools and resources.

```python
# server.py
import asyncio
import os
import json
import logging
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("weather-server")

# Initialize the FastMCP server
app = FastMCP("weather-server", description="A comprehensive weather and environmental data server")

# Database mock
WEATHER_DATA = {
    "san_francisco": {"temp": 65, "conditions": "Foggy", "wind": "12 mph"},
    "new_york": {"temp": 72, "conditions": "Sunny", "wind": "5 mph"},
    "london": {"temp": 55, "conditions": "Rainy", "wind": "15 mph"}
}

# --- Tool Definitions ---

@app.tool()
async def get_current_weather(location: str, unit: str = "F") -> str:
    """
    Retrieve the current weather for a specified location.
    
    Args:
        location: City name formatted as lowercase with underscores (e.g., 'san_francisco').
        unit: Temperature unit, 'F' or 'C'. Defaults to 'F'.
    """
    logger.info(f"Fetching weather for {location} in {unit}")
    
    if location not in WEATHER_DATA:
        return f"Error: Location '{location}' not found in database."
        
    data = WEATHER_DATA[location]
    temp = data["temp"]
    
    if unit.upper() == "C":
        temp = round((temp - 32) * 5.0/9.0, 1)
        
    return f"Weather in {location.replace('_', ' ').title()}: {temp}{unit.upper()}, {data['conditions']} with wind at {data['wind']}."

@app.tool()
async def add_weather_reading(location: str, temp: float, conditions: str, wind: str) -> str:
    """
    Add a new weather reading to the local database.
    
    Args:
        location: City name.
        temp: Temperature in Fahrenheit.
        conditions: Weather description (e.g., 'Sunny').
        wind: Wind speed and direction string.
    """
    key = location.lower().replace(" ", "_")
    WEATHER_DATA[key] = {
        "temp": temp,
        "conditions": conditions,
        "wind": wind
    }
    logger.info(f"Added reading for {location}")
    return f"Successfully recorded weather for {location}."

# --- Resource Definitions ---

@app.resource("weather://reports/{location}/summary.txt")
async def get_weather_summary(location: str) -> str:
    """
    Resource representing a detailed weather summary file for a location.
    """
    if location not in WEATHER_DATA:
        raise ValueError(f"Resource not found: {location}")
        
    data = WEATHER_DATA[location]
    report = [
        f"--- WEATHER SUMMARY: {location.upper()} ---",
        f"Temperature: {data['temp']}F",
        f"Conditions: {data['conditions']}",
        f"Wind: {data['wind']}",
        "------------------------------------",
        "Forecast indicates steady conditions."
    ]
    return "\n".join(report)

# --- Prompts ---

@app.prompt()
def weather_analysis_prompt(location: str) -> str:
    """
    Prompt template to guide an LLM in analyzing weather patterns.
    """
    return f"Analyze the current weather conditions for {location}. Consider the implications for outdoor activities and suggest clothing choices."

# --- Lifecycle Hooks ---

@app.on_startup
async def startup_handler():
    logger.info("Weather server is starting up...")
    # Initialize connections, load configurations
    os.environ["SERVER_READY"] = "true"

@app.on_shutdown
async def shutdown_handler():
    logger.info("Weather server is shutting down. Cleaning up resources...")
    # Close database connections, flush logs

if __name__ == "__main__":
    logger.info("Running FastMCP application.")
    app.run()
```

## TypeScript SDK

The TypeScript SDK provides a strictly typed, class-based architecture for building MCP servers. It uses Zod for robust input validation and schema generation.

### TypeScript Full Example

Below is a complete implementation of a task management server using the TypeScript SDK.

```typescript
// server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { 
  CallToolRequestSchema, 
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

// Initialize server
const server = new Server(
  {
    name: "task-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// Database mock
interface Task {
  id: string;
  title: string;
  completed: boolean;
}
const tasks: Record<string, Task> = {
  "t1": { id: "t1", title: "Review PR #42", completed: false },
  "t2": { id: "t2", title: "Update documentation", completed: true }
};

// Define tool schemas using Zod
const CreateTaskSchema = z.object({
  title: z.string().describe("The title of the task to create"),
});

const CompleteTaskSchema = z.object({
  id: z.string().describe("The ID of the task to mark as completed"),
});

// Register Tool List handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "create_task",
        description: "Create a new task in the system",
        inputSchema: {
          type: "object",
          properties: {
            title: { type: "string" }
          },
          required: ["title"]
        }
      },
      {
        name: "complete_task",
        description: "Mark an existing task as completed",
        inputSchema: {
          type: "object",
          properties: {
            id: { type: "string" }
          },
          required: ["id"]
        }
      }
    ]
  };
});

// Register Tool Call handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === "create_task") {
      const parsed = CreateTaskSchema.parse(args);
      const id = `t${Object.keys(tasks).length + 1}`;
      tasks[id] = { id, title: parsed.title, completed: false };
      return {
        content: [{ type: "text", text: `Task created with ID: ${id}` }]
      };
    }
    
    if (name === "complete_task") {
      const parsed = CompleteTaskSchema.parse(args);
      if (!tasks[parsed.id]) {
        throw new Error(`Task ${parsed.id} not found`);
      }
      tasks[parsed.id].completed = true;
      return {
        content: [{ type: "text", text: `Task ${parsed.id} marked complete.` }]
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error) {
    if (error instanceof Error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
        isError: true
      };
    }
    throw error;
  }
});

// Start the server
async function run() {
  console.error("Starting Task Server...");
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Server running on stdio.");
}

run().catch(console.error);
```

## Server Lifecycle Hooks

Understanding the lifecycle of an MCP server is critical for managing state, database connections, and graceful shutdowns.
1.  **Initialization**: The client sends an `initialize` request. The server responds with its capabilities and version.
2.  **Running**: The server actively processes JSON-RPC messages (e.g., `CallTool`, `ReadResource`).
3.  **Shutdown**: Not strictly defined by a specific MCP message in all transports, but typically managed via transport closure (e.g., EOF on stdin/stdout).

In FastMCP, you use `@app.on_startup` and `@app.on_shutdown` to manage async resources safely.

## Structured Logging

Since MCP servers often communicate over `stdio`, you cannot simply `print()` or `console.log()` to standard output, as this corrupts the JSON-RPC payload.
-   **Python**: Use `logging` directed to `sys.stderr` or a file.
-   **TypeScript**: Use `console.error()` for logs, keeping `console.log()` exclusively for the JSON-RPC transport if managing it manually.
-   **MCP Logging Capability**: Clients can request servers to send logs via JSON-RPC notifications (`notifications/message/info`). FastMCP routes Python logs to this channel automatically if configured.

## Testing MCP Servers

Testing is essential for robust MCP servers.
-   **Unit Testing (Python)**: Directly import and call your FastMCP tool functions using pytest, bypassing the MCP layer.
-   **Integration Testing**: Use a dummy client (like `mcp-client` or the MCP Inspector) to spawn the server process, send JSON-RPC requests, and validate the JSON-RPC responses.
-   **TypeScript**: Use `vitest` or `jest` to instantiate the `Server` class, attach an in-memory transport, and test handlers directly.

## Common Patterns

-   **State Management**: Servers are generally stateless regarding the LLM conversation but stateful regarding the local environment (e.g., holding a database connection pool).
-   **Error Handling**: Always catch exceptions and return them as graceful JSON-RPC error objects or tool results with `isError: true` to allow the LLM to recover, rather than crashing the process.
-   **Resource Templates**: Use URI templates (`file:///{path}`) to expose dynamic sets of files without listing millions of items upfront.

## Publishing a Server

1.  **Packaging**: Package Python servers via `pyproject.toml` (Pipx-installable) and TypeScript servers via `package.json` (`npx`-executable).
2.  **Documentation**: Provide a clear `README.md` detailing the arguments needed to run the server, environmental variables required (API keys), and a list of exposed tools.
3.  **Registry**: Submit open-source servers to community directories like the official MCP repository or `smithery.ai`.

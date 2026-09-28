# Agentic AI: Tool Use and Function Calling

## 1. Function Calling and Tool Schemas Internals

In modern LLMs, tool use is achieved by providing the model with a JSON schema describing available functions. The model then outputs a structured JSON response indicating which function to call and with what arguments.

### System Messages vs Tokens

When a schema is provided, it is typically converted into a system message or special tokens that the model understands. 
This allows the model to differentiate between normal text generation and a tool invocation request.

### JSON Schema and Pydantic

Pydantic is often used in Python to define tool schemas, which are then exported to JSON schema format.

```python
from pydantic import BaseModel, Field

class WeatherQuery(BaseModel):
    \"\"\"
    Query the weather for a specific location.
    \"\"\"
    location: str = Field(..., description="The city and state, e.g., San Francisco, CA")
    unit: str = Field("celsius", description="The unit of temperature, e.g., celsius or fahrenheit")

# Example of generating JSON schema
print(WeatherQuery.schema_json(indent=2))
```




































































































































































































## 2. Tool Execution Engine and Dispatcher

A tool execution engine is responsible for taking the model's tool call request, executing the corresponding function, and returning the result to the model.

### ToolRegistry Class

```python
import inspect
from typing import Callable, Dict, Any

class ToolRegistry:
    \"\"\"
    A registry for tools that can be invoked by the agent.
    \"\"\"
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        \"\"\"
        Register a tool function.
        \"\"\"
        self._tools[name] = func

    def get_tool(self, name: str) -> Callable:
        \"\"\"
        Retrieve a tool by name.
        \"\"\"
        return self._tools.get(name)

    def execute(self, name: str, kwargs: Dict[str, Any]) -> Any:
        \"\"\"
        Execute a tool with the provided arguments.
        \"\"\"
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool {name} not found.")
        return tool(**kwargs)
```









































































































































































































## 3. Parallel Tool Calling

Modern agents can execute multiple tool calls in parallel to save time.

### asyncio.gather Execution

```python
import asyncio
import json

async def execute_parallel(registry: ToolRegistry, tool_calls: list):
    \"\"\"
    Execute multiple tool calls in parallel.
    \"\"\"
    tasks = []
    for call in tool_calls:
        tool_name = call.get("name")
        arguments = json.loads(call.get("arguments", "{}"))
        tool_func = registry.get_tool(tool_name)
        
        if asyncio.iscoroutinefunction(tool_func):
            tasks.append(tool_func(**arguments))
        else:
            tasks.append(asyncio.to_thread(tool_func, **arguments))
            
    return await asyncio.gather(*tasks, return_exceptions=True)
```




























































































## 4. Tool Error Recovery and Self-Correction

When a tool call fails, the agent must be able to recover and retry.

### Schema Errors and Exceptions

```python
def robust_execute(registry, tool_calls, max_retries=3):
    \"\"\"
    Execute tools with automatic retry loops for self-correction.
    \"\"\"
    results = []
    for call in tool_calls:
        retries = 0
        success = False
        while retries < max_retries and not success:
            try:
                res = registry.execute(call["name"], call["arguments"])
                results.append(res)
                success = True
            except Exception as e:
                retries += 1
                if retries == max_retries:
                    results.append(f"Error: {str(e)}")
    return results
```


























































































## 5. Model Context Protocol (MCP)

MCP defines how clients and servers interact to provide tools to the model.

### Python Implementation

```python
# Pseudo-code for MCP Server
class MCPServer:
    def __init__(self):
        self.tools = []

    def add_tool(self, tool):
        self.tools.append(tool)

    def handle_request(self, request):
        # Handle stdio or SSE requests
        pass
```














































































## 6. Dynamic Tool Discovery and Tool Filtering

For agents with hundreds of tools, dynamic discovery is necessary to fit within the context window.

### Semantic Retrieval

```python
class ToolRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve_relevant_tools(self, query: str, top_k: int = 5):
        \"\"\"
        Retrieve the most relevant tools for a given query.
        \"\"\"
        embeddings = self.embed(query)
        return self.vector_store.search(embeddings, top_k=top_k)
        
    def embed(self, text: str):
        # Generate embeddings
        pass
```




































# Tool Use Cheatsheet

## Concepts

| Concept | Description | Key Technologies |
|---|---|---|
| Function Calling | The ability of an LLM to generate structured requests to execute external code. | JSON Schema, special tokens |
| Dispatcher | The engine that receives tool calls, executes them, and returns results. | Python, asyncio |
| Tool Schema | The definition of a tool's inputs, usually defined as a JSON Schema. | Pydantic |
| MCP | Model Context Protocol, a standard for client-server tool interactions. | stdio, SSE |
| Semantic Retrieval | Finding relevant tools dynamically based on context to save tokens. | Vector DBs, Embeddings |


## Architecture Diagram

```ascii
+-------------------+        +-------------------+        +-------------------+
|                   |        |                   |        |                   |
|   User Prompt     +------->+   Agent Logic     +------->+   LLM (Model)     |
|                   |        |   (LangChain/etc) |        |                   |
+-------------------+        +--------+----------+        +---------+---------+
                                      ^                             |
                                      |                             |
                             Observation (Result)            Tool Call (JSON)
                                      |                             |
                                      |                             v
+-------------------+        +--------+----------+        +---------+---------+
|                   |        |                   |        |                   |
| External APIs     +<-------+   Tool Dispatcher |<-------+   Tool Registry   |
| Databases         |        |   (Execution)     |        |   (Schemas)       |
| Sandboxes         +------->+                   |        |                   |
+-------------------+        +-------------------+        +-------------------+
```

## Tool Execution Flow

```ascii
1. Request: LLM outputs {"name": "get_weather", "arguments": {"city": "Paris"}}
      |
      v
2. Dispatch: Dispatcher intercepts JSON, looks up 'get_weather'
      |
      v
3. Execute: Dispatcher runs get_weather(city="Paris")
      |
      v
4. Result: Function returns {"temp": 22, "condition": "Sunny"}
      |
      v
5. Observation: Dispatcher formats result as message and sends back to LLM
```

## Retry Logic

```ascii
[Tool Call] ---> (Execute) ---> [Success] ---> (Return to LLM)
                     |
                 [Exception]
                     |
                     v
             (Format Error Msg)
                     |
                     v
             (Send Error to LLM)
                     |
                     v
             [LLM Self-Corrects] ---> (New Tool Call) ---> ...
```

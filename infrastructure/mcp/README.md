# Model Context Protocol (MCP) — Curriculum

> **Goal:** Go from zero to building, hosting, and integrating production-grade MCP servers.
> Covers spec internals, transport layers, tool/resource/prompt primitives, security, testing, and real-world integrations with Claude, Cursor, and custom clients.

---

## Who is this for?

- Engineers building AI-powered tools who want structured context injection
- Developers integrating LLMs into existing systems (databases, APIs, filesystems)
- Anyone building agents or AI workflows with Claude, GPT-4, Gemini, or open-source models
- Backend engineers adding MCP servers to production services

---

## Module Map

| # | Module | Key Topics | Difficulty |
|---|--------|-----------|-----------|
| **M1** | `01_foundations/` | What MCP is, why it exists, JSON-RPC 2.0, architecture overview, vs alternatives | Beginner |
| **M2** | `02_transport_layer/` | stdio transport, HTTP+SSE transport, WebSocket, lifecycle, initialization handshake | Beginner |
| **M3** | `03_tools/` | Tool definition schema, inputSchema (JSON Schema), annotations, handler patterns, error handling | Intermediate |
| **M4** | `04_resources/` | Resource URIs, MIME types, static vs dynamic resources, resource templates, subscriptions | Intermediate |
| **M5** | `05_prompts/` | Prompt primitives, arguments, embedded resources, multi-turn prompt templates | Intermediate |
| **M6** | `06_sampling_roots/` | Sampling API, completion requests, roots, client capabilities negotiation | Advanced |
| **M7** | `07_building_servers/` | Python SDK (`mcp`), TypeScript SDK, FastMCP, server lifecycle, full working servers | Intermediate |
| **M8** | `08_integrations/` | Claude Desktop config, Cursor IDE, custom clients, debugging with MCP Inspector | Intermediate |
| **M9** | `09_security_production/` | Auth (OAuth 2.0 / API keys), input validation, rate limiting, logging, deployment | Advanced |
| **M10** | `10_real_world_projects/` | 4 full end-to-end projects: DB Explorer, GitHub Bot, Filesystem Assistant, Slack Notifier | Advanced |

---

## Suggested Study Path

```
Week 1: M1 → M2 → M3  (foundations + first tool server)
Week 2: M4 → M5 → M6  (resources, prompts, sampling)
Week 3: M7 → M8       (build real servers, integrate with Claude/Cursor)
Week 4: M9 → M10      (harden + ship real projects)
```

---

## Prerequisites

- Python 3.10+ or TypeScript/Node 18+
- Basic understanding of JSON and HTTP
- Familiarity with async programming (`asyncio` / `async-await`)
- Optional but helpful: LangChain / LangGraph basics

---

## Language Approach

- **Python** — primary language for all examples (using official `mcp` SDK + `FastMCP`)
- **TypeScript** — secondary examples in M7 and M8 (using `@modelcontextprotocol/sdk`)

---

## What is MCP?

Model Context Protocol (MCP) is an **open standard** developed by Anthropic that defines how AI models (like Claude) connect to external data sources, tools, and services. Think of it as a USB-C standard — but for connecting AI models to the world.

**Before MCP:** Every LLM integration required custom code, bespoke APIs, and ad-hoc prompt engineering to give models access to external data.

**After MCP:** Any MCP-compatible client (Claude Desktop, Cursor, custom agent) can connect to any MCP server through a standard protocol — regardless of what tools or data the server exposes.

```
┌─────────────────┐     MCP Protocol     ┌──────────────────────┐
│   MCP Client    │◄────────────────────►│    MCP Server        │
│  (Claude, etc.) │   JSON-RPC 2.0       │  (your code)         │
│                 │   over stdio/HTTP    │  - Tools             │
│  Sends:         │                      │  - Resources         │
│  - tool calls   │                      │  - Prompts           │
│  - resource req │                      │  - Sampling          │
└─────────────────┘                      └──────────────────────┘
```

# Agentic AI Curriculum

## Introduction to Agentic AI

Agentic AI represents a fundamental paradigm shift in how we build applications with Large Language Models (LLMs). Instead of treating LLMs as mere text processors or rigid components within a strict Directed Acyclic Graph (DAG) of prompts, Agentic AI empowers models with autonomy. Agents possess the ability to perceive their environment, reason about the current state, determine the most appropriate sequence of actions, and execute tool calls to interact with the external world. Crucially, they can observe the results of these actions, adapt their plans, and reflect on their mistakes. This moves AI from deterministic, hardcoded pipelines to dynamic, goal-seeking systems capable of handling long-horizon tasks and complex edge cases.

In traditional LLM chains, control flow is dictated by the programmer. If step A fails, the chain breaks. In agentic systems, control flow is delegated to the LLM itself. The model evaluates its progress, determines if an error occurred, and proactively attempts alternative solutions.

## Core Agentic Architecture

A robust AI Agent typically consists of the following core components interacting in a continuous loop:

1. Perception: The interface through which the agent receives input. This can be text prompts, structured JSON, images (in multimodal models), or continuous data streams.
2. Reasoning (Brain): The LLM acting as the cognitive engine. It analyzes the perception data, generates thoughts, formulates strategies, and decides which tools to invoke.
3. Tool Calling: The mechanism mapping the agent's intent to actionable functions. This translates textual intent into structured JSON payloads (e.g., API requests).
4. Environment Interaction: The actual execution of tools. This often occurs within sandboxed runtimes (for code execution) or against external systems (databases, SaaS APIs).
5. Memory: 
    - Short-term Memory: The contextual state of the current execution loop, including conversation history and temporary scratchpads.
    - Long-term Memory: Persistent storage, often utilizing vector databases, to recall past interactions, learned rules, and user preferences.
6. Reflection: The self-correction loop where the agent analyzes failures, evaluates its outputs against a rubric, and adjusts its behavior for future iterations.

## Module Map

| Module | Topic | Learning Objectives |
|---|---|---|
| 01 | Agent Fundamentals | Understand the autonomy spectrum, implement a from-scratch ReAct loop, build Plan-and-Execute architectures, and integrate Finite State Machines. |
| 02 | Tool Use & Function Calling | Master JSON schemas, parallel tool execution, error recovery loops, and the Model Context Protocol (MCP). |
| 03 | Memory Systems | (Coming Soon) Implement short-term conversational memory, long-term vector retrieval, and entity relationship graphs. |
| 04 | Multi-Agent Systems | (Coming Soon) Design collaborative agent swarms, hierarchical delegation, and consensus mechanisms. |
| 05 | Evaluation & Observability | (Coming Soon) Track agent trajectories, trace tool execution latency, and build deterministic evaluation rubrics. |
| 06 | Production Deployment | (Coming Soon) Secure agents, manage rate limits, handle context window exhaustion, and deploy via Kubernetes/Serverless. |

## Prerequisites

To succeed in this curriculum, you should have a solid foundation in the following areas:

- Advanced Python Programming: Deep understanding of Pydantic, decorators, metaclasses, and modern typing constructs.
- Asynchronous Programming: Mastery of `asyncio`, coroutines, event loops, and concurrent task execution in Python.
- LLM Fundamentals: Familiarity with prompt engineering, context windows, tokenization mechanisms, and foundational model limitations.
- API Integration: Extensive experience building and consuming RESTful APIs, managing HTTP requests, handling JSON serialization, and implementing rate limiting.

## Recommended Study Order

1. Begin with Module 01 to grasp the philosophical and architectural differences between simple chains and autonomous agents.
2. Review the raw Python implementations of the ReAct and Plan-and-Execute loops to understand the underlying mechanics without relying on opaque frameworks.
3. Proceed to Module 02 to learn how to connect these autonomous brains to the external world safely and effectively.
4. Complete the QnA sections at the end of each module to rigorously test your conceptual understanding.
5. Use the CHEATSHEETs for quick reference during your own system designs and implementations.

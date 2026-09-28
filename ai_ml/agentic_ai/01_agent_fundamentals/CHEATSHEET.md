# Agent Fundamentals Cheatsheet

## Architectures Comparison

| Architecture | Core Mechanism | Best For | Pros | Cons |
|---|---|---|---|---|
| **Zero-Shot** | Direct generation | Simple queries | Fast, cheap | High hallucination |
| **ReAct** | Interleaved Think/Act | Search, API usage | Grounded, observable | Token heavy, slow |
| **Plan & Execute** | upfront planning, step execution | Long-horizon tasks | Structured, trackable | Rigid initial plan |
| **Reflexion** | Trial, evaluate, self-correct | Coding, logic puzzles | Iterative improvement | Very high token cost |
| **FSM-Agent** | Strict state transitions + LLM logic | Production systems | Safe, predictable | Complex to design |


## ReAct Loop Visualized

```text
+-------------------+
|   User Prompt     |
+---------+---------+
          |
          v
+---------+---------+
|      Thought      |  <-- "I need to search for X"
+---------+---------+
          |
          v
+---------+---------+
|      Action       |  <-- Tool: WebSearch
+---------+---------+
          |
          v
+---------+---------+
|   Action Input    |  <-- Query: "X"
+---------+---------+
          |
          v
+---------+---------+
|    Observation    |  <-- Result from Tool
+---------+---------+
          | (Loop until Final Answer)
          v
+---------+---------+
|   Final Answer    |
+-------------------+
```

## Tool Definition Schema

| Field | Type | Description | Importance |
|---|---|---|---|
| **Name** | String | Unique identifier for the tool | High - used for routing |
| **Description** | String | Detailed explanation of when to use it | Critical - guides LLM choice |
| **Arguments** | JSON Schema | Types and descriptions of inputs | High - ensures correct params |
| **Function** | Callable | The actual code to execute | Critical - the actual capability |

## FSM State Transition Example

```text
      [START]
         |
         v
+------------------+
|                  |
|  Understand Req  |
|                  |
+------------------+
    |         |
Valid Req  Invalid Req
    |         |
    v         v
+--------+ +--------+
|        | |        |
|  Plan  | | Clarify|
|        | |        |
+--------+ +--------+
    |         |
    +----<----+
```

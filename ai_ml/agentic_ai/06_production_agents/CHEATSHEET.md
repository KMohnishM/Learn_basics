# Module 6: CHEATSHEET - Production Agents

## 1. Production Agent Readiness Checklist

| Category | Requirement | Description | Status |
| :--- | :--- | :--- | :--- |
| **Observability** | Traces configured | Every session outputs OpenTelemetry traces to a backend. | [ ] |
| **Observability** | Token Tracking | In/Out tokens are logged per span for cost attribution. | [ ] |
| **Security** | Sandboxing | Generated code executes in isolated microVMs/containers. | [ ] |
| **Security** | HITL Guardrails | Destructive tool calls require asynchronous human approval. | [ ] |
| **Security** | Input Filtering | NeMo Guardrails block direct/indirect prompt injections. | [ ] |
| **Reliability** | Cycle Detection | Hashed state tracking halts execution on infinite loops. | [ ] |
| **Reliability** | Fallback Models | API timeouts route to secondary provider (e.g., Anthropic -> OpenAI). | [ ] |
| **Cost** | Prompt Caching | Prefix caching enabled for iterative ReAct loops. | [ ] |
| **Cost** | Tiered Routing | Simple tasks delegated to 8B/70B models instead of frontier. | [ ] |

---

## 2. Agent Evals Metrics & Formula Table

| Metric | Formula / Measurement | Purpose |
| :--- | :--- | :--- |
| **Pass@k** | Probability of success given `k` independent attempts. | Measures robustness and consistency on non-deterministic tasks. |
| **Trajectory Score** | `(Optimal Steps) / (Total Agent Steps Taken)` | Measures efficiency. Lower score = wandering, hallucinated tool calls. |
| **Tool Error Rate** | `(Failed Tool Calls) / (Total Tool Calls) * 100` | Identifies bad prompt engineering or overly complex tool schemas. |
| **Cost Per Run** | `(In_Tokens * In_Price) + (Out_Tokens * Out_Price)` | Financial metric to determine if the agent is economically viable. |
| **Intervention Rate**| `(Runs requiring Human UI) / (Total Runs)` | Tracks autonomy level of the system over time. |

---

## 3. OpenTelemetry Agent Tracing Schema Reference

When instrumenting agents with OpenTelemetry (OpenInference standard), ensure the following span attributes are attached:

```text
span.name: "llm_generation"
attributes:
  - llm.model_name: "claude-3-5-sonnet"
  - llm.provider: "anthropic"
  - llm.prompt_template: "You are an assistant. Task: {user_input}"
  - llm.input_messages: [{"role": "user", "content": "..."}]
  - llm.output_messages: [{"role": "assistant", "tool_calls": [...]}]
  - llm.token_count.prompt: 1540
  - llm.token_count.completion: 215

span.name: "tool_execution"
attributes:
  - tool.name: "query_postgres_db"
  - tool.description: "Executes read-only SQL"
  - tool.arguments: '{"query": "SELECT * FROM users;"}'
  - tool.result: '[{"id": 1, "name": "Alice"}]'
  - tool.error: null
```

---

## 4. Guardrails & Sandboxing Best Practices Table

| Threat Vector | Mitigation Strategy | Tooling / Infrastructure |
| :--- | :--- | :--- |
| **Prompt Injection** | Pre-flight semantic filtering of user input | Guardrails AI, NeMo Guardrails |
| **Unauthorized Tools** | Role-based Access Control (RBAC) at tool layer | IAM policies, API gateways |
| **Malicious Code Gen** | Disposable isolated execution environments | Docker, gVisor, AWS Firecracker |
| **Infinite Loops** | Max step bounds, Cycle detection hashing | Python state trackers, Redis |
| **PII Data Leakage** | Post-flight NER scanning on LLM output text | Microsoft Presidio, Custom LLM Judge |

# Multi-Agent Systems (MAS) Cheatsheet

## 1. Communication Topologies

### Hierarchical (Supervisor / Orchestrator)
Central supervisor delegates to specialized subagents.
```text
       [ Supervisor ]
         /       \
[Agent A]         [Agent B]
```

### Sequential (Pipeline)
Linear flow. Output of one is input to next.
```text
[Agent A] ---> [Agent B] ---> [Agent C]
```

### Collaborative (Peer-to-Peer)
Unstructured, dynamic communication between all nodes.
```text
[Agent A] <---> [Agent B]
    ^               ^
    |               |
    v               v
[Agent C] <---> [Agent D]
```

### Blackboard
Agents communicate only through a shared memory state.
```text
      [ Shared Blackboard ]
      ^        ^        ^
      |        |        |
[Agent A]  [Agent B]  [Agent C]
```

### Debate / Consensus
Generators propose, Arbiter/Critic evaluates.
```text
[Generator 1] --\
                 -> [Arbiter] -> Final Output
[Generator 2] --/
```

---

## 2. Framework Comparison Matrix

| Feature | LangGraph | AutoGen | CrewAI |
| :--- | :--- | :--- | :--- |
| **Mental Model** | State Machine / Directed Graph | Chat Room / Conversational | Org Chart / Roles & Tasks |
| **State Mgt.** | Explicit (TypedDict / Pydantic) | Implicit (Message History) | Implicit (Task Context) |
| **Control Flow** | Edges & Router Functions | GroupChatManager / Rules | Sequential / Hierarchical |
| **Best For** | Production pipelines, HITL | Prototyping, Brainstorming | Business process automation |
| **Learning Curve** | Steep | Moderate | Low |
| **Flexibility** | Extremely High | High | Moderate |

---

## 3. Implementation Patterns

### Agent-as-a-Tool (Python Pseudocode)
The Orchestrator treats subagents as functions that return strings. Context is strictly isolated.
```python
def orchestrator_loop(user_input):
    # Orchestrator decides what to do
    action = llm.plan(user_input)
    
    if action == "needs_research":
        # Call subagent like a tool
        result = research_agent.execute(action.query)
        # Orchestrator resumes with result
        return llm.synthesize(result)
```

### Explicit Handoff (Swarm Style)
Agents return a special object to transfer the active control flow.
```python
class Handoff:
    def __init__(self, target_agent):
        self.target_agent = target_agent

def triage_agent(message):
    if "billing" in message:
        return Handoff(billing_agent)
    return "How can I help?"

# Execution loop
current_agent = triage_agent
while True:
    response = current_agent(user_input)
    if isinstance(response, Handoff):
        current_agent = response.target_agent # Control transfers
    else:
        break
```

---

## 4. LangGraph StateGraph Template

```python
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# 1. Define the State Schema
class GraphState(TypedDict):
    input_text: str
    intermediate_data: List[str]
    final_result: str

# 2. Define Node Functions (Agents)
def node_researcher(state: GraphState):
    # Execute LLM logic
    data = f"Researched: {state['input_text']}"
    return {"intermediate_data": [data]} # Mutate state

def node_writer(state: GraphState):
    # Execute LLM logic
    text = f"Draft based on {state['intermediate_data']}"
    return {"final_result": text} # Mutate state

# 3. Define Routing Logic (Conditional Edges)
def router(state: GraphState):
    if len(state.get("intermediate_data", [])) > 0:
        return "writer"
    return "researcher"

# 4. Build and Compile the Graph
workflow = StateGraph(GraphState)

workflow.add_node("researcher", node_researcher)
workflow.add_node("writer", node_writer)

workflow.set_entry_point("researcher")
workflow.add_conditional_edges("researcher", router)
workflow.add_edge("writer", END)

app = workflow.compile()

# 5. Execute
initial_state = {"input_text": "Quantum Computing", "intermediate_data": []}
result = app.invoke(initial_state)
```

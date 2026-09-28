# Module 4: Multi-Agent Systems (MAS)

## 1. Why Multi-Agent Systems (MAS)?

The shift from monolithic large language model interactions to Multi-Agent Systems (MAS) represents a fundamental evolution in how we architect AI solutions. Rather than relying on a single, massive prompt to solve a complex problem end-to-end, MAS decomposes the problem space into discrete, manageable domains handled by specialized agents. This architectural paradigm offers several critical advantages that parallel traditional software engineering principles.

### Cognitive Load and Prompt Complexity
Single massive agents suffer from prompt bloat. When an agent is tasked with planning, coding, reviewing, and testing simultaneously, the prompt context becomes saturated with conflicting instructions and overlapping concerns. This leads to the "lost in the middle" phenomenon, where the model forgets or ignores critical constraints. By splitting tasks into multiple agents, each agent receives a highly focused prompt tailored specifically to its current responsibility. The cognitive load on any single LLM call is dramatically reduced, resulting in higher fidelity outputs and tighter adherence to instructions.

### Conway's Law in AI Architecture
Conway's Law states that organizations design systems that mirror their own communication structures. In AI, building a system to replace or augment a human workflow is most effective when the AI system mirrors the specialized roles of that workflow. If a software development team consists of a Product Manager, a Lead Developer, a QA Engineer, and a Security Auditor, the MAS should instantiate agents reflecting these exact roles. This alignment ensures that the system's internal boundaries, handoffs, and feedback loops match the well-understood logic of the domain it is automating.

### Modularity, Testability, and Reusability
MAS forces developers to define explicit interfaces between agents. When an agent generates code and passes it to a reviewer agent, the handoff is an observable event. This modularity means that individual agents can be tested in isolation. You can evaluate the reviewer agent's performance independently of the generator agent. Furthermore, a well-designed specialized agent (e.g., a SQL generation agent) can be reused across entirely different applications, reducing duplication of effort and standardizing capabilities across an enterprise.

### Fault Isolation and Resilience
In a single-agent system, an error in early reasoning often cascades, contaminating all subsequent output and leading to total failure. In a MAS, failures can be isolated. If a data-fetching agent fails to retrieve information, a supervisor agent can detect the failure, implement a retry mechanism, or fallback to an alternative data source, without disrupting the overall execution flow. This fault isolation significantly increases the robustness of AI applications deployed in production environments.

### Parallel Execution
Many tasks contain independent sub-tasks. A monolithic agent processes everything sequentially due to the autoregressive nature of LLMs. In a Multi-Agent System, an orchestrator can dispatch independent sub-tasks to multiple agents simultaneously. For example, while one agent researches a topic, another can draft an outline, and a third can gather visual assets. This parallel execution dramatically reduces latency and improves the user experience.

## 2. Communication Topologies & Coordination

The effectiveness of a Multi-Agent System is heavily dependent on how the agents are organized and how they communicate. Choosing the right topology is crucial for system performance, reliability, and cost.

### Hierarchical (Supervisor / Manager)
In a hierarchical topology, a single central agent acts as the supervisor. This agent does not execute the granular tasks; instead, it analyzes the objective, breaks it down, delegates sub-tasks to specialized worker agents, and synthesizes their results.

```text
       +------------------+
       |                  |
       |  Supervisor Agent|
       |                  |
       +--------+---------+
                |
    +-----------+-----------+
    |           |           |
+---v---+   +---v---+   +---v---+
|       |   |       |   |       |
|Agent A|   |Agent B|   |Agent C|
|       |   |       |   |       |
+-------+   +-------+   +-------+
```

*Pros:* Centralized control, easy to track progress, predictable execution flow.
*Cons:* The supervisor can become a bottleneck or single point of failure. High token cost due to the supervisor processing all intermediate outputs.

### Sequential (Pipeline)
A sequential topology links agents in a linear chain. The output of one agent becomes the direct input to the next. This pattern is ideal for well-defined workflows with clear progression, such as content creation pipelines.

```text
+-------+      +-------+      +-------+      +-------+
|       |      |       |      |       |      |       |
|Agent A+----->+Agent B+----->+Agent C+----->+Agent D|
|       |      |       |      |       |      |       |
+-------+      +-------+      +-------+      +-------+
```

*Pros:* Simple to implement, easy to debug, minimal overhead in coordination.
*Cons:* Rigid; cannot easily handle conditional branching or dynamic task reallocation. Errors compound down the chain.

### Collaborative (Peer-to-Peer / Network)
In a collaborative topology, agents communicate with each other directly without a central supervisor. They may use direct messaging or a shared context to coordinate their actions.

```text
    +-------+           +-------+
    |       |           |       |
    |Agent A+<--------->+Agent B|
    |       |           |       |
    +---+---+           +---+---+
        ^                   ^
        |                   |
        |       +-------+   |
        |       |       |   |
        +------>+Agent C+---+
                |       |
                +-------+
```

*Pros:* Highly flexible, scalable, allows for emergent problem-solving behaviors.
*Cons:* Prone to infinite loops, difficult to trace execution, requires complex consensus mechanisms.

### Blackboard Pattern
The Blackboard pattern uses a shared memory space (the blackboard) where agents read data and post their results. An external controller (or the agents themselves) determines who acts next based on the state of the blackboard.

```text
                +-------------------+
                |                   |
                |   Shared Memory   |
                |   (Blackboard)    |
                |                   |
                +---+-------+---+---+
                    ^       ^   ^
                    |       |   |
       +------------+       |   +-------------+
       |                    |                 |
+------+--+            +----+----+       +----+----+
|         |            |         |       |         |
| Agent A |            | Agent B |       | Agent C |
|         |            |         |       |         |
+---------+            +---------+       +---------+
```

*Pros:* Decouples agents completely, supports asynchronous execution, handles diverse knowledge sources.
*Cons:* The blackboard can become a bottleneck, managing state consistency is complex.

### Debate / Consensus
In a debate topology, multiple agents are given the same prompt or variations of a prompt, and they generate different solutions. An arbiter agent (or a voting mechanism) is then used to evaluate the solutions and select the best one, or the agents critique each other until consensus is reached.

```text
+-------+                        +-------+
|       |                        |       |
|Agent A+-----+            +-----+Agent C|
|       |     |            |     |       |
+-------+     v            v     +-------+
          +---+------------+---+
          |                    |
          |   Arbiter Agent    |
          |                    |
          +---+------------+---+
              ^            ^
+-------+     |            |     +-------+
|       |     |            |     |       |
|Agent B+-----+            +-----+Agent D|
|       |                        |       |
+-------+                        +-------+
```

*Pros:* High quality output, robust against hallucinations, explores multiple solution paths.
*Cons:* Very high token usage, slow execution time.

## 3. The Orchestrator-Subagent Pattern

The Orchestrator-Subagent pattern is a specific implementation of the hierarchical topology and is one of the most practical and widely used MAS architectures in production today. It leverages the concept of "Agent-as-a-Tool".

### The Core Concept
In this pattern, the supervisor (orchestrator) is an agent equipped with tools. However, instead of these tools executing simple python functions or API calls, the tools are wrappers around *other agents* (subagents). When the orchestrator decides to call a tool, it is actually passing a prompt and context to a specialized subagent, waiting for its response, and then using that response to continue its orchestration loop.

### Why use Agent-as-a-Tool?
1. Interface Standardization: From the orchestrator's perspective, triggering a complex reasoning agent is identical to calling a calculator tool. The abstraction simplifies the orchestrator's logic.
2. Context Encapsulation: The orchestrator does not need to know *how* the subagent solves the problem, only *what* the subagent is capable of and *what* it returns. This prevents the orchestrator's context window from being flooded with the subagent's internal scratchpad or reasoning steps.
3. Strict Boundaries: It enforces clear boundaries. The subagent receives only the parameters passed in the tool call, not the entire conversational history of the orchestrator.

### Python Implementation Example

Below is a simplified implementation of the Orchestrator-Subagent pattern using standard Python and a generic LLM client interface.

```python
import json
from typing import Dict, Any, List

class Agent:
    def __init__(self, name: str, system_prompt: str, tools: List[Dict[str, Any]] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        
    def generate(self, user_prompt: str) -> str:
        # Mock LLM call
        print(f"[{self.name}] Thinking...")
        if self.name == "Researcher":
            return "Found information: The capital of France is Paris."
        elif self.name == "Writer":
            return "Here is a poem about Paris: City of light, shining bright..."
        return "Task complete."

class Orchestrator:
    def __init__(self):
        self.research_agent = Agent(
            name="Researcher",
            system_prompt="You are a research agent. Find factual information."
        )
        self.writer_agent = Agent(
            name="Writer",
            system_prompt="You are a creative writer. Write engaging content."
        )
        
        # Define the tools available to the orchestrator
        self.tools = [
            {
                "name": "call_researcher",
                "description": "Call this tool to research factual information.",
                "parameters": {"query": "string"}
            },
            {
                "name": "call_writer",
                "description": "Call this tool to generate creative text based on facts.",
                "parameters": {"facts": "string", "style": "string"}
            }
        ]
        
    def run(self, objective: str):
        print(f"[Orchestrator] Starting objective: {objective}")
        
        # Step 1: Orchestrator decides to research
        print("[Orchestrator] Decided to call researcher.")
        research_result = self.research_agent.generate("Find capital of France.")
        print(f"[Orchestrator] Received from Researcher: {research_result}")
        
        # Step 2: Orchestrator decides to write based on research
        print("[Orchestrator] Decided to call writer.")
        final_output = self.writer_agent.generate(f"Facts: {research_result}")
        print(f"[Orchestrator] Received from Writer: {final_output}")
        
        return final_output

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run("Write a poem about the capital of France.")
```

## 4. Agent Handoff Protocols

Agent handoffs occur when control of the execution flow transfers from one agent to another. Managing these handoffs elegantly is critical for building systems that don't get stuck in infinite loops or lose critical context.

### Explicit Handoffs (Swarm Style)
In recent lightweight frameworks like OpenAI's Swarm, handoffs are treated as first-class citizens and modeled as specific return types from tool calls. Instead of returning a string, an agent's tool can return a reference to another agent.

When an agent returns a handoff object, the framework's execution loop intercepts it, updates the active agent to the newly designated agent, and continues the conversation loop using the new agent's system prompt and tools.

### Preserving vs. Filtering Context
A major challenge during a handoff is deciding how much history to pass to the next agent.
- Full History: The new agent sees the entire conversation transcript. This provides maximum context but quickly eats up the token limit and increases cognitive load.
- Filtered History: A summarizing agent (or deterministic logic) compresses the history into a concise summary before the handoff.
- State Object: The system maintains an external state object (like a dictionary). Agents read from and write to this state object, and during a handoff, only the state object is passed, not the raw message history.

### Python Implementation of Explicit Handoff

```python
class Handoff:
    def __init__(self, target_agent: 'Agent'):
        self.target_agent = target_agent

class Agent:
    def __init__(self, name: str):
        self.name = name
        
    def execute(self, message: str) -> Any:
        print(f"[{self.name}] Received: {message}")
        if self.name == "TriageAgent":
            if "refund" in message.lower():
                print(f"[{self.name}] Routing to BillingAgent")
                return Handoff(Agent("BillingAgent"))
            else:
                print(f"[{self.name}] Routing to TechSupportAgent")
                return Handoff(Agent("TechSupportAgent"))
        elif self.name == "BillingAgent":
            return "I will process your refund."
        elif self.name == "TechSupportAgent":
            return "Have you tried turning it off and on again?"

def run_swarm(initial_agent: Agent, user_message: str):
    current_agent = initial_agent
    
    while True:
        response = current_agent.execute(user_message)
        
        if isinstance(response, Handoff):
            current_agent = response.target_agent
            print(f"[System] Handoff complete. Active agent is now {current_agent.name}")
            # In a real system, the user_message or a modified context would be passed.
        else:
            print(f"[System] Final Response: {response}")
            break

if __name__ == "__main__":
    triage = Agent("TriageAgent")
    run_swarm(triage, "I need a refund for my last purchase.")
```

## 5. Multi-Agent Debate & Self-Critique

The Multi-Agent Debate pattern is a powerful mechanism for improving the reliability and accuracy of LLM outputs. It leverages the concept that models are often better at evaluating answers than generating them from scratch (a concept similar to generative adversarial networks).

### Generator, Critic, and Arbiter
This pattern typically involves three distinct roles:
1. Generator: Proposes a solution to the problem.
2. Critic: Reviews the proposed solution against a set of constraints or test cases, identifying flaws, edge cases, or inefficiencies.
3. Arbiter (Optional): If multiple generators propose solutions, the arbiter evaluates them all and selects the best one.

### The Feedback Loop
The debate is not a single pass. It operates in a loop:
1. Generator creates code.
2. Critic reviews code and provides feedback.
3. If feedback is negative, Generator revises the code based on the feedback.
4. Loop continues until the Critic approves the code or a maximum iteration limit is reached.

### Majority Voting
An alternative to the Generator/Critic loop is Majority Voting (also known as self-consistency). The system spawns N identical agents, gives them all the same prompt, and asks them to independently arrive at an answer. An aggregator script then extracts the final answers and takes the majority vote. This is highly effective for tasks with deterministic answers (math, logic puzzles).

### Python Code Review Pipeline Example

```python
def generate_code(prompt: str) -> str:
    # Mock generation
    return "def add(a, b):\n    return a - b  # Bug introduced"

def critique_code(code: str) -> dict:
    # Mock critique
    if "-" in code:
        return {"approved": False, "feedback": "The function subtracts instead of adding."}
    return {"approved": True, "feedback": "Looks good."}

def fix_code(code: str, feedback: str) -> str:
    # Mock fix
    return "def add(a, b):\n    return a + b"

def debate_loop(task: str, max_iterations: int = 3):
    print(f"[Task] {task}")
    current_code = generate_code(task)
    
    for i in range(max_iterations):
        print(f"\n--- Iteration {i+1} ---")
        print(f"[Generator] Output:\n{current_code}")
        
        evaluation = critique_code(current_code)
        print(f"[Critic] Feedback: {evaluation['feedback']}")
        
        if evaluation["approved"]:
            print("[System] Code approved by critic.")
            return current_code
            
        print("[System] Requesting revision...")
        current_code = fix_code(current_code, evaluation["feedback"])
        
    print("[System] Max iterations reached. Returning best effort.")
    return current_code

if __name__ == "__main__":
    final_code = debate_loop("Write a python function to add two numbers.")
```

## 6. Framework Architectures

The ecosystem of Multi-Agent frameworks is evolving rapidly. While the underlying concepts are similar, the architectural abstractions differ significantly. Understanding these differences is key to choosing the right tool for the job.

### LangGraph (StateGraph)
LangGraph, built by the creators of LangChain, models multi-agent workflows as state machines using mathematical graphs (nodes and edges).
- Architecture: Agents are represented as nodes in a graph. Handoffs and conditional logic are represented as directed edges between nodes. A central state object (typically a typed dictionary) is passed along the edges.
- State Management: The state object is mutated by each node. This provides rigorous, trackable state management and makes it easy to implement persistence (checkpointing) and human-in-the-loop features.
- Best For: Complex, long-running workflows requiring strict control flow, human intervention, and robust state persistence.

### AutoGen (GroupChat)
Microsoft's AutoGen popularized the multi-agent conversational paradigm.
- Architecture: AutoGen is heavily centered around the concept of a `ConversableAgent`. Agents communicate by sending messages to one another. The most common pattern is the `GroupChat`, where multiple agents are placed in a shared room, and a `GroupChatManager` decides who speaks next based on the conversation history.
- State Management: State is largely implicitly managed through the conversation history. The transcript *is* the state.
- Best For: Exploratory tasks, collaborative brainstorming, and scenarios where emergent behavior from agent interactions is desired.

### CrewAI (Roles and Tasks)
CrewAI takes an organizational structure approach, heavily inspired by human team dynamics.
- Architecture: You define `Agents` with specific roles, goals, and backstories. You then define `Tasks` and assign them to specific agents. Agents are grouped into a `Crew`, which orchestrates the execution of the tasks.
- State Management: CrewAI manages task progression internally, passing the output of one task as context to the next, similar to a sophisticated sequential pipeline.
- Best For: Rapid prototyping of business processes, scenarios that closely mirror existing human organizational structures.

### Side-by-Side Comparison

| Feature | LangGraph | AutoGen | CrewAI |
| :--- | :--- | :--- | :--- |
| Core Abstraction | Graph (Nodes/Edges) | Conversable Agents | Roles / Tasks / Crews |
| State Management | Explicit (TypedDict) | Implicit (Message History) | Implicit (Task Outputs) |
| Execution Flow | Deterministic / Graph-based | Dynamic / Conversational | Sequential / Hierarchical |
| Human-in-the-loop | First-class support (Checkpoints)| Supported via prompts/tools | Supported |
| Learning Curve | Steep | Moderate | Low |
| Primary Use Case | Reliable production pipelines | Exploratory problem solving | Business workflow automation |

### Code Snippet Comparison

**LangGraph (Conceptual):**
```python
# Define state
class State(TypedDict):
    messages: list
    current_agent: str

# Define graph
workflow = StateGraph(State)
workflow.add_node("agent_a", agent_a_node)
workflow.add_node("agent_b", agent_b_node)
workflow.add_conditional_edges("agent_a", router_function)
workflow.set_entry_point("agent_a")
app = workflow.compile()
```

**AutoGen (Conceptual):**
```python
agent_a = AssistantAgent(name="Agent_A")
agent_b = AssistantAgent(name="Agent_B")
groupchat = GroupChat(agents=[agent_a, agent_b], messages=[], max_round=10)
manager = GroupChatManager(groupchat=groupchat)
agent_a.initiate_chat(manager, message="Start task")
```

**CrewAI (Conceptual):**
```python
researcher = Agent(role='Researcher', goal='Find data')
writer = Agent(role='Writer', goal='Write report')
task1 = Task(description='Research topic', agent=researcher)
task2 = Task(description='Write summary', agent=writer)
crew = Crew(agents=[researcher, writer], tasks=[task1, task2])
result = crew.kickoff()
```

## Conclusion

Multi-Agent Systems represent a significant leap forward in AI engineering. By adopting paradigms like the Orchestrator-Subagent pattern, Debate loops, and rigorous graph-based state management, developers can build systems that are far more robust, capable, and reliable than single-prompt architectures. The key to mastering MAS is understanding that the complexity moves from prompt engineering to system architecture and coordination design.

### Section: Complete LangGraph StateGraph Architecture
```python
from typing import TypedDict, Annotated, List, Union
import operator
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    task: str
    plan: List[str]
    draft: str
    critique: str
    iterations: int
    final_output: str

def planner_node(state: AgentState) -> dict:
    return {"plan": ["research", "draft", "critique"], "iterations": 0}

def writer_node(state: AgentState) -> dict:
    return {"draft": f"Draft content for: {state['task']}"}

def critic_node(state: AgentState) -> dict:
    passed = state["iterations"] >= 2
    critique = "Approved" if passed else "Needs deeper technical data"
    return {"critique": critique, "iterations": state["iterations"] + 1}

def should_continue(state: AgentState) -> str:
    if state["critique"] == "Approved":
        return "finalize"
    return "revise"

# Build StateGraph
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("writer", writer_node)
workflow.add_node("critic", critic_node)
workflow.add_node("finalize", lambda state: {"final_output": state["draft"]})

workflow.set_entry_point("planner")
workflow.add_edge("planner", "writer")
workflow.add_edge("writer", "critic")
workflow.add_conditional_edges("critic", should_continue, {"revise": "writer", "finalize": "finalize"})
workflow.add_edge("finalize", END)

app = workflow.compile()
```

### Section: AutoGen & CrewAI Production Architectures
- AutoGen `GroupChat` with custom speaker selection function.
- CrewAI Hierarchical process with manager LLM.
- Handling race conditions and deadlocks in multi-agent swarms.
































































































































































































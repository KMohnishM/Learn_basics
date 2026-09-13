# 🕸️ LangGraph Mastery: State Machines & Multi-Agent Orchestration

Welcome to the **LangGraph Curriculum**. LangGraph is a specialized framework designed to compile and run language model workflows as **State Machines (graphs)**. 

While standard chains are linear and strict, LangGraph introduces **cycles and loops**, enabling you to develop agentic systems with complex, self-correcting logic, persistent memory database sessions, and human-in-the-loop validation checkpoints.

---

## 💡 The Paradigm Shift: Why LangGraph?

In standard LangChain, pipelines are designed as Directed Acyclic Graphs (DAGs) using LangChain Expression Language (LCEL). Once execution flows forward, it cannot loop back without complex manual loops:

```
[Standard Chain] Input -> Prompt -> LLM -> Parser -> Done
```

In LangGraph, we define our workflows using **States, Nodes, and Edges**. This allows loops and cycles, making it possible to build feedback loops:

```
                +-------------------+
                |                   |
                v                   |
Input -> [Generator Node] -> [Critic Node] -> (Approved?) --Yes--> Output
                                 ^              |
                                 |              |
                                 +----No--------+
```

### Core Architecture Components
1. **`State`**: The database schema of the graph. It is a shared, key-value data structure (represented by a Python `TypedDict` or Pydantic class). Every node receives the current state, modifies it, and returns the updates.
2. **`Nodes`**: The computational steps of the graph. A node is a simple Python function (sync or async) that takes the current state as input, runs operations (like LLM prompts, API requests, calculations), and outputs a dictionary representing updates to the state.
3. **`Edges`**: The routing connections between nodes.
   - **Direct Edges**: Move directly from Node A to Node B.
   - **Conditional Edges**: Execute a routing function to decide which node to move to next based on variables in the current state (e.g. routing to an editor node if errors are found, or ending the graph if the result is correct).

---

## 🛠️ Local Environment Setup

To start running the code, navigate to the `langgraph/` directory and configure your python environment:

### Step 1: Navigate to Directory
```bash
cd langgraph
```

### Step 2: Create & Activate Virtual Environment
```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: API Keys
LangGraph loads credentials from the same `.env` file in the parent workspace directory. If you haven't set up API keys, follow the [LangChain root instructions](../langchain/README.md). To enable LangSmith trace visualizations:
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=langgraph_tutorial
```

---

## 📚 Syllabus and Progress Tracker

Here is the step-by-step roadmap for your LangGraph learning path:

| Module | Title | Format | Key Concepts |
| :--- | :--- | :--- | :--- |
| **[Module 1](./modules/01_graph_basics/README.md)** | [Graph Basics](./modules/01_graph_basics/) | Notebook | `StateGraph`, Nodes, Edges, compiling, and running basic linear graph executions. |
| **[Module 2](./modules/02_cyclic_graphs/README.md)** | [Cyclic Graphs & Loops](./modules/02_cyclic_graphs/) | Notebook | Conditional edges, routing functions, reflection loops, self-correction patterns. |
| **[Module 3](./modules/03_state_management/README.md)** | [State Management](./modules/03_state_management/) | Notebook | Reducers, list appending schemas (`add_messages`), partial state updates, schemas. |
| **[Module 4](./modules/04_persistence_memory/README.md)** | [Memory & Checkpointing](./modules/04_persistence_memory/) | Notebook | `SqliteSaver` checkpointers, conversation threads, state restoration, "Time Travel". |
| **[Module 5](./modules/05_human_in_the_loop/README.md)** | [Human-in-the-Loop](./modules/05_human_in_the_loop/) | Notebook | Graph breakpoints (`interrupt_before`), pausing state execution, manual state modification, resume hooks. |
| **[Module 6](./modules/06_multi_agent_systems/README.md)** | [Multi-Agent Systems](./modules/06_multi_agent_systems/) | Python script | Collaborative worker nodes, Hand-offs, Supervisor routers, team orchestration. |

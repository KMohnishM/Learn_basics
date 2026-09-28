# Module 5: Advanced Agentic Patterns

## Introduction

In this module, we will explore advanced design patterns for autonomous agents. While basic sequential execution (like chain-of-thought) is sufficient for straightforward tasks, complex real-world environments require dynamic, resilient, and adaptive architectures. The patterns discussed here address non-deterministic failures, multi-step planning over long horizons, human oversight, and parallel execution.

## 1. The OODA Loop in Autonomous Agents

The OODA loop (Observe, Orient, Decide, Act) is a strategic framework developed by military strategist John Boyd. When applied to AI agents, it provides a more robust alternative to the standard ReAct (Reason, Act) paradigm.

### Theoretical Framework

1. Observe: The agent gathers raw data from its environment. This includes pulling from sensors, reading API responses, capturing user inputs, or monitoring system states.
2. Orient: The agent contextualizes the observations. It queries its memory base, cross-references with its configured persona, updates its mental model of the environment, and filters out noise.
3. Decide: The agent generates candidate plans. It runs a risk-reward evaluation for each plan, considers potential failure modes, and selects the optimal path forward.
4. Act: The agent executes the chosen plan by dispatching a tool call, modifying a state variable, or responding to the user.

### OODA vs ReAct

ReAct primarily focuses on a tight loop of reasoning about an immediate observation and taking an action. OODA places a heavy emphasis on the "Orient" phase, forcing the agent to reconcile new data with prior knowledge and historical context before considering actions. 

### Architecture Diagram

```text
+-------------------+
|                   |
|   OBSERVE         |<--------------------------------+
|   - Fetch Data    |                                 |
|   - Read Logs     |                                 |
|                   |                                 |
+--------+----------+                                 |
         |                                            |
         v                                            |
+--------+----------+                                 |
|                   |                                 |
|   ORIENT          |                                 |
|   - Check Memory  |                                 |
|   - Update State  |                                 |
|   - Filter Noise  |                                 |
|                   |                                 |
+--------+----------+                                 |
         |                                            |
         v                                            |
+--------+----------+                                 |
|                   |                                 |
|   DECIDE          |                                 |
|   - Generate Plans|                                 |
|   - Evaluate Risk |                                 |
|   - Select Action |                                 |
|                   |                                 |
+--------+----------+                                 |
         |                                            |
         v                                            |
+--------+----------+                                 |
|                   |                                 |
|   ACT             |                                 |
|   - Call Tool     |---------------------------------+
|   - Mutate State  |
|                   |
+-------------------+
```

### Python Implementation of OODA Loop

```python
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Observation(BaseModel):
    raw_data: str
    source: str
    timestamp: float

class OrientationState(BaseModel):
    current_context: str
    historical_summary: str
    risk_level: str

class Decision(BaseModel):
    action_type: str
    parameters: Dict[str, Any]
    confidence_score: float

class OODAAgent:
    def __init__(self, name: str):
        self.name = name
        self.memory: List[Observation] = []
        self.state: Optional[OrientationState] = None

    async def observe(self, environment_data: str, source: str) -> Observation:
        """Gather data from the environment."""
        import time
        obs = Observation(
            raw_data=environment_data,
            source=source,
            timestamp=time.time()
        )
        self.memory.append(obs)
        return obs

    async def orient(self, latest_obs: Observation) -> OrientationState:
        """Contextualize the observation against memory."""
        # Simulated LLM orientation process
        historical_context = " ".join([m.raw_data for m in self.memory[-5:]])
        
        self.state = OrientationState(
            current_context=f"Processing: {latest_obs.raw_data}",
            historical_summary=f"Recent history: {historical_context}",
            risk_level="LOW" if "error" not in latest_obs.raw_data.lower() else "HIGH"
        )
        return self.state

    async def decide(self, orientation: OrientationState) -> Decision:
        """Generate and evaluate candidate actions."""
        # Simulated decision making
        if orientation.risk_level == "HIGH":
            return Decision(
                action_type="ESCALATE",
                parameters={"reason": "High risk detected in context"},
                confidence_score=0.95
            )
        else:
            return Decision(
                action_type="CONTINUE_PROCESSING",
                parameters={"data": orientation.current_context},
                confidence_score=0.85
            )

    async def act(self, decision: Decision) -> Any:
        """Execute the chosen decision."""
        print(f"[{self.name}] Executing action: {decision.action_type}")
        print(f"[{self.name}] Parameters: {decision.parameters}")
        
        if decision.action_type == "ESCALATE":
            return "Escalated to human operator."
        return "Processing complete."

    async def run_cycle(self, environment_input: str):
        print(f"--- Starting OODA Cycle ---")
        obs = await self.observe(environment_input, "system_sensor")
        print(f"OBSERVE: {obs}")
        
        orient_state = await self.orient(obs)
        print(f"ORIENT: {orient_state}")
        
        decision = await self.decide(orient_state)
        print(f"DECIDE: {decision}")
        
        result = await self.act(decision)
        print(f"ACT RESULT: {result}")
        print(f"---------------------------\n")

# Example Usage
async def main_ooda():
    agent = OODAAgent("SecurityBot")
    await agent.run_cycle("All systems nominal.")
    await agent.run_cycle("Warning: Unauthorized access attempt detected on port 22.")

if __name__ == "__main__":
    asyncio.run(main_ooda())
```

## 2. Advanced Planning: Tree of Thoughts (ToT) & LATS

Linear reasoning models often fail on complex algorithmic or strategic tasks because they cannot backtrack efficiently when they hit a dead end.

### Language Agent Tree Search (LATS)

LATS (Zhou et al., 2023) combines the exploratory power of Monte Carlo Tree Search (MCTS) with the generative and evaluative capabilities of Large Language Models. 

#### The Four Phases of MCTS in LATS

1. Selection: The agent traverses the existing reasoning tree from the root to a leaf node. It uses the UCT (Upper Confidence bounds applied to Trees) algorithm to balance exploitation (choosing paths with high known value) and exploration (choosing paths that haven't been tried often).
2. Expansion: Upon reaching a leaf node, the LLM is prompted to generate multiple diverse candidate next steps (actions or thoughts).
3. Evaluation / Simulation: Each new candidate state is evaluated. In LATS, the LLM itself acts as a value function, scoring the state on a scale (e.g., 0.0 to 1.0) based on how close it is to the final goal. Alternatively, automated tests can be run to provide deterministic feedback.
4. Backpropagation: The score from the evaluation is propagated back up the tree to the root. The visit counts of all parent nodes are incremented, and their average value scores are updated.

### Python Implementation of LATS

```python
import math
import random
from typing import List, Optional

class StateNode:
    def __init__(self, state_description: str, parent: Optional['StateNode'] = None):
        self.state_description = state_description
        self.parent = parent
        self.children: List['StateNode'] = []
        self.visits = 0
        self.value = 0.0
        self.is_terminal = False

    def uct_score(self, exploration_weight: float = 1.414) -> float:
        if self.visits == 0:
            return float('inf')
        
        exploitation = self.value / self.visits
        exploration = exploration_weight * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

class LATSAgent:
    def __init__(self, max_iterations: int = 50):
        self.max_iterations = max_iterations

    def select(self, node: StateNode) -> StateNode:
        """Phase 1: Selection using UCT."""
        current = node
        while current.children and not current.is_terminal:
            current = max(current.children, key=lambda c: c.uct_score())
        return current

    def expand(self, node: StateNode) -> List[StateNode]:
        """Phase 2: Expansion generating multiple candidates."""
        if node.is_terminal:
            return []
        
        # Simulated LLM generation of diverse next states
        candidates = [
            f"{node.state_description} -> Action A",
            f"{node.state_description} -> Action B",
            f"{node.state_description} -> Action C"
        ]
        
        new_nodes = []
        for cand in candidates:
            child = StateNode(state_description=cand, parent=node)
            node.children.append(child)
            new_nodes.append(child)
            
        return new_nodes

    def evaluate(self, node: StateNode) -> float:
        """Phase 3: Evaluation using LLM as value function."""
        # Simulated LLM scoring
        score = random.uniform(0.1, 0.9)
        # Randomly decide if terminal to simulate reaching a goal
        if random.random() > 0.8:
            node.is_terminal = True
            score = 1.0 if random.random() > 0.5 else 0.0
        return score

    def backpropagate(self, node: StateNode, score: float):
        """Phase 4: Backpropagation of scores."""
        current = node
        while current is not None:
            current.visits += 1
            current.value += score
            current = current.parent

    def search(self, initial_state: str) -> StateNode:
        root = StateNode(state_description=initial_state)
        
        for i in range(self.max_iterations):
            leaf = self.select(root)
            if not leaf.is_terminal:
                new_nodes = self.expand(leaf)
                if new_nodes:
                    node_to_eval = random.choice(new_nodes)
                else:
                    node_to_eval = leaf
            else:
                node_to_eval = leaf
                
            score = self.evaluate(node_to_eval)
            self.backpropagate(node_to_eval, score)
            
            if leaf.is_terminal and score == 1.0:
                print(f"Found optimal path at iteration {i}")
                return leaf
                
        # Return the best child of the root after max iterations
        return max(root.children, key=lambda c: c.visits) if root.children else root

# Example Usage
if __name__ == "__main__":
    agent = LATSAgent(max_iterations=100)
    best_node = agent.search("Initial Problem State")
    print("Best State Achieved:", best_node.state_description)
```

## 3. Reflexion & Reinforcement via Verbal Feedback

Reflexion is a pattern that enables agents to learn from their mistakes without requiring weight updates (fine-tuning). It relies on a verbal memory buffer.

### The Mechanism

1. Action Generation: The agent attempts to solve a task.
2. Evaluation: An external validator (or self-evaluation) scores the attempt. If it fails, feedback is generated.
3. Reflection: The agent analyzes the feedback and writes a structured reflection into its verbal memory buffer: `(Trial Number, Goal, Mistake Identified, Actionable Learning)`.
4. Refinement: In the next iteration, the prompt is injected with the memory buffer, preventing the agent from repeating the same logical errors.

### Python Code: Reflexion Agent

```python
from pydantic import BaseModel
from typing import List

class MemoryEntry(BaseModel):
    trial_number: int
    goal: str
    mistake_identified: str
    actionable_learning: str

class ReflexionAgent:
    def __init__(self):
        self.memory_buffer: List[MemoryEntry] = []
        self.current_trial = 0

    def format_prompt(self, base_task: str) -> str:
        prompt = f"Task: {base_task}\n\n"
        if self.memory_buffer:
            prompt += "Past Reflections:\n"
            for mem in self.memory_buffer:
                prompt += f"- Trial {mem.trial_number}: I mistakenly {mem.mistake_identified}. In the future, I must {mem.actionable_learning}\n"
        return prompt

    def evaluate_output(self, output: str) -> bool:
        # Simulated deterministic evaluation
        return "optimal_solution" in output.lower()

    def generate_reflection(self, goal: str, failed_output: str) -> MemoryEntry:
        self.current_trial += 1
        # Simulated LLM reflection generation
        return MemoryEntry(
            trial_number=self.current_trial,
            goal=goal,
            mistake_identified=f"used a brute force approach in '{failed_output}'",
            actionable_learning="use a hash map to reduce time complexity to O(N)."
        )

    def solve(self, task: str):
        max_attempts = 3
        for attempt in range(max_attempts):
            prompt = self.format_prompt(task)
            print(f"--- Attempt {attempt+1} Prompt ---\n{prompt}")
            
            # Simulated LLM generation
            if attempt == 0:
                output = "Here is a nested loop solution..."
            elif attempt == 1:
                output = "Here is a sorting-based solution..."
            else:
                output = "Here is the optimal_solution using a hash map..."
                
            is_correct = self.evaluate_output(output)
            if is_correct:
                print("Task solved successfully!")
                return output
            else:
                reflection = self.generate_reflection(task, output)
                self.memory_buffer.append(reflection)
                print(f"Task failed. Reflection recorded.\n")
                
        print("Failed to solve task within max attempts.")
        return None

# Usage
agent = ReflexionAgent()
agent.solve("Find two numbers that add up to target in an array.")
```

## 4. Human-in-the-Loop (HITL) Architectures

For critical applications, autonomous execution is too dangerous. HITL architectures introduce breakpoints, state persistence, and human editing capabilities.

### Key Concepts

1. Breakpoints and Interrupts: The agent stops execution before invoking tools flagged as sensitive (e.g., `delete_database`).
2. State Persistence: The agent's memory, call stack, and pending tool arguments are serialized to a database. The process can exit, freeing up memory.
3. Resumption: An asynchronous webhook (triggered by a UI button click from a human) deserializes the state and resumes execution.
4. Human State Editing: The human doesn't just approve/reject; they can edit the arguments of the pending tool call before approving.

### Checkpointed HITL Agent Implementation

```python
import json
import uuid
from typing import Dict, Any, Literal

# Simulated Database
PERSISTENT_STORE = {}

class AgentState(BaseModel):
    session_id: str
    history: List[str]
    pending_action: Optional[Dict[str, Any]] = None
    status: Literal["RUNNING", "WAITING_ON_HUMAN", "COMPLETED", "REJECTED"] = "RUNNING"

class HITLAgent:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def save_state(self, state: AgentState):
        PERSISTENT_STORE[self.session_id] = state.model_dump_json()
        print(f"State saved for session {self.session_id}")

    def load_state(self) -> AgentState:
        data = PERSISTENT_STORE.get(self.session_id)
        if not data:
            return AgentState(session_id=self.session_id, history=[])
        return AgentState.model_validate_json(data)

    def execute_workflow(self, command: str):
        state = self.load_state()
        if state.status == "WAITING_ON_HUMAN":
            print("Cannot execute; waiting on human approval.")
            return

        state.history.append(f"User command: {command}")
        
        # Simulate agent deciding to take a destructive action
        if "delete" in command.lower():
            print("Destructive action detected. Halting for human approval.")
            state.pending_action = {
                "tool": "delete_database",
                "args": {"db_name": "production_users"}
            }
            state.status = "WAITING_ON_HUMAN"
            self.save_state(state)
            return

        print("Action safe. Executing immediately.")
        state.history.append("Executed safe action.")
        self.save_state(state)

def human_reviewer_endpoint(session_id: str, action: Literal["APPROVE", "REJECT", "EDIT"], edited_args: Dict = None):
    data = PERSISTENT_STORE.get(session_id)
    if not data:
        print("Session not found.")
        return
        
    state = AgentState.model_validate_json(data)
    if state.status != "WAITING_ON_HUMAN":
        print("Session not waiting for human.")
        return

    if action == "REJECT":
        state.status = "REJECTED"
        state.pending_action = None
        print("Human rejected the action.")
    elif action == "APPROVE":
        print(f"Executing tool {state.pending_action['tool']} with args {state.pending_action['args']}")
        state.status = "COMPLETED"
        state.pending_action = None
    elif action == "EDIT":
        state.pending_action['args'] = edited_args
        print(f"Executing tool {state.pending_action['tool']} with EDITED args {edited_args}")
        state.status = "COMPLETED"
        state.pending_action = None

    PERSISTENT_STORE[session_id] = state.model_dump_json()

# Simulation
session = str(uuid.uuid4())
agent = HITLAgent(session)
agent.execute_workflow("Please delete the old test database")

# Human reviews and edits
human_reviewer_endpoint(session, "EDIT", edited_args={"db_name": "test_users_only"})
```

## 5. Dynamic Routing & Subagent Spawning

Monolithic agents become unstable as prompt sizes grow. Modern patterns use hierarchical routing and dynamic subagent spawning.

### Fan-Out / Fan-In Parallelism

When a task can be parallelized (e.g., researching 5 different competitors), a supervisor agent can "fan-out" the work by spawning 5 independent subagents. It waits for all to complete using `asyncio.gather`, then "fans-in" the results to a synthesizer agent.

### Python Implementation of Fan-Out / Fan-In

```python
import asyncio

async def research_subagent(topic: str, delay: int) -> str:
    """A dynamically spawned subagent."""
    print(f"[Subagent] Starting research on: {topic}")
    await asyncio.sleep(delay)  # Simulate network/LLM latency
    print(f"[Subagent] Completed research on: {topic}")
    return f"Deep insights regarding {topic}..."

async def synthesizer_agent(reports: List[str]) -> str:
    """Aggregates subagent outputs."""
    print("\n[Synthesizer] Compiling final report from subagent data...")
    summary = "Executive Summary:\n"
    for idx, report in enumerate(reports):
        summary += f"{idx+1}. {report}\n"
    return summary

async def orchestrator_agent(main_topic: str, subtopics: List[str]):
    print(f"[Orchestrator] Task received: {main_topic}")
    print(f"[Orchestrator] Fanning out to {len(subtopics)} subagents...\n")
    
    # Fan-Out Phase
    tasks = []
    for topic in subtopics:
        # Assign varying delays to simulate real-world variance
        import random
        delay = random.uniform(0.5, 2.0)
        tasks.append(research_subagent(topic, delay))
        
    # Wait for all subagents concurrently
    results = await asyncio.gather(*tasks)
    
    # Fan-In Phase
    final_report = await synthesizer_agent(results)
    print("\n=== FINAL OUTPUT ===")
    print(final_report)

# Run the swarm
if __name__ == "__main__":
    asyncio.run(orchestrator_agent(
        "AI Market Analysis 2024",
        ["OpenAI models", "Anthropic models", "Google models", "Meta open source"]
    ))
```

## Conclusion

Mastering these five patterns—OODA loops for resilience, LATS for deep planning, Reflexion for self-improvement, HITL for safety, and Fan-Out/Fan-In for scale—elevates an LLM application from a simple wrapper to a true autonomous system. Each pattern introduces complexity, requiring careful state management and asynchronous programming, but the resulting robustness is essential for production-grade Agentic AI.

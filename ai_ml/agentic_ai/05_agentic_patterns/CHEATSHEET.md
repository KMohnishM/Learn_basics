# Module 5: CHEATSHEET - Advanced Agentic Patterns

## 1. Pattern Comparison Matrix

| Feature | ReAct (Reason + Act) | Reflexion (Self-Critique) | ToT / LATS (Tree Search) | OODA (Observe -> Act) |
| :--- | :--- | :--- | :--- | :--- |
| **Execution Style** | Linear / Sequential | Iterative loop with memory | Branching / Parallel paths | Continuous / Real-time |
| **Backtracking** | Very Poor | Moderate (via prompt memory) | Excellent (mathematical MCTS) | N/A (Forward moving) |
| **Compute Cost** | Low | Medium (Multiple attempts) | Extremely High | Low to Medium |
| **Latency** | Fast | Medium | Very Slow | Extremely Fast |
| **Best Used For** | Simple API calls, lookups | Coding, content refinement | Complex logic, math, planning | Gaming, Trading, Live Support |
| **Core Mechanism** | `Thought -> Action -> Obs` | `Act -> Evaluate -> Reflect` | `Select -> Expand -> Score` | `Observe -> Orient -> Decide` |

---

## 2. LATS (MCTS) Algorithm Flowchart

```text
              [ ROOT NODE ]
             /             \
  (Selection Phase via UCT formula)
           /                 \
      [ NODE A ]          [ NODE B ] (Highest UCT)
                           /      |      \
                (Expansion Phase via LLM Prompting)
                       /          |          \
                 [Leaf 1]     [Leaf 2]     [Leaf 3]
                                  |
                   (Evaluation Phase via LLM Judge)
                                  |
                          [ Score: 0.85 ]
                                  |
                (Backpropagation Phase updates tree)
                                  |
                 [Updates Node B and Root Node averages]
```

---

## 3. Human-in-the-Loop (HITL) State Machine

```text
  [ START WORKFLOW ]
          |
          v
   [ AGENT REASONING ] <-----------------------------------+
          |                                                |
          v                                                |
  [ TOOL CALL INTENT ]                                     |
          |                                                |
          v                                                |
  { Is Tool Sensitive? } --(NO)--> [ EXECUTE TOOL ] -------+
          |
        (YES)
          |
          v
  [ SERIALIZE STATE TO DB ]
          |
          v
  [ HALT AGENT PROCESS ]
          |
          v
  [ HUMAN UI DASHBOARD ]
          |
      (Human Review)
     /      |       \
    /       |        \
(REJECT) (APPROVE) (EDIT ARGS)
   |        |          |
   v        |          v
[EXIT]      |    [ UPDATE STATE DB ]
            |          |
            v          v
   [ DESERIALIZE & WAKE AGENT ]
            |
            v
      [ EXECUTE TOOL ]
            |
            v
   [ CONTINUE WORKFLOW ]
```

---

## 4. Fan-Out / Fan-In Async Python Template

```python
import asyncio
from typing import List

# 1. Worker Definition
async def worker_subagent(task_id: int, payload: str) -> str:
    """Independent subagent execution."""
    print(f"Worker {task_id} starting: {payload}")
    # Await LLM call / Tool execution here
    await asyncio.sleep(1) 
    return f"Result_{task_id}"

# 2. Synthesizer Definition
async def synthesizer(results: List[str]) -> str:
    """Aggregates outputs."""
    return f"Aggregated Report: {', '.join(results)}"

# 3. Orchestrator Definition
async def orchestrator(tasks: List[str]):
    # FAN-OUT: Create concurrent tasks
    futures = [
        worker_subagent(i, task) 
        for i, task in enumerate(tasks)
    ]
    
    # Wait for all workers to complete in parallel
    results = await asyncio.gather(*futures)
    
    # FAN-IN: Synthesize
    final_output = await synthesizer(results)
    print(final_output)

# Execution
if __name__ == "__main__":
    asyncio.run(orchestrator(["TaskA", "TaskB", "TaskC"]))
```

---

## 5. UCT Formula Breakdown (Upper Confidence Bound)

```text
UCT = ( W_i / N_i )  +  c * sqrt( ln(N_p) / N_i )
```
* **`W_i`**: Total score (wins) of the current node.
* **`N_i`**: Number of times the current node has been visited.
* **`(W_i / N_i)`**: The **Exploitation** term. Favors nodes with historically high scores.
* **`N_p`**: Number of times the parent node has been visited.
* **`c`**: Exploration parameter (usually 1.414). Higher means more random exploration.
* **`sqrt(...)`**: The **Exploration** term. Increases for unvisited nodes, forcing the algorithm to check neglected paths.

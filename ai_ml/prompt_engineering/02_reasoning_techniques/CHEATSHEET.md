# Reasoning Techniques Cheatsheet

## 1. Reasoning Techniques Decision Guide

| Technique | Complexity Level | Core Mechanism | Best Used For | Drawbacks |
| :--- | :--- | :--- | :--- | :--- |
| **Chain-of-Thought (CoT)** | Low | Elicits step-by-step logic ("Let's think step by step"). | Math, logic puzzles, basic multi-step tasks. | Susceptible to early errors cascading; linear only. |
| **Self-Consistency** | Medium | Samples diverse paths, majority vote. | Tasks with discrete verifiable answers (coding, math). | High compute cost; requires temperature tuning. |
| **Step-Back Prompting** | Medium | Abstracts to principles before solving. | Knowledge-heavy logic (physics, rulesets). | Requires tasks to have underlying principles. |
| **Least-to-Most** | High | Decomposes and solves sequentially. | Compositional generalization, long-chain arithmetic. | Very slow sequential generation. |
| **Tree of Thoughts (ToT)**| Very High | Search tree, evaluate states, backtrack. | Planning, crosswords, complex exploration. | Extreme latency; high token cost; requires harness. |

## 2. Self-Consistency Python Algorithm Flowchart

```text
+---------------------------------------------------+
|               Start Self-Consistency              |
+---------------------------------------------------+
                          |
                          v
+---------------------------------------------------+
| Set Temperature > 0.0 (e.g., 0.5)                 |
| Set Num_Samples (N = 5 to 10)                     |
+---------------------------------------------------+
                          |
                          v
+---------------------------------------------------+
| Loop i from 1 to N:                               |
|   1. Prompt Model: Question + CoT Prompt          |
|   2. Generate Path[i]                             |
|   3. Extract Answer[i] from Path[i]               |
+---------------------------------------------------+
                          |
                          v
+---------------------------------------------------+
| Aggregate Answers:                                |
|   Count frequencies of each Answer[i]             |
+---------------------------------------------------+
                          |
                          v
+---------------------------------------------------+
| Apply Majority Vote:                              |
|   Final_Answer = Mode(Answer_List)                |
+---------------------------------------------------+
                          |
                          v
+---------------------------------------------------+
|                Return Final_Answer                |
+---------------------------------------------------+
```

## 3. Tree of Thoughts (ToT) Step-by-Step Prompting Template

**Phase 1: Thought Generation**
**Prompt:** "Given the current state: [State]. Propose 3 possible next steps to advance towards the solution. Describe each step concisely."

**Phase 2: State Evaluation**
**Prompt:** "Evaluate the following proposed steps based on their potential to reach the final goal.
Goal: [Goal]
State: [State]
Proposed Step: [Step]
Score this step as 'Sure', 'Likely', or 'Impossible' to reach the goal. Provide a brief justification."

**Phase 3: Search & Branch (Managed by External Script)**
*   If Score == 'Impossible': Prune branch.
*   If Score == 'Sure' or 'Likely': Add to queue, set as new [State], loop Phase 1.

## 4. Chain-of-Density Summarization Recipe

**Step 1: Baseline Summary**
*   **Prompt:** "Write a 3-sentence summary of the provided text. Focus only on the most critical information."

**Step 2: Iterative Densification (Repeat 3-5 times)**
*   **Prompt:** "Identify 1-3 salient entities (names, numbers, concepts) from the source text that are missing from the current summary.
    Rewrite the summary to include these new entities.
    **CRITICAL CONSTRAINT:** The new summary must be exactly the same length (word count) as the previous summary. You must compress and merge sentences to make room for the new entities."

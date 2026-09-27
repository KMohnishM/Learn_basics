# Module 2: Advanced Reasoning Techniques in Prompt Engineering

## Introduction

This module delves into advanced reasoning strategies for Large Language Models (LLMs). As LLMs scale, their capacity for complex problem-solving increases, but zero-shot prompting often falls short for tasks requiring multi-step logic, formal planning, or mathematical rigor. The techniques covered here provide structural frameworks to elicit deliberate, step-by-step reasoning, unlocking higher performance on mathematical, logical, and algorithmic challenges. 

By the end of this module, you will understand the theoretical underpinnings of these methods and how to implement them programmatically using Python. We will explore everything from basic Chain-of-Thought to complex directed acyclic graph-based reasoning architectures.

---

## 1. Chain-of-Thought (CoT) Prompting

### 1.1 Foundational Discovery
Chain-of-Thought (CoT) prompting, introduced by Wei et al. (2022), is a seminal technique that significantly improves the reasoning abilities of LLMs. By providing intermediate reasoning steps alongside the final answer in few-shot exemplars, the model is guided to produce similar reasoning traces for new problems. This mimics human cognitive processes, where complex problems are broken down into manageable intermediate steps before arriving at a conclusion.

Standard prompting forces the model to map the input directly to the output:
`P(y | x)` where x is the question and y is the answer.

CoT modifies this probability distribution by conditioning the output on an intermediate reasoning trace `z`:
`P(y | x) \approx \sum_z P(y | x, z) P(z | x)`

By sampling `z` first, the model is able to arrive at `y` with much higher accuracy for tasks requiring logic.

### 1.2 Cognitive Rationale
The core mechanism behind CoT's effectiveness lies in the allocation of autoregressive forward-pass compute. Standard prompting forces the model to jump directly to the answer in a single generation step. CoT, however, allows the model to "think out loud," distributing the computational burden across multiple tokens. Each generated token conditions the probability distribution for subsequent tokens, effectively creating a working memory where intermediate conclusions guide the final inference.

### 1.3 Zero-Shot CoT
Kojima et al. (2022) discovered that simply appending "Let's think step by step" to a prompt can elicit reasoning traces without few-shot examples. This Zero-Shot CoT acts as a universal trigger, shifting the model's generation trajectory towards an analytical mode.

**Template:**
```text
Question: [Insert Problem Here]
Answer: Let's think step by step.
```

### 1.4 Manual Few-Shot CoT
While Zero-Shot CoT is highly effective, Manual Few-Shot CoT often yields superior results by demonstrating the exact reasoning format desired. This involves crafting specific exemplars tailored to the task domain.

**Example Template for Math Word Problems:**
```text
Question: Roger has 5 tennis balls. He buys 2 more cans of tennis balls. Each can has 3 tennis balls. How many tennis balls does he have now?
Reasoning: Roger started with 5 balls. 2 cans of 3 tennis balls each is 6 tennis balls. 5 + 6 = 11.
Answer: 11

Question: The cafeteria had 23 apples. If they used 20 to make lunch and bought 6 more, how many apples do they have?
Reasoning: The cafeteria had 23 apples originally. They used 20 to make lunch. So they had 23 - 20 = 3. They bought 6 more apples, so they have 3 + 6 = 9.
Answer: 9

Question: [New Problem]
Reasoning:
```

### 1.5 Auto-CoT
To reduce the manual effort of crafting exemplars, Auto-CoT automates the process by clustering questions from a dataset, selecting a representative question from each cluster, and using Zero-Shot CoT to generate reasoning traces. These generated traces, after filtering for correctness, are then used as few-shot exemplars for the main task.

---

## 2. Self-Consistency & Ensemble Reasoning

### 2.1 The Limitation of Greedy Decoding
Standard generation typically employs greedy decoding or low-temperature sampling, selecting the most probable token at each step. Wang et al. observed that this deterministic approach can trap the model in sub-optimal reasoning paths. Complex problems often have multiple valid reasoning routes leading to the correct answer, and greedy decoding fails to explore them.

### 2.2 The Self-Consistency Algorithm
Self-Consistency addresses this by sampling multiple reasoning paths (e.g., N=10 to 40) at a higher temperature. It then extracts the final answer from each path and selects the most frequent answer (majority vote). This marginalizes out the reasoning paths, focusing the probability mass on the most robust final answer.

### 2.3 Complete Python Implementation
Below is a robust Python implementation of a Self-Consistency engine, simulating the interaction with an LLM API and performing the majority vote algorithm.

```python
import re
from typing import List, Dict, Any
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class SelfConsistencyEngine:
    """
    An engine for performing Self-Consistency reasoning with LLMs.
    """
    def __init__(self, llm_client: Any, num_samples: int = 15, temperature: float = 0.7):
        """
        Initializes the Self-Consistency Engine.
        
        Args:
            llm_client: A mock or real LLM client for generating text.
            num_samples: The number of reasoning paths to sample (N).
            temperature: The sampling temperature.
        """
        self.llm_client = llm_client
        self.num_samples = num_samples
        self.temperature = temperature
        
    def _generate_paths(self, prompt: str) -> List[str]:
        """
        Generates multiple reasoning paths using the LLM.
        """
        paths = []
        for i in range(self.num_samples):
            logging.info(f"Generating path {i+1}/{self.num_samples}")
            response = self.llm_client.generate(
                prompt=prompt, 
                temperature=self.temperature,
                max_tokens=512
            )
            paths.append(response)
        return paths
        
    def _extract_answer(self, text: str) -> str:
        """
        Extracts the final answer from a reasoning path.
        Assumes the answer is formatted as 'Answer: [value]' or similar.
        """
        match = re.search(r"Answer:\s*(.*)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
            
        numbers = re.findall(r"-?\d+\.?\d*", text)
        if numbers:
            return numbers[-1]
            
        return "Extraction Failed"
        
    def _majority_vote(self, answers: List[str]) -> str:
        """
        Performs a majority vote on the extracted answers.
        """
        valid_answers = [a for a in answers if a != "Extraction Failed"]
        if not valid_answers:
            return "No valid answers generated."
            
        counter = Counter(valid_answers)
        most_common = counter.most_common(1)
        return most_common[0][0]
        
    def solve(self, problem: str) -> Dict[str, Any]:
        """
        Solves a problem using Self-Consistency.
        
        Args:
            problem: The problem statement.
            
        Returns:
            A dictionary containing the final answer and the detailed paths.
        """
        prompt = f"Question: {problem}\nAnswer: Let's think step by step.\n"
        
        logging.info(f"Starting Self-Consistency with {self.num_samples} samples...")
        paths = self._generate_paths(prompt)
        
        answers = []
        for path in paths:
            ans = self._extract_answer(path)
            answers.append(ans)
            
        final_answer = self._majority_vote(answers)
        
        return {
            "final_answer": final_answer,
            "paths": paths,
            "extracted_answers": answers
        }
```

---

## 3. Tree of Thoughts (ToT) & Graph of Thoughts (GoT)

### 3.1 Tree of Thoughts (ToT)
Introduced by Yao et al., Tree of Thoughts generalizes CoT by framing the reasoning process as a search over a tree where nodes represent intermediate thoughts. 

#### 3.1.1 Components of ToT
1.  **Thought Decomposition:** Breaking the problem into intermediate steps that the LLM can evaluate.
2.  **Thought Generation:** Proposing next steps given the current state.
3.  **State Evaluation:** Assessing the promise of a state (a sequence of thoughts) towards solving the problem. Strategies include independent valuation (rating from 1-10) or voting across states.
4.  **Search Algorithm:** Utilizing classic algorithms like Breadth-First Search (BFS) or Depth-First Search (DFS) to explore the tree of thoughts.

#### 3.1.2 Python Implementation of Tree of Thoughts
This implementation demonstrates a robust ToT search algorithm utilizing BFS and beam search.

```python
import math
from typing import List, Dict, Any, Callable

class TotNode:
    """Represents a state in the Tree of Thoughts."""
    def __init__(self, state: str, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.value = 0.0
        
    def add_child(self, child_node):
        self.children.append(child_node)
        
    def get_path(self) -> List[str]:
        path = []
        current = self
        while current:
            path.append(current.state)
            current = current.parent
        return path[::-1]

class TreeOfThoughts:
    """
    Implements the Tree of Thoughts search algorithm.
    """
    def __init__(self, 
                 llm_generator: Callable[[str, int], List[str]], 
                 llm_evaluator: Callable[[str], float],
                 max_depth: int = 5,
                 beam_width: int = 3):
        """
        Args:
            llm_generator: Function to generate next thoughts.
            llm_evaluator: Function to evaluate a thought state.
            max_depth: Maximum depth of the search tree.
            beam_width: Number of states to keep at each level (Beam Search).
        """
        self.generate = llm_generator
        self.evaluate = llm_evaluator
        self.max_depth = max_depth
        self.beam_width = beam_width
        
    def solve_bfs(self, initial_state: str) -> str:
        """
        Executes Breadth-First Search (Beam Search) to find the best reasoning path.
        """
        root = TotNode(initial_state)
        current_level = [root]
        
        for depth in range(self.max_depth):
            print(f"Exploring Depth {depth + 1}...")
            next_level = []
            
            for node in current_level:
                new_thoughts = self.generate(node.state, self.beam_width * 2)
                
                for thought in new_thoughts:
                    child = TotNode(thought, parent=node)
                    child.value = self.evaluate(child.state)
                    node.add_child(child)
                    next_level.append(child)
                    
            next_level.sort(key=lambda x: x.value, reverse=True)
            current_level = next_level[:self.beam_width]
            
            if not current_level:
                break
                
        best_node = max(current_level, key=lambda x: x.value)
        best_path = best_node.get_path()
        return "\n -> ".join(best_path)
```

### 3.2 Graph of Thoughts (GoT)
Besta et al. introduced Graph of Thoughts, extending ToT by allowing arbitrary graph structures. GoT enables operations like aggregating multiple reasoning paths into a single thought or refining a previous thought based on new information. This models non-linear human problem-solving more accurately, where we often combine ideas or backtrack and modify previous assumptions.

#### 3.2.1 Core GoT Operations
- **Aggregation:** Merging multiple thoughts into a consolidated state.
- **Refinement:** Iteratively improving a single thought.
- **Generation:** Expanding a thought into multiple potential next steps.

#### 3.2.2 Python Implementation of Graph of Thoughts

```python
import uuid
from typing import List, Set, Dict

class GotNode:
    """Represents a thought in a Graph of Thoughts."""
    def __init__(self, content: str):
        self.id = str(uuid.uuid4())
        self.content = content
        self.parents: List['GotNode'] = []
        self.score: float = 0.0

class GraphOfThoughts:
    """
    A foundational implementation of the Graph of Thoughts framework.
    """
    def __init__(self, llm_client):
        self.llm = llm_client
        self.nodes: Dict[str, GotNode] = {}
        
    def add_node(self, content: str, parents: List[GotNode] = None) -> GotNode:
        node = GotNode(content)
        if parents:
            node.parents.extend(parents)
        self.nodes[node.id] = node
        return node
        
    def evaluate_node(self, node: GotNode) -> float:
        prompt = f"Rate the quality of this thought on a scale of 0 to 1:\nThought: {node.content}\nScore:"
        try:
            response = self.llm.generate(prompt)
            node.score = float(response.strip())
        except ValueError:
            node.score = 0.0
        return node.score

    def aggregate(self, nodes: List[GotNode]) -> GotNode:
        """Aggregates multiple thoughts into a single synthesized thought."""
        combined_content = "\n".join([f"- {n.content}" for n in nodes])
        prompt = f"Synthesize the following thoughts into a single coherent conclusion:\n{combined_content}\nSynthesis:"
        synthesized_content = self.llm.generate(prompt)
        return self.add_node(synthesized_content, parents=nodes)
        
    def refine(self, node: GotNode) -> GotNode:
        """Refines a thought to improve its quality."""
        prompt = f"Critique and improve the following thought:\nOriginal: {node.content}\nImproved Thought:"
        improved_content = self.llm.generate(prompt)
        return self.add_node(improved_content, parents=[node])

    def solve(self, initial_problem: str, iterations: int = 3) -> GotNode:
        """
        Executes a simplistic GoT algorithm.
        """
        root = self.add_node(f"Initial problem: {initial_problem}")
        current_layer = [root]
        
        for i in range(iterations):
            next_layer = []
            for node in current_layer:
                # Generate multiple paths
                for _ in range(2):
                    prompt = f"Given this context: {node.content}, what is the next logical step?"
                    new_thought = self.llm.generate(prompt)
                    new_node = self.add_node(new_thought, parents=[node])
                    self.evaluate_node(new_node)
                    next_layer.append(new_node)
            
            # Select top thoughts
            next_layer.sort(key=lambda n: n.score, reverse=True)
            top_thoughts = next_layer[:3]
            
            # Aggregate top thoughts
            if len(top_thoughts) > 1:
                aggregated = self.aggregate(top_thoughts)
                self.evaluate_node(aggregated)
                current_layer = [aggregated]
            else:
                current_layer = top_thoughts
                
        return current_layer[0]
```

---

## 4. Specialized Reasoning Frameworks

### 4.1 Step-Back Prompting
Step-Back Prompting involves prompting the model to abstract a specific problem into a broader principle or concept before attempting to solve it. By grounding its reasoning in high-level principles, the model is less prone to errors in specific details. This method is exceptionally powerful for Physics and Mathematics domains.

**Process:**
1.  **Abstraction:** Prompt the LLM to identify the underlying principle or concept of the problem.
2.  **Reasoning:** Prompt the LLM to use the identified principle to solve the original problem.

**Example Implementation:**
```python
class StepBackPrompting:
    def __init__(self, llm_client):
        self.llm = llm_client
        
    def solve(self, question: str) -> str:
        # Step 1: Abstraction
        abstraction_prompt = f"What is the underlying physics principle or formula required to solve this question: '{question}'? Provide only the principle."
        principle = self.llm.generate(abstraction_prompt)
        
        # Step 2: Reasoning
        reasoning_prompt = f"Principle: {principle}\n\nUse this principle to answer the following question step by step: {question}"
        answer = self.llm.generate(reasoning_prompt)
        
        return f"Identified Principle: {principle}\n\nFinal Answer: {answer}"
```

### 4.2 Least-to-Most Prompting
Least-to-Most Prompting breaks down a complex problem into a series of simpler subproblems and solves them sequentially. Crucially, the solution to each subproblem is appended to the prompt for subsequent subproblems.

**Process:**
1.  **Decomposition:** The LLM decomposes the main problem into a list of subproblems.
2.  **Sequential Solving:** The LLM solves each subproblem one by one, using previously generated answers as context.

```python
class LeastToMostPrompting:
    def __init__(self, llm_client):
        self.llm = llm_client
        
    def solve(self, problem: str) -> str:
        # Step 1: Decomposition
        decomp_prompt = f"Break down the following complex problem into a numbered list of simpler sub-questions. Problem: {problem}"
        sub_questions_raw = self.llm.generate(decomp_prompt)
        sub_questions = [sq.strip() for sq in sub_questions_raw.split('\n') if sq.strip() and sq[0].isdigit()]
        
        # Step 2: Sequential Solving
        context = ""
        for i, sq in enumerate(sub_questions):
            solve_prompt = f"Context previously established:\n{context}\n\nQuestion: {sq}\nAnswer:"
            answer = self.llm.generate(solve_prompt)
            context += f"Q: {sq}\nA: {answer}\n\n"
            
        # Final answer formulation based on all context
        final_prompt = f"Based on the following steps:\n{context}\n\nProvide the final answer to the original problem: {problem}"
        final_answer = self.llm.generate(final_prompt)
        return final_answer
```

### 4.3 Chain-of-Density (CoD) Summarization
Chain-of-Density is a specialized technique for generating highly dense and informative summaries. The model is prompted to iteratively rewrite a summary, adding new missing entities from the source text at each step while maintaining the same length. This forces the model to abstract and condense information, resulting in a summary with high entity density.

**CoD Iteration Process:**
1.  Generate a baseline summary.
2.  Identify 1-3 missing key entities from the source text.
3.  Rewrite the summary to incorporate the new entities, keeping the length exactly the same.
4.  Repeat steps 2-3 for N iterations.

```python
class ChainOfDensity:
    def __init__(self, llm_client):
        self.llm = llm_client
        
    def summarize(self, document: str, iterations: int = 3) -> List[str]:
        summaries = []
        
        # Initial baseline summary
        prompt = f"Write a brief summary of the following text:\n{document}\nSummary:"
        current_summary = self.llm.generate(prompt)
        summaries.append(current_summary)
        
        for _ in range(iterations):
            density_prompt = f"""
            Article: {document}
            Current Summary: {current_summary}
            
            Task:
            1. Identify 2 key entities from the Article missing from the Current Summary.
            2. Rewrite the Current Summary to include these new entities.
            3. The new summary MUST be the exact same length as the Current Summary.
            
            Output format:
            Missing Entities: [entity1, entity2]
            Dense Summary: [your new summary here]
            """
            
            response = self.llm.generate(density_prompt)
            match = re.search(r"Dense Summary:\s*(.*)", response, re.DOTALL | re.IGNORECASE)
            if match:
                current_summary = match.group(1).strip()
                summaries.append(current_summary)
                
        return summaries
```

### 4.4 Skeleton-of-Thought (SoT)
Skeleton-of-Thought is designed to reduce the latency of LLM generation. Instead of generating the answer sequentially, SoT prompts the model to first generate a "skeleton" or outline of the answer. Then, it issues parallel requests to generate the content for each point in the skeleton simultaneously.

**Process:**
1.  **Skeleton Generation:** Prompt the LLM to provide a concise outline of the answer.
2.  **Point Expansion:** For each point in the outline, initiate a separate API call to expand on that point concurrently.
3.  **Aggregation:** Concatenate the expanded points into the final answer.

**Implementation Example:**
```python
import concurrent.futures

class SkeletonOfThought:
    def __init__(self, llm_client):
        self.llm = llm_client
        
    def generate_skeleton(self, prompt: str) -> List[str]:
        skeleton_prompt = f"Provide a brief outline (list of points) to answer: {prompt}. Output only the points, one per line."
        response = self.llm.generate(skeleton_prompt)
        return [point.strip() for point in response.split('\n') if point.strip()]
        
    def expand_point(self, point: str, context: str) -> str:
        expansion_prompt = f"Context: {context}\nExpand on this specific point in one paragraph: {point}"
        return self.llm.generate(expansion_prompt)
        
    def solve(self, prompt: str) -> str:
        # Step 1: Generate Skeleton
        skeleton = self.generate_skeleton(prompt)
        
        # Step 2: Parallel Expansion
        expanded_points = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            futures = [executor.submit(self.expand_point, point, prompt) for point in skeleton]
            
            # Collect results in order
            for future in futures:
                expanded_points.append(future.result())
                
        # Step 3: Aggregation
        final_answer = ""
        for i, (point, expansion) in enumerate(zip(skeleton, expanded_points)):
            final_answer += f"### {i+1}. {point}\n{expansion}\n\n"
            
        return final_answer
```

---

## 5. ReAct (Reasoning and Acting)

### 5.1 Introduction to ReAct
ReAct (Yao et al., 2022) is a paradigm that interleaves reasoning traces and action steps in LLMs. While CoT relies solely on internal parametric knowledge, ReAct enables models to interact with external environments (e.g., APIs, search engines, databases) to gather information. The reasoning steps guide the next actions, and the observations from actions inform subsequent reasoning.

### 5.2 Implementation of ReAct
The implementation involves a loop of Thought -> Action -> Observation until the final answer is found.

```python
import re

class ReActAgent:
    def __init__(self, llm_client, tools: Dict[str, Callable]):
        self.llm = llm_client
        self.tools = tools
        self.max_steps = 10
        
    def run(self, query: str) -> str:
        prompt = f"Answer the following query using the available tools: {list(self.tools.keys())}.\nQuery: {query}\n"
        
        for step in range(self.max_steps):
            response = self.llm.generate(prompt)
            prompt += response + "\n"
            
            # Check for Final Answer
            if "Final Answer:" in response:
                return response.split("Final Answer:")[1].strip()
                
            # Parse Action
            action_match = re.search(r"Action:\s*(\w+)\s*\[(.*?)\]", response)
            if action_match:
                tool_name, tool_input = action_match.groups()
                if tool_name in self.tools:
                    observation = self.tools[tool_name](tool_input)
                    prompt += f"Observation: {observation}\n"
                else:
                    prompt += f"Observation: Error - Tool {tool_name} not found.\n"
                    
        return "Failed to find final answer within max steps."
```

## 6. Evaluation Strategies

Evaluating reasoning capabilities requires more than just accuracy matching.
- **Exact Match (EM):** Checking if the final extracted string matches the ground truth.
- **Reasoning Trace Overlap:** Using ROUGE or BLEU to score the intermediate steps against human-written CoT.
- **Logical Entailment:** Using a secondary judge LLM to verify that step N+1 logically follows from step N.

## Advanced Discussion on Prompt Optimization
Prompt engineering is moving towards automated optimization. Techniques like DSPy programmatically optimize prompts by defining the desired behavior and using a compiler to automatically generate and refine few-shot exemplars and instructions. This shifts the paradigm from manual prompt crafting to prompt programming, enabling dynamic adaptation across different underlying models without requiring complete rewrites of the prompt logic. By viewing prompting through the lens of program compilation, developers can rely on automated metric-driven optimization rather than trial and error.

## Conclusion
Mastering these advanced reasoning techniques allows practitioners to push the boundaries of what LLMs can achieve. By structuring the model's generation process, we can mitigate hallucinations, improve logical consistency, and tackle problems that were previously out of reach. The transition from simple instruction tuning to structured reasoning frameworks represents a fundamental shift in how we interact with and utilize large language models, moving towards reliable, complex programmatic AI systems.

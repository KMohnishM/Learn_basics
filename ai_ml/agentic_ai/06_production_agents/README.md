# Module 6: Production Agents

## Introduction

Moving an autonomous agent from a Jupyter notebook to a production environment requires a massive paradigm shift. Standard software engineering principles—observability, security, evaluation, and cost management—must be adapted to handle the non-deterministic nature of Large Language Models. In this module, we will cover rigorous evaluation frameworks, OpenTelemetry tracing, sandbox security for tool execution, and architectural optimizations to reduce latency and token costs.

## 1. Agent Evaluation & Benchmarking

Evaluating agents is fundamentally different from evaluating standard LLM outputs. Traditional NLP metrics like BLEU and ROUGE are useless because they measure text similarity, whereas agents are designed to execute actions and mutate state.

### Multi-Dimensional Evaluation

1. Trajectory Evaluation: Did the agent take an optimal path? This involves measuring:
   - Tool Call Accuracy: Did it use the right tools with the correct arguments?
   - Extraneous Calls: Did it make redundant or hallucinated tool calls?
   - Backtracking Count: How many times did it fail and have to correct itself?
2. Final State Evaluation: Regardless of the path, was the overarching goal accomplished? (e.g., Is the database updated correctly? Does the generated code compile and pass tests?)
3. Efficiency: Total tokens consumed, end-to-end execution latency, and the number of steps taken.

### Industry Benchmarks
- SWE-bench: Evaluates software engineering agents by tasking them to resolve real-world GitHub issues. Success is measured by running the repository's unit test suite.
- GAIA: General AI Assistants benchmark measuring reasoning, tool use, and web browsing.
- WebArena: Evaluates agents navigating real web applications.

### LLM-as-a-Judge Python Framework

```python
import json
from pydantic import BaseModel, Field
from typing import List, Dict

class EvaluationScore(BaseModel):
    trajectory_score: int = Field(ge=1, le=5, description="Score from 1 to 5 for efficiency of path taken.")
    final_state_score: int = Field(ge=0, le=1, description="Binary score: 1 if goal achieved, 0 otherwise.")
    reasoning: str = Field(description="Detailed explanation for the scores.")

class LLMJudge:
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name

    def build_evaluation_prompt(self, task: str, agent_trajectory: List[Dict], final_output: str) -> str:
        prompt = f"""
        You are an expert AI evaluator. Review the following agent execution:
        
        TASK: {task}
        
        TRAJECTORY:
        {json.dumps(agent_trajectory, indent=2)}
        
        FINAL OUTPUT:
        {final_output}
        
        Evaluate the agent based on trajectory efficiency (no redundant steps, correct tool usage) 
        and final state accuracy. Return a JSON object matching the EvaluationScore schema.
        """
        return prompt

    def evaluate_run(self, task: str, trajectory: List[Dict], output: str) -> EvaluationScore:
        prompt = self.build_evaluation_prompt(task, trajectory, output)
        print("Sending prompt to LLM Judge...")
        
        # Simulated LLM response
        simulated_response = {
            "trajectory_score": 4,
            "final_state_score": 1,
            "reasoning": "The agent achieved the goal successfully. However, it made one redundant API call to the search tool before utilizing the database tool."
        }
        
        return EvaluationScore(**simulated_response)

def run_evaluation_suite():
    judge = LLMJudge()
    
    # Mock data for an agent run
    task = "Find the total revenue for Q3."
    trajectory = [
        {"step": 1, "tool": "search_web", "args": {"query": "Q3 revenue"}},
        {"step": 2, "tool": "query_sql_db", "args": {"query": "SELECT sum(amount) FROM sales WHERE quarter='Q3'"}}
    ]
    output = "The total revenue for Q3 is $4.2M."
    
    score = judge.evaluate_run(task, trajectory, output)
    print("Evaluation Results:")
    print(f"Trajectory: {score.trajectory_score}/5")
    print(f"Success: {score.final_state_score}/1")
    print(f"Notes: {score.reasoning}")

if __name__ == "__main__":
    run_evaluation_suite()
```

## 2. Distributed Tracing & Observability

When an agent fails in production, looking at raw application logs is insufficient. You need to trace the exact sequence of LLM generations, tool executions, and memory retrievals.

### OpenTelemetry and OpenInference

OpenTelemetry provides a standard for distributed tracing. For AI agents, the OpenInference standard extends OpenTelemetry to include LLM-specific attributes.

- Traces: Represent the entire end-to-end user session or workflow.
- Spans: Represent individual operations within the trace (e.g., an LLM call, a tool execution).
- Attributes: Metadata attached to spans (e.g., token usage, model name, prompt templates, tool arguments).

### Python Code: OpenTelemetry Manual Spans

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# Setup OpenTelemetry
provider = TracerProvider()
processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

class ObservableAgent:
    def execute_tool(self, tool_name: str, args: dict) -> str:
        with tracer.start_as_current_span("tool_execution") as span:
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("tool.arguments", str(args))
            
            print(f"Executing {tool_name}...")
            # Simulate tool execution
            result = f"Result of {tool_name}"
            
            span.set_attribute("tool.result", result)
            return result

    def generate_response(self, prompt: str) -> str:
        with tracer.start_as_current_span("llm_generation") as span:
            span.set_attribute("llm.model", "gpt-4")
            span.set_attribute("llm.prompt", prompt)
            
            print("Generating LLM response...")
            response = "I have completed the task."
            
            span.set_attribute("llm.response", response)
            span.set_attribute("llm.usage.total_tokens", 150)
            return response

    def run_workflow(self, user_query: str):
        with tracer.start_as_current_span("agent_workflow") as span:
            span.set_attribute("session.user_query", user_query)
            
            # Step 1: Tool execution
            self.execute_tool("fetch_data", {"source": "database"})
            
            # Step 2: Generation
            final_answer = self.generate_response(user_query)
            span.set_attribute("session.final_answer", final_answer)

if __name__ == "__main__":
    agent = ObservableAgent()
    agent.run_workflow("Summarize the latest data.")
```

## 3. Safety, Guardrails & Sandboxing

Deploying agents with tool access introduces critical security vulnerabilities.

### Threat Vectors
1. Direct Prompt Injection: A malicious user instructs the agent to ignore its system prompt and execute harmful commands.
2. Indirect Prompt Injection: The agent fetches a seemingly benign webpage or email that contains hidden instructions commanding the agent to exfiltrate data.
3. Privilege Escalation: The agent attempts to access tools or data outside its authorized scope.

### Defense in Depth
- Guardrails: Input/output filtering using libraries like NeMo Guardrails to scan for injection attempts.
- Action Whitelisting: Strictly defining which tools an agent can use, and applying Dual-Key Authorization for destructive actions.
- Sandboxing: Running code generated by the agent in highly isolated microVMs or containers (e.g., gVisor, Firecracker) to prevent host system compromise.

### Python Code: Secure Tool Execution Sandbox

```python
import subprocess
import json

class CodeSandbox:
    def __init__(self):
        # In a real environment, this would interface with Docker or gVisor
        self.timeout_seconds = 5
        self.forbidden_imports = ["os", "sys", "subprocess", "socket"]

    def sanitize_code(self, code: str) -> bool:
        """Basic static analysis to prevent obvious malicious imports."""
        for module in self.forbidden_imports:
            if f"import {module}" in code or f"from {module}" in code:
                print(f"[Sandbox Error] Forbidden import detected: {module}")
                return False
        return True

    def execute(self, python_code: str) -> str:
        print("--- Initiating Sandboxed Execution ---")
        if not self.sanitize_code(python_code):
            return "Execution failed due to security violation."

        try:
            # WARNING: Using subprocess directly on host is NOT a true sandbox.
            # This is for architectural demonstration. Production requires Docker/gVisor.
            result = subprocess.run(
                ["python", "-c", python_code],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Execution timed out."
        except Exception as e:
            return f"System error: {str(e)}"

# Usage
sandbox = CodeSandbox()
safe_code = "print('Hello from the sandbox!')"
print("Safe code output:", sandbox.execute(safe_code))

malicious_code = "import os\nos.system('echo Hacked!')"
print("Malicious code output:", sandbox.execute(malicious_code))
```

## 4. Cost, Latency & Reliability Engineering

Scaling agents to thousands of users requires architectural optimizations to prevent exploding API costs and unacceptable latency.

### Optimizations
1. Prompt Caching: Iterative agent loops (like ReAct) repeatedly send the same massive system prompt and tool definitions on every step. Leveraging provider-level prefix caching (e.g., Anthropic Prompt Caching) cuts input token costs by up to 90% and dramatically reduces latency.
2. Model Tiering / Semantic Routing: Do not use expensive frontier models (GPT-4, Claude 3.5 Sonnet) for every step. Route simple triage, intent classification, and summarization tasks to fast, cheap, smaller models (e.g., Llama 3 8B, Haiku), and reserve frontier models exclusively for complex reasoning.
3. Semantic Caching of Tools: If an agent asks "What is the weather in NY?" and later asks "Current temp in New York", a semantic cache can intercept the second request and return the cached result of the first, avoiding redundant external API calls.
4. Loop Prevention: Implement strict step thresholds (`max_iterations = 10`) and state trajectory hashing to detect infinite cycle loops before token budgets are depleted.

## Conclusion

Building production agents is less about prompt engineering and more about robust systems engineering. By integrating rigorous LLM-as-a-judge evaluations, deep OpenTelemetry observability, containerized sandboxing, and caching strategies, developers can deploy autonomous systems that are secure, reliable, and cost-effective at scale.

### Section: SWE-bench Style Trajectory Evaluation
```python
from pydantic import BaseModel
from typing import List, Dict, Any

class AgentTrajectoryStep(BaseModel):
    step_index: int
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str
    duration_ms: float
    token_usage: Dict[str, int]

class TrajectoryEvaluator:
    """Evaluates agent trajectory for tool accuracy, backtracking, and efficiency."""
    @staticmethod
    def calculate_efficiency_score(trajectory: List[AgentTrajectoryStep], optimal_steps: int) -> float:
        actual_steps = len(trajectory)
        if actual_steps == 0:
            return 0.0
        return max(0.0, min(1.0, optimal_steps / actual_steps))
```

### Section: OpenTelemetry & OpenInference Tracing Implementation
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer("agent.tracer")

def trace_agent_step(step_name: str, input_payload: dict):
    with tracer.start_as_current_span(f"agent.step.{step_name}") as span:
        span.set_attribute("openinference.span.kind", "CHAIN")
        span.set_attribute("input.value", str(input_payload))
        # Execute step logic
        span.set_status(trace.StatusCode.OK)
```

### Section: Sandboxing with gVisor & Docker
- Isolating arbitrary code execution tools with runsc (gVisor).
- Network egress controls and temporary container destruction.
- Token and compute rate limiters.









































































































































































































































































































































































































































































































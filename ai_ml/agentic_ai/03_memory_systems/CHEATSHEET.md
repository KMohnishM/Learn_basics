# Agentic AI Memory Systems Cheatsheet

## Agent Memory Taxonomy Table

| Memory Type | Equivalent in Humans | Architecture Role | Latency / Size | Example Implementation |
|---|---|---|---|---|
| Working (Short-Term) | Immediate conscious thought | Current context window | Ultra-low / Fixed token limit | System prompt, recent message history, scratchpad |
| Episodic (Long-Term) | Memories of specific events | Log of past actions and observations | Low / Massive (Vector DB) | RAG over past conversations indexed by time/topic |
| Semantic (Long-Term) | General world knowledge | Factual reference base | Low / Massive (Vector/Graph DB) | RAG over documents, Wikipedia, knowledge graphs |
| Procedural (Long-Term) | Motor skills, how to do things | Code, tools, workflows | Medium / Moderate | Code repositories, stored Python functions, tool registries |
| Core (MemGPT) | Core identity and user facts | Always-in-context fixed fields | Ultra-low / Small | `edit_core_memory` function, editable text block |

## MemGPT Memory Tiers & Function Reference

MemGPT treats LLMs like an OS treats the CPU, using hierarchical memory management.

### Memory Tiers
1. Main Context (RAM): The fixed context window of the LLM. Contains Core Memory and working context.
2. External Memory (Disk): Massive storage outside the context window. Contains Recall Memory (past interactions) and Archival Memory (general facts).

### Function Reference
* `core_memory_append(section, content)`: Appends text to a specific section (e.g., "human" or "persona") of the Core Memory.
* `core_memory_replace(section, old_content, new_content)`: Edits existing text in the Core Memory.
* `archival_memory_insert(content)`: Saves a factual snippet to the Archival Memory (Vector DB).
* `archival_memory_search(query, page)`: Queries the Archival Memory using vector similarity or BM25.
* `recall_memory_search(query, date_range, page)`: Queries the past conversation history.

## Memory Scoring & Recency Formula Reference (Generative Agents)

When retrieving memories, a composite score determines relevance.

Score = (Alpha * Recency) + (Beta * Importance) + (Gamma * Relevance)

Where:
* Recency: Exponential decay based on time since the memory was formed or last accessed.
  * Formula: Decay = e^(-decay_rate * hours_since_last_access)
* Importance: A static score (1-10) assigned by the LLM when the memory is created. Mundane events get 1, critical events get 10.
* Relevance: Cosine similarity between the query embedding and the memory embedding.
* Alpha, Beta, Gamma: Weighting coefficients (typically 1.0 each in standard implementations).

## Python Context Manager Template

```python
import tiktoken
from typing import List, Dict

class TokenBudgetManager:
    def __init__(self, model_name: str = "gpt-4", max_tokens: int = 8192, reserve_tokens: int = 1000):
        self.encoder = tiktoken.encoding_for_model(model_name)
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens  # Reserved for new user input and agent response
        self.budget = self.max_tokens - self.reserve_tokens
        
    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))
        
    def count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        total = 0
        for msg in messages:
            total += 4  # Formatting overhead per message
            total += self.count_tokens(msg.get("role", ""))
            total += self.count_tokens(msg.get("content", ""))
        total += 2  # Reply prime overhead
        return total
        
    def prune_messages(self, messages: List[Dict[str, str]], system_prompt: Dict[str, str]) -> List[Dict[str, str]]:
        system_tokens = self.count_message_tokens([system_prompt])
        available_budget = self.budget - system_tokens
        
        retained_messages = []
        current_tokens = 0
        
        # Traverse backwards to keep the most recent context
        for msg in reversed(messages):
            msg_tokens = self.count_message_tokens([msg])
            if current_tokens + msg_tokens <= available_budget:
                retained_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
                
        return [system_prompt] + retained_messages
```

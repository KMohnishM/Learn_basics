# LangGraph Module 3: State Management (Reducers & Overwrites)

This module covers **State Reducers and Schemas**. We will examine the mechanics of key merging, how to define custom update operations using Python's `Annotated` type, and how to use the built-in `add_messages` reducer to accumulate conversational history.

---

## 💡 Core Theory

### 1. The Overwrite Default
By default, when a graph node executes and returns a dictionary, LangGraph merges the keys back into the main state dictionary. For standard types (strings, integers, floats, standard dicts), the new value simply **overwrites** the existing value:

```python
# Initial State: {"count": 1, "topic": "AI"}
# Node returns: {"count": 2}
# Merged State: {"count": 2, "topic": "AI"} (topic is preserved, count is overwritten)
```

However, if you want to accumulate list items (such as log lists or message histories), this default overwrite behavior is problematic:

```python
# Initial State: {"logs": ["Task started"]}
# Node returns: {"logs": ["Task completed"]}
# Merged State: {"logs": ["Task completed"]} (The original logs are OVERWRITTEN and lost!)
```

---

### 2. Enter Reducers
To solve this, LangGraph allows you to define a **Reducer** function for any key in your state. A Reducer is a python function that takes the *current* key value and the *new update* value, and returns the *merged* value.

We assign Reducer functions using Python's **`Annotated`** metadata type hint system:

```python
from typing import Annotated, TypedDict

# 1. Write the Reducer function
def append_logs(current: list, update: list) -> list:
    """Combines the current list with the new update list."""
    return current + update

# 2. Declare the State schema using the Reducer annotation
class LoggingState(TypedDict):
    task_name: str                                  # Defaults to overwrite
    logs: Annotated[list[str], append_logs]        # Uses the custom append Reducer!
```

Now, when a node returns `{"logs": ["Task completed"]}`, LangGraph detects the annotation, executes `append_logs(current_logs, ["Task completed"])`, and saves the combined list!

---

### 3. The Conversational Reducer: `add_messages`
Managing list inputs is especially critical when handling lists of chat message objects (`SystemMessage`, `HumanMessage`, `AIMessage`). LangGraph provides a robust, built-in reducer called **`add_messages`** (in `langgraph.graph.message`):

```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ConversationalState(TypedDict):
    # add_messages accumulates messages automatically
    messages: Annotated[list[BaseMessage], add_messages]
```

#### Why is `add_messages` special?
1. **Appending**: When a node returns `{"messages": [HumanMessage(content="Hello")]}`, the message is appended to the end of the history.
2. **Standardization**: It automatically converts raw strings or raw dict inputs (e.g. `{"role": "user", "content": "hi"}`) into proper message objects (`HumanMessage`).
3. **Id-Based Replacement (Upserting)**: If an incoming message has the **same `id`** as a message already present in the list, `add_messages` will **replace** the old message instead of appending it. This is how agents edit their previous responses or overwrite tool call status records.

---

### 4. Simplified State: `MessagesState`
Because defining chat message lists is so common, LangGraph provides a pre-built schema class called **`MessagesState`** that you can inherit from. It has a single `messages` key pre-configured with the `add_messages` reducer:

```python
from langgraph.graph import MessagesState

# This class automatically possesses a 'messages' key with the add_messages reducer!
class CustomState(MessagesState):
    extra_field: str  # You can add additional fields if needed
```

We will build custom reducers and explore message accumulation in the coding notebook!

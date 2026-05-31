# 🦜️🔗 Deep Dive LangChain Curriculum (Basic to Advanced)

Welcome to the **LangChain Mastery Curriculum**. This repository contains a structured, end-to-end guide designed to take you from a complete beginner to building sophisticated, autonomous LLM-powered applications. 

We focus on **in-depth theory, code mechanics, raw schemas, and zero placeholders**, using **free models** via OpenRouter and Hugging Face.

---

## 🛠️ Environment Setup

To start running the code, follow these steps to set up your local environment:

### Step 1: Clone and Navigate to Directory
Ensure you are in the `langchain/` directory:
```bash
cd langchain
```

### Step 2: Create a Virtual Environment
Create and activate a Python virtual environment to keep dependencies isolated:
```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
Install all the required libraries:
```bash
pip install -r requirements.txt
```

### Step 4: Configure API Keys
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Open the `.env` file and insert your API keys:
- **OpenRouter API Key**: Sign up at [OpenRouter](https://openrouter.ai/) to access free models (like Gemma 2, Llama 3, and Qwen 2.5) with no credit card required.
- **Hugging Face Token** (Optional): Sign up at [Hugging Face](https://huggingface.co/) for serverless API endpoints.
- **LangSmith API Key** (Optional): Sign up at [LangSmith](https://smith.langchain.com/) for beautiful tracking and execution debugging traces.

---

## 📚 Curriculum Structure & Progress Tracker

Here is the step-by-step roadmap. Use this tracker to mark your progress!

| Module | Topic | Format | Status | Key Concepts Covered |
| :--- | :--- | :--- | :--- | :--- |
| **[Module 1](./modules/01_setup_and_basics/README.md)** | [Setup & Basics](./modules/01_setup_and_basics/) | Notebook | ⏳ Pending | Virtual Envs, OpenRouter connection, Prompt messages (`System`, `Human`, `AI`), raw input/output schemas |
| **[Module 2](./modules/02_prompts_and_parsers/README.md)** | [Prompts & Output Parsers](./modules/02_prompts_and_parsers/) | Notebook | ⏳ Pending | `PromptTemplate`, `ChatPromptTemplate`, variable inputs, structured output parsing (`PydanticOutputParser`, `JsonOutputParser`), auto-validation |
| **[Module 3](./modules/03_lcel_and_chains/README.md)** | [LCEL & Chains](./modules/03_lcel_and_chains/) | Notebook | ⏳ Pending | LangChain Expression Language (LCEL), pipe operator (`\|`), `RunnableSequence`, `RunnablePassthrough`, `RunnableParallel`, `RunnableLambda` |
| **[Module 4](./modules/04_memory_and_history/README.md)** | [Memory & History](./modules/04_memory_and_history/) | Notebook | ⏳ Pending | Chat history buffers, trimming history to save tokens, persistence using SQLite databases, state representation |
| **[Module 5](./modules/05_rag_and_vectorstores/README.md)** | [RAG & Vectorstores](./modules/05_rag_and_vectorstores/) | Python Scripts | ⏳ Pending | Loaders, chunking strategies, vector embeddings, vector stores (FAISS), retrieval pipelines, context injection |
| **[Module 6](./modules/06_agents_and_tools/README.md)** | [Agents & Tools](./modules/06_agents_and_tools/) | Python Scripts | ⏳ Pending | Tool binding, `@tool` definition, function schemas, ReAct loop, tool-calling agents, orchestration |
| **[Module 7](./modules/07_advanced_concepts/README.md)** | [Advanced Production](./modules/07_advanced_concepts/) | Python Scripts | ⏳ Pending | Token streaming (`astream_events`), fallbacks, monitoring via LangSmith |

---

## 🎨 Recommended Workflow
1. Read the **`README.md`** inside each module folder first. It contains the theoretical foundations, API signatures, and deep explanation of "why" we use these components.
2. Open and run the corresponding **notebook (`.ipynb`)** or **script (`.py`)** in your IDE to watch the code execute in real-time.
3. Solve the **hands-on exercise** in each folder to test your understanding. Do not look at the `solution` file until you have attempted it yourself!

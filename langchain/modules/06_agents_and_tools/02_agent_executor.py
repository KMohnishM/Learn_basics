"""
MODULE 6 - SCRIPT 2: Orchestrating Agents with AgentExecutor.

This script demonstrates how to assemble a full autonomous agent equipped
with tools, prompting structures, and an execution loop.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: Please define OPENROUTER_API_KEY in your .env file.")
    sys.exit(1)

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

# ------------------------------------------------------------------------------
# Step 1: Define Tools
# ------------------------------------------------------------------------------
@tool
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numerical values together and return the result.
    
    Args:
        a: The first number.
        b: The second number.
    """
    return a * b

@tool
def get_user_status(username: str) -> str:
    """Query the user access database to find their account permissions.
    
    Args:
        username: The account handle (e.g. 'mclara').
    """
    users = {
        "alice": "Status: Active | Role: Admin",
        "bob": "Status: Suspended | Role: Contractor",
        "clara": "Status: Active | Role: Developer"
    }
    return users.get(username.lower(), f"User '{username}' not found in database.")

tools = [multiply_numbers, get_user_status]

# ------------------------------------------------------------------------------
# Step 2: Initialize Model
# ------------------------------------------------------------------------------
# Llama-3-8B-Instruct or Qwen-2.5-72B work excellent for tool calling.
model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    temperature=0.0,
)

# create_agent returns a compiled graph that loops through tool calls until done.
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt="You are a helpful IT operations assistant. Resolve the query using tools if needed.",
)


def _get_last_message_text(state: dict) -> str:
    """Extract the last assistant message from a LangChain agent state."""
    messages = state.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    if hasattr(last, "content"):
        return last.content
    if isinstance(last, dict):
        return last.get("content", "")
    return str(last)

# ------------------------------------------------------------------------------
# Step 5: Execute Queries
# ------------------------------------------------------------------------------
print("\n--- Running Single-Step Tool Query ---")
res_single = agent.invoke({"messages": [{"role": "user", "content": "Check the database status for username 'clara'."}]})
print("\nFinal Answer:\n", _get_last_message_text(res_single))


print("\n\n--- Running Multi-Step Query ---")
# The agent needs to:
# 1. Look up 'clara' status.
# 2. Get numbers to multiply (e.g. multiply 45 by 2).
# 3. Formulate the combined response.
query = "What is Clara's status? Also, what is 12.5 times 8?"
res_multi = agent.invoke({"messages": [{"role": "user", "content": query}]})
print("\nFinal Answer:\n", _get_last_message_text(res_multi))

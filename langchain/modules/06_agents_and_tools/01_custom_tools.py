"""
MODULE 6 - SCRIPT 1: Defining Custom Tools and Bindings.

This script demonstrates how to define tools using the @tool decorator,
inspect their generated schemas, and check the model's raw tool-calling outputs.
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

# ------------------------------------------------------------------------------
# Step 1: Define Custom Tools
# ------------------------------------------------------------------------------

@tool
def calculate_factorial(n: int) -> int:
    """Calculate the mathematical factorial of a positive integer 'n'.
    
    Args:
        n: The integer value to compute factorial for (e.g., 5).
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    import math
    return math.factorial(n)


@tool
def format_user_email(username: str, domain: str = "zenithtech.com") -> str:
    """Format a corporate email address given a username and optional domain name.
    
    Args:
        username: The employee's short username (e.g., 'jdoe').
        domain: The corporate domain name. Defaults to 'zenithtech.com'.
    """
    return f"{username.strip().lower()}@{domain.strip().lower()}"

# ------------------------------------------------------------------------------
# Step 2: Inspect Tool Schemas
# ------------------------------------------------------------------------------
print("=== INSPECTING TOOL METADATA ===")
print("Tool 1 Name:       ", calculate_factorial.name)
print("Tool 1 Description:", calculate_factorial.description)
print("Tool 1 Arguments:  ", calculate_factorial.args)

print("\nTool 2 Name:       ", format_user_email.name)
print("Tool 2 Description:", format_user_email.description)
print("Tool 2 Arguments:  ", format_user_email.args)
print("================================")

# ------------------------------------------------------------------------------
# Step 3: Bind Tools to the Chat Model
# ------------------------------------------------------------------------------
# We bind the list of tools to the model. This notifies the model about these functions.
# Note: For free tool calling, models like "meta-llama/llama-3-8b-instruct:free" or
# "qwen/qwen-2.5-72b-instruct:free" support tool-calling schemas.
# Let's use Qwen-2.5 72B free as it has robust function-calling performance.
tool_calling_model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    temperature=0.0,
).bind_tools([calculate_factorial, format_user_email])

# ------------------------------------------------------------------------------
# Step 4: Invoke & Check Tool Call Output
# ------------------------------------------------------------------------------
print("\nQuerying model with a request that triggers our tool...")
query = "What is the factorial of 6?"
res = tool_calling_model.invoke(query)

print("\n=== RAW MODEL RESPONSE ===")
print("Response Text Content: ", repr(res.content))
print("Response Tool Calls:   ", res.tool_calls)
print("==========================")

# Let's run a second query triggering the email formatter
print("\nQuerying model to format an email...")
query2 = "Generate a corporate email for username 'kmohnish' using domain 'google.com'."
res2 = tool_calling_model.invoke(query2)

print("\n=== RAW MODEL RESPONSE #2 ===")
print("Response Tool Calls: ", res2.tool_calls)
print("=============================")

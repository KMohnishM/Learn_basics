"""
MODULE 6 EXERCISE: Investment Calculator Agent.

Goal:
Build an autonomous agent with two tools:
1. get_stock_price: Retrieves a mock stock price for AAPL, MSFT, or GOOG.
2. calculate_shares: Divides investment budget by a stock price to return number of shares.

The agent must handle sequential actions: it should look up the stock price first,
then feed that price into the share calculator tool, and present the final answer.

Query: "I want to invest $5000 in MSFT. How many shares can I buy?"
"""

import os
import sys
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

load_dotenv()

# Step 1: Initialize model
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: Please define OPENROUTER_API_KEY in your .env file.")
    sys.exit(1)

model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="qwen/qwen-2.5-72b-instruct:free",
    temperature=0.0,
)

# Step 2: Define Tools
# TODO: Define get_stock_price tool using @tool
# Should accept 'ticker' (str) and return price (float).
# Ticker prices mock: AAPL=180.0, MSFT=400.0, GOOG=150.0. Return 0.0 otherwise.
@tool
def get_stock_price(ticker: str) -> float:
    """Retrieve the current trading price of a stock given its ticker symbol.
    
    Args:
        ticker: The stock ticker uppercase symbol (e.g. 'AAPL', 'MSFT', 'GOOG').
    """
    # TODO: Implement mock lookup
    return 0.0

# TODO: Define calculate_shares tool using @tool
# Should accept 'investment' (float) and 'price' (float) and return shares (float).
@tool
def calculate_shares(investment: float, price: float) -> float:
    """Calculate the number of stock shares that can be purchased for a given budget.
    
    Args:
        investment: Total budget amount in dollars.
        price: Single share price of the target stock.
    """
    # TODO: Implement division (check for division by zero!)
    return 0.0

tools = [get_stock_price, calculate_shares]

# Step 3: Build Prompt Template
# TODO: Define prompt incorporating {input} and MessagesPlaceholder 'intermediate_steps'
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful investment planning helper. Resolve the query using tools."),
    ("human", "{input}"),
    # MessagesPlaceholder(...)
])

# Step 4: Create Agent & Executor
# TODO: Create tool calling agent and initialize AgentExecutor (verbose=True)
agent = None
agent_executor = None

# Step 5: Test Execution
query = "I want to invest $5000 in MSFT. How many shares can I buy?"
print(f"Query: '{query}'\n")

if agent_executor:
    try:
        res = agent_executor.invoke({"input": query})
        print("\n=== AGENT RESPONSE ===")
        print(res.get("output"))
        print("=======================")
    except Exception as e:
        print("Agent execution failed. Error details:", e)
else:
    print("Initialize the TODO blocks to launch the Investment Agent!")
"""

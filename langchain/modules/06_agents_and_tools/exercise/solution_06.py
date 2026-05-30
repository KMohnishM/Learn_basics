"""
MODULE 6 EXERCISE SOLUTION: Investment Calculator Agent.
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
@tool
def get_stock_price(ticker: str) -> float:
    """Retrieve the current trading price of a stock given its ticker symbol.
    
    Args:
        ticker: The stock ticker uppercase symbol (e.g. 'AAPL', 'MSFT', 'GOOG').
    """
    prices = {
        "AAPL": 180.0,
        "MSFT": 400.0,
        "GOOG": 150.0
    }
    return prices.get(ticker.upper(), 0.0)

@tool
def calculate_shares(investment: float, price: float) -> float:
    """Calculate the number of stock shares that can be purchased for a given budget.
    
    Args:
        investment: Total budget amount in dollars.
        price: Single share price of the target stock.
    """
    if price <= 0:
        return 0.0
    return investment / price

tools = [get_stock_price, calculate_shares]

# Step 3: Build Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful investment planning helper. Resolve the query using tools. Be precise."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="intermediate_steps")
])

# Step 4: Create Agent & Executor
agent = create_tool_calling_agent(model, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# Step 5: Test Execution
query = "I want to invest $5000 in MSFT. How many shares can I buy?"
print(f"Query: '{query}'\n")

try:
    res = agent_executor.invoke({"input": query})
    print("\n=== AGENT RESPONSE ===")
    print(res.get("output"))
    print("=======================")
except Exception as e:
    print("Agent execution failed. Error details:", e)

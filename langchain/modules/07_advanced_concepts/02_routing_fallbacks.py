"""
MODULE 7 - SCRIPT 2: Model Fallbacks and Query Routing.

This script demonstrates two production patterns:
1. Fallbacks: Defining an automated backup model when the main API crashes.
2. Dynamic Routing: Selecting downstream chains based on query categorization.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: Please define OPENROUTER_API_KEY in your .env file.")
    sys.exit(1)

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

# ------------------------------------------------------------------------------
# Part 1: Resilient Fallbacks (.with_fallbacks)
# ------------------------------------------------------------------------------
print("=== DEMONSTRATING API FALLBACK PATTERN ===")

# Create a faulty model setup to simulate an API outage (wrong key and bad URL)
faulty_model = ChatOpenAI(
    openai_api_base="https://invalid-api-domain.xxx/v1",
    openai_api_key="bad_token",
    max_retries=1,
)

# Create a valid backup model
backup_model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    temperature=0.3,
)

# Build a resilient model using fallbacks
resilient_model = faulty_model.with_fallbacks([backup_model])

prompt = ChatPromptTemplate.from_template("What is 15 + 27?")
chain = prompt | resilient_model | StrOutputParser()

try:
    print("Running chain. The primary model will fail, triggering the fallback...")
    res = chain.invoke({})
    print("Execution Success!")
    print("Answer: ", res.strip())
except Exception as e:
    print("Failed despite fallback setup. Error:", e)

# ------------------------------------------------------------------------------
# Part 2: Dynamic Query Routing
# ------------------------------------------------------------------------------
print("\n=== DEMONSTRATING DYNAMIC ROUTING PATTERN ===")

# Define specialized chains
code_prompt = ChatPromptTemplate.from_template(
    "You are a Senior Python Developer. Write a concise python solution for: {query}"
)
creative_prompt = ChatPromptTemplate.from_template(
    "You are a creative writer. Write a short, funny 4-line poem about: {query}"
)

code_chain = code_prompt | backup_model | StrOutputParser()
creative_chain = creative_prompt | backup_model | StrOutputParser()

# Define the classification system
classifier_prompt = ChatPromptTemplate.from_template(
    "Classify the following user query into exactly one of these categories: 'CODE' or 'CREATIVE'.\n"
    "Respond with only the category word.\n\n"
    "Query: {query}"
)
classifier_chain = classifier_prompt | backup_model | StrOutputParser()

# Routing selection function
def route_inputs(inputs):
    query = inputs["query"]
    # Classify first
    category = classifier_chain.invoke({"query": query}).strip().upper()
    print(f"[Router Logs] Classification Category: '{category}'")
    
    if "CODE" in category:
        return code_chain.invoke({"query": query})
    else:
        return creative_chain.invoke({"query": query})

# Wrap routing function as RunnableLambda
router_chain = RunnableLambda(route_inputs)

# Test routing for coding query
test_query_1 = "A agent for writing poems"
print(f"\nQuery: '{test_query_1}'")
output_1 = router_chain.invoke({"query": test_query_1})
print("Result:\n", output_1)

# # Test routing for creative query
# test_query_2 = "A programming assistant named Antigravity."
# print(f"\nQuery: '{test_query_2}'")
# output_2 = router_chain.invoke({"query": test_query_2})
# print("Result:\n", output_2)

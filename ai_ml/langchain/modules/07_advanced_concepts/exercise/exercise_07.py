"""
MODULE 7 EXERCISE: Resilient Dynamic Routing Chain.

Goal:
Build a resilient classification and routing pipeline. 
The system should:
1. Classify queries into either 'MATH' or 'GENERAL'.
2. Use a resilient model wrapper (.with_fallbacks) to execute the classifier and final steps.
3. Route queries to either a math solver prompt or a general concept explaining prompt.
"""

import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

load_dotenv()

# Step 1: Initialize models
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: Please define OPENROUTER_API_KEY in your .env file.")
    sys.exit(1)

# Primary model (Faulty setup)
faulty_model = ChatOpenAI(
    openai_api_base="https://non-existent-domain-endpoint.xyz/v1",
    openai_api_key="bad_token",
    max_retries=1,
)

# Backup model
backup_model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="google/gemma-2-9b-it:free",
    temperature=0.0,
)

# TODO: Create a resilient_model using faulty_model.with_fallbacks([backup_model])
resilient_model = None

# Step 2: Define downstream chains
# Use resilient_model for execution!
math_prompt = ChatPromptTemplate.from_template("Solve this math expression step-by-step: {query}")
general_prompt = ChatPromptTemplate.from_template("Provide a short definition of this topic: {query}")

# TODO: Create math_chain and general_chain
math_chain = None
general_chain = None

# Step 3: Define Classifier
classifier_prompt = ChatPromptTemplate.from_template(
    "Classify this query as 'MATH' if it asks for a calculation or equation solver. "
    "Classify as 'GENERAL' for any other questions. Respond with only the category word.\n\n"
    "Query: {query}"
)
# TODO: Create classifier_chain (classifier_prompt | resilient_model | StrOutputParser)
classifier_chain = None

# Step 4: Define Routing Function
# TODO: Complete the routing function to invoke classifier_chain and route inputs
def route_query(inputs: dict) -> str:
    query = inputs["query"]
    # category = classifier_chain.invoke(...)
    category = "GENERAL"
    print(f"[Router Logs] Query category: {category}")
    
    # Route and invoke correct chain
    return ""

router_runnable = RunnableLambda(route_query)

# Step 5: Test queries
math_query = "What is 144 divided by 12?"
general_query = "What is photosynthesis?"

if resilient_model:
    try:
        print(f"Executing math query: '{math_query}'")
        res_math = router_runnable.invoke({"query": math_query})
        print("MATH ANSWER:\n", res_math)
        
        print(f"\nExecuting general query: '{general_query}'")
        res_gen = router_runnable.invoke({"query": general_query})
        print("GENERAL ANSWER:\n", res_gen)
    except Exception as e:
        print("Execution failed. Error details:", e)
else:
    print("Initialize the TODO blocks to setup the Resilient Router!")

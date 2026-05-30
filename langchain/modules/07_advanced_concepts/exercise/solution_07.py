"""
MODULE 7 EXERCISE SOLUTION: Resilient Dynamic Routing Chain.
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

# Create a resilient_model using faulty_model.with_fallbacks([backup_model])
resilient_model = faulty_model.with_fallbacks([backup_model])

# Step 2: Define downstream chains
math_prompt = ChatPromptTemplate.from_template("Solve this math expression step-by-step: {query}")
general_prompt = ChatPromptTemplate.from_template("Provide a short definition of this topic: {query}")

math_chain = math_prompt | resilient_model | StrOutputParser()
general_chain = general_prompt | resilient_model | StrOutputParser()

# Step 3: Define Classifier
classifier_prompt = ChatPromptTemplate.from_template(
    "Classify this query as 'MATH' if it asks for a calculation or equation solver. "
    "Classify as 'GENERAL' for any other questions. Respond with only the category word.\n\n"
    "Query: {query}"
)
classifier_chain = classifier_prompt | resilient_model | StrOutputParser()

# Step 4: Define Routing Function
def route_query(inputs: dict) -> str:
    query = inputs["query"]
    # Classify the query using classifier_chain
    category = classifier_chain.invoke({"query": query}).strip().upper()
    print(f"[Router Logs] Query category: {category}")
    
    # Route to the appropriate chain
    if "MATH" in category:
        return math_chain.invoke({"query": query})
    else:
        return general_chain.invoke({"query": query})

router_runnable = RunnableLambda(route_query)

# Step 5: Test queries
math_query = "What is 144 divided by 12?"
general_query = "What is photosynthesis?"

try:
    print(f"Executing math query: '{math_query}'")
    res_math = router_runnable.invoke({"query": math_query})
    print("MATH ANSWER:\n", res_math)
    
    print(f"\nExecuting general query: '{general_query}'")
    res_gen = router_runnable.invoke({"query": general_query})
    print("GENERAL ANSWER:\n", res_gen)
except Exception as e:
    print("Execution failed. Error details:", e)

"""
MODULE 1 EXERCISE SOLUTION: Basics and API connections.
"""

import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Step 1: Load environment variables
load_dotenv()

# Step 2: Validate API key existence
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: Please define OPENROUTER_API_KEY in your .env file.")
    sys.exit(1)

# Step 3: Initialize the ChatOpenAI client pointing to OpenRouter
model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="google/gemma-2-9b-it:free",
    temperature=0.3,
)

# The paragraph to process
text_to_process = (
    "LangChain is a framework designed to simplify the creation of applications "
    "using large language models. It provides wrapper APIs, integrations, and "
    "structural pipelines to allow developers to build chatbots, search systems, "
    "and autonomous agents with ease."
)

# Step 4: Create messages
messages = [
    SystemMessage(
        content=(
            "You are a helpful translation and summarization assistant. "
            "Your output must consist of two sections:\n"
            "1. TRANSLATION: The input text translated into Spanish.\n"
            "2. SUMMARY: A one-sentence summary of the text in Spanish."
        )
    ),
    HumanMessage(content=text_to_process)
]

# Step 5: Invoke the model
print("Invoking model...")
response = model.invoke(messages)

# Step 6: Print response content and token usage
print("\n=== AI RESPONSE ===")
print(response.content)
print("===================\n")

# Extract token metadata
metadata = response.response_metadata
usage = metadata.get("token_usage", {})
if usage:
    print("=== TOKEN USAGE ===")
    print(f"Prompt Tokens: {usage.get('prompt_tokens')}")
    print(f"Completion Tokens: {usage.get('completion_tokens')}")
    print(f"Total Tokens: {usage.get('total_tokens')}")
    print("===================")
else:
    print("Token usage metadata is unavailable. (Note: Some open-source endpoints do not return usage objects).")

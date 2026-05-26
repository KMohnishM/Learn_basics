"""
MODULE 1 EXERCISE: Basics and API connections.

Goal:
1. Load environment variables.
2. Initialize an OpenRouter ChatOpenAI model using "google/gemma-2-9b-it:free".
3. Write a prompt to translate a paragraph of text into Spanish and write a one-sentence summary of it.
4. Retrieve the response and print BOTH:
   - The generated response content.
   - The token usage details (prompt tokens, completion tokens, and total tokens).

Steps to perform:
- Make sure you copied `.env.example` to `.env` and filled in `OPENROUTER_API_KEY`.
- Run this file and fill in the missing 'TODO' lines of code.
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
# TODO: Initialize ChatOpenAI client.
# Base URL: "https://openrouter.ai/api/v1"
# Model Name: "google/gemma-2-9b-it:free"
# Temperature: 0.3
model = None  # Replace with initialization code

# The paragraph to process
text_to_process = (
    "LangChain is a framework designed to simplify the creation of applications "
    "using large language models. It provides wrapper APIs, integrations, and "
    "structural pipelines to allow developers to build chatbots, search systems, "
    "and autonomous agents with ease."
)

# Step 4: Create a list of messages using SystemMessage and HumanMessage.
# Design the SystemMessage to command the assistant to translate the text to Spanish
# and then add a summary in a separate section.
# TODO: Define system and human messages
messages = [
    # SystemMessage(content="..."),
    # HumanMessage(content="...")
]

# Step 5: Invoke the model
print("Invoking model...")
# TODO: Invoke model with messages list
response = None

# Step 6: Print response content and token usage
# TODO: Extract content and token metadata from response
if response:
    print("\n=== AI RESPONSE ===")
    print(response.content)
    print("===================\n")
    
    # Extract usage info from response.response_metadata
    metadata = response.response_metadata
    # TODO: Print token counts (prompt, completion, total)
else:
    print("Model invocation result is empty. Complete the TODO blocks first!")

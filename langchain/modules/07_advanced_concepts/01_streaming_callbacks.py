"""
MODULE 7 - SCRIPT 1: Async Event Streams (astream_events).

This script demonstrates how to stream tokens and event triggers asynchronously
using the astream_events API.
"""

import asyncio
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

# Initialize model
model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    temperature=0.7,
)

prompt = ChatPromptTemplate.from_template("Explain the concept of '{topic}' in detail.")
chain = prompt | model | StrOutputParser()

async def main():
    topic_query = "quantum computing"
    print(f"Starting async event stream for topic: '{topic_query}'...\n")
    
    # astream_events yields structured events representing everything happening in the chain
    # version='v2' is the standard stable format for events.
    async for event in chain.astream_events({"topic": topic_query}, version="v2"):
        kind = event["event"]
        
        # We can detect when the prompt formatting starts
        if kind == "on_prompt_start":
            print("[Event: Prompt Formatting Started]")
            
        # We can detect when the chat model starts invoking
        elif kind == "on_chat_model_start":
            print(f"[Event: Model Generation Started. Model Name: {event['name']}]")
            print("\n--- STREAMED CONTENT ---")
            
        # We stream individual tokens using on_chat_model_stream
        elif kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                # Print token as it arrives without newline buffering
                sys.stdout.write(content)
                sys.stdout.flush()
                
        # Detect when the model completes generation
        elif kind == "on_chat_model_end":
            print("\n------------------------")
            print("[Event: Model Generation Completed]")
            
        elif kind == "on_chain_end" and event["name"] == "RunnableSequence":
            print("[Event: Complete Chain Execution Finished]")

if __name__ == "__main__":
    # Execute the async loop
    asyncio.run(main())

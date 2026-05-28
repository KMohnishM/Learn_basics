"""
MODULE 2 EXERCISE: Structured Information Extraction.

Goal:
Given a raw product review text, write a Pydantic model and LangChain prompt pipeline
to extract the product details into a validated structure.

Requirements:
1. Define a Pydantic model 'ProductDetails' with:
   - product_name (str)
   - brand (str)
   - price (float, indicating the currency if possible, or just the float value)
   - key_features (list of strings)
   - overall_rating (int out of 10)
2. Use PydanticOutputParser to automatically extract the review text.
3. Print the resulting parsed object fields.
"""

import os
import sys
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()

# Step 1: Initialize model
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: Please define OPENROUTER_API_KEY in your .env file.")
    sys.exit(1)

model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="google/gemma-2-9b-it:free",
    temperature=0.0,
)

# Raw product review text to process
raw_review = (
    "I recently bought the ApexPro Wireless Mouse from Zenith Tech. It cost me exactly $89.99. "
    "The mouse features an ergonomic shell, an incredible 26,000 DPI sensor, and a battery "
    "that easily lasts 80 hours on a single charge. It also supports tri-mode connectivity (Bluetooth, "
    "2.4Ghz wireless, and USB-C). Honestly, it's a solid 9 out of 10 device, only held back by "
    "slightly squeaky mouse clicks and a somewhat bulky charging cable."
)

# Step 2: Define your Pydantic schema
# TODO: Create the class ProductDetails(BaseModel)
class ProductDetails(BaseModel):
    # Pass definitions here
    pass

# Step 3: Set up parser and format instructions
# TODO: Initialize PydanticOutputParser for ProductDetails and get instructions
parser = None
format_instructions = ""

# Step 4: Create prompt template
# TODO: Define chat prompt integrating {format_instructions} and {review}
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert data extractor. Follow instructions carefully.\n{format_instructions}"),
    ("human", "Extract from this review: {review}")
])

# Step 5: Format prompt, invoke model, and parse response
# TODO: Put it all together
print("Processing review...")
try:
    # formatted_msgs = prompt.format_messages(...)
    # raw_res = model.invoke(formatted_msgs)
    # product = parser.parse(raw_res.content)
    product = None
    
    if product:
        print("\n=== EXTRACTION SUCCESS ===")
        # TODO: Print fields of the parsed product object
        # print("Product Name:", product.product_name)
        # ...
    else:
        print("Set up the todo blocks to run extraction!")
except Exception as e:
    print("Extraction failed. Error details:", e)

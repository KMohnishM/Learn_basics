"""
MODULE 2 EXERCISE SOLUTION: Structured Information Extraction.
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
class ProductDetails(BaseModel):
    product_name: str = Field(description="The name of the product")
    brand: str = Field(description="The brand or manufacturer company name")
    price: float = Field(description="Price of the product as a decimal number")
    key_features: List[str] = Field(description="List of core features or specifications")
    overall_rating: int = Field(description="Overall review score out of 10")

# Step 3: Set up parser and format instructions
parser = PydanticOutputParser(pydantic_object=ProductDetails)
format_instructions = parser.get_format_instructions()

# Step 4: Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert data extractor. Follow instructions carefully.\n{format_instructions}"),
    ("human", "Extract from this review: {review}")
])

# Step 5: Format prompt, invoke model, and parse response
print("Processing review...")
try:
    formatted_msgs = prompt.format_messages(
        format_instructions=format_instructions,
        review=raw_review
    )
    raw_res = model.invoke(formatted_msgs)
    product = parser.parse(raw_res.content)
    
    print("\n=== EXTRACTION SUCCESS ===")
    print("Product Name:  ", product.product_name)
    print("Brand:         ", product.brand)
    print("Price:         ", f"${product.price}")
    print("Key Features:  ", product.key_features)
    print("Overall Rating:", f"{product.overall_rating}/10")
    print("===========================\n")
    print("Pydantic Object Instance type:", type(product))
except Exception as e:
    print("Extraction failed. Error details:", e)

"""
MODULE 5 EXERCISE: Corporate FAQ Q&A RAG Pipeline.

Goal:
Build a QA RAG pipeline over SolarCorp's employee handbook documents.
The system should retrieve safety protocols, answer the user's question,
and explicitly cite the source file of the document containing the answer.

Steps:
1. Chunk the provided SolarCorp documents.
2. Embed the text chunks using HuggingFaceEmbeddings (all-MiniLM-L6-v2) and store them in FAISS.
3. Define an LCEL RAG chain that retrieves context, answers the prompt, and enforces source citations.
4. Run a query asking for protocol details when encountering a leakage issue.
"""

import os
import sys
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

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

# SolarCorp raw text documents
solarcorp_docs = [
    Document(
        page_content=(
            "SolarCorp Panel installation instructions: Safety helmets and insulated gloves "
            "must be worn at all times. Panels should never be installed during rainfall or active storms "
            "due to high voltage electrical discharge risks."
        ),
        metadata={"source": "installation_safety.txt"}
    ),
    Document(
        page_content=(
            "SolarCorp Battery leakage protocol: In case of chemical leakage from the backup batteries, "
            "evacuate the immediate area and sound the zone alarm. Ventilate the room using emergency fans "
            "and contact the hazardous response unit at extension 3003."
        ),
        metadata={"source": "hazmat_response.txt"}
    ),
    Document(
        page_content=(
            "SolarCorp Visitor policy: All visitors must register at the reception lobby desk. "
            "They must wear identification badges and be accompanied by a full-time employee at all times "
            "while inside the testing laboratory."
        ),
        metadata={"source": "visitor_guidelines.txt"}
    )
]

# Step 2: Split documents
# TODO: Split solarcorp_docs into chunks using RecursiveCharacterTextSplitter
# Suggestion: chunk_size=150, chunk_overlap=20
splitter = None
chunks = []

# Step 3: Compute embeddings and load into FAISS
# TODO: Initialize HuggingFaceEmbeddings ("sentence-transformers/all-MiniLM-L6-v2")
# and build vectorstore = FAISS.from_documents(...)
embeddings = None
vectorstore = None

# Step 4: Construct LCEL RAG Chain
# TODO: Define retriever (k=1) and prompt template
# Make sure the prompt instructs the model to include the document source filename inside its response.
retriever = None

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a SolarCorp safety officer. Answer the question using the context. "
        "You must explicitly list the source file name (e.g. source: example.txt) where you found the answer.\n\n"
        "=== CONTEXT ===\n{context}"
    )),
    ("human", "{question}")
])

def format_docs(docs):
    return "\n\n".join(f"[{d.metadata.get('source')}]: {d.page_content}" for d in docs)

# TODO: Assemble rag_chain sequence
rag_chain = None

# Step 5: Test the chain
question = "What should employees do if they detect a chemical leak from a backup battery?"
print(f"Query: '{question}'\n")

if rag_chain:
    try:
        answer = rag_chain.invoke(question)
        print("=== SOLARCORP ASSISTANT RESPONSE ===")
        print(answer)
        print("=====================================")
    except Exception as e:
        print("RAG execution failed. Error details:", e)
else:
    print("Initialize the TODO blocks to set up the SolarCorp RAG system!")

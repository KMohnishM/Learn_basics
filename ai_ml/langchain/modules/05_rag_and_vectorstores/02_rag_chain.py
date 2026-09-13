"""
MODULE 5 - SCRIPT 2: Vector Search & LCEL RAG Chain.

This script implements a local vector database using FAISS, embeds texts using HuggingFace
models, and executes a full RAG chain over the document corpus.
"""

import os
import sys
from dotenv import load_dotenv

# Load env before imports
load_dotenv()

# Check key
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("ERROR: Please define OPENROUTER_API_KEY in your .env file.")
    sys.exit(1)

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ------------------------------------------------------------------------------
# Step 1: Create a Document Corpus
# ------------------------------------------------------------------------------
print("Creating documents...")
documents = [
    Document(
        page_content=(
            "The Zenith model Z1 Router features an Admin portal accessed at http://192.168.1.1. "
            "To reset the router login credentials to admin/admin, hold the reset button for 10 seconds."
        ),
        metadata={"source": "router_manual.txt"}
    ),
    Document(
        page_content=(
            "The Apex portal is Zenith Tech's employee system. It is accessed via https://apex.zenithtech.internal. "
            "Multi-factor authentication (MFA) via Duo mobile app is strictly required to log in."
        ),
        metadata={"source": "security_policy.txt"}
    ),
    Document(
        page_content=(
            "Zenith Tech offices are closed on weekends. For critical production incidents, "
            "on-call engineers can be reached via PagerDuty or by dialling extension 9999."
        ),
        metadata={"source": "on_call_roster.txt"}
    )
]

# ------------------------------------------------------------------------------
# Step 2: Slice Documents into Chunks
# ------------------------------------------------------------------------------
splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=20)
chunks = splitter.split_documents(documents)
print(f"Split documents into {len(chunks)} chunks.")

# ------------------------------------------------------------------------------
# Step 3: Embed Chunks & Setup FAISS Vector Store
# ------------------------------------------------------------------------------
print("\nInitializing HuggingFace Embeddings model (running locally)...")
# sentence-transformers/all-MiniLM-L6-v2 is a lightweight model running locally.
# It converts text chunks into 384-dimensional dense vectors.
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

print("Generating vectors and loading into FAISS database...")
vectorstore = FAISS.from_documents(chunks, embeddings)
print("FAISS Index constructed successfully!")

# ------------------------------------------------------------------------------
# Step 4: Verify Search Mechanics
# ------------------------------------------------------------------------------
query = "How do I log into the employee Zenith security system?"
print(f"\n--- Running similarity search for query: '{query}' ---")
matched_docs = vectorstore.similarity_search_with_score(query, k=2)

for doc, score in matched_docs:
    # A lower L2 score indicates higher similarity (more similar vectors)
    print(f"\nMatch Score (L2 Distance): {score:.4f}")
    print(f"Source: {doc.metadata.get('source')}")
    print(f"Content: \"{doc.page_content}\"")

# ------------------------------------------------------------------------------
# Step 5: Construct RAG synthesis chain in LCEL
# ------------------------------------------------------------------------------
print("\nSetting up LCEL RAG synthesis chain...")

# Expose vector store as a Retriever object
# k=1 tells the retriever to return only the single most relevant chunk
retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

# Define the model (OpenRouter Free Gemma 2)
model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key,
    model_name="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    temperature=0.0,
)

# Design QA Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a Zenith Tech corporate assistant. "
        "Answer the user's question using ONLY the provided context blocks. "
        "If you do not know the answer based on the context, state that you cannot find the answer.\n\n"
        "=== CONTEXT ===\n{context}"
    )),
    ("human", "{question}")
])

# Helper function to join retrieved doc contents
def format_docs(docs):
    return "\n\n".join(f"[{d.metadata.get('source')}]: {d.page_content}" for d in docs)

# Compose the RAG chain
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | model
    | StrOutputParser()
)

# ------------------------------------------------------------------------------
# Step 6: Execute RAG Chain
# ------------------------------------------------------------------------------
print("\nExecuting RAG chain query...")
question = "What URL should employees use for the Apex system, and what login security is needed?"
answer = rag_chain.invoke(question)

print("\n--- FINAL RAG RESPONSE ---")
print(answer)
print("--------------------------")

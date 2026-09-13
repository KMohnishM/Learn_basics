"""
MODULE 5 EXERCISE SOLUTION: Corporate FAQ Q&A RAG Pipeline.
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
splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=20)
chunks = splitter.split_documents(solarcorp_docs)

# Step 3: Compute embeddings and load into FAISS
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(chunks, embeddings)

# Step 4: Construct LCEL RAG Chain
retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

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

# Assemble rag_chain sequence
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | model
    | StrOutputParser()
)

# Step 5: Test the chain
question = "What should employees do if they detect a chemical leak from a backup battery?"
print(f"Query: '{question}'\n")

try:
    answer = rag_chain.invoke(question)
    print("=== SOLARCORP ASSISTANT RESPONSE ===")
    print(answer)
    print("=====================================")
except Exception as e:
    print("RAG execution failed. Error details:", e)

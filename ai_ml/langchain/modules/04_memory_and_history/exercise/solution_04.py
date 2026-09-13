"""
MODULE 4 EXERCISE SOLUTION: Conversational CLI with SQLite Persistence.
"""

import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory

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
    temperature=0.7,
)

# Step 2: Establish SQLite Connection Function
DB_URL = "sqlite:///exercise_memory.db"

def get_db_history(session_id: str):
    return SQLChatMessageHistory(session_id=session_id, connection_string=DB_URL)

# Step 3: Create conversational prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful, conversational chatbot helper. Keep answers concise."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

# Step 4: Wrap base chain
base_chain = prompt | model

conversational_chain = RunnableWithMessageHistory(
    base_chain,
    get_db_history,
    input_messages_key="question",
    history_messages_key="chat_history"
)

# Step 5: Implement CLI execution loop
def run_chat_session(session_id: str):
    print(f"--- Chat Session Started (ID: {session_id}) ---")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input or user_input.lower() in ["exit", "quit"]:
                print("\nEnding session. Goodbye!")
                break
                
            # Invoke the chain, passing config for session management
            response = conversational_chain.invoke(
                {"question": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            
            print(f"AI: {response.content}\n")
        except KeyboardInterrupt:
            print("\nEnding session.")
            break

if __name__ == "__main__":
    # We define a fixed session ID. Run it multiple times to verify SQLite persistence!
    TEST_SESSION = "developer_session_1"
    run_chat_session(TEST_SESSION)

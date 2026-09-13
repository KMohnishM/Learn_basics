"""
MODULE 4 EXERCISE: Conversational CLI with SQLite Persistence.

Goal:
Build a persistent command-line chatbot that uses SQLite to store and retrieve
its conversational history.

Steps:
1. Define a database connection string: "sqlite:///exercise_memory.db".
2. Create a session retrieval function get_session_history(session_id) using SQLChatMessageHistory.
3. Build a ChatPromptTemplate incorporating a MessagesPlaceholder named 'chat_history'.
4. Setup a RunnableWithMessageHistory wrapper around the model.
5. Implement a CLI prompt loop that prompts the user for input and queries the chain.
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

# TODO: Complete get_db_history function
def get_db_history(session_id: str):
    # Hint: Return SQLChatMessageHistory(session_id=session_id, connection_string=DB_URL)
    return None

# Step 3: Create conversational prompt template
# TODO: Create a ChatPromptTemplate with a system prompt and a MessagesPlaceholder for 'chat_history'
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful, conversational chatbot helper."),
    # MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

# Step 4: Wrap base chain
base_chain = prompt | model

# TODO: Initialize RunnableWithMessageHistory wrapping base_chain
# Make sure input_messages_key matches the human prompt key and history_messages_key matches MessagesPlaceholder
conversational_chain = None

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
                
            # TODO: Invoke the conversational_chain passing user_input and the configurable session_id
            # response = conversational_chain.invoke(...)
            response = None
            
            if response:
                print(f"AI: {response.content}\n")
            else:
                print("Define the TODO blocks to start chatting!\n")
                break
        except KeyboardInterrupt:
            print("\nEnding session.")
            break

if __name__ == "__main__":
    # We define a fixed session ID for testing persistence
    TEST_SESSION = "developer_session_1"
    run_chat_session(TEST_SESSION)

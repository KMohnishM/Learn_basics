from fastapi import FastAPI
import os
import socket

app = FastAPI()

@app.get("/")
def read_root():
    instance_name = os.getenv("INSTANCE_NAME", "Unknown Backend")
    hostname = socket.gethostname()
    return {
        "message": "Hello from the backend!",
        "instance": instance_name,
        "container_hostname": hostname
    }

# To run without docker for testing: uvicorn app:app --host 0.0.0.0 --port 8000

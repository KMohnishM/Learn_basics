"""
Lab: Vulnerable App — Find and Fix the Security Issues

This FastAPI app has 5 deliberately introduced security vulnerabilities.
Your mission: identify and fix each one.

Run: pip install fastapi uvicorn psycopg2-binary
     uvicorn vulnerable_app:app --reload

The fixes are in solution/fixed_app.py with explanations.
"""

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import subprocess
import sqlite3
import hashlib

app = FastAPI(title="Vulnerable App — Find the Bugs!")

# In-memory SQLite for demo (would be Postgres in production)
conn = sqlite3.connect(":memory:", check_same_thread=False)
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
conn.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin')")
conn.execute("INSERT INTO users VALUES (2, 'alice', 'password1', 'user')")
conn.commit()

# ─────────────────────────────────────────────
# VULNERABILITY 1: SQL Injection
# ─────────────────────────────────────────────

@app.get("/users/search")
def search_users(username: str):
    """
    Search for a user by username.
    
    VULNERABILITY: SQL Injection
    Try: username = "' OR '1'='1" to get ALL users
    Try: username = "'; DROP TABLE users;--" to destroy the database
    """
    query = f"SELECT id, username, role FROM users WHERE username = '{username}'"
    cursor = conn.execute(query)
    return [{"id": r[0], "username": r[1], "role": r[2]} for r in cursor.fetchall()]


# ─────────────────────────────────────────────
# VULNERABILITY 2: Weak Password Hashing
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(req: LoginRequest):
    """
    VULNERABILITY: Passwords hashed with MD5
    MD5 is a general-purpose hash. It's been crackable since the 1990s.
    Tools like hashcat can crack 10 billion MD5 hashes per second.
    """
    hashed = hashlib.md5(req.password.encode()).hexdigest()
    cursor = conn.execute(
        "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
        (req.username, hashed)
    )
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user_id": user[0], "username": user[1]}


# ─────────────────────────────────────────────
# VULNERABILITY 3: Command Injection
# ─────────────────────────────────────────────

@app.get("/network/ping")
def ping(host: str):
    """
    VULNERABILITY: Command Injection via shell=True
    Try: host = "127.0.0.1; whoami" to execute arbitrary commands
    """
    result = subprocess.run(f"ping -c 2 {host}", shell=True, capture_output=True, text=True)
    return {"output": result.stdout, "errors": result.stderr}


# ─────────────────────────────────────────────
# VULNERABILITY 4: IDOR (Insecure Direct Object Reference)
# ─────────────────────────────────────────────

@app.get("/users/{user_id}/data")
def get_user_data(user_id: int, x_user_id: int = Header(default=None)):
    """
    VULNERABILITY: No authorization check!
    User 2 (Alice) can access User 1 (Admin) data by changing user_id in the URL.
    """
    cursor = conn.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user[0], "username": user[1], "role": user[2]}


# ─────────────────────────────────────────────
# VULNERABILITY 5: Information Leakage
# ─────────────────────────────────────────────

@app.get("/debug")
def debug_info():
    """
    VULNERABILITY: Exposes sensitive internal information
    Should NEVER be accessible in production.
    """
    import os
    return {
        "environment_variables": dict(os.environ),   # Exposes ALL env vars (including secrets!)
        "database_url": "sqlite:///production.db",
        "users_table": [dict(zip(["id", "username", "password", "role"], row))
                       for row in conn.execute("SELECT * FROM users").fetchall()],
    }

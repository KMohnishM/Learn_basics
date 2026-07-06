"""
Solution: Fixed Secure App

All 5 vulnerabilities from vulnerable_app.py fixed with explanations.
"""

import re
import subprocess
import sqlite3
import bcrypt
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
import uuid

app = FastAPI(title="Secure App — Fixed Version")
logger = logging.getLogger(__name__)

conn = sqlite3.connect(":memory:", check_same_thread=False)
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT, role TEXT)")

# Store bcrypt hashes instead of plain passwords or MD5
admin_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
alice_hash = bcrypt.hashpw(b"password1", bcrypt.gensalt()).decode()
conn.execute("INSERT INTO users VALUES (1, 'admin', ?, 'admin')", (admin_hash,))
conn.execute("INSERT INTO users VALUES (2, 'alice', ?, 'user')", (alice_hash,))
conn.commit()

# ─────────────────────────────────────────────
# FIX 1: SQL Injection → Parameterized Queries
# ─────────────────────────────────────────────

@app.get("/users/search")
def search_users(username: str):
    """
    FIX: Use parameterized queries. The '?' placeholder ensures username
    is always treated as DATA, never as SQL code.
    """
    cursor = conn.execute(
        "SELECT id, username, role FROM users WHERE username = ?",   # ← Parameterized!
        (username,)
    )
    return [{"id": r[0], "username": r[1], "role": r[2]} for r in cursor.fetchall()]


# ─────────────────────────────────────────────
# FIX 2: MD5 → bcrypt Password Hashing
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(req: LoginRequest):
    """
    FIX: Use bcrypt. It's intentionally slow (~100ms per hash)
    making brute-force attacks infeasible.
    """
    cursor = conn.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()

    if not user or not bcrypt.checkpw(req.password.encode(), user[2].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"user_id": user[0], "username": user[1], "role": user[3]}


# ─────────────────────────────────────────────
# FIX 3: Command Injection → No shell=True, Input Validation
# ─────────────────────────────────────────────

VALID_HOSTNAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9.\-]{0,253}$')

@app.get("/network/ping")
def ping(host: str):
    """
    FIX: 
    1. Validate input against a strict regex.
    2. Pass args as a list (shell=False by default) — no shell interpretation.
    """
    if not VALID_HOSTNAME_RE.match(host):
        raise HTTPException(status_code=400, detail="Invalid hostname")

    result = subprocess.run(
        ["ping", "-c", "2", host],   # List of args, NOT a shell string
        capture_output=True, text=True, timeout=10
    )
    return {"output": result.stdout}


# ─────────────────────────────────────────────
# FIX 4: IDOR → Authorization Check
# ─────────────────────────────────────────────

@app.get("/users/{user_id}/data")
def get_user_data(user_id: int, x_user_id: Optional[int] = Header(default=None)):
    """
    FIX: Check that the requester IS the requested user OR is an admin.
    Without this check, any user could view any other user's data.
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="X-User-ID header required")

    # Get requester's role
    requester = conn.execute("SELECT role FROM users WHERE id = ?", (x_user_id,)).fetchone()
    if not requester:
        raise HTTPException(status_code=401, detail="Invalid user")

    # Only allow: own data OR admin
    if x_user_id != user_id and requester[0] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    user = conn.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user[0], "username": user[1], "role": user[2]}


# ─────────────────────────────────────────────
# FIX 5: Information Leakage → Remove Debug Endpoint
# ─────────────────────────────────────────────

# The /debug endpoint is simply REMOVED. It has no place in production.

# Instead: generic error handler that hides internal details
@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())[:8]
    logger.exception(f"Unhandled error [{error_id}]", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "error_id": error_id}
    )

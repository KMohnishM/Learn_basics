"""
Lab: Complete JWT Auth System with Refresh Token Rotation

Endpoints:
  POST /auth/register    — Create account (hashes password with bcrypt)
  POST /auth/login       — Returns access_token (30min) + refresh_token (7d)
  POST /auth/refresh     — Exchange refresh_token for new token pair
  POST /auth/logout      — Revoke refresh_token
  GET  /me               — Protected route: returns current user
  GET  /admin/users      — Admin-only route (RBAC)

Run:
  pip install fastapi uvicorn python-jose[cryptography] bcrypt pydantic redis
  docker-compose up -d
  uvicorn auth_system:app --reload
"""

import os
import uuid
import bcrypt
import redis
from datetime import datetime, timedelta, UTC
from typing import Annotated, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError

app = FastAPI(title="Auth System Lab")

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-dev-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# In-memory user store (replace with Postgres in production)
USERS_DB: dict[str, dict] = {}

security = HTTPBearer()

# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"   # "user" or "admin"

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# ─────────────────────────────────────────────
# Token Utilities
# ─────────────────────────────────────────────

def create_token(user_id: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "type": token_type,
        "jti": str(uuid.uuid4()),   # JWT ID: unique per token (for revocation)
        "exp": datetime.now(UTC) + expires_delta,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

def is_token_revoked(jti: str) -> bool:
    """Check if token's JTI (JWT ID) has been revoked in Redis."""
    return redis_client.exists(f"revoked:{jti}") == 1

def revoke_token(jti: str, ttl_seconds: int):
    """Mark a token as revoked in Redis with a TTL."""
    redis_client.setex(f"revoked:{jti}", ttl_seconds, "1")

# ─────────────────────────────────────────────
# Auth Dependency
# ─────────────────────────────────────────────

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Not an access token")

    if is_token_revoked(payload["jti"]):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    user = USERS_DB.get(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {**user, "jti": payload["jti"]}

def require_role(required_role: str):
    """Factory for role-based access control dependency."""
    async def checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(status_code=403, detail=f"Requires role: {required_role}")
        return current_user
    return checker

# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.post("/auth/register", status_code=201)
def register(req: RegisterRequest):
    if req.username in USERS_DB:
        raise HTTPException(status_code=409, detail="Username already taken")

    user_id = str(uuid.uuid4())
    hashed_pw = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt(rounds=12)).decode()

    USERS_DB[user_id] = {
        "id": user_id, "username": req.username,
        "password_hash": hashed_pw, "role": req.role
    }
    # Also index by username for lookup
    USERS_DB[req.username] = USERS_DB[user_id]

    return {"message": "Account created", "user_id": user_id}

@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    user = USERS_DB.get(req.username)
    if not user or not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_token(user["id"], user["role"], "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh = create_token(user["id"], user["role"], "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    return TokenResponse(access_token=access, refresh_token=refresh)

@app.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    payload = decode_token(credentials.credentials)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    if is_token_revoked(payload["jti"]):
        raise HTTPException(status_code=401, detail="Refresh token already used or revoked (possible theft!)")

    # TOKEN ROTATION: Invalidate the old refresh token immediately
    revoke_token(payload["jti"], REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    user = USERS_DB.get(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Issue a completely new token pair
    new_access = create_token(user["id"], user["role"], "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    new_refresh = create_token(user["id"], user["role"], "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)

@app.post("/auth/logout")
def logout(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    payload = decode_token(credentials.credentials)
    revoke_token(payload["jti"], ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return {"message": "Logged out successfully"}

@app.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "username": current_user["username"], "role": current_user["role"]}

@app.get("/admin/users")
def list_users(admin: dict = Depends(require_role("admin"))):
    """Admin-only: list all users."""
    return [{"id": u["id"], "username": u["username"], "role": u["role"]}
            for k, u in USERS_DB.items() if k == u.get("id")]

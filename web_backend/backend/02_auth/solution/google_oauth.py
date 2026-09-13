"""
Solution: Google OAuth2 Login

Implements the Authorization Code Flow for Sign in with Google.
"""

import os
import uuid
import httpx
from jose import jwt as jose_jwt
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
import redis

app = FastAPI()
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your-client-id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your-client-secret")
REDIRECT_URI = "http://localhost:8000/auth/google/callback"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")

# In-memory user store (use Postgres in production)
USERS: dict[str, dict] = {}


@app.get("/auth/google")
def google_login():
    """Redirect user to Google's OAuth2 authorization page."""
    state = str(uuid.uuid4())
    # Store state in Redis for 10 minutes (anti-CSRF)
    redis_client.setex(f"oauth_state:{state}", 600, "1")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",   # Request refresh token
        "prompt": "consent",
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{query_string}")


@app.get("/auth/google/callback")
async def google_callback(code: str, state: str):
    """Handle Google's redirect after user grants permission."""
    # 1. Validate state (anti-CSRF)
    state_key = f"oauth_state:{state}"
    if not redis_client.exists(state_key):
        raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
    redis_client.delete(state_key)

    # 2. Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        })

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

    tokens = response.json()
    id_token = tokens["id_token"]

    # 3. Decode the id_token (JWT) to get user info
    # In production, verify the signature against Google's JWKS endpoint
    # For dev, we decode without verification
    user_info = jose_jwt.decode(
        id_token,
        options={"verify_signature": False}
    )
    email = user_info["email"]
    name = user_info.get("name", email)
    google_id = user_info["sub"]

    # 4. Find or create user
    if email not in USERS:
        USERS[email] = {
            "id": str(uuid.uuid4()),
            "email": email,
            "name": name,
            "google_id": google_id,
            "role": "user",
            "auth_provider": "google",
        }

    user = USERS[email]

    # 5. Issue your own JWT tokens
    from datetime import datetime, timedelta, UTC
    access_payload = {
        "sub": user["id"],
        "role": user["role"],
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=30),
    }
    access_token = jose_jwt.encode(access_payload, JWT_SECRET, algorithm="HS256")

    return {
        "message": f"Welcome, {user['name']}!",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": email, "name": name},
    }

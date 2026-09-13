"""
Solution: Complete Auth System Test Suite

Run: pytest solution/test_auth.py -v
"""

import sys
import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Add the auth lab to path
sys.path.insert(0, "../02_auth/labs")
from auth_system import app, USERS_DB, SECRET_KEY, ALGORITHM


@pytest.fixture(autouse=True)
def clear_users():
    USERS_DB.clear()
    yield
    USERS_DB.clear()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def registered_user(client):
    client.post("/auth/register", json={"username": "testuser", "password": "password123", "role": "user"})
    return {"username": "testuser", "password": "password123"}

@pytest.fixture
def registered_admin(client):
    client.post("/auth/register", json={"username": "admin", "password": "adminpass", "role": "admin"})
    return {"username": "admin", "password": "adminpass"}

@pytest.fixture
def user_token(client, registered_user):
    r = client.post("/auth/login", json=registered_user)
    return r.json()["access_token"]

@pytest.fixture
def admin_token(client, registered_admin):
    r = client.post("/auth/login", json=registered_admin)
    return r.json()["access_token"]


# ─────────────────────────────────────────────
# Registration Tests
# ─────────────────────────────────────────────

def test_register_success(client):
    r = client.post("/auth/register", json={"username": "alice", "password": "secure123"})
    assert r.status_code == 201
    assert "user_id" in r.json()

def test_register_duplicate_username(client, registered_user):
    r = client.post("/auth/register", json={"username": "testuser", "password": "other"})
    assert r.status_code == 409

def test_register_password_is_hashed(client):
    client.post("/auth/register", json={"username": "bob", "password": "mypassword"})
    stored = USERS_DB.get("bob")
    assert stored["password_hash"] != "mypassword"
    assert stored["password_hash"].startswith("$2b$")  # bcrypt hash prefix


# ─────────────────────────────────────────────
# Login Tests
# ─────────────────────────────────────────────

def test_login_success(client, registered_user):
    r = client.post("/auth/login", json=registered_user)
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_wrong_password(client, registered_user):
    r = client.post("/auth/login", json={"username": "testuser", "password": "wrong"})
    assert r.status_code == 401

def test_login_nonexistent_user(client):
    r = client.post("/auth/login", json={"username": "nobody", "password": "pass"})
    assert r.status_code == 401

def test_access_token_is_valid_jwt(client, registered_user):
    r = client.post("/auth/login", json=registered_user)
    token = r.json()["access_token"]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "access"
    assert payload["role"] == "user"
    assert "sub" in payload
    assert "exp" in payload


# ─────────────────────────────────────────────
# Protected Route Tests
# ─────────────────────────────────────────────

def test_protected_route_without_token(client):
    r = client.get("/me")
    assert r.status_code in (401, 403)

def test_protected_route_with_valid_token(client, user_token):
    r = client.get("/me", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "testuser"

def test_admin_route_with_user_token(client, user_token):
    r = client.get("/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403

def test_admin_route_with_admin_token(client, admin_token):
    r = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200


# ─────────────────────────────────────────────
# Refresh Token Tests
# ─────────────────────────────────────────────

def test_refresh_token_works(client, registered_user):
    login = client.post("/auth/login", json=registered_user).json()
    refresh_token = login["refresh_token"]

    r = client.post("/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert r.status_code == 200
    new_tokens = r.json()
    assert "access_token" in new_tokens
    assert new_tokens["access_token"] != login["access_token"]  # New token issued

def test_refresh_token_rotation_prevents_reuse(client, registered_user):
    """Using the same refresh token twice should fail (token rotation)."""
    login = client.post("/auth/login", json=registered_user).json()
    refresh_token = login["refresh_token"]

    # First use — succeeds
    r1 = client.post("/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert r1.status_code == 200

    # Second use with the same token — should fail (it was rotated/invalidated)
    r2 = client.post("/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert r2.status_code == 401

# Module 2: Authentication & Authorization at Scale

Authentication (AuthN) and Authorization (AuthZ) are two different things that are constantly confused:
- **Authentication**: "Who are you?" — Verifying identity.
- **Authorization**: "What are you allowed to do?" — Verifying permissions.

A system that authenticates perfectly but authorizes poorly is just as insecure as one that skips authentication altogether.

---

## 1. Password Storage — The Right Way

Most data breaches that expose passwords are catastrophic because passwords were stored incorrectly. The correct approach: **never store the password. Store a hash.**

### Why MD5 and SHA-256 Are Wrong for Passwords

SHA-256 is a general-purpose cryptographic hash. It's designed to be fast — a modern GPU can compute 10 billion SHA-256 hashes per second. An attacker who steals your database can try every word in a dictionary (with variations) in seconds.

### bcrypt — The Standard

bcrypt is intentionally slow. It includes a **work factor** (cost factor) that makes each hash computation take ~100ms. 10 billion attempts/second vs 10 attempts/second changes everything.

bcrypt also automatically generates and stores a **salt** — a random value mixed into the hash. This prevents rainbow table attacks (precomputed hash-to-password tables).

```python
import bcrypt

# Hashing (at registration)
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)  # 2^12 = 4096 iterations
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Verification (at login)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
```

### Argon2 — The Modern Choice

Argon2 won the 2015 Password Hashing Competition. It's better than bcrypt because it also uses memory (making it harder to parallelize on GPUs). Use Argon2 for new systems.

```python
from argon2 import PasswordHasher

ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)
hashed = ph.hash("my_secure_password")
ph.verify(hashed, "my_secure_password")  # True
```

---

## 2. JWT Deep Dive

A **JSON Web Token** is a self-contained, signed token. It doesn't require the server to store session state.

### Structure

A JWT looks like: `header.payload.signature`

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6MTcwMDAwMDAwMH0.signature
```

- **Header** (base64url): `{"alg": "HS256", "typ": "JWT"}`
- **Payload** (base64url): `{"sub": "user_123", "exp": 1700000000, "role": "admin"}`
- **Signature**: `HMAC-SHA256(header + "." + payload, secret_key)`

### How Verification Works

The server receives the token, re-computes the signature using its secret key, and checks it matches the signature in the token. If yes: the payload is untampered and trustworthy.

**Critical**: The payload is only base64-encoded, not encrypted. Never put sensitive data (passwords, SSNs) in a JWT payload — it's readable by anyone who has the token.

### HS256 vs RS256

- **HS256** (HMAC-SHA256): One secret key used for both signing and verification. Simple. All services that verify the token must share the secret key.
- **RS256** (RSA-SHA256): Private key signs the token, public key verifies it. More complex. Allows any service to verify tokens without sharing the secret (just share the public key).

**Use RS256 in microservices** where multiple services need to verify tokens but shouldn't all have the signing key.

### JWT Claims

Standard claims:
- `sub` (subject): User ID
- `exp` (expiry): Token expiration timestamp (always set this!)
- `iat` (issued at): When the token was created
- `iss` (issuer): Who issued the token (e.g., "auth.yourapp.com")
- `aud` (audience): Who the token is intended for (e.g., "api.yourapp.com")

```python
import jwt
from datetime import datetime, timedelta, UTC

SECRET_KEY = "your-secret-key"  # In production: from environment variable
ALGORITHM = "HS256"

def create_access_token(user_id: str, role: str, expires_in_minutes: int = 30) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(minutes=expires_in_minutes),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
```

---

## 3. Access Tokens vs Refresh Tokens

**Access Token**: Short-lived (15-30 minutes). Used for API calls. If stolen, attacker has at most 30 minutes of access.

**Refresh Token**: Long-lived (7-30 days). Stored securely. Used only to get new access tokens. If stolen, attacker can get new access tokens indefinitely — this is the high-value target.

### The Flow

```
1. Login → Server returns: access_token (30min) + refresh_token (7 days)
2. API call → Client sends access_token in Authorization header
3. Access token expires → Client sends refresh_token to /auth/refresh
4. Server validates refresh_token, issues new access_token (+ rotates refresh_token)
5. Logout → Server invalidates the refresh_token (stores it in a "revoked" Redis set)
```

### Token Rotation

Each time a refresh token is used, it's replaced with a new one. The old one is invalidated. This means:
- If an attacker steals a refresh token and uses it, the legitimate user's next refresh attempt will fail (the old token is now invalid).
- The server detects "refresh token reuse" and can flag the account as compromised.

---

## 4. OAuth2 Flows

OAuth2 is an authorization framework that allows a third-party application (e.g., "Login with Google") to act on behalf of a user without ever seeing the user's password.

### Authorization Code Flow (with PKCE) — For Web & Mobile Apps

1. User clicks "Login with Google"
2. App redirects user to Google's authorization server with:
   - `client_id`, `redirect_uri`, `scope`, `state`, `code_challenge` (PKCE)
3. Google shows consent screen, user grants permission
4. Google redirects back to your app with an authorization `code`
5. Your app exchanges the `code` for an access token (server-side, never in browser)
6. App uses access token to call Google APIs on user's behalf

**PKCE** (Proof Key for Code Exchange): Prevents authorization code interception attacks. The app generates a random `code_verifier`, hashes it as `code_challenge`, sends it upfront, and proves ownership when exchanging the code.

### Client Credentials Flow — For Machine-to-Machine

No user involved. Service A authenticates directly as itself to get a token.
- Send `client_id` + `client_secret` → Get access token
- Use access token to call Service B's API

Used for: Cron jobs, microservice communication, CI/CD pipelines.

---

## 5. RBAC vs ABAC

### RBAC (Role-Based Access Control)
Assign users to roles. Roles have permissions.

```
User Alice → Role: "Admin"
Admin Role → Permissions: [read, write, delete]

User Bob → Role: "Viewer"
Viewer Role → Permissions: [read]
```

Simple, easy to reason about, works for most applications. Limitation: can't express "Alice can see all users, but only edit users in her department."

### ABAC (Attribute-Based Access Control)
Access decisions based on arbitrary attributes of the user, resource, and environment.

```
Policy: "Allow access if user.department == resource.department AND time is business_hours"

Alice (department=Engineering) → can access Engineering resources during business hours
Bob (department=Sales) → cannot access Engineering resources
```

Very flexible, but much more complex to implement and reason about. Use ABAC only when RBAC's expressiveness is genuinely insufficient.

---

## Next Steps

Go to `labs/` to build a complete auth system with JWT, refresh tokens, Google OAuth2, and RBAC route protection!

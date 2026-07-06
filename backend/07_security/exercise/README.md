# Exercise: Security Audit Report

## Your Mission

You have access to `labs/vulnerable_app.py`. Your task is to:

1. **Attack** each vulnerability — actually exploit it to prove it's broken.
2. **Fix** each vulnerability in `solution/fixed_app.py`.
3. **Write a security audit report** in `solution/SECURITY_AUDIT.md`.

## The 5 Vulnerabilities

| # | Vulnerability | Endpoint |
|---|---|---|
| 1 | SQL Injection | `GET /users/search?username=...` |
| 2 | Weak Password Hashing (MD5) | `POST /login` |
| 3 | Command Injection | `GET /network/ping?host=...` |
| 4 | IDOR (No Authorization) | `GET /users/{user_id}/data` |
| 5 | Information Leakage | `GET /debug` |

## Attack Instructions

### Vulnerability 1 — SQL Injection
```bash
# Normal query
curl "http://localhost:8000/users/search?username=alice"

# Injection — returns ALL users
curl "http://localhost:8000/users/search?username=' OR '1'='1"
```

### Vulnerability 3 — Command Injection
```bash
# Normal ping
curl "http://localhost:8000/network/ping?host=127.0.0.1"

# Command injection — runs arbitrary commands
curl "http://localhost:8000/network/ping?host=127.0.0.1%3B%20whoami"
# %3B = ; (semicolon), %20 = space
```

## Report Template (SECURITY_AUDIT.md)

For each vulnerability, document:
- **Severity**: Critical / High / Medium / Low
- **Description**: What the vulnerability is and why it's dangerous
- **Proof of Concept**: The exact command/payload that exploits it
- **Fix Applied**: What code change was made to fix it
- **Testing**: How to verify the fix works

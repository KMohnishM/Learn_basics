# Exercise: OAuth2 Google Login

## Background

Your app currently uses username/password auth. The product team wants to add "Sign in with Google" because users hate creating new passwords.

## Concepts to Understand First

OAuth2 Authorization Code Flow with PKCE:
1. User clicks "Sign in with Google"
2. You redirect user to: `https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&scope=openid email profile&code_challenge=...`
3. User logs in at Google and grants permission
4. Google redirects back to `your-app.com/auth/callback?code=abc123`
5. Your server exchanges the `code` for tokens: `POST https://oauth2.googleapis.com/token`
6. Google returns `access_token` and `id_token` (a JWT with user info)
7. You decode the `id_token` to get email, name, and Google's user ID
8. Create or find user in your database, issue your own JWT

## Your Task

Write `solution/google_oauth.py` — a FastAPI app with these endpoints:

### `GET /auth/google`
Generates the Google OAuth2 URL and redirects the user to it. Must include:
- `client_id` (from Google Cloud Console)
- `redirect_uri` = `http://localhost:8000/auth/google/callback`
- `scope` = `openid email profile`
- `response_type` = `code`
- A random `state` parameter (anti-CSRF token, store in session/Redis)

### `GET /auth/google/callback`
Receives the callback from Google with `?code=xxx&state=yyy`.
- Validate the `state` matches what you stored (anti-CSRF check)
- Exchange the code for tokens using `httpx.post(google_token_url, ...)`
- Decode the `id_token` (it's a JWT, decode without verification in dev)
- Look up or create a user in your database with the email
- Issue your own access + refresh token pair
- Return them to the user

### Setup Instructions
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Web application type)
3. Add `http://localhost:8000/auth/google/callback` as an authorized redirect URI
4. Set environment variables: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

# Exercise: Test the Auth System

## Your Task

Write a complete test suite for the `auth_system.py` from Module 2.

Create `solution/test_auth.py` with tests covering:

### Registration Tests
- `test_register_success` — New user registers successfully (201)
- `test_register_duplicate_username` — Registering the same username twice returns 409
- `test_register_password_is_hashed` — The stored password is not the plain text password

### Login Tests
- `test_login_success` — Returns access_token and refresh_token
- `test_login_wrong_password` — Returns 401
- `test_login_nonexistent_user` — Returns 401
- `test_access_token_is_valid_jwt` — The returned token decodes to a valid JWT payload with correct fields

### Protected Route Tests
- `test_protected_route_without_token` — Returns 403 or 401
- `test_protected_route_with_valid_token` — Returns 200 with user info
- `test_admin_route_with_user_token` — Returns 403 (not admin)
- `test_admin_route_with_admin_token` — Returns 200

### Refresh Token Tests
- `test_refresh_token_works` — Old refresh token yields new token pair
- `test_refresh_token_rotation` — Using a refresh token twice fails (the first use invalidates it)

### Fixtures Required
- `client` — TestClient for the auth app
- `registered_user` — A fixture that registers a user and returns their credentials
- `user_token` — A fixture that logs in and returns the access token

This exercise covers everything from Module 2 in one shot. Go deep!

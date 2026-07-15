# Module 6: Testing That Actually Finds Bugs

Most backend testing is theater — it creates the illusion of correctness while leaving the most dangerous bugs untouched. This module covers how to write tests that actually find real bugs and give you genuine confidence to deploy.

---

## 1. The Testing Pyramid

```
          /\
         /  \   E2E Tests
        /    \  (Few, slow, brittle — but prove the whole system works)
       /------\
      /        \ Integration Tests
     /          \ (Some — test components working together with real deps)
    /------------\
   /              \ Unit Tests
  /________________\ (Many, fast, isolated — the foundation)
```

**Unit tests**: Test one function in isolation. All dependencies mocked. Run in milliseconds. Write hundreds.

**Integration tests**: Test how components work together with real dependencies (real database, real Redis). Run in seconds. Write dozens.

**E2E tests**: Test the full user flow through the real system (UI → API → DB → UI). Run in minutes. Write a handful for critical paths only.

A common mistake: writing only unit tests with mocks everywhere and no integration tests. You end up with 100% coverage but bugs that only appear when two components interact.

---

## 2. pytest — The Deep Dive

### Fixtures — Sharing Setup Logic

```python
import pytest
from fastapi.testclient import TestClient
from your_app import app

@pytest.fixture
def client():
    """Create a fresh test client for each test."""
    return TestClient(app)

@pytest.fixture
def authenticated_client(client):
    """A client that is pre-authenticated as an admin user."""
    response = client.post("/auth/login", json={"username": "admin", "password": "secret"})
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client

def test_protected_endpoint(authenticated_client):
    response = authenticated_client.get("/admin/users")
    assert response.status_code == 200
```

### Parametrize — Test Many Cases Without Duplication

```python
@pytest.mark.parametrize("email,expected_valid", [
    ("alice@example.com", True),
    ("bob.smith@company.co.uk", True),
    ("not-an-email", False),
    ("@no-local.com", False),
    ("no-domain@", False),
    ("spaces in@email.com", False),
])
def test_email_validation(email, expected_valid):
    result = validate_email(email)
    assert result == expected_valid, f"Failed for: {email}"
```

One test function, six test cases. Adding edge cases is trivial.

### Marks — Categorize Tests

```python
@pytest.mark.slow
def test_bulk_import():
    ...

@pytest.mark.integration
def test_database_round_trip():
    ...

# Run only fast tests (skip marked as slow)
# pytest -m "not slow"
```

---

## 3. Testing Async Code

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from your_app import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/async-endpoint")
    assert response.status_code == 200
```

Configure `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"   # All async tests run without needing @pytest.mark.asyncio
```

---

## 4. Testcontainers — Real Infrastructure in Tests

Mocking the database in unit tests is fine. But a complex SQL query with joins, indexes, and transactions only reveals its bugs when run against a real database.

Testcontainers starts a real Docker container (Postgres, Redis, etc.) for your tests, and tears it down afterwards.

```python
import pytest
import psycopg2
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    """Start a real Postgres container for the entire test session."""
    with PostgresContainer("postgres:16-alpine") as container:
        yield container

@pytest.fixture
def db_connection(postgres_container):
    """Get a fresh connection to the test database."""
    conn = psycopg2.connect(postgres_container.get_connection_url())
    yield conn
    conn.close()

def test_user_creation(db_connection):
    cur = db_connection.cursor()
    cur.execute("CREATE TABLE users (id SERIAL, name TEXT)")
    cur.execute("INSERT INTO users (name) VALUES ('Alice')")
    db_connection.commit()
    
    cur.execute("SELECT name FROM users WHERE id = 1")
    result = cur.fetchone()
    assert result[0] == "Alice"
```

**Advantage**: Your test SQL runs against the exact same PostgreSQL version as production. If your query has a bug that only appears with real database behavior, Testcontainers will catch it.

---

## 5. Property-Based Testing with Hypothesis

Unit tests with specific inputs test what you thought to test. Hypothesis generates thousands of random inputs to find inputs you didn't think of.

```python
from hypothesis import given, strategies as st

def normalize_price(price: float) -> float:
    """Normalize a price to 2 decimal places, minimum $0.01."""
    return max(0.01, round(price, 2))

@given(st.floats(min_value=-1000, max_value=1000))
def test_normalize_price_invariants(price):
    """Hypothesis will generate thousands of random floats."""
    result = normalize_price(price)
    
    # These properties must ALWAYS hold
    assert result >= 0.01, f"Price should never be below $0.01, got {result}"
    assert result == round(result, 2), f"Price should have at most 2 decimal places"
    
    # Hypothesis will find: what about NaN? Infinity? -0.0?
    # If those break your function, Hypothesis will find it.
```

**Real example of bugs Hypothesis finds**:
- A sorting function that fails on empty lists
- A string parser that crashes on non-ASCII characters
- A function that breaks on `float('nan')` or `float('inf')`
- Edge cases in date arithmetic (February 29th, timezone changes)

---

## 6. Mocking Effectively

### Mock vs MagicMock
```python
from unittest.mock import Mock, MagicMock, patch

# Mock: Basic mock object
# MagicMock: Mock that also supports magic methods (__len__, __iter__, etc.)
```

### `patch` — Replace a Dependency During a Test

```python
from unittest.mock import patch

def test_payment_success(client):
    # Replace the real Stripe call with a mock
    with patch("your_app.services.stripe.charge") as mock_charge:
        mock_charge.return_value = {"id": "ch_test", "status": "succeeded"}
        
        response = client.post("/checkout", json={"amount": 100})
        
        assert response.status_code == 200
        mock_charge.assert_called_once_with(100, "USD")

def test_payment_failure(client):
    with patch("your_app.services.stripe.charge") as mock_charge:
        mock_charge.side_effect = Exception("Card declined")
        
        response = client.post("/checkout", json={"amount": 100})
        
        assert response.status_code == 402
        assert "Card declined" in response.json()["detail"]
```

---

## 7. What Coverage Actually Tells You

```bash
pytest --cov=your_app --cov-report=html
```

**Coverage tells you**: Which lines of code were executed during tests.
**Coverage does NOT tell you**: Whether your tests are correct, whether edge cases are handled, whether integrations work.

100% coverage with wrong assertions = 0% quality confidence.

Use coverage to find **untested code paths** (branches never taken, error handlers never triggered). Don't use it as a quality metric.

---

## Next Steps

Go to `labs/` to build a full test suite with unit tests, Testcontainers integration tests, and a Hypothesis property test that finds a real edge case bug!

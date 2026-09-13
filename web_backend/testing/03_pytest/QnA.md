# Pytest QnA

**Q1: What is a pytest fixture? Explain all 4 fixture scopes and give a concrete use case for each.**
A pytest fixture is a function decorated with `@pytest.fixture` that sets up state, dependencies, or resources needed for tests. Unlike `setup()` methods in xUnit, fixtures are injected explicitly as arguments to test functions.
The four main scopes dictate how often the fixture is executed:
1. `function` (default): Runs once per test function. Use case: Initializing a clean, empty list or a mocked object that must be completely fresh for every test to prevent state bleeding.
2. `class`: Runs once per test class. Use case: Setting up a specific configuration object that is read-only and shared among all methods in a test class, minimizing repetitive setup.
3. `module`: Runs once per `.py` file. Use case: Parsing a large JSON file or establishing a lightweight local resource that takes a second to load but shouldn't be reloaded for every function in the file.
4. `session`: Runs exactly once per test suite execution. Use case: Spinning up a Testcontainers database or establishing a connection to an external testing API. Shared across the entire test run for performance.

**Q2: How does `conftest.py` work? How does pytest discover it across nested directories? Can a test in `tests/unit/` use a fixture defined in `tests/conftest.py`?**
`conftest.py` is a special file used by pytest to share fixtures, hooks, and configuration across multiple test files without needing to explicitly import them.
When pytest runs, it traverses the directory structure. If it finds a `conftest.py` file, it automatically loads its fixtures and makes them available to all tests in that directory and all its subdirectories.
Yes, a test in `tests/unit/test_logic.py` can absolutely use a fixture defined in `tests/conftest.py`. Pytest scoping is hierarchical: a test can see fixtures in its own file, fixtures in a `conftest.py` in its own directory, and fixtures in any `conftest.py` in parent directories all the way up to the project root.
This hierarchical design enables keeping highly specific fixtures close to their tests, while maintaining global fixtures centrally.

**Q3: What is the difference between a `yield` fixture and a `return` fixture? Why is `yield` the correct pattern for resources that need cleanup?**
A `return` fixture simply calculates a value and returns it to the test. Once the `return` statement executes, the fixture is finished; it cannot perform any actions after the test completes.
A `yield` fixture temporarily suspends its execution, handing the yielded value to the test. After the test finishes (whether it passes, fails, or errors), pytest resumes the execution of the fixture right after the `yield` statement.
```python
@pytest.fixture
def db_connection():
    # Setup phase
    conn = create_connection()
    yield conn  # Hand control to the test
    # Teardown phase (Cleanup)
    conn.close()
```
`yield` is the correct pattern for resources needing cleanup (like database connections, file handles, or mock patches) because it guarantees the teardown code will execute, preventing resource leaks and maintaining test isolation, without needing separate `teardown()` hooks.

**Q4: How does `@pytest.mark.parametrize` work with multiple decorators? What is the cartesian product it produces? Show an example.**
`@pytest.mark.parametrize` allows you to run the same test function multiple times with different arguments. When you stack multiple `parametrize` decorators on a single test, pytest generates a cartesian product (every possible combination) of the parameters.
```python
import pytest

@pytest.mark.parametrize("browser", ["chrome", "firefox"])
@pytest.mark.parametrize("user_role", ["admin", "guest", "editor"])
def test_dashboard_access(browser, user_role):
    print(f"Testing {browser} as {user_role}")
    # assertions here
```
In this example, pytest will generate and run 6 distinct tests:
- chrome + admin
- chrome + guest
- chrome + editor
- firefox + admin
- firefox + guest
- firefox + editor
This is an incredibly powerful way to ensure exhaustive test coverage across multiple dimensions of state without writing boilerplate code or manual loops within a test.

**Q5: Explain `mocker.patch` from pytest-mock. What does it auto-clean up? How does it differ from the `unittest.mock.patch` context manager approach?**
`pytest-mock` provides a `mocker` fixture that acts as a thin wrapper around Python's built-in `unittest.mock.patch`.
When you use `mocker.patch('module.function')`, it automatically handles the teardown/unpatching at the end of the test function.
```python
def test_api_call(mocker):
    # Setup patch
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.status_code = 200
    
    # Run test
    assert my_api_func() == True
    # No cleanup needed!
```
This differs from `unittest.mock.patch` context managers (`with patch('...') as mock:`), which force extra indentation levels in your test code. It also differs from using `@patch` decorators, which inject mock arguments into your test signature from the bottom up, often confusing developers when combined with pytest fixtures. `mocker` keeps code flat and readable.

**Q6: How do you assert that a function raises a specific exception with a specific message in pytest? Show `pytest.raises` as both a context manager and a callable.**
Pytest uses `pytest.raises` to catch expected exceptions.
**As a context manager (preferred):**
```python
import pytest

def test_divide_by_zero():
    with pytest.raises(ValueError, match=r"Cannot divide by zero"):
        divide(10, 0)
```
The `match` parameter accepts a regular expression to assert that the exception's error message contains specific text.
**As a callable (useful for simple one-liners):**
```python
def test_type_error():
    pytest.raises(TypeError, divide, "10", "2")
```
The context manager pattern is generally preferred because it allows you to easily inspect the exception object if needed:
```python
with pytest.raises(ValueError) as exc_info:
    divide(10, 0)
assert exc_info.value.code == 500
```
This pattern clearly expresses the intent that the code block within the context is meant to fail.

**Q7: What is `pytest.approx`? Why is direct `==` comparison unreliable for floating-point numbers? What `abs` and `rel` tolerance parameters does it support?**
In Python (and computing in general), floating-point arithmetic is notoriously imprecise. `0.1 + 0.2` results in `0.30000000000000004`. Therefore, `assert 0.1 + 0.2 == 0.3` will fail.
`pytest.approx` solves this by checking for approximate equality within a tolerance limit.
```python
from pytest import approx

def test_float_math():
    assert 0.1 + 0.2 == approx(0.3)
```
By default, it uses a relative tolerance of `1e-6`. You can customize this:
- `rel`: Relative tolerance (e.g., `approx(0.3, rel=1e-3)`) scales the tolerance based on the magnitude of the expected value.
- `abs`: Absolute tolerance (e.g., `approx(0.3, abs=0.01)`) defines a strict +/- boundary regardless of the magnitude.
It also works on lists, dictionaries, and numpy arrays, making it indispensable for data science and math-heavy applications.

**Q8: What is `pytest.mark.xfail`? What is the difference between an `xfail` (unexpected pass = XPASS) and `skip`? What does `strict=True` do?**
`@pytest.mark.xfail` is a decorator used to mark a test that you expect to fail. This is useful when documenting a known bug that hasn't been fixed yet, or when waiting on a dependency.
A `skip` skips the execution of the test entirely. An `xfail` actually runs the test.
If an `xfail` test fails as expected, pytest marks it as an XFAIL (Expected Failure) and does not fail the CI suite.
If an `xfail` test unexpectedly passes, pytest marks it as an XPASS (Unexpected Pass). By default, an XPASS does not fail the suite, but it usually indicates that a bug was fixed or the environment changed, and the `xfail` marker should be removed.
If you set `@pytest.mark.xfail(strict=True)`, an unexpected pass (XPASS) will actually trigger a hard test suite failure, forcing developers to clean up their markers once bugs are resolved.

**Q9: How do you run only the tests that failed in the last run? What other selection flags (`-k`, `--lf`, `-x`, `-m`) are useful during development?**
Pytest tracks the state of previous runs in a `.pytest_cache` directory.
To run only the tests that failed in the last run, use the `--lf` (last failed) flag.
```bash
pytest --lf
```
Other highly useful selection flags during local development:
- `-k "expression"`: Runs tests matching a specific keyword or substring in the function name (e.g., `pytest -k "user and not admin"`).
- `-x` (or `--exitfirst`): Stops the test suite instantly on the very first failure, saving time when debugging massive suites.
- `-m "marker"`: Runs only tests decorated with a specific custom marker (e.g., `@pytest.mark.slow` -> `pytest -m "not slow"`).
These flags vastly improve developer velocity by focusing only on relevant tests.

**Q10: What is `addopts` in `pyproject.toml` pytest configuration? Give 4 useful options and explain what each does.**
`addopts` allows you to define a list of command-line arguments that pytest will automatically append to every run, ensuring consistent execution environments across your team without having to type long commands.
Example `pyproject.toml` configuration:
```toml
[tool.pytest.ini_options]
addopts = "-v --strict-markers --tb=short -p no:warnings"
```
1. `-v` (verbose): Prints the name of every individual test function alongside its PASS/FAIL status, rather than just a single dot `.`.
2. `--strict-markers`: Fails the test suite if a developer uses a custom `@pytest.mark.custom` that hasn't been explicitly registered in the config. Prevents typos like `@pytest.mark.skp`.
3. `--tb=short`: Shortens the traceback output on failure. Instead of printing massive, nested error stacks, it prints a concise summary, making terminal logs easier to read.
4. `-p no:warnings`: Disables the warnings capture plugin, preventing DeprecationWarnings from third-party libraries from cluttering your test output.

**Q11: Explain `AsyncMock` from `unittest.mock`. Why does patching an async function with regular `MagicMock` cause a `TypeError` and how does `AsyncMock` fix it?**
When testing asyncio code, you often need to mock asynchronous coroutines (functions defined with `async def`).
If you patch an async function with a standard `MagicMock`, the mock returns a standard synchronous value. When the production code tries to `await` the mocked function, Python throws a `TypeError: object is not awaitable`.
`AsyncMock` (introduced natively in Python 3.8) solves this. It acts exactly like a `MagicMock`, but when it is called, it returns a coroutine that resolves to the mocked value.
```python
from unittest.mock import AsyncMock
import pytest

@pytest.mark.asyncio
async def test_async_fetch(mocker):
    # Patch with AsyncMock
    mock_fetch = mocker.patch('my_module.fetch_data', new_callable=AsyncMock)
    mock_fetch.return_value = {"status": "ok"}
    
    # Code can safely await the mock
    result = await my_module.process_data()
    assert result == {"status": "ok"}
```
This is essential for modern Python applications utilizing async frameworks like FastAPI.

**Q12: Can a pytest fixture depend on another fixture? Show a 3-level dependency chain (session → module → function scope) and explain how pytest resolves it.**
Yes, fixtures can consume other fixtures by simply declaring them as arguments. Pytest handles the dependency graph and executes them in the correct order based on their scope (widest scope first).
```python
import pytest

@pytest.fixture(scope="session")
def database_engine():
    engine = connect_to_db()
    yield engine
    engine.dispose()

@pytest.fixture(scope="module")
def db_schema(database_engine):
    # Depends on session fixture
    database_engine.create_all_tables()
    yield database_engine
    database_engine.drop_all_tables()

@pytest.fixture(scope="function")
def db_session(db_schema):
    # Depends on module fixture
    session = db_schema.create_session()
    yield session
    session.rollback() # Ensure isolation

def test_user_creation(db_session):
    # Uses the function-scoped fixture
    db_session.add(User("Alice"))
```
Pytest resolves this chain dynamically: before the test runs, it ensures the session engine exists, builds the module schema, and finally spins up the function session.

**Q13: What is the `tmp_path` fixture? Who manages its lifecycle? What is the difference between `tmp_path` and `tmp_path_factory`?**
The `tmp_path` fixture provides a temporary directory unique to the test invocation, returned as a `pathlib.Path` object.
It is completely managed by pytest. Pytest creates it before the test and automatically cleans it up after the test session finishes, keeping only the last few runs for debugging purposes. This removes the need for developers to manually manage `tempfile` contexts and cleanup.
```python
def test_file_writer(tmp_path):
    file = tmp_path / "config.txt"
    write_config(file, {"key": "value"})
    assert file.read_text() == '{"key": "value"}'
```
The difference is scope: `tmp_path` is function-scoped (a new folder per test). `tmp_path_factory` is session-scoped. You use `tmp_path_factory` when you need to download a large artifact or build a temporary database file once for the entire test session and share it across multiple tests.

**Q14: What is a pytest plugin? Name 3 widely used pytest plugins and what hook each uses (`pytest_runtest_setup`, `pytest_collection_modifyitems`, etc.).**
Pytest has a powerful hook architecture allowing plugins to intercept and modify almost any part of the test lifecycle (collection, setup, execution, reporting).
1. **pytest-xdist**: Allows running tests in parallel across multiple CPU cores. It hooks into test scheduling to distribute tasks to worker processes via custom hooks like `pytest_xdist_setupnodes`.
2. **pytest-cov**: Integrates Coverage.py to generate test coverage reports. It uses hooks like `pytest_sessionfinish` to aggregate coverage data and print the report after all tests execute.
3. **pytest-ordering**: Allows developers to force tests to run in a specific order (e.g., `@pytest.mark.run(order=1)`). It relies heavily on the `pytest_collection_modifyitems` hook, intercepting the collected list of test items and sorting them before execution begins.
These plugins demonstrate how extensible the Pytest ecosystem is.

**Q15: How do you structure pytest tests for a FastAPI application? Compare `TestClient` (synchronous ASGI transport) vs `AsyncClient` from `httpx`. When does each apply?**
When testing FastAPI, you typically use `fastapi.testclient.TestClient`. It wraps your ASGI application and routes HTTP requests synchronously directly to the framework without opening an actual network port.
```python
from fastapi.testclient import TestClient
from myapp import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
```
This is perfect for most APIs. However, `TestClient` is synchronous. If your test itself needs to execute asynchronous code concurrently, or if you are specifically testing highly concurrent WebSocket behavior, you use `httpx.AsyncClient`.
```python
import pytest
from httpx import AsyncClient
from myapp import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
```
`TestClient` is generally faster and easier to set up for standard REST API tests, while `AsyncClient` is necessary for purely async test environments or complex integration scenarios involving async dependencies.

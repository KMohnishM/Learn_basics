# Module 3: Advanced Pytest Masterclass

This module provides an exhaustive, in-depth exploration of pytest, the most powerful and widely adopted testing framework in the Python ecosystem. By the end of this module, you will have a deep understanding of pytest's architecture, its fixture system, parametrization, mocking strategies, and async testing capabilities.

## 1. Pytest Setup and Configuration

Pytest is highly configurable. While it works out of the box with zero configuration, enterprise projects require strict configuration to ensure consistency, reproducibility, and optimal performance across different environments.

### Installation

To install pytest, along with its most common plugins for mocking, coverage, and async testing, you should define your dependencies in your project's dependency management system.

```bash
pip install pytest pytest-mock pytest-asyncio pytest-cov
```

In modern Python projects, you should use `pyproject.toml` for configuration. This file replaces legacy configuration files like `setup.cfg`, `tox.ini`, and `pytest.ini`.

### Configuring via pyproject.toml

The `pyproject.toml` file allows you to set default command-line options, define custom markers, set minimum pytest versions, and configure test discovery.

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --tb=short"
testpaths = [
    "tests",
    "integration",
]
python_files = [
    "test_*.py",
    "*_test.py",
]
python_classes = [
    "Test*",
    "*Suite",
]
python_functions = [
    "test_*",
    "check_*",
]

markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests that require external services",
    "api: marks tests that test the REST API",
    "db: tests that require database access",
]

filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
    "ignore::UserWarning",
]
```

#### Explanation of Configuration Options

- `minversion`: Ensures that all developers and CI pipelines are using a compatible version of pytest. If an older version is used, pytest will refuse to run.
- `addopts`: These are arguments that are always appended to the pytest command. 
  - `-ra` shows a summary of all tests except passed tests at the end of the run.
  - `-q` runs in quiet mode, reducing terminal noise.
  - `--strict-markers` ensures that any marker used in the code must be registered in the `markers` section. This prevents typos in marker names.
  - `--tb=short` formats the traceback to be shorter and more readable.
- `testpaths`: Specifies the directories pytest should search for tests. This speeds up test discovery since pytest won't scan the entire repository.
- `python_files`, `python_classes`, `python_functions`: Customizes the naming conventions for test discovery. By default, pytest looks for `test_*.py` and `*_test.py` files.
- `markers`: Registers custom markers. This is crucial for test categorization and selection.
- `filterwarnings`: Controls how Python warnings are handled during test runs. Setting "error" turns warnings into failures, which is excellent for catching deprecation issues early.

## 2. Writing Tests and Assertions

Unlike Python's built-in `unittest` module, which requires you to subclass `unittest.TestCase` and use specific assertion methods (e.g., `assertEqual`, `assertTrue`), pytest leverages Python's native `assert` statement. Pytest uses advanced Abstract Syntax Tree (AST) manipulation to introspect asserts and provide incredibly detailed failure messages.

### Basic Assertions

```python
def add(a: int, b: int) -> int:
    return a + b

def test_add_positive_numbers():
    result = add(2, 3)
    assert result == 5

def test_add_negative_numbers():
    result = add(-2, -3)
    assert result == -5

def test_add_mixed_numbers():
    result = add(-2, 5)
    assert result == 3
```

When an assertion fails, pytest breaks down the expression.

```python
def test_failing_example():
    expected = {"status": "ok", "count": 5, "items": ["apple", "banana"]}
    actual = {"status": "ok", "count": 4, "items": ["apple", "orange"]}
    
    # pytest will show exactly which keys and list items differ
    assert expected == actual
```

### Testing Exceptions with pytest.raises

When you expect a function to raise an exception, use the `pytest.raises` context manager. You can also verify the exception's message using the `match` parameter, which accepts a regular expression.

```python
import pytest

def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)

def test_divide_by_zero_advanced():
    # You can also capture the exception object for more detailed assertions
    with pytest.raises(ValueError) as exc_info:
        divide(10, 0)
    
    assert str(exc_info.value) == "Cannot divide by zero"
    assert exc_info.type is ValueError
```

### Floating Point Comparisons with pytest.approx

Comparing floating-point numbers directly using `==` is dangerous due to precision issues in binary floating-point arithmetic (e.g., `0.1 + 0.2` is `0.30000000000000004`). Pytest provides the `approx` function to handle this gracefully.

```python
import pytest

def calculate_tax(amount: float, rate: float) -> float:
    return amount * rate

def test_calculate_tax():
    result = calculate_tax(0.1, 3.0)
    
    # This would fail: assert result == 0.3
    # This passes:
    assert result == pytest.approx(0.3)

def test_approx_with_dictionaries():
    expected = {"price": 10.0, "tax": 0.3}
    actual = {"price": 10.000001, "tax": 0.30000004}
    
    assert actual == pytest.approx(expected, rel=1e-3)
```

The `approx` function supports `rel` (relative tolerance) and `abs` (absolute tolerance) arguments to fine-tune the comparison.

## 3. Fixtures and Dependency Injection

Fixtures are the core of pytest. They provide a powerful mechanism for managing state, setting up dependencies, and injecting data into your tests. Unlike the `setUp` and `tearDown` methods in `unittest`, fixtures are explicit, modular, reusable, and composable.

### Basic Fixtures

A fixture is defined using the `@pytest.fixture` decorator. Tests request the fixture by including its name as an argument.

```python
import pytest

class DatabaseConnection:
    def __init__(self):
        self.connected = True
    
    def fetch_data(self):
        return ["data1", "data2"]

@pytest.fixture
def db():
    """Provides a database connection."""
    connection = DatabaseConnection()
    return connection

def test_database_fetch(db):
    """The 'db' fixture is automatically injected by pytest."""
    data = db.fetch_data()
    assert len(data) == 2
    assert db.connected is True
```

### Fixture Scopes

By default, a fixture is invoked once per test function (scope="function"). However, for expensive operations (like starting a database or a browser), you can change the scope to cache the fixture instance.

Available scopes:
- `function`: (default) Invoked once per test.
- `class`: Invoked once per test class.
- `module`: Invoked once per module (file).
- `package`: Invoked once per package (directory containing `__init__.py`).
- `session`: Invoked once per test session (the entire pytest run).

```python
@pytest.fixture(scope="session")
def expensive_db_connection():
    print("\n[SETUP] Starting expensive database...")
    db = DatabaseConnection()
    yield db
    print("\n[TEARDOWN] Closing expensive database...")
```

### Teardown with the yield Statement

To perform cleanup after a test finishes (regardless of whether the test passed, failed, or raised an exception), use the `yield` statement instead of `return` in your fixture. Code before `yield` is the setup phase; code after `yield` is the teardown phase.

```python
import os
import tempfile
import pytest

@pytest.fixture
def temporary_file():
    # Setup: Create a temporary file
    fd, path = tempfile.mkstemp()
    
    # Provide the path to the test
    yield path
    
    # Teardown: Remove the temporary file
    os.close(fd)
    if os.path.exists(path):
        os.remove(path)

def test_file_writing(temporary_file):
    with open(temporary_file, "w") as f:
        f.write("Hello, World!")
    
    with open(temporary_file, "r") as f:
        assert f.read() == "Hello, World!"
```

### The conftest.py File

If you have multiple test files that need to share the same fixtures, you can define them in a `conftest.py` file. Pytest automatically discovers fixtures defined in `conftest.py` and makes them available to all test files in the same directory and its subdirectories. You do NOT need to import `conftest.py`.

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def global_config():
    return {"api_key": "secret123", "timeout": 30}

@pytest.fixture
def api_client(global_config):
    """Fixtures can request other fixtures!"""
    class APIClient:
        def __init__(self, key):
            self.key = key
    return APIClient(global_config["api_key"])
```

## 4. Parametrize: Data-Driven Testing

When you need to test the same logic with multiple sets of inputs and expected outputs, use `@pytest.mark.parametrize`. This prevents code duplication and treats each parameter set as an independent test case. If one parameter set fails, pytest will still execute the remaining sets.

### Basic Parametrization

```python
import pytest

def is_even(n: int) -> bool:
    return n % 2 == 0

@pytest.mark.parametrize("number, expected", [
    (2, True),
    (4, True),
    (3, False),
    (0, True),
    (-2, True),
    (-5, False),
])
def test_is_even(number, expected):
    assert is_even(number) == expected
```

### Generating Cartesian Products

If you stack multiple `@pytest.mark.parametrize` decorators, pytest will generate all possible combinations (the Cartesian product) of the parameters.

```python
import pytest

@pytest.mark.parametrize("browser", ["chrome", "firefox", "safari"])
@pytest.mark.parametrize("os", ["windows", "linux", "macos"])
def test_cross_browser_compatibility(browser, os):
    # This test will run 3 x 3 = 9 times
    # (chrome, windows), (chrome, linux), (chrome, macos), etc.
    print(f"Testing on {browser} under {os}")
    assert True
```

### Using pytest.param for Granular Control

You can use `pytest.param` to add specific markers or custom IDs to individual parameter sets.

```python
import pytest

@pytest.mark.parametrize("input_val, expected", [
    (1, 2),
    pytest.param(2, 4, id="double_two"),
    pytest.param(3, 6, marks=pytest.mark.slow, id="slow_test_for_three"),
    pytest.param(4, 0, marks=pytest.mark.xfail(reason="Bug #123"), id="failing_case"),
])
def test_doubling(input_val, expected):
    assert input_val * 2 == expected
```

## 5. Mocking with pytest-mock

While Python's standard `unittest.mock` is powerful, the `pytest-mock` plugin provides a convenient `mocker` fixture that wraps `unittest.mock.patch` and automatically handles teardown. This makes tests cleaner and less error-prone.

### Using the mocker Fixture

```python
import requests

def get_user_data(user_id: int) -> dict:
    response = requests.get(f"https://api.example.com/users/{user_id}")
    response.raise_for_status()
    return response.json()

def test_get_user_data(mocker):
    # Mock the requests.get function
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"id": 1, "name": "Alice"}
    mock_get = mocker.patch("requests.get", return_value=mock_response)
    
    result = get_user_data(1)
    
    assert result == {"id": 1, "name": "Alice"}
    mock_get.assert_called_once_with("https://api.example.com/users/1")
```

### Mocking Return Values and Side Effects

You can configure a mock to return different values on consecutive calls, or to raise exceptions.

```python
def test_mock_side_effects(mocker):
    # Mock to raise an exception
    mocker.patch("requests.get", side_effect=requests.exceptions.ConnectionError)
    
    with pytest.raises(requests.exceptions.ConnectionError):
        get_user_data(2)

def test_mock_multiple_returns(mocker):
    # Mock to return different values on subsequent calls
    mock_func = mocker.Mock(side_effect=[1, 2, 3])
    
    assert mock_func() == 1
    assert mock_func() == 2
    assert mock_func() == 3
    with pytest.raises(StopIteration):
        mock_func()
```

### Spying on Functions

Sometimes you want to observe a function's behavior (arguments passed, return value) without overriding its actual implementation. Use `mocker.spy` for this.

```python
import math

def calculate_hypotenuse(a, b):
    return math.sqrt(a**2 + b**2)

def test_spy_math_sqrt(mocker):
    spy = mocker.spy(math, "sqrt")
    
    result = calculate_hypotenuse(3, 4)
    
    assert result == 5.0
    spy.assert_called_once_with(25)
```

## 6. Markers and Test Selection

Markers are used to categorize tests, allowing you to selectively run specific subsets of your test suite. Pytest provides several built-in markers (`skip`, `skipif`, `xfail`), and you can define your own.

### Custom Markers

First, declare your custom markers in `pyproject.toml` (as shown in Section 1). Then apply them to your tests:

```python
import pytest

@pytest.mark.db
def test_database_insert():
    pass

@pytest.mark.api
@pytest.mark.slow
def test_api_integration():
    pass
```

To run tests with a specific marker:
```bash
pytest -m "db"
```

To run tests matching a logical expression:
```bash
pytest -m "api and not slow"
```

### Built-in Markers: skip, skipif, and xfail

- `skip`: Unconditionally skips a test.
- `skipif`: Skips a test based on a condition (e.g., checking the operating system or python version).
- `xfail`: Marks a test as expected to fail. If it fails, pytest reports it as an expected failure (xfailed) rather than a hard failure. If it unexpectedly passes, it's reported as xpassed.

```python
import sys
import pytest

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.platform == "win32", reason="Does not run on Windows")
def test_linux_specific_behavior():
    pass

@pytest.mark.xfail(reason="Known bug in the third-party library API")
def test_flaky_third_party_service():
    assert 1 == 2
```

## 7. Testing Async Code

Testing asynchronous code (coroutines using `async` and `await`) requires the `pytest-asyncio` plugin. Pytest cannot run async functions natively because they require an event loop.

### Basic Async Testing

Simply decorate your async test function with `@pytest.mark.asyncio`.

```python
import asyncio
import pytest

async def fetch_data_async():
    await asyncio.sleep(0.1)
    return {"data": "success"}

@pytest.mark.asyncio
async def test_fetch_data_async():
    result = await fetch_data_async()
    assert result == {"data": "success"}
```

### Async Fixtures

You can also define asynchronous fixtures. The `pytest-asyncio` plugin will handle running them in the event loop.

```python
import pytest
import asyncio

@pytest.fixture
async def async_db_connection():
    print("Connecting to async db...")
    await asyncio.sleep(0.1)
    yield "async_connection_object"
    print("Disconnecting from async db...")
    await asyncio.sleep(0.1)

@pytest.mark.asyncio
async def test_with_async_fixture(async_db_connection):
    assert async_db_connection == "async_connection_object"
    await asyncio.sleep(0.1)
```

### Mocking Async Functions with AsyncMock

When mocking asynchronous functions, you must use `AsyncMock` (which is available in `unittest.mock` starting from Python 3.8, and can be used via the `mocker` fixture).

```python
import pytest

class AsyncService:
    async def get_value(self):
        return 42

async def process_service_value(service: AsyncService):
    val = await service.get_value()
    return val * 2

@pytest.mark.asyncio
async def test_process_service_value(mocker):
    # Note: we use AsyncMock for async functions
    mock_service = mocker.Mock(spec=AsyncService)
    mock_service.get_value = mocker.AsyncMock(return_value=10)
    
    result = await process_service_value(mock_service)
    
    assert result == 20
    mock_service.get_value.assert_awaited_once()
```

## 8. Code Coverage

Code coverage measures the percentage of your source code that is executed when the test suite runs. High coverage does not guarantee bug-free code, but low coverage guarantees unverified code. We use the `pytest-cov` plugin, which integrates the `coverage.py` tool.

### Running Tests with Coverage

To generate a coverage report for a specific package (e.g., `my_app`):

```bash
pytest --cov=my_app
```

To generate a detailed terminal report showing exactly which lines were missed:

```bash
pytest --cov=my_app --cov-report=term-missing
```

To generate an HTML report (which creates an interactive `htmlcov/index.html` file):

```bash
pytest --cov=my_app --cov-report=html
```

### Configuring Coverage with .coveragerc

For granular control over coverage measurement, create a `.coveragerc` file. This allows you to exclude specific files, directories, or lines of code from the coverage calculation.

```ini
# .coveragerc

[run]
# Specify the directories to measure
source = my_app
# Exclude test files and migration scripts from coverage metrics
omit =
    tests/*
    my_app/migrations/*
    venv/*
    setup.py

[report]
# Do not report files that are 100% covered
skip_covered = True
# Treat coverage below 85% as a failure
fail_under = 85
# Exclude specific code patterns from coverage requirements
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
```

With `fail_under = 85`, the `pytest` command will return a non-zero exit code if the overall coverage falls below 85%, which is useful for enforcing coverage thresholds in Continuous Integration (CI) pipelines.

## Advanced Topics and Best Practices

### The tmp_path Fixture

Pytest provides a built-in `tmp_path` fixture (which returns a `pathlib.Path` object) for creating temporary directories unique to each test invocation. Pytest automatically manages the cleanup of these directories.

```python
def test_create_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("pytest is awesome")
    
    assert p.read_text() == "pytest is awesome"
    assert len(list(tmp_path.iterdir())) == 1
```

### Monkeypatching

The built-in `monkeypatch` fixture allows you to safely modify environment variables, dictionaries, and object attributes for the duration of a single test. The modifications are automatically reverted during teardown.

```python
import os

def get_database_url():
    return os.environ.get("DATABASE_URL", "sqlite:///:memory:")

def test_get_database_url_custom(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")
    assert get_database_url() == "postgres://user:pass@localhost/db"

def test_get_database_url_default(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert get_database_url() == "sqlite:///:memory:"
```

### Structuring Your Test Suite

A well-structured test suite separates different types of tests and leverages `conftest.py` effectively.

```text
my_project/
├── my_app/              # Application source code
├── pyproject.toml       # Pytest configuration
├── .coveragerc          # Coverage configuration
└── tests/
    ├── conftest.py      # Global fixtures (e.g., db connection, API clients)
    ├── unit/
    │   ├── conftest.py  # Unit test specific fixtures (e.g., basic mocks)
    │   ├── test_models.py
    │   └── test_utils.py
    ├── integration/
    │   ├── conftest.py  # Integration specific fixtures (e.g., test databases)
    │   └── test_api.py
    └── e2e/
        └── test_workflows.py
```

By placing `conftest.py` files in subdirectories, you restrict the availability of fixtures to only the tests that need them, preventing naming collisions and reducing cognitive load.

### Custom Fixtures and the request Object

Sometimes fixtures need access to the test context itself. Pytest provides the built-in `request` fixture precisely for this purpose.

```python
import pytest

@pytest.fixture
def test_logger(request):
    """A fixture that knows which test called it."""
    test_name = request.node.name
    print(f"\\n[LOG] Starting test: {test_name}")
    yield
    print(f"\\n[LOG] Finished test: {test_name}")

def test_example_with_logger(test_logger):
    assert True
```

### Parametrizing Fixtures

In addition to parametrizing tests directly, you can parametrize fixtures using the `params` argument. The `request` fixture is used to access the current parameter.

```python
import pytest

@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def db_backend(request):
    """This fixture will run the test 3 times, once for each backend."""
    backend = request.param
    yield f"connection_to_{backend}"

def test_database_operation(db_backend):
    assert db_backend.startswith("connection_to_")
```

### Pytest Hooks

Pytest allows you to customize its behavior heavily via hooks. You can define these in `conftest.py`.

```python
# conftest.py
def pytest_collection_modifyitems(config, items):
    """
    Hook to modify the list of collected test items.
    For example, automatically add the 'slow' marker to tests that mention 'sleep'.
    """
    for item in items:
        if "sleep" in item.name:
            item.add_marker(pytest.mark.slow)
```

### Conclusion

Pytest's architecture, based on fixtures, parametrization, and native assert introspection, makes it an indispensable tool for Python developers. Mastering these features allows you to write test suites that are robust, maintainable, and expressive, significantly reducing the maintenance burden of large software projects.

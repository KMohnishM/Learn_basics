# Pytest Cheatsheet

## Pytest CLI Commands
```bash
pytest                      # Run all tests in the current directory and subdirectories
pytest tests/test_api.py    # Run tests in a specific file
pytest tests/test_api.py::test_auth  # Run a specific test function
pytest -k "auth or token"   # Run tests matching a keyword expression
pytest -m "slow"            # Run tests with a specific marker
pytest -x                   # Stop after the first failure (fail fast)
pytest --maxfail=3          # Stop after 3 failures
pytest --lf                 # Run only the tests that failed in the last run (last failed)
pytest --ff                 # Run all tests, but run the previously failed ones first (failed first)
pytest -v                   # Verbose output (shows each test name)
pytest -q                   # Quiet output (minimal text)
pytest -s                   # Disable standard output capturing (allows print() statements to show)
pytest --tb=short           # Shorter traceback format (options: auto, long, short, line, native, no)
```

## Fixture Scope Table
| Scope | Instantiation | Best For |
|---|---|---|
| `function` (default) | Once per test function | Test-specific data, isolated state, temporary files (`tmp_path`) |
| `class` | Once per test class | Setting up state shared by all methods in a test class |
| `module` | Once per module (`.py` file) | Expensive setups shared by tests in the same file (e.g., compiling a large regex) |
| `package` | Once per package (`__init__.py`) | Shared resources across a specific directory of tests |
| `session` | Once per test run (entire suite) | Database connections, Docker containers, external service initialization |

## Assertion Forms
```python
# Basic equality
assert a == b
assert a != b

# Identity
assert a is b
assert a is not None

# Membership
assert item in my_list
assert key in my_dict

# Truthiness
assert is_valid
assert not is_error

# Exceptions
with pytest.raises(ValueError, match="Invalid ID"):
    process_id(-1)

# Floating point approximations
assert 0.1 + 0.2 == pytest.approx(0.3)
assert actual_dict == pytest.approx(expected_dict, rel=1e-3)
```

## Markers Reference
```python
# Skipping tests
@pytest.mark.skip(reason="Not supported")
@pytest.mark.skipif(sys.platform == "win32", reason="Linux only")

# Expected failures
@pytest.mark.xfail(reason="Bug #1234")

# Parametrization
@pytest.mark.parametrize("input,expected", [(1, 2), (2, 4)])

# Async (requires pytest-asyncio)
@pytest.mark.asyncio
async def test_something(): ...

# Custom Markers (Must be registered in pyproject.toml)
@pytest.mark.slow
@pytest.mark.db
@pytest.mark.integration
```

## conftest.py Discovery
- `conftest.py` is automatically discovered by pytest. Do NOT import it.
- Fixtures defined in a `conftest.py` are available to all test files in that directory and all subdirectories.
- A project can have multiple `conftest.py` files (e.g., `tests/conftest.py` for global fixtures, `tests/api/conftest.py` for API-specific fixtures).

## Coverage Commands (requires pytest-cov)
```bash
pytest --cov=my_package                 # Run coverage on a specific package
pytest --cov=my_package --cov-report=term-missing # Show missing line numbers in terminal
pytest --cov=my_package --cov-report=html         # Generate interactive HTML report (htmlcov/index.html)
pytest --cov=my_package --cov-fail-under=80       # Fail the test suite if coverage is below 80%
```

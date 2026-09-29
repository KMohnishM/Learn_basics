# CHEATSHEET: Python Production Tooling

## Architecture ASCII Diagram: The Modern Build Pipeline

```text
+-------------------+      +-----------------+      +-----------------+
|   Developer / CI  |      |  Build Frontend |      |  Build Backend  |
+-------------------+      +-----------------+      +-----------------+
          |                         |                        |
          |  uv build / pip build   |                        |
          |------------------------>|                        |
          |                         | Reads pyproject.toml   |
          |                         | Resolves [build-system]|
          |                         |                        |
          |                         | Creates Isolated Env   |
          |                         | Installs backend       |
          |                         |                        |
          |                         |  build_wheel() hook    |
          |                         |----------------------->|
          |                         |                        | Reads [project]
          |                         |                        | Compiles Ext.
          |                         |                        | Generates metadata
          |                         |      Returns .whl      |
          |                         |<-----------------------|
          |      Receives .whl      |                        |
          |<------------------------|                        |
          |                         |                        |
```

## Dense Command Reference: uv & ruff

| Tool | Command | Description |
| :--- | :--- | :--- |
| **uv** | `uv init <name>` | Initialize a new project with standard structure and pyproject.toml. |
| **uv** | `uv add <pkg>` | Add dependency to pyproject.toml and update uv.lock. |
| **uv** | `uv add --dev <pkg>`| Add a development-only dependency. |
| **uv** | `uv sync --locked` | Strictly sync the virtual environment to exact lockfile state. |
| **uv** | `uv run <script>` | Run a script within the isolated virtual environment. |
| **uv** | `uv pip install -r` | Install dependencies from a requirements/lockfile into env. |
| **uv** | `uv venv` | Create an extremely fast virtual environment. |
| **ruff**| `ruff check .` | Run linter over the entire repository. |
| **ruff**| `ruff check --fix .`| Run linter and automatically fix safe, auto-fixable violations. |
| **ruff**| `ruff format .` | Run the formatter to adhere to strict stylistic guidelines. |
| **ruff**| `ruff rule <rule>` | Display detailed documentation and examples for a specific rule. |

## Pytest Fixture Scopes & Execution ASCII Flow

```text
[SESSION START]
  |-- Session Fixture Setup (Runs exactly once)
  |
  |-- [PACKAGE START]
  |     |-- Package Fixture Setup
  |     |
  |     |-- [MODULE START (test_file.py)]
  |     |     |-- Module Fixture Setup
  |     |     |
  |     |     |-- [CLASS START (TestUser)]
  |     |     |     |-- Class Fixture Setup
  |     |     |     |
  |     |     |     |-- [FUNCTION START (test_one)]
  |     |     |     |     |-- Function Fixture Setup
  |     |     |     |     |-- Executes test_one()
  |     |     |     |     |-- Function Fixture Teardown
  |     |     |     |
  |     |     |     |-- [FUNCTION START (test_two)]
  |     |     |     |     |-- Function Fixture Setup
  |     |     |     |     |-- Executes test_two()
  |     |     |     |     |-- Function Fixture Teardown
  |     |     |     |
  |     |     |     |-- Class Fixture Teardown
  |     |     |
  |     |     |-- Module Fixture Teardown
  |     |
  |     |-- Package Fixture Teardown
  |
  |-- Session Fixture Teardown
[SESSION END]
```

## Mocking: "Patch Where Looked Up" Cheat Sheet

| Scenario | Target Location | Patch String | Correct Syntax |
| :--- | :--- | :--- | :--- |
| **Function in same file** | `src.utils.math.calculate` | `"src.utils.math.calculate"` | `@patch("src.utils.math.calculate")` |
| **Class imported into file**| `src.services.user.DBClient`| `"src.services.user.DBClient"` | `@patch("src.services.user.DBClient")` |
| **Method on imported class**| `src.services.user.DBClient`| N/A (Patch the method directly) | `@patch.object(DBClient, 'connect')` |
| **Built-in open()** | `src.file_handler.open` | `"builtins.open"` | `@patch("builtins.open")` |

## Production `pyproject.toml` Template

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "core-service"
version = "1.0.0"
description = "Core production service"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.1.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.3.0",
    "mypy>=1.9.0",
]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "C4", "B", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true
```

## Production Dockerfile Template (Multi-Stage with uv)

```dockerfile
# Stage 1: Build Environment
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv venv /opt/venv && uv pip install --system /opt/venv -r uv.lock

# Stage 2: Runtime Environment
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src/
RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 8000
# JSON array CMD is strictly required for SIGTERM propagation
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

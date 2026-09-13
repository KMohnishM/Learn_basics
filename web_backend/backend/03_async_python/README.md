# Module 3: Async Python & High-Performance FastAPI

Most backend engineers know asyncio exists. Far fewer understand what it actually does, why `async def` in FastAPI is not always the right choice, or how to avoid the most common async trap: accidentally blocking the event loop.

---

## 1. The GIL — Global Interpreter Lock

Python's CPython interpreter has a GIL — a mutex that only allows one thread to execute Python bytecode at a time. This means:

- **CPU-bound work** (number crunching, image processing): Multithreading gives NO speedup. Each thread takes turns holding the GIL.
- **I/O-bound work** (network calls, database queries, file reads): Multithreading helps! While thread A waits for a network response, it releases the GIL so thread B can run.

The GIL does NOT apply to:
- Native extensions written in C (NumPy, Pandas operations run without the GIL)
- Multiple processes (each process has its own GIL)

---

## 2. Concurrency vs Parallelism vs Asynchrony

These three concepts are confused constantly:

**Concurrency**: Multiple tasks are in progress at the same time, but not necessarily running simultaneously. A restaurant with one chef handling 10 orders is concurrent — the chef switches between them.

**Parallelism**: Multiple tasks run simultaneously on multiple CPU cores. A restaurant with 10 chefs, each handling one order, is parallel.

**Asynchrony**: A task can yield control while waiting for something external (I/O), allowing other work to happen. The chef puts something in the oven and handles another order while waiting.

For network-heavy backend services:
- **asyncio** provides asynchrony (one thread, one CPU core, thousands of concurrent operations)
- **multiprocessing** provides parallelism (multiple CPU cores for CPU-bound work)

---

## 3. How asyncio Works Internally

asyncio uses an **event loop** — a single-threaded infinite loop that manages the execution of coroutines.

```python
import asyncio

async def fetch_data():
    print("Start fetching")
    await asyncio.sleep(2)   # Simulates a 2-second network call
    print("Done fetching")
    return "data"

# The event loop runs coroutines
asyncio.run(fetch_data())
```

When `await asyncio.sleep(2)` is reached:
1. The coroutine is suspended
2. The event loop looks for other coroutines that are ready to run
3. After 2 seconds, the event loop wakes the coroutine and resumes it

This is how one thread can handle thousands of concurrent "waiting" operations. The key: the thread is never actually blocked — it's always running some piece of work or scheduling future work.

### Tasks vs Coroutines

```python
import asyncio

async def slow_operation(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"{name} done"

# Sequential: total time = 3 seconds
async def sequential():
    result1 = await slow_operation("A", 1)
    result2 = await slow_operation("B", 2)
    return result1, result2

# Concurrent: total time = 2 seconds (run in parallel within same thread!)
async def concurrent():
    results = await asyncio.gather(
        slow_operation("A", 1),
        slow_operation("B", 2),
    )
    return results
```

`asyncio.gather()` runs multiple coroutines concurrently. The event loop interleaves their execution, so the total time is the maximum, not the sum.

---

## 4. `async def` vs `def` in FastAPI — A Critical Distinction

This is where most FastAPI engineers have a dangerous misconception.

### `async def` endpoints
FastAPI runs these on the **event loop**. While they're executing, they MUST yield regularly with `await`. If they don't, they block the entire event loop.

```python
@app.get("/async-correct")
async def correct_async():
    # ✅ Yields to event loop while waiting for DB
    result = await db.fetch_one("SELECT ...")
    return result

@app.get("/async-broken")
async def broken_async():
    # ❌ BLOCKS the entire event loop! All other requests stall!
    import time
    time.sleep(5)  # Never use time.sleep in async functions!
    return "done"
```

### `def` endpoints (synchronous)
FastAPI runs these in a **thread pool executor** — a pool of real OS threads. Each `def` endpoint gets its own thread, so blocking operations are fine.

```python
@app.get("/sync-ok")
def sync_blocking():
    # ✅ FastAPI runs this in a thread, not the event loop
    # Blocking is OK here!
    import time
    time.sleep(5)
    return "done"
```

### The Rule

| Your endpoint does... | Use |
|----------------------|-----|
| Only async I/O (async DB, httpx, aiofiles) | `async def` |
| Blocking I/O (blocking DB driver, `requests`, `open()`) | `def` |
| CPU-bound work | `def` + consider `ProcessPoolExecutor` |

---

## 5. Async Database Access

### The Wrong Way (Blocks Event Loop)
```python
import psycopg2   # Synchronous driver!

@app.get("/users")
async def get_users():
    conn = psycopg2.connect(...)     # BLOCKS!
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")  # BLOCKS!
    return cursor.fetchall()
```

### The Right Way (asyncpg or SQLAlchemy 2.0 Async)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))   # Non-blocking!
    return result.scalars().all()
```

### Connection Pool Sizing

The database has a maximum number of allowed connections (Postgres default: 100). If you have 10 FastAPI workers each with a pool of 20 connections, you're already at 200 — your DB will reject new connections.

**Rule of thumb**: `pool_size = num_workers * (connections_per_worker)` must be less than `database_max_connections * 0.8`.

For production: use **PgBouncer** in front of Postgres. It multiplexes many application connections into fewer real database connections.

---

## 6. Background Tasks

Sometimes work doesn't need to be done before responding to the user. For example:
- Sending a welcome email after registration
- Updating analytics counters
- Generating a report

### FastAPI BackgroundTasks (Simple)
```python
from fastapi import BackgroundTasks

def send_welcome_email(email: str):
    # This runs AFTER the response is sent
    email_service.send(email, "Welcome!")

@app.post("/register")
def register(email: str, background_tasks: BackgroundTasks):
    create_user(email)
    background_tasks.add_task(send_welcome_email, email)
    return {"message": "Registered!"}  # Returns immediately
```

**Limitation**: Runs in the same process. If the server restarts, queued tasks are lost.

### Celery (Production)
```python
from celery import Celery

celery_app = Celery("tasks", broker="redis://localhost:6379/0")

@celery_app.task
def send_welcome_email(email: str):
    email_service.send(email, "Welcome!")

# In your FastAPI endpoint
@app.post("/register")
def register(email: str):
    create_user(email)
    send_welcome_email.delay(email)   # Queued in Redis, picked up by Celery worker
    return {"message": "Registered!"}
```

**Advantages**: Tasks persist across restarts. Separate worker processes. Task retries, scheduling, monitoring (Flower).

---

## 7. Profiling and Finding Bottlenecks

Before optimizing, measure. The most common mistake is optimizing the wrong thing.

### py-spy — CPU Profiler
```bash
# Install
pip install py-spy

# Profile a running process (no code changes needed!)
py-spy record -o profile.svg --pid 12345

# Profile a script
py-spy record -o profile.svg -- python my_script.py
```

This produces a flame graph showing exactly where CPU time is spent.

### Locust — Load Testing
```python
# locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def get_users(self):
        self.client.get("/users")

    @task(3)  # 3x more likely than get_users
    def get_posts(self):
        self.client.get("/posts")
```

```bash
pip install locust
locust --host=http://localhost:8000
# Open http://localhost:8089 for the web UI
```

---

## Next Steps

Go to `labs/` to build an async FastAPI service, benchmark it under load, find a blocking bottleneck, and fix it!

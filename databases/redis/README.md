# Redis Mastery Curriculum

This curriculum provides a complete, production-quality guide to mastering Redis. It moves beyond basic key-value operations to cover advanced data structures, architectural patterns, persistence strategies, high availability, and performance optimization. 

## Target Audience

This curriculum is designed for software engineers, backend developers, system architects, and DevOps professionals who want to leverage Redis as a primary data store, caching layer, message broker, and rate-limiting engine. It assumes basic familiarity with database concepts and general programming.

## Module Map

| Module | Topic | Description | Difficulty |
|---|---|---|---|
| **01** | **Data Structures** | Core data structures (Strings, Lists, Sets, Hashes, ZSETs, Streams, Geo, HyperLogLog, Bitmaps) and internal memory encodings. | Beginner to Intermediate |
| **02** | **Design Patterns** | Caching strategies, pub/sub, distributed locks, rate limiting, session stores, and background job queues. | Intermediate to Advanced |
| **03** | **Persistence & HA** | RDB snapshots, AOF logs, Redis Sentinel (High Availability), Replication, and Redis Cluster (Sharding). | Advanced |
| **04** | **Performance** | Memory optimization, eviction policies, pipelining, transactions (MULTI/EXEC), Lua scripting, and diagnostics. | Expert |

## Suggested Study Path

1. **Module 1: Data Structures** (Estimated time: 4-6 hours)
   Start here to understand what Redis is truly capable of. Focus heavily on Sorted Sets, Hashes, and Streams.
2. **Module 2: Patterns** (Estimated time: 4-5 hours)
   Learn how to apply data structures to solve real-world system design problems. Pay special attention to distributed locks and caching patterns.
3. **Module 3: Persistence & HA** (Estimated time: 5-7 hours)
   Crucial for operations and DevOps. Learn how to prevent data loss and ensure 99.99% uptime.
4. **Module 4: Performance** (Estimated time: 4-6 hours)
   Learn how to scale Redis, debug memory issues, and write atomic Lua scripts.

## How to Practice

To get the most out of this curriculum, practice the commands and concepts in a live environment.

### Local Docker Setup

The easiest way to run Redis locally without installing it directly on your host is via Docker.

**Start a Redis Server:**
```bash
docker run --name redis-server -p 6379:6379 -d redis:7.2
```

**Connect with Redis CLI:**
```bash
docker exec -it redis-server redis-cli
```

### Python Redis Client Setup

Many modules include Python examples. Setup a virtual environment and install the official `redis-py` client.

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install redis
```

**Basic Python Connection Example:**
```python
import redis

# Connect to local Redis
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Test connection
client.ping()

# Basic operations
client.set('greeting', 'Hello Redis')
print(client.get('greeting'))
```

Work through each module sequentially, reading the `README.md`, testing the commands from the `CHEATSHEET.md`, and verifying your understanding with the `QnA.md` files.

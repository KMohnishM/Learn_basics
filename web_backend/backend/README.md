# Backend Mastery — Complete Curriculum

A production-grade, deeply technical curriculum for engineers who want to build backend systems that are fast, correct, secure, and observable at scale. Not tutorial-level — every module addresses the hard questions that come up in senior engineering interviews and real production incidents.

---

## Who This Is For

- Software engineers looking to move from junior to senior level
- Engineers preparing for backend interviews at top tech companies
- Full-stack developers who want to go deep on the server side

---

## Curriculum Structure

Each module follows this structure:
```
module/
├── README.md       ← Deep-dive theory (read first — this is dense)
├── labs/           ← Runnable code you can execute and modify
├── exercise/       ← A real problem to solve independently
└── solution/       ← Full reference implementation with explanations
```

---

## Modules

| # | Module | Core Skills | Hardest Concepts |
|---|--------|-------------|-----------------|
| [M1](./01_api_design/) | **API Design That Scales** | REST maturity, HTTP semantics, versioning, cursor pagination, GraphQL, gRPC | HATEOAS, idempotency keys, N+1 in GraphQL, DataLoader |
| [M2](./02_auth/) | **Auth & Authorization** | Password hashing (bcrypt/Argon2), JWT internals, refresh token rotation, OAuth2 PKCE, RBAC/ABAC | JWT algorithm confusion attack, token rotation, PKCE |
| [M3](./03_async_python/) | **Async Python & FastAPI** | GIL, concurrency vs parallelism, asyncio internals, event loop blocking, async DB | The sync-inside-async trap, `asyncio.gather()` |
| [M4](./04_database_patterns/) | **Advanced DB Patterns** | N+1 queries, EXPLAIN ANALYZE, composite indexes, isolation levels, CQRS, Event Sourcing | SELECT FOR UPDATE, deadlocks, zero-downtime migrations |
| [M5](./05_resilience/) | **Building Resilient Services** | Timeouts, retries with backoff/jitter, Circuit Breaker, Bulkhead, graceful degradation | Thundering herd, cascading failures, idempotent retries |
| [M6](./06_testing/) | **Testing That Finds Bugs** | Testing pyramid, pytest fixtures, async tests, Testcontainers, Hypothesis property testing | The difference between coverage and confidence |
| [M7](./07_security/) | **Backend Security** | OWASP Top 10, SQL/NoSQL/Command injection, JWT attacks, IDOR, CORS, CSP, secrets management | JWT algorithm confusion, IDOR at scale, secret rotation |
| [M8](./08_observability/) | **Observability** | Structured logging, correlation IDs, Prometheus (four golden signals), distributed tracing, SLOs | Error budgets, alerting on symptoms not causes |

---

## Learning Path

### Month 1 — Core Foundations
**Week 1**: M1 (API Design) — Build and benchmark a REST vs GraphQL API  
**Week 2**: M2 (Auth) — Build a complete JWT auth system with refresh token rotation  
**Week 3**: M3 (Async) — Prove the event loop blocking problem with benchmarks  
**Week 4**: M4 (Database) — Build a bank account using Event Sourcing and CQRS

### Month 2 — Production Engineering
**Week 5**: M5 (Resilience) — Demo cascading failures, then Circuit Breakers preventing them  
**Week 6**: M6 (Testing) — Property-based testing with Hypothesis that finds a real edge case bug  
**Week 7**: M7 (Security) — Attack the deliberately vulnerable app, then fix it  
**Week 8**: M8 (Observability) — Instrument a service, run Grafana, build an SLO reporter  

---

## Prerequisites

```bash
pip install fastapi uvicorn asyncpg sqlalchemy psycopg2-binary redis httpx \
            python-jose bcrypt tenacity pytest pytest-asyncio hypothesis \
            strawberry-graphql prometheus-client
```

Docker is required for database labs:
```bash
# Start infrastructure for a specific module
cd backend/02_auth/labs && docker-compose up -d
```

---

## Interview Prep

This curriculum covers the most commonly-tested backend concepts at top engineering companies:

| Topic | Where Covered | Interview Frequency |
|-------|--------------|---------------------|
| REST vs GraphQL | M1 | ⭐⭐⭐⭐ |
| JWT & OAuth2 | M2 | ⭐⭐⭐⭐⭐ |
| Async/Concurrency | M3 | ⭐⭐⭐⭐ |
| Database Indexing | M4 | ⭐⭐⭐⭐⭐ |
| ACID & Isolation | M4 | ⭐⭐⭐⭐ |
| Circuit Breaker | M5 | ⭐⭐⭐⭐ |
| Testing Strategies | M6 | ⭐⭐⭐ |
| OWASP Vulnerabilities | M7 | ⭐⭐⭐⭐ |
| Observability / SLOs | M8 | ⭐⭐⭐⭐ |

---

## Key Technologies

| Technology | Purpose | Module |
|-----------|---------|--------|
| FastAPI | Async web framework | M1-M8 |
| Postgres + pgvector | Primary database | M2, M4 |
| Redis | Caching, rate limiting, token revocation | M2, M5 |
| pytest + Hypothesis | Testing framework | M6 |
| Prometheus + Grafana | Metrics and dashboards | M8 |
| Jaeger | Distributed tracing | M8 |
| Docker Compose | Local infrastructure | M2-M8 |

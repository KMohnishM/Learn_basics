# Java Backend

A complete curriculum covering Java backend development from core language internals through Spring Boot, enterprise patterns, and production operations.

## Module Map

| Module | Topic | Key Concepts |
|--------|-------|-------------|
| [01_java_core_modern](./01_java_core_modern/) | Java Core Modern | Records, sealed classes, pattern matching, streams, lambdas, virtual threads, CompletableFuture |
| [02_spring_core_ioc](./02_spring_core_ioc/) | Spring Core IoC | ApplicationContext, DI types, bean scopes, lifecycle, AOP, SpEL, events |
| [03_spring_boot](./03_spring_boot/) | Spring Boot | Auto-configuration, starters, profiles, Actuator, testing, packaging, graceful shutdown |
| [04_spring_data_jpa](./04_spring_data_jpa/) | Spring Data JPA | Entity mapping, relationships, N+1 problem, projections, @Transactional, auditing, locking |
| [05_spring_security](./05_spring_security/) | Spring Security | Filter chain, JWT, OAuth2, method security, CORS, CSRF, session management |
| [06_rest_apis_spring](./06_rest_apis_spring/) | REST APIs Spring | @RestController, validation, exception handling, OpenAPI, versioning, pagination, rate limiting |
| [07_jakarta_ee_j2ee](./07_jakarta_ee_j2ee/) | Jakarta EE / J2EE | Servlet lifecycle, CDI, EJB, JMS, JAX-RS, JNDI, application servers |
| [08_production_ops](./08_production_ops/) | Production Ops | JVM tuning, GC algorithms, GraalVM native, Micrometer, Flyway, K8s deployment |

## Recommended Study Order

```
1. Java Core Modern       -- language fundamentals before any framework
2. Spring Core IoC        -- understand DI and the container
3. Spring Boot            -- build your first production app
4. Spring Data JPA        -- connect to databases properly
5. REST APIs Spring       -- expose your business logic
6. Spring Security        -- secure your APIs
7. Jakarta EE / J2EE      -- enterprise context and legacy understanding
8. Production Ops         -- run in production reliably
```

## Prerequisites

- Basic Java syntax (variables, loops, classes, interfaces)
- Maven or Gradle installed
- JDK 21 installed (use SDKMAN or Homebrew)
- PostgreSQL running locally (or Docker: `docker run -e POSTGRES_PASSWORD=pass -p 5432:5432 postgres:16`)

# Testing Fundamentals Cheatsheet

## Test Types

| Test Type | Scope | Speed | Description |
|-----------|-------|-------|-------------|
| **Unit** | Small | Very Fast | Tests isolated functions/classes with mocked dependencies. |
| **Integration**| Medium| Fast | Tests how multiple units work together (e.g., DB connections). |
| **Component** | Medium| Fast | Tests a UI component in isolation (DOM rendering). |
| **E2E** | Large | Slow | Tests full user journeys across the entire application stack. |
| **Smoke** | Core | Fast | Basic checks to ensure the application starts and doesn't crash. |
| **Regression** | Broad | Varies| Re-running tests to ensure new code hasn't broken old features. |
| **Contract** | API | Fast | Ensures microservices agree on request/response formats. |

---

## Test Doubles

| Double Type | Purpose | Example Use Case |
|-------------|---------|------------------|
| **Dummy** | Fills parameter lists | Passing an empty `{}` for a logger that won't be called. |
| **Stub** | Returns canned responses| `getUser()` always returns `{ id: 1, name: "Test" }`. |
| **Spy** | Records method calls | Asserting `sendEmail()` was called exactly once. |
| **Mock** | Fails if called wrong | Setting strict expectations on how an API is called. |
| **Fake** | Working shortcut impl. | An in-memory SQLite database instead of real PostgreSQL. |

---

## TDD Cycle (Red-Green-Refactor)

```text
 ┌──────────────┐
 │   1. RED     │ Write a failing test.
 └──────┬───────┘
        │
 ┌──────▼───────┐
 │  2. GREEN    │ Write minimal code to pass the test.
 └──────┬───────┘
        │
 ┌──────▼───────┐
 │ 3. REFACTOR  │ Clean up code without breaking tests.
 └──────┬───────┘
        │
        └──────── (Repeat for next feature)
```

---

## F.I.R.S.T. Principles for Unit Tests

- **Fast**: Runs in milliseconds.
- **Isolated**: Does not depend on other tests or shared state.
- **Repeatable**: Deterministic results every time, everywhere.
- **Self-Validating**: Passes or fails without manual inspection.
- **Timely**: Written alongside or before production code.

---

## Coverage Thresholds

- **Line**: Percentage of code lines executed.
- **Branch**: Percentage of logic branches (`if`/`else`) executed.
- **Function**: Percentage of functions called.
- **Statement**: Percentage of code statements executed.
- *Best Practice*: Aim for ~80% branch coverage. 100% is a false idol.

---

## Anti-Patterns

1. **Testing Implementation Details**: Asserting *how* code works instead of *what* it returns.
2. **Over-Mocking**: Mocking everything so you're only testing the mocks, not the code.
3. **Flaky Tests**: Tests that randomly fail due to race conditions or time dependencies.
4. **God Tests**: Massive tests with 50 assertions that test an entire feature at once.
5. **Interdependent Tests**: Tests that fail if run in isolation or a different order.

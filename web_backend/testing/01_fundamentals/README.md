# Module 01: Testing Fundamentals

Software testing is the process of evaluating and verifying that a software product or application does what it is supposed to do. The benefits of testing include preventing bugs, reducing development costs, and improving performance. This module will cover the foundational concepts that apply regardless of the language or framework you are using.

## 1. Why Testing Matters

Testing is often viewed as a chore or an afterthought, but it is a critical component of software engineering. Understanding why we test is the first step to writing effective tests.

### The Cost of Bugs
According to a famous study by the IBM Systems Sciences Institute, the cost to fix a bug found during the implementation phase is about 6 times higher than one identified during design. If a bug makes it to the testing phase, it costs 15 times more. If it reaches production, fixing it costs up to 100 times more. 

When a bug hits production:
- You have to stop feature work to investigate.
- Customer trust is eroded.
- Data might be corrupted, requiring manual cleanup.
- Patches must go through the entire deployment pipeline again.

### Confidence in Refactoring
Software is never finished. Code must be refactored to accommodate new features, improve performance, or update dependencies. Without a solid test suite, developers are afraid to touch working code. "If it ain't broke, don't fix it" becomes the mantra, leading to technical debt. Tests act as a safety net, allowing developers to refactor aggressively with the confidence that they haven't broken existing functionality.

### Executable Documentation
Documentation often goes out of date the moment it is written. Tests, on the other hand, must pass on every build. A well-written test suite explains how the system is supposed to behave, what inputs are expected, and what outputs are generated. When a new developer joins the team, reading the tests is one of the best ways to understand the domain.

### The False Economy of Skipping Tests
"We don't have time to write tests." This is a false economy. While writing tests takes time upfront, debugging a complex issue manually, verifying changes by clicking through a UI, and fixing regressions take vastly more time in the long run. Code without tests is technical debt created at the exact moment the code is written.

---

## 2. Types of Tests

Software testing is categorized into various levels. Each level targets a different scope of the application.

### Unit Tests
Unit tests focus on the smallest testable parts of an application, typically individual functions or classes. They isolate the unit from its dependencies using test doubles.
- **Scope**: Very narrow.
- **Speed**: Extremely fast (milliseconds).
- **Purpose**: Verify logic, edge cases, and calculations.

### Integration Tests
Integration tests verify that different modules or services work together correctly. They often involve real databases, file systems, or network calls to internal services.
- **Scope**: Medium.
- **Speed**: Moderate.
- **Purpose**: Ensure data flows correctly between boundaries (e.g., ORM to database).

### End-to-End (E2E) Tests
E2E tests evaluate the entire application stack from the user's perspective. They interact with the UI, trigger backend processes, and verify the final state.
- **Scope**: Broad.
- **Speed**: Slow.
- **Purpose**: Validate critical user journeys (e.g., checkout process).

### Component Tests
Often used in frontend frameworks (React, Vue), component tests render a single component in isolation but interact with it as a user would (clicking buttons, typing text) rather than just calling its functions.

### Contract Tests
In microservice architectures, contract tests ensure that two services (a consumer and a provider) have a shared understanding of the API format. They prevent situations where service A changes its response format, breaking service B.

### Performance Tests
These tests determine how a system performs in terms of responsiveness and stability under a particular workload. Examples include load testing and stress testing.

### Smoke Tests
A basic set of tests run after a build to ensure the most crucial functions work. If the smoke tests fail, the build is immediately rejected. "Did the system catch fire when we turned it on?"

### Regression Tests
Tests designed specifically to ensure that recent code changes have not adversely affected existing features. Most automated test suites serve as regression tests.

---

## 3. The Test Pyramid

The Test Pyramid is a metaphor that tells us to group software tests into buckets of different granularity. It also gives an idea of how many tests we should have in each of these groups.

```text
         /\
        /  \
       /E2E \
      /------\
     /        \
    /Integrat'n\
   /            \
  /--------------\
 /                \
/       Unit       \
--------------------
```

### The Concept
- Base: Unit tests. You should have thousands of them. They are fast and cheap.
- Middle: Integration tests. You should have hundreds. They take longer to run and write.
- Top: E2E tests. You should have tens. They are slow, expensive to maintain, and prone to flakiness.

### The 70/20/10 Rule
A common rule of thumb (popularized by Google) is a 70/20/10 split: 70% unit tests, 20% integration tests, and 10% E2E tests. The exact percentages don't matter as much as the shape of the pyramid.

### The Inverted Pyramid (Anti-pattern)
An inverted pyramid (or ice cream cone) happens when a team relies heavily on manual or E2E tests and has very few unit tests. This results in incredibly slow CI pipelines and tests that fail for unpredictable reasons (flakiness).

### The Testing Trophy
Guillermo Rauch popularized the "Testing Trophy" specifically for modern frontend development:
"Write tests. Not too many. Mostly integration."
For frontend, pure unit tests often provide less value than component/integration tests that mount a component and verify DOM changes.

---

## 4. Test Doubles

When writing unit tests, you want to isolate the unit from its dependencies (databases, APIs, time). We do this using Test Doubles (a term coined by Gerard Meszaros, inspired by stunt doubles in movies).

There are five primary types of test doubles.

### 1. Dummy
Objects that are passed around but never actually used. Usually, they are just used to fill parameter lists.

```javascript
// JavaScript Example
function registerUser(user, logger) {
  // logic
}

test('registers user', () => {
  const dummyLogger = {}; // Never called, just passed to satisfy signature
  registerUser({ name: 'Alice' }, dummyLogger);
});
```

### 2. Stub
Stubs provide canned answers to calls made during the test. They do not respond to anything outside what they are programmed for.

```javascript
// JavaScript Example
const weatherServiceStub = {
  getTemperature: () => 25 // Always returns 25
};

test('recommends t-shirt when warm', () => {
  const outfit = getOutfitRecommendation(weatherServiceStub);
  expect(outfit).toBe('t-shirt');
});
```

### 3. Spy
Spies are stubs that also record some information based on how they were called. You can verify how many times a spy was called or what arguments it received.

```javascript
// JavaScript Example (using Jest)
test('calls logger with error message', () => {
  const spyLogger = { error: jest.fn() };
  
  processData('bad_data', spyLogger);
  
  expect(spyLogger.error).toHaveBeenCalledWith('Invalid data format');
  expect(spyLogger.error).toHaveBeenCalledTimes(1);
});
```

### 4. Mock
Mocks are pre-programmed with expectations which form a specification of the calls they are expected to receive. They can throw an exception if they receive an unexpected call. Often, the line between Spies and Mocks is blurred in frameworks like Jest.

```javascript
// JavaScript Example
test('processes payment', () => {
  const mockPaymentGateway = {
    charge: jest.fn().mockReturnValue(true)
  };
  
  const result = checkout(100, mockPaymentGateway);
  
  expect(mockPaymentGateway.charge).toHaveBeenCalledWith(100);
  expect(result).toBe('Success');
});
```

### 5. Fake
Fakes actually have working implementations, but usually take some shortcut which makes them not suitable for production. An in-memory database is a classic fake.

```javascript
// JavaScript Example
class FakeUserRepository {
  constructor() {
    this.users = new Map();
  }
  
  save(user) {
    this.users.set(user.id, user);
  }
  
  findById(id) {
    return this.users.get(id);
  }
}

test('saves and retrieves user', () => {
  const repo = new FakeUserRepository();
  repo.save({ id: 1, name: 'Bob' });
  expect(repo.findById(1).name).toBe('Bob');
});
```

---

## 5. Test-Driven Development (TDD)

Test-Driven Development (TDD) is a software development process relying on a very short development cycle.

### The Red-Green-Refactor Cycle

1. **Red**: Write a test for the next bit of functionality you want to add. Run the test. It should fail (because the feature isn't implemented yet). This proves the test is actually testing something.
2. **Green**: Write the absolute minimum amount of code required to make the test pass. Do not write extra features.
3. **Refactor**: Clean up the code. Remove duplication. Make it readable. Ensure all tests still pass.

### Example: Stack in JavaScript

Let's implement a simple Stack using TDD.

**Step 1: Red**
```javascript
// stack.test.js
test('Stack is empty on creation', () => {
  const stack = new Stack();
  expect(stack.isEmpty()).toBe(true);
});
```

**Step 2: Green**
```javascript
// stack.js
class Stack {
  isEmpty() {
    return true; // Simplest code to pass
  }
}
```

**Step 3: Red (Next test)**
```javascript
test('Stack is not empty after push', () => {
  const stack = new Stack();
  stack.push(1);
  expect(stack.isEmpty()).toBe(false);
});
```

**Step 4: Green**
```javascript
class Stack {
  constructor() {
    this.items = [];
  }
  isEmpty() {
    return this.items.length === 0;
  }
  push(item) {
    this.items.push(item);
  }
}
```

### Example: Stack in Python

**Step 1: Red**
```python
# test_stack.py
def test_stack_is_empty():
    stack = Stack()
    assert stack.is_empty() == True
```

**Step 2: Green**
```python
# stack.py
class Stack:
    def is_empty(self):
        return True
```

### Benefits of TDD
- Ensures high test coverage by default.
- Forces you to design from the caller's perspective, leading to better APIs.
- Prevents scope creep (you only write code to pass tests).

---

## 6. Behavior-Driven Development (BDD)

BDD emerged from TDD. It focuses on the behavior of the system from the outside rather than the internal implementation. It uses a ubiquitous language that both technical and non-technical stakeholders can understand.

### Given-When-Then
BDD tests are structured in three phases:
- **Given**: Set up the initial state or context.
- **When**: Perform the action being tested.
- **Then**: Assert the expected outcome.

### Shopping Cart Example (JavaScript)

```javascript
describe('Shopping Cart Checkout', () => {
  test('Applying a valid discount code reduces the total', () => {
    // Given
    const cart = new ShoppingCart();
    cart.addItem({ name: 'Book', price: 20 });
    cart.addItem({ name: 'Pen', price: 5 });
    
    // When
    cart.applyDiscountCode('10OFF');
    
    // Then
    expect(cart.getTotal()).toBe(15);
  });
});
```

### Gherkin Syntax
For true BDD, teams often use tools like Cucumber, which read tests written in Gherkin (a plain English syntax).

```gherkin
Feature: Shopping Cart Discount

  Scenario: Applying a valid discount
    Given a shopping cart with a total of $25
    When I apply the discount code "10OFF"
    Then the new total should be $15
```
This syntax bridges the gap between product managers writing requirements and engineers writing tests.

---

## 7. Code Coverage

Code coverage is a metric that measures the percentage of your source code executed when the test suite runs.

### Types of Coverage
- **Line Coverage**: Has each line of code been executed?
- **Branch Coverage**: Has each control structure (if/else, switch) evaluated to both true and false?
- **Function Coverage**: Has each function been called?
- **Statement Coverage**: Has each statement been executed? (Often identical to line coverage).

### Why 100% Coverage is a Bad Goal
Aiming for 100% coverage often leads to diminishing returns and perverse incentives. Developers may write meaningless tests just to hit the metric, such as asserting that a getter returns a value without testing actual business logic. A reasonable target is usually 70-80%. The focus should be on covering critical business paths.

### Mutation Testing
High coverage does not guarantee high test quality. If you delete an assertion in a test, the coverage remains the same, but the test is useless. 
Mutation testing solves this by intentionally modifying (mutating) your source code (e.g., changing `+` to `-`, or `<` to `<=`) and running the tests. If the tests still pass, a "mutant has survived," indicating your tests are weak. Tools like Stryker (JS) or Mutmut (Python) handle this.

---

## 8. Test Organisation and Naming

How you organize and name your tests severely impacts maintainability.

### Co-location vs. `__tests__` directories
There are two main schools of thought for where to put test files:

1. **Centralized (`test/` or `__tests__/` directory)**
   All tests are kept in a separate folder structure mirroring the source directory.
   - Pro: Keeps `src/` clean of test code.
   - Con: Harder to find the corresponding test for a file deeply nested in `src/`.

2. **Co-location**
   Test files sit right next to the source files (e.g., `UserService.js` and `UserService.test.js`).
   - Pro: Immediately obvious if a file has tests. Easy to import the source file.
   - Con: Clutters the source directory.

Co-location is generally preferred in modern JavaScript and Python development.

### Naming Conventions
Test names should describe the behavior, not just the function name. A test named `testCalculate()` is unhelpful when it fails.

**Pattern: MethodName_StateUnderTest_ExpectedBehavior**
- `CalculateTotal_WithEmptyCart_ReturnsZero`
- `CalculateTotal_WithDiscount_AppliesDiscountCorrectly`

**Pattern: "It should..." (BDD style)**
```javascript
describe('UserService', () => {
  describe('createUser', () => {
    it('should throw an error if email is already taken', () => {
      // ...
    });
    
    it('should save the user to the database on success', () => {
      // ...
    });
  });
});
```

---

## 9. F.I.R.S.T Principles

Good unit tests adhere to the F.I.R.S.T principles:

- **Fast**: Tests must be extremely quick. If they take minutes to run, developers will stop running them locally. Fast tests provide immediate feedback.
- **Isolated**: Tests should not depend on each other. You should be able to run any single test in isolation or run them all in parallel. They should not share state.
- **Repeatable**: A test should yield the same result every time, on any machine, regardless of external factors (like network connectivity or the current date).
- **Self-Validating**: The test itself should determine if it passed or failed via assertions. You should not have to manually inspect a log file or a database to verify the outcome.
- **Timely**: Tests should be written just before the production code (TDD), or at least concurrently with it. Writing tests months after the code is written is much harder and less effective.

---

## 10. Anti-Patterns

Recognizing bad testing practices is just as important as knowing good ones. Avoid these anti-patterns:

### Testing Implementation Details
Tests should verify the *output* of a function given an *input*, not *how* the function arrived at the output. If you test implementation details, refactoring (improving internal code without changing behavior) will break your tests.

**Bad**:
```javascript
test('sorts the array', () => {
  const array = [3, 1, 2];
  const sorter = new Sorter();
  const spy = jest.spyOn(sorter, 'quickSort'); // Assuming quicksort is used
  sorter.sort(array);
  expect(spy).toHaveBeenCalled();
});
```

**Good**:
```javascript
test('sorts the array', () => {
  const array = [3, 1, 2];
  const sorter = new Sorter();
  const result = sorter.sort(array);
  expect(result).toEqual([1, 2, 3]);
});
```

### Over-Mocking
Mocking is necessary, but mocking everything leads to brittle tests that pass even when the system is fundamentally broken. If you mock the database, the network, and all helper functions, you are only testing that your mocks work. Prefer using real dependencies where possible, especially in integration tests.

### God Tests
A God Test is a single massive test function that tests everything about a feature. It has 50 assertions and hundreds of lines of setup. When it fails, it is nearly impossible to figure out *why* it failed without extensive debugging. Keep tests small and focused on a single logical assertion.

### Flaky Tests
A flaky test is a test that sometimes passes and sometimes fails without any code changes. Causes include:
- Relying on `Date.now()` instead of mocking the system clock.
- Relying on random number generation.
- Network requests in tests.
- Asynchronous race conditions (e.g., not waiting for a UI element to fully render).
Flaky tests destroy trust in the test suite. If a test is flaky, fix it immediately or delete it.

### Interdependence
Test A creates a user in the database. Test B expects that user to exist. If you run Test B in isolation, it fails. If you run the tests in reverse order, they fail. Every test must set up its own state and clean up after itself (using `beforeEach` and `afterEach` hooks).

---

By mastering these fundamentals, you lay the groundwork for writing robust, maintainable, and effective test suites. In the next modules, we will apply these concepts hands-on using real-world testing frameworks.

### Section: Testing in a CI/CD Pipeline
- Where tests fit in the pipeline: pre-commit hooks (lint + unit), PR checks (unit + integration), merge to main (full suite), post-deployment (smoke tests)
- Pre-commit hooks with Husky + lint-staged:
```bash
npm install --save-dev husky lint-staged
npx husky init
```
```json
// package.json
{
  "lint-staged": {
    "*.{ts,js}": [
      "eslint --fix",
      "jest --findRelatedTests --passWithNoTests"
    ]
  }
}
```
- GitHub Actions full test pipeline:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm test -- --coverage --ci
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: coverage/
```
- Failing the build on coverage threshold: `--coverageThreshold='{"global":{"lines":80}}'`
- Parallelising tests in CI with `--maxWorkers=4`

### Section: Test Data Management
- Test data strategies: hardcoded constants (simplest), object mother pattern, builder pattern, faker libraries
- Object Mother pattern:
```typescript
// tests/mothers/UserMother.ts
export class UserMother {
  static valid(): User {
    return { id: 1, name: 'Alice Smith', email: 'alice@example.com', role: 'user', active: true };
  }
  static admin(): User {
    return { ...UserMother.valid(), id: 2, role: 'admin' };
  }
  static inactive(): User {
    return { ...UserMother.valid(), id: 3, active: false };
  }
  static withEmail(email: string): User {
    return { ...UserMother.valid(), email };
  }
}
// Usage in tests:
const user = UserMother.valid();
const adminUser = UserMother.admin();
```
- Builder pattern for complex objects:
```typescript
export class OrderBuilder {
  private order: Partial<Order> = {};
  withId(id: number) { this.order.id = id; return this; }
  withProduct(product: Product) { this.order.product = product; return this; }
  withQuantity(qty: number) { this.order.quantity = qty; return this; }
  withStatus(status: OrderStatus) { this.order.status = status; return this; }
  build(): Order {
    return {
      id: this.order.id ?? 1,
      product: this.order.product ?? { id: 1, name: 'Widget', price: 9.99 },
      quantity: this.order.quantity ?? 1,
      status: this.order.status ?? 'pending',
      createdAt: new Date('2024-01-01'),
    };
  }
}
// Usage:
const order = new OrderBuilder().withQuantity(5).withStatus('shipped').build();
```

### Section: Testing Error Boundaries and Edge Cases
- Boundary value analysis: test at the boundary, just below, and just above
  - For a function that accepts ages 18-65: test 17, 18, 65, 66, 0, -1, null, undefined, NaN
- Equivalence partitioning: test one value from each valid and invalid partition
- Error path testing: every thrown error and rejected promise must have a test
```typescript
// Comprehensive error path testing
describe('UserService.createUser', () => {
  it('throws ValidationError for missing name', async () => {
    await expect(service.createUser({ email: 'a@b.com' })).rejects.toThrow(ValidationError);
  });
  it('throws ValidationError for invalid email format', async () => {
    await expect(service.createUser({ name: 'Alice', email: 'notanemail' })).rejects.toThrow(ValidationError);
  });
  it('throws ConflictError for duplicate email', async () => {
    mockRepo.existsByEmail.mockResolvedValue(true);
    await expect(service.createUser({ name: 'Alice', email: 'a@b.com' })).rejects.toThrow(ConflictError);
  });
  it('propagates unexpected repository errors', async () => {
    mockRepo.save.mockRejectedValue(new Error('DB connection lost'));
    await expect(service.createUser({ name: 'Alice', email: 'a@b.com' })).rejects.toThrow('DB connection lost');
  });
});
```

### Section: Accessibility Testing
- Why accessibility (a11y) testing matters: legal compliance (ADA, WCAG 2.1), inclusive design
- jest-axe for automated a11y checking:
```bash
npm install --save-dev jest-axe
```
```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

test('LoginForm has no accessibility violations', async () => {
  const { container } = render(<LoginForm />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```
- What axe catches: missing alt text on images, form inputs without labels, insufficient colour contrast, missing ARIA roles, keyboard navigation issues
- What axe cannot catch: correct ARIA usage semantically, logical reading order, complex keyboard flows (need manual testing)

### Section: Test Performance Optimisation
- Slow test suites: identify slow tests with `--verbose` and `--testTimeout`
- Jest parallel execution: by default Jest runs test files in parallel using worker processes
  - `--runInBand`: run all tests serially in the main process (useful for debugging, slower)
  - `--maxWorkers=50%`: use half available CPU cores
- Test file isolation cost: Jest creates a new module registry per test file
  - Use `jest.isolateModules()` to reset module registry within a single test file
- Selective test runs during development:
  - `jest --watch`: re-run tests related to changed files
  - `jest --watchAll`: re-run all tests on any change
  - `jest --onlyFailures`: re-run only previously failed tests
  - Press `p` in watch mode to filter by filename pattern
  - Press `t` to filter by test name pattern

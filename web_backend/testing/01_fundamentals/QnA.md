# Fundamentals of Testing QnA

**Q1: Explain the test pyramid. Why should there be more unit tests than E2E tests? What is the testing trophy (Kent C. Dodds) and how does it differ?**
The test pyramid is a conceptual model that guides the proportion of different types of tests in a codebase. It suggests having a wide base of fast, cheap, and highly isolated unit tests, a middle layer of integration tests, and a small peak of end-to-end (E2E) tests.
This shape is rationalized by cost, execution speed, and maintenance effort. Unit tests execute in milliseconds and pinpoint exact code failures, making them cheap to run continuously. E2E tests interact with real browsers, databases, and network layers, making them notoriously slow and brittle.
An inverted pyramid (or "ice-cream cone") is an anti-pattern where an application relies heavily on E2E testing, leading to painfully slow CI pipelines and high maintenance costs due to flaky tests.
Kent C. Dodds introduced the "Testing Trophy", which slightly alters this proportion, particularly for modern front-end applications like React.
The Trophy shape is: Static Analysis (bottom), Unit Tests, Integration Tests (largest middle section), and E2E Tests (top).
The Trophy emphasizes integration tests over unit tests because testing components in isolation often requires mocking too much internal state, which doesn't give confidence that the application works for the user. Integration tests, which test the collaboration of multiple units, strike the best balance between execution speed and confidence.
This approach assumes that tools like ESLint and TypeScript catch many basic errors, reducing the need for trivial unit tests.
Thus, the trophy focuses effort where it provides the most return on investment.

**Q2: What is the difference between a Stub, Spy, Mock, and Fake? Give a concrete JavaScript code example of each.**
According to Gerard Meszaros, test doubles are categorized by their behavior and purpose.
A **Stub** provides canned answers to calls made during the test, usually not responding at all to anything outside what's programmed in for the test.
A **Spy** is a stub that also records some information based on how it was called. One form of this might be an email service that records how many messages it was sent.
A **Mock** is a test double pre-programmed with expectations which form a specification of the calls they are expected to receive. They can throw an exception if they receive a call they don't expect and are checked during verification to ensure they got all the calls they were expecting.
A **Fake** actually has working implementations, but usually takes some shortcut which makes them not suitable for production (an in-memory database is a good example).
```javascript
// Stub: Just returns a hardcoded value, no verification
const stubbedDb = { getUser: jest.fn().mockReturnValue({ name: 'John' }) };

// Spy: Records calls but might call original implementation
const spy = jest.spyOn(console, 'log');
doSomething();
expect(spy).toHaveBeenCalledWith('success');

// Mock: Sets expectations for verification
const emailMock = { send: jest.fn() };
registerUser(emailMock);
expect(emailMock.send).toHaveBeenCalledTimes(1);

// Fake: Working implementation but simplified
class FakeRepo {
  constructor() { this.users = []; }
  save(user) { this.users.push(user); }
  get(id) { return this.users.find(u => u.id === id); }
}
```

**Q3: Explain the TDD Red-Green-Refactor cycle. What does the Red phase force you to think about? What is the key discipline of the Green phase?**
Test-Driven Development (TDD) operates on a strict cycle: Red, Green, Refactor.
During the **Red** phase, you write a failing test for the next bit of functionality you want to implement. This forces you to design the API from the consumer's perspective before writing implementation details. Seeing the test fail for the right reason is crucial—it proves the test is valid and capable of catching the absence of the feature.
In the **Green** phase, you write the absolute minimum production code required to make the failing test pass. The discipline here is to resist over-engineering; if a hardcoded string makes the test pass, you write a hardcoded string. The goal is to quickly reach a known safe state.
Finally, the **Refactor** phase allows you to improve the internal structure of the code, remove duplication, and apply design patterns, all while the passing test provides a safety net.
```javascript
// Red: Write the test first, see it fail
test('add returns sum', () => { expect(add(2, 3)).toBe(5); });

// Green: Minimum code to pass
function add(a, b) { return a + b; } // Or even return 5; initially

// Refactor: Improve implementation if needed (e.g. handling multiple arguments)
function add(...args) { 
  return args.reduce((sum, num) => sum + num, 0); 
}
```
This cycle prevents writing code that isn't strictly necessary and guarantees high test coverage naturally.

**Q4: What does code coverage measure? Why is 100% line coverage not a sufficient quality metric? What is mutation testing and how does it measure test quality better?**
Code coverage tools measure which parts of your source code are executed when the test suite runs. The primary metrics are line (which lines executed), branch (which control structures evaluated to true/false), function (which functions were called), and statement coverage.
However, 100% line coverage only proves that the code was executed, not that its behavior was verified. This leads to the "test with no assertions" problem, where developers write tests to hit code paths just to satisfy coverage thresholds without actually testing outcomes.
Mutation testing provides a much stronger quality metric. Tools like Stryker introduce small changes (mutations) into your source code (e.g., changing `+` to `-`, or `<` to `<=`). If your test suite still passes, the mutant "survives", indicating a gap in your assertions. If the tests fail, the mutant is "killed".
A high mutation score means your tests are tightly coupled to the actual behavior of the code and will accurately catch regressions, making it a far superior proxy for test suite quality than simple line coverage.
It forces you to write meaningful assertions rather than just executing the code, fundamentally shifting focus from code execution to behavior verification.

**Q5: What are the F.I.R.S.T principles of unit testing? Give a concrete violation example for each principle.**
The F.I.R.S.T principles define the characteristics of high-quality unit tests: Fast, Independent, Repeatable, Self-Validating, and Thorough.
**Fast**: Tests should run quickly (in milliseconds). Violation: A unit test that connects to a real PostgreSQL database, adding hundreds of milliseconds of latency per test, which discourages developers from running the suite frequently.
**Independent**: Tests should not rely on each other. Violation: Test A sets a global `currentUser` variable, and Test B fails if run alone because it relies on Test A running first to populate that variable. They must run in any order.
**Repeatable**: Tests should yield the same result in any environment. Violation: A test that calls `new Date()` and asserts against a hardcoded timestamp, failing on a different day, or relying on local file paths.
**Self-Validating**: Tests should programmatically determine pass/fail. Violation: A test that uses `console.log()` to print a result and requires the developer to manually read the terminal output to confirm correctness. Tests should have clear boolean outputs (pass/fail).
**Thorough**: Tests should cover edge cases and failure paths. Violation: A test for a division function that only checks `divide(10, 2)` but completely ignores the `divide(10, 0)` edge case, leaving runtime crashes untested.

**Q6: What is BDD? How does the Given-When-Then structure map to test setup/action/assertion? When would you use Cucumber/Gherkin over plain Jest?**
Behavior-Driven Development (BDD) is an agile software development practice that encourages collaboration among developers, QA, and non-technical or business participants in a software project.
It focuses on the behaviors a system should exhibit, expressed in plain language. The Given-When-Then structure maps directly to the standard Arrange-Act-Assert testing pattern:
"Given" represents the test setup or initial state (Arrange). For example, "Given the user is logged in".
"When" represents the action being taken by the user or system (Act). For example, "When the user clicks the checkout button".
"Then" represents the expected outcome or assertion (Assert). For example, "Then the cart should be emptied".
Cucumber and Gherkin allow these scenarios to be written in human-readable files that are parsed to execute test code.
You would use Cucumber/Gherkin in environments where domain experts, product managers, or regulatory bodies need to read, write, or approve the exact acceptance criteria as living documentation. The overhead is not worth it for purely technical tests or small teams where developers and product owners already have a tight, shared understanding without the extra translation layer.

**Q7: What is a flaky test? Name 5 common causes and their specific fixes.**
A flaky test is a test that sometimes passes and sometimes fails without any changes to the underlying code. They destroy trust in the test suite and CI pipeline.
Five common causes and their fixes:
1. **Timing/Async issues**: Using hardcoded `setTimeout` to wait for UI updates. Fix: Use testing library's `waitFor` or explicit `await` on promises to deterministically wait for elements.
2. **Shared mutable state**: Tests mutating a global variable or shared module state. Fix: Use `beforeEach` to reset the state or initialize fresh instances of objects per test.
3. **Test order dependency**: A test relies on side effects from previous tests. Fix: Ensure complete test isolation; randomized test execution orders can help uncover these.
4. **Network calls**: Making actual HTTP requests to external APIs that might timeout or rate limit. Fix: Use tools like Mock Service Worker (MSW) or Nock to mock network boundaries reliably.
5. **Date/Time dependency**: Code behavior changes based on current system time. Fix: Use dependency injection to pass a clock instance, or use `jest.useFakeTimers()` to freeze time during test execution.

**Q8: Explain the difference between branch coverage and line coverage. Construct an example function where line coverage is 100% but branch coverage is only 50%.**
Line coverage simply counts whether a specific line of code was executed during a test run. Branch coverage tracks whether every possible path through control structures (like `if`, `switch`, or logical operators) was executed.
Consider this single-line function:
```javascript
function greet(name) {
  return "Hello, " + (name || "Guest") + "!";
}
```
If we write one test:
```javascript
test('greets name', () => { 
  expect(greet("Alice")).toBe("Hello, Alice!"); 
});
```
This test achieves 100% line coverage because the single line of the function executed. However, branch coverage is only 50% because the logical OR operator `||` created an implicit branch. The right side of the `||` ("Guest") was never evaluated.
Branch coverage catches more bugs because it forces developers to test the fallback conditions, default parameters, and error handling paths that simple line coverage often ignores. Coverage tools like Istanbul report these metrics separately to highlight untested logical paths.

**Q9: Why is testing implementation details an anti-pattern? What should you test instead? Give an example of a test refactored from implementation-detail to behaviour-focused.**
Testing implementation details means writing assertions against the internal state, private methods, or specific internal function calls of a module or component, rather than its public API.
This is an anti-pattern because it tightly couples the tests to the current architecture. If you refactor the code to improve its structure while keeping the external behavior identical, implementation-detail tests will break (false negatives).
Instead, you should test observable behaviors: given specific inputs, what are the outputs? For UI, given user interactions, what is rendered?
**Before (Implementation Detail):**
```javascript
test('sorts array', () => {
  const instance = new Sorter();
  const spy = jest.spyOn(instance, 'quickSort');
  instance.sort([3, 1, 2]);
  expect(spy).toHaveBeenCalled(); // Fails if refactored to mergeSort
});
```
**After (Behavior-Focused):**
```javascript
test('sorts array', () => {
  const instance = new Sorter();
  const result = instance.sort([3, 1, 2]);
  expect(result).toEqual([1, 2, 3]); // Passes regardless of algorithm
});
```
This ensures tests remain useful during refactoring rather than becoming a hindrance.

**Q10: What is the difference between a unit test and an integration test? Construct a concrete scenario where a unit test passes but an integration test catches a real bug.**
A unit test verifies the behavior of a single, isolated piece of code (a function or class). All external dependencies, such as databases, network calls, or even other complex classes, are mocked.
An integration test verifies that multiple units, modules, or services work together correctly. It uses real dependencies where practical to test the interaction boundaries.
Scenario:
You have a `UserService` that calls a `UserRepository`.
In your unit test for `UserService`, you mock `UserRepository` to return `{ userId: 123, userName: 'Alice' }`. The service formats this and returns successfully. The unit test passes.
However, in the real application, the PostgreSQL driver returns snake_case column names. The real `UserRepository` queries the database and gets `{ user_id: 123, user_name: 'Alice' }`.
The `UserService` fails to find `userId` and throws an error. The unit test missed this because the mock assumed the wrong contract. An integration test running against a real test database would catch this field name mismatch immediately, proving that the units communicate correctly.

**Q11: How do you test code that depends on the current time (Date.now() or new Date())? Describe two distinct approaches with code examples.**
Code depending on current time is notoriously hard to test because the environment changes continuously, leading to flaky tests if not handled correctly.
**Approach 1: Dependency Injection**
You alter the function signature to accept a time-provider.
```javascript
// Production code
function isExpired(expiryDate, now = () => Date.now()) {
  return now() > expiryDate;
}

// Test
test('detects expiry', () => {
  const past = new Date('2020-01-01').getTime();
  const mockNow = () => new Date('2020-01-02').getTime();
  expect(isExpired(past, mockNow)).toBe(true);
});
```
This is highly explicit and architecturally clean, but pollutes signatures.
**Approach 2: Global Mocking (Fake Timers)**
Test frameworks like Jest can intercept the global Date object.
```javascript
// Test
test('detects expiry', () => {
  jest.useFakeTimers();
  jest.setSystemTime(new Date('2020-01-02'));
  const past = new Date('2020-01-01').getTime();
  
  expect(isExpired(past)).toBe(true); // internally uses Date.now()
  jest.useRealTimers();
});
```
This requires no changes to the production code signature, but manipulates the global environment which requires careful cleanup to prevent polluting other tests.

**Q12: What is test isolation? Why should tests not share mutable state? Explain how beforeEach, afterEach, beforeAll, and afterAll differ in when they run.**
Test isolation is the principle that the outcome of one test should never be affected by the execution or state of another test.
Tests must not share mutable state because it causes "cascade failures" and flaky test suites. If Test A mutates a global variable and fails to clean it up, Test B might fail unexpectedly. Running Test B in isolation might pass, making the bug incredibly difficult to trace.
Framework hooks manage this lifecycle:
`beforeAll` runs exactly once before any test in the file/block starts. Use this for expensive, immutable setup.
`beforeEach` runs repeatedly, right before every single test. Use this to ensure state is fresh for every test.
`afterEach` runs repeatedly, right after every single test. Use this to clean up mocks or DOM nodes.
`afterAll` runs exactly once after all tests in the file/block have finished. Use this to close database connections.
Moving mutable setup from `beforeAll` to `beforeEach` is the standard fix for state leakage bugs in test suites.

**Q13: What is a smoke test? How is it different from a regression test and an acceptance test? When is each run in a CI/CD pipeline?**
A smoke test is a shallow, broad test suite designed to verify that the most critical functions of a system are working, usually executed immediately after a deployment. It checks if the app starts, connects to the database, and exposes healthy endpoints.
A regression test is specifically written to ensure that previously fixed bugs do not reappear. It "locks in" the correct behavior to prevent backsliding.
An acceptance test verifies that the software meets the business requirements and specifications, often written in business-readable language (like Gherkin) and focused on user journeys.
In a CI/CD pipeline:
1. Regression tests run during the CI phase on every Pull Request to prevent merging broken code.
2. Acceptance tests run as a release gate, often in a staging environment, to ensure the feature is ready for users before merging to main.
3. Smoke tests run in the CD phase, immediately after deployment to production or staging, acting as a quick sanity check before routing live traffic to the new instances.

**Q14: What is contract testing (Pact)? What microservices problem does it solve that integration tests cannot catch until production?**
Contract testing is a methodology used to ensure that two separate systems (such as a frontend SPA and a backend microservice, or two microservices) are compatible and can communicate with each other.
The microservice deployment mismatch problem occurs when services are deployed independently. Suppose the API changes a field from `user_id` to `userId`. If the frontend is not updated, it will break in production. Traditional integration tests against a shared staging environment might not catch this if the staging environment doesn't perfectly mirror the specific version pairing being deployed.
Tools like Pact solve this using a Consumer-Driven Contracts approach. The consumer (frontend) writes tests defining exactly what requests it sends and what responses it expects. This generates a "contract" (JSON file).
The contract is published to a Pact Broker. The provider (backend) then pulls this contract and runs verification tests against its own code. If the provider breaks the contract, the provider's CI fails, preventing a deployment that would break the consumer.

**Q15: How do you decide which parts of a codebase to test first when joining a legacy project with no tests? Describe a risk-based prioritisation approach.**
Adding tests to a completely untested legacy project is daunting. A risk-based prioritization approach calculates risk as: Likelihood of Change × Impact of Failure.
First, identify the high-impact areas: payment processing, authentication, data mutation logic, and public API contracts. A failure here costs money or reputation.
Next, find the frequently changed files. Using `git log --follow` or code churn analysis tools can reveal the "hotspots" where developers are actively making changes.
Where churn and impact intersect is your highest priority.
Start with "characterization tests" for these areas. These tests don't assert that the behavior is correct, but rather document what the code currently does, creating a safety net for refactoring.
Prioritize integration tests at the boundaries (e.g., API endpoints) because they provide the highest coverage for the lowest mocking effort. Finally, add unit tests for pure business logic functions (like complex calculations) that are isolated and change frequently.

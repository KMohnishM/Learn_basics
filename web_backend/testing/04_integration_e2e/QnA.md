# Integration and E2E Testing QnA

**Q1: What is the difference between unit and integration testing for a REST API endpoint? What specific bugs does Supertest catch that Jest unit tests with mocked repositories cannot?**
A unit test for an API endpoint typically isolates the controller logic, mocking out the HTTP request/response objects (like Express `req` and `res`) and the database layer. It tests logic like "if service throws, return 500".
An integration test spins up the actual web framework and often a real test database, testing the entire slice from route definition down to data persistence.
Tools like Supertest allow you to make HTTP requests against your app without starting a listening server.
Supertest catches integration bugs that mocks hide:
- Middleware order issues (e.g., accessing `req.body` before the JSON body-parser is mounted).
- Route matching errors (e.g., a regex typo in the route path).
- Serialization issues (e.g., trying to send a cyclic object via `res.json()`).
- Database schema mismatches (e.g., trying to insert a string into a database column defined as integer).
Testing the whole slice provides much higher confidence than isolated unit tests.

**Q2: What is Testcontainers? What problem does a shared development database create for integration tests that Testcontainers solves?**
Testcontainers is a library (available in JS, Java, Python) that provides lightweight, throwaway instances of common databases, message brokers, or anything else that can run in a Docker container.
A shared development database creates huge test isolation problems. If Developer A runs tests that insert users, and Developer B runs tests on the same DB that count users, tests will fail unpredictably. Parallel CI runs are impossible because they trip over each other's state.
Testcontainers solves this by dynamically spinning up a completely fresh, isolated Docker container for your specific test session (e.g., a PostgreSQL container), running the tests against it, and destroying it immediately after. This guarantees an ephemeral, pristine environment that perfectly matches production versions without maintaining a permanent test database cluster.
It abstracts away complex Docker setup, managing it via code within your test suite setup.

**Q3: What is Mock Service Worker (MSW)? How does it intercept requests at the network level differently from mocking `fetch` directly? Why is it more realistic?**
Mock Service Worker (MSW) is an API mocking library that uses Service Workers (in the browser) or Node.js interceptors to intercept actual network requests.
When you mock `fetch` using `jest.fn()`, you replace the browser's native API. This can break code that relies on specific `Response` object behaviors, headers, or streams. It also requires heavy boilerplate and doesn't work if your app switches from `fetch` to `axios`.
MSW leaves `fetch` and `axios` entirely intact. The app makes a real network request, but MSW intercepts it at the network level and returns a mocked response.
This is much more realistic because your application code executes exactly as it would in production. It processes the actual Response object, handles CORS headers realistically, and makes it incredibly easy to share mock definitions between browser UI development and Node.js integration tests.

**Q4: Explain the Page Object Model (POM) pattern in Playwright. What belongs in a Page Object class vs the test file? How does it reduce maintenance cost?**
The Page Object Model (POM) is an E2E design pattern where you encapsulate the UI elements and interactions of a specific web page into a single class.
The Page Object class contains the CSS/Role selectors (e.g., `this.loginButton = page.getByRole('button', {name: 'Login'})`) and the interaction methods (e.g., `async login(user, pass) { ... }`). It should NOT contain test assertions (`expect`).
The Test File contains the actual test logic, calling methods on the Page Object and asserting on the results.
```javascript
// Test file
test('user can log in', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.login('user', 'password');
  expect(await loginPage.isLoggedIn()).toBeTruthy();
});
```
This reduces maintenance cost drastically. If the design changes and the "Login" button changes to a different selector, you only update it in ONE place (the Page Object class), rather than updating 50 different test files that click that button.

**Q5: How does Playwright's auto-wait mechanism work? What conditions does it wait for by default? How is it different from `await page.waitForTimeout(2000)`?**
Playwright's auto-wait mechanism automatically waits for elements to be "actionable" before performing interactions like `.click()` or `.fill()`.
By default, before clicking an element, Playwright checks that the element is:
1. Attached to the DOM.
2. Visible (not hidden by CSS).
3. Stable (not animating or moving).
4. Receives Events (not obscured by a modal overlay).
5. Enabled (not `disabled`).
This is fundamentally different from `await page.waitForTimeout(2000)` (a hard sleep). Hard sleeps are terrible because they make tests slow (waiting 2 seconds even if the UI loads in 10ms) and flaky (failing if the CI server is slow and takes 3 seconds). Auto-wait makes tests fast and reliable by polling the DOM and proceeding the exact millisecond the element is ready.

**Q6: What is a test factory (e.g., `UserFactory.create()`)? Why is it better than manually inserting raw SQL or hardcoded fixtures?**
A test factory (often built with libraries like Fishery or Rosie) is a pattern for generating test data programmatically. You define a blueprint with default values (often randomized) and override specific fields when needed.
```javascript
const user = await UserFactory.create({ role: 'admin' });
// Generates: { id: 1, name: 'random_name', email: 'x@x.com', role: 'admin' }
```
This is significantly better than raw SQL or hardcoded JSON fixtures because:
1. **Resilience to schema changes**: If a new required column `status` is added to the database, you only update the Factory definition, not hundreds of SQL scripts.
2. **Intent revealing**: When a test says `UserFactory.create({ role: 'admin' })`, it highlights that the *only* important field for this test scenario is the role. Hardcoded fixtures hide this intent among dozens of irrelevant fields.
3. **Uniqueness**: Factories can use libraries like Faker to ensure unique emails per generated user, preventing database unique constraint violations during parallel test runs.

**Q7: How do you handle test database isolation in integration tests? Compare three strategies: truncate after each test, rollback transaction per test, separate database per worker.**
1. **Truncate tables**: Run `DELETE FROM table` or `TRUNCATE` after every test. Pros: Simple to implement. Cons: Slow, as it requires hitting the disk. Foreign key constraints can make truncation order complex.
2. **Rollback transaction**: Wrap every test in a database transaction and `ROLLBACK` at the end instead of committing. Pros: Extremely fast because nothing is written to disk. Cons: Cannot easily test application code that explicitly manages its own transactions, and setup can be tricky across connection pools.
3. **Separate database per worker**: During parallel execution (e.g., in Jest or Playwright), each worker gets its own isolated database schema (db_worker_1, db_worker_2). Pros: True isolation, allowing full parallel execution without lock contention or data collision. Cons: High initial setup overhead and memory consumption.
The best practice is usually separating databases per worker for parallelism, and using table truncation or transactions within the worker for per-test isolation.

**Q8: What does Playwright's `trace` capture? How do you enable it on first retry and how do you view the trace file to debug a failure?**
Playwright's trace viewer is an incredibly powerful debugging tool. It captures a comprehensive record of a test execution, including DOM snapshots at every action, network requests, console logs, and action timelines. It essentially lets you "time travel" through the failed test visually.
You enable it in `playwright.config.ts`:
```javascript
use: {
  trace: 'on-first-retry',
}
```
This configuration keeps CI fast by default, but if a test fails and automatically retries, it turns on full tracing for the retry to capture the flakiness.
When the test fails, Playwright outputs a `trace.zip` file. You can view it locally or in CI by running:
`npx playwright show-trace trace.zip` or uploading the zip to `trace.playwright.dev`. It opens a specialized UI showing exactly what the page looked like before and after the failure.

**Q9: What does `server.use()` do in MSW during a test? How does `server.resetHandlers()` in `afterEach` prevent handler leakage between tests?**
In MSW, you define baseline network mock handlers when setting up the server. However, individual tests often need to override these baselines (e.g., forcing a 500 server error to test error boundaries).
`server.use()` allows you to prepend one-off request handlers at runtime for a specific test.
```javascript
test('handles server error', () => {
  server.use(
    rest.get('/api/data', (req, res, ctx) => res(ctx.status(500)))
  );
  // UI test logic here
});
```
If you don't clean this up, the 500 error handler will "leak" into the next test, causing it to fail unexpectedly. Calling `server.resetHandlers()` in the `afterEach` hook wipes out any overrides added by `server.use()`, returning the mock server precisely to its baseline state, ensuring perfect test isolation.
This guarantees each test remains independent regardless of execution order.

**Q10: Why should Playwright tests use `getByRole` and `getByLabel` instead of CSS selectors like `.submit-btn`? What accessibility standard do role-based selectors align with?**
Testing libraries strongly advocate for user-centric selectors. A user doesn't interact with a CSS class `.submit-btn` or an ID `#login`; they interact with a "button" that says "Submit".
Using `page.getByRole('button', { name: 'Submit' })` tests the application the way an assistive technology (like a screen reader) or a human does.
This aligns perfectly with WAI-ARIA (Web Accessibility Initiative - Accessible Rich Internet Applications) standards.
If you use CSS selectors, your test might pass even if the button is completely inaccessible (e.g., using a `<div>` styled to look like a button without proper ARIA roles). By using `getByRole`, your E2E tests implicitly act as baseline accessibility tests. Furthermore, CSS classes change frequently during styling refactors, breaking tests. Roles and labels rarely change, making tests much more resilient.

**Q11: Compare Cypress and Playwright architectures. What does "runs inside the browser" (Cypress) vs "controls externally via CDP" (Playwright) mean for debugging and browser support?**
Cypress architecture injects your test code directly into the browser context alongside your application. It runs in the same event loop.
- **Debugging (Cypress)**: Excellent because you can use native browser dev tools intuitively, drop a `debugger` in your app code, and inspect everything synchronously.
- **Limitations**: Because it's inside the browser, it struggles with multi-tab scenarios, cross-origin iFrames, and handling native browser dialogs.
Playwright operates externally via the Chrome DevTools Protocol (CDP) for Chromium, communicating via WebSockets.
- **Debugging (Playwright)**: Reliant on its external Trace Viewer and Inspector UI, though still very powerful.
- **Advantages**: It has total control over the browser. It effortlessly handles multiple tabs, multiple browser contexts (simulating two different users logging in simultaneously), cross-origin boundaries, native file uploads, and offers excellent multi-browser support (WebKit, Firefox, Chromium).

**Q12: What are 5 root causes of flaky E2E tests specific to browser automation? For each, give the recommended fix.**
1. **Third-party APIs**: E2E tests failing because an external analytics or payment service is slow or down. Fix: Stub external domains at the network level using Playwright's `route` or MSW.
2. **Animations/Transitions**: Assertions running while a CSS fade animation is midway, causing elements to not be fully visible. Fix: Disable CSS animations globally in the testing environment configuration.
3. **Implicit race conditions**: Verifying UI state before an API response is fully processed. Fix: Explicitly await the API response using `page.waitForResponse('/api/data')` before asserting on the DOM.
4. **Data collisions**: Tests failing because they attempt to register the same static email address `test@test.com` simultaneously in parallel runners. Fix: Use dynamic data generation (Faker/UUIDs) for unique test data.
5. **Slow CI environments**: Hardcoded timeouts triggering because the CI CPU is constrained. Fix: Avoid hardcoded `waitForTimeout`; rely entirely on auto-waiting locators and extend global timeout configurations in CI.

**Q13: How do you configure Playwright's `webServer` option to automatically start and stop your app during tests? What is `reuseExistingServer` for?**
Playwright can manage the lifecycle of your local development server, eliminating the need to manually run `npm run dev` in one terminal before running `npm run test:e2e` in another.
In `playwright.config.ts`:
```javascript
webServer: {
  command: 'npm run dev',
  url: 'http://localhost:3000',
  timeout: 120 * 1000,
  reuseExistingServer: !process.env.CI,
}
```
Playwright runs the `command`, waits for the `url` to return a 2xx HTTP status, and then begins the tests. After the tests, it shuts down the server.
The `reuseExistingServer` option is vital for local developer experience. If set to `true`, Playwright checks if port 3000 is already active. If you already have your dev server running, Playwright skips the `command` and just uses the active server, saving startup time. In CI, it's usually `false` to ensure a clean start.

**Q14: What is `cy.intercept()` in Cypress? Show how to both stub a response and assert on the outgoing request body in the same test.**
`cy.intercept()` allows Cypress to spy on or stub network requests made by the application. It operates at the browser level.
You can use it to mock an API response to force the UI into a specific state, or to spy on a real request to verify that the frontend sent the correct payload to the backend.
```javascript
it('submits user data correctly', () => {
  // Intercept the POST request and alias it as 'createUser'
  cy.intercept('POST', '/api/users', { 
    statusCode: 201, 
    body: { id: 1, success: true } 
  }).as('createUser');

  // Trigger UI action
  cy.get('[data-cy=submit]').click();

  // Wait for the specific intercepted request
  cy.wait('@createUser').then((interception) => {
    // Assert on the outgoing payload
    expect(interception.request.body).to.deep.equal({
      name: 'Alice',
      role: 'admin'
    });
  });
});
```
This dual utility makes it indispensable for complete workflow testing.

**Q15: How should unit, integration, and E2E tests be ordered in a CI pipeline? Why should E2E tests only run if integration tests pass? What artifact do you upload on E2E failure?**
CI pipelines should follow a "fail fast" methodology. Tests are ordered by execution speed and diagnostic precision:
1. **Linting and Type Checking** (Seconds)
2. **Unit Tests** (Seconds/Minutes)
3. **Integration Tests** (Minutes)
4. **E2E Tests** (Many Minutes)
E2E tests should ONLY run if integration tests pass because E2E tests are expensive (compute heavy) and slow. If a unit test fails because a basic function is broken, the E2E test will definitely fail anyway, but it will take 10 minutes to tell you instead of 10 seconds. Furthermore, E2E failures are harder to debug; unit test failures point you exactly to the broken line of code.
When E2E tests fail in CI, you MUST upload the failure artifacts. In Playwright, this means configuring the CI workflow (e.g., GitHub Actions) to upload the `playwright-report/` directory, which contains HTML reports, screenshots, videos, and trace zip files, making debugging remote failures possible.

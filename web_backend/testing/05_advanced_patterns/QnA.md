# Advanced Testing Patterns QnA

**Q1: Explain the core RTL philosophy. What does "test what the user sees, not how it works internally" mean? Give a before/after example of a test refactored from implementation detail to behaviour.**
The core philosophy of React Testing Library (RTL) is that tests should interact with the application in the same way the user does. "Test what the user sees, not how it works internally" means you should not assert on state variables, component props, or instance methods. Users don't know what a prop is; they only know they clicked a button and a success message appeared.
Testing implementation details leads to brittle tests that break during refactoring even if the app works perfectly.
**Before (Enzyme - Implementation Detail):**
```javascript
test('increments counter', () => {
  const wrapper = shallow(<Counter />);
  // Tightly coupled to the exact state variable name 'count'
  wrapper.setState({ count: 1 });
  expect(wrapper.state().count).toBe(1);
});
```
**After (RTL - Behavior):**
```javascript
test('increments counter', () => {
  render(<Counter />);
  // User interacts with a button
  userEvent.click(screen.getByRole('button', { name: /increment/i }));
  // User observes the text change
  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```
The RTL approach ensures UI refactors do not break reliable tests.

**Q2: What is the priority order of RTL query methods? Why is `getByRole` preferred over `getByTestId`? What ARIA role does a `<button>` have?**
RTL defines a strict priority list for queries to encourage accessible testing:
1. Queries accessible to everyone: `getByRole`, `getByLabelText`, `getByPlaceholderText`, `getByText`.
2. Semantic queries: `getByAltText`, `getByTitle`.
3. Test IDs: `getByTestId`.
`getByRole` is the absolute highest priority because it ensures your UI is accessible. It verifies not just that the text exists, but that the element has the correct semantic meaning in the DOM tree, which is vital for screen readers.
`getByTestId` is a last resort. It should only be used when an element has no dynamic text or semantic role (e.g., testing dynamic SVG animations or purely visual wrappers). Overusing `data-testid` clutters production code and ignores accessibility.
A `<button>` element inherently has the ARIA role of `button`. A `<a>` tag with an href has the role of `link`.

**Q3: How do you test a custom React hook with `renderHook`? What does `act()` do and why is it required when calling hook functions that trigger state updates?**
To test custom hooks in isolation (without mounting a dummy component), RTL provides `renderHook`.
```javascript
import { renderHook, act } from '@testing-library/react';
import useCounter from './useCounter';

test('should increment', () => {
  const { result } = renderHook(() => useCounter());
  
  act(() => {
    result.current.increment();
  });
  
  expect(result.current.count).toBe(1);
});
```
The `act()` function ensures that all state updates, effects, and DOM renders related to the interaction are completely finished before moving to the next line of code (the assertion). React automatically batches updates; `act()` forces React to flush those batches synchronously for the test. If you call a state-updating hook function without wrapping it in `act()`, React will log a warning indicating that your test might assert before the state has actually settled, leading to false negatives.

**Q4: Explain Pact contract testing. What is a consumer test, what is a Pact file, what is provider verification, and what is the Pact Broker?**
Pact is a consumer-driven contract testing framework.
- **Consumer Test**: The frontend (consumer) writes a test asserting that if it makes a specific request, it expects a specific response. During this test, a mock server records this expectation.
- **Pact File**: When the consumer test passes, the mock server generates a JSON "Pact file" (the contract) that documents the exact requests and expected responses.
- **Pact Broker**: This contract is published to the Pact Broker, a central registry and repository that tracks which versions of the consumer expect which contracts from which versions of the provider.
- **Provider Verification**: The backend (provider) pulls the contract from the Broker. Pact automatically replays the recorded requests against the real backend service and verifies that the real responses match the contract expectations. If it matches, the contract is fulfilled.
This process ensures backwards compatibility safely.

**Q5: What problem does contract testing solve that a shared integration test environment cannot? Describe the deployment mismatch scenario in a microservices context.**
Shared integration environments suffer from data pollution, flakiness, and they only test "latest vs latest" code.
The deployment mismatch scenario: Suppose Consumer V1 is running in production, relying on an API field called `user_id`. The Provider team decides to rename it to `userId` and updates Provider to V2.
If they deploy Provider V2 to production before Consumer V2 is deployed, the production system breaks immediately.
Integration tests on a staging server won't catch this if staging has Consumer V2 and Provider V2 running together—they perfectly match!
Contract testing with a Pact Broker tracks *deployment environments*. The Provider pipeline checks "Can Provider V2 safely deploy alongside whatever Consumer version is currently marked as 'production'?". The Broker looks at the Consumer V1 contract, sees the `user_id` expectation, and correctly fails the Provider V2 build, preventing a production outage.

**Q6: What is property-based testing? How is it different from example-based testing? What is shrinking and why is it valuable?**
Standard testing is example-based: you provide specific inputs (`add(2, 2)`) and expect specific outputs (`4`). You might miss edge cases.
Property-based testing (using tools like `fast-check` in JS or `hypothesis` in Python) tests the *properties* or rules of a function against hundreds of randomly generated inputs. For example, testing `reverse(array)`: a property is "reversing an array twice returns the original array".
```javascript
import fc from 'fast-check';

test('reversing twice is identity', () => {
  fc.assert(
    fc.property(fc.array(fc.integer()), arr => {
      expect(arr.reverse().reverse()).toEqual(arr);
    })
  );
});
```
When property-based testing finds a failing input (e.g., an array of 50 complex objects), it performs "shrinking". Shrinking is the process of iteratively simplifying the failing input (removing elements, reducing numbers towards zero) to find the absolute minimum, simplest possible input that still triggers the bug. This makes debugging massively easier.

**Q7: What is mutation testing? How is mutation score calculated? What is a survived mutant and what does it reveal about your test suite?**
Mutation testing evaluates the quality of your test suite by deliberately inserting bugs into your production code and checking if your tests fail.
A mutation testing tool (like Stryker) alters a statement (e.g., changing `if (a < b)` to `if (a <= b)`). This mutated version is a "mutant".
If you run the test suite and a test fails, the mutant is "killed" (this is good!).
If the test suite passes, the mutant "survived" (this is bad!).
A survived mutant reveals a blind spot in your test suite. It means you wrote code that executes, but you forgot to write an assertion for that specific behavior or boundary condition.
Mutation score is calculated as: `(Killed Mutants / Total Valid Mutants) * 100`. It is a much more rigorous metric than line coverage, guaranteeing test efficacy.

**Q8: How do you configure Stryker for a TypeScript Jest project? What do `thresholds.high`, `thresholds.low`, and `thresholds.break` do?**
You install Stryker and generate a `stryker.conf.json` file. For a TS Jest project, you configure the test runner and transpiler:
```json
{
  "$schema": "./node_modules/@stryker-mutator/core/schema/stryker-schema.json",
  "testRunner": "jest",
  "coverageAnalysis": "perTest",
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts"],
  "thresholds": {
    "high": 80,
    "low": 60,
    "break": 50
  }
}
```
The thresholds define the quality standards for your CI pipeline:
- `high` (80): If the score is >= 80, the report prints in green (excellent).
- `low` (60): If the score is between 60 and 80, it prints in yellow (warning).
- `break` (50): If the score falls below 50, Stryker exits with a non-zero exit code, explicitly failing your CI build to prevent merging poorly tested code. This prevents test suite degradation.

**Q9: What is k6? What is the difference between virtual users (VUs) and requests per second? Why is VU-based load testing more realistic for real user behaviour?**
k6 is a modern load-testing tool designed by Grafana, scripted in JavaScript, designed to evaluate backend performance under stress.
Requests Per Second (RPS) measures raw throughput—firing a specific number of HTTP requests blindly every second regardless of response times.
Virtual Users (VUs) simulate independent, concurrent actors. A VU executes a script top-to-bottom in a loop. If a backend gets slow, the VU waits for the response before proceeding to the next request in its script.
VU-based load testing is much more realistic because it mimics actual human and browser behavior. A real user clicks "Submit", waits for the page to load, reads it (think time), and then clicks the next link. If your server slows down, the rate of incoming requests from real users naturally decreases as they wait. RPS testing doesn't care; it just overwhelms the server infinitely, leading to unrealistic cascade failures.

**Q10: Explain the `stages` configuration in k6. What does a ramp-up → sustain → ramp-down profile test that a flat load profile does not?**
The `stages` configuration in k6 allows you to dynamically change the number of Virtual Users over time.
```javascript
export const options = {
  stages: [
    { duration: '1m', target: 50 }, // Ramp-up
    { duration: '3m', target: 50 }, // Sustain
    { duration: '1m', target: 0 },  // Ramp-down
  ],
};
```
A flat load profile (e.g., instantly starting 50 VUs) tests raw capacity but rarely reflects real-world traffic.
The Ramp-up phase tests how your infrastructure handles scaling events (e.g., does your auto-scaler trigger in time? Does connection pooling get overwhelmed by a spike?).
The Sustain phase ensures the system doesn't degrade over time due to memory leaks or saturated queues.
The Ramp-down phase tests recovery. If your system crashed or degraded under load, does it successfully recover and resume normal operation when the traffic subsides, or does it require a manual restart?

**Q11: What does `@testing-library/user-event` provide that `fireEvent` does not? Why does `userEvent.type` simulate real browser input more accurately?**
`fireEvent` is a lightweight wrapper around the browser's native `dispatchEvent` API. It dispatches a single DOM event.
`userEvent` is a higher-level library that simulates full user interactions, dispatching the complete sequence of events that a real browser would trigger.
For example, when a user types into an input field, `fireEvent.change(input, {target: {value: 'a'}})` just fires one `change` event.
However, `userEvent.type(input, 'a')` fires:
1. `pointerover`, `pointerenter`, `mouseover`, `mouseenter`, `mousemove`
2. `mousedown`, `focus`, `mouseup`, `click` (selecting the input)
3. `keydown`, `keypress`, `input`, `keyup` (for the letter 'a')
This catches bugs that `fireEvent` misses. For example, if you have a `onKeyDown` handler that prevents certain characters, `fireEvent.change` will bypass it entirely and artificially pass the test, whereas `userEvent.type` will correctly trigger the handler and fail appropriately.

**Q12: How does visual regression testing work in Playwright? What is the pixel `threshold` parameter? How do you update a baseline snapshot after a legitimate UI change?**
Visual regression testing involves taking a screenshot of a web page or component during test execution and comparing it pixel-by-pixel against a previously saved "baseline" image.
In Playwright, you do this with `expect(page).toHaveScreenshot()`.
Because different operating systems and CI environments render fonts and anti-aliasing slightly differently, exact pixel matching is often too strict. The `threshold` parameter (e.g., `maxDiffPixels` or `maxDiffPixelRatio`) allows a specified amount of variance before failing the test, preventing flaky visual failures caused by sub-pixel rendering differences.
When a developer makes an intentional UI change (like changing a button color), the visual test will fail. To accept this new UI, the developer runs Playwright with the update flag: `npx playwright test --update-snapshots`. This overwrites the old baseline images with the new screenshots, which are then committed to version control.

**Q13: How should you structure a CI pipeline for unit, integration, and E2E tests across 3 separate jobs? How do you make E2E depend on integration passing?**
In a CI system like GitHub Actions, you structure jobs strategically to optimize time and resources.
```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps: [checkout, setup-node, run jest-unit]
    
  integration-tests:
    needs: [unit-tests] # Waits for unit tests to pass
    runs-on: ubuntu-latest
    services: [postgres] # Spins up DB
    steps: [checkout, setup-node, run jest-integration]
    
  e2e-tests:
    needs: [integration-tests] # Waits for integration tests
    runs-on: ubuntu-latest
    steps: [checkout, setup-node, install-playwright, run playwright]
```
You use the `needs` (or `depends_on`) keyword to construct a Directed Acyclic Graph (DAG) for the CI pipeline. This ensures that the expensive E2E tests only provision browsers and execute if the faster integration tests have already proven the backend API is functional, saving compute minutes and providing faster feedback loops for early failures.

**Q14: What is `waitFor` in RTL? Why should you use `waitFor(() => expect(...))` instead of `await somePromise` when asserting on async UI updates?**
`waitFor` is a utility in React Testing Library used to assert on asynchronous UI changes. It repeatedly executes a callback function containing assertions until they pass, or until a timeout is reached.
You should use `waitFor` because UI updates are often decoupled from specific promises. For example, clicking a button might fire a Redux action, trigger an API call, update a reducer, and finally trigger a React re-render.
If you just `await somePromise` (if you even have access to it in the test), you might resume execution before React has finished painting the DOM.
```javascript
// Await the DOM state, not implementation details
await waitFor(() => {
  expect(screen.getByText('Data Loaded')).toBeInTheDocument();
});
```
This polls the DOM deterministically. It keeps your tests resilient to internal asynchronous implementation details and focuses strictly on verifying when the user can finally see the result.

**Q15: How do you test a React component that requires a Context Provider? Show a custom `renderWithProviders` wrapper and explain why it avoids repeating Provider setup in every test.**
React components deep in the tree often rely on global Contexts (Theme, Redux, Router). If you `render(<Button />)` in isolation, it will crash because the Context is missing.
Instead of wrapping every single test render in layers of Providers, you create a custom render function.
```javascript
import { render } from '@testing-library/react';
import { ThemeProvider } from './ThemeContext';
import { AuthProvider } from './AuthContext';

const AllTheProviders = ({ children }) => {
  return (
    <AuthProvider>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </AuthProvider>
  );
};

const renderWithProviders = (ui, options) =>
  render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { renderWithProviders as render };
```
By exporting this custom `render` function from a test utility file, tests can simply import this instead of the default RTL render. It avoids massive code duplication across test files, ensures consistent test environments, and makes adding a new global provider trivial, as you only update the wrapper in one place.

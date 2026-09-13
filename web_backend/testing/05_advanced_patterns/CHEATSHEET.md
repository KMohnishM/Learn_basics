# Module 5: Cheatsheet

## RTL Query Priority Reference

| Query Type | When to use it | Example |
|---|---|---|
| **`getByRole`** | Always start here. Ensures accessibility. | `getByRole('button', { name: /submit/i })` |
| **`getByLabelText`** | Form fields linked via `<label htmlFor="...">`. | `getByLabelText('Email Address')` |
| **`getByPlaceholderText`**| Form fields without labels. | `getByPlaceholderText('Search...')` |
| **`getByText`** | Non-interactive text spans, paragraphs. | `getByText('Welcome back')` |
| **`getByDisplayValue`** | Asserting current form values. | `getByDisplayValue('John Doe')` |
| **`getByAltText`** | Images with alt tags. | `getByAltText('Company Logo')` |
| **`getByTestId`** | Last resort for dynamic/complex DOM trees. | `getByTestId('custom-dropdown-container')` |

## RTL Matchers (`jest-dom`)

```typescript
expect(element).toBeInTheDocument();
expect(element).toBeVisible();          // Fails if display: none or opacity: 0
expect(element).toBeDisabled();         // Good for loading buttons
expect(element).toHaveTextContent(/error/i);
expect(element).toHaveClass('active');
expect(element).toHaveValue('React');   // For input elements
expect(element).toHaveAttribute('href', '/dashboard');
```

## `renderHook` and `act` Pattern

```typescript
import { renderHook, act } from '@testing-library/react';

// 1. Render the hook
const { result, unmount, rerender } = renderHook((props) => useMyHook(props), {
  initialProps: { id: 1 }
});

// 2. Wrap state-updating actions in act()
act(() => {
  result.current.increment();
});

// 3. Assert on result
expect(result.current.value).toBe(2);
```

## Pact Workflow (ASCII Diagram)

```text
[Frontend Team]                      [Backend Team]
      |                                    |
 1. Write Consumer Test              4. Download Contract
      |                                    |
 2. Generate JSON Contract           5. Run Provider Verification
      |                                    |
 3. Push to Pact Broker -------------→ 6. Test passes? Deploy API!
```

## Stryker Configuration & Commands

```bash
# Install
npm install -D @stryker-mutator/core @stryker-mutator/jest-runner

# Initialize config
npx stryker init

# Run mutation tests
npx stryker run
```

```json
// stryker.config.json thresholds
"thresholds": {
  "high": 80,   // >= 80% Mutation score is Green
  "low": 60,    // 60-79% Mutation score is Yellow
  "break": 50   // < 50% Fails the CI pipeline (Red)
}
```

## k6 Load Testing Options

```javascript
export const options = {
  // Ramp up / Sustain / Ramp down
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 20 },
    { duration: '30s', target: 0 },
  ],
  // Performance requirements
  thresholds: {
    // 99% of requests must complete under 1.5s
    http_req_duration: ['p(99)<1500'],
    // Error rate must be strictly less than 1%
    http_req_failed: ['rate<0.01'],
  },
};
```

## Fast-Check Arbitraries Reference

| Arbitrary | Generates | Example Use Case |
|---|---|---|
| `fc.string()` | Random unicode strings | Testing text inputs |
| `fc.integer()` | Random 32-bit integers | Testing math functions |
| `fc.nat()` | Natural numbers (>=0) | Testing pagination offsets |
| `fc.boolean()` | True or false | Testing toggle states |
| `fc.array(fc.string())` | Array of random strings | Testing list rendering |
| `fc.record({ id: fc.nat() })`| Objects with specific shape | Mocking JSON API responses |
| `fc.emailAddress()` | Valid email formats | Registration form validation |

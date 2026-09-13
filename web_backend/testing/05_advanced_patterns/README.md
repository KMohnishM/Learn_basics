# Module 5: Advanced Testing Patterns

## 1. React Testing Library (RTL)

The guiding principle of React Testing Library (RTL) is encapsulated in its primary axiom: *"The more your tests resemble the way your software is used, the more confidence they can give you."* RTL intentionally avoids providing utilities to inspect a component's internal state or lifecycle methods. Instead, it forces you to interact with your application purely through DOM nodes.

### Setup and Configuration

```bash
npm install --save-dev @testing-library/react @testing-library/user-event @testing-library/jest-dom
```

You must ensure that `@testing-library/jest-dom` is imported in your test setup file. This library extends Jest's `expect` matchers with DOM-specific assertions like `toBeVisible()`, `toBeDisabled()`, and `toHaveTextContent()`.

```typescript
// jest.setup.ts
import '@testing-library/jest-dom';
```

### Complex Component Test Example

Testing a login form that interacts with an external service, manages internal loading state, and renders error messages.

```typescript
// components/LoginForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';
import { authService } from '../services/authService';

// Mock the external dependency completely
jest.mock('../services/authService');
const mockLogin = authService.login as jest.Mock;

describe('LoginForm', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mockLogin.mockClear();
  });

  it('submits form with correct credentials', async () => {
    const onSuccess = jest.fn();
    mockLogin.mockResolvedValue({ token: 'jwt-token' });

    render(<LoginForm onSuccess={onSuccess} />);

    // Interact like a user
    await user.type(screen.getByLabelText(/email/i), 'alice@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /log in/i }));

    // Assert side effects
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('alice@example.com', 'password123');
      expect(onSuccess).toHaveBeenCalledWith({ token: 'jwt-token' });
    });
  });

  it('displays error message on invalid credentials', async () => {
    mockLogin.mockRejectedValue(new Error('Invalid credentials'));

    render(<LoginForm onSuccess={jest.fn()} />);

    await user.type(screen.getByLabelText(/email/i), 'alice@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpass');
    await user.click(screen.getByRole('button', { name: /log in/i }));

    // Await the DOM update caused by the async rejection
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid credentials');
    });
  });

  it('disables submit button while loading', async () => {
    // Simulate a slow network response
    mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

    render(<LoginForm onSuccess={jest.fn()} />);

    await user.type(screen.getByLabelText(/email/i), 'alice@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /log in/i }));

    // Button should instantly disable while awaiting response
    expect(screen.getByRole('button', { name: /log in/i })).toBeDisabled();
  });
});
```

### RTL Query Priority Order
To enforce accessibility best practices, always query the DOM in the following priority order:
1. `getByRole`: Identifies elements based on accessibility roles.
2. `getByLabelText`: Primary method for form inputs.
3. `getByPlaceholderText`: Secondary method for inputs.
4. `getByText`: Locates static text content.
5. `getByDisplayValue`: Finds inputs populated with specific values.
6. `getByAltText`: Primarily for images.
7. `getByTitle`: For elements with a title attribute.
8. `getByTestId`: Use only when necessary for highly dynamic elements lacking roles.

---

## 2. Testing Custom React Hooks

Custom hooks encapsulate complex logic. While they are usually tested indirectly via the components that consume them, complex hooks should be tested in isolation using `@testing-library/react`.

```typescript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useCounter } from './useCounter';
import { useUser } from './useUser';

describe('useCounter Hook', () => {
  it('initializes and increments correctly', () => {
    const { result } = renderHook(() => useCounter(0));
    
    expect(result.current.count).toBe(0);

    // Any operation that updates React state MUST be wrapped in act()
    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });
});

// Testing hooks with async dependencies
jest.mock('../services/userService');
const { fetchUser } = require('../services/userService');

describe('useUser Hook', () => {
  it('fetches and returns user data asynchronously', async () => {
    fetchUser.mockResolvedValue({ id: 1, name: 'Alice' });

    const { result } = renderHook(() => useUser(1));

    expect(result.current.isLoading).toBe(true);
    expect(result.current.user).toBeNull();

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.user).toEqual({ id: 1, name: 'Alice' });
    expect(result.current.error).toBeNull();
  });
});
```

---

## 3. Contract Testing with Pact

In a microservice architecture, API breakage is a constant threat. Contract testing via Pact ensures that the consumer (frontend) and provider (backend API) agree on request and response formats without requiring massive, fragile E2E environments.

### The Consumer Test
The frontend developer writes a test stating what they expect the backend to return. Pact generates a JSON file (the "contract").

```typescript
// consumer.pact.test.ts
import { PactV3, MatchersV3 } from '@pact-foundation/pact';
import path from 'path';

const { like, string, integer } = MatchersV3;

const provider = new PactV3({
  consumer: 'WebFrontend',
  provider: 'UserService',
  dir: path.resolve(process.cwd(), 'pacts'),
});

describe('UserService contract', () => {
  it('returns user by ID', () => {
    return provider
      .given('user with ID 1 exists')
      .uponReceiving('a request to get user 1')
      .withRequest({ method: 'GET', path: '/api/users/1' })
      .willRespondWith({
        status: 200,
        body: {
          id: integer(1),
          name: string('Alice'),
          email: string('alice@example.com'),
          role: like('user'),
        },
      })
      .executeTest(async (mockProvider) => {
        // Run frontend fetch against mock provider
        const response = await fetch(`${mockProvider.url}/api/users/1`);
        const user = await response.json();
        expect(user.name).toBe('Alice');
      });
  });
});
```

### The Provider Verification
The backend team downloads the JSON contract from the Pact Broker and verifies their code against it.

```typescript
// provider.pact.test.ts
import { Verifier } from '@pact-foundation/pact';
import path from 'path';

describe('UserService provider verification', () => {
  it('validates the contract from WebFrontend', () => {
    return new Verifier({
      provider: 'UserService',
      providerBaseUrl: 'http://localhost:3001',
      pactUrls: [path.resolve(process.cwd(), 'pacts/WebFrontend-UserService.json')],
      stateHandlers: {
        'user with ID 1 exists': async () => {
          // Setup database state required by contract
          await db('users').insert({ id: 1, name: 'Alice', email: 'alice@example.com' });
        },
      },
    }).verifyProvider();
  });
});
```

---

## 4. Property-Based Testing with fast-check

Traditional tests are "example-based" (testing `2 + 2 = 4`). Property-based testing generates hundreds of random inputs to ensure invariant properties hold true universally.

```typescript
import * as fc from 'fast-check';

describe('Array Sorting Properties', () => {
  test('sort is idempotent (sorting twice equals sorting once)', () => {
    fc.assert(fc.property(fc.array(fc.integer()), (arr) => {
      const sorted = [...arr].sort((a, b) => a - b);
      const sortedTwice = [...sorted].sort((a, b) => a - b);
      expect(sorted).toEqual(sortedTwice);
    }));
  });

  test('reverse is its own inverse', () => {
    fc.assert(fc.property(fc.array(fc.integer()), (arr) => {
      expect([...arr].reverse().reverse()).toEqual(arr);
    }));
  });
});

describe('JSON Serialization', () => {
  test('JSON round-trip preserves data', () => {
    fc.assert(fc.property(
      fc.record({ name: fc.string(), age: fc.nat(), active: fc.boolean() }),
      (obj) => {
        expect(JSON.parse(JSON.stringify(obj))).toEqual(obj);
      }
    ));
  });
});
```

---

## 5. Mutation Testing with Stryker

Code coverage measures if a line was executed, not if it was effectively tested. Stryker mutates your source code (e.g., changes `+` to `-`, removes function calls) and runs your test suite. If the test suite passes, the mutant "survived" (a bad thing).

```json
// stryker.config.json
{
  "$schema": "./node_modules/@stryker-mutator/core/schema/stryker-schema.json",
  "testRunner": "jest",
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts"],
  "reporters": ["html", "clear-text", "progress"],
  "thresholds": {
    "high": 80,
    "low": 60,
    "break": 50
  }
}
```

---

## 6. Performance Testing with k6

Load testing is critical for assessing API behavior under stress. k6 enables developers to script performance tests using JavaScript and run them across parallel virtual users.

```javascript
// load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up traffic
    { duration: '1m', target: 50 },    // Peak load simulation
    { duration: '30s', target: 0 },    // Cooldown phase
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests must resolve < 500ms
    http_req_failed: ['rate<0.01'],    // Error rate must be under 1%
  },
};

export default function () {
  const payload = JSON.stringify({ name: 'Test', email: `user${__VU}${__ITER}@test.com` });
  const params = { headers: { 'Content-Type': 'application/json' } };
  
  const res = http.post('http://localhost:3000/api/users', payload, params);

  check(res, {
    'status is 201': (r) => r.status === 201,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });

  sleep(1); // Simulate human think-time
}
```

---

## 7. Visual Regression Testing with Playwright

CSS changes frequently cause unintended visual side-effects. Playwright captures pixel-perfect baseline images and compares them dynamically during CI runs.

```typescript
// e2e/visual/homepage.spec.ts
import { test, expect } from '@playwright/test';

test('homepage visual regression', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Mask dynamic areas like carousels or timestamps to prevent flake
  await expect(page).toHaveScreenshot('homepage-baseline.png', {
    fullPage: true,
    maxDiffPixelRatio: 0.02,
    mask: [page.getByTestId('dynamic-timestamp')]
  });
});
```

---

## 8. CI/CD Integration

Modern testing mandates automated CI pipelines. This GitHub Actions configuration demonstrates a resilient test funnel where faster tests act as a gateway for slower tests.

```yaml
# .github/workflows/test.yml
name: Test Pipeline
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: root
          POSTGRES_DB: testdb
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:integration
        env:
          DATABASE_URL: postgresql://postgres:root@localhost:5432/testdb

  e2e-tests:
    needs: [unit-tests, integration-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npx playwright test
```

### Section: Testing React Query (TanStack Query)
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useUser } from './useUser';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }, // disable retries in tests
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useUser hook', () => {
  it('fetches and returns user data', async () => {
    server.use(
      http.get('/api/users/1', () =>
        HttpResponse.json({ id: 1, name: 'Alice', email: 'alice@example.com' })
      )
    );

    const { result } = renderHook(() => useUser(1), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toMatchObject({ name: 'Alice' });
  });

  it('sets error state on fetch failure', async () => {
    server.use(
      http.get('/api/users/1', () => HttpResponse.json({ message: 'Not found' }, { status: 404 }))
    );

    const { result } = renderHook(() => useUser(1), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toContain('404');
  });
});
```

### Section: Testing Zustand Stores
```typescript
import { act, renderHook } from '@testing-library/react';
import { useCounterStore } from './counterStore';

// IMPORTANT: reset store state between tests
beforeEach(() => {
  useCounterStore.setState({ count: 0 });
});

describe('Counter store', () => {
  it('initialises with count 0', () => {
    const { result } = renderHook(() => useCounterStore());
    expect(result.current.count).toBe(0);
  });

  it('increments count when increment() is called', () => {
    const { result } = renderHook(() => useCounterStore());
    act(() => { result.current.increment(); });
    expect(result.current.count).toBe(1);
  });

  it('resets count to 0 when reset() is called', () => {
    useCounterStore.setState({ count: 10 });
    const { result } = renderHook(() => useCounterStore());
    act(() => { result.current.reset(); });
    expect(result.current.count).toBe(0);
  });
});
```

### Section: Testing Next.js Applications
```typescript
// Testing Next.js Server Actions
import { createUser } from './actions';
import { db } from '@/lib/db';

jest.mock('@/lib/db');

describe('createUser server action', () => {
  it('creates user and returns success', async () => {
    (db.user.create as jest.Mock).mockResolvedValue({ id: 1, name: 'Alice' });

    const formData = new FormData();
    formData.set('name', 'Alice');
    formData.set('email', 'alice@example.com');

    const result = await createUser({ message: '' }, formData);
    expect(result.message).toBe('User created successfully');
  });
});

// Testing Next.js API Route Handlers
import { GET, POST } from './route';
import { NextRequest } from 'next/server';

describe('GET /api/users', () => {
  it('returns list of users', async () => {
    const request = new NextRequest('http://localhost/api/users');
    const response = await GET(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(Array.isArray(data)).toBe(true);
  });
});

describe('POST /api/users', () => {
  it('creates user from request body', async () => {
    const request = new NextRequest('http://localhost/api/users', {
      method: 'POST',
      body: JSON.stringify({ name: 'Alice', email: 'alice@example.com' }),
      headers: { 'Content-Type': 'application/json' },
    });
    const response = await POST(request);
    expect(response.status).toBe(201);
  });
});
```

### Section: Accessibility Testing in RTL
```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import userEvent from '@testing-library/user-event';

expect.extend(toHaveNoViolations);

describe('Modal component accessibility', () => {
  it('has no axe violations', async () => {
    const { container } = render(<Modal isOpen title="Confirm deletion" onClose={jest.fn()} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('traps focus within modal when open', async () => {
    const user = userEvent.setup();
    render(<Modal isOpen title="Test" onClose={jest.fn()}><button>First</button><button>Last</button></Modal>);

    await user.tab();
    expect(screen.getByText('First')).toHaveFocus();
    await user.tab();
    expect(screen.getByText('Last')).toHaveFocus();
    await user.tab();
    // Focus should wrap back to first focusable element in modal
    expect(screen.getByText('First')).toHaveFocus();
  });

  it('closes on Escape key press', async () => {
    const onClose = jest.fn();
    const user = userEvent.setup();
    render(<Modal isOpen title="Test" onClose={onClose} />);

    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
```

### Section: Measuring and Improving Test Suite Performance
- Identify slow tests: `jest --verbose` shows per-test timing
- Profile test suite: `jest --logHeapUsage` to detect memory leaks in test files
- Module mocking overhead: `jest.mock()` at module level is cheap; avoid `jest.doMock()` inside tests
- Database connection pooling in integration tests: create pool once in `beforeAll`, share across tests
- Parallelisation with `--maxWorkers`: default is 50% of CPU cores; increase for I/O-bound test suites
- Jest projects for running different test types:
```javascript
// jest.config.js
module.exports = {
  projects: [
    {
      displayName: 'unit',
      testMatch: ['<rootDir>/src/**/*.test.ts'],
      testEnvironment: 'node',
    },
    {
      displayName: 'integration',
      testMatch: ['<rootDir>/tests/integration/**/*.test.ts'],
      testEnvironment: 'node',
      testTimeout: 30000,
    },
    {
      displayName: 'components',
      testMatch: ['<rootDir>/src/**/*.component.test.tsx'],
      testEnvironment: 'jsdom',
      setupFilesAfterFramework: ['<rootDir>/jest.setup.ts'],
    },
  ],
};
```
- Run only one project: `jest --selectProjects unit`

# Module 4: Integration and End-to-End (E2E) Testing

## 1. Integration Testing Philosophy

Integration testing is the critical layer of the testing pyramid that sits between fast, isolated unit tests and slow, full-stack End-to-End (E2E) tests. While unit tests focus on individual functions or classes in perfect isolation, integration tests verify that multiple components work together correctly.

### What Integration Tests Catch That Unit Tests Cannot
Unit tests often rely heavily on mocking. If you mock your database query, your unit test will pass even if your SQL syntax is invalid or your ORM configuration is broken. Integration tests are designed to catch:
- ORM query bugs and syntax errors.
- SQL constraint violations (e.g., unique constraints, foreign key violations).
- Middleware interaction bugs (e.g., authentication middleware incorrectly blocking a valid request).
- Serialization and deserialization issues (e.g., date formatting across the network).
- Database transaction failures and rollback logic.

### What Integration Tests Cannot Replace E2E For
Despite their power, integration tests usually bypass the UI layer. They cannot replace E2E tests for:
- Browser rendering issues and CSS layout bugs.
- Complex user flows spanning multiple distinct frontend pages.
- Cross-browser compatibility issues.
- Client-side routing and state management synchronization.

### The Recommended Approach
The modern standard for backend integration testing is to avoid mocking the database. Instead, you should use a real test database. While SQLite in-memory was historically popular for speed, it often masks database-specific bugs (like PostgreSQL's specific JSONB functions or date handling). The recommended approach is to use Testcontainers to spin up a real Dockerized instance of your production database engine (e.g., PostgreSQL, MySQL) specifically for the test suite. This guarantees maximum fidelity.

---

## 2. API Integration Testing with Supertest (Node.js/Express)

Supertest is the industry standard for testing Node.js HTTP servers. It allows you to simulate HTTP requests without actually binding the server to a network port, making tests fast and avoiding port conflicts during parallel test execution.

### Setup

```bash
npm install --save-dev supertest @types/supertest
```

### Full Express App Under Test

First, we construct a representative Express application. It is crucial to separate the application definition from the server instantiation (`app.listen`).

```typescript
// src/app.ts
import express from 'express';
import { userRouter } from './routes/userRouter';
import { errorHandler } from './middleware/errorHandler';
import { authMiddleware } from './middleware/authMiddleware';

const app = express();

// Global middleware
app.use(express.json());

// Routes
app.use('/api/users', userRouter);

// Protected routes
app.use('/api/admin', authMiddleware, adminRouter);

// Global error handler
app.use(errorHandler);

export { app };
```

```typescript
// src/server.ts
import { app } from './app';
import { db } from './database';

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### Integration Tests with Supertest

```typescript
// tests/integration/users.test.ts
import request from 'supertest';
import { app } from '../../src/app';
import { db } from '../../src/database';
import { UserFactory } from '../factories/userFactory';

beforeAll(async () => {
  await db.migrate.latest();
});

afterAll(async () => {
  await db.destroy();
});

afterEach(async () => {
  await db('users').delete();
});

describe('POST /api/users', () => {
  it('creates user and returns 201 with user object', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: 'Alice', email: 'alice@example.com', role: 'user' })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(201);
    expect(response.body).toMatchObject({
      id: expect.any(Number),
      name: 'Alice',
      email: 'alice@example.com',
      role: 'user',
    });
    expect(response.body.password).toBeUndefined();
  });

  it('returns 409 when email already exists', async () => {
    await UserFactory.create({ email: 'alice@example.com' });

    const response = await request(app)
      .post('/api/users')
      .send({ name: 'Alice 2', email: 'alice@example.com' });

    expect(response.status).toBe(409);
    expect(response.body.error).toContain('Email already in use');
  });

  it('returns 400 for invalid email format', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: 'Bob', email: 'not-an-email' });

    expect(response.status).toBe(400);
    expect(response.body.errors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ field: 'email' })
      ])
    );
  });
});

describe('GET /api/users/:id', () => {
  it('returns user when found', async () => {
    const user = await UserFactory.create({ name: 'Charlie' });

    const response = await request(app).get(`/api/users/${user.id}`);

    expect(response.status).toBe(200);
    expect(response.body.name).toBe('Charlie');
  });

  it('returns 404 when user not found', async () => {
    const response = await request(app).get('/api/users/99999');
    expect(response.status).toBe(404);
  });
});
```

### Testing Authentication Middleware

```typescript
// tests/integration/auth.test.ts
import request from 'supertest';
import { app } from '../../src/app';
import { UserFactory } from '../factories/userFactory';
import { generateTestToken } from '../helpers/authHelpers';

describe('GET /api/users/me (authenticated route)', () => {
  it('returns 401 without auth token', async () => {
    const response = await request(app).get('/api/users/me');
    expect(response.status).toBe(401);
  });

  it('returns user profile with valid JWT', async () => {
    const user = await UserFactory.create({ role: 'admin' });
    const token = generateTestToken(user.id);

    const response = await request(app)
      .get('/api/users/me')
      .set('Authorization', `Bearer ${token}`);

    expect(response.status).toBe(200);
    expect(response.body.id).toBe(user.id);
  });

  it('returns 403 when token belongs to wrong user role', async () => {
    const user = await UserFactory.create({ role: 'viewer' });
    const token = generateTestToken(user.id);

    const response = await request(app)
      .get('/api/admin/dashboard')
      .set('Authorization', `Bearer ${token}`);

    expect(response.status).toBe(403);
  });
});
```

---

## 3. Test Factories and Fixtures

Manually inserting test data into a database is tedious and brittle. If your schema changes (e.g., adding a new required field), you have to update every test. Test factories solve this by generating valid default data that can be overridden on a per-test basis.

```typescript
// tests/factories/userFactory.ts
import { db } from '../../src/database';
import { faker } from '@faker-js/faker';

export interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'viewer';
  password_hash: string;
  created_at: Date;
}

export class UserFactory {
  static async create(overrides: Partial<User> = {}): Promise<User> {
    const defaults = {
      name: faker.person.fullName(),
      email: faker.internet.email(),
      role: 'user' as const,
      password_hash: 'hashed_password_for_tests',
      created_at: new Date(),
    };

    const [user] = await db('users')
      .insert({ ...defaults, ...overrides })
      .returning('*');

    return user;
  }

  static async createMany(count: number, overrides: Partial<User> = {}): Promise<User[]> {
    return Promise.all(
      Array.from({ length: count }, () => UserFactory.create(overrides))
    );
  }
}
```

---

## 4. Database Integration Testing with Testcontainers

Testcontainers provides lightweight, throwaway instances of common databases running in Docker containers. This ensures your tests run against the exact same database engine as production.

```typescript
// tests/integration/database.test.ts
import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql';
import { Pool } from 'pg';
import { UserRepository } from '../../src/repositories/UserRepository';

describe('UserRepository with real PostgreSQL', () => {
  let container: StartedPostgreSqlContainer;
  let pool: Pool;
  let repository: UserRepository;

  beforeAll(async () => {
    container = await new PostgreSqlContainer('postgres:16')
      .withDatabase('testdb')
      .withUsername('testuser')
      .withPassword('testpass')
      .start();

    pool = new Pool({ connectionString: container.getConnectionUri() });
    await runMigrations(pool);
    repository = new UserRepository(pool);
  }, 60_000);

  afterAll(async () => {
    await pool.end();
    await container.stop();
  });

  afterEach(async () => {
    await pool.query('TRUNCATE users CASCADE');
  });

  test('saves and retrieves a user', async () => {
    const saved = await repository.save({ name: 'Alice', email: 'alice@example.com' });
    const found = await repository.findById(saved.id);

    expect(found).toMatchObject({ name: 'Alice', email: 'alice@example.com' });
  });

  test('throws on duplicate email (unique constraint)', async () => {
    await repository.save({ name: 'Alice', email: 'alice@example.com' });

    await expect(
      repository.save({ name: 'Alice 2', email: 'alice@example.com' })
    ).rejects.toThrow(/unique/i);
  });
});
```

---

## 5. Testing with MSW (Mock Service Worker)

Mock Service Worker intercepts outgoing HTTP requests at the network level. This means your code uses native `fetch` or `axios` exactly as it would in production, but MSW intercepts the request and returns mocked data before it hits the network.

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('https://api.github.com/users/:username', ({ params }) => {
    return HttpResponse.json({
      login: params.username,
      id: 12345,
      name: 'Test User',
    });
  }),

  http.post('https://api.stripe.com/v1/charges', async ({ request }) => {
    const body = await request.json() as any;
    if (body.amount < 50) {
      return HttpResponse.json(
        { error: { message: 'Amount too small' } },
        { status: 400 }
      );
    }
    return HttpResponse.json({ id: 'ch_test123', status: 'succeeded' });
  }),
];
```

```typescript
// tests/setup.ts
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

export const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

```typescript
// tests/integration/githubService.test.ts
import { server } from '../setup';
import { http, HttpResponse } from 'msw';
import { fetchGithubUser } from '../../src/services/githubService';

describe('githubService', () => {
  it('handles rate limit error gracefully', async () => {
    server.use(
      http.get('https://api.github.com/users/:username', () =>
        HttpResponse.json({ message: 'API rate limit exceeded' }, { status: 429 })
      )
    );

    await expect(fetchGithubUser('alice')).rejects.toThrow('rate limit');
  });
});
```

---

## 6. E2E Testing with Playwright

Playwright is a modern E2E testing framework that controls browsers directly. It is faster and more reliable than Selenium due to its auto-wait capabilities and direct browser architecture.

### Setup
```bash
npm install --save-dev @playwright/test
npx playwright install chromium
```

### Configuration
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Full Registration Flow Test
```typescript
// e2e/auth/registration.spec.ts
import { test, expect } from '@playwright/test';

test.describe('User Registration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('successfully registers a new user', async ({ page }) => {
    await page.getByLabel('Full Name').fill('Alice Smith');
    await page.getByLabel('Email').fill(`alice+${Date.now()}@example.com`);
    await page.getByLabel('Password').fill('SecurePass123!');
    await page.getByLabel('Confirm Password').fill('SecurePass123!');
    await page.getByRole('button', { name: 'Create Account' }).click();

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome, Alice')).toBeVisible();
  });

  test('shows validation error for invalid email', async ({ page }) => {
    await page.getByLabel('Email').fill('not-an-email');
    await page.getByRole('button', { name: 'Create Account' }).click();

    await expect(page.getByText('Please enter a valid email address')).toBeVisible();
    await expect(page).toHaveURL('/register');
  });

  test('shows error when passwords do not match', async ({ page }) => {
    await page.getByLabel('Password').fill('password123');
    await page.getByLabel('Confirm Password').fill('differentpassword');
    await page.getByRole('button', { name: 'Create Account' }).click();

    await expect(page.getByText('Passwords do not match')).toBeVisible();
  });
});
```

### Playwright API Interactions
```typescript
// Selectors
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByLabel('Email address').fill('user@example.com');
await page.getByPlaceholder('Search...').fill('query');
await page.getByText('Success').waitFor();
await page.getByTestId('user-card').first().click();

// Assertions
await expect(page.getByRole('heading')).toHaveText('Dashboard');
await expect(page.getByRole('status')).toBeVisible();
await expect(page).toHaveURL(/\/dashboard/);
await expect(page).toHaveTitle('My App - Dashboard');
await expect(page.getByRole('table').getByRole('row')).toHaveCount(5);

// Network interception
await page.route('**/api/users', (route) => {
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 1, name: 'Alice' }]),
  });
});

// Wait for network response
const [response] = await Promise.all([
  page.waitForResponse('**/api/submit'),
  page.getByRole('button', { name: 'Submit' }).click(),
]);
expect(response.status()).toBe(200);
```

---

## 7. Page Object Model (POM) Pattern

The Page Object Model helps reduce code duplication and isolates UI structure changes from test logic. When a selector changes, you only update it in the Page Object, not in every test file.

```typescript
// e2e/pages/LoginPage.ts
import { type Page, type Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Log In' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toHaveText(message);
  }
}
```

```typescript
// e2e/pages/DashboardPage.ts
import { type Page, type Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly welcomeHeading: Locator;

  constructor(page: Page) {
    this.page = page;
    this.welcomeHeading = page.getByRole('heading', { name: /Welcome/i });
  }

  async expectToBeVisible() {
    await expect(this.welcomeHeading).toBeVisible();
  }
}
```

```typescript
// e2e/auth/login.spec.ts
import { test } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';

test('login with valid credentials', async ({ page }) => {
  const loginPage = new LoginPage(page);
  const dashboardPage = new DashboardPage(page);

  await loginPage.goto();
  await loginPage.login('user@example.com', 'correctpassword');

  await dashboardPage.expectToBeVisible();
});
```

---

## 8. Cypress Fundamentals

Cypress is another major E2E testing framework. It executes inside the browser process alongside your application code, allowing unique debugging capabilities.

### Setup
```bash
npm install --save-dev cypress
npx cypress open
```

### Basic Tests
```javascript
// cypress/e2e/login.cy.js
describe('Login Flow', () => {
  beforeEach(() => {
    cy.visit('/login');
  });

  it('logs in with valid credentials', () => {
    cy.get('[data-testid="email"]').type('user@example.com');
    cy.get('[data-testid="password"]').type('password123');
    cy.get('[data-testid="submit"]').click();

    cy.url().should('include', '/dashboard');
    cy.get('[data-testid="welcome-message"]').should('contain', 'Welcome');
  });

  it('shows error for wrong credentials', () => {
    cy.get('[data-testid="email"]').type('user@example.com');
    cy.get('[data-testid="password"]').type('wrongpassword');
    cy.get('[data-testid="submit"]').click();

    cy.get('[data-testid="error-alert"]')
      .should('be.visible')
      .and('contain', 'Invalid credentials');
  });

  it('uses custom login command', () => {
    cy.login('user@example.com', 'password123');
    cy.url().should('include', '/dashboard');
  });
});
```

### Cypress vs Playwright Comparison

| Feature | Cypress | Playwright |
|---|---|---|
| Language | JS/TS | JS/TS, Python, Java, C# |
| Browsers | Chrome, Firefox, Edge (no Safari) | All major including WebKit/Safari |
| Architecture | Runs inside browser | Controls browser externally via CDP/BiDi |
| Parallelism | Paid plan or manual splitting | Built-in, free |
| Auto-wait | Built-in | Built-in |
| Network mocking | `cy.intercept()` | `page.route()` |
| Debugging | Time-travel debugger UI | Trace viewer UI |
| Mobile | No native emulation | Via precise device emulation |
| iFrames | Limited support | Full support |
| Multiple Tabs | Not supported | Fully supported |

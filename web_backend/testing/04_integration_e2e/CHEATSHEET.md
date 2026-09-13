# Module 4: Cheatsheet

## Supertest Common Patterns

```typescript
import request from 'supertest';
import { app } from '../app';

// 1. Basic GET request with query params
const res = await request(app)
  .get('/api/search')
  .query({ q: 'test', limit: 10 });
expect(res.status).toBe(200);

// 2. POST request with JSON payload
const res = await request(app)
  .post('/api/users')
  .send({ name: 'John' })
  .set('Accept', 'application/json');

// 3. Authenticated request
const res = await request(app)
  .get('/api/protected')
  .set('Authorization', `Bearer ${token}`);

// 4. File Upload (multipart/form-data)
const res = await request(app)
  .post('/api/upload')
  .attach('avatar', 'path/to/test-image.png')
  .field('description', 'Profile picture');

// 5. Asserting Headers
expect(res.headers['content-type']).toMatch(/json/);
```

## Playwright Locator Methods

| Method | Best For | Example |
|---|---|---|
| `getByRole()` | **Highest Priority.** Accessibility-first. Finds semantic elements. | `page.getByRole('button', { name: 'Submit' })` |
| `getByLabel()` | Form inputs linked to a label element. | `page.getByLabel('Password')` |
| `getByPlaceholder()` | Inputs lacking labels, using placeholder text. | `page.getByPlaceholder('Search users...')` |
| `getByText()` | Static text content anywhere on the page. | `page.getByText('Welcome back, Alice!')` |
| `getByAltText()` | Images and multimedia content. | `page.getByAltText('Company Logo')` |
| `getByTitle()` | Elements relying on the title attribute. | `page.getByTitle('Close window')` |
| `getByTestId()` | Fallback for highly dynamic/unstable UI elements. | `page.getByTestId('user-card-123')` |

## Playwright Assertion Methods

| Assertion | Meaning | Example |
|---|---|---|
| `toBeVisible()` | Element is in the DOM and visible to the user. | `expect(locator).toBeVisible()` |
| `toContainText()` | Element contains specific substring. | `expect(locator).toContainText('Success')` |
| `toHaveText()` | Element exactly matches the given text. | `expect(locator).toHaveText('Total: $10')` |
| `toHaveValue()` | Form input contains specific value. | `expect(input).toHaveValue('alice@test.com')` |
| `toBeDisabled()` | Button or input is interactable. | `expect(button).toBeDisabled()` |
| `toHaveCount()` | Exact number of elements matching locator. | `expect(listItems).toHaveCount(5)` |
| `toHaveURL()` | Current page URL matches string or regex. | `expect(page).toHaveURL(/.*dashboard/)` |

## Cypress vs Playwright Feature Comparison

| Feature | Cypress | Playwright |
|---|---|---|
| Native Language | JavaScript / TypeScript | TS, JS, Python, C#, Java |
| Browser Engine | Chromium, Firefox, WebKit (Experimental) | Chromium, WebKit, Firefox |
| Execution Context | Inside the browser | External (CDP / BiDi) |
| Multi-Tab Support | No (by design) | Yes (First-class support) |
| iFrame Support | Difficult / Plugin required | Native and robust |
| Network Intercept | `cy.intercept()` | `page.route()` |
| Built-in Parallelism | Paid feature (Cypress Cloud) | Native and Free |

## MSW Handler Patterns

```typescript
import { http, HttpResponse, delay } from 'msw';

export const handlers = [
  // 1. Basic JSON Response
  http.get('/api/user', () => {
    return HttpResponse.json({ name: 'John' });
  }),

  // 2. HTTP Error Response
  http.post('/api/login', () => {
    return new HttpResponse('Unauthorized', { status: 401 });
  }),

  // 3. Network Delay Simulation
  http.get('/api/heavy-data', async () => {
    await delay(2000); // Wait 2 seconds
    return HttpResponse.json({ data: 'done' });
  }),

  // 4. GraphQL Interception
  graphql.query('GetUser', ({ variables }) => {
    return HttpResponse.json({
      data: { user: { id: variables.id, name: 'Alice' } }
    });
  }),
];
```

## Page Object Model (POM) Template

```typescript
// e2e/pages/BasePage.ts
import { Page, expect } from '@playwright/test';

export abstract class BasePage {
  constructor(protected readonly page: Page) {}
  
  async waitForLoad() {
    await this.page.waitForLoadState('networkidle');
  }
}

// e2e/pages/LoginPage.ts
export class LoginPage extends BasePage {
  private emailInput = this.page.getByLabel('Email');
  private passwordInput = this.page.getByLabel('Password');
  private submitButton = this.page.getByRole('button', { name: 'Log In' });

  async navigate() {
    await this.page.goto('/login');
  }

  async login(email: string, pass: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(pass);
    await this.submitButton.click();
  }
}
```

## Test Database Isolation Strategies

| Strategy | Pros | Cons | Use Case |
|---|---|---|---|
| **TRUNCATE** | Extremely robust, resets ID sequences. | Slow on large schemas. | Default for most DB integration tests. |
| **DELETE** | Faster than truncate. | Does not reset auto-increment IDs. | Tests relying on foreign key cascades. |
| **TRANSACTION** | Lightning fast. | Can fail with nested app transactions. | Very specific, tight test suites. |
| **DROP SCHEMA** | 100% clean state. | Extremely slow, requires re-migration. | Testing migrations specifically. |

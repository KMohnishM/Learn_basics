# Software Testing Curriculum

Welcome to the comprehensive software testing curriculum. This repository is designed to teach you testing from foundational concepts to advanced end-to-end strategies across both JavaScript and Python ecosystems.

## What This Curriculum Covers

This curriculum spans multiple testing frameworks and methodologies, specifically focusing on:

- **JavaScript/TypeScript**: Jest, Vitest, Cypress, Playwright
- **Python**: pytest
- **Core Principles**: TDD, BDD, Test Doubles, Coverage, CI/CD integration

Whether you are writing a small utility function or a large distributed system, these modules will guide you through writing reliable, maintainable, and fast tests.

## Module Map

| Module | Title | Description |
|---|---|---|
| 01 | Fundamentals | Core testing concepts, test pyramid, test doubles, TDD, BDD, coverage, and anti-patterns. |
| 02 | Unit Testing | Deep dive into Jest, Vitest, and pytest. Assertions, test lifecycle, and mocking techniques. |
| 03 | Integration Testing | Testing components together, database interactions, API endpoints, and contract testing. |
| 04 | End-to-End Testing | Browser automation with Cypress and Playwright, page object models, and visual regression. |
| 05 | Advanced Topics | CI/CD pipelines, performance testing, mutation testing, and maintaining large test suites. |

## The Test Pyramid

```text
       / \
      /E2E\
     /-----\
    / Inte- \
   / gration \
  /-----------\
 /    Unit     \
/---------------\
```

The test pyramid is a conceptual framework that guides how many tests of each type you should write. 
- **Unit Tests**: The foundation. Fast, highly isolated, and numerous.
- **Integration Tests**: The middle layer. Verify components work together. Slower than unit tests, but fewer in number.
- **E2E Tests**: The peak. Simulate real user scenarios. Slow and fragile, so keep them to critical paths.

## Suggested Study Order and Time Estimates

We recommend following the modules sequentially:
1. **Module 01**: 2-3 hours. Understand the "why" and the terminology before writing code.
2. **Module 02**: 4-6 hours. Hands-on practice with unit testing tools.
3. **Module 03**: 4-5 hours. Learn to handle dependencies and side effects.
4. **Module 04**: 5-7 hours. Master UI automation and flaky test prevention.
5. **Module 05**: 3-4 hours. Integrate into continuous delivery.

Total estimated time: 18-25 hours.

## Initial Setup

### JavaScript (Jest)

To set up Jest in a new Node.js project:

```bash
mkdir js-testing
cd js-testing
npm init -y
npm install --save-dev jest
```

Update your `package.json` to include the test script:

```json
{
  "scripts": {
    "test": "jest"
  }
}
```

### Python (pytest)

To set up pytest in a Python environment:

```bash
mkdir py-testing
cd py-testing
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pytest
```

You can now run tests by simply typing `pytest` in your terminal.

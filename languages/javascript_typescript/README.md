# JavaScript & TypeScript Full-Stack Curriculum

Welcome to the comprehensive JavaScript and TypeScript full-stack curriculum. This guide is designed to take you from a fundamental understanding of the language mechanics to building production-ready, scalable, and maintainable applications.

## What This Curriculum Covers

This curriculum provides a deep dive into the core mechanics of JavaScript and TypeScript before moving on to modern frontend and backend development practices. It is tailored for engineers who want to go beyond the basics and understand how things work under the hood.

Topics covered include:
- JavaScript Engine internals (V8), memory management, and the Event Loop
- Closures, scope, prototypal inheritance, and `this` binding rules
- Asynchronous programming, promises, iterators, and generators
- Comprehensive TypeScript type system, generics, and utility types
- Advanced TypeScript patterns, configuration, and module resolution
- Building full-stack applications with modern frameworks (covered in later modules)
- Architectural patterns, testing, deployment, and performance optimization

## Who Is This For?

- **Intermediate Developers:** Looking to solidify their fundamental knowledge and understand the "why" and "how" behind the language.
- **Backend Engineers:** Transitioning to full-stack roles and needing a deep understanding of the JS/TS ecosystem.
- **Senior Engineers:** Seeking a structured refresher or looking to mentor others using a rigorous syllabus.

## Module Map

| Module | Title | Key Topics | Estimated Study Time |
|---|---|---|---|
| 01 | JavaScript Core Mechanics | V8 internals, Event Loop, Closures, `this`, Promises, Generators | 20 hours |
| 02 | TypeScript Deep Dive | Structural typing, Generics, Utility Types, Conditional Types | 25 hours |
| 03 | Modern Frontend Architecture | React/Vue internals, State management, Performance | 30 hours |
| 04 | Backend Node.js & Express | Streams, Buffers, Worker Threads, Middleware patterns | 25 hours |
| 05 | API Design & GraphQL | RESTful principles, GraphQL schemas, Resolvers, Caching | 20 hours |
| 06 | Database & ORMs | SQL/NoSQL, Prisma, TypeORM, Connection pooling | 25 hours |
| 07 | Testing & Quality Assurance | Jest, Cypress, TDD, CI/CD pipelines | 20 hours |
| 08 | Production & Deployment | Docker, Kubernetes, AWS/GCP, Monitoring, Observability | 30 hours |

## Prerequisites

Before starting this curriculum, you should have:
- Basic understanding of programming concepts (variables, loops, functions).
- Familiarity with terminal commands and Git.
- A foundational understanding of HTML and CSS.

## How to Practice

To get the most out of this curriculum, follow these setup and practice guidelines:

### 1. Node.js Version Management
Use Node Version Manager (`nvm` or `nvm-windows`) to manage Node.js versions. This allows you to test code against different runtimes.
- Install nvm.
- Run `nvm install --lts` to get the latest Long Term Support version.
- Run `nvm use --lts` to activate it.

### 2. Editor Setup (VS Code)
We strongly recommend Visual Studio Code for this curriculum.
- Install the **ESLint** and **Prettier** extensions.
- Configure your settings to format on save.

### 3. TypeScript Configuration
Always use rigorous type-checking. A recommended base `tsconfig.json` for practice:
```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist"
  }
}
```

### 4. ESLint Setup
Enforce code quality with ESLint. A basic `.eslintrc.js`:
```javascript
module.exports = {
  env: {
    node: true,
    es2021: true
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module'
  },
  plugins: [
    '@typescript-eslint'
  ],
  rules: {
    // Add custom rules here
  }
};
```

## Recommended Order of Study

The curriculum is designed to be followed linearly. Modules 1 and 2 are foundational and mandatory. Do not skip them, even if you feel confident. The deep dives into V8 internals and advanced TypeScript features will pay dividends in the subsequent framework-specific modules.

1. **Module 1 (JavaScript Core):** Master the runtime.
2. **Module 2 (TypeScript):** Master the type system.
3. **Module 3 & 4 (Frontend/Backend):** Apply core concepts to application logic.
4. **Modules 5-8 (Architecture & Ops):** Scale and deploy your applications.

Happy coding!

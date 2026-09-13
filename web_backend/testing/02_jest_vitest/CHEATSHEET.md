# Jest and Vitest Cheat Sheet

## Jest CLI Commands

| Command | Description |
| :--- | :--- |
| `jest` | Run all tests |
| `jest --watch` | Run tests in watch mode (reruns on file changes) |
| `jest --coverage` | Generate code coverage report |
| `jest <filename>` | Run tests in a specific file |
| `jest -t "name"` | Run tests matching the specified test name |
| `jest -u` | Update all failing snapshots |
| `jest --clearCache` | Clear Jest's internal cache |

## Matchers Quick Reference

| Matcher | Description | Example |
| :--- | :--- | :--- |
| `toBe(val)` | Exact equality (Object.is) | `expect(2).toBe(2)` |
| `toEqual(obj)` | Deep object/array structural equality | `expect({a:1}).toEqual({a:1})` |
| `toStrictEqual(obj)`| Deep equality, checks undefined and types | `expect(arr).toStrictEqual([])` |
| `toBeTruthy()` | Matches any truthy value | `expect(1).toBeTruthy()` |
| `toBeFalsy()` | Matches any falsy value | `expect(0).toBeFalsy()` |
| `toBeNull()` | Matches exactly null | `expect(null).toBeNull()` |
| `toContain(item)` | Checks if array contains item | `expect([1, 2]).toContain(2)` |
| `toMatch(regex)` | String regex matching | `expect('test').toMatch(/es/)` |
| `toThrow(error?)` | Checks if function throws error | `expect(() => fn()).toThrow()` |

## Mock Methods

| Method | Description |
| :--- | :--- |
| `jest.fn()` | Creates a new standalone mock function |
| `jest.spyOn(obj, 'method')`| Spies on an existing method, keeping original implementation |
| `mockFn.mockReturnValue(val)`| Sets default return value |
| `mockFn.mockReturnValueOnce(val)`| Sets return value for a single call (chainable) |
| `mockFn.mockResolvedValue(val)`| Sugar for `mockImplementation(() => Promise.resolve(val))` |
| `mockFn.mockRejectedValue(err)`| Sugar for `mockImplementation(() => Promise.reject(err))` |
| `mockFn.mockImplementation(fn)`| Provides custom logic for the mock |
| `mockFn.mockClear()` | Clears `mock.calls` and `mock.instances` |
| `mockFn.mockReset()` | Clears calls and removes mock implementations |
| `mockFn.mockRestore()` | Clears, resets, and restores original implementation |

## Setup and Teardown Order

```javascript
beforeAll(() => { /* 1. Runs ONCE before anything else */ });
beforeEach(() => { /* 2. Runs before EVERY test */ });

test('test one', () => { /* 3. Test executes */ });

afterEach(() => { /* 4. Runs after EVERY test */ });
afterAll(() => { /* 5. Runs ONCE after everything finishes */ });
```

## Parameterised Tests (`test.each`)

**Array Syntax:**
```javascript
test.each([
  [1, 1, 2],
  [1, 2, 3],
])('.add(%i, %i)', (a, b, expected) => {
  expect(a + b).toBe(expected);
});
```

**Object Syntax:**
```javascript
test.each([
  {a: 1, b: 1, expected: 2},
  {a: 1, b: 2, expected: 3},
])('.add($a, $b)', ({a, b, expected}) => {
  expect(a + b).toBe(expected);
});
```

## Vitest vs Jest Differences

| Feature | Jest | Vitest |
| :--- | :--- | :--- |
| **Globals** | `test`, `expect` available by default | Must import or set `globals: true` |
| **Config** | `jest.config.js` | Uses `vite.config.js` |
| **Speed** | Moderate (CommonJS pipeline) | Blazing fast (Native ESM + Workers) |
| **Mock Object**| `jest` (e.g., `jest.fn()`) | `vi` (e.g., `vi.fn()`) |
| **Module Mock**| `jest.mock('module')` | `vi.mock('module')` (Requires careful placement) |
| **Typescript** | Requires `ts-jest` or Babel | Out of the box |

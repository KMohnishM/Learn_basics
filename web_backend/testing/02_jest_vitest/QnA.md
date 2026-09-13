# Jest and Vitest QnA

**Q1: What is the difference between `toBe` and `toEqual` in Jest? When does `toBe` on objects produce wrong results?**
In Jest, `toBe` uses `Object.is` to test exact equality. It is perfect for primitives like strings, numbers, and booleans.
`toEqual` recursively checks all properties of an object or elements of an array, testing for "deep equality".
Using `toBe` on objects produces wrong results (or unexpected test failures) because it compares object references in memory, not their structural contents.
```javascript
const obj1 = { id: 1 };
const obj2 = { id: 1 };

// This FAILS because they are different instances in memory
expect(obj1).toBe(obj2);

// This PASSES because their properties and values match
expect(obj1).toEqual(obj2);
```
Therefore, always use `toEqual` when asserting against the shape and contents of arrays and objects, reserving `toBe` strictly for primitive values and reference identity checks. It prevents subtle bugs where identical-looking objects are incorrectly flagged as different.

**Q2: Explain the difference between `jest.clearAllMocks()`, `jest.resetAllMocks()`, and `jest.restoreAllMocks()`. When should you use each?**
These three functions handle mock cleanup but with increasing levels of destructiveness.
`jest.clearAllMocks()` only clears the usage data (e.g., `mock.calls` and `mock.instances`). The mock implementation and return values remain intact. Use this in `beforeEach` to ensure call counts reset between tests without having to re-define mock behaviors.
`jest.resetAllMocks()` does everything `clearAllMocks` does, PLUS it removes any mocked return values or implementations, resetting the mock to a purely empty function returning `undefined`. Use this when you want completely fresh mock definitions per test.
`jest.restoreAllMocks()` does everything `resetAllMocks` does, PLUS it restores the original non-mocked implementation. This ONLY works for mocks created with `jest.spyOn`. Use this when you need to mock a method for a few tests, but return to the real implementation for subsequent tests in the same file.
Understanding these prevents test bleed where previous tests dictate the behavior of future ones.

**Q3: How do you test code that calls `setTimeout`? Explain Jest fake timers, `jest.useFakeTimers()`, `jest.advanceTimersByTime()`, and `jest.runAllTimers()`.**
Code that uses asynchronous timers like `setTimeout` makes tests slow and flaky if you wait for real time to pass. Jest provides Fake Timers to synchronously control time.
Calling `jest.useFakeTimers()` replaces the global timer functions with Jest's mock implementations.
```javascript
test('executes callback after 5 seconds', () => {
  jest.useFakeTimers();
  const callback = jest.fn();
  
  setTimeout(callback, 5000);
  
  expect(callback).not.toHaveBeenCalled();
  
  // Fast-forward time synchronously
  jest.advanceTimersByTime(5000);
  
  expect(callback).toHaveBeenCalledTimes(1);
  jest.useRealTimers(); // Cleanup
});
```
`jest.advanceTimersByTime(ms)` moves time forward by a specific amount, triggering any timers that fall in that window.
`jest.runAllTimers()` exhaustively fast-forwards time until all pending timers have been executed, which is useful when you don't care about the specific duration, just that the timers finish.

**Q4: What is a snapshot test in Jest? When is it useful (component output, serialised config) and when does it become a maintenance burden?**
A snapshot test renders a piece of code, serializes the output into a text string, and saves it to a `.snap` file. On subsequent runs, Jest compares the new output to the saved snapshot. If they differ, the test fails.
Snapshots are highly useful for capturing large, complex, and deterministic data structures like React component render trees, Redux state trees, or serialized configuration files. They provide massive coverage for minimal effort.
However, they become a maintenance burden when overused or applied to non-deterministic data (like generated UUIDs or current dates). Because they capture *everything*, developers often get "snapshot fatigue" where they blindly press `u` to update failing snapshots without reviewing the diffs. This defeats the purpose of the test. Snapshots are meant to alert you to unexpected changes; if the data is constantly changing organically, snapshots are the wrong tool, and you should use explicit assertions instead.

**Q5: Explain `jest.spyOn`. How does it differ from `jest.mock`? When would you prefer a spy over replacing the whole module?**
`jest.spyOn` allows you to track calls to a specific method of an existing object, and optionally replace its implementation.
`jest.mock` replaces an entire module with mock functions. It hoists to the top of the file and obliterates the original implementation of every export.
You prefer a spy when you only want to mock one specific method on an object while keeping the rest of the object's original behavior intact, or when you want to execute the original code but just verify that it was called.
```javascript
const video = {
  play() { return true; },
  pause() { return false; }
};

test('plays video', () => {
  // We spy on play, but pause remains untouched
  const spy = jest.spyOn(video, 'play');
  const isPlaying = video.play();
  
  expect(spy).toHaveBeenCalled();
  expect(isPlaying).toBe(true); // Original implementation ran
  
  spy.mockRestore(); // Important cleanup!
});
```
Spies are less intrusive and better suited for partial mocks of large objects.

**Q6: How do you test code that throws synchronous errors? And async functions that reject? Show both patterns with complete code.**
To test synchronous errors, you must wrap the function call inside an anonymous callback function, passing that callback to `expect`, and chaining `.toThrow()`. If you don't wrap it, the error bubbles up and crashes the test immediately.
To test asynchronous rejections, you use the `.rejects` modifier on the expect statement, combined with `await`.
```javascript
// Synchronous error testing
function throwSync() { throw new Error('Bad Input'); }

test('catches sync error', () => {
  expect(() => {
    throwSync();
  }).toThrow('Bad Input');
});

// Asynchronous rejection testing
async function throwAsync() { throw new Error('Network Failure'); }

test('catches async error', async () => {
  await expect(throwAsync()).rejects.toThrow('Network Failure');
});
```
Matching specific error messages ensures you're catching the right error, not just an accidental TypeError.

**Q7: What does `mockReturnValueOnce` do versus `mockReturnValue`? Give a test scenario where you need different return values on the 1st, 2nd, and 3rd call.**
`mockReturnValue` sets a permanent return value for the mock function. Every time it is called, it will return that value.
`mockReturnValueOnce` queues a return value for a single specific call. You can chain multiple `mockReturnValueOnce` calls to simulate a sequence of different behaviors. When the queued values run out, it falls back to whatever was set by `mockReturnValue` (or undefined).
Scenario: Testing a resilient API client that implements exponential backoff retries. You want the network to fail twice, then succeed on the third attempt.
```javascript
test('retries network request', async () => {
  const fetchMock = jest.fn()
    .mockRejectedValueOnce(new Error('503 Service Unavailable')) // 1st call fails
    .mockRejectedValueOnce(new Error('503 Service Unavailable')) // 2nd call fails
    .mockResolvedValue({ status: 200, data: 'success' }); // 3rd call succeeds
    
  const result = await fetchWithRetry(fetchMock);
  
  expect(fetchMock).toHaveBeenCalledTimes(3);
  expect(result.data).toBe('success');
});
```
This is essential for testing robust failure recovery paths.

**Q8: Explain `test.each`. Write an example parameterised test for a `validatePassword` function with 6 different input scenarios including edge cases.**
`test.each` is Jest's API for parameterized testing. It allows you to define a table of inputs and expected outputs, running the same test logic multiple times with different data. This drastically reduces boilerplate when testing functions with many edge cases.
```javascript
function validatePassword(pw) {
  if (pw.length < 8) return false;
  if (!/[A-Z]/.test(pw)) return false;
  return true;
}

// Using template literal table format
test.each`
  password        | expected | scenario
  ${'abc'}        | ${false} | ${'too short'}
  ${'abcdefghi'}  | ${false} | ${'no uppercase'}
  ${'Abcdefg'}    | ${false} | ${'uppercase but too short'}
  ${'ValidPass1'} | ${true}  | ${'valid password'}
  ${''}           | ${false} | ${'empty string'}
  ${'        '}   | ${false} | ${'whitespace only'}
`('returns $expected when password is $scenario', ({password, expected}) => {
  expect(validatePassword(password)).toBe(expected);
});
```
This automatically generates 6 distinct test cases in the test runner output, making it highly readable and ensuring exhaustive coverage of edge cases.

**Q9: What is the difference between `beforeAll` and `beforeEach`? What concrete test isolation bug occurs when you use `beforeAll` to initialise state that tests mutate?**
`beforeAll` executes exactly once before any tests in the suite run. `beforeEach` executes immediately before every single test in the suite.
The isolation bug occurs when you initialize a mutable object in `beforeAll` and the tests modify that object.
```javascript
let user;
beforeAll(() => {
  user = { name: 'John', role: 'guest' }; // Shared mutable state
});

test('promotes user', () => {
  user.role = 'admin';
  expect(user.role).toBe('admin');
});

test('demotes user', () => {
  // BUG: user.role is ALREADY 'admin' from the previous test!
  // If this test expected the initial state to be 'guest', it will fail.
  user.role = 'banned'; 
});
```
Because the tests share the exact same memory reference, modifications leak across tests, breaking test isolation. Changing `beforeAll` to `beforeEach` ensures `user` is freshly created before every test, fixing the bug.

**Q10: How does Vitest differ from Jest architecturally? What are the 3 main advantages for a Vite + TypeScript project?**
Vitest is a next-generation testing framework designed specifically for the Vite ecosystem. Architecturally, Jest uses CommonJS and a custom runtime to execute tests and mock modules. Vitest natively uses Vite's transform pipeline and dev server.
Three main advantages for a Vite + TypeScript project:
1. **Shared Configuration**: Vitest automatically reads your `vite.config.ts`. You don't need to maintain two separate, complex configuration files for aliases, plugins, and transforms (a huge pain point in Jest).
2. **Native ESM and TypeScript Support**: Jest requires Babel or `ts-jest` to transpile TypeScript and struggles heavily with native ES Modules. Vitest handles ESM and TS natively via esbuild, running significantly faster out of the box.
3. **HMR-like Watch Mode**: Because it uses Vite's module graph, Vitest's watch mode is incredibly intelligent. It only re-runs the specific tests affected by the precise file you just saved, much like Hot Module Replacement in the browser, making the developer experience blisteringly fast.

**Q11: How do you mock a named ES module export in Jest? What configuration (`transformIgnorePatterns`) is needed and what is the limitation with `jest.mock` and ES module live bindings?**
Mocking native ES modules in Jest is notoriously difficult because ESM has read-only live bindings.
To mock a named export, you typically use `jest.mock`:
```javascript
import { fetchData } from './api';
jest.mock('./api', () => ({
  fetchData: jest.fn().mockResolvedValue('data')
}));
```
If the module is a third-party dependency in `node_modules` that ships as raw ESM, Jest will choke on the `import` statements. You must configure `transformIgnorePatterns` in `jest.config.js` to tell Jest to compile that specific package:
```javascript
transformIgnorePatterns: ['/node_modules/(?!(my-esm-package|other-pkg)/)']
```
The limitation is that within true ESM, exports are immutable. If module A imports a function from module B, and you try to reassign that function in your test, it will throw a TypeError in native ESM environments. `jest.mock` relies on intercepting module resolution under the hood via Babel/CommonJS transforms to bypass this, meaning it's a simulated ESM environment.

**Q12: What are asymmetric matchers in Jest? Give concrete examples of when `expect.any()`, `expect.stringMatching()`, `expect.objectContaining()`, and `expect.arrayContaining()` are necessary.**
Asymmetric matchers allow you to check that a value meets certain criteria without caring about its exact literal value. They are essential when testing outputs containing generated or unpredictable data like timestamps, UUIDs, or random strings.
```javascript
const result = createUser('Alice');
// Returns: { id: 'uuid-here', name: 'Alice', created_at: 16200000, roles: ['user'] }

expect(result).toEqual({
  // expect.any() - check type, ignore specific value
  id: expect.any(String),
  
  name: 'Alice',
  
  // expect.stringMatching() - regex validation
  name: expect.stringMatching(/^[A-Z]/), 
  
  created_at: expect.any(Number)
});

// expect.objectContaining() - ignore extraneous properties
expect(result).toEqual(
  expect.objectContaining({ name: 'Alice' })
);

// expect.arrayContaining() - verify subset regardless of order
expect(result.roles).toEqual(
  expect.arrayContaining(['user'])
);
```
They make tests robust against non-deterministic outputs.

**Q13: How would you test a function that reads a file using `fs.promises.readFile`? Show the complete test with the module mock.**
Because `fs` is a core Node module, we use `jest.mock('fs')` or `jest.mock('fs/promises')`.
```javascript
import fs from 'fs/promises';
import { getConfig } from './configReader';

// Tell Jest to mock the entire promises module
jest.mock('fs/promises');

test('reads config file', async () => {
  // Provide the mock implementation for this test
  fs.readFile.mockResolvedValueOnce('{"port": 8080}');
  
  const result = await getConfig('/path/to/config.json');
  
  expect(fs.readFile).toHaveBeenCalledWith('/path/to/config.json', 'utf-8');
  expect(result.port).toBe(8080);
});
```
This isolates the test from the actual file system, ensuring it runs fast and doesn't fail due to missing files on the CI server. It also allows you to easily simulate filesystem errors like permissions issues.

**Q14: What is the difference between `mockResolvedValue(x)` and `mockImplementation(() => Promise.resolve(x))`? Is there a practical difference in how errors surface?**
Functionally, `mockResolvedValue(x)` is syntactic sugar for `mockImplementation(() => Promise.resolve(x))`. They achieve the exact same result: making the mock function return a resolved Promise.
Practically, `mockResolvedValue` is preferred because it is significantly more readable and reduces boilerplate.
There is a subtle difference in how errors surface if you make a mistake. If you accidentally write `mockImplementation(Promise.resolve(x))` (forgetting the anonymous function wrapper), the Promise resolves immediately during test setup, not when the mock is actually called, which can lead to confusing race conditions. `mockResolvedValue` enforces the correct deferred execution under the hood, making it much safer and less prone to developer error.

**Q15: How do you write a Jest custom matcher? Write a `toBeValidUUID` custom matcher and explain `this.isNot`, `this.utils.printReceived`, and how to register it.**
A custom matcher is defined using `expect.extend()`. It must return an object with a boolean `pass` property and a `message` function.
```javascript
expect.extend({
  toBeValidUUID(received) {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    const pass = uuidRegex.test(received);
    
    if (pass) {
      return {
        pass: true,
        message: () => `expected ${this.utils.printReceived(received)} not to be a valid UUID`
      };
    } else {
      return {
        pass: false,
        message: () => `expected ${this.utils.printReceived(received)} to be a valid UUID`
      };
    }
  }
});
// Registration: Put the above in a setupFilesAfterEnv script.
```
`this.isNot` is a boolean that is true when the user calls `expect(val).not.toBeValidUUID()`. You construct the message function to return the correct failure string depending on whether it passed or failed.
`this.utils.printReceived(received)` safely formats and colorizes the received value for terminal output, ensuring consistency with built-in Jest matchers.

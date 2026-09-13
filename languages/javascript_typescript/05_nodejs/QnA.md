# Node.js QnA

1. **Explain the Node.js event loop phases in order. What is the difference between `process.nextTick` and `Promise.then` in terms of execution order?**
   The phases in order are: Timers, Pending Callbacks, Idle/Prepare, Poll, Check, Close Callbacks.
   `process.nextTick` queues its callbacks in the `nextTickQueue`, which is executed immediately after the current operation completes, before the event loop continues to the next phase. `Promise.then` callbacks go to the microtask queue, which is executed immediately after the `nextTickQueue` is drained, but still before the next event loop phase.

2. **What is libuv's thread pool? What operations use it? What operations do NOT use it?**
   Libuv maintains a thread pool (default size 4) to handle operations that cannot be performed asynchronously by the OS kernel. It is used for `fs` operations, `crypto` (like pbkdf2, scrypt), `dns.lookup`, and `zlib`. Network I/O (TCP, HTTP) does NOT use the thread pool; it uses OS-level async networking (epoll/kqueue).

3. **What is backpressure in Node.js streams? How does `pipe()` handle it?**
   Backpressure occurs when a writable stream cannot process chunks as fast as a readable stream provides them, causing data to buffer in memory. `pipe()` handles this by monitoring the writable stream's internal buffer; if it exceeds the `highWaterMark`, `pipe()` pauses the readable stream until the writable stream emits a 'drain' event.

4. **What is the difference between `pipeline()` and `pipe()`? Why should you prefer `pipeline()`?**
   `pipe()` does not automatically forward errors or destroy streams if one stream in the chain fails, leading to memory leaks and hanging processes. `pipeline()` automatically manages errors and destroys all streams in the pipeline if any stream encounters an error.

5. **When would you use Worker Threads vs the Cluster module? What are the trade-offs?**
   Use Cluster for scaling a web server across multiple CPU cores to handle more concurrent network requests. It forks separate processes. Use Worker Threads for CPU-intensive tasks (like image processing or heavy cryptography) within a single process. Worker threads share memory (via SharedArrayBuffer) and have less overhead than full processes, but are not meant for scaling I/O.

6. **What is `AsyncLocalStorage` and what problem does it solve?**
   `AsyncLocalStorage` creates an asynchronous context that persists across async boundaries (callbacks, promises). It solves the problem of passing request-specific data (like user ID, correlation ID) down a deep call stack without needing to pass it explicitly as arguments to every function.

7. **What is the difference between `Buffer.alloc()` and `Buffer.allocUnsafe()`? When is `allocUnsafe` dangerous?**
   `Buffer.alloc(size)` allocates memory and zero-fills it, ensuring no old data is present. `Buffer.allocUnsafe(size)` allocates memory but does not zero-fill it, making it faster. It is dangerous if you return or expose this buffer before fully overwriting it, as it may contain sensitive data (like passwords) previously held in that memory segment.

8. **Explain the `EventEmitter` memory leak warning. How do you prevent it?**
   Node.js warns if you add more than 10 listeners to a single event on an EventEmitter. This often happens if you register `.on()` inside a loop or a request handler without ever removing it, causing memory leaks. Prevent it by using `.once()` if you only need it to fire once, explicitly calling `removeListener()`, or increasing the limit via `setMaxListeners()` only if intentionally expected.

9. **What is the difference between `child_process.exec()` and `child_process.spawn()`? When would you use each?**
   `exec()` spawns a shell, runs the command, and buffers the entire output in memory before returning it. Use for simple commands with small output. `spawn()` does not spawn a shell (by default) and streams the output. Use for commands that generate large amounts of data or long-running processes.

10. **What is the difference between `fs.readFile()` and `fs.createReadStream()`? Which would you use for a 5GB file?**
    `readFile()` reads the entire file into memory (a Buffer) before invoking the callback. `createReadStream()` reads the file chunk by chunk. For a 5GB file, you MUST use `createReadStream()`; `readFile()` will crash the Node process as it exceeds V8's memory limits.

11. **How would you implement a zero-downtime restart with the Cluster module?**
    The master process listens for the 'exit' event on workers. When a worker dies (or is intentionally signaled to close), the master forks a new worker immediately. During a deployment, the master sequentially signals one worker to shutdown gracefully, waits for it to exit, forks a new one, waits for it to listen, and then proceeds to the next worker.

12. **Why is synchronous code dangerous in a Node.js server? Give an example.**
    Because Node.js runs on a single event loop thread, executing synchronous CPU-intensive code blocks the thread. No other requests can be processed, timers won't fire, and I/O callbacks are delayed until the synchronous code completes. Example: calling `fs.readFileSync()` or `crypto.pbkdf2Sync()` in an HTTP request handler.

13. **What is the Node.js `--inspect` flag? How do you debug a memory leak?**
    The `--inspect` flag enables the V8 inspector protocol. You can debug a memory leak by connecting Chrome DevTools to the Node process, navigating to the Memory tab, and taking Heap Snapshots. You can compare snapshots over time to see which objects are persisting and consuming memory.

14. **How does `crypto.scrypt()` differ from `crypto.createHash('sha256')`? When would you use each?**
    `createHash` is a fast cryptographic hash function. It is easily brute-forced, so it should NOT be used for passwords; use it for data integrity checks (like checksums). `scrypt` is a slow, memory-hard key derivation function specifically designed for hashing passwords to thwart brute-force and GPU attacks.

15. **Explain `SharedArrayBuffer` and `Atomics` in the context of Worker Threads.**
    `SharedArrayBuffer` allows multiple Worker threads to read and write to the same block of memory without serialization overhead. `Atomics` provides operations (like add, load, store, wait) that guarantee thread-safe access to this shared memory, preventing race conditions where multiple threads attempt to mutate the data simultaneously.

# Node.js Deep Dive: Architecture, Event Loop, and Core Modules

## 1. Node.js Architecture: V8 + libuv

Node.js is a powerful JavaScript runtime built on Chrome's V8 JavaScript engine. To truly understand Node.js, one must understand its underlying architecture, which is primarily composed of two massive dependencies: V8 and libuv.

### V8: The JavaScript Engine
V8 is Google's open-source high-performance JavaScript and WebAssembly engine, written in C++. It is responsible for:
- Parsing JavaScript code and converting it into an Abstract Syntax Tree (AST).
- Executing the code using the Ignition bytecode interpreter.
- Profiling the code during execution to identify "hot" functions (functions executed frequently).
- JIT-compiling those hot paths into optimized machine code using the TurboFan optimizing compiler.
- Managing memory allocation and garbage collection for JavaScript objects.

### libuv: The Asynchronous I/O Library
libuv is a multi-platform C library that provides support for asynchronous I/O based on event loops. It abstracts the underlying OS-specific mechanisms. It is responsible for:
- Providing the Event Loop, which orchestrates all asynchronous operations.
- Providing a Thread Pool for operations that cannot be performed asynchronously at the OS level (like file system operations or DNS lookups).
- Handling timers, child processes, signals, and asynchronous TCP/UDP sockets.

### Architecture Overview
The architecture of a Node.js process consists of a single-threaded event loop, asynchronous I/O delegated to the OS, and a thread pool for blocking operations.

```text
  ┌─────────────────────────────────┐
  │         Node.js Process         │
  │  ┌───────────┐  ┌─────────────┐ │
  │  │    V8     │  │   libuv     │ │
  │  │ Call Stack│  │ Event Loop  │ │
  │  └───────────┘  └──────┬──────┘ │
  │                        │        │
  │            ┌───────────┴──────┐ │
  │            │  Thread Pool     │ │
  │            │  (4 threads)     │ │
  │            └──────────────────┘ │
  └─────────────────────────────────┘
            │
            ▼
       OS Kernel
  (epoll/kqueue/IOCP)
```

### The Thread Pool (libuv)
By default, libuv creates a thread pool with 4 threads. This pool is utilized exclusively for operations that are inherently synchronous or block the thread.
- The size of this pool can be adjusted using the environment variable `UV_THREADPOOL_SIZE`. The maximum allowed size is typically 1024.
- Operations that use the thread pool include:
  - All `fs.*` (file system) operations (except those that are explicitly synchronous, which block the main thread).
  - Certain `crypto` operations, specifically `crypto.pbkdf2`, `crypto.scrypt`, and `crypto.randomBytes`.
  - `dns.lookup` (but not `dns.resolve`, which is asynchronous network I/O).
  - Compression operations in `zlib`.

### OS Asynchronous I/O
For network I/O, Node.js delegates the work entirely to the operating system kernel. There is no thread pool involvement.
- TCP/UDP sockets and pipes are handled directly by the kernel using the most efficient mechanism available on the platform:
  - `epoll` on Linux.
  - `kqueue` on macOS and BSD.
  - `IOCP` (I/O Completion Ports) on Windows.
- When data arrives on a socket, the OS notifies libuv, which then queues the associated callback to be executed in the event loop.

### Key Insight
A common misconception is that Node.js is entirely single-threaded. This is false.
- The V8 execution context and the Event Loop run on a single thread (the "main thread").
- However, I/O operations are either delegated to the OS (running concurrently) or executed in the libuv thread pool (running in parallel).
- Therefore, Node.js can handle thousands of concurrent connections efficiently precisely because it does not dedicate a thread to each connection.


## 2. Node.js Event Loop Phases — Exhaustive

The Event Loop is the heart of Node.js. It is what allows Node.js to perform non-blocking I/O operations despite JavaScript being single-threaded. The event loop runs indefinitely, assuming there are still pending operations, timers, or active connections. When the event loop has nothing left to do, the Node.js process exits.

The event loop consists of a series of phases. Each phase has a FIFO queue of callbacks to execute. While each phase is special in its own way, generally, when the event loop enters a given phase, it will perform any operations specific to that phase, then execute callbacks in that phase's queue until the queue has been exhausted or the maximum number of callbacks has executed. When the queue has been exhausted or the callback limit is reached, the event loop will move to the next phase, and so on.

Here are the 6 distinct phases of the event loop, executed in order:

### Phase 1: Timers
- **Purpose**: This phase executes callbacks scheduled by `setTimeout(fn, delay)` and `setInterval(fn, delay)`.
- **Mechanism**: A timer specifies the *threshold* after which a provided callback *may* be executed rather than the *exact* time a person wants it to be executed. Timers callbacks will run as early as they can be scheduled after the specified amount of time has passed.
- **Note**: Operating system scheduling or the running of other callbacks may delay them. The `delay` parameter is a minimum wait time, not a guarantee.
- **Quirk**: Calling `setTimeout(fn, 0)` is internally coerced to `setTimeout(fn, 1)` in practice due to underlying implementation details in Chromium/V8 and libuv.

### Phase 2: Pending Callbacks
- **Purpose**: This phase executes I/O callbacks deferred to the next loop iteration.
- **Mechanism**: Sometimes, some I/O callbacks are delayed for the next loop iteration. For example, some types of TCP errors (like `ECONNREFUSED` when attempting to connect) might not be handled immediately upon reception. The OS might report the error, but the callback execution is deferred to this phase.

### Phase 3: Idle, Prepare
- **Purpose**: Internal libuv use only.
- **Mechanism**: This phase is entirely internal to libuv. It is used to prepare for the upcoming polling phase. Application developers can completely ignore this phase, as it has no direct exposure via the Node.js JavaScript API.

### Phase 4: Poll
- **Purpose**: This is the most crucial phase. It retrieves new I/O events and executes their callbacks.
- **Mechanism**: The poll phase has two main functions:
  1. Calculating how long it should block and poll for I/O.
  2. Processing events in the poll queue.
- **Blocking**: When the event loop enters the poll phase and there are no timers scheduled, it will BLOCK and wait for incoming connections, requests, etc., and then execute their callbacks immediately.
- **Timeouts**: If there are timers scheduled, the event loop will check if any timers have expired. If one or more timers are ready, the event loop will wrap back to the timers phase to execute those timers' callbacks. It calculates a timeout to know exactly how long to wait for I/O events before giving up and checking the timers again.
- **Performance**: This phase is what makes Node.js incredibly efficient for I/O-heavy workloads. It spends most of its idle time sleeping here, waiting for the OS to wake it up when a socket becomes readable or writable.

### Phase 5: Check
- **Purpose**: This phase exclusively executes `setImmediate(fn)` callbacks.
- **Mechanism**: `setImmediate()` is a special timer that runs in a separate phase of the event loop. It uses a libuv API that schedules callbacks to execute immediately *after* the poll phase has completed.
- **Guarantee**: `setImmediate` is guaranteed to always run after the poll phase, before the next timer phase begins.

### Phase 6: Close Callbacks
- **Purpose**: Executes close event callbacks.
- **Mechanism**: If a socket or handle is closed abruptly (e.g., `socket.destroy()`), the `'close'` event will be emitted in this phase. Otherwise, it will be emitted via `process.nextTick()`.

### The Microtask Queues: nextTick and Promises
Crucially, there are two queues that are evaluated **between EVERY single phase transition**, and also before the event loop even starts its first iteration. These are not technically part of the libuv event loop itself, but rather handled by the Node.js C++ bindings.

1. **The `process.nextTick` Queue**:
   - Contains all callbacks scheduled via `process.nextTick(fn)`.
   - Has absolute highest priority.
   - The queue is drained entirely before proceeding to the microtask queue or the next event loop phase.
   - Warning: A recursive `process.nextTick` can completely block the event loop, causing starvation, as the transition to the next phase will never happen.

2. **The Microtask Queue**:
   - Contains all resolved Promise callbacks (`.then`, `.catch`, `.finally`).
   - Evaluated immediately after the `nextTick` queue is drained.
   - Also drained entirely before proceeding to the next event loop phase.

### Exact Execution Order Example with Explanation

Consider the following purely synchronous setup:

```javascript
setTimeout(() => console.log('setTimeout'), 0);
setImmediate(() => console.log('setImmediate'));
Promise.resolve().then(() => console.log('Promise'));
process.nextTick(() => console.log('nextTick'));
console.log('sync');
```

**Execution Trace:**
1. The main script executes synchronously. `console.log('sync')` prints.
2. The script finishes. Before entering the first event loop phase, Node.js checks the microtask queues.
3. The `nextTick` queue is drained: `nextTick` prints.
4. The Promise microtask queue is drained: `Promise` prints.
5. The event loop starts.
6. **Non-deterministic branch**: Because `setTimeout(fn, 0)` is actually `1ms`, and the startup time of the Node process takes roughly ~1ms, by the time the event loop hits the Timer phase, the timer *might* have expired, or it *might not* have.
   - If it expired: `setTimeout` prints, then later in the Check phase, `setImmediate` prints.
   - If it didn't expire: The loop bypasses Timers, goes to Poll, goes to Check, `setImmediate` prints. Then on the next iteration, Timers phase runs and `setTimeout` prints.
   - Therefore, without I/O context, the order of `setTimeout(0)` and `setImmediate()` is unpredictable and depends on the performance of the machine and the OS scheduler.

**Deterministic execution within I/O:**

```javascript
const fs = require('fs');

fs.readFile(__filename, () => {
  setTimeout(() => console.log('setTimeout'), 0);
  setImmediate(() => console.log('setImmediate'));
});
```
**Execution Trace inside I/O callback:**
1. The `fs.readFile` callback is executed during the **Poll phase**.
2. Inside the callback, `setTimeout` and `setImmediate` are scheduled.
3. The callback finishes. The Poll phase completes.
4. The event loop moves to the very next phase: the **Check phase**.
5. The Check phase executes `setImmediate` callbacks. `setImmediate` prints.
6. The loop continues, eventually wrapping around to the next iteration's **Timer phase**.
7. The Timer phase executes the expired timer. `setTimeout` prints.
- **Conclusion**: Inside an I/O callback (or any callback executing in the Poll phase), `setImmediate` will ALWAYS execute before a `setTimeout(fn, 0)`.


## 3. Streams — Deep Dive

Streams are one of the most powerful and fundamental concepts in Node.js. They provide a way to handle reading and writing data asynchronously, piece by piece, rather than reading a massive file into memory all at once.

### Why Streams Matter
- **Memory Efficiency (Without Streams)**: If you use `fs.readFile` to read a 10GB video file, Node.js will attempt to allocate a 10GB Buffer in RAM. This will instantly crash your application due to V8's memory limits, and even if it didn't, it would be a catastrophic waste of system resources.
- **Memory Efficiency (With Streams)**: By using `fs.createReadStream`, the file is read in small, manageable chunks (e.g., 64KB at a time, defined by the `highWaterMark` option). The application processes one chunk, garbage collects it, and moves to the next. The memory footprint remains stable at ~64KB regardless of whether the file is 10MB or 100GB.
- **Time Efficiency (Latency)**: Without streams, you must wait for the entire 10GB file to be read before you can start sending it to a client. With streams, you can start streaming the first 64KB chunk to the network socket immediately while the disk is still reading the rest.
- **Composability**: Streams can be piped together like Unix commands. You can pipe a readable file stream into a transform stream (like a gzip compressor), and then pipe that into a writable network stream, all with automatic flow control.

### The 4 Stream Types

Node.js provides four fundamental types of streams:

1. **`Readable`**: A source of data that you can read from.
   - Examples: `fs.createReadStream()`, `http.IncomingMessage` (the request object in a server, or response object in a client), `process.stdin`.
2. **`Writable`**: A destination for data that you can write to.
   - Examples: `fs.createWriteStream()`, `http.ServerResponse` (the response object in a server), `process.stdout`.
3. **`Duplex`**: A stream that is both readable and writable, but the two channels are independent. Data written to it doesn't necessarily dictate what is read from it.
   - Example: `net.Socket` (a TCP connection — you can read incoming packets and write outgoing packets simultaneously).
4. **`Transform`**: A specialized type of Duplex stream where the output is directly computed from the input. It transforms the data as it passes through.
   - Examples: `zlib.createGzip()` (compresses data), `crypto.createCipheriv()` (encrypts data), or a custom CSV parser.

### Readable Stream Modes
Readable streams can operate in two distinct modes:

- **Paused Mode (Default)**: Also known as "pull mode". When a stream is created, it is paused. Data is read from the OS and placed into an internal buffer. You must explicitly call `stream.read()` to pull chunks of data out of the buffer.
- **Flowing Mode**: Also known as "push mode". Data is read from the underlying system and pushed to the application as fast as possible via events.
  - A stream switches to flowing mode automatically if you attach a listener to the `'data'` event.
  - Calling `stream.pipe()` also switches it to flowing mode to feed the writable stream.
  - Calling `stream.resume()` explicitly forces flowing mode.
- **Switching Back**: A flowing stream can be switched back to paused mode by calling `stream.pause()`, removing all `'data'` event listeners, or calling `stream.unpipe()`.

### Backpressure: The Most Important Stream Concept
Backpressure is the mechanism that prevents a fast readable stream from overwhelming a slow writable stream.
- **The Problem**: Imagine reading from a fast SSD and piping the data to a slow network connection. The SSD can produce data at 500MB/s, but the network can only transmit at 1MB/s. If the readable stream doesn't slow down, the writable stream's internal buffer will grow indefinitely until the Node.js process crashes with an Out-Of-Memory (OOM) error.
- **The Detection**: Writable streams have a `highWaterMark` (a threshold for their internal buffer size, typically 16KB). When you call `writable.write(chunk)`, it returns a boolean. If it returns `false`, it means the internal buffer has exceeded the `highWaterMark`. This is the signal for backpressure.
- **The Response**: When `write()` returns false, the application must immediately pause the readable stream. The writable stream will continue to drain its buffer asynchronously. Once the buffer is emptied below the threshold, the writable stream emits a `'drain'` event. The application must listen for this event and then resume the readable stream.
- **Automatic Handling**: The `.pipe()` method handles this entire backpressure dance completely automatically. This is why you should almost always use `.pipe()` or `pipeline()` rather than manually wiring up `'data'` and `'write'` calls.

**Manual backpressure handling example (for understanding internals):**
```typescript
import { createReadStream, createWriteStream } from 'fs';

const readable = createReadStream('large-file.bin');
const writable = createWriteStream('output.bin');

readable.on('data', (chunk: Buffer) => {
  // writable.write returns false if the buffer is full
  const canContinue = writable.write(chunk);
  
  if (!canContinue) {
    // Stop reading from the source!
    readable.pause();
    
    // Wait for the writable stream to empty its buffer
    writable.once('drain', () => {
      // Resume reading from the source
      readable.resume();
    });
  }
});

readable.on('end', () => {
  writable.end();
});
```

### `pipe()` vs `pipeline()`

- **`stream.pipe(destination)`**: The classic way to chain streams.
  - **Fatal Flaw**: It does NOT handle errors gracefully. If the readable stream emits an `'error'` event, it will crash the process if unhandled. Even if handled, it does NOT automatically destroy the destination stream, leading to dangling file descriptors and memory leaks.
- **`stream.pipeline(...streams)`**: Introduced in Node 10, this is the modern, robust way to chain streams.
  - It handles errors across the entire pipeline.
  - If any stream in the pipeline fails, it ensures that all other streams in the pipeline are safely destroyed, preventing leaks.
  - It provides a callback or returns a Promise when the entire pipeline is complete or errors out.
  - It seamlessly supports mixing classic streams, async generators, and async iterables.
  
**Always use `pipeline()` in production code.**

```typescript
import { pipeline } from 'stream/promises';
import { createReadStream, createWriteStream } from 'fs';
import { createGzip } from 'zlib';

async function compressFile() {
  try {
    await pipeline(
      createReadStream('input.txt'),
      createGzip(),
      createWriteStream('output.txt.gz')
    );
    console.log('Pipeline succeeded.');
  } catch (err) {
    console.error('Pipeline failed:', err);
  }
}
```

### Creating a Custom Transform Stream
Creating custom streams is common for data manipulation pipelines.

```typescript
import { Transform, TransformCallback } from 'stream';
import { createReadStream, createWriteStream } from 'fs';

class UpperCaseTransform extends Transform {
  constructor() {
    super(); // Optional options can be passed to super()
  }

  // The core method that must be implemented
  _transform(chunk: Buffer, encoding: string, callback: TransformCallback) {
    try {
      // Convert chunk to string, uppercase it, and push it down the pipeline
      const resultString = chunk.toString('utf8').toUpperCase();
      this.push(resultString); // push() sends data to the writable side
      
      // Call the callback to indicate we are done with this chunk
      callback(); 
    } catch (err) {
      // Pass errors to the callback
      callback(err as Error);
    }
  }

  // Optional: called right before the stream closes, useful for flushing trailing data
  _flush(callback: TransformCallback) {
    // We have nothing to flush in this simple example
    callback();
  }
}

// Usage in a pipeline:
import { pipeline } from 'stream/promises';

async function run() {
  await pipeline(
    createReadStream('input.txt'),
    new UpperCaseTransform(),
    createWriteStream('upper.txt')
  );
}
```


## 4. Buffers

In standard JavaScript (prior to typed arrays), there was no mechanism to handle raw binary data natively. Node.js introduced the `Buffer` class to fulfill this requirement, primarily for interacting with TCP streams, file system reads, and cryptographic operations.

### What is a Buffer?
- A `Buffer` is a globally available Node.js class representing a fixed-size chunk of memory allocated outside the V8 JavaScript engine.
- It is a subclass of the standard JavaScript `Uint8Array`. Consequently, Buffers share all the methods of `Uint8Array` but also provide Node-specific utilities for encoding and decoding strings.
- Because it is allocated off-heap (or outside the normal garbage collected heap for large chunks), creating large buffers does not put pressure on V8's garbage collector.

### Buffer Allocation Methods
- **`Buffer.alloc(size, [fill], [encoding])`**: Creates a new Buffer of the specified size. The underlying memory is explicitly zero-filled before being returned to the application. This ensures that no sensitive data from previously freed memory is exposed. It is safe but slightly slower due to the initialization overhead.
- **`Buffer.allocUnsafe(size)`**: Creates a new Buffer of the specified size, but the underlying memory is **NOT zero-filled**. The memory segment might contain old data, including passwords, private keys, or other sensitive information left over by the OS or other Node.js processes.
  - **Rule of Thumb**: Only use `allocUnsafe` if you are absolutely guaranteed to overwrite the entire buffer length with your own data immediately after creation (e.g., when reading from a socket into the buffer). If you send an uninitialized unsafe buffer to a client, you have introduced a severe security vulnerability.
- **`Buffer.from()`**: Creates a buffer from existing data.
  - `Buffer.from(string, encoding)`: Converts a string to a buffer using the specified encoding (e.g., `'utf8'`, `'hex'`, `'base64'`, `'ascii'`).
  - `Buffer.from(array)`: Creates a buffer from an array of bytes.
  - `Buffer.from(arrayBuffer)`: Creates a buffer that shares the exact same memory as a standard Web `ArrayBuffer`.

### Character Encodings
Buffers excel at translating between raw bytes and human-readable strings.
- **`'utf8'`**: The default encoding. Represents Unicode characters.
- **`'hex'`**: Encodes each byte as two hexadecimal characters. Extremely common for displaying cryptographic hashes.
- **`'base64'`**: Encodes binary data into ASCII characters using the Base64 alphabet. Common for sending binary data over text-based protocols (like embedding images in JSON).

```typescript
// String to Buffer
const buf = Buffer.from('Hello World', 'utf8');

// Buffer back to strings in different formats
console.log(buf.toString('hex'));    // 48656c6c6f20576f726c64
console.log(buf.toString('base64')); // SGVsbG8gV29ybGQ=
```

### Buffer vs ArrayBuffer
With the advent of the Web platform standardizing binary data, `ArrayBuffer` and `Uint8Array` were introduced to the JavaScript language specification.
- `ArrayBuffer` is the spec-compliant way to allocate binary memory in modern JS.
- Node.js `Buffer` predates `ArrayBuffer` but was later refactored to be a subclass of `Uint8Array`.
- Today, `Buffer` is primarily the Node.js API surface, while `ArrayBuffer` is the cross-platform standard. You can easily bridge them using `Buffer.from(arrayBuffer)` without copying the underlying memory.


## 5. Worker Threads

Node.js is traditionally single-threaded for execution, which is fantastic for I/O bound tasks but terrible for CPU-bound tasks. If you run a heavy computational loop (like resizing an image, parsing a massive JSON file, or running cryptographic hashes), you will block the Event Loop. While blocked, Node.js cannot accept new connections or process existing ones. 

To solve this, Node 10 introduced the `worker_threads` module, providing true multi-threading capabilities.

### Architecture of Worker Threads
- Unlike threads in languages like Java or C++, Worker Threads in Node.js do not automatically share memory.
- Each Worker is essentially an entirely separate and independent instance of V8.
- Each Worker has its own V8 Isolate, its own JavaScript context, its own heap memory, and crucially, its own libuv Event Loop.
- Because they don't share V8 state, you avoid the massive complexities of locking, mutexes, and race conditions that plague traditional multithreaded programming.

### Communication: Message Passing
The primary way Workers communicate with the main thread (and each other) is via Message Channels.
- Data sent between threads is copied using the **Structured Clone Algorithm**.
- This is a deep copy. It can handle complex objects, Maps, Sets, and cyclic graphs, but it cannot copy Functions, Error objects, or DOM nodes.

```typescript
// --- main.ts ---
import { Worker } from 'worker_threads';
import path from 'path';

function runWorker(inputData: number): Promise<number> {
  return new Promise((resolve, reject) => {
    // Spawn the worker, passing initial data
    const worker = new Worker(path.join(__dirname, 'worker.js'), {
      workerData: { input: inputData }
    });
    
    // Listen for messages from the worker
    worker.on('message', (result) => resolve(result));
    
    // Handle errors and exits
    worker.on('error', reject);
    worker.on('exit', (code) => {
      if (code !== 0) reject(new Error(`Worker stopped with exit code ${code}`));
    });
  });
}

// --- worker.ts (compiled to worker.js) ---
import { parentPort, workerData } from 'worker_threads';

// heavy CPU-bound computation
function fibonacci(n: number): number {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

// Access the data passed in during initialization
const input = workerData.input;

// Perform the work blocking THIS worker's event loop (main loop is unaffected)
const result = fibonacci(input);

// Send the result back to the main thread
if (parentPort) {
  parentPort.postMessage(result);
}
```

### Shared Memory: SharedArrayBuffer and Atomics
For ultra-high performance where copying large amounts of data (like huge matrices for WebGL or ML) is too slow, Node.js supports shared memory.
- You can instantiate a `SharedArrayBuffer` in the main thread and pass it to a worker. Both threads will have a view into the exact same physical memory addresses.
- Modifying an index in one thread instantly reflects in the other.
- **The Catch**: This reintroduces race conditions. To safely mutate shared memory, you must use the global `Atomics` object.
- `Atomics` provides atomic operations (add, sub, load, store) that guarantee hardware-level synchronization.
- **`Atomics.wait(typedArray, index, value)`**: Blocks the current thread until another thread calls `notify()` on that index. **Crucially, `Atomics.wait()` is illegal to call on the main Node.js thread**, as blocking the main thread defeats the entire purpose of Node.js. It can only be used inside workers.
- **`Atomics.notify(typedArray, index, count)`**: Wakes up workers that are sleeping on a `wait()` call.

### The Worker Pool Pattern
Spawning a new V8 isolate and thread for every incoming request is extremely slow and memory intensive (taking tens of milliseconds and megabytes of RAM). 
- In production, you must use a **Worker Pool**.
- At startup, you spawn a fixed number of workers (e.g., equal to the number of CPU cores).
- When a CPU-bound task arrives, it is placed in a queue.
- An idle worker pulls the task from the queue, executes it, returns the result via message passing, and then becomes idle again, ready for the next task.
- Libraries like `piscina` or `workerpool` implement this robustly.


## 6. Cluster Module

While Worker Threads handle CPU-bound tasks within a single process, the `cluster` module handles scaling a Node.js network application across multiple CPU cores by launching entirely separate processes.

### Architecture: Master and Workers
- A single Node.js instance runs on a single thread and can only utilize a single CPU core. If you run a Node server on an 8-core machine, 7 cores sit idle.
- The `cluster` module solves this by utilizing the `child_process.fork()` method to spawn multiple identical Node.js processes, known as "workers".
- The original process is designated the "primary" (formerly "master") process.
- **The Magic**: The cluster module allows all these distinct child processes to share the exact same server port (e.g., port 3000).

### Load Balancing
When a request arrives on port 3000:
1. The OS delivers the connection to the primary process.
2. The primary process acts as a lightweight load balancer.
3. Using an Inter-Process Communication (IPC) channel, it passes the TCP connection handle to one of the worker processes.
4. The worker process accepts the connection and executes your Express/HTTP handler.
- The default load balancing algorithm on all platforms except Windows is round-robin.

```typescript
import cluster from 'cluster';
import os from 'os';
import { createServer } from 'http';

// Entry point execution
if (cluster.isPrimary) {
  console.log(`Primary ${process.pid} is running`);

  const numCPUs = os.cpus().length;

  // Fork a worker for each CPU core
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  // Self-healing: if a worker crashes, spawn a new one immediately
  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} died with code: ${code}. Restarting...`);
    cluster.fork();
  });

} else {
  // This code runs inside the child worker processes
  // They all share the same port 3000 via the primary's IPC magic
  createServer((req, res) => {
    res.writeHead(200);
    res.end(`Hello from Worker ${process.pid}\n`);
  }).listen(3000);

  console.log(`Worker ${process.pid} started`);
}
```

### Zero-Downtime Deployments
The master-worker architecture enables zero-downtime restarts. When you push new code, you cannot simply kill the Node process and start a new one, as you will drop active connections.
Instead, using cluster:
1. The primary process is instructed to reload.
2. It sends a SIGTERM signal to Worker 1.
3. Worker 1 stops accepting new connections but finishes processing existing ones (graceful shutdown).
4. Once Worker 1 exits, the primary forks a new Worker 1 running the new code.
5. Once the new Worker 1 is listening, the primary moves to Worker 2, and so on.
- Tools like PM2 automate this entirely (`pm2 reload app`).

### Cluster vs Worker Threads: The Ultimate Distinction
- **Cluster**: Spawns entirely separate OS processes. Each has its own isolated memory space. Best for scaling HTTP servers across cores. If one worker crashes due to an unhandled exception, it does not affect the others, and the primary can restart it.
- **Worker Threads**: Spawns threads within a single OS process. They can share memory via `SharedArrayBuffer`. Best for offloading heavy, blocking CPU calculations (like video encoding) from the main event loop while keeping the application as a single logical unit.


## 7. AsyncLocalStorage

One of the longest-standing problems in Node.js was the lack of Thread-Local Storage (TLS) equivalent. In synchronous languages like Java or Python, an incoming HTTP request runs entirely on a single dedicated thread. You can store request-specific context (like a Correlation ID, the authenticated User object, or tenant details) in a thread-local variable, making it globally accessible anywhere during that request without explicitly passing it down the function call chain.

In Node.js, thousands of requests interleave concurrently on a single thread. You cannot use global variables, because Request A's data would be overwritten by Request B. Historically, developers had to pass the `req` object down through every single function call manually, muddying the API signatures.

### Enter `AsyncLocalStorage`
Introduced in the `async_hooks` module, `AsyncLocalStorage` provides a safe way to store state that is bound to the lifespan of an asynchronous logical sequence (like an HTTP request). It automatically propagates through Promises, `setTimeout`, `setImmediate`, and event emitters.

### How to use it

```typescript
import { AsyncLocalStorage } from 'async_hooks';
import crypto from 'crypto';
import express from 'express';

// 1. Define the shape of your context
interface RequestContext {
  requestId: string;
  userId?: string;
}

// 2. Instantiate the storage (typically a singleton exported from a module)
export const requestContext = new AsyncLocalStorage<RequestContext>();

const app = express();

// 3. Create a middleware that initializes the context for each incoming request
app.use((req, res, next) => {
  const context: RequestContext = {
    requestId: req.headers['x-request-id'] as string || crypto.randomUUID()
  };
  
  // .run() executes the callback (next) within the provided context.
  // Any async operation spawned inside 'next()' will inherit this context.
  requestContext.run(context, next);
});

// Deep inside your service layer, far away from the Express 'req' object:
class DatabaseService {
  async queryData() {
    // 4. Retrieve the context anywhere in the call chain
    const ctx = requestContext.getStore();
    
    const reqId = ctx?.requestId ?? 'UNKNOWN';
    console.log(`[${reqId}] Executing database query...`);
    
    // The request ID is automatically logged without being passed as a parameter!
  }
}
```

### Common Use Cases
- **Distributed Tracing**: Automatically appending a correlation ID to all logs generated during a specific request.
- **User Context**: Making the authenticated user's ID available to lower-level database repositories to enforce Row-Level Security without passing the user object everywhere.
- **Tenant Isolation**: In multi-tenant SaaS applications, determining which tenant database connection to use based on the context.


## 8. Core Built-in Modules

Node.js comes with a rich standard library. Relying on core modules rather than NPM packages for fundamental operations reduces bundle size, improves security (supply chain), and ensures stability.

### `crypto`
Provides cryptographic functionality that wraps OpenSSL.
- **`crypto.randomUUID()`**: The fastest, built-in way to generate RFC 4122 UUID v4 strings. No need for the `uuid` npm package anymore.
- **`crypto.createHash('sha256')`**: For generating fast, one-way hashes (checksums). 
  - *Warning*: NEVER use `createHash` (SHA256, MD5) for hashing passwords. They are designed to be fast, making them vulnerable to brute-force attacks.
- **`crypto.scrypt(password, salt, keylen, callback)`**: A memory-hard Key Derivation Function. This is the recommended built-in method for hashing user passwords securely. It requires significant RAM to compute, defeating GPU brute-force attacks.
- **`crypto.pbkdf2(...)`**: Another password hashing algorithm. Still secure if configured with enough iterations (e.g., > 300,000), but `scrypt` is generally preferred now.
- **`crypto.createCipheriv(algorithm, key, iv)`**: For symmetric encryption. Always use authenticated encryption modes like `'aes-256-gcm'`. GCM (Galois/Counter Mode) not only encrypts the data but also provides an authentication tag (via `cipher.getAuthTag()`) to ensure the ciphertext has not been tampered with.

### `fs` (File System)
- **Callback API (`fs.readFile`)**: The legacy asynchronous API requiring callbacks. Prone to callback hell.
- **Synchronous API (`fs.readFileSync`)**: Blocks the event loop. Acceptable only during application startup to read configuration files. Never use in request handlers.
- **Promise API (`require('fs/promises')`)**: The modern API. Returns Promises, enabling `async/await`. Always prefer this.
- **File Watching (`fs.watch`)**: Extremely unreliable across different operating systems (triggers multiple times, misses events). Do not use in production. Use the `chokidar` NPM package instead, which handles OS inconsistencies.

### `path`
Handles cross-platform file path normalization. (Windows uses `\`, POSIX uses `/`).
- **`path.join(...paths)`**: Joins segments using the correct OS separator. `path.join('/foo', 'bar')` yields `/foo/bar` on Linux and `\foo\bar` on Windows.
- **`path.resolve(...paths)`**: Resolves a sequence of paths into an absolute path, acting like a sequence of `cd` commands originating from `process.cwd()`.
- **`path.basename`, `dirname`, `extname`**: Extracts the filename, directory path, and file extension respectively.
- **ES Modules Quirk**: In CommonJS, `__dirname` and `__filename` are injected globally. In ES Modules (`import/export`), they do not exist. You must derive them:
  ```typescript
  import { fileURLToPath } from 'url';
  import { dirname } from 'path';
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = dirname(__filename);
  ```

### `child_process`
Allows spawning external OS processes and communicating with them via stdin/stdout streams.
- **`exec(command, callback)`**: Spawns a shell and runs the command within it, buffering the entire output into memory. 
  - *Danger*: Highly vulnerable to Shell Injection attacks if the command includes unsanitized user input. Avoid if possible.
- **`spawn(command, [args])`**: Does NOT spawn a shell by default. It executes the binary directly. It streams the input and output, making it safe for massive data and immune to basic shell injection. Always prefer `spawn`.
- **`execFile(file, [args], callback)`**: Similar to `exec`, but executes the file directly without a shell. Safer, but still buffers output in memory.
- **`fork(modulePath)`**: A specialized version of `spawn` designed exclusively for spawning other Node.js processes. It automatically establishes an IPC communication channel, allowing you to use `child.send(message)` to pass data back and forth.


## 9. Debugging & Performance

Running Node.js in production requires knowing how to introspect the runtime when things go wrong (memory leaks, CPU spikes, event loop stalls).

### The Inspector (V8 Debugger)
Node.js embeds the V8 inspector, the exact same protocol used by Chrome DevTools.
- Run your app with the `--inspect` flag: `node --inspect server.js`.
- Node will open a WebSocket server on `127.0.0.1:9229`.
- Open Google Chrome and navigate to `chrome://inspect`. Your Node process will appear. Clicking "inspect" opens a full Chrome DevTools window connected to your backend process.
- **`--inspect-brk`**: Extremely useful. It starts the inspector but pauses execution on the very first line of your script, allowing you to set breakpoints before any setup code runs.

### Memory Leaks & Heap Snapshots
Unlike C++, you don't leak memory by forgetting to `free()` it. In Node.js, you leak memory by retaining references to objects that are no longer needed (e.g., pushing data into a global array and never removing it). The Garbage Collector cannot clean up objects that are still referenced.
- **Detecting a leak**: Monitor `process.memoryUsage().heapUsed` over time. If it looks like a sawtooth wave that continually creeps upwards, you have a leak.
- **Finding the leak**: 
  1. Connect via Chrome DevTools (`--inspect`).
  2. Go to the "Memory" tab and take a "Heap Snapshot".
  3. Run load against your app.
  4. Take a second "Heap Snapshot".
  5. Select "Comparison" mode to see exactly which objects were allocated between snapshot 1 and 2 and never garbage collected. Look for massive strings, closures, or arrays.

### CPU Profiling
If your app is running slowly, you need to know which functions are taking up the most CPU time.
- Run with `--prof`: `node --prof server.js`.
- This generates a massive, unreadable log file (`isolate-0x...-v8.log`).
- Process the log file: `node --prof-process isolate-*.log > processed.txt`.
- Open `processed.txt`. It provides a detailed breakdown of where V8 spent its time, categorized into JavaScript execution, C++ bindings, and Garbage Collection. You will see a list of functions sorted by the number of CPU ticks they consumed.

### Clinic.js (Advanced Diagnostics)
For complex performance issues, the `clinic` npm package (maintained by NearForm) is the industry standard.
- **`clinic doctor -- node server.js`**: Analyzes CPU, memory, and Event Loop delay, and heuristically diagnoses the problem (e.g., "I/O bound", "Event loop blocked").
- **`clinic flame`**: Generates interactive flamegraphs to visually represent CPU profiling. The wider a bar, the more CPU time that function consumed.
- **`clinic bubbleprof`**: Generates a map of async operations (Promises, timeouts) to help you understand complex asynchronous control flows and where latency is introduced.

# Node.js Cheatsheet

## Event Loop Phases

```text
       +------------------------------------+
       |           Synchronous Code         |
       +------------------------------------+
                         |
       +------------------------------------+
       |  process.nextTick() callbacks      | <-- Executed immediately after sync code
       +------------------------------------+
       |  Promise.then() microtasks         |
       +------------------------------------+
                         |
   +-------------------------------------------------+
   |                     |                           |
   |   +------------------------------------+        |
   |   |            Timers Phase            |        |
   |   | (setTimeout, setInterval expired)  |        |
   |   +------------------------------------+        |
   |                     |                           |
   |   +------------------------------------+        |
   |   |        Pending Callbacks           |        |
   |   |   (System/TCP error callbacks)     |        |
   |   +------------------------------------+        |
   |                     |                           |
   |   +------------------------------------+        |
   |   |           Idle, Prepare            |        |
   |   |         (Internal usage)           |        |
   |   +------------------------------------+        |
   |                     |                           |
   |   +------------------------------------+        |
   |   |              Poll Phase            |        |
   |   |   (I/O, fs, net, crypto returns)   | <----- Blocks here if queue is empty
   |   +------------------------------------+        |
   |                     |                           |
   |   +------------------------------------+        |
   |   |             Check Phase            |        |
   |   |      (setImmediate callbacks)      |        |
   |   +------------------------------------+        |
   |                     |                           |
   |   +------------------------------------+        |
   |   |          Close Callbacks           |        |
   |   |     (socket.on('close'), etc.)     |        |
   |   +------------------------------------+        |
   |                     |                           |
   +-------------------------------------------------+
```
*Note: `process.nextTick` and `Promises` are evaluated between EVERY phase transition as well.*

---

## Libuv Thread Pool vs OS Async

| Operation Type | Uses Thread Pool (`UV_THREADPOOL_SIZE`) | Uses OS Async Networking (epoll/kqueue/IOCP) |
| :--- | :---: | :---: |
| HTTP/HTTPS Requests | ❌ | ✅ |
| TCP/UDP Sockets | ❌ | ✅ |
| `fs` (File System) | ✅ | ❌ |
| `dns.lookup` | ✅ | ❌ |
| `dns.resolve` | ❌ | ✅ |
| `crypto` (pbkdf2, scrypt, randomBytes) | ✅ | ❌ |
| `zlib` (Compression) | ✅ | ❌ |

---

## Stream Types Quick-Reference

| Type | Description | Common Example |
| :--- | :--- | :--- |
| **Readable** | Can only read data | `fs.createReadStream()`, `http.IncomingMessage` |
| **Writable** | Can only write data | `fs.createWriteStream()`, `http.ServerResponse` |
| **Duplex** | Can both read and write independently | `net.Socket` (TCP socket) |
| **Transform**| Duplex where output is computed from input | `zlib.createGzip()`, `crypto.createCipheriv()` |

---

## Cluster vs Worker Threads

| Feature | Cluster Module | Worker Threads |
| :--- | :--- | :--- |
| **Primary Use Case** | Scaling web servers across CPU cores | Offloading heavy CPU tasks from main thread |
| **Isolation** | High (Separate processes) | Low (Threads within same process) |
| **Memory** | Isolated (High memory overhead) | Shared via `SharedArrayBuffer` (Low overhead) |
| **State Sharing** | IPC via JSON messaging (Slow) | Fast direct memory access, Atomics |
| **Server Ports** | Workers can share identical TCP ports | Cannot naturally share TCP server ports |

---

## Key Built-in Module Methods

**`fs`**
- `fs.promises.readFile(path)`: Async read whole file.
- `fs.createReadStream(path)`: Stream read for large files.
- `fs.promises.writeFile(path, data)`: Async write.

**`path`**
- `path.join(__dirname, 'folder', 'file.txt')`: Safely joins paths for cross-platform.
- `path.resolve('folder')`: Resolves to absolute path from current working directory.

**`crypto`**
- `crypto.randomUUID()`: Generates UUIDv4.
- `crypto.scrypt(pwd, salt, 64, cb)`: Secure password hashing.

**`child_process`**
- `cp.exec('ls -la', cb)`: Shell command, buffers output.
- `cp.spawn('ls', ['-la'])`: Streamed output, no shell overhead.

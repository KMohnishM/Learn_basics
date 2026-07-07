# Q&A — Socket Programming

---

## 🟢 Easy

**Q1. What is a socket? What does it represent?**

A socket is an OS-provided endpoint for bidirectional network communication. It represents one end of a network connection (or, for UDP, a communication endpoint).

Internally, a socket is a file descriptor (on Unix-like systems) backed by kernel data structures that track: local IP, local port, remote IP, remote port, protocol, send/receive buffers, and TCP state.

Applications use sockets via syscalls: `socket()`, `bind()`, `listen()`, `accept()`, `connect()`, `send()`, `recv()`, `close()`.

---

**Q2. What is the purpose of `bind()`, `listen()`, and `accept()`?**

**`bind()`**: Associates a socket with a specific local IP address and port. Tells the OS: "This socket should receive packets sent to this IP:port."

**`listen()`**: Marks the socket as passive — ready to accept incoming connections. The `backlog` parameter sets how many fully-established connections the kernel can queue before the application calls `accept()`.

**`accept()`**: Dequeues the next completed connection from the accept queue and returns a NEW socket file descriptor for that specific client connection. The original listening socket remains open and continues accepting new clients.

---

**Q3. What is the difference between `send()`/`recv()` and `read()`/`write()` on a socket?**

On Unix, sockets are file descriptors. `read()` and `write()` work on sockets just like files. `send()` and `recv()` are socket-specific and add a `flags` parameter.

Important `flags`:
- `MSG_NOWAIT`: Non-blocking (return EAGAIN if no data, even if socket is blocking).
- `MSG_PEEK`: Read data without consuming it from the buffer.
- `MSG_WAITALL`: Block until the full requested amount is received.
- `MSG_OOB`: Out-of-band data (urgent).

For simple use cases, `read()`/`write()` and `send()`/`recv()` (with flags=0) are equivalent.

---

**Q4. Why do we use `htons()` and `htonl()`?**

Network protocols define multi-byte fields in **big-endian (network byte order)**. x86 CPUs are little-endian. Without conversion, a port number like `8080` would be stored and sent as bytes `[0x90, 0x1F]` (little-endian) instead of `[0x1F, 0x90]` (big-endian) — the receiving end would interpret it as a completely different port.

- `htons()`: host-to-network short (16-bit). Use for port numbers.
- `htonl()`: host-to-network long (32-bit). Use for IP addresses.
- `ntohs()`, `ntohl()`: reverse (network to host), used when reading from packets.

Always convert before putting values into socket address structures or packet headers.

---

**Q5. What is Nagle's algorithm and when would you disable it?**

Nagle's algorithm: TCP waits to accumulate data before sending — either the buffer is full (MSS) or an ACK has been received for previously sent data. Reduces the number of small packets (reduces overhead from many tiny 1-byte sends).

**When to disable (TCP_NODELAY)**:
- **Latency-sensitive protocols**: Online games, VoIP, interactive terminals (SSH), financial trading. Sending immediately is more important than minimizing packet count.
- **Request-response protocols**: If you send a request in two writes (e.g., HTTP header then body), Nagle may delay the second write waiting for an ACK — adding up to 200ms latency. `TCP_NODELAY` sends both immediately.

---

## 🟡 Medium

**Q6. Explain epoll and why it's more efficient than select() for high-concurrency servers.**

**select()**: Takes a set of ALL monitored file descriptors. Scans through ALL of them to find which are ready. O(n) per call — with 10,000 connections, checks 10,000 fds even if only 2 are ready. Also limited to 1024 fds.

**epoll()**: Kernel maintains a red-black tree of monitored fds. When a fd becomes ready, the kernel adds it to a ready list. `epoll_wait()` returns ONLY ready fds — O(1) per ready event regardless of total monitored count. No fd limit.

**Practical difference**: With 100,000 idle connections and 10 active ones, `select()` scans 100,000 fds; `epoll_wait()` returns exactly 10 entries.

**epoll modes:**
- **Level-triggered (LT, default)**: epoll notifies as long as data is available. Same semantics as select/poll. Safe but may over-notify.
- **Edge-triggered (ET, `EPOLLET`)**: epoll notifies only when state changes (new data arrived). Must read ALL available data in a single notification. More efficient but requires non-blocking sockets and careful coding.

---

**Q7. What happens in the kernel when a new TCP connection arrives? Walk through from SYN to accept() returning.**

1. **NIC receives packet** → DMA to ring buffer → interrupt fired.
2. **Interrupt handler** (softirq) processes packet: moves up the network stack.
3. **IP layer**: Validates checksum, routes to appropriate socket based on destination IP+port.
4. **TCP layer**: Sees SYN flag. Checks if a listening socket exists for this port.
   - Found: Places in **SYN queue** (incomplete queue). Sends SYN-ACK.
5. **Client sends ACK** → kernel receives it.
6. **TCP layer**: Matches ACK to SYN queue entry. Completes the 3-way handshake. Creates a new **socket** (a connected socket, different from the listening socket). Moves to **Accept queue** (complete queue).
7. **Application calls `accept()`**:
   - If accept queue has entries: dequeues one, returns a new fd to the application.
   - If accept queue is empty: `accept()` blocks (or returns EAGAIN if non-blocking).
8. **Application sends/receives** via the new fd.

**Key insight**: The TCP handshake is entirely handled by the kernel. The application is not involved until `accept()` is called. This is why a server can be slow to call `accept()` — connections still complete their handshakes.

---

**Q8. What is SO_REUSEPORT and why does nginx use it?**

`SO_REUSEPORT`: Allows multiple sockets to bind to the same IP:port. The kernel distributes incoming connections among all bound sockets (using a hash of the 5-tuple).

**The thundering herd problem** (why nginx uses SO_REUSEPORT):
Without SO_REUSEPORT: All worker processes share ONE accept queue. A new connection wakes ALL workers simultaneously (all wake up from `epoll_wait()`). Only one actually gets the connection; the others go back to sleep. Wasted context switches.

**With SO_REUSEPORT**: Each nginx worker has its own listening socket (its own accept queue). The kernel distributes connections — each worker wakes only for its own connections. No thundering herd. Better CPU core utilization. Better latency (no lock contention on the accept queue).

**Real-world**: nginx, HAProxy, and most modern high-performance servers use SO_REUSEPORT.

---

**Q9. What are Unix domain sockets? Why use them instead of TCP localhost?**

Unix domain sockets (AF_UNIX / AF_LOCAL) are sockets that communicate via a filesystem path instead of IP:port. Used for IPC between processes on the same machine.

**Advantages over TCP localhost (127.0.0.1):**
1. **Performance**: No IP or TCP overhead — no checksum, no sequence numbers, no congestion control, no TCP header processing. Typically 2-5× faster throughput than TCP localhost.
2. **Permissions**: Access controlled by filesystem permissions on the socket file (`chmod`). Only processes with permission to read/write the socket file can connect.
3. **File descriptor passing**: Unix sockets support `SCM_RIGHTS` — one process can send an open file descriptor to another process through the socket. Powerful IPC primitive.
4. **No port exhaustion**: Not bound by ephemeral port limits.

**Common uses**: nginx → PHP-FPM, application → PostgreSQL/Redis, systemd socket activation.

---

## 🔴 Hard

**Q10. Design an event-driven TCP server that handles 100,000 concurrent connections with a single thread. Describe the architecture.**

**Architecture: Non-blocking sockets + epoll event loop**

```c
// Setup
int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
setsockopt(listen_fd, SOL_SOCKET, SO_REUSEPORT, ...);
bind(listen_fd, ...);
listen(listen_fd, 1024);
fcntl(listen_fd, F_SETFL, O_NONBLOCK);  // Non-blocking

int epfd = epoll_create1(0);

// Add listening socket to epoll
struct epoll_event ev = {.events = EPOLLIN, .data.fd = listen_fd};
epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

// Event loop
struct epoll_event events[MAX_EVENTS];
while (1) {
    int n = epoll_wait(epfd, events, MAX_EVENTS, -1);
    
    for (int i = 0; i < n; i++) {
        if (events[i].data.fd == listen_fd) {
            // New connection
            while (1) {  // Accept all pending connections
                int client_fd = accept4(listen_fd, NULL, NULL, SOCK_NONBLOCK);
                if (client_fd == -1) break;  // EAGAIN = no more
                // Add client to epoll
                struct epoll_event cev = {
                    .events = EPOLLIN | EPOLLET,  // Edge-triggered
                    .data.fd = client_fd
                };
                epoll_ctl(epfd, EPOLL_CTL_ADD, client_fd, &cev);
            }
        } else {
            // Existing connection has data
            int fd = events[i].data.fd;
            handle_client(fd);  // Read all available data, process, write response
        }
    }
}
```

**Key design decisions:**
- **EPOLLET (edge-triggered)**: Called only when new data arrives, not repeatedly while data is buffered. Must read ALL available data in `handle_client()` (loop until EAGAIN).
- **Non-blocking everywhere**: `accept()` with SOCK_NONBLOCK, client sockets set non-blocking. Never block in the event loop.
- **Single thread**: No context switching overhead. No locks needed for connection state (one thread = no concurrent access).

**To scale beyond one CPU core**: Run N worker threads (N = CPU cores), each with its own epoll loop and its own listening socket (SO_REUSEPORT). Kernel distributes connections across workers. This is exactly what nginx does.

---

**Q11. What is the difference between edge-triggered and level-triggered epoll? Give a scenario where using edge-triggered mode incorrectly causes a bug.**

**Level-triggered (LT)**: epoll notifies as long as there is data to read in the buffer. If you read only 100 bytes but 1000 are available, epoll notifies you again on the next `epoll_wait()`. Familiar semantics — similar to select()/poll().

**Edge-triggered (ET)**: epoll notifies ONCE when new data arrives (state change). If you don't read all available data, epoll will NOT notify you again until MORE new data arrives — you've missed the existing data.

**Bug scenario with ET mode:**
```
1. Client sends 1000 bytes.
2. epoll_wait() returns: fd is readable.
3. Application calls recv(fd, buf, 100, 0) — reads only 100 bytes.
4. 900 bytes still in the buffer.
5. epoll_wait() is called again. No notification! (Buffer had data before; no state change occurred.)
6. Application waits forever. Client times out. 900 bytes never processed.
```

**Fix**: In ET mode, always read in a loop until `recv()` returns -1 with `errno = EAGAIN`:
```c
while (1) {
    int n = recv(fd, buf, sizeof(buf), 0);
    if (n == -1) {
        if (errno == EAGAIN) break; // All data drained
        // Handle error
    }
    if (n == 0) { close(fd); break; } // Connection closed
    process(buf, n);
}
```

**When to use ET**: High-performance servers where you want to avoid spurious wake-ups. Requires disciplined coding.
**When to use LT**: When simplicity matters more than maximum performance.

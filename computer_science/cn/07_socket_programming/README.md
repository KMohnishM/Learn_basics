# Module 7: Socket Programming & How Connections Work

---

## 1. What is a Socket?

A **socket** is a software endpoint for two-way communication between processes — either on the same machine or across a network. It's the fundamental abstraction the OS provides for network programming.

The OS identifies a network connection by the 5-tuple:
```
{Protocol, Source IP, Source Port, Destination IP, Destination Port}
```

Every socket has an associated local address (IP + port). TCP sockets also have a remote address once connected.

---

## 2. Socket Types

**Stream Socket (SOCK_STREAM)**: Uses TCP. Provides reliable, ordered, byte-stream delivery. The application sees a continuous stream of bytes with no message boundaries.

**Datagram Socket (SOCK_DGRAM)**: Uses UDP. Unreliable, connectionless. Each `sendto()` sends one datagram; each `recvfrom()` receives one datagram. Message boundaries preserved.

**Raw Socket (SOCK_RAW)**: Bypasses the transport layer — application constructs IP packets directly. Used by ping (constructs ICMP), traceroute, packet sniffers. Requires root/admin privileges.

---

## 3. The Client-Server Socket Flow

### Server Side

```c
// 1. Create socket
int server_fd = socket(AF_INET, SOCK_STREAM, 0);
//   AF_INET = IPv4, AF_INET6 = IPv6, AF_UNIX = Unix domain socket

// 2. Set socket options (optional but important)
setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
// SO_REUSEADDR: allows rebinding to a port in TIME_WAIT state

// 3. Bind to an IP and port
struct sockaddr_in addr = {
    .sin_family = AF_INET,
    .sin_port = htons(8080),      // htons: host-to-network byte order
    .sin_addr.s_addr = INADDR_ANY // Listen on all interfaces
};
bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));

// 4. Listen (mark socket as passive — ready to accept connections)
listen(server_fd, backlog);
// backlog: max pending connections in the accept queue (typically 128-1024)

// 5. Accept connections in a loop
while (1) {
    struct sockaddr_in client_addr;
    socklen_t len = sizeof(client_addr);
    int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &len);
    // accept() blocks until a client connects, returns a NEW fd for this connection
    
    // Handle client in a new thread/process:
    handle_client(client_fd);
    close(client_fd);
}
```

### Client Side

```c
// 1. Create socket
int sock_fd = socket(AF_INET, SOCK_STREAM, 0);

// 2. Connect to server
struct sockaddr_in server_addr = {
    .sin_family = AF_INET,
    .sin_port = htons(8080),
};
inet_pton(AF_INET, "192.168.1.1", &server_addr.sin_addr);
connect(sock_fd, (struct sockaddr*)&server_addr, sizeof(server_addr));
// connect() triggers the TCP 3-way handshake

// 3. Send and receive
send(sock_fd, "Hello, server!", 14, 0);
char buf[1024];
int n = recv(sock_fd, buf, sizeof(buf), 0);
// recv() blocks until data is available

// 4. Close
close(sock_fd);
// Triggers TCP 4-way FIN teardown
```

---

## 4. The Listen Backlog and Accept Queue

When a client connects, the server's kernel performs the TCP 3-way handshake automatically — the application is not involved during the handshake. The kernel maintains two queues:

```
Clients connecting:
   → SYN received → [SYN Queue / Incomplete Queue]
   → Handshake complete → [Accept Queue / Complete Queue]
   → accept() called → removes from accept queue → returns fd
```

**SYN Queue (Incomplete Queue)**: Half-open connections (SYN received, SYN-ACK sent, ACK not yet received). Size: `net.ipv4.tcp_max_syn_backlog`.

**Accept Queue (Complete Queue)**: Fully established connections waiting for the application to call `accept()`. Size: `min(backlog, net.core.somaxconn)`.

**If Accept Queue is full**: New completed connections are silently dropped (or RST sent). This is why slow servers miss connections even though the TCP handshake succeeded.

**Linux defaults**: `somaxconn = 4096` (changed from 128 in recent kernels). High-traffic servers set `backlog = 1024` or higher.

---

## 5. Byte Order — Network vs Host

**Problem**: Different CPU architectures store multi-byte integers differently.
- **Big-endian**: Most significant byte at lowest address. Example: 0x0050 stored as [0x00, 0x50].
- **Little-endian**: Least significant byte at lowest address. Example: 0x0050 stored as [0x50, 0x00]. (x86/x86-64 is little-endian.)

**Network byte order** is big-endian (defined in RFC). All multi-byte values in packet headers (port numbers, IP addresses, etc.) must be in network byte order.

```c
htons()  // Host to Network Short (16-bit port numbers)
htonl()  // Host to Network Long  (32-bit IP addresses, etc.)
ntohs()  // Network to Host Short
ntohl()  // Network to Host Long
```

Always use these when putting values into or extracting from packet structures.

---

## 6. I/O Multiplexing — Handling Multiple Connections

A naive server creates one thread per connection. With 10,000 connections, that's 10,000 threads — each consuming ~2MB of stack = 20GB RAM. Not scalable.

### select()

```c
fd_set readfds;
FD_ZERO(&readfds);
FD_SET(sock1, &readfds);
FD_SET(sock2, &readfds);

struct timeval timeout = {5, 0}; // 5 second timeout
int ready = select(max_fd + 1, &readfds, NULL, NULL, &timeout);
// Block until at least one fd is ready to read (or timeout)
// After return: check FD_ISSET(fd, &readfds) for each fd
```

**Limitations**: Max 1024 file descriptors (FD_SETSIZE). O(n) scanning of all fds. `readfds` is modified by select() and must be re-initialized every call.

### poll()

Similar to select() but no 1024-fd limit. Uses a `pollfd` array. Still O(n) scanning.

### epoll() (Linux — Scalable)

```c
int epfd = epoll_create1(0);

struct epoll_event ev;
ev.events = EPOLLIN; // notify when readable
ev.data.fd = sock_fd;
epoll_ctl(epfd, EPOLL_CTL_ADD, sock_fd, &ev);

struct epoll_event events[MAX_EVENTS];
int n = epoll_wait(epfd, events, MAX_EVENTS, timeout_ms);
// Blocks until at least one event. Returns ONLY ready fds.
```

**Advantages over select/poll:**
- **O(1) per event** (regardless of total monitored fds): Only ready fds are returned, not all monitored fds.
- **No limit on file descriptors**: Can handle millions of connections.
- **Edge-triggered mode (EPOLLET)**: Notified only when the state changes (new data arrives), not repeatedly while data is available. More efficient, but requires careful coding (must drain entire buffer on each notification).

**Level-triggered (default)**: Notified as long as data is available. Simpler to use.

### kqueue (BSD/macOS equivalent of epoll)

Similar to epoll — event-based, O(1) per event. Used in nginx on BSD/macOS.

### io_uring (Linux 5.1+)

The newest and most powerful Linux I/O model. Uses shared ring buffers between kernel and userspace — submits I/O requests and collects completions WITHOUT any syscall overhead in the common case. Used by modern high-performance servers.

---

## 7. Non-blocking Sockets

By default, socket operations block: `recv()` waits until data arrives; `connect()` waits until connection is established.

**Non-blocking mode**: `fcntl(fd, F_SETFL, O_NONBLOCK)`. Now:
- `recv()` returns -1 with `errno = EAGAIN` if no data is available.
- `connect()` returns -1 with `errno = EINPROGRESS` immediately; use epoll to wait for writability to detect completion.
- `accept()` returns -1 with `errno = EAGAIN` if no pending connections.

Non-blocking sockets + epoll is the standard model for high-performance event-driven servers (nginx, Node.js event loop, etc.).

---

## 8. Unix Domain Sockets

**Unix domain sockets (AF_UNIX)** allow IPC (inter-process communication) between processes on the same machine. Instead of IP:port, they use a **file system path** as the address.

```c
// Server:
struct sockaddr_un addr;
addr.sun_family = AF_UNIX;
strcpy(addr.sun_path, "/tmp/myapp.sock");
bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));
```

**Advantages over TCP for local IPC:**
- No TCP overhead (no handshakes, no IP stack processing, no checksumming for loopback)
- Higher throughput than TCP localhost (2-10× faster for local communication)
- Can pass file descriptors between processes (fd passing via `SCM_RIGHTS`)
- Filesystem-based permissions (who can connect = who can open the socket file)

**Common uses**: PostgreSQL, Redis, and nginx all accept Unix socket connections. Application → database communication is often via Unix socket for lower latency.

---

## 9. Socket Options

Important socket options set via `setsockopt()`:

```c
// Allow rebinding to a port in TIME_WAIT
setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

// Allow multiple sockets to bind the same port (load balancing)
setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt));

// Disable Nagle's algorithm (send immediately, don't wait for buffer to fill)
setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &opt, sizeof(opt));

// Set send/receive buffer sizes
setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &size, sizeof(size));
setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size));

// Set connection timeout (SO_KEEPALIVE sends TCP keepalive probes)
setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &opt, sizeof(opt));
```

**Nagle's Algorithm**: TCP batches small sends together (waits up to 200ms or until ACK arrives) to reduce packet count. Good for throughput; bad for latency-sensitive apps (gaming, VoIP, interactive terminals). `TCP_NODELAY` disables it.

**SO_REUSEPORT**: Multiple processes can bind the same port. The kernel load-balances incoming connections among them. Used by nginx (multiple worker processes all bind port 80) — eliminates the "thundering herd" problem of all workers waking on a single accept queue.

---

## 10. The C10K Problem and Modern Solutions

**C10K problem** (coined 1999 by Dan Kegel): How to handle 10,000 simultaneous connections on a single server?

Traditional thread-per-connection model fails at scale:
- 10,000 threads × 2MB stack = 20GB RAM just for stacks
- Context switching overhead between 10,000 threads
- OS scheduler struggles with thousands of runnable threads

**Solutions that enabled modern web scale:**

**Event-driven architecture (single-threaded event loop)**: One thread, non-blocking I/O, epoll. Handle all connections in one loop. When data arrives on ANY connection, process it. No thread switching. Used by: Node.js (JavaScript event loop), nginx.

```
while (true) {
    events = epoll_wait(epfd, ...)  // block until something is ready
    for each ready fd:
        read/process/write
}
```

**Thread pool + async I/O**: Multiple threads (one per CPU), each running an event loop. Used by: Go (goroutines + netpoller), Tokio (Rust async runtime).

**C10M problem** (2013): Can we handle 10 million connections? Achieved by: kernel bypass (DPDK — direct hardware access), zero-copy networking, RDMA.

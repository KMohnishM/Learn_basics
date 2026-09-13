# Cheat Sheet — Socket Programming

## Socket Types
| Type | Protocol | Reliable? | Boundaries? | Use |
|------|----------|:---------:|:-----------:|-----|
| SOCK_STREAM | TCP | ✅ | ❌ stream | HTTP, SSH, DB |
| SOCK_DGRAM | UDP | ❌ | ✅ preserved | DNS, VoIP, gaming |
| SOCK_RAW | IP | — | — | ping, traceroute |

## Server Socket Lifecycle
```
socket()   → create file descriptor
  ↓
setsockopt() → SO_REUSEADDR (allow port reuse after TIME_WAIT)
  ↓
bind()     → associate with IP:port
  ↓
listen(fd, backlog) → mark as passive, set queue size
  ↓
accept()   → block until connection, returns NEW fd for each client
  ↓
send()/recv() → communicate
  ↓
close()    → triggers FIN teardown
```

## Client Socket Lifecycle
```
socket() → connect() [3-way handshake] → send()/recv() → close()
```

## Kernel Accept Queues
```
Client SYN arrives:
  → SYN Queue (incomplete): handshake in progress
  → ACK received → Accept Queue (complete): waiting for accept()
  → accept() called → returns fd to application

If Accept Queue full → new connections dropped silently
sysctl:
  net.ipv4.tcp_max_syn_backlog  (SYN queue size)
  net.core.somaxconn            (Accept queue size, default 4096)
```

## Byte Order Conversion
```
htons(x)  → Host to Network Short  (16-bit, use for ports)
htonl(x)  → Host to Network Long   (32-bit, use for IPv4 addr)
ntohs(x)  → Network to Host Short
ntohl(x)  → Network to Host Long

Network byte order = Big-endian
x86 = Little-endian → MUST convert
```

## I/O Multiplexing Comparison
| Method | Max FDs | Complexity | Scalability | Notes |
|--------|:-------:|:---------:|:-----------:|-------|
| select() | 1024 | O(n) scan | ❌ Poor | Portable |
| poll() | Unlimited | O(n) scan | ❌ Poor | No 1024 limit |
| epoll() | Unlimited | O(1)/event | ✅ Excellent | Linux only |
| kqueue() | Unlimited | O(1)/event | ✅ Excellent | BSD/macOS |
| io_uring | Unlimited | O(1), zero-copy | ✅ Best | Linux 5.1+ |

## epoll API
```c
int epfd = epoll_create1(0);

// Add fd to watch
struct epoll_event ev = {.events = EPOLLIN, .data.fd = fd};
epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &ev);

// Wait for events (returns only READY fds)
int n = epoll_wait(epfd, events, MAX_EVENTS, timeout_ms);

// Modify or remove
epoll_ctl(epfd, EPOLL_CTL_MOD, fd, &ev);
epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
```

## Edge-Triggered vs Level-Triggered
| | Level-Triggered (default) | Edge-Triggered (EPOLLET) |
|-|--------------------------|--------------------------|
| When notified | As long as data available | Only when NEW data arrives |
| Must drain buffer | ❌ (can read partially) | ✅ (must loop until EAGAIN) |
| Risk | Spurious wake-ups | Miss data if don't drain |
| Complexity | Simple | Requires careful coding |

## Key Socket Options
```c
SO_REUSEADDR   → rebind port in TIME_WAIT
SO_REUSEPORT   → multiple processes share same port (no thundering herd)
TCP_NODELAY    → disable Nagle's algorithm (send immediately)
SO_KEEPALIVE   → send TCP keepalive probes (detect dead connections)
SO_SNDBUF/RCVBUF → set send/receive buffer sizes
```

## Unix Domain Sockets vs TCP Localhost
| | Unix Domain Socket | TCP Localhost |
|-|-------------------|---------------|
| Address | Filesystem path | 127.0.0.1:port |
| Speed | 2-5× faster | Standard |
| Overhead | No IP/TCP processing | Full TCP stack |
| Permissions | Filesystem (chmod) | Port-based |
| FD passing | ✅ SCM_RIGHTS | ❌ |
| Use | nginx↔PHP, app↔Redis | Cross-host protocols |

## Non-blocking Socket Pattern
```c
fcntl(fd, F_SETFL, O_NONBLOCK);

// recv loop for edge-triggered epoll:
while (1) {
    int n = recv(fd, buf, sizeof(buf), 0);
    if (n == -1 && errno == EAGAIN) break; // All data read
    if (n == 0) { close(fd); break; }      // Connection closed
    if (n < 0) { handle_error(); break; }
    process(buf, n);
}
```

## C10K Solutions
```
Problem: 10,000 concurrent connections with one server

Traditional (thread-per-conn): 10K threads × 2MB = 20GB RAM ❌

Solutions:
  1. Event loop + epoll (nginx, Node.js): 1 thread, O(1) per event ✅
  2. Thread pool + async I/O (Go, Rust/Tokio): N threads (N=cores) ✅
  3. SO_REUSEPORT: N workers each with own epoll loop ✅

C10M: kernel bypass (DPDK), zero-copy, RDMA for 10M connections
```

## Key System Calls
```
socket(domain, type, proto)   → create socket fd
bind(fd, addr, addrlen)       → assign local address
listen(fd, backlog)           → mark passive
accept(fd, addr, addrlen)     → get client fd (blocks)
accept4(fd, addr, addrlen, flags) → accept with SOCK_NONBLOCK
connect(fd, addr, addrlen)    → initiate connection
send(fd, buf, len, flags)     → send data
recv(fd, buf, len, flags)     → receive data
sendto/recvfrom               → UDP (includes address)
close(fd)                     → close socket (FIN if TCP)
shutdown(fd, SHUT_RDWR)       → shutdown without close
```

# Cheat Sheet — Transport Layer

## TCP 3-Way Handshake
```
Client              Server
  │── SYN (seq=x) ──────────→ │   "Let's connect. My seq starts at x."
  │← SYN-ACK (seq=y,ack=x+1) │   "OK. My seq=y. I expect x+1 from you."
  │── ACK (ack=y+1) ─────────→ │   "I expect y+1 from you. Connected!"
```

## TCP 4-Way Teardown
```
Client              Server
  │── FIN (seq=u) ──────────→ │   "I'm done sending."
  │← ACK (ack=u+1) ──────────│   "OK, but I may still send."
  │                            │   [server finishes sending...]
  │← FIN (seq=v) ─────────────│   "I'm done sending too."
  │── ACK (ack=v+1) ─────────→│   "Acknowledged."
  │ [TIME_WAIT 2×MSL (~2 min)] │
```

## TCP Header Key Fields
| Field | Bits | Purpose |
|-------|------|---------|
| Source/Dst Port | 16 each | Process identification |
| Sequence # | 32 | Byte position of first byte in segment |
| Acknowledgment # | 32 | Next byte expected (cumulative) |
| Window Size | 16 | Receiver buffer available (flow control) |
| Flags | 6+ | SYN/ACK/FIN/RST/PSH/URG/ECE/CWR |
| Header Length | 4 | Header size in 32-bit words (min 5=20B) |

## Control Flags
```
SYN: Establish connection (seq# sync)
ACK: Acknowledgment# valid
FIN: No more data from this side
RST: Abort connection immediately
PSH: Deliver data to app immediately
URG: Urgent data (rarely used)
ECE/CWR: Explicit Congestion Notification
```

## TCP Congestion Control
```
State:           Action on:         cwnd change
Slow Start       Each ACK           +1 MSS (doubles per RTT)
Cong. Avoidance  Each RTT           +1 MSS (linear)
Timeout          Packet loss        ssthresh=cwnd/2, cwnd=1, restart SS
Fast Retransmit  3 dup ACKs        ssthresh=cwnd/2, cwnd=ssthresh
```

## AIMD
```
Additive Increase: cwnd += 1 MSS per RTT (probing for bandwidth)
Multiplicative Decrease: cwnd /= 2 on loss (react strongly)
Result: Fair sharing of bottleneck bandwidth over time
```

## Slow Start Threshold (ssthresh)
```
Initial: very large (or last cwnd/2 from previous connection)
After timeout: ssthresh = cwnd/2, restart with cwnd=1
After 3 dup ACKs: ssthresh = cwnd/2, cwnd = ssthresh (fast recovery)
```

## Flow Control
```
rwnd = receiver's advertised window (free buffer space)
Sender: never have more than rwnd bytes unacknowledged
rwnd = 0: sender stops (sends 1-byte window probe periodically)
```

## Throughput Formula
```
Throughput ≈ min(rwnd, cwnd) / RTT

BDP (Bandwidth-Delay Product) = bandwidth × RTT
  = amount of data "in flight" to fill the pipe

Example: 1 Gbps link, 100ms RTT
  BDP = 10^9 × 0.1 = 100 MB (need 100MB window to saturate link!)
  Default 64KB window only achieves: 65536 / 0.1 ≈ 5 Mbps
  → Use TCP Window Scale option (up to 1GB window)
```

## TCP vs UDP
| Feature | TCP | UDP |
|---------|:---:|:---:|
| Connection | ✅ | ❌ |
| Reliability | ✅ | ❌ |
| Ordering | ✅ | ❌ |
| Flow Control | ✅ | ❌ |
| Congestion Control | ✅ | ❌ |
| Header Size | 20-60B | 8B |
| Message Boundaries | ❌ stream | ✅ preserved |
| Use | HTTP,SSH,FTP | DNS,VoIP,gaming |

## SYN Flood & SYN Cookies
```
Attack: flood server with SYN (spoofed src IPs) → fill half-open table

SYN Cookie defense:
  Server: encode {src IP, port, dst IP, port, time, secret} in ISN of SYN-ACK
  Server: discard all state (no half-open entry created)
  Client ACK arrives: ACK# = ISN+1, server recomputes hash, verifies, creates state
  
  Result: SYN flood wastes nothing; no spoofed ACK possible (IPs are spoofed)
```

## Congestion Algorithms
| Algorithm | Default In | Key Idea |
|-----------|-----------|---------|
| TCP Reno | Legacy | AIMD, loss-based |
| TCP CUBIC | Linux (since 2.6.19) | Cubic window function, faster recovery |
| BBR | Google/Linux | Model-based: estimate bandwidth+RTT, not loss-based |

## TIME_WAIT
```
Duration: 2 × MSL (MSL ≈ 60s → TIME_WAIT ≈ 120s)
Purpose:
  1. Final ACK might be lost → server retransmits FIN → we re-ACK
  2. Old packets from this connection expire (max TTL × 2 for round trip)

Problem: High-traffic servers accumulate many TIME_WAIT sockets
Fix: tcp_tw_reuse, SO_REUSEADDR, reduce MSL
```

## Key Numbers
```
TCP min header:    20 bytes
TCP max header:    60 bytes (with options)
UDP header:        8 bytes (fixed)
Default MSS:       1460 bytes (1500 MTU - 20 IP header - 20 TCP header)
Default TCP window: 65,535 bytes (without window scale)
Max TCP window:    ~1 GB (with window scale option, scale factor up to 14)
TIME_WAIT:         2 × 60s = 120 seconds (typical)
Fast retransmit:   After 3 duplicate ACKs
```

# Module 4: Transport Layer — TCP & UDP

---

## 1. The Transport Layer's Role

The Transport layer bridges the gap between the network (which delivers packets host-to-host) and applications (which need process-to-process communication). It adds:

- **Port numbers**: Multiplexing/demultiplexing — multiple processes on the same host can use the network simultaneously.
- **Error detection**: UDP: checksum only. TCP: checksum + retransmission.
- **Reliability**: TCP guarantees every byte arrives in order, exactly once.
- **Flow control**: TCP prevents a fast sender from overwhelming a slow receiver.
- **Congestion control**: TCP detects and responds to network congestion.

---

## 2. Ports and Multiplexing

**Port numbers** are 16-bit integers (0–65,535). Each network connection is identified by a **5-tuple**: `{protocol, source IP, source port, destination IP, destination port}`.

This 5-tuple is how the kernel demultiplexes incoming packets to the correct process. When a TCP SYN arrives, the kernel looks up which socket is listening on `{destination IP, destination port}` and delivers the connection to it.

A server can handle thousands of simultaneous connections on the same port (e.g., port 80) because each connection has a different source IP+port, making a unique 5-tuple.

---

## 3. UDP — User Datagram Protocol

UDP is a **connectionless, unreliable, lightweight** transport protocol.

### UDP Header (8 bytes — extremely small)

```
┌──────────────────┬──────────────────┐
│   Source Port    │  Destination Port │  (2 + 2 = 4 bytes)
├──────────────────┼──────────────────┤
│     Length       │    Checksum       │  (2 + 2 = 4 bytes)
└──────────────────┴──────────────────┘
```

**Header fields:**
- **Source Port (16 bits)**: Sending process's port. Optional in UDP (can be 0 if reply not needed).
- **Destination Port (16 bits)**: Target process's port.
- **Length (16 bits)**: Length of UDP header + data in bytes.
- **Checksum (16 bits)**: Optional error detection (mandatory in IPv6). Covers UDP header + data + pseudo-header (source IP, dest IP, protocol).

### UDP Characteristics

- **No connection setup**: No handshake. Send immediately.
- **No reliability**: Dropped, duplicated, or reordered packets are not detected or corrected.
- **No flow control**: Sender can transmit at any rate.
- **No congestion control**: UDP doesn't slow down during congestion.
- **Message boundaries preserved**: If you send 100 bytes, the receiver gets exactly one 100-byte message (not fragmented into pieces like TCP streams).

### When to Use UDP

UDP is the right choice when:
- **Speed matters more than reliability**: Live video streaming, online gaming, VoIP — a dropped frame is better than a delayed one.
- **Application handles its own reliability**: QUIC (HTTP/3) builds reliability on top of UDP.
- **Small request-response**: DNS — a query fits in one packet; if it's lost, just retry. TCP overhead for a one-round-trip DNS query would be wasteful.
- **Broadcast/multicast**: UDP supports one-to-many (TCP is point-to-point).
- **Short lived**: DHCP, SNMP, TFTP.

---

## 4. TCP — Transmission Control Protocol

TCP is a **connection-oriented, reliable, stream-based** transport protocol. It guarantees that data sent by the sender arrives at the receiver in the correct order, without duplicates, and without corruption.

### TCP Header (20 bytes minimum, up to 60 bytes with options)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |       |C|E|U|A|P|R|S|F|                              |
| Offset|  Rsv  |W|C|R|C|S|S|Y|I|       Window Size           |
|       |       |R|E|G|K|H|T|N|N|                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |         Urgent Pointer        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Options (if Data Offset > 5)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Critical fields:**

- **Source/Destination Port (16 bits each)**: Process identification.
- **Sequence Number (32 bits)**: Byte offset of the first byte in this segment, relative to the ISN (Initial Sequence Number). Used for ordering and detecting missing data.
- **Acknowledgment Number (32 bits)**: The next byte the receiver expects. Cumulative: "I've received everything up to byte N-1, send me byte N." Only valid when ACK flag is set.
- **Data Offset / Header Length (4 bits)**: TCP header length in 32-bit words (min 5 = 20 bytes, max 15 = 60 bytes).
- **Control Flags (6+2 bits)**:
  - **SYN**: Synchronize sequence numbers (used in connection setup).
  - **ACK**: Acknowledgment number is valid.
  - **FIN**: No more data from sender (used in connection teardown).
  - **RST**: Reset connection (abort immediately).
  - **PSH**: Push data to application immediately (don't buffer).
  - **URG**: Urgent data present (pointed to by Urgent Pointer).
  - **ECE/CWR**: ECN — Explicit Congestion Notification.
- **Window Size (16 bits)**: Number of bytes the receiver is willing to accept (receive buffer space). Implements flow control. Scaled by the TCP Window Scale Option (window scale factor up to 2^14, allowing windows up to 1GB).
- **Checksum (16 bits)**: Error detection over header + data + pseudo-header.
- **Options**: MSS (Maximum Segment Size), Window Scale, SACK (Selective Acknowledgment), Timestamps, etc.

---

## 5. TCP 3-Way Handshake — Connection Establishment

```
Client                              Server
  |                                   |
  |──── SYN (seq=x) ──────────────→  |  Client starts: "Let's connect. My seq starts at x."
  |                                   |  Server: "OK, and my seq starts at y."
  |←─── SYN-ACK (seq=y, ack=x+1) ── |  Server: "I acknowledge x; expect x+1 next."
  |                                   |
  |──── ACK (seq=x+1, ack=y+1) ────→ |  Client: "I acknowledge y; expect y+1 next."
  |                                   |
  [Connection established]
```

**Why 3-way (not 2-way)?**
- 2-way would establish the connection from the client's perspective but the server would never know the client received the SYN-ACK.
- 3 messages ensure BOTH sides have confirmed that both directions of communication work.
- A 2-way handshake is vulnerable to old, delayed SYN packets accidentally establishing stale connections.

**ISN (Initial Sequence Number)**: Chosen randomly (not starting from 0) to:
1. **Security**: If ISN were predictable, an attacker could inject fake TCP segments.
2. **Ambiguity**: Packets from previous connections with the same 5-tuple might be in transit — random ISN prevents them from being misinterpreted.

**Half-open connections**: During the handshake, the server allocates state after receiving SYN. An attacker can send many SYNs with forged source IPs (the SYN-ACK goes nowhere), filling the server's half-open connection table — a **SYN flood attack**.

**Defense**: **SYN cookies** — the server doesn't allocate state for a SYN. Instead, it encodes connection info into the ISN of the SYN-ACK. State is only created when the ACK arrives (client proves it received the SYN-ACK). The SYN-ACK ISN is computed as a hash of `{src IP, src port, dst IP, dst port, secret}`.

---

## 6. TCP Connection Teardown — 4-Way FIN Handshake

TCP connections are **full-duplex** — data flows in both directions independently. Each direction must be closed independently.

```
Client                              Server
  |──── FIN (seq=u) ──────────────→ |  Client: "I'm done sending."
  |←─── ACK (ack=u+1) ──────────── |  Server: "Noted. (But I might still send data.)"
  |                                  |  [Server may continue sending...]
  |←─── FIN (seq=v) ──────────────  |  Server: "I'm done sending too."
  |──── ACK (ack=v+1) ────────────→ |  Client: "Noted."
  |                                  |
  [Client waits TIME_WAIT (2×MSL)]
```

**TIME_WAIT state**: After sending the final ACK, the client enters TIME_WAIT for **2 × MSL (Maximum Segment Lifetime)**, typically 2 minutes (MSL = 60s on many systems).

**Why TIME_WAIT?**
1. The final ACK might be lost → server will retransmit FIN → client must still be alive to re-send ACK.
2. Ensures all packets from the old connection have expired before the same 5-tuple is reused. Prevents old packets from being interpreted as belonging to a new connection.

**TIME_WAIT storms**: High-volume servers closing many connections rapidly accumulate thousands of TIME_WAIT sockets. Solutions: `SO_REUSEADDR`, `tcp_tw_reuse` (reuse TIME_WAIT sockets for new outgoing connections to different destinations), reduce TIME_WAIT duration.

---

## 7. TCP Reliability — Sequence Numbers and ACKs

**Cumulative ACK**: The ACK number tells the sender "I've received all bytes up to N-1, send me N." If segment 1 (bytes 1-100) is lost but segment 2 (bytes 101-200) arrives, the receiver still ACKs 1 (next expected byte) because bytes 1-100 are missing — it can't acknowledge beyond the gap.

**Retransmission**: Sender starts a retransmission timer when sending a segment. If no ACK received within RTO (Retransmission Timeout), the segment is retransmitted. RTO is estimated based on measured RTT.

**RTT Estimation**:
```
SRTT = (1-α) × SRTT + α × RTT_sample     (α = 0.125)
RTTVAR = (1-β) × RTTVAR + β × |SRTT - RTT_sample|  (β = 0.25)
RTO = SRTT + 4 × RTTVAR
```

**Duplicate ACKs**: If sender sends segments 1, 2, 3, 4 and segment 2 is lost:
- Receiver gets 1 → ACK 2 (OK)
- Receiver gets 3 → ACK 2 (duplicate — "still waiting for 2")
- Receiver gets 4 → ACK 2 (duplicate — "still waiting for 2")
- Sender gets 3 duplicate ACKs for byte 2 → **Fast Retransmit**: retransmit segment 2 immediately without waiting for RTO.

**SACK (Selective Acknowledgment)**: Extension to TCP that allows receivers to specify exactly which ranges of bytes were received (not just cumulative). Sender only retransmits the specific missing segments.

---

## 8. TCP Flow Control — Sliding Window

The receiver advertises its available buffer space in the **Window Size** field of every ACK. The sender may not have more than `window_size` bytes in flight (sent but not yet acknowledged).

```
Sender side:
[Acknowledged | Sent, not ACKed | Can send now | Cannot send yet]
              ↑                  ↑              ↑
         send_base        next_seq_num    send_base + rwnd

If rwnd = 0: sender stops. Sender probes with 1-byte "window probe" to detect when receiver has free space.
```

**Zero window**: When the receiver's buffer is full, it sends an ACK with Window Size = 0. The sender immediately stops sending. This is flow control in action.

---

## 9. TCP Congestion Control

Flow control prevents overwhelming the receiver. Congestion control prevents overwhelming the **network** (routers, links) between sender and receiver.

TCP cannot directly observe the network's state. It infers congestion from:
1. **Packet loss** (implied by timeout or 3 duplicate ACKs)
2. **RTT increase** (queuing delay is rising)
3. **ECN (Explicit Congestion Notification)**: routers mark packets when queues are filling — TCP reacts before loss occurs.

**Congestion Window (cwnd)**: Sender's self-imposed limit. Actual send rate = min(rwnd, cwnd) / RTT.

### Slow Start

Connection starts with cwnd = 1 MSS (Maximum Segment Size). Each ACK received doubles cwnd (exponential growth).

```
cwnd: 1 → 2 → 4 → 8 → 16 → ... until ssthresh or loss
```

"Slow start" is a misnomer — it's exponential growth. It's called "slow" because it starts from 1 MSS instead of flooding the network immediately.

### Congestion Avoidance

When cwnd reaches **ssthresh** (slow start threshold), TCP switches to linear growth:
- Each RTT (not each ACK): cwnd += 1 MSS

```
cwnd: ssthresh → ssthresh+1 → ssthresh+2 → ... (linear)
```

This is the additive increase phase of **AIMD (Additive Increase, Multiplicative Decrease)**.

### Congestion Events

**Timeout (severe congestion)**:
- ssthresh = cwnd / 2
- cwnd = 1 MSS
- Restart slow start

**3 Duplicate ACKs (fast retransmit, mild congestion)**:
- ssthresh = cwnd / 2
- cwnd = ssthresh (TCP Reno) or cwnd = ssthresh + 3 (TCP Reno variant)
- Enter Congestion Avoidance

### AIMD — Additive Increase Multiplicative Decrease

The fundamental TCP behavior:
- **Additive Increase**: Gently probe for more bandwidth. +1 MSS per RTT during congestion avoidance.
- **Multiplicative Decrease**: React strongly to congestion. cwnd = cwnd / 2 on packet loss.

AIMD is fair: if two TCP flows share a bottleneck link, they converge to equal shares over time (mathematical proof via AIMD convergence).

### Modern Congestion Control Algorithms

**TCP CUBIC** (Linux default since 2.6.19): Uses a cubic function of time since last congestion event for window growth — grows faster than Reno in high-bandwidth, long-delay paths. Window recovery curve looks like a cubic polynomial.

**BBR (Bottleneck Bandwidth and RTT)** (Google, 2016): Models the network to explicitly estimate available bandwidth and RTT at the bottleneck. Doesn't rely on packet loss as a signal. More efficient on high-bandwidth, lossy links (where random loss was incorrectly interpreted as congestion by Reno).

---

## 10. TCP vs UDP Summary

| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | ✅ Connection-oriented | ❌ Connectionless |
| Reliability | ✅ Guaranteed delivery, no loss | ❌ No guarantee |
| Ordering | ✅ In-order delivery | ❌ No ordering |
| Duplicates | ✅ No duplicates | ❌ Duplicates possible |
| Flow Control | ✅ Sliding window | ❌ None |
| Congestion Control | ✅ AIMD, CUBIC, BBR | ❌ None |
| Header Size | 20–60 bytes | 8 bytes |
| Speed | Slower (overhead) | Faster (minimal overhead) |
| Message Boundaries | ❌ Stream (no boundaries) | ✅ Preserved |
| Use Cases | HTTP, SSH, FTP, email | DNS, DHCP, VoIP, streaming, gaming |

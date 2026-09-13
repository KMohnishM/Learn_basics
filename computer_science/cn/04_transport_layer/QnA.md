# Q&A — Transport Layer

---

## 🟢 Easy

**Q1. What is the difference between TCP and UDP?**

| TCP | UDP |
|-----|-----|
| Connection-oriented (3-way handshake) | Connectionless |
| Reliable: guaranteed delivery, ordering, no duplicates | Unreliable: may lose, reorder, duplicate |
| Flow control + congestion control | No flow/congestion control |
| 20-byte header | 8-byte header |
| Slower, higher overhead | Faster, lower overhead |
| HTTP, SSH, FTP, database connections | DNS, VoIP, streaming, gaming |

---

**Q2. What is a port number and why is it needed?**

A port number is a 16-bit integer (0–65,535) that identifies a specific process/service on a host. Multiple applications can run on the same host simultaneously (web server, SSH, database). Port numbers allow the OS to demultiplex incoming packets to the correct application.

A connection is uniquely identified by: `{protocol, src IP, src port, dst IP, dst port}` (the 5-tuple). Port 80 on a server can handle thousands of simultaneous connections because each has a different client IP + source port.

---

**Q3. Explain the TCP 3-way handshake.**

```
1. Client → Server: SYN (seq=x)          "Let's connect, my sequence starts at x"
2. Server → Client: SYN-ACK (seq=y, ack=x+1)  "OK, my seq=y, I expect your x+1 next"
3. Client → Server: ACK (ack=y+1)         "Acknowledged, I expect your y+1 next"
```

Purpose:
- Both sides agree on initial sequence numbers (needed for reliable delivery)
- Both sides confirm the connection is bidirectional (both TX and RX paths work)
- Both sides allocate connection state

---

**Q4. What is the sequence number in TCP and why does it start randomly?**

The sequence number identifies the byte position of the first byte in a TCP segment relative to the stream. It enables the receiver to detect missing segments, reorder out-of-order segments, and identify duplicates.

**Random ISN (Initial Sequence Number)**: Starting from a random number (not 0) serves two purposes:
1. **Security**: Predictable sequence numbers allow attackers to forge TCP segments and inject malicious data.
2. **Ambiguity prevention**: If the same 5-tuple is reused for a new connection, old packets still in transit could be misinterpreted as belonging to the new connection if sequence numbers overlapped.

---

**Q5. What is the difference between flow control and congestion control in TCP?**

**Flow control**: Prevents the sender from overwhelming the **receiver's buffer**. Managed via the receiver's advertised window size in TCP headers. If the receiver's buffer is full, window=0 tells the sender to stop.

**Congestion control**: Prevents the sender from overwhelming the **network** (routers/links between endpoints). TCP infers congestion from packet loss or RTT increase and reduces its send rate (AIMD — slow down by half on loss, increase linearly otherwise).

Flow control is a bilateral agreement between sender and receiver. Congestion control is a response to inferred network conditions.

---

## 🟡 Medium

**Q6. What is TCP's TIME_WAIT state? Why does it last 2×MSL?**

After sending the final ACK (in the 4-way teardown), the active closer (usually client) enters TIME_WAIT and waits for **2 × MSL (Maximum Segment Lifetime)** before fully closing.

**Why 2×MSL (typically ~120 seconds)?**

1. **Lost final ACK**: If the client's ACK (to the server's FIN) is lost, the server retransmits its FIN. The client must still be alive to re-ACK. MSL is the max time a packet can be in the network, so 2×MSL is enough time for the FIN to reach the client and the re-ACK to reach the server.

2. **Old packet expiration**: All packets from the closed connection have a TTL. 2×MSL guarantees that every packet from the old connection has been dropped by the network before the same 5-tuple can be reused for a new connection. This prevents old packets from being misinterpreted as new connection data.

**Problem in practice**: High-traffic servers close thousands of connections per second → thousands of TIME_WAIT sockets accumulate. Can exhaust ephemeral port space. Solutions: `SO_REUSEADDR`, `tcp_tw_reuse`.

---

**Q7. Explain TCP's fast retransmit mechanism. Why not wait for the RTO timeout?**

When the receiver gets an out-of-order segment (e.g., segments arrive 1, 3, 4 but not 2):
- Receiver sends a duplicate ACK for each out-of-order segment received: "I'm still waiting for byte 2."
- After **3 duplicate ACKs** for the same byte, the sender doesn't wait for the RTO timeout — it immediately retransmits the missing segment.

**Why not wait for RTO?** RTO is estimated based on RTT and is typically hundreds of milliseconds to seconds. Waiting for RTO after a single packet loss introduces unnecessary delay. 3 duplicate ACKs are a strong signal that a specific segment was lost (not just delayed). Fast retransmit recovers from loss in ~1 RTT instead of 1 RTO.

After fast retransmit, TCP performs **fast recovery**: ssthresh = cwnd/2, cwnd = ssthresh (instead of resetting to 1 as in full timeout recovery) — recognizing that 3 dup ACKs is a less severe event than timeout.

---

**Q8. Explain TCP slow start and congestion avoidance. What triggers the switch between them?**

**Slow Start**: Connection begins with cwnd = 1 MSS. For each ACK received, cwnd += 1 MSS. Since each window's worth of segments generates a window's worth of ACKs, cwnd doubles each RTT. Exponential growth.

**Switch trigger**: When cwnd reaches `ssthresh` (slow start threshold), TCP switches to Congestion Avoidance.

**Congestion Avoidance**: For each RTT, cwnd += 1 MSS (linear growth). More conservative — probing for bandwidth slowly.

**ssthresh is set to**: `cwnd/2` at the time of the last congestion event (timeout or 3 dup ACKs). So after each congestion event, the next slow start won't overshoot as much.

**Full cycle:**
```
Start: cwnd=1
Slow start: 1→2→4→8→...→ssthresh  (exponential)
Cong. Avoid: ssthresh→ssthresh+1→...→loss  (linear)
Timeout: ssthresh=cwnd/2, cwnd=1, restart slow start
3 dup ACKs: ssthresh=cwnd/2, cwnd=ssthresh, fast recovery
```

---

**Q9. What is a SYN flood attack? How does SYN cookie defend against it?**

**SYN Flood**: Attacker sends thousands of SYN packets with spoofed source IPs. Server responds with SYN-ACK to the fake IPs (no response comes back). Server allocates a half-open connection state for each SYN. The half-open connection table fills up → server can no longer accept legitimate connections.

**SYN Cookies**: Instead of allocating state on SYN, the server encodes connection information into the **ISN of the SYN-ACK**:
```
ISN = hash(src_IP, src_port, dst_IP, dst_port, timestamp, secret_key)
```
- Server sends SYN-ACK with this ISN, discards all state.
- If a legitimate ACK arrives, its ACK number = server's ISN + 1.
- Server recomputes the hash from the 5-tuple → verifies the connection was real → allocates state and completes the handshake.

**Effect**: Server allocates ZERO state per SYN. SYN flood has no effect on memory. The attacker would need to receive the SYN-ACK (impossible with spoofed IPs) to complete the handshake.

---

## 🔴 Hard

**Q10. Walk through TCP's AIMD and explain why it leads to fairness on a shared link.**

**AIMD (Additive Increase Multiplicative Decrease)**:
- **Additive Increase**: Every RTT without loss → cwnd += 1 MSS. Gradually probe for more bandwidth.
- **Multiplicative Decrease**: On congestion event → cwnd = cwnd × 0.5. React strongly to congestion.

**Fairness proof (intuition with two flows on a shared link)**:

Suppose two TCP flows share a bottleneck link of capacity C.
Plot their cwnd values as (x, y) on a 2D graph:
- **Full utilization line**: x + y = C (both flows together using full capacity)
- **Equal share line**: x = y

When both flows have cwnd > C (overloading), both experience loss and halve their windows. The new point moves toward the equal-share line. Then both increase linearly. After several cycles, they converge to the point where x = y = C/2.

Mathematically: AIMD's decrease is proportional (halving means flow with larger share shrinks more in absolute terms), while increase is equal (both add 1 MSS per RTT). This drives toward equality over time.

**QUIC caveat**: QUIC runs over UDP and implements its own congestion control. Stream-level multiplexing means a single QUIC connection doesn't suffer head-of-line blocking (unlike HTTP/2 over TCP), but the congestion control principles remain the same.

---

**Q11. How does the receive window (rwnd) interact with the congestion window (cwnd) to determine actual send rate?**

TCP send rate = min(rwnd, cwnd) bytes in flight at any time.

**Scenario 1 — Receiver bottleneck** (slow receiver):
- cwnd = 1MB (TCP is trying to send fast based on network conditions)
- rwnd = 65,535 bytes (receiver's buffer is small)
- Sender can only have 65,535 bytes unacknowledged → capped by receiver

**Scenario 2 — Network bottleneck**:
- cwnd = 32,768 bytes (congestion control has throttled sender)
- rwnd = 1MB (receiver has plenty of buffer)
- Sender can only have 32,768 bytes unacknowledged → capped by network congestion

**Throughput formula (approximately)**:
```
Throughput ≈ min(rwnd, cwnd) / RTT

Theoretical TCP max throughput:
  With rwnd = W bytes and RTT = R seconds:
  Throughput = W / R bytes/second

Example: 64KB window, 100ms RTT:
  65,536 / 0.1 = 655,360 bytes/sec ≈ 5.2 Mbps
  (Window Scale Option allows up to 1GB window → much higher)
```

This is why window size matters: a 64KB TCP window over a 100ms trans-Pacific link can only achieve ~5Mbps regardless of the available 10Gbps link bandwidth. **BDP (Bandwidth-Delay Product)** = bandwidth × RTT = the buffer needed to fill the pipe.

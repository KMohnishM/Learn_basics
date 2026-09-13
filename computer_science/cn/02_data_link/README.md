# Module 2: Physical & Data Link Layer

---

## 1. Physical Layer — Bits on the Wire

The Physical layer is concerned with transmitting raw bits — 0s and 1s — over a physical medium. It defines the electrical, optical, or radio characteristics of the transmission.

### Transmission Media

**Twisted Pair Cable (Copper)**:
- Pairs of wires twisted together. Twisting reduces electromagnetic interference (EMI) from adjacent pairs.
- **UTP (Unshielded Twisted Pair)**: Cat5e (up to 1Gbps/100m), Cat6 (10Gbps/55m), Cat6a (10Gbps/100m), Cat7 (10Gbps/100m), Cat8 (40Gbps/30m).
- **STP (Shielded Twisted Pair)**: Additional shielding for high-interference environments.
- Used in: home networks, office LANs, data centers (short distances).

**Fiber Optic**:
- Transmits light pulses through glass or plastic fiber. No electromagnetic interference. Huge bandwidth.
- **Single-mode fiber (SMF)**: Narrow core (9μm), laser light source. Long distances (up to 100km+). Expensive. Used in: undersea cables, long-haul telecom links.
- **Multi-mode fiber (MMF)**: Wider core (50/62.5μm), LED light source. Shorter distances (up to 2km). Cheaper. Used in: data center interconnects.

**Coaxial Cable**: Thick central copper conductor, insulator, braided shield. High bandwidth, good shielding. Used in: cable TV, legacy Ethernet (10BASE5, 10BASE2).

**Wireless (Radio)**:
- **Wi-Fi (802.11)**: 2.4GHz (range: ~70m indoors) and 5GHz (range: ~30m indoors). Higher frequency = shorter range but less interference.
- **Cellular (4G LTE, 5G)**: Base stations connected to backbone networks.
- **Satellite**: High latency (GEO: ~600ms round-trip, LEO like Starlink: ~40ms).

### Signal Transmission

**Analog vs Digital**: Analog signals are continuous (sound waves); digital signals are discrete (0 or 1). Networks transmit digital data.

**Bandwidth vs Throughput**:
- **Bandwidth**: Maximum theoretical data rate of a channel (e.g., 1Gbps).
- **Throughput**: Actual data rate achieved (always ≤ bandwidth due to overhead, errors, congestion).
- **Latency**: Time for one bit to travel from source to destination.

**Nyquist's Theorem**: Maximum data rate of a noiseless channel with bandwidth B Hz and M discrete signal levels:
```
Max data rate = 2B × log₂(M) bits/second
```

**Shannon's Theorem**: Maximum data rate of a channel with bandwidth B Hz and signal-to-noise ratio S/N:
```
C = B × log₂(1 + S/N) bits/second
```
This is the absolute theoretical limit regardless of signal levels used. Cannot exceed Shannon's capacity no matter how clever the encoding.

---

## 2. Data Link Layer Overview

The Data Link layer sits between Physical (raw bits) and Network (IP routing). Its jobs:

1. **Framing**: Package bits into **frames** with clear start and end delimiters.
2. **Physical Addressing**: Use **MAC addresses** to identify source and destination on the same LAN.
3. **Error Detection**: Append a CRC (Cyclic Redundancy Check) to detect corrupted frames.
4. **Access Control (MAC sublayer)**: Coordinate shared access to the medium (who can transmit when).
5. **Flow Control**: Prevent a fast sender from overwhelming a slow receiver on a single link.

Two sublayers:
- **LLC (Logical Link Control, 802.2)**: Interface to the Network layer, flow control, error notification.
- **MAC (Media Access Control)**: Physical addressing, access control for the medium.

---

## 3. MAC Addresses

A **MAC (Media Access Control) address** is a 48-bit (6-byte) hardware address assigned to a network interface card (NIC) by the manufacturer.

**Format**: `AA:BB:CC:DD:EE:FF` (hexadecimal, colon-separated). Example: `00:1A:2B:3C:4D:5E`

**Structure**:
```
AA:BB:CC : DD:EE:FF
└──────┘   └──────┘
 OUI (24-bit)    Device ID (24-bit)
 Organizationally Unique Identifier
 (assigned to manufacturer by IEEE)
```

The first 24 bits (OUI) identify the manufacturer. The last 24 bits are assigned by the manufacturer to uniquely identify each NIC. This gives 2^24 ≈ 16 million unique addresses per manufacturer.

**Special addresses**:
- `FF:FF:FF:FF:FF:FF` = Broadcast address (every device on the LAN receives this frame)
- Bit 0 of byte 0 = 0: unicast; = 1: multicast/broadcast
- Bit 1 of byte 0 = 0: globally unique (burned-in); = 1: locally administered

**Scope**: MAC addresses are only meaningful within a single network segment (LAN). Routers do NOT forward frames based on MAC addresses — they strip the frame and re-wrap with new MAC addresses for each hop.

**MAC spoofing**: Software can change the MAC address that a NIC presents (the "burned-in" address can be overridden in software). This is why MAC-based access control is not truly secure.

---

## 4. Ethernet — The Dominant LAN Technology

**Ethernet (IEEE 802.3)** is the technology used by virtually all wired LANs. It defines:
- Physical layer specifications (cable types, signal encoding, speeds)
- Frame format
- CSMA/CD access control (for older half-duplex Ethernet)

### Ethernet Frame Format

```
┌────────────┬──────────┬──────────┬───────────┬──────────┬─────┐
│  Preamble  │ Dest MAC │ Src MAC  │ EtherType │ Payload  │ FCS │
│  7 bytes   │ 6 bytes  │ 6 bytes  │ 2 bytes   │ 46-1500B │ 4B  │
└────────────┴──────────┴──────────┴───────────┴──────────┴─────┘
```

- **Preamble (7 bytes)**: Alternating 1s and 0s (`10101010...`) for clock synchronization. Helps receiver lock onto the signal timing.
- **SFD (Start Frame Delimiter, 1 byte)**: `10101011` — marks the end of preamble, start of frame.
- **Destination MAC (6 bytes)**: Target device's MAC address (or broadcast).
- **Source MAC (6 bytes)**: Sender's MAC address.
- **EtherType (2 bytes)**: Identifies the protocol in the payload. `0x0800` = IPv4, `0x0806` = ARP, `0x86DD` = IPv6, `0x8100` = VLAN tag (802.1Q).
- **Payload (46–1500 bytes)**: IP packet (or other protocol data). Minimum 46 bytes (padded if smaller — needed for CSMA/CD collision detection). Maximum 1500 bytes = the **MTU (Maximum Transmission Unit)** for Ethernet.
- **FCS (Frame Check Sequence, 4 bytes)**: CRC-32 checksum. Receiver recomputes CRC; if it doesn't match the FCS, the frame is discarded (silent drop — no notification to sender; upper layers handle this).

**Jumbo frames**: Non-standard Ethernet frames with MTU > 1500 bytes (typically 9000 bytes). Used in data centers for performance (fewer frames for same data = less overhead). Both endpoints and all switches in the path must support jumbo frames.

### CSMA/CD (Legacy Half-Duplex Ethernet)

In the era of coaxial cable Ethernet (bus topology) and hubs, all devices shared a single medium. **CSMA/CD** (Carrier Sense Multiple Access with Collision Detection) managed access:

1. **Carrier Sense**: Before transmitting, listen for a carrier signal. If busy, wait.
2. **Multiple Access**: All devices have equal access.
3. **Collision Detection**: While transmitting, continue to listen. If a collision is detected (two devices transmitted simultaneously), both stop immediately.
4. **Jam signal**: Both send a jam signal to ensure all devices know a collision occurred.
5. **Binary exponential backoff**: Wait a random time (0 to 2^k - 1 slot times, where k = collision count), then retry.

**Modern switched Ethernet is full-duplex**: Each port has a dedicated point-to-point link. No collisions possible. CSMA/CD is disabled. Each device has the full bandwidth to itself. Switches replaced hubs, eliminating collision domains.

---

## 5. Switches — How They Work

A **switch** is an L2 device that interconnects devices on a LAN. Unlike a hub (which broadcasts everything everywhere), a switch learns which MAC address is connected to each port and forwards frames only to the correct port.

### MAC Address Table (CAM Table)

The switch maintains a MAC address table (Content Addressable Memory table):
```
MAC Address          Port    VLAN    Age
00:1A:2B:3C:4D:5E   Port 1   1      30s
AA:BB:CC:DD:EE:FF   Port 3   1      120s
```

**Learning**: When a frame arrives on a port, the switch records `{source MAC → port}` in the CAM table (with a timer, typically 300 seconds).

**Forwarding**:
- If destination MAC is in the table → forward ONLY to that port (unicast).
- If destination MAC is NOT in the table (unknown unicast) → **flood** to all ports except the incoming port.
- If destination MAC is `FF:FF:FF:FF:FF:FF` (broadcast) → flood to all ports.

**Filtering**: If source and destination are on the same port (same segment) → don't forward.

### Switching Methods

**Store-and-Forward**: Receive the complete frame, verify FCS checksum, then forward. Drops corrupted frames. Highest latency.

**Cut-Through**: Start forwarding after reading just the destination MAC (14 bytes). Lowest latency. Forwards corrupted frames (FCS not checked). Two sub-modes: Fast-forward (14 bytes) and Fragment-free (64 bytes — avoids forwarding runts).

**Adaptive switching**: Switches between cut-through and store-and-forward based on error rates.

---

## 6. ARP — Address Resolution Protocol

**The problem**: To send an Ethernet frame to a specific device on the LAN, you need its MAC address. You only know its IP address (from a DNS lookup, for example). ARP maps IP → MAC.

**ARP is a Layer 2/3 boundary protocol** — it operates between L2 (uses Ethernet frames) and L3 (resolves IP addresses).

### ARP Operation

**Scenario**: Host A (192.168.1.1) wants to send a packet to Host B (192.168.1.2) on the same LAN.

1. Host A checks its **ARP cache** (temporary table of IP→MAC mappings). Not found.

2. Host A broadcasts an **ARP Request**:
   - Ethernet header: Destination MAC = `FF:FF:FF:FF:FF:FF` (broadcast)
   - ARP payload: "Who has IP 192.168.1.2? Tell 192.168.1.1 (00:AA:BB:CC:DD:EE)"
   - Every device on the LAN receives this frame.

3. Host B (192.168.1.2) recognizes its IP. Host B sends an **ARP Reply** (unicast):
   - Destination MAC = Host A's MAC (from the ARP request)
   - "192.168.1.2 is at 00:11:22:33:44:55"

4. Host A updates its ARP cache: `192.168.1.2 → 00:11:22:33:44:55` (typically cached for ~20 minutes).

5. Host A now knows the MAC address and sends the IP packet wrapped in an Ethernet frame directly to Host B.

**What about different subnets?** If Host A wants to send to 8.8.8.8 (Google's DNS), which is on a different network, Host A first checks: Is 8.8.8.8 on my subnet? No. So ARP for the **default gateway** (router) IP instead. The router's MAC is placed in the Ethernet frame's destination; the router forwards the IP packet.

### ARP Cache and Timeouts

ARP cache entries typically expire after 20 minutes (Linux) or 2 minutes (Windows) to accommodate IP changes. You can view it with `arp -a` on any OS.

### Gratuitous ARP

A device can send an ARP reply without a request — advertising its own IP→MAC mapping to update everyone's ARP cache. Used when:
- A NIC is replaced (new MAC, same IP — update everyone)
- IP failover (a floating IP moves to a different machine)
- On network join (announce presence)

### ARP Spoofing (ARP Poisoning)

An attacker sends fake ARP replies to the LAN, associating the attacker's MAC with a legitimate IP (e.g., the default gateway). Other devices update their ARP cache with the false mapping and send traffic to the attacker instead — a **Man-in-the-Middle (MITM) attack**.

Defense: **Dynamic ARP Inspection (DAI)** on managed switches — validates ARP packets against a DHCP snooping binding table.

---

## 7. VLANs — Virtual LANs

**Problem**: In a large office with 1000 devices, all on one flat LAN, broadcast traffic (ARP, DHCP) is sent to all 1000 devices — massive waste and security issue (accounting can see HR's broadcasts).

**VLAN (Virtual LAN)**: Logically partition a single physical switch into multiple isolated virtual switches. Each VLAN is a separate broadcast domain.

```
Switch ports 1-10  → VLAN 10 (Engineering)
Switch ports 11-20 → VLAN 20 (HR)
Switch ports 21-30 → VLAN 30 (Finance)
```

Traffic in VLAN 10 cannot reach VLAN 20 directly — it must go through a router (or L3 switch) to inter-VLAN route.

**802.1Q VLAN tagging**: When a frame travels between switches (on a **trunk link**), a 4-byte VLAN tag is inserted into the Ethernet header to identify which VLAN the frame belongs to.

```
[ Dest MAC | Src MAC | 802.1Q Tag (4B) | EtherType | Payload | FCS ]
```

The 802.1Q tag contains a 12-bit VLAN ID (supports 4096 VLANs, though 0 and 4095 are reserved).

---

## 8. Error Detection — CRC

The FCS field in an Ethernet frame uses **CRC-32** (Cyclic Redundancy Check with a 32-bit polynomial).

**How CRC works:**
1. Sender treats the frame data as a very large binary number and divides it by a pre-agreed polynomial using binary division (XOR operations).
2. The remainder of this division is the CRC checksum.
3. Sender appends the CRC to the frame.
4. Receiver performs the same calculation on the received data.
5. If the computed CRC matches the received FCS → no error detected.
6. If they don't match → frame is corrupted, silently dropped.

**CRC detects**: Single-bit errors (100%), burst errors up to 32 bits (100% with CRC-32), larger burst errors (very high probability). **CRC does NOT correct errors** — it only detects them. Correction is the responsibility of upper layers (TCP retransmission) or error-correcting codes at the physical layer (like in Wi-Fi).

---

## 9. Wi-Fi (802.11) — Wireless Data Link

Wi-Fi uses the Data Link layer protocol **CSMA/CA** (Collision Avoidance, not Detection) because:
- In wireless, a transmitting device can't hear collisions on the channel (its own signal drowns out incoming signals — the **hidden terminal problem**).
- Physical collision detection is impossible in wireless.

**CSMA/CA**:
1. Sense if the channel is idle.
2. If idle, wait a random backoff time (prevents all devices from transmitting simultaneously after a silence).
3. Transmit.
4. Wait for ACK from the receiver. If no ACK → assume collision, retry with exponential backoff.

Wi-Fi adds **RTS/CTS (Request to Send / Clear to Send)** for large frames: sender sends a short RTS, receiver replies with CTS. All other devices that hear either message know to stay silent for the duration. Solves hidden terminal problem at the cost of overhead.

**Wi-Fi Standards (802.11):**

| Standard | Band | Max Speed | Year |
|----------|------|-----------|------|
| 802.11b | 2.4GHz | 11 Mbps | 1999 |
| 802.11g | 2.4GHz | 54 Mbps | 2003 |
| 802.11n (Wi-Fi 4) | 2.4/5GHz | 600 Mbps | 2009 |
| 802.11ac (Wi-Fi 5) | 5GHz | 3.5 Gbps | 2014 |
| 802.11ax (Wi-Fi 6) | 2.4/5/6GHz | 9.6 Gbps | 2019 |

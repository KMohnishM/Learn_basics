# Q&A — Physical & Data Link Layer

---

## 🟢 Easy

**Q1. What is a MAC address? How is it structured?**

A MAC (Media Access Control) address is a 48-bit hardware identifier assigned to a NIC by the manufacturer. Written as 6 colon-separated hex bytes: `00:1A:2B:3C:4D:5E`.

Structure:
- **First 24 bits (3 bytes)**: OUI (Organizationally Unique Identifier) — identifies the manufacturer (assigned by IEEE).
- **Last 24 bits (3 bytes)**: Device-specific identifier — assigned by the manufacturer.

Special: `FF:FF:FF:FF:FF:FF` = broadcast address. Bit 0 of byte 0 = 1 → multicast/broadcast.

---

**Q2. What is ARP and why is it needed?**

ARP (Address Resolution Protocol) maps IP addresses to MAC addresses within a local network. 

It's needed because Ethernet frames use MAC addresses to deliver data on a LAN, but the Network layer (IP) only knows destination IP addresses. Before sending a frame, the host needs to know the MAC address of the destination (or the default gateway for remote destinations). ARP broadcasts "Who has this IP?" and the owner replies with its MAC.

---

**Q3. What is the MTU of Ethernet and why does it matter?**

Ethernet's MTU (Maximum Transmission Unit) is **1500 bytes** — the maximum payload size in an Ethernet frame.

Why it matters: IP packets larger than the MTU must be **fragmented** into smaller pieces that fit. Each fragment is sent as a separate IP packet, with reassembly at the destination. Fragmentation adds overhead and is best avoided. Modern protocols use **Path MTU Discovery** to find the smallest MTU along the path and send packets that fit without fragmentation.

---

**Q4. What is CSMA/CD? Why is it not used in modern networks?**

CSMA/CD (Carrier Sense Multiple Access with Collision Detection): Before transmitting, listen for activity (CS). All devices share access (MA). If a collision occurs (two transmit simultaneously), both stop, send a jam signal, wait a random backoff time, and retry (CD).

**Not used in modern networks** because modern switched Ethernet is **full-duplex**: each port has a dedicated link between device and switch. No shared medium → no collisions possible → CSMA/CD is disabled. Switches replaced hubs, which eliminated collision domains entirely.

---

**Q5. What is the difference between a hub and a switch?**

**Hub (L1)**: Receives a signal on one port, amplifies it, and broadcasts it to ALL other ports. All devices share bandwidth. Every device is in the same collision domain. Security issue (every device can sniff all traffic).

**Switch (L2)**: Learns which MAC address is on which port. Forwards frames only to the correct port. Each port has its own collision domain (full-duplex). Dedicated bandwidth per connection. Better security.

---

## 🟡 Medium

**Q6. Walk through a complete ARP exchange. Host A (192.168.1.10, MAC: AA:AA) wants to send to Host B (192.168.1.20, MAC: BB:BB). Both are on the same LAN.**

1. Host A checks ARP cache for 192.168.1.20 → not found.
2. Host A broadcasts an ARP Request on the LAN:
   - Ethernet: SRC=AA:AA, DST=FF:FF:FF:FF:FF:FF
   - ARP: "Who has 192.168.1.20? Tell 192.168.1.10 at AA:AA"
3. All devices receive it. Only Host B (192.168.1.20) responds.
4. Host B sends ARP Reply (unicast):
   - Ethernet: SRC=BB:BB, DST=AA:AA
   - ARP: "192.168.1.20 is at BB:BB"
5. Host A updates ARP cache: 192.168.1.20 → BB:BB.
6. Host A sends the IP packet: Ethernet frame with DST=BB:BB.

**Now Host A wants to send to 8.8.8.8 (different subnet)**:
- 8.8.8.8 is not on 192.168.1.0/24 → must go through default gateway (router).
- Host A ARPs for the **router's IP** (e.g., 192.168.1.1), gets router's MAC.
- Host A sends frame with DST=router's MAC, IP DST=8.8.8.8.
- Router receives it, strips the frame, routes the IP packet.

---

**Q7. What is ARP spoofing? How is it done and how is it defended against?**

**Attack**: An attacker sends unsolicited ARP replies to the LAN: "192.168.1.1 (the router/gateway) is at MY_MAC." All devices update their ARP cache, associating the gateway IP with the attacker's MAC. Now all traffic destined for the gateway is sent to the attacker — a Man-in-the-Middle attack. The attacker can read, modify, or drop packets before forwarding them.

**Why it works**: ARP has no authentication. Any device can claim any IP.

**Defenses**:
1. **Dynamic ARP Inspection (DAI)**: Managed switches validate ARP packets against the DHCP snooping binding table (which knows which IP was given to which MAC on which port). Forged ARPs are dropped.
2. **Static ARP entries**: Manually configured IP→MAC mappings that never change. Impractical at scale.
3. **Encryption (TLS/VPN)**: Even if traffic is intercepted, it's encrypted and useless to the attacker.
4. **802.1X port authentication**: Only authenticated devices can send traffic on the network.

---

**Q8. How does a switch build and use its MAC address table?**

**Building (Learning)**:
When a frame arrives on port X, the switch records: `{source MAC → port X, timestamp}` in the CAM table. This way, the switch learns where each source MAC is located.

**Using (Forwarding)**:
- Look up destination MAC in the table.
  - Found: Forward frame only to that port (unicast delivery).
  - Not found (unknown unicast): Flood frame to all ports except the incoming port.
  - `FF:FF:FF:FF:FF:FF` (broadcast): Flood to all ports.

**Aging**: Entries expire (typically 300 seconds). If a device moves ports or is replaced, the old entry expires and new learning happens.

**CAM table overflow attack (MAC flooding)**: Attacker floods the switch with frames using thousands of fake source MAC addresses, filling the CAM table. The switch can no longer learn real mappings → falls back to flooding ALL frames to ALL ports (acting like a hub). Attacker can now sniff all traffic. Defense: Port security (limit MAC addresses per port).

---

**Q9. Calculate the maximum data rate using Shannon's theorem for a channel with bandwidth 4MHz and SNR of 30 dB.**

First, convert SNR from dB to linear:
```
SNR_dB = 30 dB
SNR_linear = 10^(30/10) = 10^3 = 1000
```

Apply Shannon's theorem:
```
C = B × log₂(1 + S/N)
C = 4,000,000 × log₂(1 + 1000)
C = 4,000,000 × log₂(1001)
C = 4,000,000 × 9.97
C ≈ 39.88 Mbps
```

This is the theoretical maximum. No encoding scheme can exceed ~40 Mbps on this channel regardless of how many signal levels are used.

---

## 🔴 Hard

**Q10. What is the hidden terminal problem in wireless networks? How does RTS/CTS solve it?**

**Hidden Terminal Problem**: 
- Node A can reach Node B. Node C can reach Node B. But A and C are out of range of each other (hidden from each other).
- A and C both sense the channel as idle (they can't hear each other), both transmit to B simultaneously → collision at B.
- CSMA/CA fails because A cannot detect that C is transmitting.

```
A ←───── out of range ─────→ C
A ──────→ [B can hear both] ←──── C
```

**RTS/CTS Solution**:
1. A wants to send a large frame to B. A sends a short **RTS (Request to Send)** to B.
2. B responds with **CTS (Clear to Send)** broadcast. The CTS includes the duration of the upcoming transmission.
3. C hears the CTS from B (even though C can't hear A's RTS). C knows to stay silent for the specified duration.
4. A transmits. No collision.

**Overhead**: Every large frame transmission requires 2 extra small frames (RTS + CTS). For small frames, the overhead is larger than the benefit. Wi-Fi devices use RTS/CTS only for frames above an RTS threshold (default often 2347 bytes — so only very large frames use it).

---

**Q11. Explain VLANs in depth. How does 802.1Q tagging work? How does inter-VLAN routing happen?**

**VLANs** logically partition a switch into multiple isolated broadcast domains without needing separate physical switches.

**802.1Q tagging**: When a frame travels between two switches on a trunk link (a link that carries traffic from multiple VLANs), a 4-byte tag is inserted after the source MAC address in the Ethernet frame:

```
[Dest MAC][Src MAC][802.1Q Tag (4B)][EtherType][Payload][FCS]

802.1Q tag structure:
  - TPID (Tag Protocol Identifier): 0x8100 (identifies as VLAN-tagged)
  - PCP (Priority Code Point): 3 bits (802.1p QoS priority 0-7)
  - DEI (Drop Eligible Indicator): 1 bit
  - VLAN ID: 12 bits (0-4095, but 0 and 4095 reserved → 4094 usable VLANs)
```

Access ports (connecting to end devices): frames are untagged when sent to the device, tagged internally by the switch.
Trunk ports (connecting switches): frames are tagged with their VLAN ID.

**Inter-VLAN routing**: Devices in different VLANs cannot communicate directly (different broadcast domains). To route between VLANs:
1. **Router-on-a-stick**: One physical link between switch and router, configured as trunk. Router has virtual sub-interfaces — one per VLAN. Traffic from VLAN 10 to VLAN 20 goes: device → switch → router (VLAN 10 sub-interface) → routing decision → router (VLAN 20 sub-interface) → switch → destination device.
2. **Layer 3 Switch**: A switch with built-in routing capability. Creates SVIs (Switched Virtual Interfaces) — one per VLAN — and routes between them in hardware at wire speed.

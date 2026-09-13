# Cheat Sheet — Physical & Data Link Layer

## Transmission Media
| Medium | Speed | Distance | Use |
|--------|-------|----------|-----|
| Cat5e UTP | 1 Gbps | 100m | Home/office LAN |
| Cat6a UTP | 10 Gbps | 100m | Data center |
| Single-mode fiber | 100 Gbps+ | 100 km+ | Long-haul, WAN |
| Multi-mode fiber | 10–100 Gbps | 2 km | Data center interconnects |
| Wi-Fi 6 (ax) | 9.6 Gbps (theoretical) | ~30m indoors | Wireless LAN |

## Shannon & Nyquist
```
Nyquist (noiseless): Max rate = 2B × log₂(M)  bits/sec
Shannon (noisy):     Capacity = B × log₂(1 + S/N)  bits/sec

B = bandwidth (Hz), M = signal levels, S/N = signal-to-noise ratio

Convert SNR from dB: S/N = 10^(SNR_dB / 10)
Example: 30 dB SNR → S/N = 1000
```

## MAC Address Structure
```
AA:BB:CC : DD:EE:FF
└──OUI──┘  └─Device─┘
(Manufacturer, 24-bit)  (Unique ID, 24-bit)

FF:FF:FF:FF:FF:FF = Broadcast (received by all on LAN)
Bit 0 of byte 0 = 0 → Unicast | = 1 → Multicast/Broadcast
Bit 1 of byte 0 = 0 → Globally unique | = 1 → Locally administered
```

## Ethernet Frame Format
```
[Preamble 7B][SFD 1B][Dst MAC 6B][Src MAC 6B][EtherType 2B][Payload 46-1500B][FCS 4B]

Preamble:  10101010... clock sync
EtherType: 0x0800=IPv4, 0x0806=ARP, 0x86DD=IPv6, 0x8100=802.1Q VLAN
MTU:       1500 bytes (jumbo frames = 9000 bytes in data centers)
FCS:       CRC-32 — detects errors, does NOT correct
```

## 802.1Q VLAN Tag (inserted after Src MAC)
```
[TPID: 0x8100 | PCP: 3b | DEI: 1b | VLAN ID: 12b]
                                      └─ 0–4095, 4094 usable VLANs
```

## ARP Operation
```
Need: IP → MAC mapping on same LAN

Step 1: Broadcast ARP Request (dst=FF:FF:FF:FF:FF:FF)
        "Who has 192.168.1.20? Tell me (AA:AA)"

Step 2: Target unicasts ARP Reply
        "192.168.1.20 is at BB:BB"

Step 3: Requester caches result (~20 min Linux, ~2 min Windows)

For different subnet: ARP for default GATEWAY IP, not destination
```

## Switch MAC Address Table (CAM Table)
```
Learning:    Record {src MAC → ingress port} on every frame received
Forwarding:  Known unicast → forward to that port only
             Unknown unicast → flood all ports (except ingress)
             Broadcast → flood all ports (except ingress)
Aging:       Remove entries after ~300 seconds
```

## Hub vs Switch vs Router
| | Hub | Switch | Router |
|-|-----|--------|--------|
| Layer | L1 | L2 | L3 |
| Addresses | None | MAC | IP |
| Traffic | Broadcasts all | Unicasts (or floods) | Routes between networks |
| Collision domain | 1 (all share) | Per port | Per interface |

## CSMA/CD vs CSMA/CA
| | CSMA/CD | CSMA/CA |
|-|---------|---------|
| Used in | Wired Ethernet (legacy) | Wi-Fi (802.11) |
| Collision handling | Detect & abort | Avoid via random backoff |
| After collision | Exponential backoff | Exponential backoff + ACK |
| Full duplex? | Yes (modern switched) | No (shared wireless medium) |

## ARP Spoofing
```
Attack: Send fake ARP replies → "gateway IP is at MY_MAC"
        → All traffic goes to attacker (MITM)
        → Works because ARP has no authentication

Defense:
  - Dynamic ARP Inspection (DAI) on managed switches
  - 802.1X authentication
  - TLS encryption (data useless even if intercepted)
```

## Wi-Fi Bands
| Band | Range (indoor) | Congestion | Best For |
|------|:-------------:|:----------:|---------|
| 2.4 GHz | ~70m | High (many devices) | Range, legacy devices |
| 5 GHz | ~30m | Lower | Speed, modern devices |
| 6 GHz (Wi-Fi 6E) | ~15m | Lowest | Very high speed, new only |

## Key Numbers
```
Ethernet MTU:          1500 bytes (jumbo: 9000)
MAC address size:      48 bits (6 bytes)
Ethernet frame min:    64 bytes (46B payload minimum, padded if needed)
Ethernet frame max:    1518 bytes (1500 + 18 header/FCS)
Switch CAM aging:      ~300 seconds
ARP cache timeout:     ~20 min (Linux), ~2 min (Windows)
CRC polynomial:        CRC-32 (4-byte FCS)
802.1Q VLAN IDs:       0–4095 (4094 usable)
```

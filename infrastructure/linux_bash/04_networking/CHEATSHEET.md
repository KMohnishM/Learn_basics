# Networking Cheat Sheet

## Network Configuration (`ip`)
| Command | Description |
|---|---|
| `ip a` | Show all IP addresses |
| `ip link show` | Show interface status |
| `ip link set eth0 up` | Bring interface up |
| `ip link set eth0 down` | Bring interface down |
| `ip addr add 192.168.1.10/24 dev eth0` | Assign IP address to interface |
| `ip addr del 192.168.1.10/24 dev eth0` | Remove IP address |
| `ip route show` | Show routing table |
| `ip route add default via 192.168.1.1` | Add default gateway |
| `ip route add 10.0.0.0/8 via 192.168.1.254` | Add static route |
| `ip neigh show` | Show ARP table |

## Socket Statistics (`ss`)
| Command | Description |
|---|---|
| `ss -tulnp` | Show listening TCP/UDP ports + PIDs |
| `ss -ta` | Show all TCP connections (established and listening) |
| `ss -ua` | Show all UDP connections |
| `ss -s` | Show socket summary statistics |
| `ss -t '( dport = :22 )'` | Filter for destination port 22 |

## DNS & Resolution (`dig`, `resolvectl`)
| Command | Description |
|---|---|
| `dig example.com` | Query A record |
| `dig example.com MX` | Query MX (mail) records |
| `dig @8.8.8.8 example.com` | Query specific nameserver |
| `dig example.com +short` | Return only the IP address |
| `dig example.com +trace` | Trace resolution path from root servers |
| `dig -x 8.8.8.8` | Reverse DNS lookup |
| `resolvectl status` | Show systemd-resolved DNS config |

## Connectivity Testing
| Command | Description |
|---|---|
| `ping -c 4 8.8.8.8` | Send 4 ICMP echo requests |
| `traceroute example.com` | Trace path (UDP by default) |
| `traceroute -I example.com` | Trace path using ICMP |
| `traceroute -T -p 443 example.com` | Trace path using TCP port 443 |
| `mtr example.com` | Continuous combined ping/traceroute |
| `curl -I https://example.com` | Fetch HTTP headers only |
| `curl -v https://example.com` | Verbose HTTP/TLS transaction |

## Secure Shell (`ssh`, `rsync`)
| Command | Description |
|---|---|
| `ssh user@host` | Connect to host |
| `ssh -p 2222 user@host` | Connect on specific port |
| `ssh-copy-id user@host` | Copy local public key to remote authorized_keys |
| `ssh -L 8080:localhost:80 user@host` | Local port forward (Access remote port 80 via local 8080) |
| `ssh -R 9000:localhost:3000 user@host`| Remote port forward (Expose local 3000 to remote 9000) |
| `ssh -D 1080 user@host` | Dynamic port forward (SOCKS proxy) |
| `rsync -avz /local/dir user@host:/dir` | Sync directory to remote, preserving metadata |
| `rsync -avz --delete /dir user@host:/dir`| Mirror directory (deletes missing files on target) |

## Firewall (`ufw`, `iptables`)
| Command | Description |
|---|---|
| `sudo ufw status verbose` | Check UFW status and rules |
| `sudo ufw allow 22/tcp` | Allow SSH |
| `sudo ufw allow from 10.0.0.0/8` | Allow traffic from subnet |
| `sudo iptables -L -v -n` | List iptables rules with packet counters |
| `sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT`| Allow incoming HTTP |
| `sudo iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT`| Insert allow SSH at top of chain |
| `sudo iptables -F` | Flush all iptables rules (DANGER) |

## Packet Capture & Diagnostics
| Command | Description |
|---|---|
| `sudo tcpdump -i eth0 -n` | Capture on eth0, no DNS resolution |
| `sudo tcpdump -i eth0 port 80` | Capture traffic on port 80 |
| `sudo tcpdump -i eth0 host 10.1.1.1` | Capture traffic to/from IP |
| `sudo tcpdump -w file.pcap` | Write capture to file |
| `nc -zv 10.1.1.1 22` | Check if TCP port 22 is open |
| `nc -l -p 8080` | Start simple listening server |
| `nmap 10.1.1.1` | Scan top 1000 ports |
| `nmap -p- 10.1.1.1` | Scan all 65535 ports |
| `nmap -sV 10.1.1.1` | Detect service versions |

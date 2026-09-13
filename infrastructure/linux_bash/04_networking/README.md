# Module 4: Linux Networking and Communications

## 1. Network Interfaces and Configuration

Understanding how Linux handles network interfaces is fundamental for any systems engineer or DevOps architect. The networking stack in Linux is robust and highly configurable, supporting everything from simple desktop networking to complex routing and switching tasks. In a production environment, configuring and troubleshooting network interfaces correctly ensures high availability and performance.

### The `ip` Command Deep Dive
The `ip` command from the `iproute2` package has largely replaced the legacy `ifconfig` and `route` commands. It provides comprehensive control over network interfaces, routing, tunnels, and even traffic control.

#### Viewing Interfaces and Addresses
To view all network interfaces and their assigned IP addresses, run:
```bash
ip address show
```
Or simply:
```bash
ip a
```
The output typically includes the loopback interface (`lo`) and one or more physical or virtual interfaces (e.g., `eth0`, `enp3s0`, `wlan0`). Key details in the output include:
- `mtu`: Maximum Transmission Unit. The default is usually 1500 bytes. Changing this is required for jumbo frames (9000 bytes) in high-throughput environments.
- `state`: The operational state, such as UP, DOWN, or UNKNOWN.
- `link/ether`: The MAC address (hardware address) of the interface.
- `inet`: IPv4 address and CIDR prefix (e.g., /24 for a 255.255.255.0 netmask).
- `inet6`: IPv6 address and scope (link-local or global).
- `brd`: The broadcast address for the subnet.

#### Managing Interface State
To bring an interface up or down:
```bash
ip link set eth0 up
ip link set eth0 down
```
This modifies the administrative state of the link. If a cable is unplugged, the operational state may still be DOWN even if the administrative state is UP. 

To change the MTU of an interface:
```bash
ip link set dev eth0 mtu 9000
```

#### Assigning and Removing IP Addresses
You can temporarily assign an IP address to an interface using the following command:
```bash
ip address add 192.168.1.50/24 dev eth0
```
This is useful for troubleshooting or temporary configurations. To remove the address:
```bash
ip address del 192.168.1.50/24 dev eth0
```
Note that changes made via the `ip` command are volatile. They will not survive a reboot. Persistent configuration requires modifying NetworkManager, systemd-networkd, or `/etc/network/interfaces` depending on your distribution.

#### Viewing and Managing Routes
The routing table determines where network traffic is sent. To view the current IPv4 routing table:
```bash
ip route show
```
The output shows the default gateway and routes for connected subnets. Example output:
```text
default via 192.168.1.1 dev eth0 proto dhcp metric 100
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10 metric 100
```
- `default via 192.168.1.1`: This is the default gateway. Any traffic not destined for a known subnet goes here.
- `proto kernel`: Indicates the route was created by the kernel during interface initialization.
- `metric`: Route priority. Lower metric wins when multiple default routes exist.

To add a static route for a specific subnet:
```bash
ip route add 10.0.0.0/8 via 192.168.1.254 dev eth0
```
To delete a specific route:
```bash
ip route del 10.0.0.0/8
```
To view the route a specific IP will take:
```bash
ip route get 8.8.8.8
```

### The Legacy `ifconfig` Command
While deprecated, `ifconfig` (from `net-tools`) is still encountered on older systems (like RHEL 6 or older Debian versions).
To view interfaces:
```bash
ifconfig -a
```
To assign an IP and bring the interface up in one line:
```bash
ifconfig eth0 192.168.1.50 netmask 255.255.255.0 up
```
If you encounter a system without `iproute2` installed, `ifconfig` and `route -n` are your fallback tools.

### Investigating Sockets with `ss` and `netstat`
Understanding which ports are open and listening is critical for security and application troubleshooting. A server listening on unintended ports is a security risk.

#### The `ss` Command
The `ss` (socket statistics) command is the modern replacement for `netstat`. It is faster, dumps socket information directly from kernel space, and handles high socket counts much better.

To list all listening TCP and UDP ports, showing numeric addresses and process information:
```bash
ss -tulnp
```
Flags explained:
- `-t`: Show TCP sockets.
- `-u`: Show UDP sockets.
- `-l`: Show listening sockets.
- `-n`: Do not resolve service names (show numeric ports like 22 instead of 'ssh'). This speeds up the command significantly.
- `-p`: Show the process using the socket. This requires root or sudo privileges.

To view all established TCP connections:
```bash
ss -ta
```
To filter by destination port (e.g., viewing all inbound SSH connections):
```bash
ss -t '( dport = :22 )'
```
To view socket memory usage:
```bash
ss -m
```

#### The `netstat` Command
If `ss` is unavailable, `netstat` can be used:
```bash
netstat -tulnp
```
The output includes the protocol, receive/send queues, local address, foreign address, state, and PID/Program name. Large send/receive queues can indicate a performance bottleneck or an application that is hanging and not reading from its socket buffer.

## 2. DNS and Name Resolution

The Domain Name System (DNS) translates human-readable domain names into IP addresses. Mastery of DNS tools is essential for diagnosing resolution failures, which are among the most common network issues.

### System DNS Configuration
DNS resolvers are typically configured in `/etc/resolv.conf`. A standard file might look like this:
```text
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
options timeout:2 attempts:3
```
- `nameserver`: Defines the IP address of a DNS server.
- `search`: Defines a search domain for unqualified hostnames. If you ping `server1`, the system will append `.example.com` and query `server1.example.com`.
- `options`: Tweaks resolver behavior, such as timeouts.

On modern systems (e.g., Ubuntu, systemd-based distributions), `systemd-resolved` manages this file, often pointing to a local stub resolver at `127.0.0.53`. To query systemd-resolved directly and see the actual upstream DNS servers:
```bash
resolvectl status
```
Or on older systemd versions:
```bash
systemd-resolve --status
```

### The `/etc/hosts` File
Before querying DNS, the system checks the local `/etc/hosts` file. This is useful for overriding DNS or configuring local aliases.
```text
127.0.0.1   localhost
192.168.1.50 dev-server
```
If you ping `dev-server`, it resolves instantly to `192.168.1.50` without any network traffic.

### The `dig` Command
`dig` (Domain Information Groper) is the most versatile DNS query tool. It provides granular details about DNS records and the resolution process.

To perform a standard A record query:
```bash
dig google.com
```
The output contains several sections:
- `HEADER`: Shows the status. `NOERROR` means success. `NXDOMAIN` means the domain does not exist. `SERVFAIL` indicates an upstream server error.
- `QUESTION SECTION`: The query made (usually IN A).
- `ANSWER SECTION`: The resolved IP address, record type, and TTL (Time To Live in seconds).

To query a specific record type (e.g., MX for mail servers, TXT for SPF/DKIM records):
```bash
dig google.com MX
dig google.com TXT
dig google.com AAAA
```
To query a specific nameserver, bypassing `/etc/resolv.conf` entirely (useful for verifying if a specific DNS server has updated its cache):
```bash
dig @8.8.8.8 google.com
```
To view the exact path of resolution from the root servers down (trace):
```bash
dig google.com +trace
```
To get a concise, IP-only output (ideal for scripting):
```bash
dig google.com +short
```
Reverse DNS lookup (finding the PTR record / hostname for an IP):
```bash
dig -x 8.8.8.8
```

### The `nslookup` and `host` Commands
`nslookup` is a simpler tool for DNS queries, often used interactively in both Linux and Windows.
```bash
nslookup google.com
nslookup -type=mx google.com 8.8.8.8
```
`host` provides clean, straightforward output:
```bash
host google.com
host -t TXT google.com
```

### Troubleshooting Resolution Issues
If pinging a domain fails but pinging its IP works, DNS is the root cause.
Check the Name Service Switch configuration in `/etc/nsswitch.conf` to ensure `dns` is listed under the `hosts` entry:
```text
hosts: files dns
```
This tells the system to check `/etc/hosts` first, then query DNS. If `dns` is missing, domain resolution will fail globally for the system.

## 3. Connectivity Testing

Validating network connectivity between nodes involves sending specific packets and observing responses. This goes beyond simple pings; it involves testing specific paths and application ports.

### The `ping` Command
`ping` sends ICMP Echo Request packets and waits for ICMP Echo Reply packets.
```bash
ping 8.8.8.8
```
To send exactly 4 packets and then exit:
```bash
ping -c 4 8.8.8.8
```
To adjust the packet size (useful for testing MTU fragmentation issues):
```bash
ping -s 1472 8.8.8.8
```
If `ping -s 1472` works but `ping -s 1473` fails, your path MTU is 1500 (1472 bytes payload + 8 bytes ICMP header + 20 bytes IP header).

To flood ping (requires root) to test network under extreme load or measure raw packet loss:
```bash
sudo ping -f -c 10000 8.8.8.8
```

### The `traceroute` Command
`traceroute` tracks the path packets take to a destination by incrementally increasing the Time To Live (TTL) value in the IP headers.
```bash
traceroute google.com
```
By default, Linux `traceroute` uses UDP packets to high-numbered ports. Many modern firewalls silently drop these. To use ICMP instead (which mimics Windows `tracert` behavior):
```bash
traceroute -I google.com
```
To use TCP SYN packets on port 80 or 443 (crucial for testing paths through strict firewalls that only allow web traffic):
```bash
sudo traceroute -T -p 443 google.com
```

### The `mtr` Command (My Traceroute)
`mtr` combines `ping` and `traceroute` into a real-time diagnostic tool. It runs continuously, updating packet loss and latency for every hop.
```bash
mtr google.com
```
To run it in report mode (sends 10 packets and outputs a static summary, great for sharing in tickets):
```bash
mtr -c 10 --report google.com
```

### Connectivity Testing with `curl` and `wget`
`curl` and `wget` are HTTP/FTP clients but are incredibly useful for connectivity testing at the application layer, especially when dealing with APIs, load balancers, or proxies.

To test if a web server is responding and view HTTP headers only:
```bash
curl -I https://google.com
```
To see the full request/response process, including TLS handshakes, certificate details, and exact headers sent and received:
```bash
curl -v https://google.com
```
To bypass DNS and force resolution to a specific IP (useful for testing a specific backend node behind a load balancer):
```bash
curl --resolve google.com:443:192.168.1.100 https://google.com
```
To test connectivity and output only the HTTP status code (ideal for health check scripts):
```bash
curl -o /dev/null -s -w "%{http_code}\n" https://google.com
```
To test connectivity without writing to a file using `wget`:
```bash
wget -qO- https://google.com > /dev/null
```

## 4. SSH — Secure Shell Deep Dive

SSH is the standard protocol for secure remote administration. It operates on port 22 by default and encrypts all communication, replacing insecure protocols like Telnet.

### SSH Client Connection
The basic syntax to connect to a remote host:
```bash
ssh username@hostname
```
To connect on a non-standard port (e.g., port 2222, often used to avoid mass automated scans):
```bash
ssh -p 2222 username@hostname
```
To execute a single command remotely, retrieve the output locally, and exit immediately:
```bash
ssh username@hostname "df -h && free -m"
```
To force pseudo-terminal allocation (needed for interactive commands like `top` or `nano` over SSH):
```bash
ssh -t username@hostname "top"
```

### SSH Key-Based Authentication
Key-based authentication is far more secure and convenient than passwords. It relies on asymmetric cryptography.
1. Generate an SSH key pair. Ed25519 is the modern standard, offering high security and fast performance:
```bash
ssh-keygen -t ed25519 -C "admin@workstation"
```
2. Copy the public key to the remote host:
```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub username@hostname
```
This utility automatically appends the public key to `~/.ssh/authorized_keys` on the remote server with the correct file permissions (600) and directory permissions (700).

### The `ssh-agent`
`ssh-agent` holds decrypted private keys in memory. If your private key is protected by a passphrase (as it should be), the agent prevents you from having to type the passphrase on every single connection.
To start the agent in the background:
```bash
eval "$(ssh-agent -s)"
```
To add your private key to the agent:
```bash
ssh-add ~/.ssh/id_ed25519
```
To list keys currently loaded in the agent:
```bash
ssh-add -l
```

### The SSH Config File
The `~/.ssh/config` file allows you to define per-host connection parameters. This vastly simplifies connection commands and enables complex routing.
Example configuration:
```text
Host web-prod
    HostName 10.1.2.3
    User deploy
    Port 2222
    IdentityFile ~/.ssh/id_ed25519_prod
    ServerAliveInterval 60

Host db-prod
    HostName 10.1.2.4
    User admin
    ProxyJump web-prod
```
With this config, running `ssh db-prod` will automatically authenticate to `web-prod`, establish a secure tunnel, and then authenticate to `db-prod` through that tunnel. `ServerAliveInterval 60` keeps connections alive through idle timeouts or strict stateful firewalls.

### SSH Port Forwarding (Tunnels)
SSH can tunnel other TCP traffic securely over the encrypted connection. This is invaluable for securely accessing unencrypted services or bypassing restrictive firewalls.

#### Local Port Forwarding
Forwards a local port to a remote destination through the SSH server.
```bash
ssh -L 8080:localhost:80 username@hostname
```
Accessing `http://localhost:8080` locally securely connects you to `localhost:80` on the remote host. Useful for accessing local-only web dashboards like Kibana or internal administrative panels.

#### Remote Port Forwarding
Forwards a port on the remote SSH server back to a local destination.
```bash
ssh -R 9000:localhost:3000 username@hostname
```
Anyone accessing port 9000 on the remote server is tunneled to port 3000 on your local machine. Useful for exposing a local development server to external clients temporarily.

#### Dynamic Port Forwarding (SOCKS Proxy)
Creates a local SOCKS proxy that routes traffic dynamically to any destination through the remote server.
```bash
ssh -D 1080 username@hostname
```
Configure your web browser to use `localhost:1080` as a SOCKS5 proxy. Your web traffic will exit from the remote SSH server, masking your true IP address.

### Secure File Transfer: `scp`, `rsync`, and `sftp`
To transfer files securely over the SSH protocol:

`scp` (Secure Copy) is simple but aging. It is gradually being deprecated in favor of sftp.
```bash
scp file.txt username@hostname:/tmp/
scp -r /local/dir username@hostname:/remote/dir
```

`sftp` provides an interactive FTP-like session over SSH.
```bash
sftp username@hostname
sftp> put local_file.txt
sftp> get remote_file.txt
```

`rsync` is the modern, delta-transfer optimized standard, and is heavily preferred for directory synchronization, backups, and large transfers:
```bash
rsync -avz /local/dir/ username@hostname:/remote/dir/
```
- `-a`: Archive mode (preserves permissions, ownership, timestamps, symlinks).
- `-v`: Verbose output.
- `-z`: Compress file data during the transfer to save bandwidth.
- `-P`: Show progress bar and allow resuming partial transfers.
- `-e`: Specify a custom shell command (e.g., `rsync -avz -e "ssh -p 2222" ...`).

To delete files on the destination that no longer exist on the source (mirroring):
```bash
rsync -avz --delete /local/dir/ username@hostname:/remote/dir/
```

## 5. Firewall with iptables and ufw

Managing host-level firewalls is critical for securing Linux environments against unauthorized access and network-based attacks.

### Uncomplicated Firewall (UFW)
UFW is a frontend for iptables/nftables designed to be easy to use. It is the default on Ubuntu and Debian systems.

To check UFW status and active rules:
```bash
sudo ufw status verbose
```
To set default policies (best practice is to deny all incoming, allow all outgoing):
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
```
**CRITICAL**: Always allow SSH before enabling the firewall to prevent locking yourself out!
```bash
sudo ufw allow ssh
```
To allow a specific port and protocol:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```
To allow traffic from a specific IP subnet to a specific port:
```bash
sudo ufw allow from 192.168.1.0/24 to any port 3306
```
To delete an existing rule:
```bash
sudo ufw delete allow 80/tcp
```
To enable UFW and apply the rules:
```bash
sudo ufw enable
```

### The `iptables` Command
`iptables` is the traditional and granular tool for configuring the Linux kernel firewall (Netfilter). It operates using tables, chains, and rules.

#### Basic iptables Concepts
- **Tables**: `filter` (default, used for access control), `nat` (Network Address Translation), `mangle` (packet modification).
- **Chains**: `INPUT` (destined for the host), `FORWARD` (routed through the host), `OUTPUT` (originating from the host).
- **Targets**: `ACCEPT`, `DROP` (silently discard), `REJECT` (discard and send an ICMP error).

#### Viewing Rules
To list rules in the `filter` table with line numbers and packet counters:
```bash
sudo iptables -L -v -n --line-numbers
```
- `-n`: Numeric output (do not resolve IPs or ports to names).
- `-v`: Verbose (shows packet/byte counters, interface names).

#### Creating Rules
To allow incoming SSH traffic:
```bash
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```
To allow established and related connections (essential for stateful inspection and ensuring return traffic is permitted):
```bash
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```
To allow all loopback traffic (required by many local services):
```bash
sudo iptables -A INPUT -i lo -j ACCEPT
```
To drop incoming traffic from a specific malicious IP:
```bash
sudo iptables -A INPUT -s 203.0.113.50 -j DROP
```
To set the default policy to DROP:
```bash
sudo iptables -P INPUT DROP
```

#### Managing Rules
To insert a rule at the top of the chain (line 1) so it is evaluated first:
```bash
sudo iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
```
To delete a rule by its line number:
```bash
sudo iptables -D INPUT 1
```
To flush (delete) all rules in a chain:
```bash
sudo iptables -F INPUT
```
To save rules so they persist across reboots (commands vary by distribution):
```bash
sudo iptables-save > /etc/iptables/rules.v4 # Debian/Ubuntu
sudo iptables-save > /etc/sysconfig/iptables # RHEL/CentOS
```

### Introduction to `nftables`
`nftables` is the modern replacement for `iptables`, combining IPv4, IPv6, ARP, and bridge filtering into a single, high-performance engine. It uses a consolidated syntax.

To view the current ruleset:
```bash
sudo nft list ruleset
```
To flush all rules:
```bash
sudo nft flush ruleset
```
To allow SSH using nftables in an existing table and chain:
```bash
sudo nft add rule inet filter input tcp dport 22 accept
```
`nftables` is highly programmable and handles massive rule sets much more efficiently than iptables.

## 6. Network Diagnostics

When connectivity fails and standard tools aren't providing enough information, deep packet-level analysis is required.

### The `tcpdump` Command
`tcpdump` captures network packets traversing an interface. It uses Berkeley Packet Filter (BPF) syntax for powerful filtering, allowing you to isolate exactly what you need.

To capture all traffic on a specific interface (eth0):
```bash
sudo tcpdump -i eth0
```
To capture traffic and avoid resolving IPs and ports (highly recommended for performance):
```bash
sudo tcpdump -i eth0 -n
```
To capture traffic originating from or destined to a specific host:
```bash
sudo tcpdump -i eth0 host 10.1.1.50
```
To capture traffic on a specific port:
```bash
sudo tcpdump -i eth0 port 80
```
To capture only TCP SYN packets (useful for spotting incoming connection attempts or scans):
```bash
sudo tcpdump -i eth0 "tcp[tcpflags] & tcp-syn != 0"
```
To increase the snap length to capture the entire packet payload, and write it to a PCAP file for GUI analysis in Wireshark:
```bash
sudo tcpdump -i eth0 -s 0 -w capture.pcap
```
To read and analyze a capture file directly in the terminal:
```bash
tcpdump -r capture.pcap -n
```

### The `netcat` (nc) Command
`nc` is often called the "Swiss Army knife" of networking. It reads and writes data across network connections using TCP or UDP.

To test if a TCP port is open (port scanning mode, avoiding sending actual payload data):
```bash
nc -zv 10.1.1.50 22
```
To start a simple raw listening server on port 8080:
```bash
nc -l -p 8080
```
To connect to that server from another machine:
```bash
nc 10.1.1.50 8080
```
Anything typed on the client will appear on the server, and vice versa. This is excellent for debugging firewalls.

To transfer a file quickly over the network without SSH:
Receiver (starts listening and writes to file):
```bash
nc -l -p 8080 > received_file.tar.gz
```
Sender (connects and streams file):
```bash
nc 10.1.1.50 8080 < local_file.tar.gz
```

### The `nmap` Command
`nmap` is a powerful network discovery and security auditing tool. It is essential for verifying firewall configurations from the outside.

To scan a single host for open ports (scans the top 1000 common ports):
```bash
nmap 10.1.1.50
```
To perform a fast scan (top 100 ports only):
```bash
nmap -F 10.1.1.50
```
To scan a specific port or a range of ports:
```bash
nmap -p 22,80,443 10.1.1.50
nmap -p 1-1024 10.1.1.50
```
To scan an entire subnet to find active hosts (ping sweep):
```bash
nmap -sn 192.168.1.0/24
```
To detect the Operating System and service/application versions running on open ports (requires root):
```bash
sudo nmap -O -sV 10.1.1.50
```
To perform a stealth SYN scan (the default when running as root, faster and less likely to be logged by legacy firewalls):
```bash
sudo nmap -sS 10.1.1.50
```

### Advanced Diagnostics Scenarios

#### Scenario 1: Intermittent Packet Loss
If a server experiences intermittent connectivity drops, `mtr` is your primary tool. Leave it running for 10-15 minutes pointing to the destination. Look for the hop where packet loss begins and persists through subsequent hops. Loss at a single middle hop with 0% loss at the final destination usually indicates ICMP rate limiting at the router, not actual data loss.

#### Scenario 2: Asymmetric Routing Issues
Sometimes packets leave a server via one interface (e.g., eth0) but return via another (e.g., eth1). Stateful firewalls (like iptables) will drop the return packets because they never saw the outgoing SYN on eth1. Use `tcpdump` on both interfaces simultaneously to diagnose this:
```bash
sudo tcpdump -i eth0 icmp
sudo tcpdump -i eth1 icmp
```
If you ping a remote host and see the outgoing Echo Request on `eth0` but the incoming Echo Reply on `eth1`, you have an asymmetric routing loop to fix in your routing table.

#### Scenario 3: Investigating High Network Traffic Spikes
If monitoring alerts trigger for high outbound bandwidth, you need to identify the offending process immediately.
Use `iftop` (requires installation) to view real-time bandwidth usage by connection:
```bash
sudo iftop -i eth0
```
Identify the remote IP and local port consuming the most bandwidth. Then, map that local port back to a process ID using `ss`:
```bash
sudo ss -tulnp | grep <LOCAL_PORT>
```
Once you have the PID, you can investigate or kill the application causing the network saturation.

#### Theory: TCP vs UDP Networking
When configuring and troubleshooting network applications, distinguishing between TCP and UDP is critical. TCP is connection-oriented; it performs a three-way handshake before transmitting data and ensures delivery through acknowledgements. If a packet is lost, TCP retransmits it. This makes it highly reliable but slower, suitable for SSH, HTTP, and FTP. UDP is connectionless; it sends data without verifying receipt. It is faster but unreliable, suitable for DNS queries, video streaming, and real-time gaming where a dropped packet is preferable to a delayed packet.

#### Troubleshooting: Default Gateway Issues
If a server can ping local hosts but cannot reach the Internet, the default gateway is likely missing or incorrect. Verify the routing table with `ip route show`. If the line beginning with `default via` is missing, you must add it manually or ensure the DHCP client successfully received a gateway from the DHCP server. 
To add it manually for immediate remediation:
```bash
ip route add default via 192.168.1.1 dev eth0
```
Ensure you replace `192.168.1.1` and `eth0` with the correct IP address and interface for your specific network topology. Failure to persist this setting in the network configuration files will result in the same outage on the next reboot.

This concludes the networking module. Mastering these tools and concepts provides a strong foundation for managing complex Linux environments.

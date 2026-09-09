# Module 4: Networking Q&A

### 1. Explain what ss -tulnp shows.
The `ss` command is a modern replacement for `netstat` used to dump socket statistics.
When you run `ss -tulnp`, you are providing five specific flags that filter and format the output.
- `-t` restricts the output to only show TCP sockets.
- `-u` restricts the output to only show UDP sockets.
- `-l` filters for sockets that are currently in a listening state, waiting for incoming connections.
- `-n` forces numeric output, meaning it displays the raw IP addresses and port numbers instead of attempting to resolve them to hostnames or service names (like `ssh` or `http`). This is critical for performance.
- `-p` displays the process ID (PID) and the name of the program to which each socket belongs. This flag requires root privileges to see processes owned by other users.
To run it effectively in a production environment:
```bash
sudo ss -tulnp
```
You can also filter the output using grep to find a specific service:
```bash
sudo ss -tulnp | grep ":22"
```

### 2. Difference between curl -I and curl -v?
The `curl` command is widely used for transferring data and testing network connectivity at the application layer.
`curl -I` (or `--head`) sends an HTTP HEAD request instead of the standard GET request. It asks the server to return only the HTTP response headers and no actual document body.
This is incredibly useful for quickly checking the HTTP status code (e.g., 200 OK, 404 Not Found) or inspecting headers like `Server` or `Content-Type`.
```bash
curl -I https://example.com
```
On the other hand, `curl -v` (verbose) sends a standard GET request but outputs a massive amount of debugging information to stderr.
It shows the entire process: DNS resolution, the TCP three-way handshake, the TLS handshake (including certificate verification), the exact HTTP request headers sent by curl, and the exact HTTP response headers received from the server, followed by the response body.
```bash
curl -v https://example.com
```
You can combine flags, but they serve different diagnostic purposes.

### 3. How does SSH key-based authentication work? Handshake?
SSH key-based authentication uses asymmetric cryptography, specifically a public-private key pair, to verify a client's identity without sending a password over the network.
The process begins during the SSH handshake after the encrypted tunnel is established.
1. The client tells the server which public key it wants to authenticate with.
2. The server checks its `~/.ssh/authorized_keys` file for that specific public key.
3. If the key is found, the server generates a random string (a challenge) and encrypts it using the client's public key.
4. The encrypted challenge is sent back to the client.
5. The client uses its private key to decrypt the challenge.
6. The client combines the decrypted challenge with the session ID, hashes it, and sends the hash back to the server.
7. The server verifies the hash. If it matches, authentication succeeds.
To generate a key pair and copy it to a server:
```bash
ssh-keygen -t ed25519 -C "user@workstation"
ssh-copy-id username@remote-server
```

### 4. What is SSH port forwarding? Local, remote, dynamic.
SSH port forwarding, or SSH tunneling, allows you to securely route local or remote network traffic through an encrypted SSH connection.
- **Local Port Forwarding** (`-L`): Forwards a port from the client machine to a destination reachable from the SSH server. Useful for accessing internal services.
```bash
ssh -L 8080:internal-db.local:3306 user@bastion-host
```
- **Remote Port Forwarding** (`-R`): Forwards a port on the remote SSH server back to a destination reachable from the client. Useful for exposing a local development server.
```bash
ssh -R 9000:localhost:3000 user@remote-server
```
- **Dynamic Port Forwarding** (`-D`): Creates a local SOCKS proxy on the client. The SSH client routes all traffic sent to this proxy dynamically through the SSH server to its final destination.
```bash
ssh -D 1080 user@proxy-server
```
This is commonly used to encrypt web browsing traffic on untrusted networks.

### 5. What is ~/.ssh/config file? Bastion host config?
The `~/.ssh/config` file is a user-specific configuration file for the SSH client. It allows you to define shortcuts and specific parameters for different hosts, saving you from typing long, complex commands.
A bastion host (or jump server) is a heavily secured server used as a single point of entry into a private network.
You can configure your SSH client to automatically route connections through a bastion host using the `ProxyJump` directive.
Here is an example configuration:
```text
Host bastion
    HostName 198.51.100.10
    User admin
    IdentityFile ~/.ssh/id_rsa_bastion

Host internal-server
    HostName 10.0.1.50
    User deploy
    ProxyJump bastion
```
With this configuration, connecting to the internal server requires only a simple command:
```bash
ssh internal-server
```

### 6. rsync vs scp? --delete?
Both `rsync` and `scp` are used to transfer files securely over SSH, but they function very differently.
`scp` (Secure Copy) is a simple, older tool that copies files blindly. If you interrupt a transfer, you must start from the beginning.
```bash
scp -r /local/data user@server:/remote/data
```
`rsync` is a modern, advanced tool designed for synchronization. It uses a delta-transfer algorithm to send only the differences between source and destination files.
This makes subsequent transfers incredibly fast. It also supports resuming interrupted transfers and preserving complex metadata.
```bash
rsync -avz /local/data/ user@server:/remote/data/
```
The `--delete` flag tells `rsync` to delete files in the destination directory that no longer exist in the source directory. This is critical for creating exact mirrors or backups.
```bash
rsync -avz --delete /local/data/ user@server:/remote/data/
```

### 7. dig example.com +trace?
The `dig` command is used for querying DNS nameservers.
By default, `dig` asks the system's configured resolver to perform the lookup and return the final answer.
When you append `+trace`, `dig` alters its behavior entirely. It bypasses the local resolver and performs an iterative lookup itself, starting from the DNS root servers.
It mimics the exact process a recursive resolver follows.
1. It queries the root servers (`.`) for the Top-Level Domain (TLD) nameservers (e.g., `.com`).
2. It queries the TLD nameservers for the authoritative nameservers for the domain (e.g., `example.com`).
3. It queries the authoritative nameservers for the final A record.
```bash
dig example.com +trace
```
This is an invaluable diagnostic tool. If a DNS record was recently updated but isn't resolving correctly, `+trace` will show you exactly which server in the chain is returning stale data or failing to respond.

### 8. tcpdump for TCP SYN to specific port?
`tcpdump` is a command-line packet analyzer. To capture specific types of packets, you must use Berkeley Packet Filter (BPF) syntax.
A TCP SYN packet is the first packet sent in the TCP three-way handshake, used to initiate a connection.
Capturing SYN packets is highly useful for identifying connection attempts, port scans, or diagnosing firewall issues.
To capture only TCP SYN packets destined for port 80 on the `eth0` interface:
```bash
sudo tcpdump -i eth0 "tcp[tcpflags] & tcp-syn != 0 and port 80"
```
To explain the filter: `tcp[tcpflags]` looks at the flags byte in the TCP header. The bitwise AND operator `&` isolates the SYN bit. If the result is not zero, the SYN flag is set.
To avoid resolving hostnames and ports (which can slow down the capture and generate unwanted DNS traffic), you should always use the `-n` flag:
```bash
sudo tcpdump -i eth0 -n "tcp[tcpflags] & tcp-syn != 0 and port 80"
```

### 9. ufw vs iptables?
`iptables` is the traditional, low-level command-line tool used to configure the Linux kernel's Netfilter firewall framework.
It is extremely powerful and granular but has a steep learning curve. Rules are organized into complex tables (filter, nat, mangle) and chains (INPUT, OUTPUT, FORWARD).
```bash
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```
`ufw` (Uncomplicated Firewall) is a high-level frontend for `iptables` (or `nftables` on newer systems).
It was designed by Ubuntu to provide an intuitive, user-friendly interface for common firewall tasks, abstracting away the complexity of chains and tables.
```bash
sudo ufw allow ssh
```
Under the hood, `ufw` translates its simple commands into the corresponding `iptables` rules.
While `ufw` is perfect for standard host-based firewalls, complex routing, NAT, or packet mangling scenarios still require direct use of `iptables` or `nftables`.

### 10. iptables OUTPUT policy? ESTABLISHED,RELATED?
In `iptables`, chains have default policies that dictate what happens to a packet if it does not match any specific rule.
The `OUTPUT` chain handles packets generated locally by the host and destined for the network.
Setting the `OUTPUT` policy to `DROP` means the server cannot initiate any outbound network connections by default.
```bash
sudo iptables -P OUTPUT DROP
```
This is a high-security posture, preventing compromised software from phoning home or downloading malware.
`ESTABLISHED,RELATED` refers to the state tracking module in Netfilter (`conntrack`).
To allow a server to respond to incoming requests (like a web server responding to HTTP GETs) without opening up all outbound traffic, you must explicitly allow return traffic for established connections:
```bash
sudo iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```
This stateful inspection ensures that only packets belonging to valid, already-negotiated connections are permitted to leave.

### 11. Verify TCP port open? (curl, nc, nmap, ss)
There are multiple ways to verify if a TCP port is open, depending on your vantage point.
From the local server itself, you check if the process is listening using `ss`:
```bash
sudo ss -tulnp | grep :443
```
From a remote client, you must test connectivity through the network and any intermediate firewalls.
You can use `netcat` (`nc`) in scanning mode (`-z`) to test the port without sending payload data:
```bash
nc -zv 192.168.1.50 443
```
You can use `nmap` for a more comprehensive scan, which will also tell you if the port is open, filtered (blocked by a firewall), or closed:
```bash
nmap -p 443 192.168.1.50
```
If the port hosts an HTTP service, `curl` is the best tool, as it tests both the TCP connection and the application layer response:
```bash
curl -I https://192.168.1.50
```

### 12. ARP table? ip neigh show?
The Address Resolution Protocol (ARP) translates IPv4 network addresses (like `192.168.1.50`) into physical hardware MAC addresses (like `00:1A:2B:3C:4D:5E`).
This translation is necessary because Ethernet switches route frames based on MAC addresses, not IP addresses.
Every host maintains a local ARP cache (the ARP table) to avoid querying the network for every single packet.
To view the current ARP table in modern Linux, use the `ip` command to show neighbor objects:
```bash
ip neigh show
```
The legacy command for this is:
```bash
arp -a
```
If you suspect an IP conflict or an ARP spoofing attack, you can flush the ARP cache to force the system to resolve the MAC addresses again:
```bash
sudo ip neigh flush all
```

### 13. CIDR notation? 192.168.1.0/24? 10.0.0.0/8?
Classless Inter-Domain Routing (CIDR) notation is a compact way to represent an IP address and its associated routing prefix (subnet mask).
The number after the slash indicates how many bits of the IP address are dedicated to the network portion. An IPv4 address is 32 bits long.
- `192.168.1.0/24`: The `/24` means the first 24 bits represent the network, and the remaining 8 bits are for hosts. This is equivalent to a subnet mask of `255.255.255.0`. It provides 256 total IP addresses, with 254 usable for hosts.
- `10.0.0.0/8`: The `/8` means the first 8 bits represent the network, and the remaining 24 bits are for hosts. This is equivalent to a subnet mask of `255.0.0.0`. It provides over 16.7 million usable host addresses.
To calculate these ranges on the command line, you can use the `ipcalc` utility:
```bash
ipcalc 192.168.1.0/24
```
This will output the network address, broadcast address, netmask, and host range.

### 14. mtr vs traceroute?
Both tools are used to trace the network path from a source to a destination, but they operate and display data differently.
`traceroute` performs a single, sequential trace. It sends packets with incrementing TTLs, records the response from each router along the path, prints the result, and exits.
```bash
traceroute google.com
```
`mtr` (My Traceroute) combines the functionality of `traceroute` and `ping`. It repeatedly traces the path and continuously pings every router along the route in real-time.
```bash
mtr google.com
```
This continuous polling makes `mtr` significantly better for diagnosing intermittent network issues. If packet loss is fluctuating or a router is experiencing high latency spikes, `traceroute` might miss it during its single pass, whereas `mtr` will clearly display the degradation over time.

### 15. Securely transfer SSH private key? Permissions?
Transferring an SSH private key requires extreme caution, as anyone possessing it can impersonate you.
The most secure method is to never transfer it at all. Instead, generate a new key pair on the new machine and authorize its public key on your servers.
If you absolutely must transfer a private key, use a secure, encrypted channel like `scp` or `rsync` over SSH:
```bash
scp ~/.ssh/id_ed25519 user@new-workstation:~/.ssh/
```
Once transferred, the file permissions must be strictly enforced. SSH clients will refuse to use a private key file if it is readable by other users on the system.
The private key must have `600` permissions (read and write only by the owner).
```bash
chmod 600 ~/.ssh/id_ed25519
```
The `.ssh` directory itself must have `700` permissions (read, write, and execute only by the owner).
```bash
chmod 700 ~/.ssh
```

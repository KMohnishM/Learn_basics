# Module 1: Version Control & Linux Automation

Welcome to the very beginning of your DevOps journey! Before we can start orchestrating clusters of containers in the cloud, we must deeply understand the bedrock of all modern software engineering: **Version Control**, **Linux OS architecture**, and **Networking**. 

DevOps is about automating the software lifecycle. To automate a system, you must first deeply understand how it works manually. This module is theory-heavy because these foundational concepts will appear in every single module moving forward.

---

## 1. Version Control (Git) - Under the Hood

You likely know basic Git commands (`add`, `commit`, `push`), but in DevOps, you need to understand *why* Git does what it does.

### How Git Stores Data
Git does not store diffs (changes) between files. Instead, Git stores **snapshots**.
- **Blobs (Binary Large Objects)**: When you add a file, Git compresses its contents and stores it in its database (inside the `.git/objects` folder) as a "blob", named by its SHA-1 hash.
- **Trees**: A tree object represents a directory. It contains pointers to blobs (files) and other trees (subdirectories).
- **Commits**: A commit object points to the root tree of your project at that moment in time. It also contains metadata: author, timestamp, commit message, and a pointer to its parent commit(s).

### Branching Strategies
When a team of 50 developers works on a single codebase, how do you prevent chaos? You use a branching strategy.

1. **GitFlow**: A strict, heavy process.
   - `main`: Stores the official release history.
   - `develop`: An integration branch for features.
   - `feature/xxx`: Branches off `develop` for specific features.
   - **Pros**: Very structured, great for software with scheduled, versioned releases (like an iOS app).
   - **Cons**: Slow, leads to massive "merge hell" when features live too long.
2. **Trunk-Based Development**: The DevOps standard.
   - Developers push code directly to a single `main` branch (the "trunk") multiple times a day.
   - Features are hidden behind "Feature Flags" in the code until they are ready.
   - **Pros**: Rapid integration, no massive merge conflicts, continuous delivery.

### Merge vs. Rebase
When pulling changes from a remote branch, you have two ways to integrate them:
- **`git merge`**: Takes two branches and ties them together with a new "merge commit". It preserves the exact history of what happened, but makes the commit graph look like a messy spiderweb.
- **`git rebase`**: Takes your local commits, rewinds them, pulls down the new remote commits, and replays your local commits *on top* of them. It creates a perfectly linear, clean history. 
- *DevOps Golden Rule*: **Never rebase commits that exist outside your local repository.** Rebasing rewrites history. If you rewrite history that others have already downloaded, you will break their repositories.

---

## 2. Linux Architecture & Administration

Over 90% of cloud infrastructure runs on Linux. Understanding it is non-negotiable.

### Kernel vs. User Space
Linux is divided into two distinct areas to protect the system:
1. **The Kernel**: The core of the OS. It manages hardware (CPU, Memory, Disk), networking, and security. User programs cannot touch the hardware directly.
2. **User Space**: Where your applications run (e.g., your Python app, a database, the Bash shell). When an app needs hardware resources (like reading a file), it must make a **System Call (syscall)** to ask the Kernel to do it on its behalf.

### Standard Streams and Piping
Every process in Linux automatically has three communication channels opened:
1. `stdin` (Standard Input, File Descriptor 0): Data going *into* the process.
2. `stdout` (Standard Output, File Descriptor 1): Normal data coming *out* of the process.
3. `stderr` (Standard Error, File Descriptor 2): Error messages coming *out*.

**Piping (`|`)**: One of Linux's most powerful features. It takes the `stdout` of one command and connects it directly into the `stdin` of the next command.
```bash
# Example: List all files, find lines with "error", and count them
cat app.log | grep "error" | wc -l
```

### File Permissions
Linux uses a 3x3 permission grid. 
- **Entities**: User (Owner), Group, Others (Everyone else).
- **Permissions**: Read (r, value 4), Write (w, value 2), Execute (x, value 1).
If a file has permissions `chmod 755 script.sh`:
- Owner gets 7 (4+2+1 = Read/Write/Execute)
- Group gets 5 (4+1 = Read/Execute)
- Others get 5 (4+1 = Read/Execute)

---

## 3. Terminal & Bash Scripting

DevOps engineers automate manual tasks. Bash is the glue of Linux automation.

### Text Manipulation Tools
- **`grep`**: Searches for patterns (regex) within text.
- **`awk`**: A full programming language designed for text processing and data extraction, treating text as rows and columns (separated by spaces by default).
- **`sed`**: Stream editor used for finding and replacing text on the fly.

### Scripting Basics
A bash script always starts with a "shebang" (`#!/bin/bash`), telling the OS which interpreter to use.
```bash
#!/bin/bash
# A basic loop and conditional
for i in {1..5}; do
  if [ $i -eq 3 ]; then
    echo "Found the magic number: $i"
  else
    echo "Processing $i..."
  fi
done
```

---

## 4. Networking Fundamentals

You cannot securely deploy applications or debug connectivity issues without knowing networking.

### The OSI Model
A conceptual framework showing how data travels over a network. You primarily deal with:
- **Layer 3 (Network)**: Routing data packets using IP addresses.
- **Layer 4 (Transport)**: Ensuring data arrives via TCP (reliable, ordered connection) or UDP (fast, unordered connection).
- **Layer 7 (Application)**: Protocols like HTTP, DNS, and SSH that applications use to talk to each other.

### DNS (Domain Name System)
The phonebook of the internet. It translates human-readable names (`www.google.com`) into IP addresses (`142.250.190.46`).
1. **A Record**: Maps a domain directly to an IPv4 address.
2. **CNAME**: Maps an alias domain to another domain (e.g., `www.example.com` -> `example.com`).

### HTTP vs. HTTPS
- **HTTP (Port 80)**: Unencrypted plaintext. Anyone intercepting the traffic can read it.
- **HTTPS (Port 443)**: Encrypted using SSL/TLS. 
  - **TLS Handshake**: The client and server agree on an encryption algorithm. The server presents a cryptographic Certificate (proving its identity). They generate a shared secret key, and all further communication is encrypted with that key.

### Secure Shell (SSH)
How we securely access remote Linux servers. It uses **Public Key Cryptography** (Asymmetric encryption).
- **Public Key**: Like a padlock. You put this on the remote server (in the `~/.ssh/authorized_keys` file). It is safe to share with the world.
- **Private Key**: Like the key to the padlock. You keep this securely on your laptop. **Never share this.**
When you try to log in, the server challenges you to prove you have the private key that matches the public padlock.

---

## What's Next?
Now that we have covered the heavy theory, it is time to put it into practice. Head over to the `labs/` directory to write some automation scripts!

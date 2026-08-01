# Module 6: Distributed Systems

> **Goal**: Understand the fundamental theory, realities, and algorithms that make distributed systems work. 
> Scaling from a single machine to a cluster of machines introduces entirely new classes of problems: partial failures, network partitions, concurrent modifications, and time synchronization issues. This module covers how we reason about and solve these problems in production environments.

---

## Table of Contents

1. [The Realities of Distributed Systems](#1-the-realities-of-distributed-systems)
2. [CAP Theorem](#2-cap-theorem)
3. [PACELC Theorem (CAP Extension)](#3-pacelc-theorem-cap-extension)
4. [Consistency Models](#4-consistency-models)
5. [Vector Clocks & Version Vectors](#5-vector-clocks--version-vectors)
6. [Quorum Mechanics](#6-quorum-mechanics)
7. [Consensus Algorithms](#7-consensus-algorithms)
8. [Distributed Transactions](#8-distributed-transactions)
9. [Time and Order in Distributed Systems](#9-time-and-order-in-distributed-systems)
10. [Failure Detection & Membership](#10-failure-detection--membership)
11. [Distributed Locking](#11-distributed-locking)

---

## 1. The Realities of Distributed Systems

Moving from a single-node system (where operations either succeed or fail completely) to a distributed system introduces a massive leap in complexity. In a single-node system, if a function call fails, it fails synchronously and the program crashes. In a distributed system, function calls happen over a network, introducing ambiguity and uncertainty.

### 1.1 The 8 Fallacies of Distributed Computing

Coined by L. Peter Deutsch and others at Sun Microsystems in the 1990s, these are the false assumptions engineers often make when designing distributed systems:

#### 1. The network is reliable
* **Reality**: Switches fail, cables get cut by backhoes, BGP misconfigurations blackhole traffic, and Wi-Fi connections drop.
* **Failure Scenario**: A payment gateway service times out talking to the processing node because a network link flapped. The application assumed the network call would eventually succeed, leaving the transaction in an unknown state (did the user get charged or not?).
* **Solution Strategy**: Implement retries with exponential backoff and jitter, circuit breakers, and ensure all network operations are idempotent.

#### 2. Latency is zero
* **Reality**: The speed of light is an absolute physical limit. Cross-datacenter calls take milliseconds; cross-continental calls take hundreds of milliseconds.
* **Failure Scenario**: A developer tests a microservice architecture locally on their laptop (loopback latency = ~0.05ms) and sees excellent performance. In production across AWS Availability Zones (latency = 2-5ms) or regions (latency = 50ms), the cascade of 20 sequential service calls adds a full second or more of latency, breaking the SLA.
* **Solution Strategy**: Batch requests, use asynchronous messaging, and move data closer to compute using CDNs or local caches.

#### 3. Bandwidth is infinite
* **Reality**: Network links can saturate, causing packet drops and severe latency spikes. TCP congestion control kicks in and slows everything down.
* **Failure Scenario**: A batch job is deployed to sync data between two microservices every night at midnight. It attempts to transfer a 50GB payload over a shared 1Gbps link, saturating it and causing latency spikes for all user-facing services sharing that link.
* **Solution Strategy**: Compress data (gRPC/Protobuf instead of JSON), implement rate limiting, and design APIs to only send delta updates.

#### 4. The network is secure
* **Reality**: Traffic can be intercepted, spoofed, or manipulated. Internal networks are not immune to attacks (Zero Trust architecture assumes the network is compromised).
* **Failure Scenario**: Internal traffic isn't encrypted because "it's inside the VPC." A compromised low-privilege container listens to the subnet using packet sniffing, stealing unencrypted database credentials and PII.
* **Solution Strategy**: Mutual TLS (mTLS) for all service-to-service communication, encrypt data in transit and at rest.

#### 5. Topology doesn't change
* **Reality**: Nodes are constantly added, removed, or fail. Autoscaling scales up and down continuously based on load. Cloud environments are inherently ephemeral.
* **Failure Scenario**: A service caches the IP address of its database upon startup instead of using a dynamic service discovery mechanism. When the database fails over to a new primary node with a new IP, the service endlessly attempts to connect to the dead node, requiring a manual restart.
* **Solution Strategy**: Use dynamic Service Discovery (Consul, Eureka), health checks, and intelligent client-side or proxy-based load balancing (Envoy, HAProxy).

#### 6. There is one administrator
* **Reality**: Multiple teams manage different parts of the infrastructure, rolling out updates independently. Open-source dependencies are updated by third parties.
* **Failure Scenario**: The database platform team upgrades Postgres globally, which changes the default connection pool behavior. The application team isn't informed, their configurations break, and their service suddenly runs out of connections during peak hours.
* **Solution Strategy**: Strong API contracts, versioning, Infrastructure as Code (IaC), and blameless post-mortems with cross-functional communication.

#### 7. Transport cost is zero
* **Reality**: Serialization and deserialization (JSON, XML) costs CPU cycles. Moving data across availability zones or regions costs real money (AWS data egress fees are notoriously high).
* **Failure Scenario**: A system constantly pulls entire 1MB user records from a central database just to update a single "last_login" boolean field. This results in massive AWS bandwidth bills and high CPU utilization on both the database and the application servers just for JSON parsing.
* **Solution Strategy**: Use efficient binary formats, implement GraphQL or field-masking to fetch only needed data.

#### 8. The network is homogeneous
* **Reality**: A system runs on different OS versions, different hardware architectures (x86 vs ARM), and varying network speeds. Consumer devices range from high-end laptops on fiber to 5-year-old smartphones on 3G.
* **Failure Scenario**: A message queue producer assumes all consumers process messages at the exact same rate. One consumer is running on older, slower hardware. It cannot keep up, causing backpressure on the queue, leading to eventual out-of-memory (OOM) crashes across the entire cluster.
* **Solution Strategy**: Standardize on containerization (Docker) to abstract the OS, but design systems to be resilient to varying processing speeds (decoupled queues, backpressure handling).

### 1.2 Partial Failures: Harder than Total Failures

In a single-machine system, if the power supply dies, the entire system halts. This is a **total failure**. It is easy to reason about: the system is down, you reboot it.

In a distributed system, a request might span 5 different microservices, 3 databases, and a cache. If service 3 fails, or the network to service 3 drops packets, you have a **partial failure**. 

The fundamental problem with network communication is that it is inherently unreliable. When Service A makes a synchronous HTTP call to Service B and it times out, Service A **does not know what happened**. 

```
The Ambiguity of a Network Timeout:

Service A ---------------------------> Service B (Payment API)
             POST /charge

Scenario 1: Request dropped
Service A --x   (Network drops packet)
Result: B never saw it. User not charged.

Scenario 2: Node crashed during processing
Service A ----> Service B (Starts processing)
                Service B CRASHES
Result: B saw it, but didn't finish. User not charged (hopefully rolled back).

Scenario 3: Response dropped
Service A ----> Service B (Processes successfully, charges user)
                Service B returns 200 OK
Service A <---x (Network drops response)
Result: B finished successfully. User WAS charged. Service A thinks it failed!
```

Because Service A cannot distinguish between Scenario 1 and Scenario 3, it cannot blindly retry the operation. If it retries Scenario 3, the user gets double-charged.

This means **all non-read operations in a distributed system must be idempotent**. Idempotency means that performing the operation multiple times yields the same result as performing it once. (e.g., passing a unique `Idempotency-Key` header with the payment request).

### 1.3 The Fundamental Trade-off

Every distributed system architecture is a constant balancing act between three properties:

1. **Correctness (Consistency)**: Do all users see the exact same data? If I write a value, does everyone instantly see it?
2. **Availability**: Can the system accept reads and writes right now, even if some nodes are down?
3. **Performance (Latency)**: How fast does the system respond? (Measured in milliseconds/microseconds).

You can tune the system to favor one or two, but never all three perfectly under all conditions. To get absolute correctness, you must coordinate across nodes, which increases latency and reduces availability if nodes cannot communicate. To get maximum availability and lowest latency, you must allow nodes to act independently, which sacrifices correctness.

---

## 2. CAP Theorem

Proposed by Eric Brewer in 2000 and later formally proven by Seth Gilbert and Nancy Lynch at MIT, the CAP theorem is a foundational principle for understanding distributed data stores.

It states that a distributed data store can guarantee at most two of the following three properties simultaneously:

### 2.1 Precise Definitions

It is critical to use the exact academic definitions for CAP, as casual definitions lead to severe misunderstandings.

* **Consistency (C)**: Specifically, *Linearizability*. Every read receives the most recent write or an error. In other words, all nodes see the exact same data at the exact same time. It behaves as if there is only one copy of the data.
* **Availability (A)**: Every request to a non-failing node receives a (non-error) response, without the guarantee that it contains the most recent write. The system remains operational.
* **Partition Tolerance (P)**: The system continues to operate despite an arbitrary number of messages being dropped, delayed, or lost by the network between nodes.

### 2.2 Why 'P' is Non-Negotiable

A common interview mistake is saying, "I choose CA." 

A network partition is a physical reality. Cables get cut, switches reboot, routers misroute packets, and JVM Garbage Collection pauses can cause a node to become unresponsive, simulating a network drop. 

You **cannot** design a system that prevents network partitions. The network is outside of your control. Therefore, you do not "choose between C, A, and P." 

Instead, the CAP theorem really says:
**In the presence of a network partition (P), you must choose between Consistency (C) or Availability (A).**

### 2.3 CP vs AP Systems with Real Examples

When a partition occurs (e.g., Data Center 1 cannot talk to Data Center 2):

#### CP (Consistent and Partition Tolerant) Systems
The system chooses consistency. If a node cannot communicate with the majority of the cluster to ensure it has the latest data, it will return an error or timeout rather than returning potentially stale data.

* **Behavior**: Halts writes (and often reads) on the minority side of the partition to prevent split-brain scenarios.
* **Real Examples**:
  * **Zookeeper / etcd / Consul**: These are coordination systems that rely on strict consensus. If a network partition leaves a minority of nodes isolated, they stop accepting writes.
  * **HBase**: Built on HDFS, if a region server loses contact with the master, it will shut down to protect data consistency.
  * **MongoDB (in typical replica set mode)**: If a secondary loses contact with the primary, it cannot accept writes. If the primary loses contact with the majority, it steps down, sacrificing availability until a new primary is elected.

#### AP (Available and Partition Tolerant) Systems
The system chooses availability. Nodes continue to accept reads and writes even if they cannot talk to each other, meaning they might return stale data or accept conflicting writes that must be resolved later.

* **Behavior**: Always returns a response, even if it's stale. Accepts writes everywhere, leading to eventual consistency and conflict resolution upon healing.
* **Real Examples**:
  * **Cassandra (in default configurations)**: Designed to be highly available. If a node is partitioned, it will still accept writes and rely on hinted handoffs and read repair later.
  * **Riak / Dynamo**: Designed explicitly for high availability. 
  * **DNS (Domain Name System)**: Highly available, eventually consistent. If a root server is unreachable, cached stale records are happily served.

### 2.4 Limitations of the CAP Theorem

While famous, the CAP theorem is frequently misunderstood and has strict limitations:
1. **It's extreme**: It only talks about 100% availability vs 100% linearizable consistency during an absolute network partition. Real systems operate in gray areas.
2. **It treats systems as monoliths**: Modern databases (like Cassandra or CosmosDB) allow you to tune consistency on a per-query basis. A single database can be CP for one query and AP for another.
3. **It ignores normal operations**: CAP says nothing about what happens when the network is healthy. It provides no guidance for performance trade-offs during the 99.9% of the time the system is functioning normally.

---

## 3. PACELC Theorem (CAP Extension)

Because CAP ignores normal operations, Daniel Abadi proposed the **PACELC** theorem in 2010 to provide a much more complete and practical picture of distributed system trade-offs.

It states:
* **P** (If there is a Partition) -> choose **A** (Availability) or **C** (Consistency)
* **E** (Else, during normal operation) -> choose **L** (Latency) or **C** (Consistency)

When the network is healthy (which is almost always), a system must trade off between latency (how fast it returns a response) and consistency (ensuring all replicas are completely synchronized before returning).

If you want strong consistency during normal operations, you must wait for replicas to acknowledge the write. That wait time equals higher latency. If you want low latency, you must return immediately after writing to the local node, sacrificing immediate consistency.

### 3.1 Classification Table

| Database System | PACELC Classification | Explanation |
|-----------------|-----------------------|-------------|
| **Cassandra**   | PA / EL               | **PA**: During partition, chooses Availability. **EL**: Normally, trades Consistency for lower Latency (by default, writes don't wait for all replicas). |
| **MongoDB**     | CP / EC               | **CP**: During partition, minority drops offline. **EC**: Normally, routes to primary to ensure Consistency, accepting the network Latency cost. |
| **HBase**       | CP / EC               | **CP**: Operates strictly consistently; partition halts affected regions. **EC**: Normal operations prioritize consistency over latency. |
| **VoltDB**      | PC / EC               | **PC**: Strictly consistent in-memory DB. Never sacrifices consistency, regardless of network state. |

### 3.2 IMPORTANT: Modern DynamoDB is Highly Configurable

A very common misconception in system design is labeling Amazon's DynamoDB purely as an AP system. Historically, the original Amazon Dynamo paper (2007) described an AP system. However, **modern AWS DynamoDB is a managed service that is highly configurable**. 

**DynamoDB is NOT inherently an AP system.**

* **Reads**: You can configure DynamoDB for `ConsistentRead=true` (strongly consistent reads) or `ConsistentRead=false` (eventually consistent, lower latency).
* **Transactions**: DynamoDB supports full ACID transactions across multiple items via `TransactWriteItems`.
* **Architecture**: Behind the scenes, modern DynamoDB operates using a single-leader replication model for a given partition (using Paxos-like protocols). This makes it more akin to a CP/EC system depending on how you configure your API calls. It prioritizes data safety and consistency over raw availability in many failure modes.

---

## 4. Consistency Models (Spectrum from Strong to Weak)

Consistency is not a binary true/false attribute. It is a wide spectrum. Stronger consistency is easier for application developers to reason about (it acts like a single variable in memory) but comes at the cost of higher latency and lower availability. Weaker consistency is faster and more robust but pushes complexity into the application layer.

### 4.1 The Consistency Spectrum

```
Strongest -------------------------------------------------------------> Weakest
  Linearizability -> Sequential -> Causal -> Read-Your-Writes -> Eventual
```

### 4.2 Linearizability (Strong Consistency)
* **Definition**: The gold standard. Operations appear to take effect instantaneously at exactly one point in time between their invocation and completion. There is a strict, global total order of operations across the entire system that aligns with physical real-world time.
* **Example**: If Client A successfully writes `AccountBalance=100`, any subsequent read by any client (even on a different continent 1 millisecond later) MUST return `100`. 
* **Cost**: Extremely high latency. Requires synchronous consensus algorithms (like Raft/Paxos) or specialized hardware like atomic clocks (Google Spanner).
* **Use Case**: Financial ledgers, distributed locks.

### 4.3 Sequential Consistency
* **Definition**: All nodes see all operations in the exact same order, but that order doesn't necessarily match the real-time physical clock. 
* **Example**: Client A writes `X=1`, then Client B writes `Y=2`. 
  * Node 1 might see `X=1` then `Y=2`. 
  * Node 2 MUST also see `X=1` then `Y=2`. 
  * They cannot see `Y=2` then `X=1`. 
  * However, they might both see this sequence happen 5 seconds after the actual physical writes occurred. The order is preserved globally, but real-time freshness is not.
* **Use Case**: Multiplayer games where the exact timing matters less than everyone seeing the same sequence of events.

### 4.4 Causal Consistency
* **Definition**: Operations that are causally related must be seen in the same order by all nodes. Operations that are concurrent (unrelated) can be seen in different orders by different nodes.
* **Example**: If User A posts a comment, and User B replies to A's comment, there is a causal link. Everyone in the world must see A's comment before B's reply. But if User C posts an unrelated comment on a different thread simultaneously, some users might see C before A, while others might see A before C.
* **Use Case**: Social media comment threads, collaborative document editing.

### 4.5 Eventual Consistency
* **Definition**: The weakest guarantee. If no new updates are made to a given data item, eventually all accesses will return the last updated value. There are no ordering guarantees while the system is converging.
* **Example**: DNS is the classic example. If you change a DNS record, it might take 24-48 hours for every ISP in the world to reflect the change. During that time, different users see different IPs. 
* **Use Case**: Search engine indexing, metrics aggregation, user profile updates (changing your bio).

### 4.6 Client-Centric Consistency Models
These focus on the experience of a single client session, rather than global guarantees.

* **Read-Your-Writes**: If you update your profile picture, the database guarantees that the next time YOU load the page, you see the new picture. Other users might still see the old one for a while, but you are never confused by your own actions.
* **Monotonic Reads**: If you read a value at version 5, you will never subsequently read version 4. Time never goes backwards for a single client. If you refresh the page, you won't see older data than you saw previously.
* **Monotonic Writes**: A system guarantees to serialize writes by the same process.

---

## 5. Vector Clocks & Version Vectors

When dealing with AP or highly distributed systems (like Riak or Cassandra) that accept writes concurrently on different nodes without strict coordination, we must be able to detect write conflicts.

### 5.1 The Limitation of Lamport Clocks
Lamport clocks (discussed in detail in Section 9) provide a total ordering of events using simple integer counters. They can tell you the causal order. 

However, **Lamport clocks CANNOT detect concurrent events**. 
If we look at two Lamport timestamps, `Clock(A) = 5` and `Clock(B) = 10`:
* We know `A < B` in the logical clock sequence.
* But we **do not know** if Event A causally preceded (caused) Event B, or if A and B were completely concurrent and unrelated, and B just happened to get a higher number.

To safely merge data in distributed systems, we must know if two updates were concurrent.

### 5.2 Vector Clocks
To detect concurrency, we use Vector Clocks. Instead of a single counter, a vector clock is an array of counters, one for each node in the system.

**Algorithm for a 3-node system (Nodes X, Y, Z):**
1. Initially, all clocks are `[0, 0, 0]`.
2. **Local Event**: When Node X performs a local event, it increments its own counter: `[1, 0, 0]`.
3. **Sending**: When Node X sends a message to Node Y, it attaches its vector clock `[1, 0, 0]`.
4. **Receiving**: When Node Y receives the message, it updates its own clock by taking the element-wise maximum of its clock and the received clock, and then increments its own counter: `max([0,0,0], [1,0,0]) + increment_Y = [1, 1, 0]`.

### 5.3 Conflict Detection (Version Vectors)
Version vectors are a practical, optimized implementation of vector clocks used in databases to detect write conflicts on specific keys/rows.

**How to compare Vector Clocks (V1 and V2):**
* **Dominance (Causality)**: V1 dominates V2 if every counter in V1 is `>=` the corresponding counter in V2, and at least one counter is strictly greater. This means V1 is causally newer.
* **Equality**: V1 equals V2 if all counters are identical.
* **Conflict (Concurrency)**: If neither V1 dominates V2, NOR V2 dominates V1, the events are **concurrent**.

```text
Example of Conflict Detection:

Initial State: [X:0, Y:0]

1. Node X updates the shopping cart (adds Apple):
   Node X vector: [X:1, Y:0]

2. Node Y independently updates the SAME cart (adds Banana):
   Node Y vector: [X:0, Y:1]

3. System attempts to synchronize Node X and Node Y.
   Compare [X:1, Y:0] vs [X:0, Y:1]
   
   X:1 > X:0
   Y:0 < Y:1

   Because neither vector dominates the other, they are INCOMPARABLE.
   This definitively proves a CONCURRENT WRITE CONFLICT occurred. Node X and Node Y 
   modified the data without seeing each other's changes.
```

### 5.4 Conflict Resolution Strategies
When a version vector indicates a conflict, the system must resolve it:

1. **Last-Write-Wins (LWW)**: 
   * The database looks at the physical wall-clock timestamp attached to the writes (ignoring the vector clock entirely) and simply keeps the one with the newest timestamp.
   * **Pros**: Simple, automatic, database handles it.
   * **Cons**: Data loss. In the cart example, the Apple or Banana will be silently deleted. (Used heavily by Cassandra).
2. **Multi-Value Register (Client Resolution)**: 
   * The database stores BOTH conflicting versions. On the next read request, it returns both versions to the client.
   * **Pros**: No data loss.
   * **Cons**: Pushes massive complexity to the application code. The application must merge the data (e.g., merging the carts to contain both Apple and Banana) and write back the resolved version. (Made famous by Amazon Dynamo).
3. **CRDTs (Conflict-Free Replicated Data Types)**: 
   * Specialized data structures (like counters, sets) designed mathematically so that concurrent updates can always be merged automatically without conflict or data loss. Used in modern collaborative apps like Figma.

---

## 6. Quorum Mechanics

In a distributed database where data is replicated across multiple nodes for fault tolerance, how do we ensure we get consistent reads? If we write to Node A, and immediately read from Node B, how do we ensure Node B has the data?

We use Quorums. A quorum is the minimum number of nodes that must participate in an operation for it to be considered successful.

### 6.1 The Quorum Invariant
To guarantee strong consistency (specifically, read-your-writes and linearizability), the system must adhere to the mathematical formula:

**`R + W > N`**

Where:
* **`N`** = Replication Factor (total number of nodes storing a copy of the data)
* **`W`** = Write Quorum (number of nodes that must acknowledge a write for it to succeed)
* **`R`** = Read Quorum (number of nodes that must respond to a read request)

Because `R + W > N`, by the Pigeonhole Principle, the set of nodes we write to and the set of nodes we read from **must overlap by at least one node**. Therefore, at least one node in the read quorum will possess the latest write, and we can look at the version vectors or timestamps to return the correct data.

### 6.2 Common Configurations
Assume a typical production setup with `N = 3` replicas.

1. **Balanced / Strict Quorum (R=2, W=2)**: 
   * `2 + 2 = 4 > 3`. Strong consistency is guaranteed.
   * Tolerates 1 node failure for both reads and writes. If 1 node is dead, 2 are still up, so quorums can be met.
   * This is the most common default setting.

2. **Read-Optimized (R=1, W=3)**:
   * `1 + 3 = 4 > 3`. Strong consistency is guaranteed.
   * Reads are blazing fast (only need to hit 1 local node).
   * Writes are slow (must wait for all 3 nodes) and highly fragile (if 1 node goes down, ALL writes fail).
   * Good for read-heavy, rarely updated reference data.

3. **Write-Optimized (R=3, W=1)**:
   * `3 + 1 = 4 > 3`. Strong consistency is guaranteed.
   * Writes are fast (ack after 1 node saves it).
   * Reads are slow (must query all 3) and fragile.
   * Good for heavy logging or telemetry ingestion.

### 6.3 Read Repair
What happens when a node misses a write? 
In an `N=3, W=2, R=2` system, a write succeeds if Node 1 and Node 2 acknowledge it. Node 3 might have been offline or dropped the packet. Node 3 now has stale data.

When a client subsequently issues a read with `R=2`, the coordinator node might fetch data from Node 2 (up-to-date) and Node 3 (stale). 
The coordinator compares their timestamps/version vectors, identifies that Node 2 has the newer data, and returns that to the client. 
Crucially, **in the background, the coordinator issues a write to Node 3** with the newer data. This process of fixing stale replicas during read operations is called **Read Repair**.

### 6.4 Hinted Handoff
What if a target node (Node A) is down during a write? If we have W=2 and only 1 replica is up, the write would fail, hurting availability.

To improve availability, systems like Cassandra use Hinted Handoff. The coordinator writes the data to a temporary fallback node (Node D, which doesn't normally own this partition), wrapping it with a "hint" that says: *"This data belongs to Node A. Hold onto it until A comes back online."*
When Node A recovers, Node D streams the hinted data to A, then deletes its local copy. 

This provides high write availability but briefly sacrifices strict durability guarantees (if Node D crashes before A recovers, the data might be lost).

### 6.5 Sloppy Quorum
In a strict quorum, if a network partition leaves you with fewer than `W` healthy replica nodes for a specific key, writes fail. 

A **Sloppy Quorum** relaxes this constraint. It allows the system to accept writes to ANY `W` nodes in the entire cluster, even if they aren't the designated replicas for that specific partition. 
* **Trade-off**: This maximizes availability (strong AP behavior). However, it destroys strict consistency. A subsequent strict read (`R=2`) targeting the correct replicas might completely miss the data until the sloppy nodes eventually sync the data back to the correct nodes via hinted handoffs.

---

## 7. Consensus Algorithms

How do multiple independent nodes agree on a single value (or a sequence of log entries) in a system where networks drop packets and nodes randomly crash? This is the core distributed consensus problem.

### 7.1 The FLP Impossibility Theorem
In 1985, Fischer, Lynch, and Paterson published a paper proving the **FLP Impossibility Theorem**, one of the most famous results in distributed systems.

It states:
In an asynchronous network where messages can be delayed arbitrarily, and where even a single node can crash unannounced, **no deterministic consensus algorithm can guarantee it will ever terminate (reach agreement)**.

This means that if you try to write a purely deterministic algorithm for nodes to agree, there is always a sequence of delays and crashes that will result in an infinite deadlock. 

**Solution**: All practical consensus algorithms (Raft, Paxos) sidestep FLP by introducing **randomization** (like random election timeouts) to break symmetry and deadlocks. They guarantee safety (they won't agree on the wrong thing), but technically do not guarantee liveness (they might theoretically stall forever, though practically the probability goes to zero quickly).

### 7.2 Raft (Deep Dive)
Designed by Diego Ongaro and John Ousterhout at Stanford in 2014, Raft was created specifically to be understandable, unlike Paxos. It is the de facto standard consensus algorithm today, powering systems like etcd, Consul, CockroachDB, and TiDB.

Raft decomposes consensus into distinct, manageable subproblems:

#### A. Leader Election
* Nodes are always in one of three states: **Follower**, **Candidate**, or **Leader**.
* Time is divided into **Terms** (monotonically increasing integers). Each term begins with an election.
* **Mechanism**:
  1. All nodes start as Followers.
  2. If a Follower receives no heartbeats from a Leader for a randomized `election timeout` (typically 150-300ms), it promotes itself to a Candidate.
  3. It increments the term number, votes for itself, and sends `RequestVote` RPCs to all other nodes.
  4. If it receives votes from a majority of the cluster, it becomes the Leader and begins sending heartbeats.
  5. The *randomized* timeout is crucial—it prevents split votes where multiple nodes become candidates simultaneously and tie endlessly.

#### B. Log Replication
Once a Leader is elected, it is the sole authority for all writes.
1. Clients send write requests to the Leader.
2. The Leader appends the command to its local log.
3. The Leader sends `AppendEntries` RPCs to all Followers to replicate the log entry.
4. Once a **majority** of Followers write to their log and acknowledge (ACK) the request, the Leader **commits** the entry to its state machine (executes it).
5. The Leader responds with success to the client, and includes the commit index in subsequent heartbeats so Followers know they can safely apply the entry too.

#### C. Safety Properties
Raft's design enforces several strict safety invariants:
* **Election Safety**: At most one leader can be elected in a given term.
* **Log Matching**: If two logs contain an entry with the same index and term, then the logs are identical in all entries up through that given index. If a Follower's log conflicts with the Leader's, the Leader forces the Follower to overwrite its log to match.

```text
Raft State Machine Transitions (ASCII Diagram):

                     +----------------+
                     |                |
                     |    Follower    |<-------------------+
                     |                |                    |
                     +--------+-------+                    |
                              |                            |
          Times out,          |                            | Discovers
          starts election     |                            | current leader
                              v                            | or new term
                     +--------+-------+                    |
                     |                |                    |
          +--------->|   Candidate    |--------------------+
          |          |                |
          |          +--------+-------+
          |                   |
          | Times out,        | Receives majority
          | new election      | of votes
          |                   v
          |          +--------+-------+
          |          |                |
          +----------|     Leader     |
     Discovers       |                |
     server with     +----------------+
     higher term
```

### 7.3 Paxos (Overview)
Paxos is the grandfather of consensus algorithms, published by Leslie Lamport in 1989. It is famously used in Google Spanner and Cassandra (for lightweight transactions).

It operates in two broad phases:
* **Phase 1 (Prepare/Promise)**: A proposer suggests a proposal number `N`. Acceptors promise not to accept any future proposals with numbers lower than `N`.
* **Phase 2 (Accept/Accepted)**: Proposer suggests a value. Acceptors accept it if they haven't made a conflicting promise to a higher `N`.

While Basic Paxos is mathematically elegant, building a production system requires Multi-Paxos (streaming multiple values), which is notoriously difficult to understand, implement correctly, and debug. This is why Raft was created and is preferred for new systems.

---

## 8. Distributed Transactions

When a single logical operation must modify data across multiple separate databases, microservices, or partitions while maintaining ACID properties (Atomicity, Consistency, Isolation, Durability), we require distributed transactions.

### 8.1 Two-Phase Commit (2PC)
2PC is a synchronous protocol coordinated by a central Transaction Manager (Coordinator) to ensure all participating databases (Participants) either all commit or all rollback.

* **Phase 1: Prepare**: 
  * The Coordinator asks all participants, "Can you commit this transaction?"
  * Participants validate the transaction, write intent to their Write-Ahead Log (WAL), **acquire locks on the affected rows**, and reply "Yes" or "No".
* **Phase 2: Commit/Abort**: 
  * If ALL participants say "Yes", the Coordinator writes a "Commit" decision to its WAL and sends a "Commit" command to all participants.
  * If ANY participant says "No", the Coordinator sends an "Abort" command to all.
  * Participants execute the command and release their locks.

**The Major Flaw of 2PC: Blocking**
2PC is a blocking protocol. If a participant replies "Yes" to the prepare phase, it has locked its local resources. It is now waiting for Phase 2. 
If the Coordinator crashes or the network partitions right after Phase 1, the participant is **blocked**. It cannot commit (maybe someone else said No) and it cannot abort (maybe the coordinator decided to Commit). It must hold the locks indefinitely until the Coordinator recovers.

* **IMPORTANT Accuracy Note**: 2PC locking is **NOT indefinite** in a properly built system. Because the Coordinator persists its decision to a WAL, when the Coordinator node restarts (or a high-availability standby takes over), it reads the WAL and completes the Phase 2 protocol, resolving the in-doubt participants. However, during that downtime (which could be minutes), availability drops significantly as critical rows remain locked.

### 8.2 Three-Phase Commit (3PC)
3PC attempts to solve the blocking problem of 2PC by adding a "Pre-Commit" phase and utilizing timeouts. 
* **Reality check**: 3PC assumes a synchronous network model with bounded message delays, which is categorically false in the real world (Fallacy #1 & #2). During unpredictable network partitions, 3PC can actually lead to data inconsistencies and split-brain decisions. It is almost never used in modern production systems.

### 8.3 The Saga Pattern
Because 2PC locks resources and degrades availability, modern microservice architectures utilize the Saga pattern. A Saga breaks a distributed transaction into a sequence of local, independent transactions. 

Each microservice updates its own local database and publishes an event or message to trigger the next step in the saga.

If a step fails (e.g., inventory is reserved, but payment fails), the Saga executes **compensating transactions** to explicitly undo the previous steps (e.g., release the inventory).

**Implementations**:
1. **Choreography (Event-Driven)**: 
   * No central coordinator. Service A publishes `OrderCreated`. Service B listens, executes payment, then publishes `PaymentProcessed`. 
   * **Pros**: Highly decoupled, no single point of failure.
   * **Cons**: Very hard to monitor, test, and debug. The workflow logic is scattered across many codebases.
2. **Orchestration (Command-Driven)**: 
   * A central Saga Orchestrator (e.g., AWS Step Functions, Temporal, Camunda) manages the state machine. It tells Service A to create the order, waits for success, then tells Service B to process payment.
   * **Pros**: Centralized logic, easy to see the current state of a transaction.
   * **Cons**: Introduces a single point of failure/bottleneck (the orchestrator itself).

**When to use Sagas vs 2PC**: 
* Use 2PC for strictly coupled data within the boundaries of a single highly-available database cluster (like Google Spanner or CockroachDB). 
* Use Sagas for long-running, loosely coupled business processes spanning different domains or external microservices where eventual consistency is acceptable.

---

## 9. Time and Order in Distributed Systems

In a single machine, we rely on the local CPU clock to determine the order of events. In a distributed system spanning multiple machines, establishing a global timeline is incredibly difficult.

### 9.1 Wall Clock Problems (Physical Time)
Using physical time (Time of Day via the server's clock) to order distributed events is fundamentally flawed:
* **NTP Drift**: Quartz clocks on motherboards drift apart based on temperature and manufacturing variance. NTP (Network Time Protocol) synchronizes them with internet time servers, but there is always a skew (typically single-digit milliseconds, but can drift to seconds under load).
* **Time Going Backwards**: If a server's clock is running fast, NTP doesn't always slow it down; it sometimes forcibly steps the clock backward. This causes `time(Event_2) < time(Event_1)` even if Event 2 happened physically after Event 1 on the same machine.
* **Leap Seconds**: Extra seconds injected to account for Earth's rotation can wreak havoc on software assuming every minute has exactly 60 seconds.

Therefore, you **cannot** reliably say Event A happened before Event B simply because Node 1's timestamp for A is `10:00:01.000` and Node 2's timestamp for B is `10:00:01.005`.

### 9.2 Lamport Timestamps (Logical Time)
Leslie Lamport introduced logical clocks in 1978 to capture the "happens-before" relationship without relying on physical time at all. 

* **Mechanism**:
  1. Each node keeps a simple integer counter `L` (initialized to 0).
  2. Before executing any event, a node increments `L = L + 1`.
  3. When a node sends a message, it attaches its current `L`.
  4. When a node receives a message with timestamp `T`, it updates its own clock to be greater than both its current time and the received time: `L = max(L, T) + 1`.
* **Properties**: It provides a total ordering of events. If Event A causally influences Event B, then `L(A) < L(B)`. To break ties if two nodes generate the same counter, we append the Node ID: `(L, NodeID)`.
* **Critical Limitation**: As emphasized in Section 5, Lamport clocks **CANNOT detect concurrent events**. Just because `L(A) < L(B)` does not mean A caused B; they could be completely concurrent and unrelated. Only Vector Clocks can detect concurrency.

### 9.3 Hybrid Logical Clocks (HLC)
Modern distributed databases (like CockroachDB and MongoDB) use Hybrid Logical Clocks. HLCs combine physical NTP time with logical counters. 
They attempt to stay as close to physical time as possible (for human readability and point-in-time recovery) but use logical counters to guarantee monotonicity (time never goes backwards) and strictly track causality across nodes.

### 9.4 Google Spanner TrueTime
Google bypassed the logical clock problem entirely by throwing customized hardware at it. TrueTime utilizes GPS receivers and atomic clocks installed directly in every Google datacenter. 

TrueTime doesn't return a single timestamp; it returns an interval `[earliest, latest]` representing the bounded uncertainty of the clock at that exact moment (typically 1 to 7 milliseconds).

If Spanner needs to guarantee strict linearizability (ensuring a transaction is visibly completed before the next begins), it executes the transaction and then **simply waits out the uncertainty interval** (e.g., pauses for 7ms) before returning success to the client. This guarantees that physical time has definitively passed the transaction's commit timestamp, ensuring global causal ordering without communication overhead.

---

## 10. Failure Detection & Membership

How does a cluster of 1,000 nodes know if Node 42 is dead, overloaded, or just experiencing a network partition?

### 10.1 Heartbeating (Ping/Ack)
Nodes ping a central coordinator or each other every `X` seconds. If no ping is received after `Y` seconds, the node is declared dead.
* **The Problem**: If the network is momentarily congested, pings are delayed. The system might incorrectly declare a healthy node dead (false positive), triggering an expensive, massive reshuffling of terabytes of data to recreate replicas, which further congests the network, leading to cascading failures.

### 10.2 Phi Accrual Failure Detector
Used by Cassandra and Akka. Instead of a binary "Up/Down" state based on a hardcoded timeout, it outputs a continuous probability value `Phi (Φ)` representing the likelihood that a node is dead, based on the historical distribution of heartbeat latencies.
* **Adaptive**: If network latency spikes system-wide, the historical average increases, and the detector dynamically adapts its threshold. This drastically reduces false-positive failures during transient network weather. Application logic triggers node removal only when `Φ > 8` (roughly 99.9999% certainty).

### 10.3 Gossip Protocol (Epidemic Routing)
Instead of having a central coordinator monitor all 1,000 nodes (a massive bottleneck), nodes use epidemic information spreading.
* **Mechanism**: Every second, a node randomly picks `K` other nodes and shares its state (who it thinks is alive/dead, its current version vectors).
* **Properties**: Information spreads exponentially, similar to a viral infection. Convergence across the entire cluster happens reliably in `O(log N)` time.
* **Robustness**: Highly resilient to network partitions and node churn. Used in Cassandra (for topology discovery), Consul, and Amazon Dynamo.

### 10.4 SWIM Protocol
Scalable Weakly-consistent Infection-style Process Group Membership. It elegantly combines failure detection and membership via gossip to reduce network overhead.
* Instead of everyone heartbeating a central server, Node A randomly probes Node B. 
* If A cannot reach B directly (perhaps a routing issue), A asks Node C and Node D to try reaching B on its behalf. 
* If C and D also fail to reach B, B is marked as suspect, and eventually dead, and this update is efficiently gossiped to the cluster.

---

## 11. Distributed Locking

Sometimes, multiple processes across different machines need exclusive, mutually-exclusive access to a shared resource (like writing to a specific file in S3, or electing a master worker to process a batch job).

### 11.1 Why Distributed Locks are Dangerous
Martin Kleppmann (author of *Designing Data-Intensive Applications*) famously outlined why standard, time-based distributed locks are flawed and dangerous:

1. Client 1 acquires a lock from the lock service, valid for 10 seconds.
2. Client 1 experiences a long JVM Garbage Collection pause (e.g., 15 seconds), or its VM is paused by the hypervisor.
3. The 10 seconds pass. The lock expires in the lock service.
4. Client 2 acquires the lock and starts writing data to the shared resource.
5. Client 1's GC pause ends. It wakes up, is unaware time has passed, believes it still holds the valid lock, and writes to the resource.
**Result**: Uncoordinated concurrent writes leading to data corruption.

### 11.2 Fencing Tokens
To solve the GC pause and network delay problems, locks must generate a **Fencing Token** (a monotonically increasing integer) upon acquisition, and the target storage system must validate it.

1. Client 1 acquires lock, lock service grants token `33`.
2. Client 1 pauses. Lock expires.
3. Client 2 acquires lock, lock service grants token `34`.
4. Client 2 writes to storage, passing token `34`. The storage system accepts it and remembers `34` as the highest seen token.
5. Client 1 wakes up, writes to storage passing token `33`.
6. The storage system explicitly rejects Client 1's write because `33 < 34`. Correctness is maintained.

### 11.3 Redis Redlock
Redis provides distributed locking via the Redlock algorithm: a client tries to acquire a lock on a majority (`N/2 + 1`) of independent Redis nodes with a strict timeout. 
* **Critique**: Redlock relies heavily on assumptions about physical clock drift across the Redis nodes and, crucially, it does not provide fencing tokens. 
* **Verdict**: It is excellent for *efficiency* (preventing two workers from doing the same heavy computation and wasting CPU), but it is dangerous to use for *strict correctness* (where two workers modifying the same data causes catastrophic corruption).

### 11.4 Zookeeper Ephemeral Nodes
Apache Zookeeper (and etcd) is the enterprise standard for distributed coordination. 
Clients connect to ZK and create an "ephemeral node". If the client crashes, is partitioned, or its TCP session drops, ZK reliably deletes the node. Other clients set watches on this node to immediately know when the leader dies. 
Crucially, ZK provides the linearizability and monotonically increasing sequence numbers (zxid) required to generate safe fencing tokens, making it safe for strict correctness locking.

---

*End of Module 6*

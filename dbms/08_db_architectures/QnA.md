# Q&A — Database Architectures & NoSQL

---

## 🟢 Easy

**Q1. What is the difference between database partitioning and sharding?**

- **Partitioning**: Splitting a large table into smaller parts logically within the **same database engine instance**. It resides on the same machine.
- **Sharding**: Splitting a table horizontally (horizontal partitioning) and distributing those parts across **different physical database nodes** (different servers), each with its own independent CPU, RAM, and disk.

---

**Q2. State the CAP Theorem. What does it mean in practice?**

The CAP theorem states that a distributed data store can guarantee at most two of: **Consistency** (all nodes see the same data at the same time), **Availability** (every request gets a non-error response), and **Partition Tolerance** (system runs despite network disconnects).

**In practice**: Networks *will* partition eventually. Therefore, Partition Tolerance ($P$) is non-negotiable. The real choice is strictly between:
- **CP**: Choose Consistency. Reject writes or block reads if a partition cannot reach the majority quorum.
- **AP**: Choose Availability. Allow partitioned nodes to accept reads/writes, returning stale data and resolving conflicts later.

---

**Q3. Name the four primary categories of NoSQL databases and their main use cases.**

1. **Key-Value**: Stores data as simple key-value pairs (e.g., Redis). Best for: session stores, caching, user profiles.
2. **Document**: Stores data as semi-structured documents like JSON (e.g., MongoDB). Best for: content management, e-commerce catalog, schema-flexible logs.
3. **Wide-Column**: Grouped columns stored in tables (e.g., Cassandra). Best for: timeseries, IoT metrics, massive scale analytics.
4. **Graph**: Stores data as nodes and edges (relationships) (e.g., Neo4j). Best for: social networks, recommendation engines, fraud detection.

---

## 🟡 Medium

**Q4. Explain Consistent Hashing. Why is it used in sharding?**

- **What it is**: Consistent Hashing maps both database keys and server node addresses to a shared circular hash space (the "hash ring"). To write/read a key, we hash the key and traverse the ring clockwise until we hit the first server node.
- **Why used**: Under traditional hashing (`node = hash(key) % N`), if we add or remove a server (changing $N$), almost all keys hash to different nodes, triggering a massive data migration (nearly 100% of data moves). With Consistent Hashing, adding/removing a node only affects the keys immediately adjacent to it on the ring. Only $\approx 1/N$ of the total keys need to migrate, minimizing network and disk overhead during scaling.

---

**Q5. Explain the PACELC theorem. Give examples of databases classified under it.**

The PACELC theorem is an extension of the CAP theorem to describe distributed database behavior during normal (non-partitioned) operation:
- **P-A / C**: If there is a Partition ($P$), choose Availability ($A$) or Consistency ($C$).
- **E-L / C**: Else ($E$, normal operation), choose Latency ($L$) or Consistency ($C$).

Classifications:
- **Cassandra (PA/EL)**: Prefers Availability during partitions and Low Latency during normal operations (uses async replication).
- **MongoDB (PC/EC)**: Prefers Consistency during partitions and Consistency during normal operations (waits for replica write-acknowledgments, adding latency).
- **HBase (PC/EC)**: Strong consistency in both states.

---

## 🔴 Hard

**Q6. You are designing a leaderless replicated data store (like Cassandra) with $N = 5$ replicas. Calculate:**
1. **The minimum Read Quorum ($R$) needed if Write Quorum ($W$) is set to 3 to ensure strong consistency.**
2. **If we configure $W = 2$ and $R = 2$, is the system strongly consistent? If not, trace a scenario that leads to a stale read.**

#### Part 1: Minimum Read Quorum ($R$) for $W = 3$
The Quorum Invariant for strong consistency (read-your-writes) is:
$$R + W > N$$
Substitute $N = 5, W = 3$:
$$R + 3 > 5$$
$$R > 2 \implies R_{\text{min}} = 3$$

We need a read quorum of **$R = 3$** nodes to guarantee that at least one node in the read set overlaps with the write set, ensuring we fetch the most recent write.

#### Part 2: Analysis of $W = 2$ and $R = 2$ with $N = 5$
Check the Quorum Invariant:
$$R + W = 2 + 2 = 4$$
Since $4 \le 5$, the quorum invariant is **violated** ($R + W \ngtr N$). The system is **eventually consistent**, not strongly consistent.

**Stale Read Scenario Trace:**
- Let the 5 replicas be $A, B, C, D, E$. Initial state of row: `version = 1`.
- A client writes a new value `version = 2`.
- Since $W = 2$, the write succeeds as soon as it is written to 2 nodes, say $A$ and $B$.
- Replicas $C, D, E$ still contain the old value `version = 1`.
- A second client performs a read. Since $R = 2$, it queries 2 random nodes, say $C$ and $D$.
- Both $C$ and $D$ return `version = 1`.
- The client receives `version = 1` (a stale read), completely missing the write to `version = 2` that happened on $A$ and $B$.

---

**Q7. Design a database sharding strategy for an international chat application. The database must store messages. The table schema is `messages(message_id, sender_id, receiver_id, chat_room_id, content, timestamp)`.**
1. **Analyze candidate partition keys: `message_id`, `sender_id`, `chat_room_id`.**
2. **Recommend the optimal partition key and justify your choice.**

#### Part 1: Candidate Key Analysis
- **`message_id`**:
  - *Pros*: Good distribution if IDs are generated randomly or using Snowflake UUIDs. Prevents hot spots.
  - *Cons*: Most queries in a chat app are: "Retrieve the last 50 messages for chat room X." If partitioned by `message_id`, this query must be **scatter-gathered** (sent to every single shard in the system to collect messages, then sorted by timestamp). Terrible read performance at scale.
- **`sender_id`**:
  - *Pros*: Distributes users evenly.
  - *Cons*: Chat messages belong to a room/conversation between multiple users. Querying messages in a room still requires querying shards of multiple senders.
- **`chat_room_id`**:
  - *Pros*: All messages sent in the same chat room are stored on the **same shard**. Reading the history of a chat room requires querying exactly **one shard** (single-partition read). Extremely fast.
  - *Cons*: Large group chat rooms (celebrity channels or public announcements) can create hot shards (one shard gets hammered with writes, others idle).

#### Part 2: Recommendation & Justification
The optimal partition key is **`chat_room_id`**.

**Justification**:
- Chat applications are read-heavy on a per-room basis (scrolling through history). Storing a chat room's history on a single shard eliminates scatter-gather queries, keeping read latency low.
- **Handling Hot Shard Edge Cases**: For very large public chat rooms (e.g., millions of members), we can use a **composite/salted partition key**: `chat_room_id + hash(timestamp)`. This splits the hot room's writes across multiple shards for active intervals while keeping normal private chats consolidated on single shards.

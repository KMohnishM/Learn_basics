# Module 6: Distributed Systems Deep Dive

When you scale from one server to many, you enter the realm of Distributed Systems. It is a world where network packets disappear, clocks are fundamentally out of sync, and servers crash silently.

## 1. The 8 Fallacies of Distributed Computing
Peter Deutsch (Sun Microsystems) defined 8 false assumptions engineers make when moving from a single machine to a distributed architecture:
1. The network is reliable. (It isn't. Cables get cut, switches die).
2. Latency is zero. (Speed of light is a hard limit).
3. Bandwidth is infinite.
4. The network is secure.
5. Topology doesn't change.
6. There is one administrator.
7. Transport cost is zero.
8. The network is homogeneous.

## 2. The CAP Theorem
Formulated by Eric Brewer. In a distributed data store, you can only guarantee two out of three properties:
- **Consistency**: Every read receives the most recent write or an error.
- **Availability**: Every request receives a (non-error) response, without the guarantee that it contains the most recent write.
- **Partition Tolerance**: The system continues to operate despite an arbitrary number of messages being dropped by the network between nodes.

**The Reality**: In the real world, network partitions (P) WILL happen. You cannot avoid them. Therefore, you must choose between **CP** (Consistency under partition) or **AP** (Availability under partition).
- **CP System (e.g., Zookeeper, HBase)**: If a network link breaks between two nodes, the system refuses to accept writes to prevent data inconsistency. 
- **AP System (e.g., Cassandra, DynamoDB)**: If a link breaks, the system accepts writes on both sides. When the network heals, the system has to figure out how to merge the conflicting data.

## 3. Consensus Algorithms
How do multiple machines agree on a single value (or who the "Leader" is) when the network is unreliable?
- **Raft**: Understandable consensus. Nodes elect a leader via heartbeats and randomized timeouts. The leader takes writes and replicates the log to followers. If a follower misses a heartbeat, it assumes the leader is dead and starts an election.
- **Paxos**: The mathematically proven, but notoriously difficult to understand predecessor to Raft. 

## 4. Distributed Transactions
How do you update a database in Microservice A and a database in Microservice B atomically?
- **Two-Phase Commit (2PC)**: A coordinator asks all services "Are you ready to commit?" (Prepare Phase). If all say yes, it tells them "Commit!" (Commit Phase). Problem: It is blocking. If the coordinator dies during the commit phase, the databases are locked indefinitely.
- **The Saga Pattern**: A sequence of local transactions. Service A updates its DB and publishes an event. Service B hears the event and updates its DB. If Service B fails, it publishes a "Failure" event, and Service A executes a **Compensating Transaction** (a rollback, e.g., refunding the money).

## 5. Time and Order
You cannot rely on the physical clock of a server (`time.time()`). Server A's clock might be 5 milliseconds faster than Server B's. If they both process an event at the exact same physical time, Server A's event will look like it happened in the future!
- **Logical Clocks (Lamport Timestamps)**: A way to capture the *causality* of events (Event A happened before Event B) using a simple incrementing integer attached to messages, rather than relying on physical time.

---
## Next Steps
Go to `labs/` to run a Python simulation of the CAP Theorem!

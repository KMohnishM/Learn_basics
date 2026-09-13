"""
consistent_hashing.py
=====================
A complete, production-quality implementation of Consistent Hashing with Virtual Nodes.

This is the algorithm used by:
  - Apache Cassandra (vnodes for data distribution)
  - Amazon DynamoDB (partition assignment)
  - Memcached clients (ketama consistent hashing)
  - Nginx upstream hashing
  - Content Delivery Networks (cache shard assignment)

Why Consistent Hashing?
  Regular hash: server = hash(key) % num_servers
    Problem: Changing num_servers causes (N-1)/N keys to remap
    Example: 3 servers -> 4 servers: ~75% of keys move to new server!
    This causes a cache stampede (or massive data rebalancing in databases)

  Consistent hash: Only K/N keys need to move when a server is added/removed
    Example: 3 servers -> 4 servers: only ~25% of keys move to new server
    K = total keys, N = number of servers

How to run:
  python consistent_hashing.py

Concepts demonstrated:
  1. Basic ring construction
  2. Server placement on the ring
  3. Key-to-server mapping
  4. Adding a server (minimal disruption)
  5. Removing a server (minimal disruption)
  6. Virtual nodes (for even distribution)
  7. Distribution statistics (to verify evenness)
"""

import hashlib
import bisect
import random
import string
from collections import defaultdict
from typing import Optional


class ConsistentHashRing:
    """
    Consistent Hash Ring with Virtual Node support.
    
    The ring is implemented as a SORTED LIST of (hash_value, server_name) tuples.
    For each key lookup, we:
        1. Hash the key to get a position on the ring (0 to 2^32-1)
        2. Find the first server whose position is >= the key's hash (clockwise)
        3. If no such server exists (key hash is larger than all servers), wrap around
           and use the first server (the lowest hash value on the ring)
    
    This is efficiently implemented using binary search on the sorted list.
    
    Args:
        virtual_nodes_per_server: How many virtual nodes each physical server gets.
            Higher value = more even distribution but more memory.
            Typical production values: 150-300 per server.
            We use 150 by default (Cassandra uses 256 by default).
    
    Internal data structures:
        ring: SortedList of (hash_value, server_name) pairs
              Kept sorted by hash_value for binary search
        sorted_hashes: List of just the hash values (for bisect)
        ring_map: Dict mapping hash_value -> server_name
        servers: Set of physical server names
    """
    
    def __init__(self, virtual_nodes_per_server: int = 150):
        """
        Initialize an empty hash ring.
        
        Args:
            virtual_nodes_per_server: Number of positions each server occupies on the ring.
                More virtual nodes = more even distribution (law of large numbers)
                Less virtual nodes = faster lookups but uneven distribution
        """
        # Number of virtual nodes per physical server
        # This is the key parameter for distribution evenness
        self.virtual_nodes_per_server = virtual_nodes_per_server
        
        # Sorted list of hash values (positions on the ring)
        # We keep this sorted using bisect for O(log N) lookup
        self.sorted_hashes: list[int] = []
        
        # Mapping from hash value (ring position) to server name
        # Each server has virtual_nodes_per_server entries in this dict
        self.ring_map: dict[int, str] = {}
        
        # Set of physical server names (for tracking what's in the ring)
        self.servers: set[str] = set()
    
    def _hash(self, key: str) -> int:
        """
        Hash a string key to an integer position on the ring.
        
        We use MD5 and take the first 4 bytes as a 32-bit integer.
        This gives us a range of [0, 2^32 - 1] = [0, 4,294,967,295].
        
        Why MD5 and not a faster hash?
            - MD5 produces a uniform distribution (good for ring placement)
            - Speed is less critical here (this is during ring setup/lookup, not hot path)
            - In production, use xxhash or murmurhash3 for better performance
        
        Why use only 4 bytes (32-bit)?
            - Gives 4 billion positions on the ring (enough for any practical purpose)
            - Smaller numbers = faster sorting and comparison
            - Production systems sometimes use 64-bit (MD5 gives 16 bytes)
        
        Args:
            key: String to hash. Can be a server name (during ring construction)
                 or a cache key/user ID (during lookup).
        
        Returns:
            Integer in range [0, 2^32 - 1]
        """
        md5_hash = hashlib.md5(key.encode('utf-8')).digest()
        # Convert first 4 bytes to a big-endian unsigned 32-bit integer
        return int.from_bytes(md5_hash[:4], byteorder='big')
    
    def add_server(self, server_name: str) -> None:
        """
        Add a server to the hash ring.
        
        For each virtual node, we:
            1. Create a unique key: "server_name:vnode_index"
            2. Hash it to get a ring position
            3. Insert into the sorted ring
        
        When a new server is added:
            - Keys that used to go to the NEXT clockwise server now go to the new server
            - Only ~1/N of all keys are affected (where N = new server count)
            - This is the fundamental advantage of consistent hashing!
        
        Time complexity: O(V * log(N*V)) where V = virtual nodes, N = current servers
            - V hash computations
            - Each bisect.insort is O(log(N*V))
        
        Args:
            server_name: Unique name for this server (e.g., "server-1", "192.168.1.1:8080")
        """
        if server_name in self.servers:
            print(f"Warning: Server '{server_name}' is already in the ring")
            return
        
        self.servers.add(server_name)
        
        # Place virtual_nodes_per_server positions on the ring for this physical server
        for i in range(self.virtual_nodes_per_server):
            # Create a unique key for each virtual node
            # Adding index i ensures each virtual node has a DIFFERENT hash
            vnode_key = f"{server_name}:vnode:{i}"
            hash_value = self._hash(vnode_key)
            
            # Add to ring map: hash_value -> physical server name
            # Multiple hash values (virtual nodes) all point to the same physical server
            self.ring_map[hash_value] = server_name
            
            # Insert into sorted list using bisect to maintain sorted order
            # bisect.insort is O(N) due to list insertion, but acceptable for setup
            bisect.insort(self.sorted_hashes, hash_value)
    
    def remove_server(self, server_name: str) -> None:
        """
        Remove a server from the hash ring.
        
        When a server is removed:
            - Its keys are automatically redistributed to the NEXT clockwise server
            - Only ~1/N of all keys are affected
            - No other servers are impacted
        
        This models what happens when:
            - A server crashes (removed from ring, traffic goes to next server)
            - A server is decommissioned (gracefully removed)
            - A database node is taken offline for maintenance
        
        Args:
            server_name: Name of server to remove. Must exist in the ring.
        
        Raises:
            KeyError: If server_name is not in the ring
        """
        if server_name not in self.servers:
            raise KeyError(f"Server '{server_name}' not found in the ring")
        
        self.servers.remove(server_name)
        
        # Remove all virtual nodes for this server
        for i in range(self.virtual_nodes_per_server):
            vnode_key = f"{server_name}:vnode:{i}"
            hash_value = self._hash(vnode_key)
            
            # Remove from ring map
            del self.ring_map[hash_value]
            
            # Remove from sorted hash list
            # bisect.bisect_left finds the index, then we remove it
            idx = bisect.bisect_left(self.sorted_hashes, hash_value)
            if idx < len(self.sorted_hashes) and self.sorted_hashes[idx] == hash_value:
                self.sorted_hashes.pop(idx)
    
    def get_server(self, key: str) -> Optional[str]:
        """
        Find which server is responsible for a given key.
        
        Algorithm:
            1. Hash the key to get its position on the ring
            2. Find the first server CLOCKWISE from that position (next larger hash)
            3. If we've gone past all servers (key hash > all server hashes), wrap around
               to the first server (minimum hash value) -- this simulates the ring
        
        This is the core operation of consistent hashing.
        Time complexity: O(log(N*V)) where N = servers, V = virtual nodes per server
        
        Args:
            key: The key to look up (cache key, user ID, session ID, etc.)
        
        Returns:
            Server name responsible for this key, or None if ring is empty
        
        Example:
            ring.get_server("user:12345") -> "server-3"
            ring.get_server("cache:photos:thumb") -> "server-1"
        """
        if not self.sorted_hashes:
            return None  # Empty ring
        
        # Hash the key to get its position on the ring
        key_hash = self._hash(key)
        
        # Binary search: find the first server hash >= key_hash
        # bisect_right returns the insertion point to the right of any existing key_hash
        # We use bisect_right so that a key with the exact same hash as a server goes
        # to THAT server (or technically the next one with bisect_right)
        idx = bisect.bisect(self.sorted_hashes, key_hash)
        
        # If idx equals the length, the key_hash is larger than all server hashes
        # Wrap around to the first server (simulate the circular ring)
        if idx >= len(self.sorted_hashes):
            idx = 0
        
        # Look up which physical server owns this virtual node position
        server_hash = self.sorted_hashes[idx]
        return self.ring_map[server_hash]
    
    def get_distribution(self, num_keys: int = 10000) -> dict:
        """
        Test how evenly keys are distributed across servers.
        
        This is used to validate that our virtual node count is sufficient
        for even distribution. We generate `num_keys` random keys and count
        how many go to each server.
        
        Args:
            num_keys: Number of test keys to generate. More keys = more accurate measurement.
                      10,000 is enough to see distribution patterns.
        
        Returns:
            Dictionary mapping server_name -> percentage of keys assigned to it
        
        Ideal distribution:
            With N servers, each server should get ~100/N percent of keys.
            Virtual nodes help approach this ideal.
            
            With 3 servers and 150 virtual nodes each (450 total positions):
                Ideal: 33.33% each
                Typical actual: 30-37% each (within 10% of ideal)
            
            With 3 servers and 1 virtual node each (3 total positions):
                Could be wildly uneven: 10%, 60%, 30% (depends on hash values)
        """
        if not self.servers:
            return {}
        
        # Count how many of the test keys go to each server
        count_per_server = defaultdict(int)
        
        for i in range(num_keys):
            # Generate a random key (simulating real cache keys or user IDs)
            key = f"test_key:{i}:{random.randint(0, 1000000)}"
            server = self.get_server(key)
            if server:
                count_per_server[server] += 1
        
        # Convert to percentages for easy reading
        distribution = {}
        for server in self.servers:
            count = count_per_server.get(server, 0)
            distribution[server] = {
                "count": count,
                "percentage": (count / num_keys) * 100
            }
        
        return distribution
    
    def print_ring_summary(self) -> None:
        """Print a summary of the current ring state."""
        print(f"\nHash Ring State:")
        print(f"  Physical servers: {len(self.servers)}")
        print(f"  Virtual nodes per server: {self.virtual_nodes_per_server}")
        print(f"  Total ring positions: {len(self.sorted_hashes)}")
        print(f"  Servers: {sorted(self.servers)}")


# =============================================================================
# DEMONSTRATION FUNCTIONS
# =============================================================================

def demo_basic_consistent_hashing():
    """
    Demo 1: Basic consistent hashing - add servers, route keys.
    Shows that the same key always goes to the same server.
    """
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Consistent Hashing")
    print("=" * 60)
    
    # Create ring with low virtual node count to better illustrate concepts
    # (In production, use 150+)
    ring = ConsistentHashRing(virtual_nodes_per_server=50)
    
    # Add 3 servers to the ring
    ring.add_server("cache-server-1")
    ring.add_server("cache-server-2")
    ring.add_server("cache-server-3")
    ring.print_ring_summary()
    
    # Test some keys
    test_keys = [
        "user:1001",
        "user:2002",
        "product:5678",
        "session:abc123",
        "thumbnail:img_001",
        "search:query:hello+world",
    ]
    
    print("\nKey-to-Server Mapping:")
    print("-" * 50)
    initial_mapping = {}
    for key in test_keys:
        server = ring.get_server(key)
        initial_mapping[key] = server
        print(f"  {key:<35} -> {server}")
    
    return ring, initial_mapping, test_keys


def demo_server_addition_minimal_disruption(ring, initial_mapping, test_keys):
    """
    Demo 2: Add a 4th server. Show that MOST keys don't change.
    This is the key advantage of consistent hashing over regular hashing.
    """
    print("\n" + "=" * 60)
    print("DEMO 2: Adding a Server (Minimal Key Disruption)")
    print("=" * 60)
    
    print("\nAdding 'cache-server-4' to the ring...")
    ring.add_server("cache-server-4")
    ring.print_ring_summary()
    
    print("\nKey-to-Server Mapping AFTER adding cache-server-4:")
    print("-" * 50)
    moved_count = 0
    for key in test_keys:
        new_server = ring.get_server(key)
        old_server = initial_mapping[key]
        moved = new_server != old_server
        if moved:
            moved_count += 1
        status = "MOVED" if moved else "same"
        print(f"  {key:<35} -> {new_server:<20} ({status})")
    
    print(f"\nResult: {moved_count}/{len(test_keys)} keys moved to new server")
    print(f"With regular hashing: 3/4 = 75% of keys would have moved!")
    print(f"With consistent hashing: only ~{moved_count}/{len(test_keys)} moved")
    
    return ring


def demo_server_removal_minimal_disruption(ring, test_keys):
    """
    Demo 3: Remove a server. Show that only that server's keys are reassigned.
    This models a server failure or graceful decommission.
    """
    print("\n" + "=" * 60)
    print("DEMO 3: Removing a Server (Server Failure Simulation)")
    print("=" * 60)
    
    # Record current state
    before_removal = {key: ring.get_server(key) for key in test_keys}
    
    print("\nSimulating: cache-server-2 has crashed!")
    print("Removing cache-server-2 from the ring...")
    ring.remove_server("cache-server-2")
    ring.print_ring_summary()
    
    print("\nKey-to-Server Mapping AFTER cache-server-2 crashed:")
    print("-" * 60)
    for key in test_keys:
        new_server = ring.get_server(key)
        old_server = before_removal[key]
        moved = new_server != old_server
        status = "REASSIGNED" if moved else "unchanged"
        print(f"  {key:<35} -> {new_server:<20} ({status})")
    
    print("\nKey insight: Only keys that were on cache-server-2 needed reassignment!")
    print("Keys on cache-server-1, cache-server-3, cache-server-4 are UNAFFECTED")
    
    return ring


def demo_distribution_analysis():
    """
    Demo 4: Compare distribution with 1 vs 150 virtual nodes.
    Shows WHY virtual nodes are necessary for even distribution.
    """
    print("\n" + "=" * 60)
    print("DEMO 4: Virtual Nodes and Distribution Evenness")
    print("=" * 60)
    
    servers = ["db-shard-1", "db-shard-2", "db-shard-3"]
    
    # Test with 1 virtual node (no virtual nodes, effectively)
    print("\nRing with 1 virtual node per server:")
    ring_no_vnodes = ConsistentHashRing(virtual_nodes_per_server=1)
    for s in servers:
        ring_no_vnodes.add_server(s)
    
    dist = ring_no_vnodes.get_distribution(num_keys=10000)
    for server, data in sorted(dist.items()):
        bar = "#" * int(data["percentage"])
        print(f"  {server:<15}: {data['percentage']:5.1f}% {bar}")
    
    print(f"\n  Ideal distribution: 33.3% each")
    print(f"  With 1 vnode: distribution is very uneven (depends on random hash positions)")
    
    # Test with 50 virtual nodes
    print("\nRing with 50 virtual nodes per server:")
    ring_50_vnodes = ConsistentHashRing(virtual_nodes_per_server=50)
    for s in servers:
        ring_50_vnodes.add_server(s)
    
    dist = ring_50_vnodes.get_distribution(num_keys=10000)
    for server, data in sorted(dist.items()):
        bar = "#" * int(data["percentage"])
        print(f"  {server:<15}: {data['percentage']:5.1f}% {bar}")
    
    # Test with 150 virtual nodes (production-like)
    print("\nRing with 150 virtual nodes per server (production-like):")
    ring_150_vnodes = ConsistentHashRing(virtual_nodes_per_server=150)
    for s in servers:
        ring_150_vnodes.add_server(s)
    
    dist = ring_150_vnodes.get_distribution(num_keys=10000)
    for server, data in sorted(dist.items()):
        bar = "#" * int(data["percentage"])
        print(f"  {server:<15}: {data['percentage']:5.1f}% {bar}")
    
    print("\nWith 150 virtual nodes, distribution is within 3-5% of ideal!")
    print("This is why Cassandra defaults to 256 vnodes (they call them 'token ranges')")


def demo_weighted_consistent_hashing():
    """
    Demo 5: Weighted consistent hashing for heterogeneous server capacity.
    Larger servers get more virtual nodes -> more of the key space -> more traffic.
    """
    print("\n" + "=" * 60)
    print("DEMO 5: Weighted Consistent Hashing")
    print("(For servers with different capacities)")
    print("=" * 60)
    
    class WeightedConsistentHashRing(ConsistentHashRing):
        """Extended ring that supports per-server virtual node counts (weights)."""
        
        def __init__(self):
            # We'll handle virtual nodes manually, don't set a fixed count
            super().__init__(virtual_nodes_per_server=0)
            self.server_weights = {}
        
        def add_server(self, server_name: str, weight: int = 100) -> None:
            """Add a server with a custom weight (number of virtual nodes)."""
            self.server_weights[server_name] = weight
            self.servers.add(server_name)
            
            for i in range(weight):
                vnode_key = f"{server_name}:vnode:{i}"
                hash_value = self._hash(vnode_key)
                self.ring_map[hash_value] = server_name
                bisect.insort(self.sorted_hashes, hash_value)
    
    ring = WeightedConsistentHashRing()
    
    # 3 servers with different capacities
    # Server 1: 32GB RAM, 8 CPU -> weight 200 (high capacity)
    # Server 2: 16GB RAM, 4 CPU -> weight 100 (standard)
    # Server 3: 8GB RAM, 2 CPU  -> weight 50  (low capacity, older hardware)
    ring.add_server("large-server", weight=200)     # Gets ~57% of keys
    ring.add_server("medium-server", weight=100)    # Gets ~29% of keys
    ring.add_server("small-server", weight=50)      # Gets ~14% of keys
    
    dist = ring.get_distribution(num_keys=10000)
    print("\nWeighted distribution (large:medium:small = 200:100:50 = 4:2:1):")
    for server, data in sorted(dist.items()):
        bar = "#" * int(data["percentage"] / 2)
        print(f"  {server:<18}: {data['percentage']:5.1f}% {bar}")
    
    print("\nExpected: large ~57%, medium ~29%, small ~14%")
    print("This ensures each server handles traffic proportional to its capacity")
    print("Used in Cassandra when nodes have different storage capacities")


def demo_real_world_use_case():
    """
    Demo 6: Real-world use case - Distributed Redis Cache Sharding.
    Shows how a production cache cluster uses consistent hashing.
    """
    print("\n" + "=" * 60)
    print("DEMO 6: Real-World Use Case - Distributed Cache Sharding")
    print("=" * 60)
    
    print("\nScenario: Redis cluster with 5 shards (nodes)")
    print("We use consistent hashing to determine which shard holds each key")
    print("This is similar to how Redis Cluster works internally\n")
    
    ring = ConsistentHashRing(virtual_nodes_per_server=150)
    
    redis_nodes = [
        "redis-node-1:6379",
        "redis-node-2:6379",
        "redis-node-3:6379",
        "redis-node-4:6379",
        "redis-node-5:6379",
    ]
    
    for node in redis_nodes:
        ring.add_server(node)
    
    # Simulate cache lookups for various keys
    cache_operations = [
        ("user_profile:user_id:1001", "read"),
        ("product_catalog:product_id:5000", "read"),
        ("session:session_token:xK7mP9", "read"),
        ("rate_limit:api_key:key_abc", "write"),
        ("leaderboard:game_id:chess", "write"),
        ("thumbnail:video_id:v_999", "read"),
        ("search_cache:query:python+tutorial", "read"),
        ("cart:user_id:2002", "write"),
    ]
    
    print("Cache Key -> Redis Node Mapping:")
    print("-" * 70)
    for key, op in cache_operations:
        node = ring.get_server(key)
        print(f"  [{op.upper():<5}] {key:<45} -> {node}")
    
    print("\nDistribution across nodes:")
    dist = ring.get_distribution(100000)
    for node, data in sorted(dist.items()):
        bar = "#" * int(data["percentage"] * 2)
        print(f"  {node:<25}: {data['percentage']:5.1f}% {bar}")
    
    print("\nNow: Simulate adding a new node to the cluster (cache expansion)")
    print("Adding redis-node-6:6379...")
    
    # Record current assignments for 100 test keys
    test_keys = [f"test:key:{i}" for i in range(100)]
    before = {k: ring.get_server(k) for k in test_keys}
    
    ring.add_server("redis-node-6:6379")
    after = {k: ring.get_server(k) for k in test_keys}
    
    # Count how many moved
    moved = sum(1 for k in test_keys if before[k] != after[k])
    print(f"\nOf 100 test keys:")
    print(f"  Moved to new node: {moved}")
    print(f"  Stayed on same node: {100 - moved}")
    print(f"  Migration rate: {moved}% (expected ~{100//6}% = 1/6 of keys)")
    print(f"  Regular hashing would have moved: ~83% of keys!")


def main():
    """Run all consistent hashing demonstrations."""
    print("\n" + "#" * 60)
    print("  CONSISTENT HASHING WITH VIRTUAL NODES")
    print("  Module 2: Scalability Labs")
    print("#" * 60)
    
    # Demo 1: Basic routing
    ring, initial_mapping, test_keys = demo_basic_consistent_hashing()
    
    # Demo 2: Adding a server with minimal disruption
    ring = demo_server_addition_minimal_disruption(ring, initial_mapping, test_keys)
    
    # Demo 3: Server removal/failure
    ring = demo_server_removal_minimal_disruption(ring, test_keys)
    
    # Demo 4: Distribution analysis (why virtual nodes matter)
    demo_distribution_analysis()
    
    # Demo 5: Weighted hashing for heterogeneous servers
    demo_weighted_consistent_hashing()
    
    # Demo 6: Real-world Redis cache sharding
    demo_real_world_use_case()
    
    print("\n" + "=" * 60)
    print("KEY TAKEAWAYS:")
    print("=" * 60)
    print("""
1. CONSISTENT HASHING: When N servers -> N+1, only 1/(N+1) of keys move.
   Regular hashing: N/(N+1) of keys move (catastrophic for caches!)

2. VIRTUAL NODES: Without them, distribution is uneven (bad!).
   With 150+ virtual nodes per server, distribution is within 3-5% of ideal.

3. WEIGHTED VNODES: Give more virtual nodes to more powerful servers.
   They get proportionally more of the key space (and thus more traffic).

4. APPLICATIONS:
   - Cache sharding (memcached, Redis)
   - Database sharding (Cassandra, DynamoDB)
   - Load balancing for stateful services
   - CDN: which edge node caches which content

5. CASSANDRA uses this exact algorithm:
   - Each node is assigned "token ranges" (segments of the ring)
   - Data with a key hash in that range is stored on that node
   - Adding/removing nodes only migrates adjacent token ranges
    """)


if __name__ == "__main__":
    main()

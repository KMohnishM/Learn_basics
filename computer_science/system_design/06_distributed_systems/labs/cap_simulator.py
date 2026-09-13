import time

class Node:
    def __init__(self, name):
        self.name = name
        self.data = {}
        self.is_isolated = False

    def write(self, key, value):
        if self.is_isolated:
            print(f"[{self.name}] ERROR: I am isolated. Write failed.")
            return False
        self.data[key] = value
        print(f"[{self.name}] Wrote {key}={value}")
        return True

    def read(self, key):
        value = self.data.get(key, None)
        print(f"[{self.name}] Read {key}={value}")
        return value

class CPSystem:
    """Consistency and Partition Tolerance (Sacrifices Availability)"""
    def __init__(self):
        self.node_a = Node("Node A")
        self.node_b = Node("Node B")
        
    def write(self, key, value):
        # In a CP system, we MUST be able to write to BOTH nodes (quorum) to guarantee consistency.
        if self.node_a.is_isolated or self.node_b.is_isolated:
            print("[CP System] Write REJECTED to preserve consistency during partition.")
            return False
            
        self.node_a.write(key, value)
        self.node_b.write(key, value)
        return True

class APSystem:
    """Availability and Partition Tolerance (Sacrifices Consistency)"""
    def __init__(self):
        self.node_a = Node("Node A")
        self.node_b = Node("Node B")
        
    def write_to_a(self, key, value):
        # In an AP system, we accept the write even if the other node is dead.
        # This keeps the system highly available, but causes data inconsistency!
        self.node_a.write(key, value)
        if not self.node_b.is_isolated:
            self.node_b.write(key, value)
        else:
            print("[AP System] Node B is isolated. Write accepted ONLY on Node A. (Inconsistent State!)")

if __name__ == "__main__":
    print("=== Testing CP System ===")
    cp = CPSystem()
    cp.write("balance", 100)
    
    print("\n--- Network Partition Occurs! ---")
    cp.node_b.is_isolated = True
    
    cp.write("balance", 200) # This will fail to protect consistency.
    
    
    print("\n\n=== Testing AP System ===")
    ap = APSystem()
    ap.write_to_a("balance", 100)
    
    print("\n--- Network Partition Occurs! ---")
    ap.node_b.is_isolated = True
    
    ap.write_to_a("balance", 200) # This succeeds, but Node B still has balance=100!
    
    print("\n[AP System] Node A balance:", ap.node_a.data['balance'])
    print("[AP System] Node B balance:", ap.node_b.data['balance'])
    print("We have Split Brain! (Inconsistency)")

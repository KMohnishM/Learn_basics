import time
import uuid
import random

# Simulating 4 database shards
class Shard:
    def __init__(self, name):
        self.name = name
        self.data = {}

    def insert(self, key, value):
        self.data[key] = value

    def count(self):
        return len(self.data)

shards = [Shard("Shard A"), Shard("Shard B"), Shard("Shard C"), Shard("Shard D")]
num_shards = len(shards)

# Hash-based sharding function
def get_shard(user_id):
    # Convert string ID to an integer hash, then modulo by number of shards
    # This guarantees the same user_id always goes to the same shard
    shard_index = hash(user_id) % num_shards
    return shards[shard_index]

print("Simulating 10,000 user registrations...")
for _ in range(10000):
    user_id = str(uuid.uuid4())
    user_data = {"name": f"User_{random.randint(1,100)}", "status": "active"}
    
    # Route to the correct shard
    target_shard = get_shard(user_id)
    target_shard.insert(user_id, user_data)

print("\n--- Data Distribution ---")
for shard in shards:
    print(f"{shard.name}: {shard.count()} users")

print("\nNotice how hash-based sharding evenly distributes the data!")
print("But what happens if we add a 5th shard? All the modulo math changes, and we have to move all the data!")

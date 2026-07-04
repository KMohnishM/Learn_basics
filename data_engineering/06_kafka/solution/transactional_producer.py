from confluent_kafka import Producer
import json
import time

# To enable Exactly-Once semantics, you MUST provide a transactional.id
conf = {
    'bootstrap.servers': 'localhost:29092',
    'transactional.id': 'banking_producer_1'
}

producer = Producer(conf)

# 1. Initialize transactions (fences off any zombie producers with the same ID)
producer.init_transactions()

topic = "bank_transfers"

try:
    # 2. Begin transaction
    producer.begin_transaction()
    
    # 3. Produce messages as part of the transaction
    transfer = {"from": "Alice", "to": "Bob", "amount": 1000}
    producer.produce(topic, value=json.dumps(transfer).encode('utf-8'))
    
    # 4. Commit the transaction
    # If the network fails here and the producer retries, Kafka's transaction 
    # coordinator ensures the duplicate is deduplicated! Exactly-once achieved.
    producer.commit_transaction()
    print("Transaction committed successfully.")
    
except Exception as e:
    # If anything fails, abort the entire transaction
    print(f"Transaction failed, aborting: {e}")
    producer.abort_transaction()

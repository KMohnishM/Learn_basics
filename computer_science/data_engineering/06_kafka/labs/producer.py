from confluent_kafka import Producer
import json
import time
import random

# Kafka producer configuration
conf = {'bootstrap.servers': 'localhost:29092'}
producer = Producer(conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

topic = "user_events"

print("Producing real-time events to Kafka...")
for i in range(100):
    user_id = f"user_{random.randint(1, 10)}"
    event = {
        "user_id": user_id,
        "event_type": random.choice(["page_view", "click", "add_to_cart"]),
        "timestamp": int(time.time())
    }
    
    # We use user_id as the KEY so all events for a user go to the same partition
    # This guarantees ordered processing for that user!
    producer.produce(
        topic, 
        key=user_id.encode('utf-8'), 
        value=json.dumps(event).encode('utf-8'), 
        callback=delivery_report
    )
    
    # Poll handles delivery reports (callbacks)
    producer.poll(0)
    time.sleep(0.5)

# Wait for any outstanding messages to be delivered
producer.flush()

from confluent_kafka import Consumer, KafkaError
import json

# Consumer configuration
conf = {
    'bootstrap.servers': 'localhost:29092',
    'group.id': 'analytics_group',
    # auto.offset.reset determines what to do if there is no initial offset
    # 'earliest' means read from the very beginning of the topic
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['user_events'])

print("Starting analytics consumer...")
try:
    while True:
        msg = consumer.poll(timeout=1.0)
        
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event
                continue
            else:
                print(msg.error())
                break
                
        # Parse the message
        event = json.loads(msg.value().decode('utf-8'))
        print(f"Processed: User {event['user_id']} performed {event['event_type']}")
        
except KeyboardInterrupt:
    pass
finally:
    # Close down consumer to commit final offsets.
    consumer.close()

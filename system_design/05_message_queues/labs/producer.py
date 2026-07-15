import pika
import json
import time
import random
import uuid

def publish_orders():
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the queue (creates it if it doesn't exist)
    # durable=True means the queue will survive a RabbitMQ restart
    channel.queue_declare(queue='orders', durable=True)

    print("Producer started. Sending 10 orders...")
    
    for i in range(10):
        # Create a fake order
        order = {
            "order_id": str(uuid.uuid4()),
            "user_id": random.randint(1, 100),
            "amount": round(random.uniform(10.0, 500.0), 2),
            # Let's inject a "poison pill" (bad data) on the 7th order
            "is_valid": False if i == 7 else True
        }
        
        # Publish to the queue
        channel.basic_publish(
            exchange='', # Default exchange
            routing_key='orders', # The name of the queue
            body=json.dumps(order),
            # delivery_mode=2 makes the MESSAGE persistent on disk
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f" [x] Sent order {i}: {order['order_id']}")
        time.sleep(0.5)

    connection.close()

if __name__ == "__main__":
    try:
        # Requires: pip install pika
        publish_orders()
    except Exception as e:
        print("Error: Is RabbitMQ running via docker-compose?")

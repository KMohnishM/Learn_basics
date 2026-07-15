import pika
import json
import time

def process_order(ch, method, properties, body):
    order = json.loads(body)
    print(f" [x] Received order {order['order_id']}")
    
    # Simulate processing time
    time.sleep(1)
    
    # Check if the order is valid
    if not order.get("is_valid", True):
        print(f" [!] ERROR: Invalid order {order['order_id']}. Simulating crash.")
        # We reject the message and requeue it. 
        # This will cause an infinite loop (Poison Pill!) because the consumer will just read it and crash again.
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)
        return

    print(" [x] Successfully processed order.")
    # Acknowledge the message so RabbitMQ deletes it from the queue
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='orders', durable=True)

    # Prefetch count = 1 tells RabbitMQ not to give more than one message to a worker at a time.
    # Good for load balancing across multiple consumers.
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(queue='orders', on_message_callback=process_order)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()

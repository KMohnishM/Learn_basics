import pika
import json
import time

def process_order(ch, method, properties, body):
    order = json.loads(body)
    print(f" [x] Received order {order['order_id']}")
    
    time.sleep(1)
    
    if not order.get("is_valid", True):
        print(f" [!] ERROR: Invalid order. Moving to DLQ.")
        # requeue=False combined with the queue DLX config means: "Route this to the DLX"
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
        return

    print(" [x] Successfully processed order.")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # 1. Declare the Dead Letter Exchange (DLX)
    channel.exchange_declare(exchange='dlx_exchange', exchange_type='direct')
    
    # 2. Declare the Dead Letter Queue
    channel.queue_declare(queue='dead_letter_queue', durable=True)
    
    # 3. Bind the DLQ to the DLX
    channel.queue_bind(exchange='dlx_exchange', queue='dead_letter_queue', routing_key='dlx_key')

    # 4. Declare the main queue, configuring it to send dead letters to our DLX
    arguments = {
        'x-dead-letter-exchange': 'dlx_exchange',
        'x-dead-letter-routing-key': 'dlx_key'
    }
    # Note: If the 'orders' queue already exists from the lab without these arguments, 
    # RabbitMQ will throw an error. You must delete the queue in the Management UI first!
    channel.queue_declare(queue='orders_with_dlq', durable=True, arguments=arguments)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='orders_with_dlq', on_message_callback=process_order)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()

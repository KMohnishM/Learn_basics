# Exercise: Implement a Dead Letter Queue (DLQ)

If you ran the `producer.py` and `consumer.py` scripts in the lab, you noticed a massive problem.
The 7th order was a "poison pill" (bad data). 

The consumer crashed, rejected the message, and put it *back* on the queue (`requeue=True`). 
Then, the consumer immediately picked up the same bad message, crashed again, put it back again... creating an infinite loop. The 8th, 9th, and 10th orders were stuck behind it forever!

## Your Task

Fix this by implementing a **Dead Letter Queue (DLQ)**.

When a queue is configured with a DLQ, any message that is rejected with `requeue=False` is automatically moved to the DLQ instead of being deleted.

1. Write a new consumer script in `solution/dlq_consumer.py`.
2. Before declaring the `orders` queue, you must declare a new exchange (e.g., `dlx_exchange`) and a new queue (e.g., `dead_letter_queue`), and bind them together.
3. Modify the declaration of the main `orders` queue to include the `x-dead-letter-exchange` argument, pointing to your DLX.
4. Modify the `process_order` function: when it encounters an invalid order, it should reject it with `requeue=False`.

If you do this correctly, the bad message will be routed to the `dead_letter_queue`, and the consumer will successfully process orders 8, 9, and 10!

*Hint: Check the RabbitMQ documentation for `x-dead-letter-exchange`.*

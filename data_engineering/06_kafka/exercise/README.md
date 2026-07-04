# Exercise: Exactly-Once Semantics (Transactions)

By default, Kafka guarantees **At-Least-Once** delivery. If a producer sends a message, and the network drops the acknowledgment from the broker, the producer will retry and send the message again. This leads to duplicate messages in the topic.

For analytics, maybe a duplicate page view is fine. But for a banking app processing a $1000 transfer, a duplicate is catastrophic. You need **Exactly-Once** semantics.

## Your Task

Kafka 0.11 introduced the Transactional API to solve this.

Write a new producer in `solution/transactional_producer.py`. 
You must configure the `Producer` object with a `transactional.id`. 
Then, you must initialize transactions, begin a transaction, produce a message, and commit the transaction.

If you do this correctly, Kafka guarantees that even if the producer retries under the hood due to network failures, the message will only be written to the log exactly once!

*Hint: Look at the confluent-kafka-python documentation for `init_transactions()`, `begin_transaction()`, and `commit_transaction()`.*

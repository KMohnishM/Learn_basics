# Apache Kafka Curriculum

Welcome to the Apache Kafka learning path. This curriculum is designed to take you from fundamentals to advanced distributed systems concepts.

## Module Map

1. **01 Foundations**: Core architecture, Log-centric storage, Brokers, Topics, Partitions, ISRs, and KRaft vs Zookeeper.
2. **02 Producers**: RecordAccumulator, Serializers, Partitioners, Acknowledgements, Retries, Idempotence, compression.
3. **03 Consumers**: Consumer Groups, Offsets, Rebalancing, Fetch loops, Commit strategies.
4. **04 Kafka Connect**: Source and Sink connectors, Converters, Transforms, Distributed mode.
5. **05 Kafka Streams**: Topologies, KStream/KTable, State Stores, Exactly-once semantics.
6. **06 Operations & Tuning**: Monitoring, Security (SASL/SSL), Partition Reassignment, Tiered Storage.

## Study Path

Start with Foundations to understand the immutable log concept. Then move to Producers to understand how data gets into Kafka. Following that, study Consumers to see how data is read. Once the core clients are understood, move to the ecosystem (Connect and Streams), and finish with Operations.

## Docker Compose KRaft Setup

To run Kafka locally without Zookeeper, use KRaft mode. Create a `docker-compose.yml` file:

```yaml
version: '3'
services:
  kafka:
    image: confluentinc/cp-kafka:7.4.0
    hostname: kafka
    container_name: kafka
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: 'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT'
      KAFKA_ADVERTISED_LISTENERS: 'PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092'
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@kafka:29093'
      KAFKA_LISTENERS: 'PLAINTEXT://kafka:29092,CONTROLLER://kafka:29093,PLAINTEXT_HOST://0.0.0.0:9092'
      KAFKA_INTER_BROKER_LISTENER_NAME: 'PLAINTEXT'
      KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
      KAFKA_LOG_DIRS: '/tmp/kraft-combined-logs'
      CLUSTER_ID: 'MkU3OEVBNTcwNTJENDM2Qk'
```

Run it using:
```bash
docker-compose up -d
```

## Python Client Setup

We will use `confluent-kafka-python`, the official librdkafka wrapper.

```bash
pip install confluent-kafka
```

Example Producer:
```python
from confluent_kafka import Producer

conf = {'bootstrap.servers': 'localhost:9092'}
p = Producer(conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}]")

p.produce('my-topic', b'my_value', callback=delivery_report)
p.flush()
```

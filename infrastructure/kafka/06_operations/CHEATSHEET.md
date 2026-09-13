# Kafka Operations Cheatsheet

## Schema Registry Compatibility Matrix

| Mode | Meaning | Allowed Changes | Upgrade Order |
| :--- | :--- | :--- | :--- |
| **BACKWARD** | New consumer can read old data | Delete fields, add optional fields | Consumers, then Producers |
| **FORWARD** | Old consumer can read new data | Add fields, delete optional fields | Producers, then Consumers |
| **FULL** | Both Backward & Forward | Modify optional fields only | Any order |
| **NONE** | No validation | Any changes allowed | N/A |
| **_TRANSITIVE**| Compatible with ALL previous versions | Same as above, applied transitively | Same as above |

## CLI Command Reference

### Topic Management

**Create a Topic:**
```bash
kafka-topics.sh --bootstrap-server localhost:9092 --create --topic my-topic --partitions 3 --replication-factor 2
```

**Alter Partitions (Increase only):**
```bash
kafka-topics.sh --bootstrap-server localhost:9092 --alter --topic my-topic --partitions 5
```

**Alter Topic Configuration (e.g., Log Compaction):**
```bash
kafka-configs.sh --bootstrap-server localhost:9092 --alter --entity-type topics --entity-name my-topic --add-config cleanup.policy=compact
```

### Consumer Groups

**List Consumer Groups:**
```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
```

**Describe a Consumer Group (Check Lag):**
```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group my-consumer-group
```

**Reset Offsets (e.g., to earliest):**
```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group my-group --reset-offsets --to-earliest --execute --topic my-topic
```

### Cluster Operations

**Partition Reassignment (Generate Plan):**
```bash
kafka-reassign-partitions.sh --bootstrap-server localhost:9092 --topics-to-move-json-file topics.json --broker-list "1,2,3" --generate
```

**Partition Reassignment (Execute Plan):**
```bash
kafka-reassign-partitions.sh --bootstrap-server localhost:9092 --reassignment-json-file plan.json --execute
```

**Preferred Replica Election:**
```bash
kafka-leader-election.sh --bootstrap-server localhost:9092 --election-type PREFERRED --all-topic-partitions
```

### Security / ACLs

**Add ACL (Allow User Bob to Write):**
```bash
kafka-acls.sh --bootstrap-server localhost:9092 --add --allow-principal User:Bob --operation Write --topic sales-data
```

**List ACLs for a Topic:**
```bash
kafka-acls.sh --bootstrap-server localhost:9092 --list --topic sales-data
```

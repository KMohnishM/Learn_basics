# Module 3: Saga and Outbox Patterns

## 1. The Distributed Transaction Problem (2PC flaws)

In traditional monolithic applications, data consistency is typically maintained using standard local database transactions (ACID). However, in microservices architectures, each service manages its own database (Database-per-Service pattern). This distributed nature introduces significant challenges when a single business operation requires updating multiple databases across different services. 

Historically, the Two-Phase Commit (2PC) protocol was the standard solution for managing distributed transactions. 2PC uses a coordinator to manage the transaction across all participating databases. 
It consists of a Prepare Phase (where the coordinator asks participants to vote on committing) and a Commit Phase (where the final decision is executed).

### Flaws of 2PC in Microservices
1. Synchronous Blocking: 2PC locks resources across all participating databases during the prepare phase. These locks remain until the commit phase concludes. This severely limits throughput and scaling.
2. Single Point of Failure: The transaction coordinator becomes a critical bottleneck and failure point.
3. NoSQL Incompatibility: Many modern data stores (NoSQL databases, message brokers) do not support the XA transaction protocol required for 2PC.
4. CAP Theorem Limitations: 2PC prioritizes Consistency over Availability, which is often undesirable in highly available microservices environments.

## 2. Saga Pattern (Choreography vs Orchestration implementation code)

To address the shortcomings of 2PC, the Saga pattern is utilized. A saga is a sequence of local transactions. Each local transaction updates the database and publishes a message or event to trigger the next local transaction in the saga.

### Choreography-Based Saga
In choreography, there is no central orchestrator. Each service listens to events emitted by other services and decides if it needs to execute a local transaction.

#### Python Code Example (Choreography)

```python
# order_service.py
import pika
import json

def create_order(order_data):
    order_id = db.save_order(order_data, status="PENDING")
    
    event = {
        "event_type": "OrderCreated",
        "order_id": order_id,
        "customer_id": order_data["customer_id"],
        "amount": order_data["amount"]
    }
    publish_event("order_events", event)

def on_payment_processed(event):
    if event["event_type"] == "PaymentBilled":
        db.update_order_status(event["order_id"], "APPROVED")
    elif event["event_type"] == "PaymentFailed":
        db.update_order_status(event["order_id"], "REJECTED")

# payment_service.py
def on_order_created(event):
    try:
        process_payment(event["customer_id"], event["amount"])
        
        success_event = {
            "event_type": "PaymentBilled",
            "order_id": event["order_id"]
        }
        publish_event("payment_events", success_event)
    except Exception as e:
        failure_event = {
            "event_type": "PaymentFailed",
            "order_id": event["order_id"],
            "reason": str(e)
        }
        publish_event("payment_events", failure_event)
```

### Orchestration-Based Saga
In orchestration, a central coordinator (Saga Execution Coordinator) tells each participant what to do.

#### Python Code Example (Orchestration)

```python
# saga_orchestrator.py
class CreateOrderSaga:
    def __init__(self, order_id):
        self.order_id = order_id
        self.state = "STARTED"

    def execute(self):
        send_command("order_service", "CreateOrderCmd", {"order_id": self.order_id})
        self.state = "AWAITING_ORDER_CREATED"

    def handle_reply(self, reply):
        if self.state == "AWAITING_ORDER_CREATED":
            if reply["status"] == "SUCCESS":
                send_command("payment_service", "BillCustomerCmd", {"order_id": self.order_id})
                self.state = "AWAITING_PAYMENT"
            else:
                self.state = "FAILED"
        
        elif self.state == "AWAITING_PAYMENT":
            if reply["status"] == "SUCCESS":
                send_command("order_service", "ApproveOrderCmd", {"order_id": self.order_id})
                self.state = "COMPLETED"
            else:
                send_command("order_service", "RejectOrderCmd", {"order_id": self.order_id})
                self.state = "COMPENSATING"
```

## 3. Compensating Transactions (rules and examples)

If a step in a saga fails, the saga must execute compensating transactions to undo the effects of preceding steps.

### Rules for Compensating Transactions
1. Semantic Undo: Do not simply DELETE rows. Often, compensation involves business logic (e.g., crediting a previously debited account).
2. Idempotency: Compensating transactions must be idempotent, as they may be retried.
3. Guaranteed Success: Compensations generally should not fail for business reasons. Technical failures require indefinite retries.

### Example Scenario
Saga: Book Flight -> Book Hotel -> Rent Car
If Rent Car fails, the compensations are:
1. Cancel Hotel
2. Cancel Flight

#### Implementation Detail (SQL)

```sql
-- Forward Transaction
INSERT INTO hotel_bookings (booking_id, status, amount) VALUES ('b-123', 'CONFIRMED', 250.00);

-- Compensating Transaction
UPDATE hotel_bookings 
SET status = 'CANCELLED_COMPENSATED',
    refunded_amount = 250.00
WHERE booking_id = 'b-123' AND status = 'CONFIRMED';
```

## 4. Outbox Pattern — Solving Dual-Write

The dual-write problem happens when a service updates the database and publishes to a message broker. If one fails, the system is inconsistent.

The Outbox Pattern uses the local database transaction to atomicly update the business entities and insert an event record into a dedicated `outbox` table.

### Python Code Example (Outbox)

```python
def create_user_outbox(user_data):
    try:
        db.begin_transaction()
        
        user_id = db.execute("INSERT INTO users (name) VALUES (?)", (user_data["name"],)).lastrowid
        
        event_payload = json.dumps({"type": "UserCreated", "id": user_id})
        db.execute("INSERT INTO outbox (aggregate_id, payload) VALUES (?, ?)", (user_id, event_payload))
        
        db.commit() 
    except Exception:
        db.rollback()
```

### Outbox Relay Implementation Code (Python Polling)

```python
import time

def process_outbox():
    while True:
        try:
            db.begin_transaction()
            messages = db.execute("SELECT id, payload FROM outbox WHERE processed = FALSE FOR UPDATE SKIP LOCKED")
            
            for msg in messages:
                kafka_producer.send("events", msg["payload"])
                db.execute("UPDATE outbox SET processed = TRUE WHERE id = ?", (msg["id"],))
            
            db.commit()
        except Exception:
            db.rollback()
        
        time.sleep(1)
```

### Change Data Capture (CDC) with Debezium

A superior approach to polling is CDC using Debezium.

#### Debezium Connector Configuration (YAML)

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaConnector
metadata:
  name: outbox-connector
spec:
  class: io.debezium.connector.postgresql.PostgresConnector
  tasksMax: 1
  config:
    database.hostname: postgres-db
    database.port: 5432
    database.user: debezium
    database.password: dbz
    database.dbname: orderdb
    database.server.name: order-server
    plugin.name: pgoutput
    table.include.list: public.outbox
    transforms: outbox
    transforms.outbox.type: io.debezium.transforms.outbox.EventRouter
    transforms.outbox.route.topic.replacement: ${routedByValue}
    transforms.outbox.table.field.event.id: id
    transforms.outbox.table.field.event.key: aggregate_id
    transforms.outbox.table.field.event.type: event_type
    transforms.outbox.table.field.event.payload: payload
```

## 5. Saga State Machine (SQL schema)

Orchestrators need a persistent state machine to survive crashes.

### SQL Schema Definition

```sql
CREATE TABLE saga_instances (
    saga_id VARCHAR(255) PRIMARY KEY,
    saga_type VARCHAR(100) NOT NULL,
    current_state VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INT DEFAULT 1
);

CREATE TABLE saga_steps (
    step_id SERIAL PRIMARY KEY,
    saga_id VARCHAR(255) REFERENCES saga_instances(saga_id),
    step_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

## 6. Idempotent Saga Steps (Python SQL example)

Message delivery is typically "at least once". Saga participants must be idempotent.

```sql
CREATE TABLE processed_messages (
    message_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

```python
def process_payment_cmd(message_id, account_id, amount):
    try:
        db.begin_transaction()
        
        try:
            db.execute("INSERT INTO processed_messages (message_id) VALUES (?)", (message_id,))
        except IntegrityError:
            db.rollback()
            return {"status": "ALREADY_PROCESSED"}
            
        db.execute("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, account_id))
        db.commit()
        return {"status": "SUCCESS"}
    except Exception as e:
        db.rollback()
        raise e
```

## 7. Advanced Considerations for Distributed Transactions

### Tracing and Observability
When implementing sagas, distributed tracing is absolutely essential. A single business transaction may span multiple asynchronous steps across different services. OpenTelemetry should be used to inject the `saga_id` as a trace ID or correlation ID across all events and HTTP calls. This allows developers to visualize the entire saga lifecycle in tools like Jaeger or Zipkin. 
Without this, debugging a stalled saga or understanding the sequence of compensations becomes practically impossible.

### Securing the Inter-Service Communication
Since saga participants exchange commands and events, ensuring the integrity and authenticity of these messages is crucial. Implementing mutual TLS (mTLS) between services and the message broker (e.g., Kafka) ensures that only authorized services can trigger state changes. Additionally, the event payloads might contain sensitive PII, meaning encryption at rest and in transit must be enforced.

### Scalability of the Orchestrator
The Saga Execution Coordinator (SEC) can become a bottleneck if not designed carefully. To scale out, the SEC must be stateless in memory, relying entirely on the `saga_instances` database table for state. Optimistic locking (using the `version` column) prevents race conditions when multiple SEC instances attempt to process replies for the same saga concurrently.

### Handling Network Partitions
In a cloud environment, network partitions will occur. The saga pattern handles this gracefully through eventual consistency. If a service becomes isolated, the orchestrator will experience a timeout and can initiate compensations. Once the network recovers, messages buffered in the broker will be delivered, and the system will eventually converge to a consistent state.

## 8. Real-world Failure Mode Mitigations

### Dead Letter Queues (DLQ)
When a compensating transaction fails consistently (e.g., due to a persistent database issue on the participant's side), the message cannot simply be discarded. It must be routed to a Dead Letter Queue (DLQ). The operations team monitors the DLQ and manually intervenes to resolve the data inconsistency.

### Circuit Breakers
If a downstream service involved in a saga is experiencing an outage, continuously starting new sagas that rely on it will only compound the problem and fill up queues. The orchestrator should utilize circuit breakers (like Resilience4j). When the failure rate exceeds a threshold, the circuit breaker opens, and new sagas immediately fast-fail or enter a compensating state without attempting to call the degraded service.

### Database Connection Management
The outbox relay, especially if polling is used, can consume significant database connections. At scale, this leads to connection exhaustion. Using a connection pooler like PgBouncer for PostgreSQL ensures that the outbox polling mechanism and the application logic efficiently share a limited pool of backend database connections.

### Kafka Topic Compaction
For orchestration sagas, the state of the saga is often emitted as events to a Kafka topic. To prevent this topic from growing indefinitely, Kafka log compaction can be enabled using the `saga_id` as the message key. This ensures that Kafka only retains the latest state for each saga, optimizing storage and replay times for the SEC.

## 9. Testing Sagas Effectively

Testing distributed sagas requires a multi-layered approach:

### Unit Testing
The business logic within each local transaction must be unit tested. Furthermore, the orchestrator's state transitions must be rigorously tested using mock participants to verify that it correctly navigates success, failure, and timeout scenarios.

### Integration Testing
Integration tests should verify the interaction between the service and the database, ensuring that the local transaction and the outbox insertion truly happen atomically. Testcontainers can be used to spin up a temporary database instance for these tests.

### End-to-End (E2E) Testing
E2E tests must simulate the full saga lifecycle. This involves deploying all participating services, the message broker, and the orchestrator. Chaos engineering techniques, such as randomly terminating services or dropping network packets, should be introduced to verify that the saga pattern correctly handles failures and eventual consistency.

## 10. Deployment Strategies for Sagas

### Kubernetes Deployments
When deploying saga participants to Kubernetes, they must be configured with appropriate readiness and liveness probes. If a service loses connectivity to its local database, it should fail its readiness probe to stop receiving synchronous traffic, though it may still process async events from the broker once the database recovers.

### Versioning Saga Workflows
Saga workflows evolve over time. When an orchestrator's logic changes, in-flight sagas (running the old version) must complete successfully. This requires supporting multiple versions of the orchestrator simultaneously or designing the new orchestrator logic to be backward compatible with the state of existing `saga_instances`.

## 11. Extended Debezium Configuration Details

To run Debezium effectively for the Outbox pattern in a production environment, you need more than just the connector YAML. The PostgreSQL database must be configured correctly.

### PostgreSQL Configuration (`postgresql.conf`)

```ini
# Required for Debezium logical replication
wal_level = logical
max_wal_senders = 4
max_replication_slots = 4
```

This ensures that PostgreSQL writes enough information to the Write-Ahead Log (WAL) to reconstruct the exact row changes and streams them to Debezium.

## 12. Conclusion

The Saga and Outbox patterns are indispensable tools for building robust, scalable microservices architectures. They replace traditional distributed transactions (2PC) with a model that embraces eventual consistency and local isolation. While they introduce complexity—requiring careful consideration of orchestrator scaling, idempotency, compensations, and observability—they provide the fault tolerance and performance necessary for modern cloud-native applications. Mastering these patterns is a critical step in mastering microservices design.

### Section: Process Manager Pattern

```python
# Process Manager: stateful workflow coordinator, more powerful than a simple Saga
# Handles long-running business processes that may span hours/days
# Reacts to events AND can query state of other services

class OrderFulfillmentProcessManager:
    """
    Manages the full order fulfillment lifecycle:
    Order -> Payment -> Inventory pick -> Packaging -> Shipping -> Delivered
    May take hours (same-day delivery) to days (standard shipping)
    """

    STATE_TRANSITIONS = {
        'ORDER_RECEIVED':      ['PAYMENT_PENDING'],
        'PAYMENT_PENDING':     ['PAYMENT_CONFIRMED', 'PAYMENT_FAILED'],
        'PAYMENT_CONFIRMED':   ['PICKING_IN_PROGRESS'],
        'PICKING_IN_PROGRESS': ['PICKING_COMPLETE', 'PICKING_FAILED'],
        'PICKING_COMPLETE':    ['PACKAGING_IN_PROGRESS'],
        'PACKAGING_IN_PROGRESS': ['READY_FOR_SHIPMENT'],
        'READY_FOR_SHIPMENT':  ['SHIPPED'],
        'SHIPPED':             ['DELIVERED', 'DELIVERY_FAILED'],
        'DELIVERED':           [],  # terminal
        'PAYMENT_FAILED':      [],  # terminal
        'PICKING_FAILED':      ['REFUND_INITIATED'],
        'REFUND_INITIATED':    ['REFUNDED'],  # terminal
    }

    def __init__(self, process_id: str, order_id: str):
        self.process_id = process_id
        self.order_id = order_id
        self.state = 'ORDER_RECEIVED'
        self.history = []

    def transition(self, new_state: str, context: dict = None):
        allowed = self.STATE_TRANSITIONS.get(self.state, [])
        if new_state not in allowed:
            raise InvalidTransitionError(
                f'Cannot transition from {self.state} to {new_state}. Allowed: {allowed}'
            )
        self.history.append({
            'from': self.state, 'to': new_state,
            'timestamp': datetime.utcnow().isoformat(),
            'context': context
        })
        self.state = new_state

    async def on_event(self, event: dict):
        event_type = event['event_type']

        if event_type == 'PaymentProcessed' and self.state == 'PAYMENT_PENDING':
            self.transition('PAYMENT_CONFIRMED')
            await self.initiate_picking()

        elif event_type == 'PaymentFailed' and self.state == 'PAYMENT_PENDING':
            self.transition('PAYMENT_FAILED', {'reason': event['failure_reason']})
            await self.notify_customer_payment_failed()

        elif event_type == 'ItemsPicked' and self.state == 'PICKING_IN_PROGRESS':
            self.transition('PICKING_COMPLETE')
            await self.initiate_packaging()

        elif event_type == 'ShipmentCreated' and self.state == 'READY_FOR_SHIPMENT':
            self.transition('SHIPPED', {'tracking_id': event['tracking_id']})
            await self.notify_customer_shipped(event['tracking_id'])

        await self.save()

    async def handle_timeout(self):
        # Scheduled job checks for stuck processes
        if self.state == 'PAYMENT_PENDING' and self.age_minutes() > 30:
            # Payment timed out -- cancel order
            self.transition('PAYMENT_FAILED', {'reason': 'TIMEOUT'})
            await self.release_inventory_hold()
            await self.save()

# Persistence: process manager state stored in DB
# CREATE TABLE process_manager_state (
#   process_id    UUID PRIMARY KEY,
#   order_id      UUID NOT NULL UNIQUE,
#   current_state VARCHAR(50) NOT NULL,
#   history       JSONB NOT NULL DEFAULT '[]',
#   created_at    TIMESTAMPTZ DEFAULT NOW(),
#   updated_at    TIMESTAMPTZ DEFAULT NOW()
# );
```

### Section: Outbox Pattern with Polling Publisher vs CDC

Comparison of outbox relay implementations:

```python
# Implementation 1: Polling Publisher
# Simple, no extra infrastructure, but adds DB read load

async def polling_outbox_relay(
    poll_interval: float = 0.5,
    batch_size: int = 100
):
    while True:
        async with db.transaction():
            # Lock rows to prevent concurrent relay instances from double-publishing
            rows = await db.fetch(
                '''
                SELECT id, event_type, payload, aggregate_id
                FROM outbox
                WHERE status = 'PENDING'
                ORDER BY created_at
                LIMIT $1
                FOR UPDATE SKIP LOCKED
                ''',
                batch_size
            )

            for row in rows:
                try:
                    topic = row['event_type'].lower().replace('_', '-')
                    await kafka_producer.send(
                        topic=topic,
                        key=row['aggregate_id'].encode(),
                        value=row['payload'].encode()
                    )
                    await db.execute(
                        'UPDATE outbox SET status = $1, published_at = NOW() WHERE id = $2',
                        'PUBLISHED', row['id']
                    )
                except KafkaError as e:
                    await db.execute(
                        'UPDATE outbox SET retry_count = retry_count + 1, last_error = $1 WHERE id = $2',
                        str(e), row['id']
                    )

        await asyncio.sleep(poll_interval)

# Implementation 2: Debezium CDC (Change Data Capture)
# Reads PostgreSQL Write-Ahead Log directly
# Zero DB load; near real-time; no application code change

# Debezium PostgreSQL connector configuration:
debezium_config = {
    'connector.class': 'io.debezium.connector.postgresql.PostgresConnector',
    'database.hostname': 'postgres',
    'database.port': '5432',
    'database.user': 'debezium',
    'database.password': 'dbz_password',
    'database.dbname': 'orders_db',
    'database.server.name': 'order-service',
    'table.include.list': 'public.outbox',  # only watch outbox table
    'plugin.name': 'pgoutput',
    'publication.name': 'dbz_publication',
    # Outbox Event Router SMT (Single Message Transform)
    'transforms': 'outbox',
    'transforms.outbox.type': 'io.debezium.transforms.outbox.EventRouter',
    'transforms.outbox.table.field.event.id': 'id',
    'transforms.outbox.table.field.event.key': 'aggregate_id',
    'transforms.outbox.table.field.event.type': 'event_type',
    'transforms.outbox.table.field.event.payload': 'payload',
    'transforms.outbox.route.by.field': 'event_type',
    'transforms.outbox.route.topic.regex': '.*',
}

# PostgreSQL setup for Debezium:
# ALTER SYSTEM SET wal_level = logical;  -- required for CDC
# CREATE PUBLICATION dbz_publication FOR TABLE outbox;
# CREATE USER debezium REPLICATION LOGIN PASSWORD 'dbz_password';
# GRANT SELECT ON TABLE outbox TO debezium;
```

### Section: Testing Sagas

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

class TestOrderSagaOrchestrator:

    @pytest.fixture
    def orchestrator(self):
        return OrderSagaOrchestrator(
            order_id='ord_test_123',
            order={'items': [{'product_id': 'SKU-1', 'quantity': 2}], 'total': 49.99}
        )

    @pytest.mark.asyncio
    async def test_successful_saga(self, orchestrator):
        # Mock all downstream service calls
        orchestrator.reserve_inventory = AsyncMock(return_value={'reservation_id': 'res_1'})
        orchestrator.process_payment = AsyncMock(return_value={'payment_id': 'pay_1', 'status': 'SUCCESS'})
        orchestrator.confirm_order = AsyncMock()

        await orchestrator.execute()

        orchestrator.reserve_inventory.assert_called_once()
        orchestrator.process_payment.assert_called_once()
        orchestrator.confirm_order.assert_called_once()
        assert orchestrator.state == 'COMPLETED'

    @pytest.mark.asyncio
    async def test_payment_failure_triggers_compensation(self, orchestrator):
        orchestrator.reserve_inventory = AsyncMock(return_value={'reservation_id': 'res_1'})
        orchestrator.process_payment = AsyncMock(side_effect=PaymentError('CARD_DECLINED'))
        orchestrator.release_inventory_reservation = AsyncMock()
        orchestrator.cancel_order = AsyncMock()

        await orchestrator.execute()

        # Compensation must have been called
        orchestrator.release_inventory_reservation.assert_called_once()
        orchestrator.cancel_order.assert_called_once_with('PAYMENT_FAILED')
        assert orchestrator.state == 'CANCELLED'

    @pytest.mark.asyncio
    async def test_inventory_failure_no_compensation_needed(self, orchestrator):
        orchestrator.reserve_inventory = AsyncMock(side_effect=InventoryError(['SKU-1']))
        orchestrator.process_payment = AsyncMock()  # should never be called
        orchestrator.cancel_order = AsyncMock()

        await orchestrator.execute()

        orchestrator.process_payment.assert_not_called()  # no payment attempted
        orchestrator.cancel_order.assert_called_once_with('INSUFFICIENT_STOCK')

    @pytest.mark.asyncio
    async def test_saga_is_idempotent(self, orchestrator):
        # Simulate: payment was charged but response was lost (network failure)
        # On retry, payment should detect duplicate and return cached result
        payment_call_count = 0

        async def idempotent_payment():
            nonlocal payment_call_count
            payment_call_count += 1
            if payment_call_count == 1:
                raise TimeoutError('Network timeout')  # first call times out
            return {'payment_id': 'pay_1', 'status': 'SUCCESS'}  # retry succeeds

        orchestrator.reserve_inventory = AsyncMock(return_value={'reservation_id': 'res_1'})
        orchestrator.process_payment = idempotent_payment
        orchestrator.confirm_order = AsyncMock()

        # First attempt: payment times out
        with pytest.raises(TimeoutError):
            await orchestrator.execute()

        # Retry: should succeed (payment idempotency key prevents double charge)
        await orchestrator.execute()
        assert orchestrator.state == 'COMPLETED'
        assert payment_call_count == 2  # called twice but charged once
```

### Section: Monitoring Saga Health

```sql
-- Dashboard queries for saga health

-- Sagas currently in flight (by state)
SELECT current_state, COUNT(*) as count,
       AVG(EXTRACT(EPOCH FROM (NOW() - started_at)) / 60) as avg_age_minutes
FROM order_sagas
WHERE current_state NOT IN ('COMPLETED', 'CANCELLED')
GROUP BY current_state
ORDER BY count DESC;

-- Stuck sagas (in same state for > 30 minutes)
SELECT saga_id, order_id, current_state,
       EXTRACT(EPOCH FROM (NOW() - updated_at)) / 60 AS minutes_stuck
FROM order_sagas
WHERE current_state NOT IN ('COMPLETED', 'CANCELLED')
  AND updated_at < NOW() - INTERVAL '30 minutes'
ORDER BY minutes_stuck DESC;

-- Saga completion rate by outcome (last 24h)
SELECT
  CASE WHEN current_state = 'COMPLETED' THEN 'success'
       WHEN current_state = 'CANCELLED' THEN 'cancelled'
       ELSE 'in_flight'
  END AS outcome,
  COUNT(*) as count,
  round(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as pct
FROM order_sagas
WHERE started_at > NOW() - INTERVAL '24 hours'
GROUP BY 1;

-- Outbox relay lag (how far behind is publishing?)
SELECT
  COUNT(*) FILTER (WHERE status = 'PENDING') AS pending_events,
  MAX(EXTRACT(EPOCH FROM (NOW() - created_at))) FILTER (WHERE status = 'PENDING') AS max_lag_seconds,
  COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_events
FROM outbox;
-- Alert if max_lag_seconds > 30 or failed_events > 0
```

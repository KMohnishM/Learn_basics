# Saga and Outbox QnA

## 1. Why is Two-Phase Commit (2PC) rarely used in microservices? What are its specific failure modes and performance characteristics that make it unsuitable for high-throughput distributed systems?
Two-Phase Commit (2PC) is a distributed transaction protocol that ensures strong consistency across multiple databases. It operates in two phases: a voting phase (asking all databases if they can commit) and a commit phase (instructing all to commit). It is rarely used in microservices because it fundamentally violates the principles of loose coupling and independent scalability.
Its performance characteristics are terrible for high-throughput systems. 2PC uses synchronous, blocking locks. While the transaction coordinator is waiting for the slowest database to acknowledge the voting phase, resources in all participating databases remain locked, preventing concurrent updates. This severely bottlenecks system throughput.
Furthermore, its failure modes are brittle. 2PC introduces a single point of failure (the transaction coordinator). If the coordinator crashes between the voting and commit phases, participating databases are left in a blocking "in-doubt" state, holding locks indefinitely until human intervention occurs. In a cloud-native microservices environment where network partitions and node failures are common, this lack of partition tolerance (CAP theorem) makes 2PC effectively unusable.

## 2. What is the Saga pattern? What is the fundamental difference between a compensating transaction in a saga and a database rollback? Give examples of compensatable and non-compensatable operations.
The Saga pattern manages distributed transactions across multiple microservices without using distributed locks. It breaks a large transaction into a sequence of local database transactions. Each local transaction updates data within a single service and publishes an event or message to trigger the next step.
The fundamental difference is that a database rollback utilizes the database engine's undo log to revert uncommitted changes, making it appear as if the transaction never happened. A compensating transaction in a Saga is a new, explicitly coded business operation designed to semantically reverse the effects of a previously committed local transaction. The original action was committed and visible to the system; the compensation is a counter-action.
Examples of compensatable operations: Reserving inventory (compensation: releasing inventory), charging a credit card (compensation: issuing a refund), allocating loyalty points (compensation: removing the points).
Examples of non-compensatable operations (Pivot or Retryable transactions): Sending a physical email to a customer (you cannot un-send an email; you can only send an apology), firing a physical rocket. These must be placed at the very end of the saga sequence.

## 3. Explain Choreography-based Saga. Walk through the complete success path and the payment failure path for an e-commerce order (inventory reserve -> payment -> confirm). What makes debugging choreography hard?
In a Choreography-based Saga, there is no central orchestrator. Services communicate by publishing and subscribing to domain events. Each service acts independently, listening for specific events and reacting by executing local logic and emitting new events.
Success Path:
1. Order Service creates a pending order and publishes `OrderCreated`.
2. Inventory Service listens, reserves items, and publishes `InventoryReserved`.
3. Payment Service listens, charges the card, and publishes `PaymentSucceeded`.
4. Order Service listens, updates status to "Confirmed", and publishes `OrderConfirmed`.
Failure Path (Payment fails):
1. Order Service publishes `OrderCreated`.
2. Inventory Service publishes `InventoryReserved`.
3. Payment Service attempts charge, fails, and publishes `PaymentFailed`.
4. Inventory Service listens to `PaymentFailed`, executes a compensating transaction to release the stock.
5. Order Service listens to `PaymentFailed`, updates status to "Cancelled".
Debugging choreography is exceptionally hard because the business process flow is implicit, scattered across the codebase of multiple services. There is no single place to look to understand the saga's current state. If a saga gets stuck, you must trace logs across multiple services to figure out which event was lost or which service failed to react.

## 4. Explain Orchestration-based Saga. Show a Python orchestrator that handles inventory + payment + order confirmation, including compensation on payment failure. What are the trade-offs vs choreography?
Orchestration-based Saga uses a central controller (the Orchestrator) to explicitly manage the workflow. The orchestrator tells the participant services what local transactions to execute via command messages, waits for responses, and decides the next step or triggers compensations if errors occur.
```python
class OrderOrchestrator:
    def __init__(self, message_bus):
        self.bus = message_bus

    def execute_saga(self, order_id):
        try:
            # 1. Command Inventory
            self.bus.send_sync("InventoryService", {"cmd": "Reserve", "id": order_id})
            
            # 2. Command Payment
            try:
                self.bus.send_sync("PaymentService", {"cmd": "Charge", "id": order_id})
            except PaymentFailedException:
                # Trigger Compensation explicitly
                self.bus.send_sync("InventoryService", {"cmd": "Release", "id": order_id})
                self.bus.send_sync("OrderService", {"cmd": "RejectOrder", "id": order_id})
                return "Failed"
                
            # 3. Confirm Order
            self.bus.send_sync("OrderService", {"cmd": "ConfirmOrder", "id": order_id})
            return "Success"
            
        except Exception as e:
            # Handle generic timeouts/failures
            pass
```
Trade-offs: Orchestration is much easier to understand, test, and debug because the workflow logic is centralized. However, it risks introducing tight coupling if the orchestrator takes on too much business logic (becoming a "god service") rather than just routing workflow commands. Choreography is more decoupled but harder to manage at scale.

## 5. What is the Outbox pattern? Why is dual-writing to a database and a Kafka topic not atomic? Show the exact failure scenario it solves (crash between DB write and Kafka publish).
The Outbox pattern solves the problem of reliably publishing messages to a broker (like Kafka) immediately after a local database transaction commits. 
Dual-writing means executing `db.commit()` and then immediately calling `kafka.publish()`. This is not atomic because it spans two different distributed systems without a 2PC coordinator.
The exact failure scenario it solves:
1. Application updates the `Orders` table in PostgreSQL.
2. Application calls `db.commit()`. The order is saved.
3. *Application crashes due to OOM or network failure.*
4. `kafka.publish('OrderCreated')` is never called.
Now the system is in an inconsistent state: the database reflects an order, but downstream services (Inventory, Payment) were never notified. 
The Outbox pattern solves this by writing the domain event into a specialized `outbox` table within the same database schema as part of the SAME local transaction. If the transaction commits, both the order data and the event are guaranteed to be saved atomically. A separate background process then safely reads the `outbox` table and publishes to Kafka.

## 6. What is Change Data Capture (CDC) with Debezium? How does it read the PostgreSQL Write-Ahead Log? Show the Debezium connector configuration for an outbox table. Why is it better than polling?
Change Data Capture (CDC) is a technology that monitors and captures changes in a database so they can be propagated to other systems. Debezium is an open-source distributed platform for CDC built on Apache Kafka Connect.
Instead of querying the database tables with SQL, Debezium connects directly to the database's internal replication mechanisms. For PostgreSQL, it reads the Write-Ahead Log (WAL) via the `pgoutput` logical decoding plugin. As soon as PostgreSQL commits a transaction to disk, Debezium reads the binary log entry and converts it into a Kafka message in real-time.
```json
{
  "name": "outbox-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.server.name": "ecommerce_db",
    "table.include.list": "public.outbox",
    "transforms": "outbox",
    "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
    "transforms.outbox.table.field.event.id": "id",
    "transforms.outbox.table.field.event.type": "aggregate_type",
    "transforms.outbox.table.field.event.payload": "payload"
  }
}
```
CDC is vastly superior to polling (e.g., `SELECT * FROM outbox WHERE sent = false`) because polling causes continuous CPU/I/O load on the database even when idle, introduces latency (the polling interval), and can miss updates if rows are modified between polls. CDC is event-driven, low-latency, and has virtually zero impact on database performance.

## 7. What are compensating transactions? Give a table of operations and their compensating transactions for an e-commerce order saga. Which operations cannot be compensated?
Compensating transactions are specific, application-level actions designed to undo the effects of a previously committed local transaction within a Saga. Because microservices cannot rely on database rollbacks across network boundaries, developers must write code to semantically reverse state.
| Service | Original Operation | Compensating Transaction |
| :--- | :--- | :--- |
| Inventory | `reserve_stock(SKU, qty)` | `release_stock(SKU, qty)` |
| Payment | `authorize_card(amount)` | `void_authorization(amount)` |
| Payment | `capture_funds(amount)` | `issue_refund(amount)` |
| Loyalty | `add_points(user, points)` | `deduct_points(user, points)` |

Operations that cannot be compensated are those that interact with the physical world or external, immutable systems. For example:
- Sending an SMS or Email. You cannot retract it from the user's phone.
- Dispensing cash from an ATM.
- Shipping a physical box from a warehouse (once it's on the truck).
These non-compensatable operations are termed "Pivot Transactions" and must be placed at the very end of the saga sequence. If everything before the pivot succeeds, the saga will guarantee the pivot and subsequent steps execute.

## 8. How do you make saga steps idempotent? Show a Python inventory reservation function that is safe to retry on network failure, using database constraints to prevent duplicate reservations.
Idempotency is crucial in sagas because message brokers guarantee at-least-once delivery, and network timeouts often trigger retries. A saga step must be safe to execute multiple times without causing unintended side effects (like double-reserving inventory).
The safest way to implement idempotency is using unique constraints at the database level.
```python
from sqlalchemy.exc import IntegrityError

def reserve_inventory(session, order_id, sku, quantity):
    try:
        # Create an idempotency record. The database has a UNIQUE constraint on order_id.
        reservation = InventoryReservation(order_id=order_id, sku=sku, qty=quantity)
        session.add(reservation)
        
        # Perform the actual business logic
        product = session.query(Product).filter_by(sku=sku).one()
        if product.stock < quantity:
            raise InsufficientStockException()
        product.stock -= quantity
        
        session.commit()
        return "Reserved"
        
    except IntegrityError:
        # The unique constraint on order_id was violated. 
        # This means we ALREADY processed this exact reservation request successfully.
        session.rollback()
        return "Already Reserved (Idempotent Success)"
```

## 9. What is a saga state machine? Show the SQL schema for persisting saga state and the valid state transitions for an order saga. Why is this necessary for orchestration-based sagas?
A saga state machine is the internal mechanism used by a Saga Orchestrator to track the progress of a distributed workflow. Because sagas run asynchronously over long periods, the orchestrator must persist the current state to a database. If the orchestrator service crashes, it must be able to reboot, read the state, and resume the saga where it left off.
```sql
CREATE TABLE order_saga_state (
    saga_id UUID PRIMARY KEY,
    order_id UUID NOT NULL,
    current_state VARCHAR(50) NOT NULL,
    payload JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Valid states: PENDING, INVENTORY_RESERVED, PAYMENT_PROCESSED, COMPLETED,
-- COMPENSATING_INVENTORY, ABORTED
```
Valid state transitions:
- `PENDING` -> (success) -> `INVENTORY_RESERVED`
- `INVENTORY_RESERVED` -> (success) -> `PAYMENT_PROCESSED` -> `COMPLETED`
- `INVENTORY_RESERVED` -> (failure) -> `COMPENSATING_INVENTORY` -> `ABORTED`
This is strictly necessary for orchestration-based sagas to guarantee durability. Without persistent state, an in-memory orchestrator crash would result in orphaned, half-completed transactions scattered across microservices with no way to trigger compensation or resumption.

## 10. What is the Process Manager pattern and how does it extend the Saga pattern? Give the complete state machine for an order fulfillment process that spans hours (payment -> picking -> packaging -> shipping -> delivered).
While a Saga pattern typically focuses on maintaining data consistency across a relatively fast, linear sequence of technical transactions, a Process Manager (or Routing Slip) extends this concept to handle complex, long-running business workflows that involve human interaction, complex branching logic, and timeouts. A process manager doesn't just react to technical failures; it actively drives the business process forward over hours or days.
State Machine for Fulfillment (spans days):
1. `AWAITING_PAYMENT`: Enters upon order creation.
2. `READY_FOR_PICKING`: Triggered when payment clears. Wait for warehouse worker.
3. `PICKING_IN_PROGRESS`: Triggered when a worker scans a barcode.
4. `READY_FOR_PACKAGING`: Items gathered.
5. `SHIPPED`: Tracking number generated.
6. `DELIVERED`: Triggered via webhook from external carrier (FedEx).
If a package remains in `READY_FOR_PICKING` for > 24 hours, the Process Manager actively emits an `EscalateToManager` event. It manages time-based transitions, unlike a simple Saga which primarily handles immediate success/compensation paths.

## 11. What is the semantic lock pattern in sagas? What race condition does it prevent when two concurrent sagas try to modify the same aggregate?
Because sagas use local transactions instead of distributed locks, they expose intermediate states to other processes, violating the Isolation property of ACID (resulting in ACD). 
The Semantic Lock pattern prevents race conditions by adding an application-level flag to an aggregate to indicate that it is currently involved in an ongoing saga, preventing other sagas from interfering.
Consider a user with a $100 balance. Saga A starts to buy a $100 item. It locally deducts $100 (balance=0) and moves to the shipping step. Before Saga A finishes, Saga B attempts to buy a $50 item. Seeing balance=0, Saga B rejects. But what if Saga A's shipping step fails and it compensates, refunding the $100? Saga B was incorrectly rejected based on dirty data.
To fix this using a semantic lock, Saga A doesn't just deduct the money; it changes the account status from `AVAILABLE` to `LOCKED_PENDING_TX`. If Saga B tries to access the account, it sees the `LOCKED` status and must either wait or reject the request explicitly, preventing the system from acting on an uncommitted intermediate state.

## 12. How do you handle saga timeouts? If the Payment Service does not respond within 30 seconds, what should the orchestrator do? Show the timeout handling code.
In asynchronous microservices, a lack of response could mean the downstream service crashed, the network dropped the message, or it's just very slow. A Saga Orchestrator must employ timeouts to ensure sagas do not hang indefinitely.
If the Payment Service does not respond within 30 seconds, the orchestrator should assume failure and initiate the compensation sequence (e.g., releasing inventory). It must also account for the fact that the delayed payment might eventually succeed (a race condition).
```python
import time

class SagaOrchestrator:
    def wait_for_payment(self, saga_id):
        timeout = time.time() + 30.0
        while time.time() < timeout:
            status = self.db.get_saga_status(saga_id)
            if status == 'PAYMENT_SUCCESS':
                return self.proceed_to_shipping(saga_id)
            elif status == 'PAYMENT_FAILED':
                return self.trigger_compensation(saga_id)
            time.sleep(1) # Poll for async completion
            
        # Timeout occurred
        self.db.update_status(saga_id, 'TIMEOUT_COMPENSATING')
        self.trigger_compensation(saga_id)
        
        # Crucial: Send an explicit command to the Payment Service to cancel
        # any in-flight processing for this saga to prevent late-arriving success.
        self.message_bus.send("PaymentService", {"cmd": "CancelIfPending", "saga_id": saga_id})
```

## 13. How do you test a saga? Show pytest tests for: successful flow, payment failure with compensation, inventory failure with no compensation needed, and idempotent retry.
Testing orchestration-based sagas involves mocking the downstream service responses and verifying the orchestrator executes the correct sequence of state transitions and outgoing commands.
```python
import pytest
from unittest.mock import Mock

def test_saga_success_flow(orchestrator, mock_bus):
    mock_bus.simulate_response("InventoryService", "Success")
    mock_bus.simulate_response("PaymentService", "Success")
    orchestrator.execute(order_id="123")
    assert mock_bus.sent_commands == ["ReserveInventory", "ProcessPayment", "ConfirmOrder"]

def test_saga_payment_failure_with_compensation(orchestrator, mock_bus):
    mock_bus.simulate_response("InventoryService", "Success")
    mock_bus.simulate_error("PaymentService", "InsufficientFunds")
    orchestrator.execute(order_id="123")
    assert mock_bus.sent_commands == ["ReserveInventory", "ProcessPayment", "ReleaseInventory", "CancelOrder"]

def test_saga_inventory_failure_no_compensation(orchestrator, mock_bus):
    mock_bus.simulate_error("InventoryService", "OutOfStock")
    # Payment should not even be called
    orchestrator.execute(order_id="123")
    assert mock_bus.sent_commands == ["ReserveInventory", "CancelOrder"]

def test_saga_idempotent_retry(orchestrator, mock_bus):
    # Simulate a network timeout on first try, success on second
    mock_bus.simulate_timeout("InventoryService") 
    mock_bus.simulate_response("InventoryService", "Success")
    mock_bus.simulate_response("PaymentService", "Success")
    orchestrator.execute(order_id="123")
    # Ensure ReserveInventory is sent twice, but saga still completes
    assert mock_bus.sent_commands == ["ReserveInventory", "ReserveInventory", "ProcessPayment", "ConfirmOrder"]
```

## 14. What monitoring queries do you run on saga state? Show SQL queries for: sagas by state, stuck sagas (in same state > 30 minutes), saga completion rate, and outbox relay lag.
Monitoring persistent saga state is essential for operating a distributed system. Sagas that hang or fail silently result in poor customer experience and data inconsistency.
```sql
-- 1. Sagas by current state (Dashboard overview)
SELECT current_state, COUNT(*) 
FROM order_saga_state 
GROUP BY current_state;

-- 2. Stuck sagas (Alerting rule: requires human intervention)
SELECT saga_id, order_id, current_state, updated_at
FROM order_saga_state
WHERE current_state NOT IN ('COMPLETED', 'ABORTED') 
  AND updated_at < NOW() - INTERVAL '30 minutes';

-- 3. Saga completion rate (Success vs Compensation over the last hour)
SELECT 
    SUM(CASE WHEN current_state = 'COMPLETED' THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN current_state = 'ABORTED' THEN 1 ELSE 0 END) AS compensation_count
FROM order_saga_state
WHERE updated_at > NOW() - INTERVAL '1 hour';

-- 4. Outbox relay lag (Detect if CDC/relay process is down)
SELECT COUNT(*) AS pending_messages
FROM outbox 
WHERE processed = false 
  AND created_at < NOW() - INTERVAL '1 minute';
```

## 15. What is the difference between an outbox table polling relay and a Debezium CDC relay? Compare on: operational complexity, latency, database load, ordering guarantees, and failure recovery.
Both patterns solve dual-write issues, but their underlying mechanisms differ vastly.
- Polling Relay: A background thread runs `SELECT * FROM outbox WHERE sent = false`, publishes to Kafka, and then updates the row to `sent = true`.
- Debezium CDC Relay: A Kafka Connect process tails the database's binary transaction log (WAL), converting log entries directly into Kafka messages.
Comparison:
1. Operational Complexity: Polling is simpler to write initially (just a cron job). Debezium is highly complex to operate, requiring managing Kafka Connect clusters and understanding database logical decoding.
2. Latency: Polling inherently introduces latency equal to the polling interval (e.g., 5 seconds). Debezium is near real-time (sub-millisecond) as it acts on the stream.
3. Database Load: Polling causes constant I/O and CPU load on the database via repeated SELECT/UPDATE queries. Debezium has near-zero impact as it reads the existing transaction log.
4. Ordering Guarantees: Polling can struggle with strict ordering if multiple worker threads poll concurrently, requiring complex locking. Debezium guarantees strict global ordering exactly as it occurred in the database transaction log.
5. Failure Recovery: If a polling process crashes, you rely on the `sent=false` flag. If Debezium crashes, it simply resumes reading from its last recorded offset in the WAL, making it highly robust.

# Module 1: Microservices Decomposition Patterns

## 1. Monolith vs Microservices — The Real Trade-offs

When designing software systems, the architectural choice between a monolith and a microservices architecture is one of the most consequential decisions an engineering team will make. This decision impacts not only the technical implementation but also the organizational structure, deployment pipelines, and scaling strategies.

### The Monolithic Architecture
A monolithic architecture is a unified model where all business logic, user interfaces, data access layers, and background jobs are packaged and deployed as a single unit. In Java, this might be a single WAR file; in Ruby on Rails or Django, it is a single application directory structure.

#### Advantages of the Monolith
1. Simplicity in Development: Initially, it is much easier to build, test, and deploy a single application. Developers can run the entire application on their local machines without complex orchestration.
2. Performance: In-memory function calls are orders of magnitude faster than network calls. A monolith does not suffer from network latency between components.
3. Transaction Management: Maintaining data consistency is straightforward. A single database transaction can span multiple domain entities, ensuring ACID properties.
4. Simplified Testing: End-to-end testing is simpler when the system is a single cohesive unit.

#### Disadvantages of the Monolith
1. Scaling Bottlenecks: A monolith scales as a single unit. If the reporting module requires more memory, the entire application must be scaled, leading to wasted resources.
2. Cognitive Load: As the codebase grows, it becomes increasingly difficult for any single developer to understand the entire system.
3. Deployment Risk: A single bug in a minor feature can crash the entire application. Deployments become high-risk events, often requiring downtime.
4. Technology Lock-in: Upgrading frameworks or languages becomes a massive undertaking. The entire codebase must be migrated simultaneously.

### The Microservices Architecture
Microservices architecture decomposes the application into a suite of small, independently deployable services, organized around business capabilities.

#### Advantages of Microservices
1. Independent Scalability: Services can be scaled independently based on their specific resource requirements.
2. Fault Isolation: A failure in the recommendation service does not bring down the checkout service.
3. Technology Diversity: Different services can be written in different languages or use different databases (Polyglot Persistence).
4. Organizational Alignment: Teams can take ownership of specific services, aligning with Conway's Law.

#### Disadvantages of Microservices
1. Distributed System Complexity: Network latency, partial failures, and distributed tracing introduce immense complexity.
2. Data Consistency: Without distributed transactions (which are discouraged), maintaining data consistency requires complex patterns like Sagas.
3. Operational Overhead: Managing dozens or hundreds of services requires mature DevOps, CI/CD, and monitoring infrastructure.

---

## 2. Domain-Driven Design (DDD) Fundamentals

Domain-Driven Design (DDD), introduced by Eric Evans, is a software development philosophy that aligns the software architecture with the business domain. It is the most effective methodology for determining microservice boundaries.

### The Core Concepts of DDD

#### 1. Domains and Subdomains
A domain is the sphere of knowledge and activity around which the application logic revolves. For an e-commerce company, the domain is retail.
Because the domain is too large to comprehend at once, it is broken down into subdomains:
- Core Subdomain: The primary differentiator for the business (e.g., the recommendation engine).
- Supporting Subdomain: Necessary for the business but not a competitive advantage (e.g., product catalog).
- Generic Subdomain: Standard business functions that could be bought off the shelf (e.g., invoicing, identity management).

#### 2. Bounded Context
A Bounded Context is a linguistic and conceptual boundary within which a specific domain model applies. The same term can mean different things in different contexts.
For example, a 'Product':
- In the Sales Context: It is an item with a price, title, and description.
- In the Inventory Context: It is a stock-keeping unit (SKU) with a physical location, weight, and quantity.
- In the Shipping Context: It is a package with dimensions and weight.
By defining bounded contexts, we prevent the creation of giant, confusing "god classes" that try to satisfy all requirements simultaneously.

#### 3. Ubiquitous Language
Within a Bounded Context, the development team and domain experts must agree on a Ubiquitous Language—a shared vocabulary used consistently in conversations, documentation, and code. If the business calls it a "Shopper," the code should use `Shopper`, not `User` or `Customer`.

#### 4. Aggregates and Aggregate Roots
An Aggregate is a cluster of domain objects that can be treated as a single unit for the purpose of data changes. Every aggregate has a root and a boundary.
- Aggregate Root: The only object through which the aggregate can be accessed or modified.
- Transactional Boundary: A single database transaction should only modify one aggregate.

```python
# Example of an Aggregate Root in Python
class OrderLine:
    def __init__(self, product_id: str, quantity: int, price: float):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

class Order:  # The Aggregate Root
    def __init__(self, order_id: str, customer_id: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.status = "PENDING"
        self.lines: list[OrderLine] = []

    def add_item(self, product_id: str, quantity: int, price: float):
        if self.status != "PENDING":
            raise ValueError("Cannot modify a finalized order")
        self.lines.append(OrderLine(product_id, quantity, price))
```

#### 5. Entities vs Value Objects
- Entity: An object with a distinct identity that runs through time and different states (e.g., `Order`, `Customer`).
- Value Object: An object described solely by its attributes. It has no conceptual identity and is immutable (e.g., `Money`, `Address`).

#### 6. Domain Events
A domain event captures the memory of something interesting that occurred in the domain. They are crucial for decoupling microservices.
Example: `OrderPlaced`, `InventoryReserved`, `PaymentProcessed`.

---

## 3. Service Decomposition Strategies

Decomposing a monolith is not a random process. Several proven strategies exist.

### A. Decomposition by Business Capability
This approach aligns services with business capabilities—what the business does to generate value.
Examples: Order Management, Customer Management, Shipping, Inventory.
Pros: Stable over time. Business capabilities rarely change, even if the implementation does.
Cons: Can lead to overly large services if capabilities are defined too broadly.

### B. Decomposition by Subdomain
This uses DDD to identify subdomains and maps services to them.
Examples: Product Catalog (Supporting), Pricing (Core), Identity (Generic).
Pros: Excellent alignment with domain experts and ubiquitous language.
Cons: Requires deep domain knowledge and time investment to model correctly.

### C. Decomposition by Verb / Use Case
Services are built around specific actions or use cases.
Examples: `CheckoutService`, `SearchService`, `ReportingService`.
Pros: Highly optimized for specific, high-value user journeys.
Cons: Can lead to fragmented logic where state is managed across too many services.

### D. The Strangler Fig Pattern
This is not a theoretical boundary strategy but a migration strategy. Named after a vine that grows around a tree until the tree dies, this pattern involves slowly replacing parts of a monolith with microservices.
1. Intercept traffic at the API Gateway.
2. Route new functionality or migrated endpoints to the new microservice.
3. Route legacy endpoints to the monolith.
4. Over time, the monolith is "strangled" until it can be decommissioned.

---

## 4. Data Per Service Pattern

The golden rule of microservices is the Data Per Service pattern.

### The Rule
Each microservice must have its own private database. No other service is allowed to connect to this database directly. All data access must go through the service's API.

### Why is this necessary?
1. Loose Coupling: If services share a database, a schema change in one service will break the others.
2. Polyglot Persistence: The search service needs Elasticsearch, the user service needs PostgreSQL, and the cart service needs Redis. Forcing them to share a database compromises performance.
3. Independent Scaling: The read-heavy catalog database can be scaled independently of the write-heavy transactional database.

### The Trade-off: Distributed Data
Because data is distributed, we can no longer use simple SQL joins across services.
Instead, we must use patterns like:
- API Composition: An API gateway queries multiple services and joins the data in memory.
- CQRS (Command Query Responsibility Segregation): Maintaining read-optimized materialized views by listening to domain events.

---

## 5. Service Granularity — Finding the Right Size

How big should a microservice be? The term "micro" is misleading.

### Heuristics for Sizing
1. Two-Pizza Team Rule: A service should be owned by a team that can be fed with two pizzas (6-10 people).
2. Autonomy: If a change in Service A requires a simultaneous deployment of Service B, they are too small and should be merged.
3. Single Reason to Change: A service should adhere to the Single Responsibility Principle.
4. Cognitive Load: A developer should be able to understand the entire service codebase in a few days.

### The Danger of Nanoservices
Nanoservices are services that are too small. They lead to an explosion of network hops, massive deployment overhead, and complex debugging. If a service only contains a single endpoint or a single database table, it is likely a nanoservice.

---

## 6. Anti-Patterns to Avoid

When moving to microservices, organizations often fall into predictable traps.

### 1. The Distributed Monolith
This occurs when an application is split into microservices, but they are so tightly coupled that they must be deployed together, scale together, and fail together. You inherit all the complexity of distributed systems with none of the benefits.
Symptoms: Coordinated deployments, shared databases, synchronous RPC chains.

### 2. Chatty Services
When services are too finely grained, rendering a single UI page might require dozens of synchronous network calls between services. This leads to severe latency and cascaded failures.
Solution: Re-evaluate boundaries, consolidate related services, or use GraphQL/BFF (Backend for Frontend).

### 3. Shared Libraries for Business Logic
Sharing utility code (e.g., logging formatting) is fine. Sharing domain logic via a common library (e.g., `ecommerce-core.jar`) is an anti-pattern. If the library changes, every service must be recompiled and redeployed, coupling their lifecycles.

### 4. Long Synchronous Chains
If Service A calls Service B, which calls Service C, which calls Service D synchronously, the availability of the system is the product of the availability of all four services. If each is 99% available, the total availability is 0.99^4 = 96%.
Solution: Use asynchronous communication (event-driven architecture) and the Choreography pattern.

---

## 7. Complete Example — E-Commerce Decomposition (YAML)

Below is an exhaustive YAML configuration describing the architecture of a decomposed e-commerce system using Kubernetes-style deployment manifests to illustrate service boundaries, dedicated databases, and messaging infrastructure.

```yaml
# ---------------------------------------------------------
# Architecture: E-Commerce Microservices
# ---------------------------------------------------------

apiVersion: v1
kind: Architecture
metadata:
  name: shop-system
spec:
  apiGateway:
    name: edge-router
    technology: Kong / NGINX
    responsibilities:
      - Authentication
      - Rate Limiting
      - Routing to internal services
  
  messageBroker:
    name: kafka-cluster
    topics:
      - order.created
      - order.paid
      - inventory.reserved
      - shipment.dispatched

  services:
    - name: CatalogService
      domain: Product Subdomain (Supporting)
      database:
        type: MongoDB
        name: catalog_db
      endpoints:
        - GET /api/v1/products
        - GET /api/v1/products/{id}
      subscribesTo: []
      publishes:
        - product.updated

    - name: InventoryService
      domain: Inventory Subdomain (Core)
      database:
        type: PostgreSQL
        name: inventory_db
      endpoints:
        - POST /api/v1/inventory/reserve
      subscribesTo:
        - order.created
      publishes:
        - inventory.reserved
        - inventory.out_of_stock

    - name: OrderService
      domain: Order Subdomain (Core)
      database:
        type: PostgreSQL
        name: order_db
      endpoints:
        - POST /api/v1/orders
        - GET /api/v1/orders/{id}
      subscribesTo:
        - inventory.reserved
        - order.paid
      publishes:
        - order.created

    - name: PaymentService
      domain: Payment Subdomain (Generic)
      database:
        type: CockroachDB
        name: payment_db
      endpoints:
        - POST /api/v1/payments
      subscribesTo:
        - inventory.reserved
      publishes:
        - order.paid
        - payment.failed

    - name: ShippingService
      domain: Shipping Subdomain (Supporting)
      database:
        type: MySQL
        name: shipping_db
      endpoints:
        - GET /api/v1/shipments/{id}/tracking
      subscribesTo:
        - order.paid
      publishes:
        - shipment.dispatched
```

---

## 8. Migration from Monolith — Step by Step (Python)

Migrating a monolithic application requires a structured, safe approach. We will demonstrate the Strangler Fig pattern using a Python Flask application.

### Phase 1: The Monolith
Imagine a legacy Flask monolith that handles everything.

```python
# monolith.py
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('monolith.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/users/<int:user_id>')
def get_user(user_id):
    # Monolithic user fetch
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return jsonify(dict(user))

@app.route('/orders', methods=['POST'])
def create_order():
    # Monolithic order creation touching multiple domains
    data = request.json
    conn = get_db_connection()
    
    # 1. Verify user
    user = conn.execute('SELECT * FROM users WHERE id = ?', (data['user_id'],)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    # 2. Check inventory
    item = conn.execute('SELECT * FROM inventory WHERE item_id = ?', (data['item_id'],)).fetchone()
    if item['stock'] < data['quantity']:
        return jsonify({'error': 'Out of stock'}), 400
        
    # 3. Create order
    cursor = conn.cursor()
    cursor.execute('INSERT INTO orders (user_id, item_id, quantity) VALUES (?, ?, ?)',
                   (data['user_id'], data['item_id'], data['quantity']))
    
    # 4. Update inventory (Tight coupling!)
    cursor.execute('UPDATE inventory SET stock = stock - ? WHERE item_id = ?',
                   (data['quantity'], data['item_id']))
    
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'order_id': order_id, 'status': 'success'})

if __name__ == '__main__':
    app.run(port=5000)
```

### Phase 2: Extracting the Service and Using an API Gateway

We identify the Order domain as our first target for extraction. We create a new, separate service.

```python
# new_order_service.py (Runs on port 5001)
from flask import Flask, request, jsonify
import psycopg2 # Now using an independent database

app = Flask(__name__)

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    
    # Instead of direct DB access to other domains, we now rely on events or synchronous checks.
    # For simplicity in this step, we assume the API Gateway has validated the user.
    # We will publish an event for inventory later.
    
    conn = psycopg2.connect("dbname=orders_db user=admin")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO orders (user_id, item_id, quantity) VALUES (%s, %s, %s) RETURNING id',
                   (data['user_id'], data['item_id'], data['quantity']))
    
    order_id = cursor.fetchone()[0]
    conn.commit()
    
    # Emit an event to Kafka (Mocked here)
    # kafka_producer.send('order.created', {'order_id': order_id, 'item_id': ...})
    
    return jsonify({'order_id': order_id, 'status': 'pending_inventory_check'})

if __name__ == '__main__':
    app.run(port=5001)
```

### Phase 3: The API Gateway (Nginx / API Gateway logic)

We use a gateway to route traffic intelligently, strangling the monolith.

```python
# gateway.py (Simulating an API Gateway like Kong)
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

MONOLITH_URL = "http://localhost:5000"
NEW_ORDER_SERVICE_URL = "http://localhost:5001"

@app.route('/users/<int:user_id>')
def proxy_users(user_id):
    # Still routed to the monolith
    resp = requests.get(f"{MONOLITH_URL}/users/{user_id}")
    return jsonify(resp.json()), resp.status_code

@app.route('/orders', methods=['POST'])
def proxy_orders():
    # Strangler Fig: Traffic is now routed to the new microservice
    resp = requests.post(f"{NEW_ORDER_SERVICE_URL}/orders", json=request.json)
    return jsonify(resp.json()), resp.status_code

if __name__ == '__main__':
    app.run(port=8080)
```

### Summary of Migration
By utilizing the API Gateway to route traffic, the client applications (web, mobile) are entirely unaware that a migration is taking place. Over months or years, more routes in `gateway.py` are pointed away from `MONOLITH_URL` to new microservice URLs. When no routes point to the monolith, it is safely deleted.

---
### Real-World War Story: The Distributed Monolith Disaster
In a mid-sized fintech company, the CTO decreed a mandate to "move to microservices." The team broke their Rails monolith into 15 Node.js services. However, they kept the single PostgreSQL database.
When Service A updated a user record, it occasionally locked rows that Service B was trying to read for a batch process. The resulting deadlocks took down the entire cluster. Because the services were deeply entangled via the database schema, they couldn't be deployed independently. A schema change required coordinating 15 deployments simultaneously on a Saturday night.
The fix took 18 months: they had to slowly untangle the schema, introduce event streaming (Kafka) for state transfer, and implement the Data Per Service pattern.

### Conclusion
Decomposition is the hardest part of microservices. Get the boundaries right using Domain-Driven Design, enforce strict data isolation, and migrate incrementally using the Strangler Fig pattern.

### Section: Event Storming — Discovery Technique

Event Storming is a collaborative workshop technique for discovering bounded contexts and domain events:

```
Event Storming Process (3 phases):

Phase 1 - Unstructured Exploration:
  Participants write Domain Events (orange stickies) on a timeline
  Events are past-tense: OrderPlaced, PaymentFailed, ItemShipped
  No structure yet — just get everything on the board

Phase 2 - Enforce Timeline:
  Arrange events chronologically
  Identify causes: Commands (blue) trigger Events (orange)
  Commands: PlaceOrder, ProcessPayment, ShipItem

Phase 3 - Identify Aggregates:
  Group Commands + Events that belong to the same entity
  Each group is a candidate Bounded Context / Microservice

Result for e-commerce:
  [Order Aggregate]:     PlaceOrder -> OrderPlaced, CancelOrder -> OrderCancelled
  [Payment Aggregate]:   ProcessPayment -> PaymentProcessed, RefundPayment -> RefundIssued
  [Inventory Aggregate]: ReserveStock -> StockReserved, ReleaseStock -> StockReleased
  [Shipping Aggregate]:  CreateShipment -> ShipmentCreated, MarkDelivered -> OrderDelivered
```

### Section: CQRS — Command Query Responsibility Segregation

CQRS separates the write model (commands) from the read model (queries):

```python
# Without CQRS: same model for reads and writes
class OrderRepository:
    def create_order(self, order: Order) -> Order: ...  # write
    def get_order(self, id: str) -> Order: ...          # read -- same heavy domain model
    def list_orders(self, user_id: str) -> list[Order]: ...  # read with JOINs

# With CQRS: separate models optimized for each purpose

# Command side: rich domain model, validates business rules
class OrderCommandHandler:
    def handle_place_order(self, cmd: PlaceOrderCommand) -> str:
        # Load aggregate, validate, mutate, save, publish event
        order = Order.create(
            customer_id=cmd.customer_id,
            items=cmd.items
        )
        # Validates: stock available, customer active, payment method valid
        self.order_repo.save(order)
        self.event_bus.publish(OrderPlaced(order_id=order.id, ...))
        return order.id

# Query side: thin read models, optimized for specific views
class OrderQueryHandler:
    def get_order_summary(self, order_id: str) -> OrderSummaryView:
        # Direct SQL query against read-optimized schema (denormalized)
        row = self.db.execute(
            '''SELECT o.id, o.status, o.total,
                      c.name as customer_name, c.email,
                      COUNT(oi.id) as item_count
               FROM orders o
               JOIN customers c ON o.customer_id = c.id
               JOIN order_items oi ON o.id = oi.order_id
               WHERE o.id = %s
               GROUP BY o.id, c.name, c.email''',
            (order_id,)
        )
        return OrderSummaryView(**row)

    def list_orders_for_user(self, user_id: str, page: int, size: int) -> list[OrderListView]:
        # Separate denormalized read model -- no joins needed
        return self.read_db.execute(
            'SELECT * FROM order_list_view WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s',
            (user_id, size, page * size)
        )
```

CQRS benefits:
- Read and write sides can scale independently (reads are usually 90% of traffic)
- Read model can be a different database entirely (PostgreSQL writes, Elasticsearch reads)
- Read models can be rebuilt from event log at any time
- Write model stays focused on business rules without read performance pressure

CQRS + Event Sourcing:
```python
# Event Sourcing: persist events, not current state
# State is derived by replaying events

class Order:
    def __init__(self):
        self.id = None
        self.status = None
        self.items = []
        self.events = []  # uncommitted events

    @classmethod
    def from_events(cls, events: list) -> 'Order':
        order = cls()
        for event in events:
            order.apply(event)
        return order

    def place(self, customer_id: str, items: list):
        # Validate
        if not items:
            raise ValueError('Order must have at least one item')
        # Record event (do not mutate state directly)
        event = OrderPlaced(order_id=str(uuid4()), customer_id=customer_id, items=items)
        self.apply(event)
        self.events.append(event)

    def apply(self, event):
        if isinstance(event, OrderPlaced):
            self.id = event.order_id
            self.status = 'PENDING'
            self.items = event.items
        elif isinstance(event, OrderConfirmed):
            self.status = 'CONFIRMED'
        elif isinstance(event, OrderCancelled):
            self.status = 'CANCELLED'

# Event store table:
# CREATE TABLE event_store (
#   event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   aggregate_id  UUID NOT NULL,
#   aggregate_type VARCHAR(100) NOT NULL,
#   event_type    VARCHAR(100) NOT NULL,
#   event_version INT NOT NULL,
#   payload       JSONB NOT NULL,
#   created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
# );
# CREATE UNIQUE INDEX ON event_store(aggregate_id, event_version);  -- optimistic locking
```

### Section: Service Versioning and Backward Compatibility

```python
# API versioning strategies for microservices

# Strategy 1: URL path versioning (most common)
# /v1/orders -- current consumers
# /v2/orders -- new consumers with breaking changes
# Run both versions simultaneously during transition

# Strategy 2: Backward-compatible API evolution (Postel's Law)
# Be conservative in what you send, liberal in what you accept

# Safe changes (non-breaking):
#   - Adding new optional fields to response
#   - Adding new optional request parameters
#   - Adding new endpoints
#   - Expanding enum values (if consumers handle unknown values)

# Breaking changes (require new version):
#   - Removing fields from response
#   - Renaming fields
#   - Changing field types (string -> int)
#   - Changing required fields to mandatory

# Consumer-driven contract testing (Pact):
# Consumer defines what it needs; provider verifies it satisfies all consumers
# Prevents accidentally breaking downstream services

# Example: Order Service (consumer) contract with Inventory Service (provider)
# Consumer test:
pact = Consumer('order-service').has_pact_with(Provider('inventory-service'))
pact.given('product SKU-123 has 10 units in stock').upon_receiving(
    'a stock check request'
).with_request(
    method='GET', path='/inventory/SKU-123'
).will_respond_with(
    status=200,
    body={'product_id': 'SKU-123', 'available': 10, 'reserved': 2}
)
# This contract is published to a Pact Broker
# Provider CI pipeline verifies it can satisfy all consumer contracts
```

### Section: Health Checks and Readiness

```python
# Every microservice must expose health endpoints
# Kubernetes uses these for liveness (restart if unhealthy) and readiness (route traffic)

from fastapi import FastAPI
from sqlalchemy import text
import redis
import httpx

app = FastAPI()

@app.get('/health/live')
async def liveness():
    # Minimal check: is the process alive and responsive?
    # Do NOT check external dependencies here (would cause restart loops)
    return {'status': 'alive'}

@app.get('/health/ready')
async def readiness():
    # Thorough check: can we serve traffic?
    # Check all critical dependencies
    checks = {}
    all_healthy = True

    # Database
    try:
        await db.execute(text('SELECT 1'))
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {e}'
        all_healthy = False

    # Redis cache
    try:
        redis_client.ping()
        checks['redis'] = 'ok'
    except Exception as e:
        checks['redis'] = f'error: {e}'
        all_healthy = False

    # Critical upstream service
    try:
        resp = await httpx.get('http://inventory-service/health/live', timeout=2.0)
        checks['inventory_service'] = 'ok' if resp.status_code == 200 else f'status: {resp.status_code}'
    except Exception as e:
        checks['inventory_service'] = f'error: {e}'
        # Note: not marking all_healthy=False for non-critical upstream

    status_code = 200 if all_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={'status': 'ready' if all_healthy else 'not_ready', 'checks': checks}
    )

# Kubernetes probe configuration:
# livenessProbe:
#   httpGet:
#     path: /health/live
#     port: 8080
#   initialDelaySeconds: 10
#   periodSeconds: 10
#   failureThreshold: 3
# readinessProbe:
#   httpGet:
#     path: /health/ready
#     port: 8080
#   initialDelaySeconds: 5
#   periodSeconds: 5
#   failureThreshold: 2
```

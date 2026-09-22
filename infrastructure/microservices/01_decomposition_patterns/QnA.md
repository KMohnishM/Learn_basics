# Decomposition Patterns QnA

## 1. What is Conway's Law? How does it influence microservice boundaries? Give a concrete example of an org structure and the service boundaries it naturally produces.
Conway's Law states that organizations which design systems are constrained to produce designs which are copies of the communication structures of these organizations. In the context of microservices, this law implies that the architecture of a system will inevitably reflect the team structure building it. If you have distinct frontend, backend, and database teams, you will naturally produce a monolithic, three-tier architecture because changes require coordination across these communication boundaries. To effectively build microservices, organizations often employ the "Inverse Conway Maneuver," which involves restructuring the teams to match the desired architecture. By creating cross-functional teams that own specific business domains, the system naturally evolves into independent microservices aligned with those domains. For example, consider an e-commerce company organized into independent business units: a Shopping Cart team, an Inventory team, and a Payments team, each with their own developers, QA, and product managers. This organizational structure naturally produces a Shopping Cart Service, an Inventory Service, and a Payments Service. Each team can deploy independently and evolve their service without tightly coupling to the others, accurately reflecting their communication boundaries.

## 2. What is a Bounded Context in Domain-Driven Design? Why is it the natural unit for a microservice? Give an example of the same concept (e.g. Product) having different meanings in two different Bounded Contexts.
A Bounded Context in Domain-Driven Design (DDD) is a distinct semantic boundary within which a particular domain model is defined and strictly applies. Within this boundary, every term has a single, unambiguous meaning, forming a Ubiquitous Language shared by developers and domain experts. The Bounded Context is considered the natural unit for a microservice because it encapsulates high cohesion (everything within the context relates to a single business capability) and loose coupling (it interacts with other contexts through well-defined interfaces). This alignment prevents the creation of massive, entangled "god classes" and allows each service to evolve its data model independently. A classic example is the concept of a "Product." In a Catalog Bounded Context, a Product is defined by its display name, description, images, and customer reviews; it's all about presentation. However, in an Inventory Bounded Context, the same "Product" is defined by its SKU, weight, warehouse location, and stock levels. If you tried to force a single Product model across the entire system, you would end up with a massive table and conflicting requirements. By separating them into different Bounded Contexts, the Catalog Service and Inventory Service can each maintain their own optimized representation of a Product.

## 3. What is the Database-per-Service pattern? Why is sharing a database between microservices an anti-pattern? What are the cascading consequences of a schema change in a shared database?
The Database-per-Service pattern dictates that each microservice must manage its own persistent data, and this data can only be accessed by other services via the owning service's API. This ensures tight encapsulation and prevents hidden coupling through the database tier. Sharing a database between microservices is widely considered an anti-pattern because it introduces integration database coupling, destroying the independence that microservices aim to provide. When multiple services connect to the same tables, they become tightly bound to the same schema. If Service A needs to modify a column to support a new feature, Service B might break because it expects the old schema. The cascading consequences of a schema change in a shared database are severe: developers must coordinate deployments across multiple teams, lock contention increases, and a performance degradation in one service's query can saturate the database, taking down all other services sharing it. Furthermore, it prevents teams from choosing the best polyglot persistence strategy for their specific needs, forcing a graph-heavy service to use a relational schema just because the rest of the company does.

## 4. What is an Aggregate in DDD? What is the Aggregate Root? Why should transactions never span multiple aggregates? Give a concrete Order aggregate example with its constituent parts.
An Aggregate in Domain-Driven Design is a cluster of domain objects that can be treated as a single unit for data changes. It defines a consistency boundary; all invariants (business rules) within the aggregate must be strictly enforced at all times. The Aggregate Root is the single, specific entity within this cluster that acts as the gateway. External objects can only hold references to the Aggregate Root, never to the internal constituent objects. Transactions should never span multiple aggregates because doing so introduces tight coupling, increases lock contention, and violates the principle of independent scalability. If you need to update multiple aggregates, you should achieve eventual consistency using domain events rather than distributed transactions. For a concrete example, consider an `Order` aggregate. The `Order` entity is the Aggregate Root. Its constituent parts might include a list of `OrderItem` entities and a `ShippingAddress` value object. 
```python
class OrderItem:
    def __init__(self, product_id, quantity, price):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

class Order:
    def __init__(self, order_id, customer_id):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = []
        self.status = "CREATED"
        
    def add_item(self, item: OrderItem):
        # Invariants are checked here
        if self.status != "CREATED":
            raise ValueError("Cannot add items to confirmed order")
        self.items.append(item)
```

## 5. What is the Strangler Fig pattern for migrating a monolith? Walk through each phase (facade introduction, parallel running, cutover) for an e-commerce order module.
The Strangler Fig pattern is a risk-mitigated strategy for incrementally migrating a monolithic application to a microservices architecture. Instead of a high-risk "big bang" rewrite, the new system is built around the edges of the old one, gradually taking over functionality until the monolith can be decommissioned. 
Phase 1: Facade Introduction. We deploy an API Gateway (the facade) in front of the e-commerce monolith. Initially, this gateway routes 100% of the traffic, including order placement, directly to the monolith. This establishes the routing infrastructure without changing behavior.
Phase 2: Parallel Running (or Dark Launching). We build the new Order Microservice. The API Gateway is configured to route the primary request to the monolith, but asynchronously shadow the request to the new microservice. The results from the new service are logged and compared against the monolith's output, but not returned to the user. This ensures the new logic is correct under production load.
Phase 3: Cutover. Once confidence is high, the API Gateway routing rules are updated. Traffic for `/api/orders` is now directed entirely to the new Order Microservice. The order module inside the monolith is deprecated and eventually deleted as the "strangler fig" has completely replaced it.

## 6. What is a Distributed Monolith? How does it form despite being built as separate services? Why is it considered the worst outcome of a microservices migration?
A Distributed Monolith is a system that is deployed as separate microservices but maintains the tight coupling of a monolithic architecture. It forms when organizations adopt the physical separation of microservices (different repositories, separate deployments) without adhering to the logical boundaries required for independence (loose coupling, high cohesion). This often happens when services share a single database, when they rely on synchronous, blocking REST calls for every operation, or when business logic is scattered across multiple services rather than encapsulated within bounded contexts. It is considered the worst outcome of a microservices migration because it combines the drawbacks of both architectures. You incur the immense operational complexity, network latency, and distributed debugging nightmares of microservices, but you retain the inability to deploy independently or scale autonomously. If updating Service A requires simultaneously updating and deploying Service B and Service C, you have a distributed monolith, not a microservices architecture.

## 7. What is CQRS? What are the command side and query side? Show a Python example of a command handler and a query handler for an Order service, using different models for each.
CQRS (Command Query Responsibility Segregation) is an architectural pattern that separates the data mutation operations (Commands) from the data retrieval operations (Queries). This segregation allows the write model to be optimized for enforcing business invariants and transaction integrity, while the read model can be heavily denormalized and optimized for fast query performance. The command side typically handles complex validation and domain logic, updating a primary database. The query side reads from a separate, synchronized data store (like an Elasticsearch index or a materialized view) designed for rapid retrieval.
```python
# Command Side: Optimized for business logic
class CreateOrderCommand:
    def __init__(self, customer_id, items):
        self.customer_id = customer_id
        self.items = items

class OrderCommandHandler:
    def __init__(self, write_repository):
        self.repo = write_repository
        
    def handle(self, command: CreateOrderCommand):
        order = Order(command.customer_id)
        for item in command.items:
            order.add_item(item) # Domain logic applied
        self.repo.save(order)
        # Publish OrderCreatedEvent...

# Query Side: Optimized for fast reads
class GetOrderSummaryQuery:
    def __init__(self, order_id):
        self.order_id = order_id

class OrderQueryHandler:
    def __init__(self, read_database):
        self.db = read_database
        
    def handle(self, query: GetOrderSummaryQuery):
        # Reads from a denormalized view, no domain logic
        return self.db.query("SELECT * FROM order_summary_view WHERE id = ?", query.order_id)
```

## 8. What are Domain Events? How do they differ from API calls for communicating between services? Give 5 domain events from an e-commerce system and what each triggers.
Domain Events are historical records of something significant that has happened within a business domain. They represent facts that occurred in the past and are immutable. They differ fundamentally from synchronous API calls because they decouple the producer from the consumers. An API call is an imperative command ("do this right now," expecting a response), creating temporal coupling. A domain event is a declarative statement ("this happened," expecting no direct response), allowing multiple independent services to react asynchronously without the producer knowing about them.
Five e-commerce domain events:
1. `OrderPlaced`: Triggered by the Order Service. Consumed by the Inventory Service to reserve stock, and by the Payment Service to initiate a charge.
2. `PaymentSucceeded`: Triggered by the Payment Service. Consumed by the Order Service to update status to "Paid", and by the Fulfillment Service to begin packing.
3. `InventoryExhausted`: Triggered by the Inventory Service. Consumed by the Catalog Service to update the product page to show "Out of Stock."
4. `OrderShipped`: Triggered by the Fulfillment Service. Consumed by the Notification Service to send a tracking email to the customer.
5. `CustomerAccountCreated`: Triggered by the Identity Service. Consumed by the Marketing Service to send a welcome email and add them to the promotional mailing list.

## 9. What is Event Sourcing? How does it store state differently from a traditional database? Show a Python Order aggregate that applies events to rebuild state from an event store.
Event Sourcing is an architectural pattern where state changes are logged as a sequence of immutable events rather than overwriting the current state in a database row. Instead of storing the current state of an `Order`, the system stores an append-only log of events: `OrderCreated`, `ItemAdded`, `ShippingAddressUpdated`. To determine the current state, the system replays these events in sequence from the beginning. This provides an impeccable audit trail, allows for point-in-time reconstruction of state, and avoids complex relational mapping.
```python
class OrderAggregate:
    def __init__(self):
        self.id = None
        self.items = []
        self.status = None
        self.version = 0

    def apply(self, event):
        if event['type'] == 'OrderCreated':
            self.id = event['data']['order_id']
            self.status = 'CREATED'
        elif event['type'] == 'ItemAdded':
            self.items.append(event['data']['item_sku'])
        elif event['type'] == 'OrderShipped':
            self.status = 'SHIPPED'
        self.version += 1

    @classmethod
    def load_from_history(cls, events):
        aggregate = cls()
        for event in events:
            aggregate.apply(event)
        return aggregate

# Usage
history = [
    {'type': 'OrderCreated', 'data': {'order_id': '123'}},
    {'type': 'ItemAdded', 'data': {'item_sku': 'SKU-A'}},
]
order = OrderAggregate.load_from_history(history)
```

## 10. What is Event Storming? What are the three phases? What artifacts (Domain Events, Commands, Aggregates) does it produce?
Event Storming is a rapid, interactive workshop-based method used to explore complex business domains and discover microservice boundaries. It brings together technical experts (developers, architects) and domain experts (product owners, business analysts) to model the system using sticky notes on a large wall. 
The process typically involves three phases:
1. Chaotic Exploration: Participants identify Domain Events (orange stickies, past tense, e.g., "Order Placed") and place them on a timeline. This surfaces the core business process and terminology.
2. Enforcing the Timeline: The events are ordered chronologically. Participants identify the Commands (blue stickies, imperative, e.g., "Place Order") that trigger the events, and the Actors/Systems that issue the commands.
3. Grouping into Aggregates/Bounded Contexts: Participants identify the business concepts or state machines (Aggregates, yellow stickies) that process the commands and emit the events. By grouping related aggregates and events, natural Bounded Contexts emerge, which often translate directly into microservice boundaries.

## 11. What is the difference between a Core Domain, Supporting Subdomain, and Generic Subdomain? How does this classification affect the build-vs-buy decision for each?
In Domain-Driven Design, the overall business domain is broken down into subdomains to focus effort effectively.
A Core Domain is the primary area that provides competitive advantage and differentiates the company from its competitors. This is the secret sauce. 
A Supporting Subdomain is necessary for the business but does not provide a competitive edge. It is custom to the business but not the primary differentiator.
A Generic Subdomain is a functional area required by the business but common across many industries (e.g., payroll, user authentication, CRM).
This classification directly drives the build-vs-buy decision:
- Core Domains MUST be built in-house. This is where you invest your best engineering talent to write custom microservices because this is what makes your business unique.
- Supporting Subdomains should be built in-house if necessary, but you should minimize investment. Consider outsourcing or using low-code solutions if possible.
- Generic Subdomains MUST be bought or adopted from open-source. You should never write your own authentication server (use Auth0 or Keycloak) or CRM system (use Salesforce), as building them diverts resources from the Core Domain.

## 12. What is the Shared Library anti-pattern in microservices? Why does a shared common library become a coupling mechanism? How do you share code safely across services?
The Shared Library anti-pattern occurs when teams create a massive "common" or "utils" library containing shared business logic, domain models, and database access code, which is then imported by multiple microservices. While DRY (Don't Repeat Yourself) is good in a monolith, in microservices, this shared library becomes a severe coupling mechanism. If the core library changes a data model to satisfy Service A, Service B and Service C might break or require immediate recompilation and deployment. It forces teams to coordinate releases, effectively recreating a distributed monolith through library dependencies. 
To share code safely across services, you must distinguish between business logic and technical infrastructure. You should never share domain models or business rules via libraries. If business logic needs to be shared, it should be extracted into its own independent microservice with an API. You CAN share technical cross-cutting concerns via libraries—such as logging frameworks, metrics exporters, or HTTP client wrappers—because these do not contain business rules and change infrequently.

## 13. What is consumer-driven contract testing (Pact)? How does it prevent a provider service from accidentally breaking its consumers? What is a Pact Broker?
Consumer-driven contract testing is a methodology where the expectations of a consumer service regarding an API provider are captured in a formalized "contract." Tools like Pact are used to implement this. The consumer writes tests defining the exact request it will send and the minimal response structure it requires. This generates a contract file. 
This prevents the provider service from accidentally breaking its consumers because the provider's CI/CD pipeline downloads these contracts and runs them against its own API before deploying. If a provider team changes a field name or removes an endpoint that a consumer relies on, the contract test will fail in the provider's build, halting the deployment. This provides fast, localized feedback without the flakiness of end-to-end integration environments. 
A Pact Broker is a centralized repository that stores these contracts. Consumers publish their generated contracts to the broker, and providers fetch them during their builds. It tracks which versions of consumers and providers are compatible, enabling safe, independent deployments.

## 14. What are insertion anomalies and how do they manifest in a chatty services anti-pattern? Give a concrete scenario where Service A makes 10 synchronous calls to Service B per user request and explain the cascading failure risk.
Insertion anomalies typically refer to database normalization issues, but in the context of microservice decomposition, they manifest when data is scattered across services in a way that forces excessive, inefficient communication to assemble a complete view. This leads to the "chatty services" anti-pattern.
Consider a scenario where an API Gateway (Service A) needs to render a user dashboard showing their profile, recent orders, and loyalty points. If the system is overly decomposed, Service A might need to make a synchronous call to the User Service, then iterate over 10 recent orders and make 10 distinct synchronous calls to the Order Service to fetch details, and finally call the Loyalty Service. 
The cascading failure risk here is immense. If the Order Service experiences slight latency (e.g., 50ms to 200ms), Service A's response time degrades by 1.5 seconds (10 * 150ms increase). Thread pools in Service A will quickly exhaust waiting for these responses, causing Service A to fail entirely. This single point of slowness cascades up the chain, bringing down the entire dashboard feature. The solution is usually API aggregation, CQRS, or rethinking the service boundaries to group related data.

## 15. What is the two-pizza team rule and how does it govern microservice size? What organizational dysfunction occurs when a single service is owned by too many teams?
The "two-pizza team" rule, popularized by Amazon, suggests that a team should be small enough that it can be fed with two large pizzas (roughly 6 to 10 people). This rule governs microservice size by dictating that a single microservice should be small enough to be fully understood, developed, tested, and operated by a single two-pizza team. The cognitive load of the service must fit within the capacity of this small group.
If a microservice grows so large that it requires multiple teams to manage it, severe organizational dysfunction occurs. Communication overhead skyrockets as teams must coordinate deployments and resolve merge conflicts. Accountability is lost ("who is on call for this module?"), and the agility promised by microservices evaporates because decisions require consensus across dozens of engineers. When a service becomes too large for a two-pizza team, it is a strong signal that the domain boundary is incorrect and the service needs to be decomposed further.

# Jakarta EE and J2EE Architecture: Questions and Answers

---

### Question 1: What is the difference between Jakarta EE and Spring Framework?

**Answer:**
Jakarta EE (formerly Java EE) is an open, vendor-neutral collection of specifications governed by the Eclipse Foundation, whereas the Spring Framework is an opinionated, commercial, and open-source implementation platform maintained by Broadcom (VMware Tanzu).

Jakarta EE defines standardized APIs (such as Jakarta Servlets, Jakarta Persistence, Jakarta REST, and Jakarta CDI) through formal Specification Committees. To run a Jakarta EE application, you deploy code into a certified application server or runtime (such as WildFly, Payara, Eclipse GlassFish, or Quarkus) that implements those specifications.

Spring, conversely, does not define standard specifications; it provides direct implementations. Spring applications typically package an embedded web runtime (such as Tomcat or Netty) inside a self-executable JAR file. While Spring heavily leverages several underlying Jakarta specifications (such as Jakarta Servlet and Jakarta Validation), it implements its own inversion of control (IoC) container, transactional proxy subsystem, and web MVC engine.

```java
// Jakarta EE CDI & JAX-RS Endpoint
@Path("/accounts")
@RequestScoped
public class AccountResource {
    @Inject
    private AccountService accountService;

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response getAccount(@QueryParam("id") Long id) {
        return Response.ok(accountService.findById(id)).build();
    }
}

// Spring Boot REST Controller
@RestController
@RequestMapping("/accounts")
public class AccountController {
    private final AccountService accountService;

    public AccountController(AccountService accountService) {
        this.accountService = accountService;
    }

    @GetMapping
    public ResponseEntity<AccountDto> getAccount(@RequestParam Long id) {
        return ResponseEntity.ok(accountService.findById(id));
    }
}
```

In modern cloud computing, Jakarta EE has adapted through minimal profiles (Jakarta EE Core Profile) used in frameworks like Quarkus, while Spring Boot remains the dominant enterprise application framework due to its rich starter ecosystem, auto-configuration, and rapid developer workflow.

---

### Question 2: Explain the full Servlet lifecycle from loading to destruction.

**Answer:**
The Servlet lifecycle is managed entirely by the servlet container (such as Tomcat, Jetty, or Undertow). The lifecycle transitions through four discrete phases: Class Loading & Instantiation, Initialization, Request Servicing, and Destruction.

1. **Loading and Instantiation:** The container locates the servlet class via annotations (`@WebServlet`) or `web.xml`. If `load-on-startup` is non-negative, the container instantiates the servlet during server startup. Otherwise, instantiation is deferred until the first incoming request mapped to the servlet URL arrives.
2. **Initialization (`init`):** Once instantiated, the container calls `servlet.init(ServletConfig config)` exactly once. The servlet reads initialization parameters and sets up expensive resources. If `init()` throws an exception, the servlet is marked out-of-service.
3. **Request Servicing (`service`):** For every incoming HTTP request, the container allocates a worker thread from its thread pool and executes `service(ServletRequest, ServletResponse)`. In `HttpServlet`, the `service()` method inspects the HTTP request method verb (`GET`, `POST`, `PUT`, `DELETE`) and delegates to `doGet()`, `doPost()`, etc.
4. **Destruction (`destroy`):** When the application is stopped or undeployed, the container calls `destroy()` once. Active worker threads are permitted to finish before the servlet instance is released for garbage collection.

```java
@WebServlet(name = "LifecycleDemoServlet", urlPatterns = "/lifecycle", loadOnStartup = 1)
public class LifecycleDemoServlet extends HttpServlet {
    private DataSource dataSource;

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        try {
            InitialContext ctx = new InitialContext();
            this.dataSource = (DataSource) ctx.lookup("java:comp/env/jdbc/AppDS");
            log("Servlet initialized and DataSource handle acquired.");
        } catch (NamingException e) {
            throw new ServletException("Initialization failed", e);
        }
    }

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        resp.setContentType("text/plain");
        resp.getWriter().println("Servicing thread: " + Thread.currentThread().getName());
    }

    @Override
    public void destroy() {
        log("Releasing resources during servlet destruction.");
        this.dataSource = null;
        super.destroy();
    }
}
```

Because a single servlet instance serves concurrent requests across multiple threads, all instance variables must be thread-safe, immutable, or avoided altogether.

---

### Question 3: What are the differences between Stateless, Stateful, and Singleton EJBs?

**Answer:**
Enterprise JavaBeans (EJBs) provide container-managed transactional components categorized into three session bean lifecycle models: Stateless (`@Stateless`), Stateful (`@Stateful`), and Singleton (`@Singleton`).

1. **Stateless Session Beans (`@Stateless`):**
   - Retain no client-specific conversational state across method invocations.
   - The container maintains an instance pool. A client call can be routed to any arbitrary available bean in the pool.
   - Extremely scalable and high-throughput because instances are freely reused among concurrent threads.
2. **Stateful Session Beans (`@Stateful`):**
   - Maintain client conversational state across multiple sequential invocations.
   - Each client gets a dedicated bean instance.
   - When memory pressure occurs, the container serializes the bean and writes it to disk (passivation) via `@PrePassivate`, and restores it later via `@PostActivate`.
   - The client must explicitly invoke a method annotated with `@Remove` to destroy the bean instance.
3. **Singleton Session Beans (`@Singleton`):**
   - Exactly one instance exists per application lifecycle across the entire JVM.
   - Supports concurrent thread access managed either by the container (`@ConcurrencyManagement(CONTAINER)`) using `@Lock(LockType.READ)` and `@Lock(LockType.WRITE)` or by the bean developer.
   - Can initialize eagerly on container startup using `@Startup`.

```java
@Stateless
public class OrderProcessingStatelessBean {
    public void placeOrder(Long customerId, Long itemId) {
        // Stateless calculation and database write
    }
}

@Stateful
public class ShoppingCartStatefulBean implements Serializable {
    private final List<Long> cartItems = new ArrayList<>();

    public void addItem(Long itemId) {
        cartItems.add(itemId);
    }

    @Remove
    public void checkout() {
        // Complete transaction and release bean
    }
}

@Singleton
@Startup
@ConcurrencyManagement(ConcurrencyManagementType.CONTAINER)
public class GlobalExchangeRateCache {
    private final Map<String, Double> rates = new ConcurrentHashMap<>();

    @Lock(LockType.READ)
    public Double getRate(String currency) {
        return rates.get(currency);
    }

    @Lock(LockType.WRITE)
    public void updateRate(String currency, Double rate) {
        rates.put(currency, rate);
    }
}
```

Stateless beans are preferred in modern architectures because horizontal scaling requires stateless service tiers.

---

### Question 4: What is CDI and how does it differ from Spring's dependency injection?

**Answer:**
Contexts and Dependency Injection (CDI) is the official type-safe dependency injection specification of the Jakarta EE platform (JSR 365 / Jakarta CDI). While both CDI and Spring IoC decouple object creation from consumption, they operate under fundamentally different design philosophies and mechanisms.

CDI is strictly type-safe. In Spring, beans are historically identified by string names (with `@Qualifier("beanName")`), whereas CDI relies heavily on custom runtime annotations as qualifiers. If an injection point in CDI cannot be uniquely resolved at deployment time, the container fails fast during application startup with an `UnsatisfiedResolutionException` or `AmbiguousResolutionException`.

CDI also defines contextual lifecycles where bean instances are bound directly to active runtime contexts (`@RequestScoped`, `@SessionScoped`, `@ConversationScoped`, `@ApplicationScoped`, `@Dependent`). When a client injects a `@RequestScoped` bean into an `@ApplicationScoped` bean, CDI injects a client proxy that dynamically delegates method calls to the instance associated with the calling thread's current HTTP request.

```java
// CDI Custom Qualifier Definition
@Qualifier
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.FIELD, ElementType.TYPE, ElementType.METHOD, ElementType.PARAMETER})
public @interface MockPayment {}

// Producer bean in CDI
@ApplicationScoped
public class GatewayProducer {
    @Produces
    @MockPayment
    public PaymentClient createMockClient() {
        return new PaymentClient("http://sandbox.gateway.local");
    }
}

// Injection in CDI
@RequestScoped
public class OrderService {
    @Inject
    @MockPayment
    private PaymentClient paymentClient;

    public void checkout() {
        paymentClient.charge(100.0);
    }
}
```

In contrast, Spring's `@Autowired` uses bean names as a fallback for resolution, provides extensive conditional annotations (`@ConditionalOnProperty`), and integrates natively with Spring Boot auto-configuration.

---

### Question 5: What are the differences between JMS Queues and Topics?

**Answer:**
The Java Message Service (JMS) specification defines two fundamental messaging models: Point-to-Point (PTP) using Queues, and Publish/Subscribe (Pub/Sub) using Topics.

1. **JMS Queue (Point-to-Point):**
   - Each message has exactly one consumer. If multiple consumers listen to the same queue, the JMS broker distributes messages across consumers in a round-robin or competitive consumer pattern.
   - A message is removed from the queue as soon as one consumer successfully acknowledges receipt.
   - If no consumers are active when a message arrives, the queue holds the message until a consumer connects.
   - Ideal for task distribution, order execution, and parallel background worker architectures.
2. **JMS Topic (Publish/Subscribe):**
   - Each message is broadcast to all active subscribers registered to that topic.
   - In standard subscriptions, if a consumer is offline when a message is published, the message is permanently missed.
   - With **Durable Subscriptions**, the broker retains unacknowledged messages for a disconnected subscriber until it reconnects.
   - Ideal for notifications, price quote broadcasts, and event-driven state updates.

```java
public class JmsMessagingExample {
    public void produceMessages(JMSContext context, Queue queue, Topic topic) {
        // Point-to-point delivery: only one worker consumes this message
        context.createProducer().send(queue, "Order-ID-90210: Process payment");

        // Broadcast delivery: all active subscribers receive this notification
        context.createProducer().send(topic, "MARKET_ALERT: EUR/USD rate changed");
    }

    public void consumeQueue(JMSContext context, Queue queue) {
        JMSConsumer consumer = context.createConsumer(queue);
        String payload = consumer.receiveBody(String.class, 5000);
        System.out.println("Processing single task: " + payload);
    }

    public void registerDurableTopicSubscriber(JMSContext context, Topic topic) {
        // Retains missed events across restarts
        JMSConsumer durableConsumer = context.createDurableConsumer(topic, "AuditSubscription");
        durableConsumer.setMessageListener(msg -> {
            System.out.println("Audit log received broadcast message");
        });
    }
}
```

Queues guarantee load distribution without duplicate processing, while Topics guarantee multi-consumer fan-out.

---

### Question 6: How does @PersistenceContext work in Jakarta EE vs Spring's @Autowired EntityManager?

**Answer:**
In standard Jakarta EE, `@PersistenceContext` injects a container-managed `EntityManager` whose lifecycle and persistence context boundary are bound directly to active JTA transactions. In Spring Boot, injecting an `EntityManager` via `@PersistenceContext` or `@Autowired` injects a transactional proxy that delegates dynamically to the thread's current Spring transaction.

Under Jakarta EE with a Transaction-Scoped persistence context (the default), calling methods on the injected `EntityManager` automatically binds operations to the current JTA transaction. When the transaction commits, changes are flushed to the database, and the persistence context is cleared and closed.

In Spring Framework, Spring registers `SharedEntityManagerCreator`. When you inject `EntityManager`, Spring injects a dynamic proxy (`java.lang.reflect.Proxy`) implementing `EntityManager`. When any method (e.g., `persist()`, `find()`) is called on this proxy, it queries `TransactionSynchronizationManager` to retrieve or create the active `EntityManager` bound to the current `@Transactional` context.

```java
// Jakarta EE Enterprise Bean
@Stateless
public class JakartaJpaService {
    @PersistenceContext(unitName = "EnterprisePU")
    private EntityManager em;

    public void updateAccount(Long id, BigDecimal newBalance) {
        // Directly uses container-managed EntityManager bound to JTA
        Account account = em.find(Account.class, id);
        account.setBalance(newBalance);
    }
}

// Spring Boot Service
@Service
public class SpringJpaService {
    @PersistenceContext // Or @Autowired in modern Spring
    private EntityManager em;

    @Transactional
    public void updateAccount(Long id, BigDecimal newBalance) {
        // Invokes SharedEntityManagerCreator proxy, resolving thread-bound EntityManager
        Account account = em.find(Account.class, id);
        account.setBalance(newBalance);
    }
}
```

Spring's abstraction permits the identical code to run seamlessly outside an application server on lightweight JDBC transaction managers without requiring a full JTA provider.

---

### Question 7: What is JNDI and why is it used in enterprise applications?

**Answer:**
The Java Naming and Directory Interface (JNDI) is an enterprise API that provides naming and directory lookup capabilities. It enables Java applications to discover and access data and objects through unified hierarchical names, decoupling application code from deployment infrastructure configurations.

In enterprise application servers (such as WebLogic, WebSphere, and WildFly), operational resources such as JDBC connection pools, JMS queues, and mail sessions are configured and managed centrally by system administrators inside the server's management console or configuration files. The application simply looks up these resources by name (e.g., `java:comp/env/jdbc/OrderDS`).

This separation provides critical operational advantages:
- Infrastructure configurations (passwords, connection pool sizes, database cluster URLs) can be changed without re-compiling or modifying application code.
- Multiple applications deployed on the same server can share a single managed connection pool.
- Passwords and secrets remain encrypted within the application server's secure credential store.

```java
public class JndiDataSourceLookup {
    public Connection obtainManagedConnection() throws NamingException, SQLException {
        // Create initial naming context
        InitialContext context = new InitialContext();

        // Standard JNDI environment lookup
        DataSource ds = (DataSource) context.lookup("java:comp/env/jdbc/ProductionPostgresDS");

        // The returned connection is managed by the application server pool
        return ds.getConnection();
    }
}
```

In modern cloud-native architectures, JNDI has largely fallen out of favor. Spring Boot and container orchestration (Kubernetes) externalize configurations through environment variables, ConfigMaps, and properties files rather than centralized directory lookups.

---

### Question 8: What is the difference between JAX-RS and Spring MVC for REST APIs?

**Answer:**
JAX-RS (Jakarta RESTful Web Services) is a formal, vendor-neutral specification (JSR 370 / Jakarta REST) implemented by runtimes like Jersey, RESTEasy, and Apache CXF. Spring MVC is a comprehensive web framework built into the Spring Framework ecosystem.

Key architectural and syntactic differences include:

1. **Annotations:**
   - JAX-RS uses `@Path`, `@GET`, `@POST`, `@Produces`, `@Consumes`, `@PathParam`, and `@QueryParam`.
   - Spring MVC uses `@RequestMapping` (or `@GetMapping`, `@PostMapping`), `@PathVariable`, `@RequestParam`, and `@RequestBody`.
2. **Response Handling:**
   - JAX-RS relies heavily on the `Response` builder pattern (`Response.status(200).entity(body).build()`).
   - Spring MVC supports returning POJOs directly (serialized via Jackson), `ResponseEntity<T>`, or reactive `Mono`/`Flux`.
3. **Execution Model:**
   - JAX-RS implementations run as a servlet (e.g., Jersey's `ServletContainer`) or native filter.
   - Spring MVC funnels all incoming HTTP requests through a single front controller: `DispatcherServlet`.

```java
// JAX-RS Standard Implementation
@Path("/api/users")
@Produces(MediaType.APPLICATION_JSON)
public class JaxRsUserResource {
    @GET
    @Path("/{id}")
    public Response getUser(@PathParam("id") Long id) {
        UserProfile user = fetchUser(id);
        if (user == null) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }
        return Response.ok(user).header("X-Custom-Header", "Value").build();
    }
}

// Spring MVC Equivalent
@RestController
@RequestMapping("/api/users")
public class SpringMvcUserController {
    @GetMapping("/{id}")
    public ResponseEntity<UserProfile> getUser(@PathVariable Long id) {
        UserProfile user = fetchUser(id);
        if (user == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok().header("X-Custom-Header", "Value").body(user);
    }
}
```

Spring MVC is overwhelmingly preferred in modern microservices due to seamless integration with Spring Boot Actuator, Spring Data, and Spring Security.

---

### Question 9: What is JTA and how does it differ from resource-local transactions?

**Answer:**
The Java Transaction API (JTA / Jakarta Transactions) coordinates transactions across multiple heterogeneous transactional resources using a Two-Phase Commit (2PC) protocol, managed by an XA-compliant Transaction Manager. In contrast, Resource-Local transactions operate exclusively on a single transactional resource (such as a single JDBC connection or single JMS session).

In a Resource-Local transaction:
- The transaction boundary is tied directly to the underlying database connection (`connection.setAutoCommit(false)`, `connection.commit()`).
- High performance with minimal overhead.
- Cannot span multiple disparate systems (e.g., debiting a PostgreSQL database and sending a message to an IBM MQ broker atomically).

In a JTA transaction:
- A centralized Transaction Manager (such as Narayana, Atomikos, or Bitronix) coordinates multiple XA resources.
- Executes Two-Phase Commit:
  - Phase 1 (Prepare): The coordinator asks all participating resources if they can commit. Each resource locks rows/resources and logs intent.
  - Phase 2 (Commit): If all resources vote yes, the coordinator issues a global commit. If any fails, all rollback.

```java
@Stateless
public class MultiResourceBankingBean {

    @Resource(lookup = "java:comp/env/jdbc/CheckingAccountDS") // XA DataSource 1
    private DataSource checkingDs;

    @Resource(lookup = "java:comp/env/jdbc/SavingsAccountDS")  // XA DataSource 2
    private DataSource savingsDs;

    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public void transferCrossDatabase(Long fromId, Long toId, BigDecimal amount) {
        // Both database operations participate in the same global JTA transaction
        debitAccount(checkingDs, fromId, amount);
        creditAccount(savingsDs, toId, amount);
        // If either fails, the JTA transaction manager rolls back both databases
    }
}
```

JTA introduces latency and locking overhead, so modern microservice architectures generally avoid 2PC in favor of Saga patterns and eventual consistency.

---

### Question 10: What is a WAR file vs an EAR file?

**Answer:**
WAR (Web Application Archive) and EAR (Enterprise Application Archive) are standard Java enterprise archive formats defined by the Java EE/Jakarta EE specifications. Both use standard ZIP compression but serve fundamentally different deployment topologies.

1. **WAR (Web Application Archive):**
   - Designed to package a single web module.
   - Contains web resources (HTML, JSP, CSS, JavaScript), servlets, web filters, and REST controllers.
   - Standard internal layout:
     - `WEB-INF/web.xml`: Web deployment descriptor.
     - `WEB-INF/classes/`: Compiled application class files.
     - `WEB-INF/lib/`: Application-scoped JAR dependencies.
   - Can be deployed directly to lightweight servlet containers like Apache Tomcat and Jetty.
2. **EAR (Enterprise Application Archive):**
   - Designed to package an entire enterprise suite composed of multiple sub-modules.
   - Standard internal layout:
     - `META-INF/application.xml`: Enterprise deployment descriptor mapping modules.
     - Contains multiple WAR files (web portals, admin panels).
     - Contains multiple EJB JAR files (business beans, message consumers).
     - `lib/`: Shared enterprise libraries accessible across all contained WARs and EJBs.
   - Requires a full-profile application server (WebLogic, WebSphere, WildFly).

```xml
<!-- META-INF/application.xml inside an EAR file -->
<application xmlns="https://jakarta.ee/xml/ns/jakartaee" version="10">
    <display-name>EnterpriseBankingSuite</display-name>
    <module>
        <web>
            <web-uri>customer-web.war</web-uri>
            <context-root>/portal</context-root>
        </web>
    </module>
    <module>
        <ejb>banking-core-ejb.jar</ejb>
    </module>
</application>
```

In modern cloud computing, EAR files are obsolete. Microservices package single executable JARs with embedded servers, running inside isolated Docker containers.

---

### Question 11: Why were EJBs largely replaced by Spring beans?

**Answer:**
Enterprise JavaBeans (EJBs), particularly in EJB 1.x and 2.x, suffered from extreme complexity, heavyweight container coupling, slow development cycles, and intrusive programming models. The Spring Framework emerged specifically as a lightweight antidote to EJB pain points.

The primary drivers of EJB's replacement include:
1. **Intrusive Programming Model:** EJB 2.x required developers to implement multiple interfaces (`EJBObject`, `EJBHome`, `SessionBean`) and write verbose XML deployment descriptors (`ejb-jar.xml`) for every business component. Spring introduced Plain Old Java Objects (POJOs), allowing business logic to exist without framework inheritance.
2. **Heavy Container Dependency & Testing Pain:** EJBs could not run outside of heavy application servers like WebLogic or WebSphere. Unit testing an EJB required starting a full container or writing complex mocks. Spring beans could be instantiated and unit tested with standard JUnit and Mockito in milliseconds.
3. **Over-Engineered Distributed Computing:** EJB was architected around Remote Method Invocation (RMI), assuming business methods would be called across different physical servers. In practice, remote network calls introduced massive latency and serialization overhead. Spring focused on co-located POJOs connected via clean Dependency Injection.
4. **Declarative Services without EJB Overhead:** Spring introduced Aspect-Oriented Programming (AOP), delivering declarative transactions (`@Transactional`) and security on ordinary POJOs without requiring EJB containers.

```java
// EJB 2.x approach (Legacy Anti-pattern)
public class LegacyAccountBean implements SessionBean {
    public void ejbCreate() {}
    public void ejbActivate() {}
    public void ejbPassivate() {}
    public void ejbRemove() {}
    public void setSessionContext(SessionContext ctx) {}
    // Business logic entangled with container callbacks
}

// Spring POJO approach (Modern Clean Architecture)
@Service
public class ModernAccountService {
    @Transactional
    public void executeTransfer(Long from, Long to, BigDecimal amount) {
        // Pure domain logic, fully testable without application server
    }
}
```

Although EJB 3.0 simplified its model to use annotations, Spring had already captured the market with superior developer productivity.

---

### Question 12: How do you migrate a Servlet-based application to Spring MVC?

**Answer:**
Migrating a legacy Servlet-based web application to Spring MVC involves decomposing manual request parsing, session management, and response rendering into Spring's declarative controller architecture.

The step-by-step modernization strategy consists of:
1. **Introduce `DispatcherServlet`:** Configure Spring's `DispatcherServlet` to intercept application traffic, gradually replacing individual servlet mappings.
2. **Convert `HttpServlet` classes to `@RestController` / `@Controller`:**
   - Replace `doGet()` and `doPost()` with `@GetMapping` and `@PostMapping`.
   - Remove manual parsing of `HttpServletRequest.getParameter()` in favor of `@RequestParam` and typed `@PathVariable`.
   - Replace manual JSON serialization (e.g., writing strings to `response.getWriter()`) with typed DTO return types automatically handled by Jackson.
3. **Migrate Servlet Filters to Spring Filters or Interceptors:**
   - Convert `jakarta.servlet.Filter` classes into Spring `OncePerRequestFilter` or `HandlerInterceptor` components.
4. **Migrate JNDI / Manual Connection Logic to Spring Data:**
   - Replace raw JDBC queries inside servlets with Spring Data JPA repositories or `JdbcTemplate`.

```java
// Before: Legacy HttpServlet
@WebServlet("/api/v1/customer")
public class CustomerServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String idStr = req.getParameter("id");
        Long id = Long.parseLong(idStr);
        Customer customer = customerDao.findById(id);
        resp.setContentType("application/json");
        resp.getWriter().write("{\"id\":" + customer.getId() + ",\"name\":\"" + customer.getName() + "\"}");
    }
}

// After: Modern Spring MVC Controller
@RestController
@RequestMapping("/api/v1/customer")
public class CustomerController {
    private final CustomerService customerService;

    public CustomerController(CustomerService customerService) {
        this.customerService = customerService;
    }

    @GetMapping
    public CustomerDto getCustomer(@RequestParam Long id) {
        return customerService.findById(id); // Jackson handles JSON serialization automatically
    }
}
```

This migration eliminates manual error handling, enhances testability, and standardizes validation via `@Valid`.

---

### Question 13: What is the javax to jakarta namespace change and why did it happen?

**Answer:**
The transition from the `javax.*` namespace to `jakarta.*` is the most significant breaking change in the history of enterprise Java. It occurred as a legal and governance consequence of Oracle transferring Java EE to the Eclipse Foundation.

In 2017, Oracle transferred the management of Java EE specifications, test compatibility kits (TCKs), and reference implementations to the Eclipse Foundation. However, Oracle retained the commercial trademark for the word "Java". After extended negotiations, Oracle and the Eclipse Foundation agreed that:
- The platform could no longer be called "Java EE"; it was renamed **Jakarta EE**.
- The Eclipse Foundation was forbidden from modifying or evolving any specification under the `javax.*` package namespace.

To allow enterprise Java to evolve, the Eclipse Foundation executed a clean break:
- **Jakarta EE 8 (2019):** Maintained full binary compatibility with Java EE 8, retaining the `javax.*` namespace.
- **Jakarta EE 9 (2020):** Renamed all package namespaces from `javax.*` to `jakarta.*` (e.g., `javax.servlet` became `jakarta.servlet`, `javax.persistence` became `jakarta.persistence`). No new features were added; the sole purpose was executing the namespace migration.
- **Jakarta EE 10 / 11:** Continued introducing new features built entirely on `jakarta.*`.

```java
// Legacy Java EE 8 / Spring Boot 2.x
import javax.servlet.http.HttpServletRequest;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.validation.constraints.NotNull;

// Modern Jakarta EE / Spring Boot 3.x
import jakarta.servlet.http.HttpServletRequest;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.validation.constraints.NotNull;
```

This shift directly impacted the ecosystem: Spring Boot 3.0 (released in late 2022) made Jakarta EE 9/10 baseline, breaking compatibility with libraries still relying on `javax.*`.

---

### Question 14: How does async servlet processing work?

**Answer:**
Standard servlet processing is synchronous and thread-per-request: the worker thread allocated from the container thread pool remains blocked while the servlet performs long-running database queries, calls downstream REST services, or waits for file I/O. Under high concurrent traffic, this causes container thread pool exhaustion.

Asynchronous servlet processing (introduced in Servlet 3.0) resolves this by allowing the servlet thread to release itself back to the container pool while the long-running operation completes asynchronously on a separate thread pool.

The workflow proceeds as follows:
1. The servlet enables async support (`@WebServlet(asyncSupported = true)`).
2. The servlet initiates async processing by calling `request.startAsync()`, which returns an `AsyncContext`.
3. The original container thread exits the `service()` method and returns to the container pool to accept new incoming HTTP connections.
4. The background task executes on an independent application thread pool.
5. When the result is ready, the background thread writes the response using `AsyncContext.getResponse()` and calls `AsyncContext.complete()`.

```java
@WebServlet(urlPatterns = "/async-quote", asyncSupported = true)
public class AsyncQuoteServlet extends HttpServlet {
    private final ExecutorService workerPool = Executors.newFixedThreadPool(16);

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) {
        AsyncContext asyncContext = req.startAsync();
        asyncContext.setTimeout(5000); // 5 second timeout

        workerPool.submit(() -> {
            try {
                // Long-running non-blocking task
                String priceQuote = fetchPriceQuoteFromExternalService();
                HttpServletResponse response = (HttpServletResponse) asyncContext.getResponse();
                response.setContentType("application/json");
                response.getWriter().write("{\"quote\":" + priceQuote + "}");
            } catch (Exception e) {
                ((HttpServletResponse) asyncContext.getResponse()).setStatus(500);
            } finally {
                asyncContext.complete(); // Signals container that response is finished
            }
        });
    }

    private String fetchPriceQuoteFromExternalService() throws InterruptedException {
        Thread.sleep(1000);
        return "142.50";
    }
}
```

This architecture paved the way for modern reactive web engines and non-blocking I/O servlets.

---

### Question 15: What is the role of web.xml in a Jakarta EE application and is it still needed?

**Answer:**
`web.xml`, formally known as the Web Application Deployment Descriptor, is an XML configuration file located inside `WEB-INF/web.xml`. In early versions of the Servlet specification (Servlet 2.x and earlier), `web.xml` was strictly mandatory: it was the sole mechanism to register servlets, define URL mappings, configure servlet filters, register lifecycle listeners, declare security constraints, and set session timeout parameters.

With the introduction of Servlet 3.0 (and continuing in Jakarta EE 9/10/11), `web.xml` became optional. The container automatically discovers components using metadata annotations:
- `@WebServlet` replaces `<servlet>` and `<servlet-mapping>`.
- `@WebFilter` replaces `<filter>` and `<filter-mapping>`.
- `@WebListener` replaces `<listener>`.
- Programmatic configuration via `ServletContainerInitializer` or Spring's `WebApplicationInitializer`.

```xml
<!-- Example of legacy web.xml configuration -->
<web-app xmlns="https://jakarta.ee/xml/ns/jakartaee" version="6.0">
    <display-name>CoreInventorySystem</display-name>

    <servlet>
        <servlet-name>InventoryServlet</servlet-name>
        <servlet-class>com.example.InventoryServlet</servlet-class>
    </servlet>

    <servlet-mapping>
        <servlet-name>InventoryServlet</servlet-name>
        <url-pattern>/inventory/*</url-pattern>
    </servlet-mapping>

    <session-config>
        <session-timeout>30</session-timeout>
        <cookie-config>
            <http-only>true</http-only>
            <secure>true</secure>
        </cookie-config>
    </session-config>
</web-app>
```

**Is it still needed today?**
In modern Spring Boot and cloud-native applications, `web.xml` is never needed. Spring Boot registers servlets and filters programmatically using embedded Tomcat configuration beans (`ServletRegistrationBean`, `FilterRegistrationBean`). In traditional Jakarta EE WAR deployments, `web.xml` is only retained when developers need to enforce global session security flags, define absolute filter execution ordering, or override annotations without modifying compiled class files.

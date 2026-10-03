# Jakarta EE and J2EE Cheatsheet

---

## 1. Jakarta EE vs Spring Framework Comparison

| Feature Category | Jakarta EE | Spring Framework |
|---|---|---|
| Dependency Injection | `@Inject`, `@Named`, `@ApplicationScoped` | `@Autowired`, `@Component`, `@Service` |
| REST API Resource | `@Path`, `@GET`, `@Produces`, `@Consumes` | `@RestController`, `@GetMapping`, `@PostMapping` |
| Persistence / ORM | `@PersistenceContext`, `persistence.xml` | `JpaRepository`, `spring.datasource.*` |
| Transaction Demarcation | `@Transactional(TxType.REQUIRED)` | `@Transactional(propagation = Propagation.REQUIRED)` |
| Validation | `@NotNull`, `@Size`, `@Valid` | `@NotNull`, `@Size`, `@Valid` (via Jakarta Validator) |
| Asynchronous Task | `@Asynchronous` | `@Async` |
| Application Lifecycle | `@Startup`, `ServletContextListener` | `@PostConstruct`, `ApplicationReadyEvent` |

---

## 2. Servlet Core Annotations

| Annotation | Target | Purpose | Key Attributes |
|---|---|---|---|
| `@WebServlet` | Type | Declares and maps an HTTP servlet | `name`, `urlPatterns`, `loadOnStartup`, `asyncSupported` |
| `@WebFilter` | Type | Declares an HTTP request/response filter | `filterName`, `urlPatterns`, `dispatcherTypes` |
| `@WebListener` | Type | Registers context, session, or request listeners | None |
| `@WebInitParam` | Nested | Defines key-value servlet/filter init params | `name`, `value` |
| `@MultipartConfig` | Type | Configures multipart/form-data upload handling | `location`, `maxFileSize`, `maxRequestSize` |

---

## 3. CDI Scopes Reference

| Scope Annotation | Lifecycle Boundary | State Retention | Proxy Injected? |
|---|---|---|---|
| `@RequestScoped` | Single HTTP request or worker event | Thread-isolated; discarded after request | Yes (Client Proxy) |
| `@SessionScoped` | Single `HttpSession` | User-isolated; must be `Serializable` | Yes (Client Proxy) |
| `@ApplicationScoped` | Application JVM runtime | Shared across all threads and clients | Yes (Client Proxy) |
| `@ConversationScoped`| Demarcated multi-step user flow | Explicitly started/ended via `Conversation` | Yes (Client Proxy) |
| `@Dependent` | Matches the injecting client instance | Bound to enclosing lifecycle (default) | No (Direct Reference) |

---

## 4. EJB Component Types

| EJB Annotation | State Model | Concurrency Control | Primary Use Case |
|---|---|---|---|
| `@Stateless` | No client state; pooled | Container serialized access per instance | Transactional business services |
| `@Stateful` | Client-bound state across calls | Passivated to disk upon memory pressure | Conversational workflows (legacy checkout) |
| `@Singleton` | Single shared instance | `@Lock(LockType.READ)` / `@Lock(WRITE)` | Application cache, global registry |
| `@MessageDriven`| Stateless message listener | Container pool consuming from destination | Asynchronous JMS message consumers |

---

## 5. JAX-RS (REST) Annotations

| JAX-RS Annotation | Target | HTTP Mapping / Functional Meaning |
|---|---|---|
| `@Path("/resource")` | Class / Method | Declares URI routing pattern |
| `@GET`, `@POST`, `@PUT`, `@DELETE` | Method | Binds method to specific HTTP verb |
| `@Produces(MediaType.JSON)` | Class / Method | Response serialization format (`Content-Type`) |
| `@Consumes(MediaType.JSON)` | Class / Method | Accepted incoming request body format |
| `@PathParam("id")` | Parameter | Extracts variable from URI template |
| `@QueryParam("limit")` | Parameter | Extracts URL query parameter string |
| `@HeaderParam("X-Auth")` | Parameter | Extracts HTTP request header |
| `@Provider` | Class | Registers custom `ExceptionMapper`, filter, or interceptor |

---

## 6. JMS Messaging Types

| JMS Entity / Model | Cardinality | Persistence / Delivery Guarantee | Typical Enterprise Use |
|---|---|---|---|
| `Queue` (Point-to-Point) | 1:1 (Single consumer) | Retained until acknowledged by receiver | Asynchronous order/task execution |
| `Topic` (Pub/Sub) | 1:N (All subscribers) | Non-durable lost if offline; durable stored | Market data, cache invalidation alerts |
| `TextMessage` | Payload | String / JSON / XML payload | Enterprise payload interchange |
| `BytesMessage` | Payload | Uninterpreted stream of binary bytes | High-performance binary transfer |
| `JMSContext` | Session / Connection | AutoCloseable API for producing/consuming | JMS 2.0+ unified messaging API |

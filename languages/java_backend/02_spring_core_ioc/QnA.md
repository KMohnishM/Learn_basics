# Spring Core & IoC: Interview Questions and Answers

---

### Question 1: What is the difference between IoC and Dependency Injection?

**Answer:**
Inversion of Control (IoC) is a high-level architectural design principle where the custom-written portions of a computer program receive the flow of control from a generic, reusable framework. In traditional procedural programming, the main application code drives execution and decides when to instantiate classes and call library functions. Under IoC, the framework acts as the driver and calls application code at designated extension points (the Hollywood Principle: "Don't call us, we'll call you").

Dependency Injection (DI) is a specific subtype and design pattern implementing Inversion of Control. Under Dependency Injection, the responsibility of creating and wiring dependent objects is extracted away from the dependent object itself and transferred to an external assembler or container (such as Spring's `ApplicationContext`).

Without DI, a class instantiates its collaborators directly using constructors:
```java
public class UserService {
    // Tight coupling: Cannot substitute mock for testing without source changes
    private final UserRepository repository = new JdbcUserRepository();
}
```

With Dependency Injection, dependencies are provided externally:
```java
@Service
public class UserService {
    private final UserRepository repository;

    // IoC container injects collaborator at runtime
    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

In summary: IoC defines the broad architectural paradigm of reversing control flow, whereas Dependency Injection is the concrete creational pattern used by Spring to supply dependencies to managed components.

---

### Question 2: Explain the full Spring Bean lifecycle from instantiation to destruction.

**Answer:**
The Spring bean lifecycle encompasses the entire sequence of operations that the IoC container performs on a bean from class instantiation until destruction during container shutdown. Understanding this sequence is vital when writing infrastructure extensions or troubleshooting initialization timing issues.

The complete lifecycle progresses through nine distinct phases:
1. **Instantiation**: The container creates the bean instance via reflection using its constructor or factory method.
2. **Populate Properties**: Dependencies declared via constructor, setter, or fields are resolved and injected into the bean instance.
3. **Aware Interfaces**: If the bean implements Spring Aware interfaces, the container invokes:
   - `BeanNameAware.setBeanName(String name)`
   - `BeanClassLoaderAware.setBeanClassLoader(ClassLoader loader)`
   - `BeanFactoryAware.setBeanFactory(BeanFactory factory)`
   - `ApplicationContextAware.setApplicationContext(ApplicationContext context)`
4. **BeanPostProcessor Pre-Initialization**: All registered `BeanPostProcessor` beans have their `postProcessBeforeInitialization()` method invoked on the instance.
5. **Initialization Callbacks**: Custom initialization routines run in the following priority order:
   - Methods annotated with `@PostConstruct`
   - `InitializingBean.afterPropertiesSet()`
   - Custom `init-method` declared via `@Bean(initMethod = "init")`
6. **BeanPostProcessor Post-Initialization**: `postProcessAfterInitialization()` is invoked. This phase creates AOP dynamic proxies (`@Transactional`, `@Async`, custom aspects).
7. **Ready for Use**: The bean is placed into the container cache and made available for injection into application components.
8. **Container Shutdown**: The container begins graceful termination.
9. **Destruction Callbacks**: Destruction hooks execute in the following order:
   - Methods annotated with `@PreDestroy`
   - `DisposableBean.destroy()`
   - Custom `destroy-method` declared via `@Bean(destroyMethod = "cleanup")`

```java
@Component
public class LifecycleDemonstrationBean implements InitializingBean, DisposableBean {

    @PostConstruct
    public void postConstructCallback() {
        System.out.println("Phase 5a: @PostConstruct invoked");
    }

    @Override
    public void afterPropertiesSet() {
        System.out.println("Phase 5b: InitializingBean.afterPropertiesSet invoked");
    }

    @PreDestroy
    public void preDestroyCallback() {
        System.out.println("Phase 9a: @PreDestroy invoked");
    }

    @Override
    public void destroy() {
        System.out.println("Phase 9b: DisposableBean.destroy invoked");
    }
}
```

---

### Question 3: Why is field injection with @Autowired considered bad practice?

**Answer:**
Field injection injects dependencies directly into private fields using reflection by placing `@Autowired` on the field declaration. While it minimizes lines of code, it introduces critical software design flaws and is strongly discouraged in production Spring architectures:

1. **Violates Immutability**: Fields annotated with `@Autowired` cannot be declared `final`, meaning their references can be reassigned during the bean's runtime lifecycle.
2. **Hides Dependencies from Public API**: A consumer of the class cannot tell what dependencies it requires without reading the private implementation details.
3. **Blocks Plain Unit Testing**: You cannot instantiate the class in a standard JUnit test using `new UserService(...)`. You are forced to either initialize an entire Spring context (making tests slow) or use reflection hacks like `ReflectionTestUtils`.
4. **Masks SRP Violations**: With constructor injection, adding a 7th or 8th dependency creates an ugly constructor with too many arguments, immediately signaling a Single Responsibility Principle violation. Field injection hides this anti-pattern.

```java
// BAD: Field Injection
@Service
public class BadOrderService {
    @Autowired private PaymentClient paymentClient; // Non-final, hidden, reflection-bound
}

// GOOD: Constructor Injection
@Service
public class GoodOrderService {
    private final PaymentClient paymentClient;

    public GoodOrderService(PaymentClient paymentClient) {
        this.paymentClient = Objects.requireNonNull(paymentClient, "paymentClient required");
    }
}
```

Constructor injection guarantees immutability, fail-fast compilation, and trivial unit test mocking.

---

### Question 4: What is the difference between @Component, @Service, @Repository, and @Controller?

**Answer:**
All four annotations are component stereotypes in Spring, and each is annotated with `@Component` as a meta-annotation. Therefore, any class marked with `@Service`, `@Repository`, or `@Controller` is discovered and registered as a Spring bean during component scanning.

However, each stereotype carries distinct semantic roles and runtime behavior:
- `@Component`: The generic baseline stereotype for any Spring-managed class or infrastructure utility that does not fit into a domain architectural layer.
- `@Repository`: Designates classes in the persistence layer (DAOs, database access classes). Crucially, Spring registers a `PersistenceExceptionTranslationPostProcessor` that intercepts methods in `@Repository` beans and automatically translates native database exceptions (like `SQLException`, `HibernateException`, or `MongoException`) into Spring's consistent `DataAccessException` hierarchy.
- `@Service`: Designates classes in the business logic layer. It serves semantic intent, indicating where business transactions, domain orchestrations, and application security rules belong.
- `@Controller` / `@RestController`: Designates the presentation layer. In Spring MVC and REST APIs, these handle incoming HTTP requests, map path variables and request bodies, and return views or JSON payloads.

```java
// Presentation Layer
@RestController
@RequestMapping("/api/orders")
public class OrderApiController {
    private final OrderService orderService;
    public OrderApiController(OrderService orderService) { this.orderService = orderService; }
}

// Business Layer
@Service
@Transactional
public class OrderService {
    private final OrderRepository orderRepository;
    public OrderService(OrderRepository orderRepository) { this.orderRepository = orderRepository; }
}

// Persistence Layer: Automatic exception translation enabled
@Repository
public class OrderRepository {
    public void persist(Order order) { /* native JPA or JDBC operations */ }
}
```

---

### Question 5: How do you handle multiple beans of the same type with @Qualifier and @Primary?

**Answer:**
When multiple beans implement the same interface or extend the same base class, Spring's autowiring mechanism fails with a `NoUniqueBeanDefinitionException` unless instructed on which bean to select. Spring resolves this ambiguity using `@Primary` and `@Qualifier`.

- `@Primary`: Declares a default fallback bean candidate among several implementations. When an injection point requests the interface without specifying a qualifier, Spring selects the `@Primary` bean.
- `@Qualifier("beanName")`: Explicitly identifies the target bean by name or custom annotation at both the bean definition and injection site, overriding any `@Primary` defaults.

```java
public interface PaymentGateway {
    void process(double amount);
}

@Component
@Primary
public class StripePaymentGateway implements PaymentGateway {
    @Override public void process(double amount) { System.out.println("Charging Stripe: " + amount); }
}

@Component("paypal")
public class PayPalPaymentGateway implements PaymentGateway {
    @Override public void process(double amount) { System.out.println("Charging PayPal: " + amount); }
}

@Service
public class CheckoutManager {
    private final PaymentGateway defaultGateway;
    private final PaymentGateway paypalGateway;

    public CheckoutManager(
            PaymentGateway defaultGateway, // Injects StripePaymentGateway because it is marked @Primary
            @Qualifier("paypal") PaymentGateway paypalGateway // Explicitly injects PayPalPaymentGateway
    ) {
        this.defaultGateway = defaultGateway;
        this.paypalGateway = paypalGateway;
    }
}
```

Using custom qualifier annotations (e.g., `@PayPalGateway`) is also recommended to eliminate brittle hardcoded string names.

---

### Question 6: What is the difference between singleton and prototype bean scope?

**Answer:**
The bean scope determines the instantiation frequency, caching policy, and lifecycle management applied by the Spring container:

1. **Singleton Scope (Default)**:
   - Exactly one shared instance is created per Spring `ApplicationContext`.
   - The instance is created eagerly at container startup (unless explicitly marked `@Lazy`).
   - The single shared instance is cached in the container's singleton registry and reused for every subsequent injection or `getBean()` invocation.
   - The container completely manages its lifecycle, including `@PostConstruct` and `@PreDestroy` callbacks.
   - Singleton beans must be stateless or strictly thread-safe.

2. **Prototype Scope**:
   - A new instance is created every single time the bean is requested via injection or `getBean()`.
   - The instance is created lazily when requested.
   - The container does not cache the instance.
   - **Crucial Lifecycle Exception**: Spring instantiates, configures, and invokes `@PostConstruct` on prototype beans, but **does not invoke `@PreDestroy` callbacks**. The calling client is solely responsible for resource cleanup.

```java
@Component
@Scope("prototype")
public class TaskWorker {
    private final UUID workerId = UUID.randomUUID();
    public UUID getWorkerId() { return workerId; }
}

@Component
public class WorkerDispatcher {
    private final ObjectProvider<TaskWorker> workerProvider;

    public WorkerDispatcher(ObjectProvider<TaskWorker> workerProvider) {
        this.workerProvider = workerProvider;
    }

    public void dispatch() {
        // Generates two completely distinct instances
        TaskWorker worker1 = workerProvider.getObject();
        TaskWorker worker2 = workerProvider.getObject();
        System.out.println(worker1.getWorkerId().equals(worker2.getWorkerId())); // false
    }
}
```

---

### Question 7: How does Spring AOP work under the hood — JDK dynamic proxy vs CGLIB?

**Answer:**
Spring AOP is proxy-based. When a bean is targeted by an aspect (or annotations like `@Transactional` or `@Async`), Spring does not alter the compiled class bytecode. Instead, during the `BeanPostProcessor.postProcessAfterInitialization()` lifecycle phase, Spring wraps the target bean in a dynamic proxy that intercepts method calls, executes advice, and delegates to the target object.

Spring AOP employs two underlying proxy mechanisms:

1. **JDK Dynamic Proxies**:
   - Built into the standard Java runtime (`java.lang.reflect.Proxy`).
   - Can only proxy classes that implement one or more interfaces.
   - Generates a proxy class implementing the target interfaces. If code attempts to cast the proxy to the target concrete implementation class, a `ClassCastException` is thrown.

2. **CGLIB Dynamic Proxies**:
   - Uses bytecode generation library (repackaged inside `spring-core`) to generate a dynamic subclass of the target class at runtime.
   - Does not require interfaces; can proxy classes directly.
   - Cannot intercept `final` classes or `final` methods because subclasses cannot override them.
   - **Default behavior**: Spring Boot 2.x and 3.x default to CGLIB proxies (`spring.aop.proxy-target-class=true`).

```java
// Target interface and class
public interface AuditService { void logAction(String action); }

@Service
public class AuditServiceImpl implements AuditService {
    @Override public void logAction(String action) { System.out.println("Logged: " + action); }
}

// Behind the scenes in BeanPostProcessor:
// JDK Proxy: class $Proxy12 implements AuditService { ... }
// CGLIB Proxy: class AuditServiceImpl$$EnhancerBySpringCGLIB$$ extends AuditServiceImpl { ... }
```

---

### Question 8: What is a BeanPostProcessor and when would you write a custom one?

**Answer:**
A `BeanPostProcessor` (BPP) is an internal SPI interface in the Spring container that allows developers to implement custom modification or wrapping logic for new bean instances. Unlike regular beans, BPPs are instantiated very early during container startup so they can intercept all subsequent bean instantiations.

The interface defines two callback methods:
- `postProcessBeforeInitialization(Object bean, String name)`: Executes before any initialization callbacks (such as `@PostConstruct` or `afterPropertiesSet`).
- `postProcessAfterInitialization(Object bean, String name)`: Executes after all initialization callbacks. This is where proxies are created.

Write a custom `BeanPostProcessor` when developing infrastructure libraries, custom annotation processors, automated security validation, or custom profiling proxies.

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface Monitored {}

@Component
public class PerformanceMonitoringBpp implements BeanPostProcessor {

    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) throws BeansException {
        if (bean.getClass().isAnnotationPresent(Monitored.class)) {
            // Wrap the target bean in a custom dynamic proxy
            return Proxy.newProxyInstance(
                    bean.getClass().getClassLoader(),
                    bean.getClass().getInterfaces(),
                    (proxy, method, args) -> {
                        long start = System.currentTimeMillis();
                        try {
                            return method.invoke(bean, args);
                        } finally {
                            System.out.println(method.getName() + " took " + (System.currentTimeMillis() - start) + "ms");
                        }
                    }
            );
        }
        return bean; // Return unmodified bean if annotation is absent
    }
}
```

---

### Question 9: How do @ConditionalOnMissingBean and @ConditionalOnProperty work?

**Answer:**
Both `@ConditionalOnMissingBean` and `@ConditionalOnProperty` are conditional registration annotations used heavily in Spring Boot auto-configuration modules to dynamically decide whether a bean should be registered in the `ApplicationContext`.

1. **`@ConditionalOnProperty`**: Checks the environment (`application.properties`, environment variables) for a specific configuration key and value.
   - `name`: Property key to inspect.
   - `havingValue`: Target value required for bean registration.
   - `matchIfMissing`: Defines whether the condition succeeds if the property is not defined at all.

2. **`@ConditionalOnMissingBean`**: Inspects the container to check if a bean of the specified type or name has already been registered (for example, by user code). If found, this auto-configured bean definition is skipped. This allows users to easily override framework defaults simply by defining their own `@Bean`.

```java
@Configuration
public class NotificationAutoConfiguration {

    // Registers SendGrid client only if explicitly enabled via properties
    @Bean
    @ConditionalOnProperty(name = "notification.provider", havingValue = "sendgrid", matchIfMissing = false)
    public NotificationClient sendGridClient() {
        return new SendGridClient();
    }

    // Default fallback: Only registered if the user has NOT provided their own NotificationClient bean
    @Bean
    @ConditionalOnMissingBean(NotificationClient.class)
    public NotificationClient fallbackLogClient() {
        return new LoggingNotificationClient();
    }
}
```

This pattern provides opinionated defaults out of the box while allowing full user customizability without code conflicts.

---

### Question 10: What is the difference between @Value and @ConfigurationProperties?

**Answer:**
Both `@Value` and `@ConfigurationProperties` inject configuration data into Spring components, but they differ significantly in architecture, type safety, and scalability:

1. **`@Value`**:
   - Injects values on an individual field or constructor parameter basis.
   - Evaluates SpEL expressions (`#{...}`) and property placeholders (`${...}`).
   - Does not support relaxed binding (the property string must match exactly).
   - Prone to typos that are only detected at runtime when the specific component loads.
   - Unwieldy when dealing with hierarchical configurations containing dozens of properties.

2. **`@ConfigurationProperties`**:
   - Binds an entire prefix subtree of configuration properties to a structured POJO or Java Record.
   - Supports relaxed binding (e.g., `max-connections`, `maxConnections`, `MAX_CONNECTIONS` all map to `maxConnections`).
   - Supports standard JSR-380 validation (`@Validated`, `@Min`, `@NotNull`, `@Pattern`).
   - IDE auto-completion support via `spring-boot-configuration-processor`.

```java
// @Value approach: Fragmented, no relaxed binding
@Component
public class LegacyClient {
    @Value("${client.timeout:5000}")
    private int timeout;
}

// @ConfigurationProperties approach: Structured, validated, type-safe
@ConfigurationProperties(prefix = "client")
@Validated
public record ClientProperties(
        @NotBlank String endpoint,
        @Min(100) @Max(10000) int timeoutMillis,
        boolean enableTls
) {}
```

Modern Spring Boot applications favor `@ConfigurationProperties` for complex settings and reserve `@Value` strictly for simple one-off flags.

---

### Question 11: How does the Spring Event system work with @EventListener?

**Answer:**
The Spring Event system provides an in-process publish-subscribe messaging mechanism that decouples domain orchestrations from secondary side effects (such as sending notifications, writing audit records, or invalidating caches).

The system consists of three architectural components:
1. **Event Object**: An immutable data carrier (typically a Java Record) encapsulating the domain event payload.
2. **Publisher**: Any Spring bean can inject `ApplicationEventPublisher` and invoke `.publishEvent(eventObject)`.
3. **Listeners**: Any managed bean method annotated with `@EventListener(PayloadType.class)`.

By default, event listeners execute **synchronously on the caller thread** within the same transaction. Adding `@Async` runs the listener concurrently on a separate background thread pool.

```java
// 1. Immutable Event
public record UserRegisteredEvent(String userId, String email, Instant createdAt) {}

// 2. Publisher
@Service
public class RegistrationService {
    private final ApplicationEventPublisher eventPublisher;

    public RegistrationService(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }

    public void register(String email) {
        String userId = UUID.randomUUID().toString();
        // Domain logic...
        eventPublisher.publishEvent(new UserRegisteredEvent(userId, email, Instant.now()));
    }
}

// 3. Listener
@Component
public class WelcomeEmailNotifier {
    @EventListener
    @Async // Runs asynchronously in background thread
    public void onUserRegistered(UserRegisteredEvent event) {
        System.out.println("Sending welcome email to: " + event.email());
    }
}
```

---

### Question 12: What happens when you have a circular dependency between Spring beans?

**Answer:**
A circular dependency occurs when Bean A requires Bean B, and Bean B directly or indirectly requires Bean A.

When using **constructor injection**, Spring detects the cycle during container startup when attempting to instantiate the beans. To construct Bean A, it needs an instance of Bean B; but to construct Bean B, it needs an instance of Bean A. Because neither constructor can complete, Spring halts startup and throws a `BeanCurrentlyInCreationException`.

Since Spring Boot 2.6, circular dependencies are **prohibited by default**. The container fails fast on startup rather than attempting implicit workarounds.

```java
// Fails with BeanCurrentlyInCreationException on startup:
@Service
public class OrderService {
    public OrderService(BillingService billing) {}
}

@Service
public class BillingService {
    public BillingService(OrderService order) {}
}

// Temporary Workaround (Not recommended as permanent architecture):
@Service
public class BillingService {
    private final OrderService order;
    public BillingService(@Lazy OrderService order) { // Injects a synthetic proxy to break construction deadlock
        this.order = order;
    }
}
```

**Permanent Solutions:**
1. **Refactor and extract shared logic**: Create a third service (`InvoiceCalculator`) containing the shared behavior, and inject it into both services.
2. **Decouple via Application Events**: Instead of `BillingService` calling `OrderService` directly, publish an event and listen asynchronously.

---

### Question 13: What is the difference between BeanFactoryPostProcessor and BeanPostProcessor?

**Answer:**
Both interfaces allow customization of the Spring IoC container, but they operate at fundamentally different abstraction levels and stages of container bootstrap:

1. **`BeanFactoryPostProcessor` (BFPP)**:
   - Operates on bean **configuration metadata** (`BeanDefinition` objects), before any actual bean instances are created.
   - Can inspect and modify bean definitions (e.g., change property values, mark beans lazy, alter bean classes).
   - Example built-in BFPP: `PropertySourcesPlaceholderConfigurer` (resolves `${...}` placeholders in configuration metadata).

2. **`BeanPostProcessor` (BPP)**:
   - Operates on **bean instances** after they have been instantiated by the container.
   - Executes around initialization methods (`@PostConstruct`, `afterPropertiesSet`).
   - Can wrap beans in dynamic proxies, modify bean internal state, or register metrics.
   - Example built-in BPP: `CommonAnnotationBeanPostProcessor` (processes `@PostConstruct` and `@PreDestroy`), `AbstractAutoProxyCreator` (creates AOP and `@Transactional` proxies).

```java
// BFPP: Operates on metadata before instances exist
@Component
public class MetadataModifier implements BeanFactoryPostProcessor {
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory factory) {
        BeanDefinition def = factory.getBeanDefinition("myService");
        def.setScope(BeanDefinition.SCOPE_PROTOTYPE);
    }
}

// BPP: Operates on initialized instances
@Component
public class InstanceModifier implements BeanPostProcessor {
    @Override
    public Object postProcessAfterInitialization(Object bean, String name) {
        System.out.println("Bean initialized: " + name);
        return bean;
    }
}
```

---

### Question 14: How does @Scope("prototype") with scoped proxy work?

**Answer:**
When a short-lived bean (such as `prototype`, `request`, or `session` scope) is injected into a `singleton` bean, an architectural impedance mismatch occurs. Because the singleton bean is instantiated only once at startup, its dependencies are injected only once. Consequently, without special handling, the singleton would hold onto the exact same prototype instance for the entire application lifetime, defeating the purpose of prototype scope.

Applying a scoped proxy (`proxyMode = ScopedProxyMode.TARGET_CLASS`) resolves this problem. Instead of injecting the real prototype instance directly, Spring injects a lightweight CGLIB proxy.

Whenever the singleton invokes any method on this proxy, the proxy intercepts the method call, requests a brand-new prototype instance from the `BeanFactory`, invokes the target method on that fresh instance, and returns the result.

```java
@Component
@Scope(value = ConfigurableBeanFactory.SCOPE_PROTOTYPE, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class RequestTokenGenerator {
    private final UUID token = UUID.randomUUID();
    public UUID getToken() { return token; }
}

@Service
public class AuthenticationService {
    // Injected with CGLIB proxy, NOT a fixed raw instance!
    private final RequestTokenGenerator tokenGenerator;

    public AuthenticationService(RequestTokenGenerator tokenGenerator) {
        this.tokenGenerator = tokenGenerator;
    }

    public void processTwoLogins() {
        // Each call to getToken() on the proxy fetches a new prototype instance behind the scenes
        System.out.println(tokenGenerator.getToken()); // Token A
        System.out.println(tokenGenerator.getToken()); // Token B (Different UUID!)
    }
}
```

---

### Question 15: Explain how @Configuration and @Bean work together vs component scanning.

**Answer:**
In Spring, bean definitions can be created using two primary paradigms: explicit Java configuration (`@Configuration` + `@Bean`) and implicit component scanning (`@ComponentScan` + `@Component` stereotypes).

1. **`@Configuration` and `@Bean` (Explicit Configuration)**:
   - A `@Configuration` class is a source of bean definitions where methods annotated with `@Bean` return instances managed by the container.
   - Spring enhances `@Configuration` classes using CGLIB. When one `@Bean` method calls another `@Bean` method in the same configuration class, the CGLIB proxy intercepts the invocation and returns the cached singleton bean from the container rather than re-executing the Java method.
   - **Best used for**: Third-party classes where you cannot add `@Component` annotations (e.g., configuring `HikariDataSource`, `RedisTemplate`, or external SDK clients), and when complex conditional construction logic is required.

2. **Component Scanning (Implicit Configuration)**:
   - The container automatically scans classpath packages for classes annotated with `@Component`, `@Service`, `@Repository`, or `@Controller`.
   - **Best used for**: First-party application code (controllers, services, repositories) written and maintained by your team.

```java
// 1. Explicit Configuration: Configuring third-party libraries
@Configuration
public class ExternalClientConfig {
    @Bean
    public S3Client amazonS3Client() {
        return S3Client.builder().region(Region.US_EAST_1).build();
    }
}

// 2. Component Scanning: First-party domain code
@Service
public class DocumentArchiveService {
    private final S3Client s3Client; // Injected from @Bean definition above
    public DocumentArchiveService(S3Client s3Client) {
        this.s3Client = s3Client;
    }
}
```

Modern Spring architectures combine both: component scanning manages internal domain components, while `@Configuration` classes manage third-party integrations and infrastructural beans.

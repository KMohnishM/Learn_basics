# Spring Core and Inversion of Control (IoC)

This module delivers an exhaustive, production-grade guide to the foundational architecture of the Spring Framework. It covers the Inversion of Control container, bean lifecycle mechanics, advanced dependency injection, configuration strategies, Spring Expression Language (SpEL), and Aspect-Oriented Programming (AOP).

---

## Table of Contents
1. [Inversion of Control (IoC) and Dependency Injection (DI)](#1-inversion-of-control-ioc-and-dependency-injection-di)
2. [Spring ApplicationContext and Bean Factory Architecture](#2-spring-applicationcontext-and-bean-factory-architecture)
3. [Bean Definition and Component Scanning](#3-bean-definition-and-component-scanning)
4. [Dependency Injection Types and Best Practices](#4-dependency-injection-types-and-best-practices)
5. [Bean Scopes and Scoped Proxies](#5-bean-scopes-and-scoped-proxies)
6. [The Complete Spring Bean Lifecycle](#6-the-complete-spring-bean-lifecycle)
7. [Conditional Bean Registration](#7-conditional-bean-registration)
8. [Resolving Ambiguity: `@Qualifier` and `@Primary`](#8-resolving-ambiguity-qualifier-and-primary)
9. [Customizing the Container: `BeanPostProcessor` and `BeanFactoryPostProcessor`](#9-customizing-the-container-beanpostprocessor-and-beanfactorypostprocessor)
10. [Application Events and Decoupled Communication](#10-application-events-and-decoupled-communication)
11. [Spring Expression Language (SpEL)](#11-spring-expression-language-spel)
12. [Configuration Properties and Environment Abstraction](#12-configuration-properties-and-environment-abstraction)
13. [Aspect-Oriented Programming (AOP) Under the Hood](#13-aspect-oriented-programming-aop-under-the-hood)
14. [Circular Dependencies: Detection, Prevention, and Refactoring](#14-circular-dependencies-detection-prevention-and-refactoring)

---

## 1. Inversion of Control (IoC) and Dependency Injection (DI)

### The Architectural Problem IoC Solves

In traditional procedural or unmanaged object-oriented software, a component directly instantiates its own dependencies using the `new` operator:

```java
// Tightly coupled architecture
public class OrderService {
    private final OrderRepository repository = new PostgresOrderRepository();
    private final NotificationClient notifier = new SendGridEmailClient();
}
```

This direct instantiation introduces severe architectural liabilities:
1. **Tight Coupling**: `OrderService` is permanently bound to specific concrete implementations (`PostgresOrderRepository` and `SendGridEmailClient`).
2. **Untestable Code**: Unit testing `OrderService` in isolation is impossible without connecting to a live PostgreSQL database and SendGrid API.
3. **Configuration Sprawl**: Changes to dependency construction arguments ripple through every consuming class across the codebase.

### The Hollywood Principle

Inversion of Control inverts the flow of control. Instead of the application component driving execution and pulling dependencies, the container manages lifecycle and pushes dependencies into the component. This is often summarized as the **Hollywood Principle**: *"Don't call us, we'll call you."*

### IoC vs Dependency Injection

- **Inversion of Control (IoC)** is a broad architectural design principle wherein the framework controls program flow (e.g., event loops, GUI frameworks, template method patterns, and component containers).
- **Dependency Injection (DI)** is a specific design pattern implementing IoC. In DI, an external assembler (the IoC container) injects references to dependent objects into a client object during instantiation.

---

## 2. Spring ApplicationContext and Bean Factory Architecture

The Spring IoC engine consists of two fundamental interfaces: `BeanFactory` and `ApplicationContext`.

```
BeanFactory (Low-level configuration mechanism, lazy loading)
    └── ListableBeanFactory
            └── HierarchicalBeanFactory
                    └── ApplicationContext (Enterprise-ready container)
                            ├── AnnotationConfigApplicationContext
                            ├── ClassPathXmlApplicationContext
                            └── WebApplicationContext
```

### Core Implementations

1. **`BeanFactory`**: The root interface providing the fundamental configuration mechanism and basic bean retrieval (`getBean()`). Beans are loaded lazily on demand.
2. **`ApplicationContext`**: A complete superset of `BeanFactory`. It introduces:
   - Eager pre-instantiation of singleton beans during startup.
   - Internationalization and message resolution (`MessageSource`).
   - Integrated event publishing mechanism (`ApplicationEventPublisher`).
   - Environment and property management (`EnvironmentCapable`).
   - Resource loading capabilities (`ResourceLoader`).

### Concrete Implementations

- **`AnnotationConfigApplicationContext`**: Used in modern standalone Java applications and Spring Boot. Scans annotations such as `@Configuration` and `@Component`.
- **`ClassPathXmlApplicationContext`**: Legacy container that parses XML files located on the application classpath.
- **`GenericWebApplicationContext`**: Web-aware context providing request, session, and application scopes.

### Standalone Context Bootstrap Example

```java
package com.backend.spring.bootstrap;

import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

public record DatabaseCredentials(String url, String username) {}

@Configuration
public class AppConfig {
    @Bean
    public DatabaseCredentials credentials() {
        return new DatabaseCredentials("jdbc:postgresql://localhost:5432/orders", "db_admin");
    }
}

public class ApplicationBootstrap {
    public static void main(String[] args) {
        try (var context = new AnnotationConfigApplicationContext(AppConfig.class)) {
            DatabaseCredentials creds = context.getBean(DatabaseCredentials.class);
            System.out.println("Connected to: " + creds.url());
        }
    }
}
```

---

## 3. Bean Definition and Component Scanning

A Spring Bean is an object that is instantiated, assembled, and managed by the Spring IoC container. The container represents beans internally using the `BeanDefinition` interface, which metadata describes:
- Target class name
- Scope (`singleton`, `prototype`, etc.)
- Constructor arguments and property values
- Autowiring mode
- Lazy initialization flags
- Initialization and destruction callbacks

### Component Stereotypes

Spring provides specialized annotations derived from `@Component`:

```
@Component (Generic Spring-managed component)
    ├── @Service (Service Layer: business logic and transaction boundaries)
    ├── @Repository (Persistence Layer: exception translation into DataAccessException)
    └── @Controller / @RestController (Presentation Layer: HTTP request routing and serialization)
```

### `@ComponentScan` Mechanics

`@ComponentScan` instructs the container where to look for annotated classes.

```java
package com.backend.spring.config;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.FilterType;
import org.springframework.stereotype.Repository;

@Configuration
@ComponentScan(
        basePackages = "com.backend.spring",
        includeFilters = @ComponentScan.Filter(type = FilterType.ANNOTATION, classes = Repository.class),
        excludeFilters = @ComponentScan.Filter(type = FilterType.REGEX, pattern = ".*TestService.*")
)
public class ContainerScanConfig {}
```

### `@Configuration` and the CGLIB Proxy

When a class is annotated with `@Configuration`, Spring creates a CGLIB subclass proxy at runtime. This ensures that direct `@Bean` method invocations intercept calls and return the singleton instance from the container rather than invoking the method repeatedly.

```java
@Configuration
public class InfrastructureConfig {

    @Bean
    public DataSource dataSource() {
        return new HikariDataSource();
    }

    @Bean
    public EntityManagerFactory entityManagerFactory() {
        // Calling dataSource() here intercepts via CGLIB proxy to return existing singleton
        return new EntityManagerFactory(dataSource());
    }

    @Bean
    public TransactionManager transactionManager() {
        // Calling dataSource() here returns the exact same singleton instance
        return new DataSourceTransactionManager(dataSource());
    }
}
```

If `@Configuration(proxyBeanMethods = false)` is used (referred to as "Lite Mode"), no CGLIB proxy is generated, and inter-method calls invoke regular Java methods, creating duplicate instances.

---

## 4. Dependency Injection Types and Best Practices

Spring supports three primary styles of dependency injection: Constructor Injection, Setter Injection, and Field Injection.

### 1. Constructor Injection (Recommended Standard)

Dependencies are provided as parameters to the class constructor.

```java
package com.backend.spring.di;

import org.springframework.stereotype.Service;
import java.util.Objects;

@Service
public class PaymentProcessingService {

    private final PaymentGatewayClient gatewayClient;
    private final LedgerRepository ledgerRepository;

    // @Autowired is optional in Spring 4.3+ when a single constructor exists
    public PaymentProcessingService(PaymentGatewayClient gatewayClient, 
                                    LedgerRepository ledgerRepository) {
        this.gatewayClient = Objects.requireNonNull(gatewayClient, "gatewayClient must not be null");
        this.ledgerRepository = Objects.requireNonNull(ledgerRepository, "ledgerRepository must not be null");
    }

    public void processPayment(String transactionId, double amount) {
        gatewayClient.charge(transactionId, amount);
        ledgerRepository.record(transactionId, amount);
    }
}
```

**Why Constructor Injection is Preferred:**
- **Immutability**: Fields can be declared `final`, preventing alteration after construction.
- **Fail-Fast Initialization**: Missing dependencies cause compiler errors or immediate instantiation exceptions.
- **Pure Unit Testing**: The class can be instantiated in plain JUnit tests without initializing a Spring test context or using reflection hacks.

### 2. Setter Injection

Used primarily for optional dependencies or mutable reconfiguration.

```java
@Service
public class AuditLogService {

    private NotificationChannel notificationChannel;

    @Autowired(required = false)
    public void setNotificationChannel(NotificationChannel notificationChannel) {
        this.notificationChannel = notificationChannel;
    }
}
```

### 3. Field Injection (Why It Is an Anti-Pattern)

Field injection injects dependencies directly into private fields using reflection via `@Autowired`.

```java
// ANTI-PATTERN: DO NOT USE IN PRODUCTION
@Service
public class InsecureOrderService {
    @Autowired
    private OrderRepository repository; // Cannot be final
}
```

**Why Field Injection is Bad:**
1. **Violates Encapsulation**: Fields cannot be declared `final`.
2. **Hidden Dependencies**: The public API of the class conceals what dependencies it requires to operate.
3. **Hard to Unit Test**: Cannot instantiate the class in a unit test without using reflection or Spring test runners.
4. **Hides Single Responsibility Principle Violations**: Classes with field injection easily accumulate 10+ dependencies without noticeable constructor bloat.

---

## 5. Bean Scopes and Scoped Proxies

Spring manages the lifecycle and distribution of beans according to their declared scope.

### Available Scopes

| Scope | Description | Lifecycle Bound To |
|---|---|---|
| `singleton` (Default) | Exactly one instance per Spring `ApplicationContext` | Container startup to shutdown |
| `prototype` | New instance created on every injection or `getBean()` request | Instantiated by container; caller manages destruction |
| `request` | One instance per HTTP request | Web request lifecycle |
| `session` | One instance per HTTP Session | Web session lifecycle |
| `application` | One instance per `ServletContext` | Web application lifecycle |
| `websocket` | One instance per WebSocket connection session | WebSocket lifecycle |

### Prototype Scope and Cleanup Caution

The Spring container instantiates, configures, and assembles prototype beans. However, the container **does not manage the complete lifecycle of a prototype bean**. Spring passes the prototype instance to the client and does not track it or call `@PreDestroy` callbacks. The client code is responsible for cleaning up prototype resources.

### Scoped Proxies

When injecting a short-lived bean (e.g., `request` or `prototype`) into a long-lived bean (`singleton`), Spring must inject a proxy rather than the real instance. Without a scoped proxy, the singleton would retain the single short-lived instance created during container startup for its entire lifetime.

```java
package com.backend.spring.scope;

import org.springframework.context.annotation.Scope;
import org.springframework.context.annotation.ScopedProxyMode;
import org.springframework.stereotype.Component;

@Component
@Scope(value = "request", proxyMode = ScopedProxyMode.TARGET_CLASS)
public class UserRequestContext {
    private String traceId;
    private String currentUserId;

    public String getTraceId() { return traceId; }
    public void setTraceId(String traceId) { this.traceId = traceId; }
    public String getCurrentUserId() { return currentUserId; }
    public void setCurrentUserId(String currentUserId) { this.currentUserId = currentUserId; }
}
```

When a singleton invokes a method on `UserRequestContext`, the CGLIB proxy intercepts the call and dynamically delegates it to the specific request-bound instance held in thread-local storage for the active HTTP request.

---

## 6. The Complete Spring Bean Lifecycle

The lifecycle of a Spring bean spans from class loading to final destruction.

### Step-by-Step Lifecycle Sequence

```
1. Instantiation (Constructor invoked)
      ↓
2. Populate Properties (Dependencies injected)
      ↓
3. Aware Interfaces:
   - BeanNameAware.setBeanName()
   - BeanClassLoaderAware.setBeanClassLoader()
   - BeanFactoryAware.setBeanFactory()
   - ApplicationContextAware.setApplicationContext()
      ↓
4. BeanPostProcessor.postProcessBeforeInitialization()
      ↓
5. Initialization Callbacks:
   - @PostConstruct annotated methods
   - InitializingBean.afterPropertiesSet()
   - Custom init-method declared in @Bean(initMethod = "...")
      ↓
6. BeanPostProcessor.postProcessAfterInitialization() (Proxies generated here!)
      ↓
7. Bean Ready for Use
      ↓
8. Container Shutdown
      ↓
9. Destruction Callbacks:
   - @PreDestroy annotated methods
   - DisposableBean.destroy()
   - Custom destroy-method declared in @Bean(destroyMethod = "...")
```

### Lifecycle Implementation Example

```java
package com.backend.spring.lifecycle;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.springframework.beans.factory.BeanNameAware;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.stereotype.Component;

@Component
public class ManagedConnectionPool implements 
        BeanNameAware, BeanFactoryAware, InitializingBean, DisposableBean {

    private String beanName;
    private BeanFactory beanFactory;
    private boolean active;

    public ManagedConnectionPool() {
        System.out.println("Phase 1: Instantiation via Constructor");
    }

    @Override
    public void setBeanName(String name) {
        System.out.println("Phase 3: BeanNameAware -> " + name);
        this.beanName = name;
    }

    @Override
    public void setBeanFactory(BeanFactory beanFactory) throws BeansException {
        System.out.println("Phase 3: BeanFactoryAware invoked");
        this.beanFactory = beanFactory;
    }

    @PostConstruct
    public void initAnnotation() {
        System.out.println("Phase 5: @PostConstruct callback executed");
    }

    @Override
    public void afterPropertiesSet() throws Exception {
        System.out.println("Phase 5: InitializingBean.afterPropertiesSet() executed");
        this.active = true;
    }

    @PreDestroy
    public void preDestroyAnnotation() {
        System.out.println("Phase 9: @PreDestroy callback executed");
    }

    @Override
    public void destroy() throws Exception {
        System.out.println("Phase 9: DisposableBean.destroy() executed");
        this.active = false;
    }
}
```

---

## 7. Conditional Bean Registration

Spring provides conditional mechanisms to instantiate beans selectively based on environment variables, configuration properties, or classpath availability.

### `@Profile` Annotation

Restricts bean registration to active environments (e.g., `dev`, `prod`, `test`).

```java
@Configuration
public class DataSourceProfileConfig {

    @Bean
    @Profile("dev")
    public DataSource h2EmbeddedDataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2).build();
    }

    @Bean
    @Profile("prod")
    public DataSource productionHikariDataSource() {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl("jdbc:postgresql://prod-db.internal:5432/main");
        return ds;
    }
}
```

### Custom `@Conditional` Implementation

```java
package com.backend.spring.conditions;

import org.springframework.context.annotation.Condition;
import org.springframework.context.annotation.ConditionContext;
import org.springframework.core.type.AnnotatedTypeMetadata;

public class LinuxEnvironmentCondition implements Condition {
    @Override
    public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
        String osName = context.getEnvironment().getProperty("os.name");
        return osName != null && osName.toLowerCase().contains("linux");
    }
}
```

Usage on a bean definition:
```java
@Bean
@Conditional(LinuxEnvironmentCondition.class)
public NativePerformanceMetrics linuxMetricsCollector() {
    return new LinuxNativePerformanceMetrics();
}
```

### Spring Boot Conditional Annotations

In Spring Boot applications, common conditional annotations include:
- `@ConditionalOnProperty(name = "feature.cache.enabled", havingValue = "true", matchIfMissing = false)`
- `@ConditionalOnClass(name = "com.zaxxer.hikari.HikariDataSource")`
- `@ConditionalOnMissingBean(type = "com.backend.spring.NotificationService")`

---

## 8. Resolving Ambiguity: `@Qualifier` and `@Primary`

When multiple beans implement the same interface, Spring cannot determine which bean to inject by type alone, throwing `NoUniqueBeanDefinitionException`.

### Using `@Primary`

`@Primary` designates a default candidate when multiple beans of the same type exist.

```java
package com.backend.spring.qualifiers;

import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

public interface MessageService {
    void sendMessage(String recipient, String message);
}

@Component
@Primary
public class SmtpEmailService implements MessageService {
    @Override
    public void sendMessage(String recipient, String message) {
        System.out.println("Sending SMTP email to: " + recipient);
    }
}

@Component
public class TwilioSmsService implements MessageService {
    @Override
    public void sendMessage(String recipient, String message) {
        System.out.println("Sending SMS to: " + recipient);
    }
}
```

### Using `@Qualifier`

`@Qualifier` specifies the exact target bean by name or custom metadata.

```java
@Service
public class AlertNotificationManager {

    private final MessageService primaryService;
    private final MessageService urgentService;

    public AlertNotificationManager(
            MessageService primaryService, // Injects @Primary (SmtpEmailService)
            @Qualifier("twilioSmsService") MessageService urgentService // Injects specific bean
    ) {
        this.primaryService = primaryService;
        this.urgentService = urgentService;
    }
}
```

### Custom Qualifier Annotations

To avoid brittle magic string identifiers, create custom qualifier annotations:

```java
package com.backend.spring.qualifiers;

import org.springframework.beans.factory.annotation.Qualifier;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target({ElementType.FIELD, ElementType.PARAMETER, ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier
public @interface SmsGateway {}

@Component
@SmsGateway
public class SecureTwilioClient implements MessageService {
    @Override public void sendMessage(String recipient, String msg) {}
}

@Service
public class UserVerificationService {
    public UserVerificationService(@SmsGateway MessageService smsService) {
        // Injects SecureTwilioClient safely with compile-time verification
    }
}
```

---

## 9. Customizing the Container: `BeanPostProcessor` and `BeanFactoryPostProcessor`

Spring provides extension hooks to intercept and modify bean definitions and bean instances.

### `BeanFactoryPostProcessor` (BFPP)

Executes before any bean is instantiated. It operates on configuration metadata (`BeanDefinition` objects), allowing modifications to property values, scopes, or class definitions.

```java
package com.backend.spring.custom;

import org.springframework.beans.BeansException;
import org.springframework.beans.factory.config.BeanFactoryPostProcessor;
import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.stereotype.Component;

@Component
public class CustomBeanFactoryPostProcessor implements BeanFactoryPostProcessor {
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) throws BeansException {
        for (String name : beanFactory.getBeanDefinitionNames()) {
            var definition = beanFactory.getBeanDefinition(name);
            if (name.startsWith("audit")) {
                definition.setLazyInit(true);
            }
        }
    }
}
```

### `BeanPostProcessor` (BPP)

Operates on instantiated bean instances. Its methods run around initialization callbacks (`@PostConstruct` / `afterPropertiesSet()`).

```java
package com.backend.spring.custom;

import org.springframework.beans.BeansException;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.stereotype.Component;

@Component
public class MetricsInstrumentationPostProcessor implements BeanPostProcessor {

    @Override
    public Object postProcessBeforeInitialization(Object bean, String beanName) throws BeansException {
        // Runs before @PostConstruct
        return bean;
    }

    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) throws BeansException {
        // Runs after initialization; this is where Dynamic Proxies (AOP, @Transactional) are wrapped!
        if (bean.getClass().isAnnotationPresent(Monitored.class)) {
            System.out.println("Instrumenting bean for metrics: " + beanName);
            return ProxyFactory.getProxy(bean);
        }
        return bean;
    }
}
```

---

## 10. Application Events and Decoupled Communication

Spring provides an in-memory event publishing system based on the Observer pattern.

### Custom Event Definition

```java
package com.backend.spring.events;

import java.time.Instant;

public record OrderPlacedEvent(String orderId, double amount, Instant timestamp) {
    public OrderPlacedEvent(String orderId, double amount) {
        this(orderId, amount, Instant.now());
    }
}
```

### Event Publisher

```java
package com.backend.spring.events;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;

@Service
public class CheckoutService {

    private final ApplicationEventPublisher eventPublisher;

    public CheckoutService(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }

    public void completeCheckout(String orderId, double amount) {
        // Business logic for placing order
        System.out.println("Order recorded in database: " + orderId);

        // Publish event to decoupled listeners
        eventPublisher.publishEvent(new OrderPlacedEvent(orderId, amount));
    }
}
```

### Synchronous and Asynchronous Listeners

```java
package com.backend.spring.events;

import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

@Component
public class OrderNotificationListener {

    @EventListener
    @Order(1) // Runs first among listeners
    public void sendEmailReceipt(OrderPlacedEvent event) {
        System.out.println("Synchronous Email dispatched for: " + event.orderId());
    }

    @EventListener
    @Async // Executed concurrently on dedicated thread pool
    @Order(2)
    public void updateAnalyticsWarehouse(OrderPlacedEvent event) {
        System.out.println("Asynchronously syncing analytics: " + event.orderId());
    }
}
```

---

## 11. Spring Expression Language (SpEL)

Spring Expression Language (SpEL) provides an expression evaluator supporting dynamic queries, property navigation, method invocations, and mathematical operations at runtime.

### Syntax and Core Constructs

- Values and Expressions: `#{expression}`
- Property place holders: `${property.key}`
- Bean references: `@beanName.methodName()`
- Ternary and Elvis operator: `condition ? trueVal : falseVal` or `name ?: 'default'`
- Safe navigation operator: `?.` (prevents `NullPointerException`)
- Collection selection: `?[predicate]` and projection: `![transformer]`

```java
package com.backend.spring.spel;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import java.util.List;

@Component
public class SpelDemonstrationComponent {

    // Mathematical evaluation
    @Value("#{2 * T(java.lang.Math).PI * 10}")
    private double perimeter;

    // Bean invocation and property extraction
    @Value("#{systemProperties['user.home']}")
    private String userHomeDirectory;

    // Ternary conditional expression
    @Value("#{systemEnvironment['DATABASE_PORT'] != null ? systemEnvironment['DATABASE_PORT'] : 5432}")
    private int databasePort;

    // Elvis operator with property fallback
    @Value("${app.theme:#{'default-dark'}}")
    private String uiTheme;

    // Bean method call
    @Value("#{@inventoryService.isItemAvailable('ITEM-100')}")
    private boolean itemReady;
}
```

---

## 12. Configuration Properties and Environment Abstraction

Spring unifies access to configuration sources (command-line arguments, system properties, environment variables, and `.properties` / `.yml` files) through the `Environment` abstraction.

### `@Value` vs `@ConfigurationProperties`

| Feature | `@Value` | `@ConfigurationProperties` |
|---|---|---|
| Binding granularity | Individual field level | Entire hierarchical POJO / Record |
| Relaxed binding | No (`kebab-case` must match strictly) | Yes (`server.port`, `serverPort`, `SERVER_PORT`) |
| JSR-380 validation | Not directly supported | Full support via `@Validated` |
| Type safety | String-based evaluation | Strongly typed with compiler checks |

### Type-Safe Configuration Properties with Records

```java
package com.backend.spring.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;
import org.springframework.validation.annotation.Validated;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import java.time.Duration;

@ConfigurationProperties(prefix = "app.http-client")
@Validated
public record HttpClientProperties(
        @NotBlank String baseUrl,
        @Min(100) @Max(10000) int maxConnections,
        @DefaultValue("5s") Duration connectTimeout,
        SecuritySettings security
) {
    public record SecuritySettings(boolean tlsEnabled, String certPath) {}
}
```

---

## 13. Aspect-Oriented Programming (AOP) Under the Hood

Aspect-Oriented Programming (AOP) complements Object-Oriented Programming by modularizing cross-cutting concerns (e.g., logging, transaction management, security authorization, and performance metrics) without polluting business logic.

### Core Concepts

- **Aspect**: A module encapsulating cross-cutting concerns (e.g., `@Aspect` class).
- **Join Point**: A point during program execution (in Spring AOP, always a method execution).
- **Pointcut**: A predicate expression matching Join Points (`execution(...)`, `@annotation(...)`).
- **Advice**: Action taken at a Join Point (`@Before`, `@AfterReturning`, `@AfterThrowing`, `@After`, `@Around`).

### Advice Types and Execution Order

```
[Method Invocation]
       ↓
@Around (Entry phase: proceed() not called yet)
       ↓
@Before
       ↓
[Target Method Execution]
       ↓
@AfterReturning (On successful completion)  OR  @AfterThrowing (On exception)
       ↓
@After (Finally: executes unconditionally)
       ↓
@Around (Exit phase: after target method completion)
```

### Complete `@Around` Profiling Aspect

```java
package com.backend.spring.aop;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class PerformanceProfilingAspect {

    private static final Logger log = LoggerFactory.getLogger(PerformanceProfilingAspect.class);

    // Pointcut matching any public method in services returning any type
    @Pointcut("execution(public * com.backend.spring.service..*.*(..))")
    public void serviceLayerOperations() {}

    // Pointcut matching methods annotated with custom @TrackLatency
    @Pointcut("@annotation(com.backend.spring.aop.TrackLatency)")
    public void latencyTrackedMethods() {}

    @Around("serviceLayerOperations() || latencyTrackedMethods()")
    public Object profileMethodExecution(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.nanoTime();
        String methodName = joinPoint.getSignature().toShortString();

        try {
            // Execute the intercepted target method
            Object result = joinPoint.proceed();
            return result;
        } catch (Throwable ex) {
            log.error("Execution failed in {}: {}", methodName, ex.getMessage());
            throw ex;
        } finally {
            long durationMillis = (System.nanoTime() - start) / 1_000_000;
            log.info("Method [{}] executed in {} ms", methodName, durationMillis);
        }
    }
}
```

### JDK Dynamic Proxies vs CGLIB Proxies

Spring AOP creates proxy objects to intercept method invocations.

1. **JDK Dynamic Proxy**:
   - Built into standard Java runtime (`java.lang.reflect.Proxy`).
   - Requires target classes to implement at least one interface.
   - Proxies the interface; cannot cast the proxy to the concrete class.
2. **CGLIB Proxy**:
   - Generates bytecode subclasses dynamically at runtime using ASM.
   - Targets classes directly without requiring interfaces.
   - Cannot proxy `final` classes or intercept `final` methods.
   - **Spring Boot 2.x and 3.x default to CGLIB proxies** (`spring.aop.proxy-target-class=true`) for consistent proxying across classes and interfaces alike.

---

## 14. Circular Dependencies: Detection, Prevention, and Refactoring

A circular dependency occurs when Bean A requires Bean B, and Bean B requires Bean A (directly or transitively via Bean C).

### Why Circular Dependencies Occur

When using constructor injection, the container cannot instantiate either bean:
1. To create `BeanA`, the container invokes `new BeanA(BeanB)`.
2. To provide `BeanB`, the container invokes `new BeanB(BeanA)`.
3. Neither constructor can proceed, causing a `BeanCurrentlyInCreationException`.

```java
// Problematic Circular Construction
@Service
public class OrderService {
    public OrderService(InvoiceService invoiceService) {}
}

@Service
public class InvoiceService {
    public InvoiceService(OrderService orderService) {}
}
```

### Breaking Cycles with `@Lazy` (Temporary Workaround)

Annotating one constructor parameter with `@Lazy` instructs Spring to inject a synthetic proxy instead of instantiating the real bean immediately:

```java
@Service
public class InvoiceService {
    private final OrderService orderService;

    public InvoiceService(@Lazy OrderService orderService) {
        this.orderService = orderService; // Injected with CGLIB proxy
    }
}
```

The real `OrderService` bean is only resolved upon the first method call on `orderService`.

### Idiomatic Architectural Refactoring

While `@Lazy` resolves startup failures, circular dependencies are architectural design smells indicating violations of the Single Responsibility Principle.

#### Architectural Solutions:
1. **Extract a Third Mediator Service**: Extract the shared functionality that both beans depend upon into a separate bean.
   ```
   [Before] OrderService  <───>  InvoiceService
   
   [After]  OrderService  ───>  SharedPaymentCalculator  <───  InvoiceService
   ```
2. **Event-Driven Decoupling**: Instead of calling a dependent service directly, publish a domain event (`OrderPlacedEvent`). The consuming service listens to the event asynchronously, breaking the compile-time and runtime dependency cycle.

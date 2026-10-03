# Spring Boot Interview Questions and Answers

### Question 1: How does Spring Boot auto-configuration work internally?

**Answer:**
Spring Boot auto-configuration inspects the classpath, existing Spring beans, and external configuration properties during startup to automatically register sensible default beans in the `ApplicationContext`. At the heart of this process is `@EnableAutoConfiguration` (imported by `@SpringBootApplication`), which utilizes `@Import(AutoConfigurationImportSelector.class)`.

In Spring Boot 3.x, `AutoConfigurationImportSelector` scans for descriptor files located at `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`. In Spring Boot 2.x, it inspected `META-INF/spring.factories`. This file contains a list of candidate configuration classes, such as `DataSourceAutoConfiguration` and `JacksonAutoConfiguration`. Each class evaluates conditional annotations before creating beans:

```java
@AutoConfiguration
@ConditionalOnClass({ DataSource.class, EmbeddedDatabaseType.class })
@ConditionalOnMissingBean(type = "javax.sql.DataSource")
@EnableConfigurationProperties(DataSourceProperties.class)
public class DataSourceAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public DataSource dataSource(DataSourceProperties properties) {
        return properties.initializeDataSourceBuilder().build();
    }
}
```

The conditional annotations (e.g., `@ConditionalOnClass`, `@ConditionalOnMissingBean`, `@ConditionalOnProperty`) determine whether the configuration class runs. If a developer explicitly declares their own `DataSource` bean, `@ConditionalOnMissingBean` evaluates to false, causing Spring Boot's default configuration to gracefully back off without throwing bean definition collision errors.

---

### Question 2: What is the difference between @SpringBootApplication, @EnableAutoConfiguration, and @ComponentScan?

**Answer:**
`@SpringBootApplication` is a composite meta-annotation that bundles three primary Spring annotations: `@SpringBootConfiguration`, `@EnableAutoConfiguration`, and `@ComponentScan`.

`@ComponentScan` tells the Spring container where to look for developer-defined components annotated with `@Component`, `@Service`, `@Repository`, or `@Controller`. By default, it scans packages recursively starting from the package in which the annotated main class resides.

`@EnableAutoConfiguration` tells Spring Boot to look beyond the developer's scanned packages and inspect third-party starters and framework libraries to automatically wire infrastructure beans (e.g., Jackson `ObjectMapper`, `DispatcherServlet`, HikariCP `DataSource`).

```java
// Equivalent decomposition of @SpringBootApplication
@SpringBootConfiguration
@EnableAutoConfiguration
@ComponentScan(basePackages = "com.example.orderservice")
public class OrderServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }
}
```

Key distinctions:
- `@ComponentScan` focuses on user-authored business beans within specified packages.
- `@EnableAutoConfiguration` focuses on framework-provided infrastructure beans loaded conditionally from `AutoConfiguration.imports`.
- `@SpringBootApplication` bundles both with standard configuration capabilities to provide zero-boilerplate application bootstrapping.

---

### Question 3: How do Spring Boot profiles work and how do you activate them?

**Answer:**
Spring Boot profiles allow developers to isolate portions of application configuration and expose them only in specific runtime environments (such as `dev`, `test`, `staging`, and `prod`). Beans can be tagged with the `@Profile` annotation to control their instantiation.

```java
@Configuration
public class DataSourceConfig {

    @Bean
    @Profile("dev")
    public DataSource devDataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .build();
    }

    @Bean
    @Profile("prod")
    public DataSource prodDataSource(@Value("${spring.datasource.url}") String url,
                                     @Value("${spring.datasource.username}") String user,
                                     @Value("${spring.datasource.password}") String pass) {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl(url);
        ds.setUsername(user);
        ds.setPassword(pass);
        return ds;
    }
}
```

Spring Boot automatically reads profile-specific configuration files named `application-{profile}.yml` or `application-{profile}.properties`. Profiles can be activated via multiple mechanisms:
1. Command line argument: `--spring.profiles.active=prod`
2. JVM system property: `-Dspring.profiles.active=prod`
3. Environment variable: `SPRING_PROFILES_ACTIVE=prod`
4. Test annotation: `@ActiveProfiles("test")`
Active profiles can also include other profiles using the property `spring.profiles.include=common,monitoring`.

---

### Question 4: What is the difference between @Value and @ConfigurationProperties?

**Answer:**
Both `@Value` and `@ConfigurationProperties` bind external configuration properties to Java classes, but they cater to fundamentally different use cases.

`@Value` performs simple, direct SpEL or scalar property injection into individual fields:
- No relaxed binding (requires exact property name matching).
- No standard JSR-380 validation support.
- Difficult to bind complex hierarchical structures like nested maps or lists.

`@ConfigurationProperties` binds structured, type-safe configuration trees to strongly-typed POJOs or Java Records:
- Supports relaxed binding (e.g., `kebab-case`, `camelCase`, and `SNAKE_CASE` map to the same field).
- Integrates with `@Validated` and Jakarta Validation (`@NotNull`, `@Min`, `@Pattern`).
- Supports immutable Record bindings via constructor parameters.

```java
@ConfigurationProperties(prefix = "app.payment")
@Validated
public record PaymentProperties(
    @NotBlank String provider,
    @Min(100) int timeoutMillis,
    List<String> currencies,
    Endpoint endpoint
) {
    public record Endpoint(String url, int port) {}
}
```

```java
// Contrast with @Value injection:
@Component
public class LegacyPaymentService {
    @Value("${app.payment.provider:stripe}")
    private String provider;

    @Value("${app.payment.timeout-millis:5000}")
    private int timeout;
}
```

---

### Question 5: How do you configure and secure Spring Boot Actuator endpoints?

**Answer:**
Spring Boot Actuator provides production-ready monitoring endpoints (`/actuator/health`, `/actuator/metrics`, `/actuator/info`). By default, only `/actuator/health` is exposed via HTTP for security reasons.

To configure and expose endpoints, specify them in `application.yml`:
```yaml
management:
  server:
    port: 9090
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
      base-path: /actuator
  endpoint:
    health:
      show-details: when_authorized
      roles: ACTUATOR_ADMIN
```

To secure sensitive endpoints using Spring Security, restrict access based on roles or authority and run them on a dedicated management port:
```java
@Configuration
public class ActuatorSecurityConfiguration {

    @Bean
    public SecurityFilterChain actuatorSecurity(HttpSecurity http) throws Exception {
        http
            .securityMatcher(EndpointRequest.toAnyEndpoint())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(EndpointRequest.to("health", "info")).permitAll()
                .anyRequest().hasRole("ACTUATOR_ADMIN")
            )
            .httpBasic(Customizer.withDefaults())
            .csrf(csrf -> csrf.disable());
        return http.build();
    }
}
```
Setting `management.server.port=9090` isolates management traffic to an internal port that can be blocked from external ingress traffic via firewall rules or reverse proxy configuration.

---

### Question 6: What is a custom Health Indicator and how do you write one?

**Answer:**
A custom `HealthIndicator` allows applications to report the operational readiness and liveness of custom internal subsystems, third-party APIs, message brokers, or remote dependencies through the `/actuator/health` endpoint.

To implement a custom indicator, implement the `HealthIndicator` interface and override the `health()` method:

```java
@Component
public class WarehouseApiHealthIndicator implements HealthIndicator {

    private final RestClient restClient;

    public WarehouseApiHealthIndicator(RestClient.Builder builder) {
        this.restClient = builder.baseUrl("https://warehouse.internal/health").build();
    }

    @Override
    public Health health() {
        try {
            long start = System.currentTimeMillis();
            ResponseEntity<Void> response = restClient.get().retrieve().toBodilessEntity();
            long latency = System.currentTimeMillis() - start;

            if (response.getStatusCode().is2xxSuccessful()) {
                return Health.up()
                    .withDetail("service", "Warehouse System")
                    .withDetail("latencyMs", latency)
                    .build();
            }
            return Health.down()
                .withDetail("statusCode", response.getStatusCode().value())
                .build();
        } catch (Exception ex) {
            return Health.down(ex)
                .withDetail("reason", "Unable to ping warehouse backend")
                .build();
        }
    }
}
```

When evaluated, Spring Boot combines all registered `HealthIndicator` beans. If any critical indicator returns `Status.DOWN`, the overall composite application health transitions to `DOWN` with HTTP status 503 Service Unavailable, signaling orchestrators like Kubernetes to restart or bypass the pod.

---

### Question 7: What is the property resolution order in Spring Boot?

**Answer:**
Spring Boot utilizes an ordered hierarchy to resolve externalized configuration values. If a property is defined in multiple sources, the source with higher precedence wins.

Key hierarchy in order of precedence (highest to lowest):
1. DevTools global settings (`~/.config/spring-boot/spring-boot-devtools.properties`).
2. Test annotations (`@TestPropertySource`, `@SpringBootTest(properties = "...")`).
3. Command-line arguments (`--server.port=9000`).
4. Properties from `SPRING_APPLICATION_JSON`.
5. Java System properties (`-Dserver.port=9000`).
6. OS Environment variables (`SERVER_PORT=9000`).
7. Profile-specific application properties outside the packaged JAR (`config/application-{profile}.yml`).
8. Profile-specific application properties inside the packaged JAR (`classpath:application-{profile}.yml`).
9. Application properties outside the packaged JAR (`config/application.yml`).
10. Application properties inside the packaged JAR (`classpath:application.yml`).
11. `@PropertySource` annotations on configuration classes.
12. Default properties set via `SpringApplication.setDefaultProperties`.

```java
// Command line override example:
// java -Dserver.port=8080 -jar app.jar --server.port=9090
// Output port will be 9090 because command-line arguments take precedence over JVM system properties.
```

This strict hierarchy ensures that configuration defaults packaged in the JAR can be seamlessly overridden during staging and production deployment via environment variables or command-line flags.

---

### Question 8: How do you switch from embedded Tomcat to Undertow?

**Answer:**
Spring Boot includes Apache Tomcat as the default embedded servlet container via `spring-boot-starter-web`. To switch to Undertow, exclude Tomcat from `spring-boot-starter-web` and add `spring-boot-starter-undertow` to the build configuration.

In Maven `pom.xml`:
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-tomcat</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-undertow</artifactId>
</dependency>
```

Configure Undertow thread pool parameters in `application.yml`:
```yaml
server:
  port: 8080
  undertow:
    threads:
      io: 16
      worker: 128
    buffer-size: 1024
    direct-buffers: true
```
Undertow uses non-blocking I/O with XNIO worker threads, making it lightweight with lower memory overhead under massive concurrent connection scenarios.

---

### Question 9: What is the difference between @SpringBootTest and @WebMvcTest?

**Answer:**
`@SpringBootTest` and `@WebMvcTest` represent full integration testing versus focused slice testing.

`@SpringBootTest` bootstraps the complete Spring `ApplicationContext`. It configures every bean, repository, security filter, and database connection. It is used for end-to-end integration testing:
```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class FullIntegrationTest {
    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void testFullFlow() {
        ResponseEntity<String> response = restTemplate.getForEntity("/api/orders", String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
    }
}
```

`@WebMvcTest` is a specialized slice test annotation. It only loads Spring MVC infrastructure components: `@Controller`, `@ControllerAdvice`, `JsonComponent`, and `Filter`. It does not load `@Service`, `@Repository`, or database entities, making execution significantly faster:
```java
@WebMvcTest(OrderController.class)
class OrderControllerSliceTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @Test
    void testEndpoint() throws Exception {
        given(orderService.getOrder(1L)).willReturn(new Order(1L, "Sample"));
        mockMvc.perform(get("/orders/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1));
    }
}
```

---

### Question 10: How do layered JARs improve Docker build caching for Spring Boot?

**Answer:**
Traditional Spring Boot fat JARs combine compiled application code and third-party dependencies into a single monolithic archive. When Docker builds an image by copying the fat JAR (`COPY target/app.jar app.jar`), any code modification invalidates the Docker build cache for that entire layer, forcing Docker to push and pull 50-100MB layers on every build.

Layered JARs break the fat JAR into distinct directory layers based on change velocity:
1. `dependencies`: Third-party release dependencies (changes rarely).
2. `spring-boot-loader`: Spring Boot launcher infrastructure (changes rarely).
3. `snapshot-dependencies`: Local snapshots or team artifacts (changes occasionally).
4. `application`: User application classes and templates (changes frequently).

By extracting these layers using `java -Djarmode=layertools -jar app.jar extract` inside a multi-stage Dockerfile, Docker caches the heavy dependency layers:

```dockerfile
FROM eclipse-temurin:21-jre AS builder
WORKDIR /workspace
ARG JAR_FILE=target/*.jar
COPY ${JAR_FILE} app.jar
RUN java -Djarmode=layertools -jar app.jar extract

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=builder /workspace/dependencies/ ./
COPY --from=builder /workspace/spring-boot-loader/ ./
COPY --from=builder /workspace/snapshot-dependencies/ ./
COPY --from=builder /workspace/application/ ./
ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```
Subsequent builds only recompile and push the thin `application` layer (often less than 500KB), resulting in near-instant container builds and distribution.

---

### Question 11: What is MDC in logging and how do you use it in Spring Boot?

**Answer:**
MDC (Mapped Diagnostic Context) is a feature provided by SLF4J and Logback that allows developers to associate contextual key-value pairs with the currently executing thread. These contextual values can be automatically formatted into every subsequent log statement generated on that thread.

In distributed microservice architectures, MDC is commonly used to trace individual HTTP requests across services using correlation IDs:

```java
@Component
public class RequestMdcFilter extends OncePerRequestFilter {

    private static final String CORRELATION_HEADER = "X-Correlation-Id";
    private static final String MDC_TRACE_KEY = "traceId";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String correlationId = request.getHeader(CORRELATION_HEADER);
        if (correlationId == null || correlationId.isBlank()) {
            correlationId = UUID.randomUUID().toString();
        }

        MDC.put(MDC_TRACE_KEY, correlationId);
        response.setHeader(CORRELATION_HEADER, correlationId);
        try {
            filterChain.doFilter(request, response);
        } finally {
            MDC.remove(MDC_TRACE_KEY);
        }
    }
}
```

In `application.yml` or `logback-spring.xml`, reference the MDC key using `%X{traceId}`:
```yaml
logging:
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] [%X{traceId}] %-5level %logger{36} - %msg%n"
```
Every log message produced during the request automatically prints the unique correlation ID.

---

### Question 12: How does spring.config.import work?

**Answer:**
Introduced in Spring Boot 2.4, `spring.config.import` provides a unified syntax for importing external configuration sources, directories, Kubernetes config maps, and cloud secrets directly from within configuration files.

Common patterns:
```yaml
spring:
  application:
    name: order-service
  config:
    import:
      - optional:file:/etc/config/database.properties
      - optional:file:/etc/secrets/
      - optional:consul:localhost:8500
      - optional:configserver:http://config-server.internal:8888
```

Key features:
1. `optional:` prefix: Prevents bootstrap failure if the specified path or remote service is unavailable.
2. Directory importing: Specifying a directory ending with `/` (e.g., `file:/etc/secrets/`) scans all individual files within that directory and mounts each file's name as a property key and its contents as the property value. This matches Kubernetes Secret and ConfigMap volume mounting.
3. Profile awareness: Allows fine-grained control over when configuration files load without relying on legacy `spring.profiles.include` workarounds.

```yaml
---
spring:
  config:
    activate:
      on-profile: prod
    import:
      - vault://secret/order-service
```

---

### Question 13: What is graceful shutdown in Spring Boot and how do you configure it?

**Answer:**
Graceful shutdown ensures that when an application receives a termination signal (`SIGTERM` in container runtimes), the embedded web server stops accepting new network connections while allowing active, in-flight HTTP requests and ongoing asynchronous tasks a defined grace period to finish execution.

Enable graceful shutdown in `application.yml`:
```yaml
server:
  shutdown: graceful

spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

Lifecycle execution flow:
1. Orchestrator issues `SIGTERM` to the Spring Boot JVM process.
2. The embedded Tomcat/Undertow server immediately stops listening on incoming ports.
3. In-flight requests continue processing up to the defined `timeout-per-shutdown-phase` (30 seconds).
4. As soon as all active requests terminate, the container closes.
5. If the timeout expires while requests remain unresolved, the server terminates them abruptly.
6. Custom `SmartLifecycle` beans execute their cleanup logic:

```java
@Component
public class BatchJobManager implements SmartLifecycle {
    private final AtomicBoolean active = new AtomicBoolean(true);

    @Override
    public void stop() {
        active.set(false);
        // complete pending processing
    }

    @Override
    public boolean isRunning() { return active.get(); }
    @Override
    public void start() { active.set(true); }
}
```

---

### Question 14: How do you write a custom Spring Boot auto-configuration?

**Answer:**
Creating a custom Spring Boot auto-configuration requires three primary steps: defining configuration properties, implementing the auto-configuration class with conditional annotations, and registering the class in the imports descriptor.

Step 1: Configuration Properties class.
```java
@ConfigurationProperties(prefix = "audit.service")
public class AuditProperties {
    private boolean enabled = true;
    private String destination = "console";
    // Getters and setters
    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean enabled) { this.enabled = enabled; }
    public String getDestination() { return destination; }
    public void setDestination(String destination) { this.destination = destination; }
}
```

Step 2: Auto-Configuration class.
```java
@AutoConfiguration
@ConditionalOnClass(AuditLogger.class)
@EnableConfigurationProperties(AuditProperties.class)
public class AuditAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    @ConditionalOnProperty(prefix = "audit.service", name = "enabled", havingValue = "true", matchIfMissing = true)
    public AuditLogger auditLogger(AuditProperties properties) {
        return new AuditLogger(properties.getDestination());
    }
}
```

Step 3: Registration descriptor.
Create `src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` and add the fully qualified class name:
```text
com.example.audit.AuditAutoConfiguration
```
Any project declaring this starter dependency automatically configures `AuditLogger` unless overridden with a custom bean definition.

---

### Question 15: What is the difference between spring-boot-starter-web and spring-boot-starter-webflux?

**Answer:**
`spring-boot-starter-web` and `spring-boot-starter-webflux` represent the two foundational web architectures in the Spring ecosystem: synchronous blocking versus asynchronous reactive.

`spring-boot-starter-web` (Spring MVC):
- Built on the standard Jakarta Servlet API.
- Employs a thread-per-request blocking model backed by embedded Tomcat.
- Each incoming HTTP connection blocks an OS execution thread until database queries or external service calls finish.
- Straightforward debugging, stack traces, and mature ecosystem integrations (JDBC, JPA).

```java
@RestController
@RequestMapping("/orders")
public class BlockingOrderController {
    @GetMapping("/{id}")
    public Order getOrder(@PathVariable Long id) {
        return orderRepository.findById(id).orElseThrow();
    }
}
```

`spring-boot-starter-webflux`:
- Built on Project Reactor and the Reactive Streams specification.
- Employs an event-loop, non-blocking I/O model backed by embedded Netty.
- Small fixed pool of threads (typically matching CPU core count) handles thousands of concurrent requests.
- Requires non-blocking reactive drivers throughout the entire stack (R2DBC instead of JDBC/JPA).

```java
@RestController
@RequestMapping("/reactive/orders")
public class ReactiveOrderController {
    @GetMapping("/{id}")
    public Mono<Order> getOrder(@PathVariable Long id) {
        return reactiveOrderRepository.findById(id);
    }
}
```
Choose `starter-web` for traditional relational database CRUD workflows; choose `starter-webflux` for high-concurrency streaming, websockets, or microservice gateways.

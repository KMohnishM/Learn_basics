# Spring Boot Deep Dive

Spring Boot is an opinionated, production-ready extension of the Spring Framework designed to minimize boilerplate configuration, streamline application bootstrapping, and provide comprehensive operational infrastructure out of the box.

---

## 1. Spring Boot Philosophy

### Convention over Configuration
Traditional enterprise Java applications built on Spring Framework required extensive XML configurations or repetitive Java configuration classes (`@Configuration`) to declare infrastructure components:
- `DataSource` bean definitions with driver classes, URLs, and connection pools.
- `TransactionManager` bean configurations.
- `DispatcherServlet`, `InternalResourceViewResolver`, and message converters for web layers.
- Object-relational mapping configuration (`LocalContainerEntityManagerFactoryBean`).

Spring Boot replaces manual boilerplate with convention over configuration:
- Sensible Defaults: If Spring Boot detects `h2` on the classpath, it configures an in-memory database. If it detects `spring-boot-starter-web`, it provisions an embedded Tomcat servlet container, JSON message converters (`Jackson2ObjectMapperBuilder`), and standard error controllers.
- Non-Invasive Defaults: Auto-configured beans back off automatically as soon as a developer defines a custom bean of the same type.

### Auto-configuration vs. Manual Configuration
- Classic Spring Framework: Explicit bean declaration for every single infrastructure component. Upgrades require auditing and modifying XML or Java config.
- Spring Boot Auto-configuration: Dynamic runtime deduction based on classpath contents, active profiles, environment properties, and existing bean definitions.

| Capability | Classic Spring Framework | Spring Boot |
| :--- | :--- | :--- |
| Application Packaging | WAR file deployed to standalone servlet container | Self-contained executable "fat" JAR with embedded server |
| Configuration | Explicit XML or `@Configuration` classes | Opinionated auto-configuration based on starters |
| Dependency Management | Manual resolution of matching library versions | Curated Bill of Materials (BOM) via parent POM |
| Operational Observability | Custom metrics, JMX, manual health endpoints | Spring Boot Actuator with out-of-the-box endpoints |
| Server Lifecycle | External lifecycle managed by Tomcat/WildFly/WebLogic | In-process lifecycle managed by Spring ApplicationContext |

### Embedded Servlet Containers
In traditional deployments, developers built a Web Application Archive (WAR) and deployed it onto an externally installed and administered servlet container (Apache Tomcat, Eclipse Jetty) or application server (WildFly, WebLogic, WebSphere). 

Spring Boot inverted this architectural model:
- The servlet container is embedded as a standard library dependency inside the application artifact.
- The JVM process executes the standard entry point `public static void main(String[] args)`.
- The embedded container creates its network connectors and threads within the lifecycle of the Spring `ApplicationContext`.
- Deployments become immutable, isolated, reproducible processes that adhere to twelve-factor application principles.

---

## 2. Project Setup

### Build Systems: Maven vs. Gradle
Spring Boot provides first-class plugins for both Apache Maven and Gradle.

#### Maven Configuration with Parent POM
Using `spring-boot-starter-parent` provides dependency management, default plugin execution bindings (such as `repackage`), UTF-8 source encoding, and Java compiler release targets.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                             https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.3</version>
        <relativePath/>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>order-service</artifactId>
    <version>1.0.0</version>
    <name>order-service</name>
    <description>Enterprise Order Management Microservice</description>

    <properties>
        <java.version>21</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

#### Bill of Materials (BOM) Pattern without Parent POM
When a project must inherit from a corporate parent POM, Spring Boot's dependency management can be imported via `scope=import` with type `pom`:

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-dependencies</artifactId>
            <version>3.2.3</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

### Curated Starters
Starters are composite dependency descriptors that bundle production-tested, compatible transitive dependencies into a single import:
- `spring-boot-starter-web`: Spring MVC, RESTful endpoints, Jackson JSON serialization, embedded Tomcat.
- `spring-boot-starter-data-jpa`: Hibernate ORM, Spring Data JPA, HikariCP connection pool, Jakarta Persistence API.
- `spring-boot-starter-security`: Spring Security core, servlet filters, authentication providers, BCrypt password hashing.
- `spring-boot-starter-validation`: Jakarta Validation API and Hibernate Validator implementation.
- `spring-boot-starter-actuator`: Production monitoring, health checks, metrics, and thread dumps.

---

## 3. Auto-configuration Deep Dive

### Mechanics of `@SpringBootApplication`
The `@SpringBootApplication` annotation is a convenience meta-annotation combining three foundational Spring annotations:
1. `@SpringBootConfiguration`: Specialized form of `@Configuration` designating the primary configuration class.
2. `@EnableAutoConfiguration`: Signals Spring Boot to scan classpath descriptors and register auto-configuration classes.
3. `@ComponentScan`: Activates recursive package scanning for `@Component`, `@Service`, `@Repository`, and `@Controller` beans starting from the package declaring the main class.

```java
package com.example.orderservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class OrderServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }
}
```

### Auto-Configuration Discovery
How Spring Boot finds auto-configurations:
- Spring Boot 1.x and 2.x: Read class declarations listed under `org.springframework.boot.autoconfigure.EnableAutoConfiguration` in `META-INF/spring.factories`.
- Spring Boot 3.x+: Uses the new imports file located at `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`. Each line contains the fully qualified class name of an auto-configuration class.

### Conditional Annotations (`@ConditionalOn*`)
Auto-configuration classes utilize conditional annotations to verify environmental prerequisites before registering beans:
- `@ConditionalOnClass(DataSource.class)`: Activates bean definition only when specified classes exist on the runtime classpath.
- `@ConditionalOnMissingBean(ObjectMapper.class)`: Registers a fallback bean only if the developer has not provided their own bean of that type or name.
- `@ConditionalOnProperty(name = "features.audit.enabled", havingValue = "true", matchIfMissing = false)`: Activates configuration based on property value.
- `@ConditionalOnWebApplication(type = Type.SERVLET)`: Matches only when the running context is a servlet-based web application.
- `@ConditionalOnResource(resources = "classpath:schema.sql")`: Matches when the resource is present on the classpath.

### Writing a Custom Auto-Configuration

Step 1: Configuration properties class.
```java
package com.example.autoconfigure.payment;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "gateway.payment")
public class PaymentGatewayProperties {
    private String endpointUrl = "https://api.gateway.internal/v1";
    private int timeoutMs = 5000;
    private String apiKey;

    public String getEndpointUrl() { return endpointUrl; }
    public void setEndpointUrl(String endpointUrl) { this.endpointUrl = endpointUrl; }
    public int getTimeoutMs() { return timeoutMs; }
    public void setTimeoutMs(int timeoutMs) { this.timeoutMs = timeoutMs; }
    public String getApiKey() { return apiKey; }
    public void setApiKey(String apiKey) { this.apiKey = apiKey; }
}
```

Step 2: Service implementation.
```java
package com.example.autoconfigure.payment;

public class PaymentGatewayClient {
    private final String endpointUrl;
    private final int timeoutMs;
    private final String apiKey;

    public PaymentGatewayClient(String endpointUrl, int timeoutMs, String apiKey) {
        this.endpointUrl = endpointUrl;
        this.timeoutMs = timeoutMs;
        this.apiKey = apiKey;
    }

    public boolean processPayment(String transactionId, double amount) {
        return amount > 0.0 && apiKey != null && !apiKey.isBlank();
    }
}
```

Step 3: Auto-configuration class.
```java
package com.example.autoconfigure.payment;

import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;

@AutoConfiguration
@ConditionalOnClass(PaymentGatewayClient.class)
@EnableConfigurationProperties(PaymentGatewayProperties.class)
public class PaymentGatewayAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    @ConditionalOnProperty(prefix = "gateway.payment", name = "api-key")
    public PaymentGatewayClient paymentGatewayClient(PaymentGatewayProperties properties) {
        return new PaymentGatewayClient(
            properties.getEndpointUrl(),
            properties.getTimeoutMs(),
            properties.getApiKey()
        );
    }
}
```

Step 4: Register in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`:
```text
com.example.autoconfigure.payment.PaymentGatewayAutoConfiguration
```

---

## 4. application.yml and application.properties

### Syntax and Hierarchical Structure
Spring Boot supports both flat properties (`application.properties`) and hierarchical YAML (`application.yml`).

```yaml
server:
  port: 8443
  servlet:
    context-path: /api/v1
  shutdown: graceful

spring:
  application:
    name: order-service
  datasource:
    url: jdbc:postgresql://localhost:5432/orderdb
    username: order_user
    password: secret_password
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
```

### Profile-Specific Configurations
Spring Boot loads properties using the naming pattern `application-{profile}.yml`:
- `application.yml`: Base configuration applied across all profiles.
- `application-dev.yml`: Local developer overrides (e.g., embedded H2, verbose SQL logging).
- `application-prod.yml`: Production overrides (strict timeouts, PostgreSQL, restricted actuator endpoints).

Multi-document YAML allows consolidating profiles into a single file:

```yaml
spring:
  application:
    name: order-service
---
spring:
  config:
    activate:
      on-profile: dev
server:
  port: 8080
spring:
  datasource:
    url: jdbc:h2:mem:orderdb;DB_CLOSE_DELAY=-1
---
spring:
  config:
    activate:
      on-profile: prod
server:
  port: 8443
spring:
  datasource:
    url: jdbc:postgresql://db.prod.internal:5432/orderdb
```

### Environment Variable Overrides
Spring Boot maps operating system environment variables to properties through relaxed binding:
- Replace dots (`.`) and hyphens (`-`) with underscores (`_`).
- Convert characters to uppercase.
- Array indexes use underscores: `app.servers[0]` becomes `APP_SERVERS_0`.

| Spring Property | Environment Variable Override |
| :--- | :--- |
| `server.port` | `SERVER_PORT=9090` |
| `spring.datasource.url` | `SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/orderdb` |
| `spring.datasource.hikari.maximum-pool-size` | `SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE=30` |
| `app.security.jwt.secret-key` | `APP_SECURITY_JWT_SECRET_KEY=long_random_base64_string` |

---

## 5. Configuration Properties

### `@ConfigurationProperties` vs `@Value`
- `@Value`: Good for simple, individual scalar values (`@Value("${app.timeout:1000}")`). Lacks type safety, structured validation, and nested object binding.
- `@ConfigurationProperties`: Strongly-typed, hierarchical binding to POJOs or Java Records. Supports JSR-380 validation, collection binding, and nested objects.

### Complex Binding with Validation
Java records provide an ideal immutable configuration model:

```java
package com.example.orderservice.config;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import java.time.Duration;
import java.util.List;
import java.util.Map;

@ConfigurationProperties(prefix = "app.order")
@Validated
public record OrderProcessingProperties(
    @NotBlank
    String defaultCurrency,

    @Min(1) @Max(500)
    int maxBatchSize,

    @NotNull
    Duration connectionTimeout,

    List<String> allowedChannels,

    Map<String, String> routingKeys,

    @Valid
    @NotNull
    RetryPolicy retryPolicy
) {
    public record RetryPolicy(
        @Min(0) int maxAttempts,
        @NotNull Duration backoffInterval,
        double backoffMultiplier
    ) {}
}
```

### Enabling Configuration Properties
Activate scanning in configuration classes:

```java
package com.example.orderservice.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(OrderProcessingProperties.class)
public class AppConfig {
}
```

YAML mapping:
```yaml
app:
  order:
    default-currency: USD
    max-batch-size: 100
    connection-timeout: 3s
    allowed-channels:
      - WEB
      - MOBILE
      - PARTNER_API
    routing-keys:
      express: priority-exchange
      standard: bulk-exchange
    retry-policy:
      max-attempts: 3
      backoff-interval: 500ms
      backoff-multiplier: 2.0
```

---

## 6. Spring Boot Profiles

### Profile Activation
Profiles isolate environments such as `local`, `dev`, `staging`, and `prod`.

Methods of activation:
1. Command-line argument:
   ```bash
   java -jar order-service.jar --spring.profiles.active=prod
   ```
2. JVM System Property:
   ```bash
   java -Dspring.profiles.active=staging -jar order-service.jar
   ```
3. Operating System Environment Variable:
   ```bash
   export SPRING_PROFILES_ACTIVE=prod
   ```
4. Programmatic activation via `SpringApplicationBuilder`:
   ```java
   public static void main(String[] args) {
       new org.springframework.boot.builder.SpringApplicationBuilder(OrderServiceApplication.class)
           .profiles("prod")
           .run(args);
   }
   ```

### Profile-Specific Beans with `@Profile`
```java
package com.example.orderservice.service;

public interface NotificationService {
    void sendNotification(String recipient, String message);
}
```

Development implementation:
```java
package com.example.orderservice.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

@Service
@Profile("dev")
public class MockNotificationService implements NotificationService {
    private static final Logger log = LoggerFactory.getLogger(MockNotificationService.class);

    @Override
    public void sendNotification(String recipient, String message) {
        log.info("[DEV MOCK] Simulated sending to {}: {}", recipient, message);
    }
}
```

Production implementation:
```java
package com.example.orderservice.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

@Service
@Profile("prod")
public class AwsSesNotificationService implements NotificationService {
    private static final Logger log = LoggerFactory.getLogger(AwsSesNotificationService.class);

    @Override
    public void sendNotification(String recipient, String message) {
        log.info("[PROD] Dispatched production email via AWS SES to {}", recipient);
    }
}
```

Profiles can use boolean logic:
```java
@Profile({"staging | prod"})
@Profile({"prod & !cloud"})
```

---

## 7. Embedded Tomcat

### Port and Network Binding
- Default port is 8080.
- Set port to `0` to allocate a dynamic random port at startup (ideal for parallel integration tests).

```yaml
server:
  port: 8443
  address: 0.0.0.0
```

### SSL/TLS Configuration
```yaml
server:
  port: 8443
  ssl:
    enabled: true
    key-store: classpath:keystore.p12
    key-store-password: changeit
    key-store-type: PKCS12
    key-alias: tomcat
    protocol: TLS
    enabled-protocols: TLSv1.3,TLSv1.2
    ciphers:
      - TLS_AES_256_GCM_SHA384
      - TLS_CHACHA20_POLY1305_SHA256
      - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
```

### Tomcat Thread Pool and Connector Tuning
```yaml
server:
  tomcat:
    threads:
      max: 200
      min-spare: 20
    max-connections: 8192
    accept-count: 100
    connection-timeout: 20000ms
    max-http-form-post-size: 2MB
```

### Switching from Tomcat to Undertow or Jetty
To switch from Tomcat to Undertow, exclude the Tomcat starter and include `spring-boot-starter-undertow`:

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

Undertow configuration in `application.yml`:
```yaml
server:
  undertow:
    threads:
      io: 16
      worker: 128
    buffer-size: 1024
    direct-buffers: true
```

---

## 8. Spring Boot Actuator

### Enabling Actuator Endpoints
Add `spring-boot-starter-actuator` to dependencies and configure endpoint visibility:

```yaml
management:
  server:
    port: 9090
  endpoints:
    web:
      exposure:
        include: health,info,metrics,env,beans,loggers,prometheus
      base-path: /actuator
  endpoint:
    health:
      show-details: always
      probes:
        enabled: true
```

### Custom HealthIndicator
Health indicators integrate with Kubernetes readiness and liveness probes.

```java
package com.example.orderservice.actuator;

import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

import java.net.HttpURLConnection;
import java.net.URI;

@Component
public class PaymentGatewayHealthIndicator implements HealthIndicator {

    private static final String GATEWAY_PING_URL = "https://payment.internal.net/health";

    @Override
    public Health health() {
        try {
            long start = System.currentTimeMillis();
            HttpURLConnection conn = (HttpURLConnection) URI.create(GATEWAY_PING_URL).toURL().openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(2000);
            conn.setReadTimeout(2000);
            int responseCode = conn.getResponseCode();
            long latency = System.currentTimeMillis() - start;

            if (responseCode == 200) {
                return Health.up()
                    .withDetail("gateway", "Payment Service")
                    .withDetail("latencyMs", latency)
                    .withDetail("statusCode", responseCode)
                    .build();
            } else {
                return Health.down()
                    .withDetail("gateway", "Payment Service")
                    .withDetail("statusCode", responseCode)
                    .build();
            }
        } catch (Exception ex) {
            return Health.down(ex)
                .withDetail("gateway", "Payment Service")
                .withDetail("error", ex.getMessage())
                .build();
        }
    }
}
```

### Custom InfoContributor
```java
package com.example.orderservice.actuator;

import org.springframework.boot.actuate.info.Info;
import org.springframework.boot.actuate.info.InfoContributor;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Map;

@Component
public class BuildInfoContributor implements InfoContributor {

    @Override
    public void contribute(Info.Builder builder) {
        builder.withDetail("service", Map.of(
            "name", "order-service",
            "version", "1.0.0",
            "deployTime", Instant.now().toString(),
            "region", "us-east-1"
        ));
    }
}
```

### Securing Actuator Endpoints
Actuator endpoints expose sensitive runtime details (`/actuator/env`, `/actuator/beans`, heap dumps) and must be protected:

```java
package com.example.orderservice.security;

import org.springframework.boot.actuate.autoconfigure.security.servlet.EndpointRequest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class ActuatorSecurityConfig {

    @Bean
    public SecurityFilterChain actuatorSecurityFilterChain(HttpSecurity http) throws Exception {
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

---

## 9. Logging

### Configuration via application.yml
Spring Boot uses SLF4J with Logback as the default logging engine:

```yaml
logging:
  level:
    root: INFO
    com.example.orderservice: DEBUG
    org.springframework.web: WARN
    org.hibernate.SQL: DEBUG
    org.hibernate.type.descriptor.sql.BasicBinder: TRACE
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n"
```

### Logback Configuration with logback-spring.xml
Create `src/main/resources/logback-spring.xml` for advanced rolling files and profiles:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration scan="true" scanPeriod="30 seconds">
    <property name="LOG_PATH" value="logs" />
    <property name="LOG_FILE" value="order-service" />

    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId:-NO_TRACE}] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <appender name="ROLLING_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${LOG_PATH}/${LOG_FILE}.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
            <fileNamePattern>${LOG_PATH}/${LOG_FILE}-%d{yyyy-MM-dd}.%i.log.gz</fileNamePattern>
            <maxFileSize>50MB</maxFileSize>
            <maxHistory>30</maxHistory>
            <totalSizeCap>5GB</totalSizeCap>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId}] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <springProfile name="dev">
        <root level="DEBUG">
            <appender-ref ref="CONSOLE" />
        </root>
    </springProfile>

    <springProfile name="prod">
        <root level="INFO">
            <appender-ref ref="CONSOLE" />
            <appender-ref ref="ROLLING_FILE" />
        </root>
    </springProfile>
</configuration>
```

### Mapped Diagnostic Context (MDC)
MDC attaches request-scoped identifiers (correlation IDs, user accounts, tenant IDs) across all log entries emitted on that execution thread.

```java
package com.example.orderservice.filter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

@Component
public class CorrelationIdFilter extends OncePerRequestFilter {

    public static final String CORRELATION_HEADER = "X-Correlation-Id";
    public static final String MDC_KEY = "traceId";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String correlationId = request.getHeader(CORRELATION_HEADER);
        if (correlationId == null || correlationId.isBlank()) {
            correlationId = UUID.randomUUID().toString();
        }

        MDC.put(MDC_KEY, correlationId);
        response.setHeader(CORRELATION_HEADER, correlationId);
        try {
            filterChain.doFilter(request, response);
        } finally {
            MDC.remove(MDC_KEY);
        }
    }
}
```

---

## 10. DevTools

### Architecture and Classloader Separation
Adding `spring-boot-devtools` accelerates local iteration:
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-devtools</artifactId>
    <scope>runtime</scope>
    <optional>true</optional>
</dependency>
```

DevTools uses two classloaders:
- Base Classloader: Loads third-party JARs and dependencies that never change during development.
- Restart Classloader: Loads compiled application classes in `target/classes`.

When code changes and the project compiles, DevTools discards only the restart classloader and spins up a new child `ApplicationContext`. This restart takes 500-1500ms rather than a cold 10-second JVM bootstrap.

### DevTools Features
1. Automatic Cache Disabling: Overrides default caching for template engines (Thymeleaf, FreeMarker) and static resources so changes reflect instantly on page refresh.
2. LiveReload: Embeds a LiveReload server on port 35729 that triggers automatic browser refreshes upon file modifications.
3. Property Overrides: Automatically configures `spring.thymeleaf.cache=false` and `spring.web.resources.cache.period=0`.
4. DevTools is automatically excluded when creating a fully packaged fat JAR via `spring-boot-maven-plugin`.

---

## 11. Testing in Spring Boot

### Test Starters and Annotations
`spring-boot-starter-test` aggregates:
- JUnit 5 (Jupiter engine)
- AssertJ fluent assertion library
- Mockito mocking framework
- JSONassert and JsonPath
- Spring Test and Spring Boot Test utilities

### `@SpringBootTest` (Full Integration Test)
Bootstraps the complete `ApplicationContext` with all beans, repositories, and listeners.

```java
package com.example.orderservice;

import com.example.orderservice.model.Order;
import com.example.orderservice.repository.OrderRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class OrderIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private OrderRepository orderRepository;

    @Test
    void shouldCreateAndFetchOrder() {
        Order order = new Order(null, "CUST-100", 250.00, "CONFIRMED");
        ResponseEntity<Order> response = restTemplate.postForEntity("/orders", order, Order.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getId()).isNotNull();

        assertThat(orderRepository.findById(response.getBody().getId())).isPresent();
    }
}
```

### Slice Tests

#### `@WebMvcTest`
Tests the web layer in isolation without loading repositories or databases.

```java
package com.example.orderservice.controller;

import com.example.orderservice.model.Order;
import com.example.orderservice.service.OrderService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @Test
    void shouldReturnOrderWhenFound() throws Exception {
        Order mockOrder = new Order(42L, "CUST-200", 99.95, "PENDING");
        given(orderService.getOrderById(42L)).willReturn(mockOrder);

        mockMvc.perform(get("/orders/42").accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(42))
            .andExpect(jsonPath("$.customerId").value("CUST-200"))
            .andExpect(jsonPath("$.totalAmount").value(99.95));
    }
}
```

#### `@DataJpaTest`
Bootstraps an in-memory database, scans `@Entity` classes, and configures Spring Data repositories. Each test runs in an automatically rolled back transaction.

```java
package com.example.orderservice.repository;

import com.example.orderservice.model.Order;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
class OrderRepositoryTest {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private OrderRepository orderRepository;

    @Test
    void shouldFindOrdersByCustomerId() {
        entityManager.persist(new Order(null, "CUST-1", 100.0, "PAID"));
        entityManager.persist(new Order(null, "CUST-1", 50.0, "PAID"));
        entityManager.persist(new Order(null, "CUST-2", 80.0, "PAID"));
        entityManager.flush();

        List<Order> results = orderRepository.findByCustomerId("CUST-1");
        assertThat(results).hasSize(2);
    }
}
```

---

## 12. Packaging and Deployment

### Fat JAR Structure
The standard Spring Boot executable archive contains classes, configuration files, and nested third-party library JARs:
- `BOOT-INF/classes/`: Application `.class` files and resource files.
- `BOOT-INF/lib/`: Transitive dependency JARs.
- `META-INF/MANIFEST.MF`: Specifies `Main-Class: org.springframework.boot.loader.JarLauncher` and `Start-Class: com.example.orderservice.OrderServiceApplication`.
- `org/springframework/boot/loader/`: Custom classloader capable of loading nested JARs directly from archive streams without extraction.

Execution:
```bash
java -jar target/order-service-1.0.0.jar
```

### Layered JARs for Optimized Docker Builds
When packaging standard fat JARs into Docker containers, a single line change in application code forces Docker to re-upload the entire 50-80MB layer containing all dependencies.

Spring Boot layered JARs separate layers by modification frequency:
1. `dependencies`: Third-party dependencies (rarely change).
2. `spring-boot-loader`: Internal Spring Boot launcher classes (rarely change).
3. `snapshot-dependencies`: Local snapshots or internal team libraries (occasional changes).
4. `application`: Application business logic and resources (frequent changes).

Enable layering in `pom.xml`:
```xml
<plugin>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-maven-plugin</artifactId>
    <configuration>
        <layers>
            <enabled>true</enabled>
        </layers>
    </configuration>
</plugin>
```

Production Multi-Stage Dockerfile:
```dockerfile
FROM eclipse-temurin:21-jre-alpine AS builder
WORKDIR /workspace
ARG JAR_FILE=target/order-service-1.0.0.jar
COPY ${JAR_FILE} application.jar
RUN java -Djarmode=layertools -jar application.jar extract

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring

COPY --from=builder /workspace/dependencies/ ./
COPY --from=builder /workspace/spring-boot-loader/ ./
COPY --from=builder /workspace/snapshot-dependencies/ ./
COPY --from=builder /workspace/application/ ./

ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

### Cloud Native Buildpacks
Build OCI-compliant container images without writing a Dockerfile:
```bash
mvn spring-boot:build-image -Dspring-boot.build-image.imageName=registry.internal.net/order-service:1.0.0
```

---

## 13. Externalized Configuration

### Property Resolution Hierarchy
Spring Boot resolves configuration values through a deterministic, ordered priority hierarchy. Later sources override earlier sources:

1. DevTools global settings properties (`~/.config/spring-boot/spring-boot-devtools.properties`).
2. `@TestPropertySource` annotations on test classes.
3. `@SpringBootTest#properties` annotation attribute.
4. Command line arguments (e.g., `--server.port=9090`).
5. `SPRING_APPLICATION_JSON` properties embedded in environment variable or system property.
6. `ServletConfig` init parameters.
7. `ServletContext` init parameters.
8. JNDI attributes from `java:comp/env`.
9. Java System properties (`System.getProperties()`, e.g., `-Dserver.port=9090`).
10. OS Environment variables (`SERVER_PORT=9090`).
11. `RandomValuePropertySource` (`random.*`).
12. Profile-specific application properties outside packaged JAR (`config/application-{profile}.properties`).
13. Profile-specific application properties inside packaged JAR (`classpath:/config/application-{profile}.properties`).
14. Application properties outside packaged JAR (`config/application.properties`).
15. Application properties inside packaged JAR (`classpath:/application.properties`).
16. `@PropertySource` annotations on `@Configuration` classes.
17. Default properties set via `SpringApplication.setDefaultProperties`.

### `spring.config.import`
Introduced in Spring Boot 2.4, `spring.config.import` manages additional configuration files, external secret mounts (e.g., Kubernetes volume mounts), and cloud configuration servers:

```yaml
spring:
  application:
    name: order-service
  config:
    import:
      - optional:file:/etc/secrets/database-credentials.properties
      - optional:configserver:http://config-server.internal:8888
      - optional:consul:localhost:8500
```
The `optional:` prefix ensures the application continues booting even if the specified file or config server is unreachable.

---

## 14. Graceful Shutdown

### Mechanics of Graceful Shutdown
In containerized cloud environments (Kubernetes), pods are terminated dynamically during rollouts and autoscaling. Without graceful shutdown:
- Incoming in-flight HTTP requests are abruptly terminated with connection resets (TCP RST).
- Running background tasks and asynchronous event listeners are killed mid-execution, causing data corruption.

When graceful shutdown is enabled:
1. The embedded servlet container stops accepting new network connections.
2. An active grace period begins during which currently in-flight requests are allowed to complete.
3. If all requests finish within the grace period, the server terminates immediately.
4. If requests exceed the grace period, remaining connections are forcefully closed and the application context shuts down.

### Configuration
```yaml
server:
  shutdown: graceful

spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

### Programmatic Shutdown Hooks
Register custom cleanup tasks that execute during container shutdown:

```java
package com.example.orderservice.lifecycle;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.SmartLifecycle;
import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicBoolean;

@Component
public class WorkerQueueConsumer implements SmartLifecycle {

    private static final Logger log = LoggerFactory.getLogger(WorkerQueueConsumer.class);
    private final AtomicBoolean running = new AtomicBoolean(false);

    @Override
    public void start() {
        running.set(true);
        log.info("Worker queue consumer started.");
    }

    @Override
    public void stop() {
        log.info("Stopping worker queue consumer and draining in-flight messages...");
        running.set(false);
    }

    @Override
    public boolean isRunning() {
        return running.get();
    }

    @Override
    public int getPhase() {
        return Integer.MAX_VALUE - 100;
    }
}
```

The `getPhase()` method dictates the shutdown sequence: beans with higher phase numbers stop before beans with lower phase numbers. This guarantees that web consumers terminate before database connection pools are closed.

# Jakarta EE and J2EE Enterprise Architecture

This module provides a production-grade guide to enterprise Java backend architectures, spanning legacy J2EE patterns, modern Jakarta EE specifications, containerized runtime environments, and concrete migration paths to modern Spring Boot ecosystems.

---

## Table of Contents
1. [History and Evolution](#1-history-and-evolution)
2. [Servlet Lifecycle](#2-servlet-lifecycle)
3. [Servlet Filters and Listeners](#3-servlet-filters-and-listeners)
4. [JSP and JSTL](#4-jsp-and-jstl)
5. [CDI (Contexts and Dependency Injection)](#5-cdi-contexts-and-dependency-injection)
6. [EJB (Enterprise JavaBeans)](#6-ejb-enterprise-javabeans)
7. [JPA in Jakarta EE](#7-jpa-in-jakarta-ee)
8. [JMS (Java Message Service)](#8-jms-java-message-service)
9. [JAX-RS (Jakarta REST)](#9-jax-rs-jakarta-rest)
10. [JAX-WS (SOAP Web Services)](#10-jax-ws-soap-web-services)
11. [JNDI (Java Naming and Directory Interface)](#11-jndi-java-naming-and-directory-interface)
12. [Connection Pooling](#12-connection-pooling)
13. [Bean Validation (Jakarta Validation)](#13-bean-validation-jakarta-validation)
14. [Application Servers](#14-application-servers)
15. [Migration: J2EE to Spring Boot](#15-migration-j2ee-to-spring-boot)

---

## 1. History and Evolution

Enterprise Java has undergone three distinct architectural eras: Java 2 Platform Enterprise Edition (J2EE), Java Platform Enterprise Edition (Java EE), and Jakarta EE. Understanding this trajectory is essential for maintaining enterprise systems, executing legacy migrations, and leveraging modern cloud-native runtimes.

```
+-----------------------------------------------------------------------------------------+
| J2EE Era (1999 - 2005)                                                                  |
| Heavyweight EJB 1.x/2.x, XML descriptors (ejb-jar.xml), distributed RMI objects        |
+-----------------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------------+
| Java EE Era (2006 - 2017)                                                               |
| Java EE 5 to 8, POJO programming, annotations (@Stateless, @Inject), lightweight JPA    |
+-----------------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------------+
| Jakarta EE Era (2018 - Present)                                                         |
| Eclipse Foundation stewardship, open standards, "jakarta.*" namespace, cloud profiles   |
+-----------------------------------------------------------------------------------------+
```

### The Transition Timeline

- **J2EE (1.2 to 1.4, 1999 - 2003):** Introduced by Sun Microsystems. Defined foundational standards including Servlets, JavaServer Pages (JSP), Enterprise JavaBeans (EJB), and Java Message Service (JMS). Suffered from excessive complexity, verbose XML descriptors, rigid home/remote interfaces, and extreme reliance on proprietary application server containers (IBM WebSphere, BEA WebLogic).
- **Java EE (5 to 8, 2006 - 2017):** Rebranded as Java EE. Introduced annotation-driven metadata, EJB 3.0 POJO models, Java Persistence API (JPA), and Contexts and Dependency Injection (CDI). Sun was acquired by Oracle in 2010. Java EE 7 (2013) introduced JAX-RS 2.0 and WebSockets, while Java EE 8 (2017) introduced JSON-B and HTTP/2 servlet support.
- **Eclipse Foundation Handoff (2017 - 2018):** Oracle transferred Java EE specifications, reference implementations (GlassFish), and test suites (TCKs) to the Eclipse Foundation to establish an open governance model. Because Oracle retained the legal trademark for the term "Java", the platform was formally renamed **Jakarta EE**.
- **The Namespace Shift (`javax.*` to `jakarta.*`):** Because the trademark dispute prevented the Eclipse Foundation from modifying package namespaces starting with `javax.*`, Jakarta EE 9 (released in 2020) executed a breaking namespace migration. All enterprise APIs (`javax.servlet.*`, `javax.persistence.*`, `javax.ws.rs.*`, `javax.transaction.*`) were moved to `jakarta.*`.
- **Jakarta EE 10 (2022):** Introduced the Jakarta EE Core Profile (a minimal profile designed for microservices and Ahead-of-Time compilation like Quarkus), Java 11/17 baseline, and module modularity.
- **Jakarta EE 11 (2024):** Set Java 21 as the runtime baseline, providing native integration with Virtual Threads (Project Loom) across servlet containers and asynchronous processing pipelines.

### Jakarta EE vs Spring Ecosystem

| Dimension | Jakarta EE | Spring Framework / Spring Boot |
|---|---|---|
| Governance | Vendor-neutral Eclipse Foundation committee | Broadcom (formerly Pivotal / SpringSource) |
| Architecture | Formal specifications with pluggable runtimes | Opinionated, unified implementation stack |
| Configuration | Standardized annotations and deployment descriptors | Auto-configuration, programmatic Java DSLs |
| Deployment Model | Historically WAR/EAR in Application Servers | Self-contained executable JAR with embedded server |
| Dependency Injection | Jakarta CDI (`@Inject`, `@Named`, `@ApplicationScoped`) | Spring IoC (`@Autowired`, `@Component`, `@Service`) |
| Persistence | Jakarta Persistence API (JPA) | Spring Data JPA on top of Hibernate/JPA |
| REST Standard | JAX-RS (`@Path`, `@GET`, `@Produces`) | Spring MVC (`@RestController`, `@GetMapping`) |

---

## 2. Servlet Lifecycle

The Java Servlet API is the bedrock of server-side Java web computing. All modern Java web frameworks, including Spring MVC and JAX-RS runtimes, operate either directly on top of servlets (e.g., Spring's `DispatcherServlet`) or emulate their lifecycle abstractions.

### The Single-Instance Multi-Thread Model

A servlet container (e.g., Apache Tomcat, Eclipse Jetty, Red Hat Undertow) manages the entire lifecycle of a servlet instance. In standard deployments, the container instantiates **only one instance** of each servlet class and handles concurrent incoming requests by dispatching separate worker threads through that single instance.

```
Client Request 1 ----+
                     |
Client Request 2 ----+---> [ Servlet Container Worker Pool ] ---> [ Single Servlet Instance ]
                     |                                                   |
Client Request 3 ----+                                            service(req, res)
                                                                         |
                                                                  doGet() / doPost()
```

### Lifecycle Methods

1. **Loading and Instantiation:** The container loads the servlet class either on container startup (if configured with `load-on-startup >= 0`) or lazily upon the arrival of the first request mapped to that servlet.
2. **Initialization (`init`):** The container calls `init(ServletConfig config)` exactly once. This method allows the servlet to read initialization parameters, establish resource handles, and initialize local caches. If `init()` throws a `ServletException`, the container drops the instance and does not route traffic to it.
3. **Request Servicing (`service`):** For every incoming HTTP request, the container allocates a thread from its connection thread pool and invokes `service(ServletRequest, ServletResponse)`. The `HttpServlet` base class unpacks the request, resolves the HTTP method verb, and delegates to the appropriate handler: `doGet()`, `doPost()`, `doPut()`, `doDelete()`, `doHead()`, or `doOptions()`.
4. **Destruction (`destroy`):** When the application is undeployed, stopped, or the container shuts down, the container invokes `destroy()`. This method provides an opportunity to release JDBC connections, stop background threads, and flush file handles before garbage collection.

### Production Servlet Example

```java
package com.example.enterprise.servlet;

import jakarta.servlet.ServletConfig;
import jakarta.servlet.ServletContext;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebInitParam;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicLong;

@WebServlet(
    name = "OrderProcessingServlet",
    urlPatterns = {"/api/v1/orders/*"},
    loadOnStartup = 1,
    initParams = {
        @WebInitParam(name = "defaultCurrency", value = "USD"),
        @WebInitParam(name = "maxBatchSize", value = "250")
    }
)
public class OrderProcessingServlet extends HttpServlet {

    private final AtomicLong requestCounter = new AtomicLong(0);
    private String defaultCurrency;
    private int maxBatchSize;

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        this.defaultCurrency = config.getInitParameter("defaultCurrency");
        String batchLimit = config.getInitParameter("maxBatchSize");
        this.maxBatchSize = (batchLimit != null) ? Integer.parseInt(batchLimit) : 100;

        ServletContext context = config.getServletContext();
        context.log("OrderProcessingServlet initialized. Default currency: " + defaultCurrency);
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        long currentCount = requestCounter.incrementAndGet();

        response.setContentType("application/json");
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.setStatus(HttpServletResponse.SC_OK);

        String pathInfo = request.getPathInfo();
        String orderId = (pathInfo != null && pathInfo.length() > 1) ? pathInfo.substring(1) : "all";

        try (PrintWriter writer = response.getWriter()) {
            writer.write(String.format(
                "{\"orderId\":\"%s\",\"currency\":\"%s\",\"processedRequests\":%d,\"timestamp\":\"%s\"}",
                escapeJson(orderId),
                escapeJson(defaultCurrency),
                currentCount,
                Instant.now().toString()
            ));
            writer.flush();
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());

        String clientBatchSizeHeader = request.getHeader("X-Batch-Size");
        int requestedBatch = (clientBatchSizeHeader != null) ? Integer.parseInt(clientBatchSizeHeader) : 1;

        if (requestedBatch > maxBatchSize) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            try (PrintWriter writer = response.getWriter()) {
                writer.write(String.format("{\"error\":\"Requested batch %d exceeds limit of %d\"}",
                        requestedBatch, maxBatchSize));
            }
            return;
        }

        response.setStatus(HttpServletResponse.SC_ACCEPTED);
        try (PrintWriter writer = response.getWriter()) {
            writer.write("{\"status\":\"ACCEPTED\",\"message\":\"Order queued for processing\"}");
        }
    }

    @Override
    public void destroy() {
        ServletContext context = getServletContext();
        context.log("OrderProcessingServlet shutting down. Final request count: " + requestCounter.get());
        super.destroy();
    }

    private String escapeJson(String input) {
        if (input == null) return "";
        return input.replace("\"", "\\\"");
    }
}
```

### Asynchronous Servlets

Introduced in Servlet 3.0, asynchronous servlet processing permits the servlet thread to return immediately to the container pool while long-running I/O or background computations run on a dedicated worker thread pool.

```java
package com.example.enterprise.servlet;

import jakarta.servlet.AsyncContext;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@WebServlet(urlPatterns = "/api/v1/async-report", asyncSupported = true)
public class AsyncReportServlet extends HttpServlet {

    private final ExecutorService reportWorkerPool = Executors.newFixedThreadPool(8);

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        final AsyncContext asyncContext = request.startAsync();
        asyncContext.setTimeout(10000); // 10 second timeout

        CompletableFuture.supplyAsync(() -> {
            try {
                // Simulate intensive analytical aggregation
                Thread.sleep(1500);
                return "{\"reportStatus\":\"COMPLETED\",\"metrics\":[104, 208, 412]}";
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new IllegalStateException("Calculation interrupted", e);
            }
        }, reportWorkerPool).thenAccept(resultPayload -> {
            try {
                HttpServletResponse asyncResponse = (HttpServletResponse) asyncContext.getResponse();
                asyncResponse.setContentType("application/json");
                asyncResponse.setCharacterEncoding(StandardCharsets.UTF_8.name());
                asyncResponse.setStatus(HttpServletResponse.SC_OK);

                PrintWriter writer = asyncResponse.getWriter();
                writer.write(resultPayload);
                writer.flush();
            } catch (IOException e) {
                getServletContext().log("Failed to write async response", e);
            } finally {
                asyncContext.complete();
            }
        }).exceptionally(ex -> {
            HttpServletResponse asyncResponse = (HttpServletResponse) asyncContext.getResponse();
            asyncResponse.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            asyncContext.complete();
            return null;
        });
    }

    @Override
    public void destroy() {
        reportWorkerPool.shutdown();
        super.destroy();
    }
}
```

---

## 3. Servlet Filters and Listeners

Filters and Listeners provide interceptor patterns and event-driven lifecycle hooks without coupling cross-cutting concerns to servlet business logic.

```
[ Incoming Request ] ---> [ Filter 1 ] ---> [ Filter 2 ] ---> [ Target Servlet ]
                                                                     |
[ Outgoing Response ] <--- [ Filter 1 ] <--- [ Filter 2 ] <----------+
```

### Servlet Filters

A Filter intercepts requests before they reach the servlet and responses before they travel back to the client. The core interface is `jakarta.servlet.Filter`.

```java
package com.example.enterprise.filter;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.FilterConfig;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.util.UUID;

@WebFilter(filterName = "TelemetryAndSecurityFilter", urlPatterns = {"/*"})
public class TelemetryAndSecurityFilter implements Filter {

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        // Initialization logic for filter lifecycle
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;

        long startTime = System.nanoTime();
        String correlationId = httpRequest.getHeader("X-Correlation-ID");
        if (correlationId == null || correlationId.isBlank()) {
            correlationId = UUID.randomUUID().toString();
        }

        // Propagate tracing header downstream
        httpResponse.setHeader("X-Correlation-ID", correlationId);
        httpResponse.setHeader("X-Content-Type-Options", "nosniff");
        httpResponse.setHeader("X-Frame-Options", "DENY");

        try {
            chain.doFilter(request, response);
        } finally {
            long durationMs = (System.nanoTime() - startTime) / 1_000_000;
            httpRequest.getServletContext().log(String.format(
                "[%s] %s %s finished in %d ms with status %d",
                correlationId,
                httpRequest.getMethod(),
                httpRequest.getRequestURI(),
                durationMs,
                httpResponse.getStatus()
            ));
        }
    }

    @Override
    public void destroy() {
        // Cleanup resources
    }
}
```

### Lifecycle Listeners

Listeners react to discrete container lifecycle events:
- `ServletContextListener`: Fires when the web application context is initialized or destroyed.
- `ServletRequestListener`: Fires whenever an individual HTTP request enters and exits the web container.
- `HttpSessionListener`: Fires whenever an HTTP session is created, invalidated, or timed out.

```java
package com.example.enterprise.listener;

import jakarta.servlet.ServletContext;
import jakarta.servlet.ServletContextEvent;
import jakarta.servlet.ServletContextListener;
import jakarta.servlet.annotation.WebListener;
import jakarta.servlet.http.HttpSessionEvent;
import jakarta.servlet.http.HttpSessionListener;

import java.util.concurrent.atomic.AtomicInteger;

@WebListener
public class ApplicationLifecycleListener implements ServletContextListener, HttpSessionListener {

    private final AtomicInteger activeSessions = new AtomicInteger(0);

    @Override
    public void contextInitialized(ServletContextEvent sce) {
        ServletContext context = sce.getServletContext();
        context.log("Enterprise Application Context Initialized successfully.");
        context.setAttribute("ACTIVE_SESSION_COUNTER", activeSessions);
    }

    @Override
    public void contextDestroyed(ServletContextEvent sce) {
        ServletContext context = sce.getServletContext();
        context.log("Enterprise Application Context is terminating.");
    }

    @Override
    public void sessionCreated(HttpSessionEvent se) {
        int count = activeSessions.incrementAndGet();
        se.getSession().getServletContext().log("Session created. Active count: " + count);
    }

    @Override
    public void sessionDestroyed(HttpSessionEvent se) {
        int count = activeSessions.decrementAndGet();
        se.getSession().getServletContext().log("Session invalidated. Active count: " + count);
    }
}
```

---

## 4. JSP and JSTL

JavaServer Pages (JSP) provided server-side template rendering where HTML was interspersed with Java code. Although replaced in modern architectures by REST APIs and decoupled UI layers (or modern template engines like Thymeleaf), understanding JSP architecture is critical for maintaining legacy enterprise software.

### The JSP Lifecycle

When a client requests a `.jsp` file, the container executes a two-phase process:
1. **Translation & Compilation:** The container's JSP compiler (e.g., Apache Jasper in Tomcat) translates the `.jsp` template into a Java source file implementing `jakarta.servlet.jsp.HttpJspPage` (which extends `HttpServlet`). It then compiles this `.java` file into a `.class` bytecode file.
2. **Execution:** The compiled servlet executes standard `_jspService(HttpServletRequest, HttpServletResponse)` calls, writing HTML directly to the output stream.

### Scriptlets vs Expression Language (EL)

Legacy JSP relied on scriptlets (`<% code %>`, `<%= expression %>`, `<%! declaration %>`), embedding procedural Java directly inside markup. This caused unmaintainable spaghetti code, zero separation of concerns, and severe XSS security vulnerabilities.

Modern JSP forbids scriptlets in favor of Expression Language (EL) and the Jakarta Standard Tag Library (JSTL).

```xml
<!-- web.xml fragment disabling scriptlets -->
<jsp-config>
    <jsp-property-group>
        <url-pattern>*.jsp</url-pattern>
        <scripting-invalid>true</scripting-invalid>
    </jsp-property-group>
</jsp-config>
```

### JSTL Core Tags Example

```jsp
<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<!DOCTYPE html>
<html>
<head>
    <title>Customer Order Overview</title>
</head>
<body>
    <h1>Account Details: <c:out value="${customer.name}" /></h1>

    <c:choose>
        <c:when test="${customer.tier == 'PLATINUM'}">
            <p class="badge-vip">Priority VIP Account Status</p>
        </c:when>
        <c:when test="${customer.tier == 'GOLD'}">
            <p class="badge-gold">Preferred Account Status</p>
        </c:when>
        <c:otherwise>
            <p class="badge-standard">Standard Account Status</p>
        </c:otherwise>
    </c:choose>

    <h2>Recent Transactions</h2>
    <table border="1">
        <thead>
            <tr>
                <th>Order Ref</th>
                <th>Amount</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <c:forEach var="order" items="${customer.orders}">
                <tr>
                    <td><c:out value="${order.referenceNumber}" /></td>
                    <td><c:out value="${order.formattedAmount}" /></td>
                    <td>
                        <c:if test="${order.settled}">
                            <span style="color: green;">Settled</span>
                        </c:if>
                        <c:if test="${not order.settled}">
                            <span style="color: red;">Pending</span>
                        </c:if>
                    </td>
                </tr>
            </c:forEach>
        </tbody>
    </table>
</body>
</html>
```

---

## 5. CDI (Contexts and Dependency Injection)

CDI (Jakarta Contexts and Dependency Injection) is the official type-safe dependency injection specification of the Jakarta EE platform, implemented by containers such as JBoss Weld and Apache OpenWebBeans.

### CDI Scopes

| Scope | Annotation | Lifecycle Description |
|---|---|---|
| Request | `@RequestScoped` | Tied to a single HTTP request or messaging interaction. Destroyed when request completes. |
| Session | `@SessionScoped` | Tied to an `HttpSession`. Must implement `java.io.Serializable`. |
| Application | `@ApplicationScoped` | Singleton per application runtime. Shared among all clients and threads. |
| Conversation | `@ConversationScoped` | Explicitly demarcated boundaries spanning multiple HTTP requests (used in JSF). |
| Dependent | `@Dependent` | Default scope. Lifecycle is strictly tied to the object into which it is injected. |

### CDI Qualifiers and Producers

CDI eliminates string-based bean identifiers through type-safe qualifiers.

```java
package com.example.enterprise.cdi;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Qualifier;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.annotation.ElementType;

public class CDIArchitectureDemo {

    @Qualifier
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.FIELD, ElementType.METHOD, ElementType.TYPE, ElementType.PARAMETER})
    public @interface PriorityPayment {}

    @Qualifier
    @Retention(RetentionPolicy.RUNTIME)
    @Target({ElementType.FIELD, ElementType.METHOD, ElementType.TYPE, ElementType.PARAMETER})
    public @interface StandardPayment {}

    public interface PaymentGateway {
        void executePayment(double amount);
    }

    @ApplicationScoped
    @PriorityPayment
    public static class SwiftWireGateway implements PaymentGateway {
        @Override
        public void executePayment(double amount) {
            // Execution via SWIFT network
        }
    }

    @ApplicationScoped
    @StandardPayment
    public static class AutomatedClearingHouseGateway implements PaymentGateway {
        @Override
        public void executePayment(double amount) {
            // Execution via ACH network
        }
    }

    // Producer method creating configured third-party instances
    @ApplicationScoped
    public static class ConfigurationProducer {

        @Produces
        @ApplicationScoped
        public PaymentAuditor produceAuditor() {
            return new PaymentAuditor("audit-cluster.internal.net", 9092);
        }
    }

    public static class PaymentAuditor {
        private final String endpoint;
        private final int port;

        public PaymentAuditor(String endpoint, int port) {
            this.endpoint = endpoint;
            this.port = port;
        }

        public void logTransaction(String details) {
            // Send log event to audit cluster
        }
    }
}
```

### Consuming Injected Beans

```java
package com.example.enterprise.cdi;

import jakarta.enterprise.context.RequestScoped;
import jakarta.inject.Inject;

@RequestScoped
public class CheckoutService {

    @Inject
    @CDIArchitectureDemo.PriorityPayment
    private CDIArchitectureDemo.PaymentGateway paymentGateway;

    @Inject
    private CDIArchitectureDemo.PaymentAuditor auditor;

    public void processOrder(String orderId, double amount) {
        paymentGateway.executePayment(amount);
        auditor.logTransaction("Order processed: " + orderId + " for amount: " + amount);
    }
}
```

---

## 6. EJB (Enterprise JavaBeans)

Enterprise JavaBeans (EJB) was designed to provide declarative transactions, distributed remote computing (RMI), security, and concurrency management. In modern systems, EJBs are predominantly replaced by Spring Services or lightweight CDI beans, but legacy enterprise banking, logistics, and insurance systems run millions of lines of EJB code.

### Types of Session Beans

1. **Stateless Session Beans (`@Stateless`):**
   - Retain no client conversational state between method invocations.
   - The container maintains an instance pool; any thread can pick up any bean instance.
   - Automatically transactional and thread-safe.
2. **Stateful Session Beans (`@Stateful`):**
   - Retain state dedicated to a single client session across multiple method calls.
   - The container serializes and passivates stateful beans to disk when memory pressure occurs and activates them upon subsequent calls.
   - Requires explicit termination via `@Remove`.
3. **Singleton Session Beans (`@Singleton`):**
   - Exactly one instance per application.
   - Provides container-managed concurrency locks (`@Lock(LockType.READ)` vs `@Lock(LockType.WRITE)`).
   - Can initialize on application startup using `@Startup`.
4. **Message-Driven Beans (`@MessageDriven`):**
   - Asynchronous event listeners integrated directly with JMS destinations.

### EJB Implementation Example

```java
package com.example.enterprise.ejb;

import jakarta.annotation.Resource;
import jakarta.ejb.Lock;
import jakarta.ejb.LockType;
import jakarta.ejb.SessionContext;
import jakarta.ejb.Singleton;
import jakarta.ejb.Startup;
import jakarta.ejb.Stateless;
import jakarta.ejb.TransactionAttribute;
import jakarta.ejb.TransactionAttributeType;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

public class EnterpriseBeansSuite {

    @Stateless
    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public static class AccountTransferBean {

        @Resource
        private SessionContext sessionContext;

        public void executeWireTransfer(long sourceAccountId, long destAccountId, double amount) {
            try {
                // Perform database updates via EntityManager
                if (amount <= 0) {
                    sessionContext.setRollbackOnly();
                    throw new IllegalArgumentException("Transfer amount must be positive");
                }
                // Funds debited and credited
            } catch (Exception ex) {
                sessionContext.setRollbackOnly();
                throw new RuntimeException("Wire transfer failed", ex);
            }
        }
    }

    @Singleton
    @Startup
    public static class GlobalSystemConfigurationRegistry {

        private final Map<String, String> cache = new HashMap<>();

        @Lock(LockType.WRITE)
        public void setParameter(String key, String value) {
            cache.put(key, value);
        }

        @Lock(LockType.READ)
        public String getParameter(String key) {
            return cache.get(key);
        }

        @Lock(LockType.READ)
        public Map<String, String> getAllParameters() {
            return Collections.unmodifiableMap(new HashMap<>(cache));
        }
    }
}
```

---

## 7. JPA in Jakarta EE

The Jakarta Persistence API (JPA) standardizes object-relational mapping (ORM). In Jakarta EE, JPA integrates with the container's Java Transaction API (JTA) subsystem.

### Configuration via `persistence.xml`

Located under `META-INF/persistence.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<persistence xmlns="https://jakarta.ee/xml/ns/persistence"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="https://jakarta.ee/xml/ns/persistence https://jakarta.ee/xml/ns/persistence/persistence_3_0.xsd"
             version="3.0">

    <persistence-unit name="EnterpriseOrderPU" transaction-type="JTA">
        <provider>org.hibernate.jpa.HibernatePersistenceProvider</provider>
        <jta-data-source>java:comp/env/jdbc/OrderPostgresDS</jta-data-source>

        <class>com.example.enterprise.jpa.CustomerEntity</class>
        <class>com.example.enterprise.jpa.OrderEntity</class>

        <properties>
            <property name="hibernate.dialect" value="org.hibernate.dialect.PostgreSQLDialect"/>
            <property name="hibernate.hbm2ddl.auto" value="validate"/>
            <property name="hibernate.show_sql" value="false"/>
            <property name="hibernate.format_sql" value="true"/>
            <property name="hibernate.connection.pool_size" value="20"/>
        </properties>
    </persistence-unit>
</persistence>
```

### Container-Managed EntityManager

In Jakarta EE, developers do not manually create or close `EntityManagerFactory` or `EntityManager` instances. The container manages transactions and injects the context using `@PersistenceContext`.

```java
package com.example.enterprise.jpa;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManager;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.Table;
import jakarta.transaction.Transactional;

import java.math.BigDecimal;
import java.util.List;

@Entity
@Table(name = "customer_records")
class CustomerEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    private BigDecimal accountBalance;

    public Long getId() { return id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public BigDecimal getAccountBalance() { return accountBalance; }
    public void setAccountBalance(BigDecimal balance) { this.accountBalance = balance; }
}

@ApplicationScoped
public class CustomerRepository {

    @PersistenceContext(unitName = "EnterpriseOrderPU")
    private EntityManager entityManager;

    @Transactional(Transactional.TxType.REQUIRED)
    public void persistCustomer(String name, BigDecimal startingBalance) {
        CustomerEntity customer = new CustomerEntity();
        customer.setName(name);
        customer.setAccountBalance(startingBalance);
        entityManager.persist(customer);
    }

    @Transactional(Transactional.TxType.SUPPORTS)
    public List<CustomerEntity> findHighValueCustomers(BigDecimal threshold) {
        return entityManager.createQuery(
                "SELECT c FROM CustomerEntity c WHERE c.accountBalance >= :threshold",
                CustomerEntity.class)
                .setParameter("threshold", threshold)
                .getResultList();
    }
}
```

---

## 8. JMS (Java Message Service)

Jakarta Messaging (JMS) standardizes asynchronous, loosely coupled enterprise message exchange across distributed systems.

### Messaging Models

1. **Point-to-Point (Queue):** Each message is dispatched to exactly one consuming receiver. Messages remain queued until acknowledged.
2. **Publish/Subscribe (Topic):** Messages are broadcast to all active subscribers. Supports durable subscriptions that retain messages while a subscriber is offline.

```
Queue Model (Point-to-Point):
[ Producer ] ---> [ JMS Queue ] ---> [ Consumer 1 ] (Consumer 2 does not receive it)

Topic Model (Publish/Subscribe):
[ Producer ] ---> [ JMS Topic ] ---+---> [ Subscriber A ]
                                   +---> [ Subscriber B ]
```

### JMS 2.0 / 3.0 Producer Example

```java
package com.example.enterprise.jms;

import jakarta.annotation.Resource;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.jms.ConnectionFactory;
import jakarta.jms.JMSContext;
import jakarta.jms.Queue;

@ApplicationScoped
public class OrderEventProducer {

    @Resource(lookup = "java:comp/env/jms/ConnectionFactory")
    private ConnectionFactory connectionFactory;

    @Resource(lookup = "java:comp/env/jms/OrderDispatchQueue")
    private Queue orderQueue;

    public void dispatchOrderCreatedEvent(String orderJsonPayload) {
        try (JMSContext context = connectionFactory.createContext(JMSContext.AUTO_ACKNOWLEDGE)) {
            context.createProducer()
                   .setPriority(4)
                   .setTimeToLive(86400000L) // 24 hour retention
                   .setProperty("sourceSystem", "WAREHOUSE_PORTAL")
                   .send(orderQueue, orderJsonPayload);
        }
    }
}
```

### Message-Driven Bean (MDB) Consumer

```java
package com.example.enterprise.jms;

import jakarta.ejb.ActivationConfigProperty;
import jakarta.ejb.MessageDriven;
import jakarta.jms.JMSException;
import jakarta.jms.Message;
import jakarta.jms.MessageListener;
import jakarta.jms.TextMessage;

@MessageDriven(
    activationConfig = {
        @ActivationConfigProperty(propertyName = "destinationLookup", propertyValue = "jms/OrderDispatchQueue"),
        @ActivationConfigProperty(propertyName = "destinationType", propertyValue = "jakarta.jms.Queue"),
        @ActivationConfigProperty(propertyName = "acknowledgeMode", propertyValue = "Auto-acknowledge")
    }
)
public class OrderNotificationConsumer implements MessageListener {

    @Override
    public void onMessage(Message message) {
        try {
            if (message instanceof TextMessage textMessage) {
                String payload = textMessage.getText();
                String source = textMessage.getStringProperty("sourceSystem");
                processOrderPayload(payload, source);
            }
        } catch (JMSException e) {
            throw new IllegalStateException("Failed to process incoming JMS message", e);
        }
    }

    private void processOrderPayload(String payload, String source) {
        // Business logic parsing JSON payload
    }
}
```

### JMS vs Apache Kafka

| Capability | Jakarta JMS | Apache Kafka |
|---|---|---|
| Architecture | Broker-centric push queue | Distributed append-only commit log |
| Consumption Model | Message consumed and deleted from broker | Offsets tracked by consumer; log retained |
| Ordering | Strict ordering per queue, broken across concurrent consumers | Strict ordering per partition |
| Scale Capacity | Thousands of messages/sec per broker | Millions of messages/sec across partitions |
| Consumer State | Broker tracks acknowledgments | Client maintains commit offset |

---

## 9. JAX-RS (Jakarta REST)

Jakarta RESTful Web Services (JAX-RS) is the standard API for building HTTP endpoints in Jakarta EE, implemented by Jersey (reference implementation), RESTEasy (WildFly/Quarkus), and Apache CXF.

### JAX-RS Resource Implementation

```java
package com.example.enterprise.rest;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.HeaderParam;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.core.UriInfo;

import java.net.URI;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Path("/v1/inventories")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class InventoryResource {

    private static final Map<String, Integer> STOCK_DB = new ConcurrentHashMap<>();

    static {
        STOCK_DB.put("SKU-1001", 45);
        STOCK_DB.put("SKU-1002", 0);
    }

    @GET
    @Path("/{sku}")
    public Response getStockLevel(
            @PathParam("sku") String sku,
            @QueryParam("includeReserved") boolean includeReserved,
            @HeaderParam("X-Tenant-ID") String tenantId) {

        Integer count = STOCK_DB.get(sku);
        if (count == null) {
            return Response.status(Response.Status.NOT_FOUND)
                           .entity("{\"error\":\"SKU not registered in catalog\"}")
                           .build();
        }

        return Response.ok(String.format("{\"sku\":\"%s\",\"quantity\":%d,\"tenant\":\"%s\"}",
                sku, count, tenantId != null ? tenantId : "DEFAULT")).build();
    }

    @POST
    public Response createInventoryItem(InventoryDto payload, @Context UriInfo uriInfo) {
        STOCK_DB.put(payload.sku(), payload.quantity());
        URI location = uriInfo.getAbsolutePathBuilder().path(payload.sku()).build();
        return Response.created(location).entity(payload).build();
    }

    @PUT
    @Path("/{sku}")
    public Response updateStock(@PathParam("sku") String sku, InventoryDto payload) {
        STOCK_DB.put(sku, payload.quantity());
        return Response.ok(payload).build();
    }

    @DELETE
    @Path("/{sku}")
    public Response removeStock(@PathParam("sku") String sku) {
        STOCK_DB.remove(sku);
        return Response.noContent().build();
    }

    public record InventoryDto(String sku, int quantity) {}
}
```

### Exception Mappers

JAX-RS handles unhandled exceptions uniformly via the `ExceptionMapper<E>` interface.

```java
package com.example.enterprise.rest;

import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;

@Provider
public class EntityNotFoundExceptionMapper implements ExceptionMapper<IllegalArgumentException> {

    @Override
    public Response toResponse(IllegalArgumentException exception) {
        return Response.status(Response.Status.BAD_REQUEST)
                .type(MediaType.APPLICATION_JSON)
                .entity(String.format("{\"error\":\"Invalid Input Parameter\",\"details\":\"%s\"}",
                        exception.getMessage()))
                .build();
    }
}
```

---

## 10. JAX-WS (SOAP Web Services)

Jakarta XML Web Services (JAX-WS) governs SOAP (Simple Object Access Protocol) RPC and document services. While REST dominates web APIs, SOAP remains pervasive in core banking (SWIFT interfaces), legacy healthcare (HL7), telecommunications, and government data exchanges.

### SOAP Envelope Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:pay="http://enterprise.example.com/payment">
    <soap:Header>
        <pay:SecurityToken>AUTH-TOKEN-99384-SECURE</pay:SecurityToken>
    </soap:Header>
    <soap:Body>
        <pay:ProcessTransferRequest>
            <pay:SourceAccountId>99104822</pay:SourceAccountId>
            <pay:DestinationAccountId>44810294</pay:DestinationAccountId>
            <pay:Amount>15000.00</pay:Amount>
        </pay:ProcessTransferRequest>
    </soap:Body>
</soap:Envelope>
```

### JAX-WS Web Service Implementation

```java
package com.example.enterprise.soap;

import jakarta.jws.WebMethod;
import jakarta.jws.WebParam;
import jakarta.jws.WebResult;
import jakarta.jws.WebService;
import jakarta.jws.soap.SOAPBinding;

@WebService(
    name = "PaymentServicePort",
    targetNamespace = "http://enterprise.example.com/payment",
    serviceName = "PaymentWebService"
)
@SOAPBinding(style = SOAPBinding.Style.DOCUMENT, use = SOAPBinding.Use.LITERAL)
public class PaymentWebServiceImpl {

    @WebMethod(operationName = "executeSettlement")
    @WebResult(name = "SettlementConfirmation")
    public SettlementResult executeSettlement(
            @WebParam(name = "accountNumber") String accountNumber,
            @WebParam(name = "settlementAmount") double settlementAmount) {

        if (settlementAmount <= 0) {
            throw new IllegalArgumentException("Amount must be greater than zero");
        }

        String transactionRef = "TX-" + System.currentTimeMillis();
        return new SettlementResult(transactionRef, "CONFIRMED", settlementAmount);
    }

    public static class SettlementResult {
        private String reference;
        private String status;
        private double amount;

        public SettlementResult() {}

        public SettlementResult(String reference, String status, double amount) {
            this.reference = reference;
            this.status = status;
            this.amount = amount;
        }

        public String getReference() { return reference; }
        public void setReference(String ref) { this.reference = ref; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        public double getAmount() { return amount; }
        public void setAmount(double amount) { this.amount = amount; }
    }
}
```

### JAX-WS (SOAP) vs JAX-RS (REST)

- **Protocol & Transport:** JAX-WS requires XML payloads strictly formatted as SOAP envelopes with WSDL schemas. JAX-RS leverages standard HTTP verbs and supports JSON, XML, Protobuf, or plaintext.
- **Contract Enforcement:** SOAP is strictly contract-driven through WSDL files, enabling compile-time client generation. REST relies on OpenAPI/Swagger as documentation rather than strict binary contracts.
- **Enterprise Standards:** SOAP includes formal specifications for WS-Security, WS-ReliableMessaging, and WS-AtomicTransaction.

---

## 11. JNDI (Java Naming and Directory Interface)

The Java Naming and Directory Interface (JNDI) provides a uniform API for binding and looking up enterprise resources, such as DataSources, JMS connection factories, and environment configurations.

### Architecture and Naming Contexts

Application servers host a centralized JNDI directory. Applications bind resources using the `java:comp/env/` namespace:
- `java:comp/env/jdbc/` -> Relational database data sources
- `java:comp/env/jms/` -> Messaging queues, topics, and factories
- `java:comp/env/mail/` -> JavaMail sessions

### Programmatic Resource Lookup

```java
package com.example.enterprise.jndi;

import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class JndiDatabaseClient {

    public void verifyDatabaseConnection() {
        InitialContext initialContext = null;
        try {
            initialContext = new InitialContext();
            Context environmentContext = (Context) initialContext.lookup("java:comp/env");
            DataSource dataSource = (DataSource) environmentContext.lookup("jdbc/CoreBankingDS");

            try (Connection connection = dataSource.getConnection();
                 PreparedStatement statement = connection.prepareStatement("SELECT 1");
                 ResultSet resultSet = statement.executeQuery()) {

                if (resultSet.next()) {
                    System.out.println("JNDI Connection successful: " + resultSet.getInt(1));
                }
            }
        } catch (NamingException | SQLException ex) {
            throw new IllegalStateException("Failed to resolve JNDI DataSource", ex);
        } finally {
            if (initialContext != null) {
                try {
                    initialContext.close();
                } catch (NamingException ignored) {
                }
            }
        }
    }
}
```

---

## 12. Connection Pooling

Opening physical database connections requires TCP three-way handshakes, TLS negotiation, authentication exchanges, and memory allocation on both client and database servers. A connection pool pre-allocates and recycles connections, eliminating connection overhead.

### Major Connection Pool Implementations

- **HikariCP:** Modern industry benchmark. Extreme high performance, zero-overhead collection wrappers, byte-code optimization, concurrent bag data structures. Default in Spring Boot 2 and 3.
- **Apache Commons DBCP2:** Stable and widely deployed; historically bundled in Apache Tomcat.
- **c3p0:** Legacy connection pool; popular in Hibernate 3/4 eras, known for automated statement caching and reconnection handling.

### Sizing Formula (Brett Wooldridge / PostgreSQL Formula)

Allocating hundreds of connections to a pool degrades database throughput due to CPU context switching and disk I/O contention.

$$\text{connections} = ((\text{core\_count} \times 2) + \text{effective\_spindle\_count})$$

For an 8-core database server with SSD storage:
$$\text{connections} = (8 \times 2) + 1 = 17$$

### Programmatic HikariCP Configuration

```java
package com.example.enterprise.pool;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Duration;

public class HikariPoolManager {

    private final HikariDataSource dataSource;

    public HikariPoolManager() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:postgresql://postgres-db.internal.net:5432/finance_db");
        config.setUsername("app_user");
        config.setPassword("SuperSecureSecret123!");
        config.setDriverClassName("org.postgresql.Driver");

        // Pool Sizing and Timeouts
        config.setMaximumPoolSize(16);
        config.setMinimumIdle(4);
        config.setIdleTimeout(Duration.ofMinutes(10).toMillis());
        config.setConnectionTimeout(Duration.ofSeconds(20).toMillis());
        config.setMaxLifetime(Duration.ofMinutes(30).toMillis());
        config.setLeakDetectionThreshold(Duration.ofSeconds(5).toMillis());

        // Performance optimizations
        config.addDataSourceProperty("cachePrepStmts", "true");
        config.addDataSourceProperty("prepStmtCacheSize", "250");
        config.addDataSourceProperty("prepStmtCacheSqlLimit", "2048");
        config.setPoolName("FinanceHikariPool");

        this.dataSource = new HikariDataSource(config);
    }

    public DataSource getDataSource() {
        return dataSource;
    }

    public void executeQuery() {
        try (Connection conn = dataSource.getConnection();
             PreparedStatement ps = conn.prepareStatement("SELECT count(*) FROM accounts");
             ResultSet rs = ps.executeQuery()) {
            if (rs.next()) {
                System.out.println("Total accounts: " + rs.getLong(1));
            }
        } catch (SQLException e) {
            throw new RuntimeException("Database execution error", e);
        }
    }

    public void shutdown() {
        if (dataSource != null && !dataSource.isClosed()) {
            dataSource.close();
        }
    }
}
```

---

## 13. Bean Validation (Jakarta Validation)

Jakarta Validation standardizes declarative metadata constraints on Java beans, validating input payloads before executing domain logic.

### Built-in Annotations and Validation Groups

```java
package com.example.enterprise.validation;

import jakarta.validation.Constraint;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import jakarta.validation.Payload;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.math.BigDecimal;

public class ValidationCatalog {

    public interface OnCreateGroup {}
    public interface OnUpdateGroup {}

    // Custom Annotation Definition
    @Target({ElementType.FIELD, ElementType.PARAMETER})
    @Retention(RetentionPolicy.RUNTIME)
    @Documented
    @Constraint(validatedBy = TaxIdValidator.class)
    public @interface ValidTaxIdentifier {
        String message() default "Invalid Tax Identifier format. Expected XX-XXXXXXX";
        Class<?>[] groups() default {};
        Class<? extends Payload>[] payload() default {};
    }

    // Constraint Validator Implementation
    public static class TaxIdValidator implements ConstraintValidator<ValidTaxIdentifier, String> {
        private static final java.util.regex.Pattern TAX_PATTERN =
                java.util.regex.Pattern.compile("^\\d{2}-\\d{7}$");

        @Override
        public boolean isValid(String value, ConstraintValidatorContext context) {
            if (value == null) return false;
            return TAX_PATTERN.matcher(value).matches();
        }
    }

    // Domain DTO
    public static class AccountRegistrationDto {

        @NotNull(groups = OnUpdateGroup.class)
        private Long id;

        @NotBlank(message = "Company name must not be blank")
        @Size(min = 2, max = 100)
        private String companyName;

        @NotBlank
        @Email(message = "Contact email must be a valid RFC 5322 address")
        private String contactEmail;

        @NotNull
        @ValidTaxIdentifier
        private String taxIdentifier;

        @NotNull
        @DecimalMin(value = "0.00", inclusive = true)
        private BigDecimal creditLimit;

        public Long getId() { return id; }
        public void setId(Long id) { this.id = id; }
        public String getCompanyName() { return companyName; }
        public void setCompanyName(String name) { this.companyName = name; }
        public String getContactEmail() { return contactEmail; }
        public void setContactEmail(String email) { this.contactEmail = email; }
        public String getTaxIdentifier() { return taxIdentifier; }
        public void setTaxIdentifier(String taxId) { this.taxIdentifier = taxId; }
        public BigDecimal getCreditLimit() { return creditLimit; }
        public void setCreditLimit(BigDecimal limit) { this.creditLimit = limit; }
    }
}
```

### Programmatic Validation Execution

```java
package com.example.enterprise.validation;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;

import java.math.BigDecimal;
import java.util.Set;

public class ValidationRunner {

    public static void main(String[] args) {
        ValidatorFactory factory = Validation.buildDefaultValidatorFactory();
        Validator validator = factory.getValidator();

        ValidationCatalog.AccountRegistrationDto dto = new ValidationCatalog.AccountRegistrationDto();
        dto.setCompanyName("Acme Logistics");
        dto.setContactEmail("invalid-email-address");
        dto.setTaxIdentifier("99-1234567");
        dto.setCreditLimit(new BigDecimal("-50.00"));

        Set<ConstraintViolation<ValidationCatalog.AccountRegistrationDto>> violations =
                validator.validate(dto);

        for (ConstraintViolation<ValidationCatalog.AccountRegistrationDto> violation : violations) {
            System.err.println("Property: " + violation.getPropertyPath() +
                               " | Violation: " + violation.getMessage());
        }
    }
}
```

---

## 14. Application Servers

Traditional enterprise Java architecture relied on centralized multi-tenant application servers. Modern cloud architecture favors single-application microservices with embedded web containers.

### Application Server Landscape

- **WildFly (formerly JBoss AS):** Red Hat's open-source, modular application server based on the JBoss Modules architecture. Lightweight and fast boot times compared to legacy alternatives.
- **GlassFish:** The Eclipse Foundation's official reference implementation for Jakarta EE specifications.
- **Oracle WebLogic & IBM WebSphere:** Commercial heavyweights. Dominated Fortune 500 financial and government environments for two decades. Provide proprietary clustering, administration consoles, and JMX orchestration.
- **Payara Server:** High-performance, production-ready fork of GlassFish with 24/7 commercial support and cloud optimizations.
- **Apache TomEE:** Apache Tomcat integrated with OpenEJB, OpenWebBeans, and ActiveMQ to pass Web Profile compliance.

### Packaging Formats: WAR vs EAR

```
WAR Deployment Structure (Single Web Application):
myapp.war
|-- META-INF/
|   `-- MANIFEST.MF
|-- WEB-INF/
|   |-- web.xml (Deployment Descriptor)
|   |-- classes/ (Compiled Servlets, Entities, Controllers)
|   |-- lib/ (Application-scoped third-party JARs)
|   `-- beans.xml (CDI activator)
`-- index.jsp / static assets

EAR Deployment Structure (Enterprise Application):
enterprise-suite.ear
|-- META-INF/
|   |-- application.xml (Declares child web and ejb modules)
|   `-- MANIFEST.MF
|-- core-ejb-services.jar (EJB business beans & persistence.xml)
|-- public-web-portal.war (Servlets, JSPs, Web filters)
|-- internal-admin.war (Administrative console)
`-- lib/ (Shared enterprise libraries loaded across all modules)
```

### The Architectural Shift

Traditional app servers ran multiple independent applications within a single JVM. This model created severe classpath conflicts, complex debugging, fragile deployments where one crashing app compromised the entire server, and vendor lock-in.

Modern software delivery deploys self-contained container images (Docker/OCI) where a single Spring Boot or Quarkus process packages an embedded server (Tomcat, Undertow, Netty) running exactly one service per container.

---

## 15. Migration: J2EE to Spring Boot

Modernizing legacy J2EE/Java EE applications into Spring Boot requires systematically replacing container-managed services with POJO abstractions.

### Modernization Mapping Table

| Legacy Component (J2EE / Jakarta EE) | Spring Boot Modern Equivalent | Key Migration Action |
|---|---|---|
| `HttpServlet` / `doGet()` / `doPost()` | Spring MVC `@RestController` / `@GetMapping` | Replace request/response streams with typed DTO return objects |
| `@Stateless` / `@Stateful` EJB | Spring `@Service` / `@Component` | Replace EJB container transactions with `@Transactional` |
| `@PersistenceContext` / `persistence.xml` | Spring Data JPA / `JpaRepository` | Remove XML; define interfaces extending `JpaRepository<T, ID>` |
| JMS Message-Driven Beans (`@MessageDriven`) | Spring `@JmsListener` or Spring for Apache Kafka | Convert MDB listeners to annotated method event handlers |
| JNDI DataSource (`InitialContext.lookup`) | Spring Boot HikariCP auto-configuration | Define `spring.datasource.*` properties in `application.yml` |
| `web.xml` / Servlet Filters | `FilterRegistrationBean` / Spring Security | Replace XML filters with `SecurityFilterChain` beans |
| SOAP Web Services (`@WebService`) | Spring-WS / Spring MVC REST API | Modernize to JSON REST or wrap with Spring-WS endpoints |

### Step-by-Step Code Transformation

#### Step 1: EJB to Spring Service

*Legacy Stateless EJB:*
```java
// Legacy EJB
package com.example.legacy;

import jakarta.ejb.Stateless;
import jakarta.ejb.TransactionAttribute;
import jakarta.ejb.TransactionAttributeType;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;

@Stateless
public class LegacyPaymentBean {

    @PersistenceContext(unitName = "FinancePU")
    private EntityManager em;

    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public void processPayment(Long accountId, Double amount) {
        // Business logic interacting with EntityManager
    }
}
```

*Modernized Spring Boot Service:*
```java
// Modern Spring Boot Service
package com.example.modern.service;

import com.example.modern.repository.AccountRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ModernPaymentService {

    private final AccountRepository accountRepository;

    public ModernPaymentService(AccountRepository accountRepository) {
        this.accountRepository = accountRepository;
    }

    @Transactional
    public void processPayment(Long accountId, Double amount) {
        var account = accountRepository.findById(accountId)
                .orElseThrow(() -> new IllegalArgumentException("Account not found: " + accountId));
        account.debit(amount);
        accountRepository.save(account);
    }
}
```

#### Step 2: JAX-RS / Servlet to Spring MVC

*Legacy JAX-RS Endpoint:*
```java
@Path("/orders")
@Produces(MediaType.APPLICATION_JSON)
public class OrderResource {
    @GET
    @Path("/{id}")
    public Response getOrder(@PathParam("id") String id) {
        return Response.ok(new OrderDto(id)).build();
    }
}
```

*Modernized Spring MVC Controller:*
```java
package com.example.modern.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    @GetMapping("/{id}")
    public ResponseEntity<OrderDto> getOrder(@PathVariable("id") String id) {
        return ResponseEntity.ok(new OrderDto(id));
    }

    public record OrderDto(String id) {}
}
```

#### Step 3: Persistence Configuration

*Legacy `persistence.xml` (deleted) replaced by `application.yml`:*

```yaml
spring:
  datasource:
    url: jdbc:postgresql://postgres.production.internal:5432/orders_db
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 16
      minimum-idle: 4
      connection-timeout: 20000
      idle-timeout: 300000
      max-lifetime: 1800000
  jpa:
    database-platform: org.hibernate.dialect.PostgreSQLDialect
    hibernate:
      ddl-auto: validate
    show-sql: false
    open-in-view: false
```

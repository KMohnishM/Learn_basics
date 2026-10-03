# Spring Boot Quick Reference Cheatsheet

## Starter Dependencies
| Starter Artifact ID | Core Included Technologies | Primary Use Case |
| :--- | :--- | :--- |
| `spring-boot-starter-web` | Spring MVC, Jackson, Embedded Tomcat | REST APIs and servlet web applications |
| `spring-boot-starter-webflux` | Spring WebFlux, Project Reactor, Netty | Reactive non-blocking streams and async APIs |
| `spring-boot-starter-data-jpa` | Hibernate ORM, Spring Data JPA, HikariCP | Relational database persistence with JPA |
| `spring-boot-starter-security` | Spring Security, Servlet Filters | Authentication, authorization, and CSRF protection |
| `spring-boot-starter-validation` | Jakarta Validation, Hibernate Validator | JSR-380 input and bean validation |
| `spring-boot-starter-actuator` | Micrometer, Spring Boot Actuator | Operational telemetry, health, and metrics |
| `spring-boot-starter-test` | JUnit 5, AssertJ, Mockito, JSONassert | Unit and integration testing suites |

## Actuator Endpoints
| Endpoint | Default Exposure | Purpose |
| :--- | :--- | :--- |
| `/actuator/health` | Yes (Public) | Summarizes application health status and probes |
| `/actuator/info` | No | Exposes arbitrary build, git, or service metadata |
| `/actuator/metrics` | No | Lists and queries Micrometer dimensional metrics |
| `/actuator/prometheus` | No | Formats metrics for Prometheus scraping |
| `/actuator/env` | No | Inspects Spring Environment configuration properties |
| `/actuator/beans` | No | Displays complete list of configured ApplicationContext beans |
| `/actuator/loggers` | No | Views and dynamically mutates logging levels at runtime |
| `/actuator/threaddump` | No | Performs and displays JVM thread state dump |

## Common application.yml Properties
```yaml
server:
  port: 8080
  shutdown: graceful
  servlet:
    context-path: /api/v1
  tomcat:
    threads:
      max: 200
      min-spare: 20

spring:
  application:
    name: order-service
  profiles:
    active: dev
  datasource:
    url: jdbc:postgresql://localhost:5432/orderdb
    username: app_user
    password: secret_password
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate
    properties:
      hibernate.dialect: org.hibernate.dialect.PostgreSQLDialect

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: always
```

## Profile Activation Methods
| Mechanism | Syntax / Command |
| :--- | :--- |
| CLI Argument | `java -jar app.jar --spring.profiles.active=prod` |
| JVM System Property | `java -Dspring.profiles.active=prod -jar app.jar` |
| Environment Variable | `export SPRING_PROFILES_ACTIVE=prod` |
| application.yml | `spring.profiles.active: prod` |
| Test Execution | `@ActiveProfiles("test")` |

## Test Slice Annotations
| Annotation | Configured Components | Excluded Components |
| :--- | :--- | :--- |
| `@SpringBootTest` | Complete ApplicationContext, all beans | None |
| `@WebMvcTest` | `@Controller`, `@ControllerAdvice`, filters | `@Service`, `@Repository`, `@Entity` |
| `@DataJpaTest` | `@Entity`, Spring Data repositories, EntityManager | Controllers, standard service beans |
| `@JsonTest` | Jackson `ObjectMapper`, Serializers, Deserializers | Web and persistence infrastructure |
| `@RestClientTest` | `RestTemplateBuilder`, `MockRestServiceServer` | WebMvc, JPA, and general context beans |

# Module 06: RESTful APIs with Spring Boot 3 & Spring 6

This module provides a comprehensive, production-grade guide to designing, building, securing, and testing enterprise RESTful APIs using Spring Boot 3.x and Spring Framework 6.x.

---

## 1. REST Architectural Principles and Richardson Maturity Model

Representational State Transfer (REST) is an architectural style designed by Roy Fielding in his doctoral dissertation. REST is not a protocol or a standard; it is a set of architectural constraints that, when applied together, yield distributed hypermedia systems that scale predictably and evolve independently.

### The Six Architectural Constraints
1. **Client-Server Architecture**: Separation of concerns between user interface / state management (client) and data storage / business domain logic (server).
2. **Statelessness**: Every request from client to server must contain all the information necessary to understand and complete the request. The server must not store client conversation state between requests.
3. **Cacheability**: Responses must implicitly or explicitly define themselves as cacheable or non-cacheable (`Cache-Control`, `ETag`, `Last-Modified`) to prevent clients from reusing stale state.
4. **Uniform Interface**: The defining constraint of REST. It encompasses:
   - Resource identification in requests (URIs).
   - Manipulation of resources through representations (JSON, XML).
   - Self-descriptive messages (Media types, headers).
   - Hypermedia as the engine of application state (HATEOAS).
5. **Layered System**: A client cannot tell whether it is connected directly to the end server or to an intermediary (load balancer, API gateway, reverse proxy, CDN).
6. **Code-on-Demand (Optional)**: Servers can temporarily extend client functionality by transferring executable code (e.g., JavaScript).

### The Richardson Maturity Model

Leonard Richardson analyzed REST services and categorized them into four levels (0 through 3) based on their adherence to REST constraints:

#### Level 0: The Swamp of POX (Plain Old XML/JSON)
Uses HTTP merely as a transport mechanism for Remote Procedure Calls (RPC). A single URI and single HTTP verb (usually POST) receives all requests. Different operations are embedded in the message payload.
- Example: `POST /endpoint` with payload `{"action": "getUser", "id": 10}` or SOAP / XML-RPC.

#### Level 1: Resources
Introduces distinct URIs for individual resources, but still relies on a single verb (often POST or GET) for all actions.
- Example: `POST /users/create`, `POST /users/10/delete`, `POST /users/10/update`.

#### Level 2: HTTP Verbs
Utilizes standard HTTP verbs according to their standard semantics (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) and leverages HTTP status codes (`200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `404 Not Found`, `409 Conflict`) accurately.
- Example:
  - `GET /users/10` -> Retrieves user.
  - `PUT /users/10` -> Replaces user.
  - `DELETE /users/10` -> Deletes user.

#### Level 3: Hypermedia Controls (HATEOAS)
Responses provide not only data, but also hypermedia links informing the client what actions can be taken next and which endpoints to call to transition application state.
- Example:
```json
{
  "id": 1002,
  "status": "AWAITING_PAYMENT",
  "amount": 250.00,
  "_links": {
    "self": { "href": "https://api.example.com/orders/1002" },
    "payment": { "href": "https://api.example.com/orders/1002/payments" },
    "cancel": { "href": "https://api.example.com/orders/1002/cancellation" }
  }
}
```

### HTTP Verbs Semantics and Characteristics

| HTTP Method | CRUD Operation | Idempotent? | Safe? | Cacheable? | Typical Success Status |
|---|---|---|---|---|---|
| `GET` | Read / Retrieve | Yes | Yes | Yes | `200 OK` |
| `POST` | Create / Process | No | No | Only with explicit headers | `201 Created`, `200 OK` |
| `PUT` | Full Replace | Yes | No | No | `200 OK`, `204 No Content` |
| `PATCH` | Partial Update | No (by RFC) / Conditional | No | No | `200 OK`, `204 No Content` |
| `DELETE` | Remove | Yes | No | No | `204 No Content`, `200 OK` |
| `HEAD` | Read Headers Only | Yes | Yes | Yes | `200 OK` |
| `OPTIONS` | Discover Capabilities | Yes | Yes | No | `200 OK`, `204 No Content` |

---

## 2. @RestController Deep Dive

In Spring Web MVC, controllers handle incoming HTTP requests and generate responses.

### @RestController vs @Controller + @ResponseBody
`@RestController` is a convenience composed annotation introduced in Spring 4.0:
```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Controller
@ResponseBody
public @interface RestController {
    @AliasFor(annotation = Controller.class)
    String value() default "";
}
```
In a standard `@Controller`, method return values represent view names resolved by view resolvers (e.g., Thymeleaf, JSP templates). By applying `@ResponseBody` (which `@RestController` includes automatically), Spring bypasses view resolution and passes the returned domain object or DTO directly to `HttpMessageConverter` (typically Jackson `MappingJackson2HttpMessageConverter`) to serialize into JSON or XML.

### Mapping Annotations and Parameter Extraction

Spring provides explicit verb mappings:
- `@GetMapping`: Read resources
- `@PostMapping`: Create resources
- `@PutMapping`: Replace entire resource
- `@PatchMapping`: Partially modify resource
- `@DeleteMapping`: Remove resource

```java
package com.example.rest.controller;

import com.example.rest.dto.CustomerCreateRequest;
import com.example.rest.dto.CustomerPatchRequest;
import com.example.rest.dto.CustomerResponse;
import com.example.rest.service.CustomerService;
import jakarta.validation.Valid;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.util.UriComponentsBuilder;

import java.net.URI;
import java.util.List;

@RestController
@RequestMapping(path = "/api/v1/customers", produces = MediaType.APPLICATION_JSON_VALUE)
public class CustomerController {

    private final CustomerService customerService;

    public CustomerController(CustomerService customerService) {
        this.customerService = customerService;
    }

    // Path Variable: extracting unique resource identifier from URI path
    @GetMapping("/{id}")
    public ResponseEntity<CustomerResponse> getCustomerById(@PathVariable("id") Long id) {
        CustomerResponse customer = customerService.findById(id);
        return ResponseEntity.ok(customer);
    }

    // Query Parameters: filtering, sorting, pagination
    @GetMapping
    public ResponseEntity<List<CustomerResponse>> listCustomers(
            @RequestParam(name = "status", required = false, defaultValue = "ACTIVE") String status,
            @RequestParam(name = "page", defaultValue = "0") int page,
            @RequestParam(name = "size", defaultValue = "20") int size
    ) {
        List<CustomerResponse> customers = customerService.findAll(status, page, size);
        return ResponseEntity.ok(customers);
    }

    // Request Headers: inspecting tracking IDs, authentication tokens, API keys
    @GetMapping("/search")
    public ResponseEntity<List<CustomerResponse>> searchCustomers(
            @RequestParam("q") String query,
            @RequestHeader(name = "X-Correlation-ID", required = false) String correlationId,
            @RequestHeader(HttpHeaders.ACCEPT_LANGUAGE) String preferredLanguage
    ) {
        List<CustomerResponse> results = customerService.search(query, preferredLanguage, correlationId);
        return ResponseEntity.ok(results);
    }

    // Request Body: deserializing incoming JSON payload with validation
    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<CustomerResponse> createCustomer(
            @Valid @RequestBody CustomerCreateRequest request,
            UriComponentsBuilder uriBuilder
    ) {
        CustomerResponse created = customerService.create(request);
        URI location = uriBuilder.path("/api/v1/customers/{id}").buildAndExpand(created.id()).toUri();
        return ResponseEntity.created(location).body(created);
    }

    // Full replacement (PUT)
    @PutMapping(path = "/{id}", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<CustomerResponse> updateCustomer(
            @PathVariable("id") Long id,
            @Valid @RequestBody CustomerCreateRequest request
    ) {
        CustomerResponse updated = customerService.replace(id, request);
        return ResponseEntity.ok(updated);
    }

    // Partial modification (PATCH)
    @PatchMapping(path = "/{id}", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<CustomerResponse> patchCustomer(
            @PathVariable("id") Long id,
            @RequestBody CustomerPatchRequest patchRequest
    ) {
        CustomerResponse patched = customerService.patch(id, patchRequest);
        return ResponseEntity.ok(patched);
    }

    // Resource removal (DELETE)
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteCustomer(@PathVariable("id") Long id) {
        customerService.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}
```

---

## 3. ResponseEntity and HTTP Response Design

`ResponseEntity<T>` extends `HttpEntity<T>` and represents the entire HTTP response: status code, headers, and body.

### Common Builder Methods
- `ResponseEntity.ok(body)`: Returns status `200 OK` with payload.
- `ResponseEntity.created(uri).body(body)`: Returns status `201 Created`, attaches the `Location` header pointing to the new resource URI, and returns the created representation.
- `ResponseEntity.accepted().build()`: Returns status `202 Accepted` for asynchronous batch jobs.
- `ResponseEntity.noContent().build()`: Returns status `204 No Content` (used for successful DELETE or updates with no returned payload).
- `ResponseEntity.badRequest().build()`: Returns status `400 Bad Request`.
- `ResponseEntity.status(HttpStatus.CONFLICT).body(problemDetail)`: Custom status code.

### Adding Custom Headers and Conditional Caching
```java
@GetMapping("/{id}/statement")
public ResponseEntity<byte[]> downloadStatement(@PathVariable Long id) {
    byte[] pdfBytes = customerService.generateStatementPdf(id);
    String eTag = customerService.calculateStatementETag(id);

    HttpHeaders headers = new HttpHeaders();
    headers.setContentType(MediaType.APPLICATION_PDF);
    headers.setContentDispositionFormData("attachment", "statement-" + id + ".pdf");
    headers.setCacheControl("max-age=3600, must-revalidate");
    headers.setETag(eTag);

    return new ResponseEntity<>(pdfBytes, headers, HttpStatus.OK);
}
```

---

## 4. Request Validation with Jakarta Bean Validation

Spring Boot incorporates Jakarta Bean Validation (Hibernate Validator engine) to validate inputs before business logic executes.

### Maven Dependency
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

### Standard Bean Validation Annotations
- `@NotNull`: Value cannot be null (empty string or empty list is allowed).
- `@NotEmpty`: Cannot be null, and size/length must be greater than zero.
- `@NotBlank`: Cannot be null, and trimmed length must be greater than zero (for strings).
- `@Size(min = 2, max = 50)`: Validates length of strings, collections, arrays.
- `@Min(value)` / `@Max(value)`: Validates numerical lower/upper bounds.
- `@Positive` / `@PositiveOrZero`: Validates positive numeric values.
- `@Email`: Validates valid email syntax.
- `@Pattern(regexp = "...")`: Validates input against regular expression.
- `@Past` / `@Future`: Validates dates relative to current instant.

### Custom Validator Implementation
Suppose an API requires validating international tax identification numbers (e.g., VAT ID).

#### 1. Define the Constraint Annotation
```java
package com.example.rest.validation;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;
import java.lang.annotation.*;

@Documented
@Constraint(validatedBy = TaxIdValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidTaxId {
    String message() default "Invalid Tax Identification Number format";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

#### 2. Implement the ConstraintValidator
```java
package com.example.rest.validation;

import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import java.util.regex.Pattern;

public class TaxIdValidator implements ConstraintValidator<ValidTaxId, String> {

    private static final Pattern TAX_PATTERN = Pattern.compile("^[A-Z]{2}[0-9A-Z]{8,12}$");

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null) {
            return true; // Use @NotBlank alongside this if value is mandatory
        }
        return TAX_PATTERN.matcher(value).matches();
    }
}
```

### Group Validation with @Validated
Group validation allows applying different constraints to the same DTO depending on whether the action is an insert or update.

```java
public class ValidationGroups {
    public interface OnCreate {}
    public interface OnUpdate {}
}
```

```java
public record UserAccountDto(
    @Null(groups = ValidationGroups.OnCreate.class)
    @NotNull(groups = ValidationGroups.OnUpdate.class)
    Long id,

    @NotBlank(groups = {ValidationGroups.OnCreate.class, ValidationGroups.OnUpdate.class})
    @Email
    String email,

    @NotBlank(groups = ValidationGroups.OnCreate.class)
    @Size(min = 8, groups = ValidationGroups.OnCreate.class)
    String password
) {}
```

Controller using `@Validated`:
```java
@PostMapping
public ResponseEntity<Void> create(@Validated(ValidationGroups.OnCreate.class) @RequestBody UserAccountDto dto) {
    return ResponseEntity.status(HttpStatus.CREATED).build();
}

@PutMapping("/{id}")
public ResponseEntity<Void> update(
        @PathVariable Long id,
        @Validated(ValidationGroups.OnUpdate.class) @RequestBody UserAccountDto dto) {
    return ResponseEntity.ok().build();
}
```

---

## 5. Exception Handling and RFC 7807 (ProblemDetail)

In Spring 6 and Spring Boot 3, Spring natively adopted **RFC 7807 (Problem Details for HTTP APIs)** via the class `org.springframework.http.ProblemDetail`.

### Why RFC 7807?
Prior to RFC 7807, every development team created disparate JSON structures for error responses:
```json
// Company A:
{"error_code": 1004, "error_msg": "Not found"}
// Company B:
{"status": "FAILURE", "details": ["Not found"]}
```
RFC 7807 standardizes machine-readable error responses with five standard keys:
- `type`: URI reference identifying the problem type.
- `title`: Short human-readable summary.
- `status`: The HTTP status code.
- `detail`: Human-readable explanation specific to this occurrence.
- `instance`: URI reference identifying the specific occurrence of the problem.

### Global Exception Handler Using @RestControllerAdvice and ProblemDetail

```java
package com.example.rest.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;

import java.net.URI;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    // 1. Handling Domain Resource Not Found
    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleResourceNotFound(ResourceNotFoundException ex, WebRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("Resource Not Found");
        problem.setType(URI.create("https://api.example.com/errors/resource-not-found"));
        problem.setProperty("timestamp", Instant.now());
        if (request instanceof ServletWebRequest servletRequest) {
            problem.setInstance(URI.create(servletRequest.getRequest().getRequestURI()));
        }
        return problem;
    }

    // 2. Handling Business Rule Conflicts (e.g. Unique Constraint, Duplicate Email)
    @ExceptionHandler(BusinessConflictException.class)
    public ProblemDetail handleConflict(BusinessConflictException ex, WebRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        problem.setTitle("Business Logic Conflict");
        problem.setType(URI.create("https://api.example.com/errors/conflict"));
        problem.setProperty("errorCode", ex.getErrorCode());
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }

    // 3. Handling Bean Validation Failures (@Valid / @Validated)
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidationExceptions(MethodArgumentNotValidException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.BAD_REQUEST, 
                "Input validation failed for one or more fields"
        );
        problem.setTitle("Constraint Violation");
        problem.setType(URI.create("https://api.example.com/errors/validation-error"));

        Map<String, String> invalidFields = new HashMap<>();
        for (FieldError fieldError : ex.getBindingResult().getFieldErrors()) {
            invalidFields.put(fieldError.getField(), fieldError.getDefaultMessage());
        }
        problem.setProperty("invalidFields", invalidFields);
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }

    // 4. Catch-All for Unhandled Internal Server Errors
    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGeneralException(Exception ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.INTERNAL_SERVER_ERROR,
                "An unexpected internal error occurred. Please contact customer support."
        );
        problem.setTitle("Internal Server Error");
        problem.setType(URI.create("https://api.example.com/errors/internal-error"));
        problem.setProperty("timestamp", Instant.now());
        return problem;
    }
}
```

---

## 6. OpenAPI / Swagger Documentation with SpringDoc

SpringDoc OpenAPI (`springdoc-openapi-starter-webmvc-ui`) automates the generation of OpenAPI 3 specifications and Swagger UI interfaces by inspecting Spring MVC controllers and annotations at runtime.

### Maven Dependency
```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.5.0</version>
</dependency>
```

### OpenAPI Configuration Bean
```java
package com.example.rest.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        final String securitySchemeName = "bearerAuth";

        return new OpenAPI()
                .info(new Info()
                        .title("Enterprise Order Management API")
                        .version("v1.0.0")
                        .description("High-throughput RESTful service for managing customer accounts and orders.")
                        .contact(new Contact().name("API Platform Team").email("api-support@example.com"))
                        .license(new License().name("Apache 2.0").url("https://www.apache.org/licenses/LICENSE-2.0")))
                .addSecurityItem(new SecurityRequirement().addList(securitySchemeName))
                .components(new Components()
                        .addSecuritySchemes(securitySchemeName,
                                new SecurityScheme()
                                        .name(securitySchemeName)
                                        .type(SecurityScheme.Type.HTTP)
                                        .scheme("bearer")
                                        .bearerFormat("JWT")));
    }
}
```

### Documenting Controller Endpoints and Models
```java
package com.example.rest.controller;

import com.example.rest.dto.OrderRequest;
import com.example.rest.dto.OrderResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Tag(name = "Order Operations", description = "Endpoints for placing, retrieving, and canceling customer orders")
@RestController
@RequestMapping("/api/v1/orders")
public class OrderDocumentationExampleController {

    @Operation(summary = "Find order by ID", description = "Retrieves complete order record matching the supplied identifier")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Order located successfully",
                    content = @Content(mediaType = "application/json", schema = @Schema(implementation = OrderResponse.class))),
            @ApiResponse(responseCode = "404", description = "Order with the given ID was not found",
                    content = @Content(mediaType = "application/problem+json", schema = @Schema(implementation = ProblemDetail.class))),
            @ApiResponse(responseCode = "401", description = "Unauthenticated caller")
    })
    @GetMapping("/{orderId}")
    public ResponseEntity<OrderResponse> getOrder(
            @Parameter(description = "Unique numeric order identifier", required = true, example = "4201")
            @PathVariable Long orderId) {
        return ResponseEntity.ok(new OrderResponse(orderId, "COMPLETED", 150.00));
    }
}
```

---

## 7. Content Negotiation

Content negotiation enables an API to serve representations of the same resource in different formats (e.g., JSON, XML) based on what the client requests via the HTTP `Accept` header.

### Configuring Jackson XML Support
To support both JSON and XML responses, include the Jackson XML dataformat dependency:
```xml
<dependency>
    <groupId>com.fasterxml.jackson.dataformat</groupId>
    <artifactId>jackson-dataformat-xml</artifactId>
</dependency>
```

### Content Negotiation in Spring Web MVC
```java
package com.example.rest.controller;

import com.example.rest.dto.ProductReport;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/reports")
public class ContentNegotiationController {

    @GetMapping(
        path = "/products",
        produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE}
    )
    public ProductReport getProductReport() {
        return new ProductReport("InventorySummary", 4500, 128900.50);
    }
}
```
When a client requests `Accept: application/xml`, Spring serializes `ProductReport` into XML. When the client sends `Accept: application/json` (or no header), Jackson defaults to JSON.

---

## 8. Request and Response DTOs with MapStruct and Java Records

Exposing database domain entities directly in REST controllers leads to tight coupling, security leaks (e.g., exposing password hashes or internal IDs), and circular serialization errors. Data Transfer Objects (DTOs) decouple internal database schemas from external API contracts.

### Using Java Records for DTOs
Java 16+ records are immutable, transparent carriers for shallowly immutable data, automatically generating constructors, getters, `equals()`, `hashCode()`, and `toString()`.

```java
public record CreateUserRequest(
    @NotBlank String firstName,
    @NotBlank String lastName,
    @Email @NotBlank String email,
    @Size(min = 8) String password
) {}

public record UserResponse(
    Long id,
    String fullName,
    String email,
    Instant createdAt
) {}
```

### Entity Mapping Using MapStruct
MapStruct generates fast, compile-time mapping code without reflection or runtime overhead.

```xml
<dependency>
    <groupId>org.mapstruct</groupId>
    <artifactId>mapstruct</artifactId>
    <version>1.5.5.Final</version>
</dependency>
<dependency>
    <groupId>org.mapstruct</groupId>
    <artifactId>mapstruct-processor</artifactId>
    <version>1.5.5.Final</version>
    <scope>provided</scope>
</dependency>
```

```java
package com.example.rest.mapper;

import com.example.rest.dto.CreateUserRequest;
import com.example.rest.dto.UserResponse;
import com.example.rest.entity.UserEntity;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface UserMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "passwordHash", ignore = true)
    @Mapping(target = "createdAt", expression = "java(java.time.Instant.now())")
    UserEntity toEntity(CreateUserRequest request);

    @Mapping(target = "fullName", expression = "java(entity.getFirstName() + \" \" + entity.getLastName())")
    UserResponse toResponse(UserEntity entity);
}
```

---

## 9. API Versioning Strategies

As requirements evolve, APIs must change without breaking existing mobile clients or partner integrations.

### 1. URI Path Versioning (Recommended)
Embed version identifier directly in path: `/api/v1/users` vs `/api/v2/users`.
- **Pros**: Explicit, visible in logs, simple to route via API Gateways.
- **Cons**: Violates pure REST URI permanence (identifies representation rather than resource).

### 2. Request Header Versioning
Pass version in custom HTTP header: `X-API-VERSION: 2`.
```java
@GetMapping(path = "/users/{id}", headers = "X-API-VERSION=1")
public UserV1Response getUserV1(@PathVariable Long id) { ... }

@GetMapping(path = "/users/{id}", headers = "X-API-VERSION=2")
public UserV2Response getUserV2(@PathVariable Long id) { ... }
```
- **Pros**: Clean URIs.
- **Cons**: Difficult to test directly in standard browser bars.

### 3. Media Type (Content Negotiation) Versioning
Pass version via `Accept` header: `Accept: application/vnd.company.app-v1+json`.
```java
@GetMapping(path = "/users/{id}", produces = "application/vnd.company.app-v1+json")
public UserV1Response getMediaV1(@PathVariable Long id) { ... }

@GetMapping(path = "/users/{id}", produces = "application/vnd.company.app-v2+json")
public UserV2Response getMediaV2(@PathVariable Long id) { ... }
```
- **Pros**: Purest REST adherence (resource URI stays fixed; representation changes).
- **Cons**: High complexity for external consumers and proxy caching configurations.

---

## 10. HTTP Clients: RestClient vs WebClient vs RestTemplate

Spring Framework has evolved its client-side HTTP communication options:
1. `RestTemplate` (Spring 3.0): Synchronous, blocking client. In maintenance mode since Spring 5.0.
2. `WebClient` (Spring 5.0): Reactive, non-blocking client part of `spring-webflux`.
3. `RestClient` (Spring 6.1 / Spring Boot 3.2): Modern synchronous, fluent client designed as the modern replacement for `RestTemplate`.

### RestClient Implementation Example (Spring 6.1+)

```java
package com.example.rest.client;

import com.example.rest.dto.ExternalPaymentResponse;
import com.example.rest.dto.PaymentRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Service
public class PaymentGatewayClient {

    private final RestClient restClient;

    public PaymentGatewayClient(
            RestClient.Builder builder,
            @Value("${payment.gateway.base-url}") String baseUrl,
            @Value("${payment.gateway.api-key}") String apiKey) {
        this.restClient = builder
                .baseUrl(baseUrl)
                .defaultHeader("Authorization", "Bearer " + apiKey)
                .defaultHeader("Accept", MediaType.APPLICATION_JSON_VALUE)
                .build();
    }

    public ExternalPaymentResponse processPayment(PaymentRequest request) {
        return restClient.post()
                .uri("/v1/charges")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .onStatus(HttpStatusCode::is4xxClientError, (req, resp) -> {
                    throw new PaymentClientException("Payment failed: " + resp.getStatusCode());
                })
                .onStatus(HttpStatusCode::is5xxServerError, (req, resp) -> {
                    throw new PaymentServerException("Payment gateway unavailable");
                })
                .body(ExternalPaymentResponse.class);
    }
}
```

---

## 11. File Upload and Download

REST APIs frequently manage document ingestion and binary assets using `MultipartFile`.

### File Upload Controller with Constraints
Configure upload size limits in `application.properties`:
```properties
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=15MB
```

```java
package com.example.rest.controller;

import org.springframework.core.io.InputStreamResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/documents")
public class DocumentController {

    private final Path storageDirectory = Path.of(System.getProperty("java.io.tmpdir"), "uploads");

    public DocumentController() throws IOException {
        Files.createDirectories(storageDirectory);
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<String> uploadDocument(
            @RequestParam("file") MultipartFile file,
            @RequestParam("category") String category
    ) throws IOException {

        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body("Uploaded file cannot be empty");
        }

        String storedFilename = UUID.randomUUID() + "-" + file.getOriginalFilename();
        Path targetPath = storageDirectory.resolve(storedFilename);
        Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);

        return ResponseEntity.status(HttpStatus.CREATED).body(storedFilename);
    }

    @GetMapping("/{fileName}")
    public ResponseEntity<Resource> downloadDocument(@PathVariable String fileName) throws IOException {
        Path filePath = storageDirectory.resolve(fileName).normalize();
        File file = filePath.toFile();

        if (!file.exists()) {
            return ResponseEntity.notFound().build();
        }

        InputStreamResource resource = new InputStreamResource(new FileInputStream(file));

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + file.getName() + "\"")
                .contentLength(file.length())
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .body(resource);
    }
}
```

---

## 12. Pagination, Sorting, and Cursor-Based Navigation

Returning unbounded datasets leads to memory starvation and database exhaustion. APIs must support pagination and sorting.

### Spring Data Web Support (Offset-Based)
```java
@GetMapping
public ResponseEntity<Page<CustomerResponse>> listCustomers(
        @PageableDefault(page = 0, size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
        Pageable pageable
) {
    Page<CustomerResponse> page = customerService.findAll(pageable);
    return ResponseEntity.ok(page);
}
```
Client query: `GET /api/v1/customers?page=2&size=10&sort=lastName,asc`

### Cursor-Based (Keyset) Pagination
Offset-based pagination (`OFFSET 100000 LIMIT 20`) becomes slow on large datasets because the database engine must scan and discard 100,000 index entries.
Cursor pagination queries against an indexed sequential key:
`SELECT * FROM orders WHERE id > :cursor ORDER BY id ASC LIMIT :limit`

```java
public record CursorPage<T>(
    List<T> content,
    Long nextCursor,
    boolean hasMore
) {}

@GetMapping("/cursor")
public ResponseEntity<CursorPage<OrderResponse>> getOrdersByCursor(
        @RequestParam(name = "cursor", required = false) Long cursor,
        @RequestParam(name = "limit", defaultValue = "20") int limit
) {
    Long effectiveCursor = cursor != null ? cursor : 0L;
    List<OrderResponse> orders = orderService.fetchOrdersAfter(effectiveCursor, limit + 1);

    boolean hasMore = orders.size() > limit;
    List<OrderResponse> results = hasMore ? orders.subList(0, limit) : orders;
    Long nextCursor = results.isEmpty() ? null : results.get(results.size() - 1).id();

    return ResponseEntity.ok(new CursorPage<>(results, nextCursor, hasMore));
}
```

---

## 13. API Rate Limiting

To prevent Denial of Service (DoS) attacks, brute-force exploitation, and upstream service exhaustion, APIs must throttle requests.

### Rate Limiting with Bucket4j Token Bucket Algorithm
Each consumer holds a virtual bucket filled with tokens at a steady replenishment rate. Each request consumes one token. If the bucket is empty, the server returns HTTP `429 Too Many Requests`.

```xml
<dependency>
    <groupId>com.bucket4j</groupId>
    <artifactId>bucket4j-core</artifactId>
    <version>8.10.1</version>
</dependency>
```

```java
package com.example.rest.ratelimit;

import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.Refill;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class RateLimitingFilter extends OncePerRequestFilter {

    private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();

    private Bucket createNewBucket() {
        // Refill 50 tokens every 1 minute; capacity 50
        Refill refill = Refill.intervally(50, Duration.ofMinutes(1));
        Bandwidth limit = Bandwidth.classic(50, refill);
        return Bucket.builder().addLimit(limit).build();
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        // Resolve client key (API Key header or remote IP)
        String apiKey = request.getHeader("X-API-KEY");
        String key = (apiKey != null) ? apiKey : request.getRemoteAddr();

        Bucket bucket = buckets.computeIfAbsent(key, k -> createNewBucket());

        if (bucket.tryConsume(1)) {
            response.addHeader("X-Rate-Limit-Remaining", String.valueOf(bucket.getAvailableTokens()));
            filterChain.doFilter(request, response);
        } else {
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.setContentType("application/json");
            response.getWriter().write("{\"error\": \"Too many requests. Limit is 50 per minute.\"}");
        }
    }
}
```

---

## 14. API Idempotency and Safe POST

An HTTP method is **idempotent** if making multiple identical requests has the same intended effect on the server state as making a single request. `GET`, `PUT`, `DELETE`, and `HEAD` are idempotent by definition. `POST` is NOT idempotent by default.

When network timeouts occur during a payment or order submission POST, a client may retry the request. Without idempotency handling, the server may charge the customer twice or create duplicate records.

### Implementing Idempotency Key Pattern with Redis
The client generates a unique UUID (Idempotency Key) and sends it in the `Idempotency-Key` header:
`Idempotency-Key: e8a946b5-7798-4b71-b6a8-d9313db09312`

```java
package com.example.rest.idempotency;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;

@Service
public class IdempotencyService {

    private final StringRedisTemplate redisTemplate;

    public IdempotencyService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public boolean lockKey(String idempotencyKey, Duration timeout) {
        String key = "idempotency:" + idempotencyKey;
        // SETNX: Sets key only if not already present
        Boolean success = redisTemplate.opsForValue().setIfAbsent(key, "PROCESSING", timeout);
        return Boolean.TRUE.equals(success);
    }

    public void saveResponse(String idempotencyKey, String responseJson, Duration ttl) {
        String key = "idempotency:" + idempotencyKey;
        redisTemplate.opsForValue().set(key, responseJson, ttl);
    }

    public String getStoredResponse(String idempotencyKey) {
        return redisTemplate.opsForValue().get("idempotency:" + idempotencyKey);
    }
}
```

---

## 15. RESTful API Design Best Practices Summary

1. **Use Nouns for Resource URIs**: Use plural nouns representing entities (`/api/v1/customers`, `/api/v1/orders`), never verbs (`/api/v1/createCustomer`, `/api/v1/deleteOrder`).
2. **Represent Hierarchies Appropriately**: Express parent-child relationships through nesting: `/api/v1/authors/{authorId}/books`. Avoid going deeper than 2 levels; use query parameters instead.
3. **Use Accurate HTTP Verbs**:
   - `GET`: Read without side effects.
   - `POST`: Create or perform non-idempotent action.
   - `PUT`: Full replacement of resource state.
   - `PATCH`: Selective delta modification.
   - `DELETE`: Resource removal.
4. **Enforce Consistent Error Responses**: Adopt RFC 7807 (`ProblemDetail`) across all microservices so API consumers parse uniform error schemas.
5. **Decouple Payloads with DTOs**: Never expose JPA `@Entity` classes directly in request or response bodies. Use Java records and compile-time mappers (MapStruct).
6. **Provide Pagination and Limits**: Never allow uncontrolled unbounded queries. Set strict defaults (`page=0`, `size=20`, `maxSize=100`).
7. **Design for Backward Compatibility**: Deprecate fields gracefully before removal using HTTP `Sunset` and `Deprecation` response headers.

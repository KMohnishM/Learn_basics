# REST APIs with Spring: Questions and Answers

---

### Question 1: What is the Richardson Maturity Model and what does Level 3 (HATEOAS) look like?

**Answer:**
The Richardson Maturity Model breaks down the characteristics of a RESTful service into four distinct stages:
- **Level 0 (POX/RPC)**: The service uses HTTP simply as a remote tunnel. All operations use a single endpoint and usually a single HTTP verb (POST) with actions defined in XML/JSON bodies.
- **Level 1 (Resources)**: The API introduces individual URIs for distinct resources, but still relies on arbitrary HTTP methods (often POST or GET for everything).
- **Level 2 (HTTP Verbs & Status Codes)**: The service utilizes standard HTTP methods (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) according to RFC specifications and returns accurate HTTP status codes (`200`, `201`, `204`, `400`, `404`, `409`).
- **Level 3 (HATEOAS - Hypermedia as the Engine of Application State)**: Responses contain hypermedia controls (links) that guide the client regarding what actions are available and which URIs transition the application state.

```java
@GetMapping("/orders/{id}")
public EntityModel<OrderResponse> getOrder(@PathVariable Long id) {
    OrderResponse order = orderService.findById(id);
    EntityModel<OrderResponse> model = EntityModel.of(order);

    model.add(linkTo(methodOn(OrderController.class).getOrder(id)).withSelfRel());
    
    if ("PENDING_PAYMENT".equals(order.status())) {
        model.add(linkTo(methodOn(PaymentController.class).processPayment(id, null)).withRel("payment"));
        model.add(linkTo(methodOn(OrderController.class).cancelOrder(id)).withRel("cancel"));
    }
    return model;
}
```

Clients do not need to hardcode transition URLs; instead, they inspect the returned `_links` object dynamically to discover permissible state actions.

---

### Question 2: What is the difference between @Controller and @RestController?

**Answer:**
In Spring MVC, `@Controller` is the traditional stereotype annotation used to define web controllers. Methods in a `@Controller` class typically return a `String` representing a logical view name (such as a Thymeleaf or JSP template) or a `ModelAndView` object resolved by a `ViewResolver` to render HTML.

`@RestController` is a specialized convenience annotation introduced in Spring 4.0 that combines `@Controller` and `@ResponseBody`:

```java
// Traditional @Controller returning serialized JSON requires @ResponseBody
@Controller
public class LegacyItemController {
    @GetMapping("/items/{id}")
    @ResponseBody
    public Item getItem(@PathVariable Long id) {
        return itemService.findById(id);
    }
}

// Modern @RestController implies @ResponseBody on all handler methods
@RestController
@RequestMapping("/items")
public class ModernItemController {
    @GetMapping("/{id}")
    public Item getItem(@PathVariable Long id) {
        return itemService.findById(id);
    }
}
```

When `@RestController` is applied at the class level, Spring Web MVC automatically routes the return values of all handler methods through registered `HttpMessageConverter` beans (such as Jackson's `MappingJackson2HttpMessageConverter`), serializing the response payload directly into the HTTP response body as JSON or XML without attempting view resolution.

---

### Question 3: How do you implement global exception handling with @RestControllerAdvice?

**Answer:**
`@RestControllerAdvice` combines `@ControllerAdvice` and `@ResponseBody`, allowing centralized exception interception across all `@RestController` classes in a Spring application. Instead of catching exceptions inside individual controller methods, unhandled exceptions bubble up to the advice where dedicated `@ExceptionHandler` methods map domain exceptions to appropriate HTTP status codes and structured response bodies.

```java
@RestControllerAdvice
public class GlobalApiExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ProblemDetail> handleNotFound(ResourceNotFoundException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("Resource Not Found");
        problem.setProperty("timestamp", Instant.now());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(problem);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidationErrors(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error -> 
            errors.put(error.getField(), error.getDefaultMessage())
        );
        return ResponseEntity.badRequest().body(errors);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ProblemDetail> handleGenericError(Exception ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "An unexpected internal error occurred."
        );
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(problem);
    }
}
```

This pattern ensures uniform error contracts across an entire API, eliminates boilerplate try-catch blocks in business controllers, and prevents leakage of internal stack traces to clients.

---

### Question 4: What is ProblemDetail (RFC 7807) and how does Spring 6 support it?

**Answer:**
RFC 7807 specifies a standard schema for reporting errors in HTTP APIs to eliminate incompatible, proprietary error formats across services. It defines standard fields: `type` (URI reference to problem documentation), `title` (short human summary), `status` (HTTP status code), `detail` (explanation specific to this occurrence), and `instance` (URI of the requested endpoint).

Spring Framework 6 and Spring Boot 3 introduce native first-class support for RFC 7807 through the `org.springframework.http.ProblemDetail` class.

```java
@RestControllerAdvice
public class ProblemDetailExceptionHandler {

    @ExceptionHandler(InsufficientFundsException.class)
    public ProblemDetail handleInsufficientFunds(InsufficientFundsException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.UNPROCESSABLE_ENTITY, 
                ex.getMessage()
        );
        problem.setType(URI.create("https://api.banking.example/errors/insufficient-funds"));
        problem.setTitle("Insufficient Account Balance");
        problem.setInstance(URI.create(request.getRequestURI()));

        // Add custom extension properties to the problem JSON
        problem.setProperty("accountNumber", ex.getAccountNumber());
        problem.setProperty("currentBalance", ex.getCurrentBalance());
        problem.setProperty("attemptedDebit", ex.getAttemptedAmount());
        problem.setProperty("timestamp", Instant.now());

        return problem;
    }
}
```

When serialized to JSON, Spring formats the response using media type `application/problem+json`, enabling standardized client parsing.

---

### Question 5: How do you create a custom validator with ConstraintValidator?

**Answer:**
Creating a custom Bean Validation constraint in Spring Boot requires two steps: defining a custom annotation annotated with `@Constraint` and implementing the `ConstraintValidator` interface.

First, define the annotation:
```java
@Documented
@Constraint(validatedBy = PhoneNumberValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidPhoneNumber {
    String message() default "Invalid international phone number format";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

Next, implement `ConstraintValidator<Annotation, TargetType>`:
```java
public class PhoneNumberValidator implements ConstraintValidator<ValidPhoneNumber, String> {
    private static final Pattern E164_PATTERN = Pattern.compile("^\\+[1-9]\\d{1,14}$");

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null || value.isBlank()) {
            return true; // Let @NotBlank handle null checks if required
        }
        return E164_PATTERN.matcher(value).matches();
    }
}
```

Finally, annotate the target field in your DTO:
```java
public record UserRegistrationRequest(
    @NotBlank String name,
    @ValidPhoneNumber String mobileNumber
) {}
```
Spring Boot automatically discovers and injects any Spring-managed dependencies directly into the `ConstraintValidator` instance if needed.

---

### Question 6: What is the difference between @Valid and @Validated?

**Answer:**
`@Valid` and `@Validated` both trigger Bean Validation on objects in Spring, but they originate from different specifications and support different capabilities:
- `@Valid` is the standard Jakarta Bean Validation annotation (part of `jakarta.validation`). It does NOT support validation groups directly in its annotation parameters. It is commonly used on method parameters (`@Valid @RequestBody Dto dto`) and on nested object properties to trigger cascading validation.
- `@Validated` is a Spring-specific annotation (part of `org.springframework.validation.annotation`). It extends standard validation to support **Validation Groups**, allowing different constraint subsets to run during different operations. It is also required at the class level on `@Service` or `@RestController` classes to validate method parameters directly (such as `@PathVariable` or `@RequestParam`).

```java
// Group validation with @Validated
@RestController
@RequestMapping("/accounts")
@Validated // Required for validating path variables and query params directly
public class AccountController {

    @PostMapping
    public ResponseEntity<Void> createAccount(
            @Validated(OnCreateGroup.class) @RequestBody AccountDto dto) {
        accountService.create(dto);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }

    @GetMapping("/{id}")
    public ResponseEntity<AccountDto> getAccount(
            @PathVariable @Min(1) Long id) { // Validated by class-level @Validated
        return ResponseEntity.ok(accountService.findById(id));
    }
}
```

Use `@Valid` for standard payload and nested object checks, and `@Validated` when validation groups or method parameter validations are needed.

---

### Question 7: How do you document REST APIs with SpringDoc OpenAPI?

**Answer:**
SpringDoc OpenAPI automates API documentation for Spring Boot 3 by inspecting controller classes, mapping annotations, and model types to produce OpenAPI 3.0 specifications and a Swagger UI web interface.

Add the dependency `springdoc-openapi-starter-webmvc-ui` and enrich controllers using Swagger annotations:

```java
@Tag(name = "Product Catalog", description = "Operations related to product lifecycle and search")
@RestController
@RequestMapping("/api/v1/products")
public class ProductDocumentationController {

    @Operation(
        summary = "Create a new product", 
        description = "Adds a new product to inventory and returns the created record"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "Product created successfully",
            content = @Content(schema = @Schema(implementation = ProductResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request payload",
            content = @Content(schema = @Schema(implementation = ProblemDetail.class)))
    })
    @PostMapping
    public ResponseEntity<ProductResponse> createProduct(
            @Parameter(description = "Product creation payload", required = true)
            @Valid @RequestBody ProductCreateRequest request) {
        ProductResponse response = productService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
```

SpringDoc automatically exposes the generated OpenAPI JSON specification at `/v3/api-docs` and the interactive web interface at `/swagger-ui.html`.

---

### Question 8: What are the different API versioning strategies and trade-offs?

**Answer:**
There are four primary strategies for versioning RESTful APIs:
1. **URI Path Versioning** (e.g., `/api/v1/users`):
   - *Pros*: Clear, self-explanatory, straightforward caching by CDNs, easily routed by API gateways.
   - *Cons*: Violates the REST principle that a URI identifies a unique resource, not its representation.
2. **Custom Header Versioning** (e.g., `X-API-VERSION: 2`):
   - *Pros*: Preserves clean, constant resource URIs; easy to implement using `@GetMapping(headers = "X-API-VERSION=2")`.
   - *Cons*: Cannot be tested directly in browser URL bars; requires specialized proxy configuration to cache separately.
3. **Media Type / Accept Header Versioning** (e.g., `Accept: application/vnd.company.v2+json`):
   - *Pros*: Architecturally purest REST implementation (content negotiation determines representation).
   - *Cons*: Steep learning curve for client consumers; complex documentation and client SDK integration.
4. **Query Parameter Versioning** (e.g., `/api/users?version=2`):
   - *Pros*: Simple to test and default fallback when version is omitted.
   - *Cons*: Pollutes query parameters; routing logic in API gateways can become brittle.

```java
@RestController
@RequestMapping("/api/customers")
public class CustomerVersioningController {
    // Media type versioning
    @GetMapping(value = "/{id}", produces = "application/vnd.company.app-v1+json")
    public CustomerV1Dto getV1(@PathVariable Long id) { return customerService.findV1(id); }

    @GetMapping(value = "/{id}", produces = "application/vnd.company.app-v2+json")
    public CustomerV2Dto getV2(@PathVariable Long id) { return customerService.findV2(id); }
}
```

Most enterprise APIs favor URI path versioning for its simplicity and operational transparency.

---

### Question 9: How do you handle file uploads in Spring Boot?

**Answer:**
Spring Boot handles file uploads using `MultipartFile` and the `StandardServletMultipartResolver`. To receive files, controller methods specify `consumes = MediaType.MULTIPART_FORM_DATA_VALUE` and accept parameters annotated with `@RequestParam("file") MultipartFile`.

Configure upload size limits in `application.properties`:
```properties
spring.servlet.multipart.max-file-size=25MB
spring.servlet.multipart.max-request-size=30MB
```

Implement the upload controller:
```java
@RestController
@RequestMapping("/api/v1/attachments")
public class AttachmentUploadController {

    private final Path rootLocation = Path.of("storage/uploads");

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<UploadResponse> uploadFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam("description") String description) throws IOException {

        if (file.isEmpty()) {
            throw new IllegalArgumentException("Cannot store empty file");
        }

        String sanitizedFilename = UUID.randomUUID() + "_" + StringUtils.cleanPath(file.getOriginalFilename());
        Path destination = this.rootLocation.resolve(sanitizedFilename).normalize();

        try (InputStream inputStream = file.getInputStream()) {
            Files.copy(inputStream, destination, StandardCopyOption.REPLACE_EXISTING);
        }

        UploadResponse response = new UploadResponse(sanitizedFilename, file.getSize(), description);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
```

Always sanitize original file names using `StringUtils.cleanPath()` or generate random UUIDs to avoid directory traversal vulnerabilities.

---

### Question 10: What is the difference between RestClient, WebClient, and RestTemplate?

**Answer:**
Spring provides three HTTP clients reflecting different evolutionary eras of the framework:
1. `RestTemplate` (Introduced Spring 3.0):
   - Synchronous, blocking client wrapping standard HTTP connections.
   - Uses an overloaded, template-method API style (`getForObject`, `exchange`) that can be cumbersome.
   - Placed in maintenance mode as of Spring 5.0 in favor of modern alternatives.
2. `WebClient` (Introduced Spring 5.0):
   - Fully reactive, non-blocking HTTP client based on Project Reactor and Netty.
   - Supports both asynchronous reactive streams (`Flux`, `Mono`) and synchronous blocking (`.block()`).
   - Requires the `spring-boot-starter-webflux` dependency.
3. `RestClient` (Introduced Spring 6.1 / Spring Boot 3.2):
   - Modern synchronous HTTP client offering a fluent, functional API similar to `WebClient`.
   - Built on top of the same infrastructure as `RestTemplate` but without reactive overhead.
   - The officially recommended choice for synchronous REST clients in modern Spring applications.

```java
// Modern synchronous client in Spring 6.1+
@Service
public class CurrencyClient {
    private final RestClient restClient;

    public CurrencyClient(RestClient.Builder builder) {
        this.restClient = builder.baseUrl("https://api.forex.example").build();
    }

    public ForexRate getRate(String pair) {
        return restClient.get()
                .uri("/rates/{pair}", pair)
                .accept(MediaType.APPLICATION_JSON)
                .retrieve()
                .body(ForexRate.class);
    }
}
```

---

### Question 11: How do you implement idempotent POST endpoints?

**Answer:**
While `GET`, `PUT`, and `DELETE` are idempotent by HTTP specification, `POST` is non-idempotent. In network failures or client timeouts during a POST request (such as charging a credit card), clients may retry, potentially creating duplicate records.

Idempotency is implemented using an **Idempotency Key pattern**:
1. The client generates a unique token (UUID) and sends it in the `Idempotency-Key` HTTP header.
2. The server checks an atomic store (e.g., Redis) using `SETNX` (Set if Not Exists).
3. If the key exists with a completed response, the server returns the cached response immediately without executing the operation again.
4. If the key is new, the server processes the request, persists the outcome in Redis with a TTL, and returns the response.

```java
@PostMapping("/charges")
public ResponseEntity<PaymentReceipt> charge(
        @RequestHeader("Idempotency-Key") String idempotencyKey,
        @Valid @RequestBody PaymentRequest request) {

    String cacheKey = "idempotency:" + idempotencyKey;
    PaymentReceipt cachedReceipt = redisTemplate.opsForValue().get(cacheKey);
    if (cachedReceipt != null) {
        return ResponseEntity.ok(cachedReceipt);
    }

    Boolean acquired = redisTemplate.opsForValue().setIfAbsent(cacheKey + ":lock", "LOCK", Duration.ofSeconds(10));
    if (!Boolean.TRUE.equals(acquired)) {
        return ResponseEntity.status(HttpStatus.CONFLICT).build();
    }

    try {
        PaymentReceipt receipt = paymentService.executePayment(request);
        redisTemplate.opsForValue().set(cacheKey, receipt, Duration.ofHours(24));
        return ResponseEntity.status(HttpStatus.CREATED).body(receipt);
    } finally {
        redisTemplate.delete(cacheKey + ":lock");
    }
}
```

---

### Question 12: What is content negotiation in Spring MVC?

**Answer:**
Content negotiation is the mechanism that enables a server to deliver different representations (such as JSON, XML, or CSV) of the same resource based on the client's preferences expressed in the HTTP `Accept` request header.

Spring MVC determines the requested media type using `ContentNegotiationManager`, resolving the media type from:
1. The `Accept` header (default and standard approach).
2. A path extension or query parameter (e.g., `?format=json` or `?format=xml`) if explicitly configured.

```java
@Configuration
public class WebContentNegotiationConfig implements WebMvcConfigurer {
    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .favorParameter(true)
            .parameterName("mediaType")
            .ignoreAcceptHeader(false)
            .defaultContentType(MediaType.APPLICATION_JSON)
            .mediaType("json", MediaType.APPLICATION_JSON)
            .mediaType("xml", MediaType.APPLICATION_XML);
    }
}
```

In the controller:
```java
@GetMapping(value = "/summary", produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
public AccountSummary getSummary() {
    return new AccountSummary("ACC-9021", 5430.50);
}
```
If the client passes `Accept: application/xml`, Spring serializes the object using Jackson XML; otherwise, it defaults to JSON.

---

### Question 13: How do you implement cursor-based pagination vs offset-based?

**Answer:**
Offset-based pagination uses `page` and `size` parameters translated to SQL `OFFSET (page * size) LIMIT size`.
- **Limitation**: When tables grow to millions of rows, `OFFSET 500000 LIMIT 20` degrades significantly because the database engine must scan and discard 500,000 index rows before returning the 20 results. Furthermore, insertions during pagination cause page drift (duplicate or skipped records).

Cursor-based (keyset) pagination uses a stable, sequential indexed attribute (such as an auto-incrementing ID or timestamp) as a pointer to the last retrieved item: `WHERE id > :lastSeenId ORDER BY id ASC LIMIT :size`.

```java
public record CursorResult<T>(List<T> data, Long nextCursor, boolean hasMore) {}

@GetMapping("/feed")
public ResponseEntity<CursorResult<PostResponse>> getFeed(
        @RequestParam(name = "cursor", required = false) Long cursor,
        @RequestParam(name = "limit", defaultValue = "20") int limit) {

    Long startId = (cursor != null) ? cursor : 0L;
    // Query limit + 1 to check if another page exists without running COUNT(*)
    List<PostEntity> entities = postRepository.findNextPosts(startId, PageRequest.of(0, limit + 1));

    boolean hasMore = entities.size() > limit;
    List<PostEntity> pageContent = hasMore ? entities.subList(0, limit) : entities;
    Long nextCursor = pageContent.isEmpty() ? null : pageContent.get(pageContent.size() - 1).getId();

    List<PostResponse> responses = pageContent.stream().map(PostResponse::from).toList();
    return ResponseEntity.ok(new CursorResult<>(responses, nextCursor, hasMore));
}
```

Cursor pagination executes in constant time `O(1)` index seek performance, making it the ideal solution for high-volume infinite-scroll feeds.

---

### Question 14: How does MapStruct differ from ModelMapper for DTO mapping?

**Answer:**
MapStruct and ModelMapper solve object-to-object mapping between JPA entities and DTOs, but use completely different architectural approaches:
1. **ModelMapper**:
   - Uses **runtime reflection** and dynamic type inspection.
   - Automatically attempts to guess field mappings based on matching property names.
   - *Drawbacks*: Incurs significant performance overhead due to reflection, makes debugging difficult when runtime mappings fail silently, and errors are only discovered during execution.
2. **MapStruct**:
   - An **annotation processor** operating entirely at **compile-time**.
   - Generates plain Java source code during compilation (visible in `target/generated-sources`).
   - *Advantages*: Executes as fast as handwritten setter calls with zero reflection overhead; mapping errors (such as mismatched types or missing unmapped fields) trigger compile-time build failures rather than production bugs.

```java
@Mapper(componentModel = "spring")
public interface OrderMapper {
    @Mapping(target = "orderReference", source = "entity.uuid")
    @Mapping(target = "totalCents", expression = "java((long)(entity.getAmount() * 100))")
    OrderDto toDto(OrderEntity entity);

    @Mapping(target = "id", ignore = true)
    OrderEntity toEntity(CreateOrderRequest request);
}
```

Because MapStruct provides compile-time safety and optimal performance, it is the standard choice in enterprise Spring Boot architectures.

---

### Question 15: How do you return different HTTP status codes from a Spring REST endpoint?

**Answer:**
Spring provides three primary mechanisms for controlling HTTP response status codes:
1. `ResponseEntity<T>`: The most flexible programmatic approach, allowing dynamic status codes, headers, and bodies based on runtime conditions:
```java
@PostMapping("/deployments")
public ResponseEntity<DeploymentResponse> createDeployment(@RequestBody DeploymentRequest req) {
    if (req.isDryRun()) {
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(new DeploymentResponse("QUEUED"));
    }
    DeploymentResponse created = deploymentService.deploy(req);
    URI location = URI.create("/api/deployments/" + created.id());
    return ResponseEntity.created(location).body(created);
}
```

2. `@ResponseStatus` Annotation: Applied directly on controller methods or custom exception classes for static status mappings:
```java
@PostMapping("/audit-log")
@ResponseStatus(HttpStatus.NO_CONTENT) // Always returns 204 No Content
public void recordAuditLog(@RequestBody AuditEntry entry) {
    auditService.record(entry);
}

@ResponseStatus(HttpStatus.GONE) // Returns 410 Gone when thrown
public class AccountDeactivatedException extends RuntimeException {}
```

3. `ProblemDetail` or `HttpServletResponse`: Injecting the servlet response directly (`response.setStatus(418)`) or returning `ProblemDetail.forStatus(HttpStatus.NOT_FOUND)` from exception handlers.

`ResponseEntity<T>` is preferred whenever status codes vary conditionally within the same method.

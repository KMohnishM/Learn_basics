# REST APIs with Spring Boot Cheatsheet

### 1. HTTP Methods and Semantics
| Method | CRUD Action | Idempotent | Safe | Typical Success Status |
|---|---|---|---|---|
| `GET` | Read / Query | Yes | Yes | `200 OK` |
| `POST` | Create / Execute | No | No | `201 Created`, `200 OK` |
| `PUT` | Replace Resource | Yes | No | `200 OK`, `204 No Content` |
| `PATCH` | Partial Update | No | No | `200 OK`, `204 No Content` |
| `DELETE` | Remove Resource | Yes | No | `204 No Content`, `200 OK` |
| `HEAD` | Read Headers Only | Yes | Yes | `200 OK` |
| `OPTIONS` | Discover Capabilities | Yes | Yes | `200 OK` |

### 2. Common HTTP Status Codes
| Status Code | Reason Phrase | Typical Usage in REST APIs |
|---|---|---|
| `200` | OK | Successful GET, PUT, or PATCH operation |
| `201` | Created | Successful POST creating a new resource; includes `Location` header |
| `202` | Accepted | Request accepted for asynchronous background processing |
| `204` | No Content | Successful DELETE or action with empty response payload |
| `304` | Not Modified | Conditional GET matching ETag/Last-Modified; cache is valid |
| `400` | Bad Request | Malformed JSON syntax or Bean Validation failure |
| `401` | Unauthorized | Missing, expired, or invalid authentication credentials |
| `403` | Forbidden | Authenticated user lacks permission / scope to access resource |
| `404` | Not Found | Resource URI or identifier does not exist |
| `409` | Conflict | Business rule conflict (e.g., duplicate unique email or version mismatch) |
| `415` | Unsupported Media Type | Request body Content-Type not supported by endpoint |
| `422` | Unprocessable Entity | Syntactically correct JSON failing domain-level validation rules |
| `429` | Too Many Requests | Rate limit or token bucket quota exceeded |
| `500` | Internal Server Error | Unhandled server exception |
| `503` | Service Unavailable | Downstream dependency or database connection offline |

### 3. ResponseEntity Builder Methods
```java
ResponseEntity.ok(body);                                // 200 OK with body
ResponseEntity.created(URI.create("/api/v1/res/" + id)) // 201 Created with Location header
              .body(body);
ResponseEntity.accepted().body(taskReference);          // 202 Accepted for async jobs
ResponseEntity.noContent().build();                     // 204 No Content
ResponseEntity.badRequest().body(problemDetail);        // 400 Bad Request
ResponseEntity.status(HttpStatus.CONFLICT).body(error); // Explicit custom status
```

### 4. Jakarta Bean Validation Annotations
| Annotation | Applicable Types | Validation Rule |
|---|---|---|
| `@NotNull` | Any Object | Value must not be `null` |
| `@NotEmpty` | String, Collection, Map, Array | Not `null`, and size/length > 0 |
| `@NotBlank` | CharSequence / String | Not `null`, and trimmed length > 0 |
| `@Size(min=X, max=Y)` | String, Collection, Map | Size or length must be within bounds |
| `@Min(val)` / `@Max(val)` | Numeric types | Numerical value bounds (inclusive) |
| `@Positive` / `@PositiveOrZero` | Numeric types | Strictly > 0 or >= 0 |
| `@Email` | CharSequence / String | Valid email address syntax |
| `@Pattern(regexp="...")` | CharSequence / String | Matches regular expression |
| `@Past` / `@Future` | Date / Time types | Temporal comparison relative to present |

### 5. OpenAPI 3 / Swagger Annotations Quick Reference
| Annotation | Scope | Purpose |
|---|---|---|
| `@Tag(name, description)` | Class / Method | Groups related operations in UI |
| `@Operation(summary, description)` | Method | Describes endpoint action and behavior |
| `@Parameter(description, example)` | Parameter | Documents path, query, or header parameters |
| `@ApiResponse(responseCode, description)` | Method | Documents possible response status and payload |
| `@Schema(description, example)` | Field / Class | Adds documentation, examples, and constraints to DTOs |
| `@SecurityRequirement(name)` | Class / Method | Declares security scheme required for endpoint |

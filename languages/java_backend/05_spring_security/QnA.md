# Spring Security: Questions and Answers

---

### Question 1: Explain the Spring Security filter chain — what happens when a request comes in?

**Answer:**
When an HTTP request enters the servlet container, it traverses standard servlet filters before reaching Spring's `DispatcherServlet`. Spring Security inserts itself into this pipeline via `DelegatingFilterProxy`, a standard servlet filter registered in the web container. `DelegatingFilterProxy` locates a Spring-managed bean named `springSecurityFilterChain`, which is an instance of `FilterChainProxy`. 

`FilterChainProxy` maintains a list of `SecurityFilterChain` instances, each matched against request criteria (such as URL paths). Once matched, the request flows sequentially through the internal security filters:

```java
@Configuration
@EnableWebSecurity
public class FilterPipelineConfig {
    @Bean
    public SecurityFilterChain customFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(new CustomAuditLoggingFilter(), UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }
}
```

The standard sequence begins with `SecurityContextHolderFilter` (or `SecurityContextPersistenceFilter` in older versions) loading any pre-existing security context from the session or thread local. Next, `HeaderWriterFilter` appends default security headers, and `CorsFilter` and `CsrfFilter` evaluate cross-origin origins and anti-forgery tokens. Authentication filters (such as `UsernamePasswordAuthenticationFilter` or custom token filters) inspect incoming headers or parameters. If authentication succeeds, the filter saves the populated `Authentication` object into `SecurityContextHolder`. Finally, `ExceptionTranslationFilter` catches access-denied or unauthenticated errors, and `AuthorizationFilter` verifies whether the principal has permission to invoke the destination URL before passing control to `DispatcherServlet`.

---

### Question 2: What is the difference between Authentication and Authorization in Spring Security?

**Answer:**
Authentication and Authorization are distinct security phases that answer different questions about an incoming request. Authentication asks "Who are you?", validating the caller's identity using credentials such as username/password, tokens, or digital certificates. Authorization asks "What are you permitted to do?", determining whether the identified principal holds sufficient permissions or roles to execute the requested operation.

In Spring Security, the interface `Authentication` encapsulates the principal, credentials, and granted authorities:

```java
// Authentication object contains principal and granted authorities
Authentication auth = new UsernamePasswordAuthenticationToken(
    userDetails, 
    null, 
    userDetails.getAuthorities()
);
SecurityContextHolder.getContext().setAuthentication(auth);

// Authorization evaluates the authorities assigned during authentication
boolean hasAdminRole = auth.getAuthorities().stream()
    .anyMatch(granted -> granted.getAuthority().equals("ROLE_ADMIN"));
```

Authentication is managed by the `AuthenticationManager` and its `AuthenticationProvider` instances, which inspect credentials and return a fully populated `Authentication` object containing a list of `GrantedAuthority` items. Once authentication completes, Authorization components like `AuthorizationFilter` and method interceptors (`@PreAuthorize`) evaluate whether those authorities satisfy the required access rules defined on endpoints or business service methods.

---

### Question 3: How do you implement JWT authentication in Spring Boot from scratch?

**Answer:**
Implementing stateless JWT authentication requires three components: a `JwtService` to generate and parse tokens, a custom `OncePerRequestFilter` to intercept incoming HTTP headers, and a `SecurityFilterChain` bean to register the filter before Spring's authentication filters.

The filter parses the `Authorization` header, extracts the token, validates its expiration and signature, and populates the `SecurityContext`:

```java
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;

    public JwtAuthenticationFilter(JwtService jwtService, UserDetailsService userDetailsService) {
        this.jwtService = jwtService;
        this.userDetailsService = userDetailsService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            chain.doFilter(request, response);
            return;
        }
        String jwt = authHeader.substring(7);
        String username = jwtService.extractUsername(jwt);
        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            if (jwtService.isTokenValid(jwt, userDetails)) {
                UsernamePasswordAuthenticationToken authToken =
                        new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }
        }
        chain.doFilter(request, response);
    }
}
```

In the security configuration, configure `sessionCreationPolicy(SessionCreationPolicy.STATELESS)` to ensure sessions are never created or queried, and call `addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)`.

---

### Question 4: What is the difference between @PreAuthorize and @Secured?

**Answer:**
Both `@PreAuthorize` and `@Secured` provide method-level security in Spring, but they differ significantly in feature set, syntax, and expression power. `@Secured` is a legacy annotation introduced in early versions of Spring Security. It accepts only literal string role names and does not support Spring Expression Language (SpEL). Furthermore, role names passed to `@Secured` must match the exact string, usually requiring the `ROLE_` prefix explicitly (e.g., `@Secured("ROLE_ADMIN")`).

`@PreAuthorize`, enabled via `@EnableMethodSecurity(prePostEnabled = true)`, supports full SpEL expressions, providing dynamic authorization based on method arguments, return values, and context beans:

```java
@Service
public class OrderService {
    // Legacy @Secured - only accepts string literals, no SpEL
    @Secured({"ROLE_ADMIN", "ROLE_MANAGER"})
    public void cancelAllOrders() {
        // Only accessible by ADMIN or MANAGER
    }

    // Modern @PreAuthorize - supports full SpEL, method arguments, and helper beans
    @PreAuthorize("hasRole('ADMIN') or #customerId == authentication.principal.id")
    public Order getOrderDetails(Long orderId, Long customerId) {
        return orderRepository.findById(orderId).orElseThrow();
    }
}
```

Because `@PreAuthorize` can evaluate conditions against runtime arguments (such as `#customerId`), execute custom bean methods (such as `@permissionEvaluator.canAccess()`), and resolve standard role checks (`hasRole('ADMIN')` handles `ROLE_` prefixes automatically), it is the recommended standard for modern applications.

---

### Question 5: When is it safe to disable CSRF protection?

**Answer:**
Cross-Site Request Forgery (CSRF) exploits the browser's automatic inclusion of ambient credentials—specifically HTTP cookies (such as `JSESSIONID`) and HTTP Basic credentials—when making cross-origin requests. An external malicious site can trick a logged-in user's browser into submitting unauthorized mutating requests (POST, PUT, DELETE) to your backend without their consent.

Disabling CSRF via `http.csrf(AbstractHttpConfigurer::disable)` is safe ONLY under the following strict architectural conditions:
1. The backend application provides a stateless REST API consumed exclusively by programmatic clients or SPAs that do NOT rely on browser session cookies for authentication.
2. Authentication credentials (such as JWT bearer tokens) are stored in client memory or browser storage and explicitly attached via the `Authorization: Bearer <token>` header on each request.
3. Browsers do not automatically attach custom `Authorization` headers to cross-origin requests, eliminating the ambient credential vector that makes CSRF possible.

```java
@Bean
public SecurityFilterChain restApiSecurityFilterChain(HttpSecurity http) throws Exception {
    http
        // Safe ONLY because authentication is purely token-based via headers, not session cookies
        .csrf(AbstractHttpConfigurer::disable)
        .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated());
    return http.build();
}
```

If your application uses session cookies (`JSESSIONID`) or renders server-side HTML forms, CSRF must never be disabled.

---

### Question 6: How does OAuth2 Resource Server JWT validation work?

**Answer:**
When an application is configured as an OAuth 2.0 Resource Server using `spring-boot-starter-oauth2-resource-server`, incoming requests must present a bearer token in the `Authorization` header. Spring Security validates this token cryptographically against the Authorization Server's public JSON Web Key Set (JWKS) without making synchronous network calls for every request.

The validation pipeline performs the following steps:
1. `BearerTokenAuthenticationFilter` extracts the token from `Authorization: Bearer <token>`.
2. The configured `JwtDecoder` (backed by `NimbusJwtDecoder`) verifies the token's cryptographic signature against keys cached from the `jwk-set-uri`.
3. It validates standard claims: verifies `exp` (has not expired), `nbf` (not before), and `iss` (matches expected issuer URI).
4. `JwtAuthenticationConverter` converts the token claims into an `AbstractAuthenticationToken` containing `GrantedAuthority` collections (by default converting `scope` or `scp` claims to `SCOPE_` authorities).

```java
@Configuration
public class ResourceServerSecurityConfig {
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/reports/**").hasAuthority("SCOPE_reports:read")
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()));
        return http.build();
    }
}
```

---

### Question 7: What is the difference between hasRole() and hasAuthority() in Spring Security?

**Answer:**
The difference between `hasRole()` and `hasAuthority()` is purely a naming convention enforced by Spring Security's authorization rules regarding the `ROLE_` prefix. Under the hood, both evaluate objects implementing the `GrantedAuthority` interface, which has a single method: `String getAuthority()`.

When using `hasRole("ADMIN")`, Spring Security automatically prepends `ROLE_` to the provided string, expecting the principal to possess a `GrantedAuthority` named `ROLE_ADMIN`. In contrast, `hasAuthority("ADMIN")` performs an exact string comparison without prepending any prefix, requiring the authority string to be exactly `"ADMIN"`.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth -> auth
        // Requires GrantedAuthority with name "ROLE_ADMIN"
        .requestMatchers("/api/admin/**").hasRole("ADMIN")
        
        // Requires GrantedAuthority with exact name "READ_PRIVILEGE" (no prefix added)
        .requestMatchers("/api/read/**").hasAuthority("READ_PRIVILEGE")
        
        // Equivalent to hasRole("USER"):
        .requestMatchers("/api/user/**").hasAuthority("ROLE_USER")
    );
    return http.build();
}
```

Best practice in modern architectures is to use `hasRole()` for coarse-grained user roles (e.g., `ROLE_ADMIN`, `ROLE_CUSTOMER`) and `hasAuthority()` for fine-grained permissions or OAuth scopes (e.g., `orders:write`, `SCOPE_profile`).

---

### Question 8: How do you implement a custom AuthenticationProvider?

**Answer:**
A custom `AuthenticationProvider` is required when authentication involves specialized logic not supported out of the box, such as proprietary legacy hashing, external mainframe verification, multi-factor authentication steps, or custom database structures.

You implement the `AuthenticationProvider` interface by defining two methods: `authenticate()` and `supports()`:

```java
@Component
public class ExternalApiAuthenticationProvider implements AuthenticationProvider {
    private final ExternalAuthClient authClient;

    public ExternalApiAuthenticationProvider(ExternalAuthClient authClient) {
        this.authClient = authClient;
    }

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        String username = authentication.getName();
        String password = authentication.getCredentials().toString();

        boolean isValid = authClient.verifyCredentials(username, password);
        if (!isValid) {
            throw new BadCredentialsException("Invalid credentials provided for external service");
        }

        List<GrantedAuthority> authorities = List.of(new SimpleGrantedAuthority("ROLE_USER"));
        return new UsernamePasswordAuthenticationToken(username, null, authorities);
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return UsernamePasswordAuthenticationToken.class.isAssignableFrom(authentication);
    }
}
```

The `supports()` method informs the `ProviderManager` whether this provider can handle the submitted `Authentication` type. In `authenticate()`, verify the credentials, throw an `AuthenticationException` on failure, or return an authenticated `Authentication` token containing principal details and authorities on success.

---

### Question 9: What is the SecurityContextHolder and how does it store authentication?

**Answer:**
`SecurityContextHolder` is the central repository where Spring Security stores details of the currently authenticated principal. It provides static access to the `SecurityContext`, which in turn holds the `Authentication` object.

The storage mechanism is determined by a pluggable strategy configured via system property or static method:
1. `MODE_THREADLOCAL` (Default): Stores the context in a `ThreadLocal` variable. Every request handled by an independent thread has its own isolated context.
2. `MODE_INHERITABLETHREADLOCAL`: Uses `InheritableThreadLocal`, causing worker threads spawned by the request thread to inherit the security context.
3. `MODE_GLOBAL`: Uses a single static context across all threads in the JVM (used in standalone desktop or CLI applications).

```java
// Accessing the current authenticated user safely
public String getCurrentLoggedInUsername() {
    SecurityContext context = SecurityContextHolder.getContext();
    Authentication authentication = context.getAuthentication();
    if (authentication == null || !authentication.isAuthenticated()) {
        throw new AccessDeniedException("No authenticated principal in security context");
    }
    return authentication.getName();
}
```

At the end of each HTTP request, Spring Security filters (`SecurityContextHolderFilter`) clear the thread-local context using `SecurityContextHolder.clearContext()` to prevent thread contamination in thread pools reused by the servlet container.

---

### Question 10: How do you configure CORS in Spring Security?

**Answer:**
When configuring CORS in a Spring application that uses Spring Security, CORS must be integrated directly into the `SecurityFilterChain`. Because CORS pre-flight `OPTIONS` requests do not contain authorization headers, they must be processed and answered before the security authorization filter evaluates permissions; otherwise, browsers block the requests.

Define a `CorsConfigurationSource` bean and attach it to `HttpSecurity.cors()`:

```java
@Configuration
public class SecurityCorsConfiguration {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .authorizeHttpRequests(auth -> auth.anyRequest().authenticated());
        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of("http://localhost:3000", "https://app.production.com"));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"));
        config.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-Requested-With"));
        config.setExposedHeaders(List.of("Authorization"));
        config.setAllowCredentials(true);
        config.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
```

This configuration ensures `CorsFilter` runs at the front of the filter chain, handles pre-flight checks cleanly, and appends `Access-Control-Allow-Origin` headers without failing unauthenticated `OPTIONS` requests.

---

### Question 11: What is session fixation and how does Spring Security prevent it?

**Answer:**
Session fixation is an attack vector where an attacker acquires a valid session identifier from a target website (e.g., by visiting the login page), tricks an unsuspecting victim into using that session ID (via query parameter injection or cookie manipulation), and waits for the victim to authenticate. Once the victim logs in, if the application retains the same session ID, the attacker can use their copy of the session ID to impersonate the victim.

Spring Security mitigates session fixation by automatically altering or recreating the HTTP session upon successful authentication. You configure this behavior in `HttpSecurity`:

```java
@Bean
public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http
        .sessionManagement(session -> session
            // Default and recommended for Servlet 3.1+ containers:
            // Generates a new session ID while preserving all existing attributes
            .sessionFixation(fixation -> fixation.changeSessionId())
        );
    return http.build();
}
```

The available strategies are:
1. `changeSessionId()`: Utilizes the Servlet 3.1 `HttpServletRequest.changeSessionId()` method to replace the identifier while preserving session attributes without overhead.
2. `migrateSession()`: Creates a completely new `HttpSession` and copies all existing session attributes over.
3. `newSession()`: Creates a new session but discards all existing attributes.
4. `none()`: Keeps the existing session unchanged (not recommended).

---

### Question 12: How do you test Spring Security endpoints with @WithMockUser?

**Answer:**
Testing secured Spring Boot endpoints with `MockMvc` is facilitated by the `spring-security-test` library. The `@WithMockUser` annotation populates the test's `SecurityContext` with an authenticated `UsernamePasswordAuthenticationToken` without requiring real users in a database or token generation routines.

You can configure the mock username, roles, and authorities directly on the test method:

```java
@SpringBootTest
@AutoConfigureMockMvc
public class AccountControllerSecurityTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @WithMockUser(username = "admin_user", roles = {"ADMIN"})
    void adminCanAccessRestrictedEndpoint() throws Exception {
        mockMvc.perform(get("/api/admin/system/metrics"))
                .andExpect(status().isOk());
    }

    @Test
    @WithMockUser(username = "regular_user", roles = {"USER"})
    void regularUserIsForbiddenFromAdminEndpoint() throws Exception {
        mockMvc.perform(get("/api/admin/system/metrics"))
                .andExpect(status().isForbidden());
    }

    @Test
    void unauthenticatedRequestReturnsUnauthorized() throws Exception {
        mockMvc.perform(get("/api/admin/system/metrics"))
                .andExpect(status().isUnauthorized());
    }
}
```

Notice that `@WithMockUser(roles = "ADMIN")` automatically populates authority `ROLE_ADMIN`. If your logic checks fine-grained permissions instead of roles, use `authorities = {"user:read", "user:write"}`.

---

### Question 13: What is DelegatingPasswordEncoder and why is it preferred?

**Answer:**
`DelegatingPasswordEncoder` is an implementation of `PasswordEncoder` that delegates to concrete encoders based on a prefix identifier embedded in the encoded password string. Rather than locking an application into a single cryptographic algorithm, it formats stored passwords as `{id}encodedPassword` (e.g., `{bcrypt}$2a$10$...`, `{argon2}$argon2id$...`, `{pbkdf2}...`).

It is preferred in modern architectures for several critical reasons:
1. **Algorithm Agility**: Security requirements change over time. When older algorithms (like MD5 or SHA-1) become deprecated, new algorithms (like Argon2 or BCrypt) can be adopted without invalidating existing user passwords.
2. **Seamless In-Place Migration**: When a user logs in, the system compares their password using the encoder corresponding to the stored prefix. If the stored prefix matches a legacy format, the application can re-encode the plaintext password using the current default algorithm and persist the new hash during authentication.
3. **Defense Against Plaintext Storage**: If an un-prefixed password is encountered, `DelegatingPasswordEncoder` can throw an exception or route to a non-matching encoder, preventing accidental plaintext comparisons.

```java
@Configuration
public class SecurityEncodingConfig {
    @Bean
    public PasswordEncoder passwordEncoder() {
        // Creates DelegatingPasswordEncoder with bcrypt as default
        return PasswordEncoderFactories.createDelegatingPasswordEncoder();
    }
}
```

---

### Question 14: How do you implement refresh token rotation with JWT?

**Answer:**
Refresh token rotation issues a new refresh token every time an access token is refreshed, invalidating the old refresh token immediately. If an attacker intercepts a refresh token and uses it after the legitimate user has already rotated it, the backend detects token reuse and revokes all refresh tokens belonging to that user family.

Implementation requires storing the active refresh token hash and a token family identifier in a database or Redis:

```java
@Service
public class TokenRotationService {
    private final RefreshTokenRepository tokenRepository;
    private final JwtService jwtService;

    public TokenRotationService(RefreshTokenRepository tokenRepository, JwtService jwtService) {
        this.tokenRepository = tokenRepository;
        this.jwtService = jwtService;
    }

    @Transactional
    public TokenResponse rotateToken(String rawRefreshToken) {
        String tokenHash = hashToken(rawRefreshToken);
        RefreshToken tokenRecord = tokenRepository.findByTokenHash(tokenHash)
                .orElseThrow(() -> new InvalidTokenException("Invalid refresh token"));

        if (tokenRecord.isRevoked()) {
            // Compromise detected! Revoke all tokens in this user family
            tokenRepository.revokeAllByFamilyId(tokenRecord.getFamilyId());
            throw new SecurityAlertException("Refresh token reuse detected. Revoking all sessions.");
        }

        // Invalidate the current refresh token
        tokenRecord.setRevoked(true);
        tokenRepository.save(tokenRecord);

        // Generate new token pair
        String newAccessToken = jwtService.generateAccessToken(tokenRecord.getUser());
        String newRefreshToken = jwtService.generateRefreshToken(tokenRecord.getUser());

        RefreshToken nextRecord = new RefreshToken(
            hashToken(newRefreshToken), 
            tokenRecord.getUser(), 
            tokenRecord.getFamilyId()
        );
        tokenRepository.save(nextRecord);

        return new TokenResponse(newAccessToken, newRefreshToken);
    }

    private String hashToken(String token) {
        return DigestUtils.sha256Hex(token);
    }
}
```

---

### Question 15: What is method security and how does @PostAuthorize differ from @PreAuthorize?

**Answer:**
Method security protects business logic and service layer methods by intercepting calls using Spring AOP and enforcing authorization rules before or after method invocation. This ensures that security rules cannot be bypassed even if endpoints are invoked via different controllers, message queues, or batch jobs.

The primary difference between `@PreAuthorize` and `@PostAuthorize` lies in the timing of the authorization check and access to return data:
- `@PreAuthorize` executes *before* the target method runs. It inspects authentication and method arguments. If the expression evaluates to false, method execution is aborted immediately and `AccessDeniedException` is thrown, preventing any state mutations.
- `@PostAuthorize` executes *after* the method finishes executing. It allows the method to execute and compute its return value, which is then made available in the SpEL expression via the special variable `returnObject`.

```java
@Service
public class PayrollService {

    // PreAuthorize: Verified before method runs; inspects argument 'employeeId'
    @PreAuthorize("hasRole('HR_ADMIN') or #employeeId == authentication.principal.id")
    public void updateBankDetails(Long employeeId, BankDetails details) {
        payrollRepository.updateAccount(employeeId, details);
    }

    // PostAuthorize: Runs method first, then verifies if caller is allowed to see the returned data
    @PostAuthorize("returnObject.ownerUsername == authentication.name or hasRole('AUDITOR')")
    public SensitiveReport generateReport(Long reportId) {
        return reportRepository.fetchSensitiveReport(reportId);
    }
}
```

Use `@PreAuthorize` for actions that mutate state or to prevent unauthorized operations, and use `@PostAuthorize` when permissions depend on domain attributes loaded during method execution.

# Spring Security 6 Quick Reference Cheatsheet

### 1. Spring Security Filter Execution Order
| Order | Filter Class | Primary Purpose |
|---|---|---|
| 1 | `ChannelProcessingFilter` | Redirects to HTTPS/SSL protocol |
| 2 | `SecurityContextHolderFilter` | Populates `SecurityContext` from repository |
| 3 | `ConcurrentSessionFilter` | Enforces concurrent user session policies |
| 4 | `HeaderWriterFilter` | Adds standard security headers (HSTS, CSP, X-Frame) |
| 5 | `CorsFilter` | Validates CORS origins and handles pre-flight OPTIONS |
| 6 | `CsrfFilter` | Verifies CSRF anti-tampering tokens on mutating calls |
| 7 | `LogoutFilter` | Clears credentials, invalidates sessions, removes cookies |
| 8 | `UsernamePasswordAuthenticationFilter` | Authenticates username/password credentials |
| 9 | `BearerTokenAuthenticationFilter` | Validates OAuth2 / JWT bearer tokens |
| 10 | `AnonymousAuthenticationFilter` | Assigns `AnonymousAuthenticationToken` if unauthenticated |
| 11 | `SessionManagementFilter` | Handles session fixation protection and concurrency |
| 12 | `ExceptionTranslationFilter` | Converts security exceptions to 401/403 or redirects |
| 13 | `AuthorizationFilter` | Verifies endpoint request authorization rules |

### 2. Common SpEL Security Expressions
| SpEL Expression | Description |
|---|---|
| `hasRole('ADMIN')` | Principal has granted authority `ROLE_ADMIN` |
| `hasAnyRole('USER', 'ADMIN')` | Principal has at least one matching `ROLE_*` authority |
| `hasAuthority('orders:write')` | Principal has exact permission string without prefix |
| `isAuthenticated()` | Principal is logged in and not anonymous |
| `isAnonymous()` | Principal is unauthenticated visitor |
| `#id == authentication.principal.id` | Checks if method argument equals logged-in user id |
| `@serviceBean.canAccess(#entityId)` | Invokes custom Spring bean method returning boolean |
| `returnObject.owner == authentication.name` | In `@PostAuthorize`, verifies returned object property |

### 3. OAuth 2.0 Grant Types
| Grant Type | Use Case | Token Exchange |
|---|---|---|
| Authorization Code with PKCE | Single Page Apps (SPA) and Native Mobile Apps | Auth Code -> Access + Refresh Token |
| Client Credentials | Machine-to-Machine (M2M) server communications | Client ID + Secret -> Access Token |
| Refresh Token | Exchanging expired access token without re-login | Refresh Token -> New Access Token |
| Device Authorization | Input-constrained devices (Smart TVs, CLI consoles) | Device Code + Verification URI |

### 4. JWT Structure and Claims
```
[Header: {"alg":"HS256","typ":"JWT"}] . [Payload: {"sub":"user123","roles":["ADMIN"],"exp":1719000000}] . [Signature]
```
- `sub` (Subject): Principal identity / user id
- `iss` (Issuer): URL of authorization server
- `exp` (Expiration): Unix timestamp after which token is invalid
- `iat` (Issued At): Unix timestamp of generation

### 5. Common Security Annotations
| Annotation | Placement | Description |
|---|---|---|
| `@EnableWebSecurity` | Class | Activates Spring Security servlet web support |
| `@EnableMethodSecurity` | Class | Activates `@PreAuthorize`, `@PostAuthorize`, `@Secured` |
| `@PreAuthorize("SpEL")` | Method | Evaluates access control before method execution |
| `@PostAuthorize("SpEL")` | Method | Evaluates access control after return value calculated |
| `@AuthenticationPrincipal` | Parameter | Resolves current authenticated principal object |
| `@WithMockUser` | Test Method | Injects mock authenticated user into test context |

### 6. Standard HttpSecurity Configuration Template
```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityCheatsheetConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http, JwtFilter jwtFilter) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)
            .cors(Customizer.withDefaults())
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**", "/swagger-ui/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }
}
```

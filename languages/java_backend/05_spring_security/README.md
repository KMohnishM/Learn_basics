# Module 05: Spring Security 6 Deep Dive

Spring Security is a powerful, customizable authentication and access-control framework for Java applications. It is the de facto standard for securing Spring-based applications, providing comprehensive support for authentication, authorization, protection against common exploits, and integrations with standard protocols such as OAuth 2.0, OpenID Connect, and SAML.

---

## 1. Spring Security Architecture

Understanding Spring Security requires understanding its servlet filter-based architecture. When a request hits a Spring Boot application, it passes through the standard Java EE `Filter` chain before reaching the `DispatcherServlet`.

### DelegatingFilterProxy and FilterChainProxy

Servlet containers (like Apache Tomcat, Jetty, or Undertow) have their own filter pipeline defined by the Servlet specification. These filters are managed by the servlet container, not by the Spring application context.

To bridge standard servlet filters and Spring-managed beans:
- `DelegatingFilterProxy`: A standard servlet filter registered in the servlet container. It does not perform security logic directly. Instead, it delegates all work to a Spring bean named `springSecurityFilterChain`.
- `FilterChainProxy`: The Spring bean wrapped by `DelegatingFilterProxy`. It contains one or more `SecurityFilterChain` instances, matches incoming request URIs, and invokes the appropriate chain of security filters.

```
Incoming HTTP Request
        │
        ▼
[ Servlet Container Filter Chain ]
        │
        ▼
[ DelegatingFilterProxy ]
        │ (delegates to Spring Bean)
        ▼
[ FilterChainProxy (springSecurityFilterChain) ]
        │
   ┌────┴───────────────────────────┐
   │ Matches request against paths  │
   ▼                                ▼
[ SecurityFilterChain 1 ]       [ SecurityFilterChain 2 ]
(/api/**)                       (/public/**)
   │
   ├─► SecurityContextHolderFilter
   ├─► HeaderWriterFilter
   ├─► CorsFilter
   ├─► CsrfFilter
   ├─► LogoutFilter
   ├─► JwtAuthenticationFilter
   ├─► UsernamePasswordAuthenticationFilter
   ├─► RequestCacheAwareFilter
   ├─► SecurityContextHolderAwareRequestFilter
   ├─► AnonymousAuthenticationFilter
   ├─► SessionManagementFilter
   ├─► ExceptionTranslationFilter
   └─► AuthorizationFilter
        │
        ▼
[ DispatcherServlet ]
        │
        ▼
[ @RestController ]
```

### Filter Ordering

Spring Security filters execute in a strict, predefined order. Standard positions include:
1. `ChannelProcessingFilter`: Enforces transport layer security (e.g., redirecting HTTP to HTTPS).
2. `SecurityContextHolderFilter`: Loads the `SecurityContext` from repository storage (e.g., HTTP session) into the thread-local context.
3. `ConcurrentSessionFilter`: Verifies session validity and tracks concurrent logins.
4. `WebAsyncManagerIntegrationFilter`: Integrates `SecurityContext` with Spring Web async processing.
5. `HeaderWriterFilter`: Appends security headers (X-Frame-Options, X-Content-Type-Options, CSP, HSTS).
6. `CorsFilter`: Handles cross-origin pre-flight OPTIONS requests and applies CORS response headers.
7. `CsrfFilter`: Validates CSRF tokens on mutating HTTP methods (POST, PUT, DELETE, PATCH).
8. `LogoutFilter`: Intercepts logout requests, clears security context, invalidates sessions, and removes cookies.
9. `AuthenticationFilter` (e.g., `UsernamePasswordAuthenticationFilter`, `BearerTokenAuthenticationFilter`, or custom `JwtAuthenticationFilter`): Authenticates incoming credentials and populates `SecurityContext`.
10. `RequestCacheAwareFilter`: Restores cached requests after successful authentication.
11. `SecurityContextHolderAwareRequestFilter`: Wraps the `HttpServletRequest` to implement standard servlet security methods (`getRemoteUser()`, `isUserInRole()`).
12. `AnonymousAuthenticationFilter`: Assigns an `AnonymousAuthenticationToken` if no authentication object exists in the `SecurityContext`.
13. `SessionManagementFilter`: Handles session fixation protection and concurrent session limits.
14. `ExceptionTranslationFilter`: Catches `AuthenticationException` and `AccessDeniedException` to initiate authentication entry points or invoke access denied handlers.
15. `AuthorizationFilter`: Final filter determining whether the current principal is permitted to access the requested URI.

### WebSecurityConfigurerAdapter (Deprecated) vs SecurityFilterChain Bean Approach

Prior to Spring Security 5.7 and Spring Boot 3.0, security configuration required extending `WebSecurityConfigurerAdapter` and overriding `configure(HttpSecurity http)`. This pattern is obsolete and was removed in Spring Security 6.

#### Legacy Approach (Removed)
```java
// DEPRECATED AND REMOVED IN SPRING SECURITY 6 - DO NOT USE
@Configuration
public class LegacySecurityConfig extends WebSecurityConfigurerAdapter {
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
            .antMatchers("/public/**").permitAll()
            .anyRequest().authenticated()
            .and()
            .httpBasic();
    }
}
```

#### Modern Approach (Spring Security 6 / Spring Boot 3+)
The modern approach defines a component-based configuration using beans of type `SecurityFilterChain` with lambda DSL.

```java
package com.example.security.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class ModernSecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(authorize -> authorize
                .requestMatchers("/api/public/**", "/health", "/swagger-ui/**", "/v3/api-docs/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/user/**").hasAnyRole("USER", "ADMIN")
                .anyRequest().authenticated()
            )
            .httpBasic(Customizer.withDefaults());

        return http.build();
    }
}
```

---

## 2. Authentication vs Authorization

Security consists of two distinct stages:
- **Authentication**: Verifying identity ("Who are you?").
- **Authorization**: Determining permissions ("Are you allowed to perform this operation?").

### Key Architectural Interfaces

1. `Authentication`: Represents the token for an authentication request or for an authenticated principal.
   - `getPrincipal()`: The identity being authenticated (often an instance of `UserDetails` or a username string).
   - `getCredentials()`: The secret proving identity (e.g., password, token). Cleared after authentication.
   - `getAuthorities()`: Collection of `GrantedAuthority` granted to the principal.
   - `isAuthenticated()`: Boolean flag indicating authentication status.
   - `getDetails()`: Additional details (IP address, certificate serial, session ID).

2. `SecurityContext`: Holds the current `Authentication` object:
   ```java
   public interface SecurityContext extends Serializable {
       Authentication getAuthentication();
       void setAuthentication(Authentication authentication);
   }
   ```

3. `SecurityContextHolder`: Provides access to the `SecurityContext`. Uses a strategy pattern:
   - `MODE_THREADLOCAL`: Default. Bound to the executing thread.
   - `MODE_INHERITABLETHREADLOCAL`: Inherited by child threads spawned by the current thread.
   - `MODE_GLOBAL`: Shared across all threads in the JVM (used in standalone desktop clients).

   Accessing the context programmatically:
   ```java
   SecurityContext context = SecurityContextHolder.getContext();
   Authentication authentication = context.getAuthentication();
   if (authentication != null && authentication.isAuthenticated()) {
       String username = authentication.getName();
       Collection<? extends GrantedAuthority> authorities = authentication.getAuthorities();
   }
   ```

4. `AuthenticationManager`: Core contract for authentication processing.
   ```java
   public interface AuthenticationManager {
       Authentication authenticate(Authentication authentication) throws AuthenticationException;
   }
   ```
   `ProviderManager` is the default implementation, delegating to a chain of configured `AuthenticationProvider` instances.

5. `AuthenticationProvider`: Executes a specific authentication type (e.g., username/password via database, LDAP, OAuth2 token).
   ```java
   public interface AuthenticationProvider {
       Authentication authenticate(Authentication authentication) throws AuthenticationException;
       boolean supports(Class<?> authentication);
   }
   ```

6. `UserDetails` and `UserDetailsService`:
   - `UserDetails`: Core user information interface representing credentials, status flags (account non-expired, account non-locked, credentials non-expired, enabled), and authorities.
   - `UserDetailsService`: Service interface with a single method to retrieve user details by username:
     ```java
     public interface UserDetailsService {
         UserDetails loadUserByUsername(String username) throws UsernameNotFoundException;
     }
     ```

### Complete Custom UserDetails and UserDetailsService Implementation

```java
package com.example.security.user;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import java.util.Collection;
import java.util.List;
import java.util.stream.Collectors;

public class SecurityUser implements UserDetails {

    private final Long id;
    private final String username;
    private final String password;
    private final boolean active;
    private final List<GrantedAuthority> authorities;

    public SecurityUser(Long id, String username, String password, boolean active, List<String> roles) {
        this.id = id;
        this.username = username;
        this.password = password;
        this.active = active;
        this.authorities = roles.stream()
                .map(SimpleGrantedAuthority::new)
                .collect(Collectors.toList());
    }

    public Long getId() {
        return id;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    @Override
    public String getPassword() {
        return password;
    }

    @Override
    public String getUsername() {
        return username;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return active;
    }
}
```

```java
package com.example.security.user;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    public CustomUserDetailsService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        UserEntity entity = userRepository.findByUsername(username)
                .orElseThrow(() -> new UsernameNotFoundException("User not found: " + username));

        List<String> authorities = entity.getRoles().stream()
                .map(role -> "ROLE_" + role.getName())
                .collect(Collectors.toList());

        return new SecurityUser(
                entity.getId(),
                entity.getUsername(),
                entity.getPasswordHash(),
                entity.isEnabled(),
                authorities
        );
    }
}
```

---

## 3. Password Encoding

Passwords must never be stored as plain text or hashed using fast, unsalted message digest algorithms like MD5 or SHA-256. Passwords must be encoded using adaptive, computationally expensive cryptographic one-way hashing functions that include unique random salts and a configurable work factor (cost).

### The PasswordEncoder Interface

```java
public interface PasswordEncoder {
    String encode(CharSequence rawPassword);
    boolean matches(CharSequence rawPassword, String encodedPassword);
    default boolean upgradeEncoding(String encodedPassword) {
        return false;
    }
}
```

### BCryptPasswordEncoder
BCrypt uses the OpenBSD Blowfish password hashing algorithm with a random 16-byte salt and an iteration exponent (log rounds) ranging between 4 and 31 (default is 10, representing 2^10 = 1024 rounds).

```java
@Configuration
public class PasswordConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        // Cost factor 12: 2^12 = 4096 rounds
        return new BCryptPasswordEncoder(12);
    }
}
```

### DelegatingPasswordEncoder
Spring Security uses `DelegatingPasswordEncoder` as the default encoder factory. It prepends the encoding identifier within curly braces to the hashed value (e.g., `{bcrypt}$2a$12$...`, `{argon2}$argon2id$...`, `{pbkdf2}...`).

Benefits:
- Supports multiple hashing algorithms in a single system.
- Enables seamless password migration when upgrading encryption algorithms without forcing immediate user password resets.
- Automatically handles legacy hashes while applying modern algorithms to newly saved passwords.

```java
@Bean
public PasswordEncoder delegatingPasswordEncoder() {
    return PasswordEncoderFactories.createDelegatingPasswordEncoder();
}
```

When verifying credentials via `matches()`, `DelegatingPasswordEncoder` extracts the prefix id, routes to the corresponding encoder, and compares the candidate password.

---

## 4. HTTP Basic and Form Login

### HTTP Basic Authentication
HTTP Basic transmits credentials using the `Authorization` header containing the string `Basic <base64-encoded(username:password)>`. Because Base64 is easily decodable, HTTP Basic must exclusively run over HTTPS.

```java
@Bean
public SecurityFilterChain basicAuthFilterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/api/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated()
        )
        .httpBasic(basic -> basic
            .realmName("InternalAdminApi")
        );
    return http.build();
}
```

### Form-Based Login
Form login presents a standard HTML form collecting credentials, posts them to a dedicated processing URL, establishes an HTTP session, and issues a session cookie (`JSESSIONID`).

```java
package com.example.security.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class FormLoginSecurityConfig {

    @Bean
    public SecurityFilterChain formSecurityFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/login", "/css/**", "/js/**", "/images/**").permitAll()
                .requestMatchers("/dashboard/**").authenticated()
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginPage("/login")                          // Custom login page URL
                .loginProcessingUrl("/perform_login")         // Action URL for the login form POST
                .defaultSuccessUrl("/dashboard", true)        // Target URL after successful login
                .failureUrl("/login?error=true")              // Redirect URL on failure
                .usernameParameter("txtUsername")             // Custom username input field name
                .passwordParameter("txtPassword")             // Custom password input field name
                .permitAll()
            )
            .logout(logout -> logout
                .logoutUrl("/perform_logout")
                .logoutSuccessUrl("/login?logout=true")
                .deleteCookies("JSESSIONID")
                .invalidateHttpSession(true)
                .clearAuthentication(true)
                .permitAll()
            );

        return http.build();
    }
}
```

---

## 5. JWT Authentication

JSON Web Tokens (JWT) enable stateless authentication in distributed systems and microservices. Instead of storing sessions server-side in memory or a database, client state and identity are encoded in a signed token sent with every HTTP request.

### JWT Structure
A JWT consists of three parts delimited by periods (`.`):
1. **Header**: Metadata containing token type (`JWT`) and signing algorithm (e.g., `HS256`, `RS256`).
2. **Payload (Claims)**: Registered claims (`sub`, `iss`, `exp`, `iat`), and custom claims (`roles`, `email`, `userId`).
3. **Signature**: Cryptographic signature calculated over Base64URL-encoded header and payload using a secret key or private key.

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwicm9sZXMiOlsiUk9MRV9VU0VSIl0sImV4cCI6MTcxOTAwMDAwMH0.SignatureHash
```

### JWT Service Implementation Using jjwt 0.12+

```java
package com.example.security.jwt;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class JwtService {

    private final SecretKey signingKey;
    private final long accessTokenExpirationMinutes;
    private final long refreshTokenExpirationDays;

    public JwtService(
            @Value("${application.security.jwt.secret-key}") String secretKey,
            @Value("${application.security.jwt.access-token-expiration-minutes:15}") long accessExpiration,
            @Value("${application.security.jwt.refresh-token-expiration-days:7}") long refreshExpiration) {
        byte[] keyBytes = secretKey.getBytes(StandardCharsets.UTF_8);
        this.signingKey = Keys.hmacShaKeyFor(keyBytes);
        this.accessTokenExpirationMinutes = accessExpiration;
        this.refreshTokenExpirationDays = refreshExpiration;
    }

    public String generateAccessToken(UserDetails userDetails, Long userId) {
        Map<String, Object> extraClaims = new HashMap<>();
        List<String> roles = userDetails.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList());
        extraClaims.put("roles", roles);
        extraClaims.put("uid", userId);

        Instant now = Instant.now();
        Instant validity = now.plus(accessTokenExpirationMinutes, ChronoUnit.MINUTES);

        return Jwts.builder()
                .claims(extraClaims)
                .subject(userDetails.getUsername())
                .issuedAt(Date.from(now))
                .expiration(Date.from(validity))
                .signWith(signingKey)
                .compact();
    }

    public String generateRefreshToken(UserDetails userDetails) {
        Instant now = Instant.now();
        Instant validity = now.plus(refreshTokenExpirationDays, ChronoUnit.DAYS);

        return Jwts.builder()
                .subject(userDetails.getUsername())
                .issuedAt(Date.from(now))
                .expiration(Date.from(validity))
                .signWith(signingKey)
                .compact();
    }

    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    public boolean isTokenValid(String token, UserDetails userDetails) {
        try {
            final String username = extractUsername(token);
            return (username.equals(userDetails.getUsername()) && !isTokenExpired(token));
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    private boolean isTokenExpired(String token) {
        Date expiration = extractClaim(token, Claims::getExpiration);
        return expiration.before(new Date());
    }

    private Claims extractAllClaims(String token) {
        return Jwts.parser()
                .verifyWith(signingKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
```

### JwtAuthenticationFilter (OncePerRequestFilter)

```java
package com.example.security.jwt;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;

    public JwtAuthenticationFilter(JwtService jwtService, UserDetailsService userDetailsService) {
        this.jwtService = jwtService;
        this.userDetailsService = userDetailsService;
    }

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain
    ) throws ServletException, IOException {

        final String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        final String jwt = authHeader.substring(7);
        final String userEmail;

        try {
            userEmail = jwtService.extractUsername(jwt);
        } catch (Exception ex) {
            filterChain.doFilter(request, response);
            return;
        }

        if (userEmail != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            UserDetails userDetails = this.userDetailsService.loadUserByUsername(userEmail);

            if (jwtService.isTokenValid(jwt, userDetails)) {
                UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                        userDetails,
                        null,
                        userDetails.getAuthorities()
                );
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }
        }

        filterChain.doFilter(request, response);
    }
}
```

---

## 6. OAuth2 Resource Server

When an application acts as an OAuth 2.0 Resource Server, it verifies bearer tokens issued by an external Authorization Server (e.g., Keycloak, Okta, Auth0, or Google Identity) before granting access to protected endpoints.

### Maven Dependency
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-oauth2-resource-server</artifactId>
</dependency>
```

### Application Properties
```properties
spring.security.oauth2.resourceserver.jwt.issuer-uri=https://auth.company.com/realms/production
spring.security.oauth2.resourceserver.jwt.jwk-set-uri=https://auth.company.com/realms/production/protocol/openid-connect/certs
```

### Resource Server Configuration with Custom Authorities Converter
By default, Spring Security maps claims with prefix `SCOPE_`. If your identity provider returns roles inside custom claims (e.g., `realm_access.roles`), a converter maps those to `ROLE_` authorities.

```java
package com.example.security.oauth2;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.convert.converter.Converter;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter;
import org.springframework.security.web.SecurityFilterChain;

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Configuration
public class ResourceServerConfig {

    @Bean
    public SecurityFilterChain resourceServerFilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/orders/**").hasAuthority("SCOPE_orders:read")
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthenticationConverter()))
            );

        return http.build();
    }

    @Bean
    public JwtAuthenticationConverter jwtAuthenticationConverter() {
        JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
        converter.setJwtGrantedAuthoritiesConverter(new KeycloakRoleConverter());
        return converter;
    }

    private static class KeycloakRoleConverter implements Converter<Jwt, Collection<GrantedAuthority>> {
        @Override
        @SuppressWarnings("unchecked")
        public Collection<GrantedAuthority> convert(Jwt jwt) {
            Map<String, Object> realmAccess = (Map<String, Object>) jwt.getClaims().get("realm_access");
            if (realmAccess == null || realmAccess.isEmpty()) {
                return Collections.emptyList();
            }

            List<String> roles = (List<String>) realmAccess.get("roles");
            if (roles == null) {
                return Collections.emptyList();
            }

            return roles.stream()
                    .map(roleName -> new SimpleGrantedAuthority("ROLE_" + roleName))
                    .collect(Collectors.toList());
        }
    }
}
```

### Accessing JWT Claims in RestControllers
```java
@RestController
@RequestMapping("/api/profile")
public class UserProfileController {

    @GetMapping("/me")
    public Map<String, Object> getCurrentUser(@AuthenticationPrincipal Jwt jwt) {
        return Map.of(
            "subject", jwt.getSubject(),
            "email", jwt.getClaimAsString("email"),
            "issuedAt", jwt.getIssuedAt(),
            "claims", jwt.getClaims()
        );
    }
}
```

---

## 7. OAuth2 Login (Client)

Spring Security OAuth2 Client enables users to authenticate via third-party identity providers using the OAuth 2.0 Authorization Code grant with PKCE (Proof Key for Code Exchange).

### Configuration in application.yml
```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          google:
            client-id: ${GOOGLE_CLIENT_ID}
            client-secret: ${GOOGLE_CLIENT_SECRET}
            scope:
              - openid
              - profile
              - email
          github:
            client-id: ${GITHUB_CLIENT_ID}
            client-secret: ${GITHUB_CLIENT_SECRET}
            scope:
              - user:email
              - read:user
```

### SecurityFilterChain for OAuth2 Client Login

```java
package com.example.security.oauth2client;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class OAuth2LoginConfig {

    private final CustomOAuth2UserService customOAuth2UserService;

    public OAuth2LoginConfig(CustomOAuth2UserService customOAuth2UserService) {
        this.customOAuth2UserService = customOAuth2UserService;
    }

    @Bean
    public SecurityFilterChain oauth2FilterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/", "/login/**", "/error").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2Login(oauth2 -> oauth2
                .loginPage("/login")
                .userInfoEndpoint(userInfo -> userInfo
                    .userService(customOAuth2UserService)
                )
                .defaultSuccessUrl("/home", true)
            );

        return http.build();
    }
}
```

### Custom OAuth2UserService Implementation
```java
package com.example.security.oauth2client;

import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

@Service
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final LocalUserRepository userRepository;

    public CustomOAuth2UserService(LocalUserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);

        String clientRegistrationId = userRequest.getClientRegistration().getRegistrationId();
        String email = oAuth2User.getAttribute("email");
        String name = oAuth2User.getAttribute("name");

        userRepository.findByEmail(email).ifPresentOrElse(
            existing -> {
                existing.setName(name);
                userRepository.save(existing);
            },
            () -> {
                LocalUser newUser = new LocalUser();
                newUser.setEmail(email);
                newUser.setName(name);
                newUser.setProvider(clientRegistrationId);
                userRepository.save(newUser);
            }
        );

        return oAuth2User;
    }
}
```

---

## 8. Method Security

Method security allows authorization checks at the service and repository layers using annotations, protecting business logic irrespective of whether it is called from a web controller, scheduled task, or asynchronous worker.

### Enabling Method Security
In Spring Security 6, annotate any configuration class with `@EnableMethodSecurity`:

```java
@Configuration
@EnableMethodSecurity(
    prePostEnabled = true, // Enables @PreAuthorize and @PostAuthorize (default true)
    securedEnabled = true, // Enables @Secured
    jsr250Enabled = true   // Enables @RolesAllowed
)
public class MethodSecurityConfig {
}
```

### Annotation Comparison
- `@PreAuthorize`: Evaluates a Spring Expression Language (SpEL) expression *before* method execution. If false, method invocation is aborted with `AccessDeniedException`.
- `@PostAuthorize`: Evaluates SpEL *after* method execution. Has access to the return value via `returnObject`.
- `@Secured`: Legacy annotation accepting an array of role names (requires `ROLE_` prefix, cannot use SpEL).
- `@RolesAllowed`: Standard JSR-250 annotation accepting role names (no SpEL).

### Practical SpEL Expressions in @PreAuthorize and @PostAuthorize

```java
package com.example.security.service;

import com.example.security.model.Document;
import org.springframework.security.access.prepost.PostAuthorize;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class DocumentService {

    // Simple role check
    @PreAuthorize("hasRole('ADMIN')")
    public void purgeAllDocuments() {
        // Business logic
    }

    // Checking specific authority
    @PreAuthorize("hasAuthority('DOCUMENT_WRITE')")
    public Document createDocument(Document doc) {
        return doc;
    }

    // Matching method parameter with current authenticated user
    @PreAuthorize("#ownerUsername == authentication.name or hasRole('ADMIN')")
    public void deleteDocument(Long docId, String ownerUsername) {
        // Only the owner or an admin can delete
    }

    // Inspecting properties of incoming arguments
    @PreAuthorize("#doc.confidential == false or hasRole('CONFIDENTIAL_VIEWER')")
    public void saveDocument(Document doc) {
        // Business logic
    }

    // Post-authorization: verify return object owner
    @PostAuthorize("returnObject.ownerUsername == authentication.name or hasRole('AUDITOR')")
    public Document getDocumentById(Long id) {
        return findDocumentFromDatabase(id);
    }

    // Calling a custom authorization service bean
    @PreAuthorize("@securityExpressions.isWorkspaceMember(#workspaceId, authentication.name)")
    public List<Document> getWorkspaceDocuments(Long workspaceId) {
        return List.of();
    }

    private Document findDocumentFromDatabase(Long id) {
        return new Document(id, "Specification", "john_doe", false);
    }
}
```

---

## 9. CORS Configuration

Cross-Origin Resource Sharing (CORS) is a browser security mechanism that restricts HTTP requests initiated from scripts to domains different from the origin serving the web page.

### Global CORS Configuration via CorsConfigurationSource
CORS must be handled before Spring Security authorization filters evaluate the request. If not configured correctly, browsers will drop pre-flight `OPTIONS` requests because they do not carry authentication credentials.

```java
package com.example.security.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

@Configuration
public class CorsSecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .authorizeHttpRequests(auth -> auth
                .anyRequest().authenticated()
            );

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        
        // Allowed origins: specific front-end domains (avoid "*" when credentials are true)
        configuration.setAllowedOrigins(List.of("https://app.example.com", "http://localhost:3000"));
        
        // Allowed HTTP methods
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        
        // Allowed request headers
        configuration.setAllowedHeaders(Arrays.asList(
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers"
        ));
        
        // Headers exposed to the browser
        configuration.setExposedHeaders(Arrays.asList("Authorization", "Content-Disposition"));
        
        // Allow cookies / authorization credentials
        configuration.setAllowCredentials(true);
        
        // Pre-flight cache duration in seconds
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
```

---

## 10. CSRF Protection

Cross-Site Request Forgery (CSRF) is an attack where a malicious website tricks a victim's browser into executing unwanted actions on a trusted site where the user is currently authenticated (via ambient session cookies or HTTP authentication).

### When Is It Safe to Disable CSRF?
- **Stateless REST APIs**: When the client stores credentials (such as JWTs) in memory, WebStorage, or headers, and the API does not use HTTP cookies for session tracking or authentication, the browser will not automatically attach credentials to cross-origin requests. In this scenario, `csrf().disable()` is safe.
- **Session-based Web Applications**: If your application uses cookies for authentication (`JSESSIONID`) or serves HTML forms to end users, CSRF protection MUST remain enabled.

### CSRF in Single Page Applications (SPA) with Spring Security 6
Spring Security 6 changed how CSRF tokens are loaded to be deferred by default. For SPAs utilizing cookies with the double-submit cookie pattern:

```java
package com.example.security.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.security.web.csrf.CsrfTokenRequestAttributeHandler;
import org.springframework.security.web.csrf.CsrfTokenRequestHandler;
import org.springframework.security.web.authentication.www.BasicAuthenticationFilter;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Configuration
public class CsrfSecurityConfig {

    @Bean
    public SecurityFilterChain spaSecurityFilterChain(HttpSecurity http) throws Exception {
        CookieCsrfTokenRepository tokenRepository = CookieCsrfTokenRepository.withHttpOnlyFalse();
        CsrfTokenRequestAttributeHandler requestHandler = new CsrfTokenRequestAttributeHandler();
        requestHandler.setCsrfRequestAttributeName(null);

        http
            .csrf(csrf -> csrf
                .csrfTokenRepository(tokenRepository)
                .csrfTokenRequestHandler(requestHandler)
            )
            .addFilterAfter(new CsrfCookieFilter(), BasicAuthenticationFilter.class)
            .authorizeHttpRequests(auth -> auth
                .anyRequest().authenticated()
            );

        return http.build();
    }

    private static class CsrfCookieFilter extends OncePerRequestFilter {
        @Override
        protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
                throws ServletException, IOException {
            CsrfToken csrfToken = (CsrfToken) request.getAttribute(CsrfToken.class.getName());
            if (csrfToken != null) {
                // Accessing the token forces deferred token generation and sets the cookie
                csrfToken.getToken();
            }
            filterChain.doFilter(request, response);
        }
    }
}
```

---

## 11. Session Management

Spring Security provides fine-grained control over how HTTP sessions are created, fixed, and bounded.

### Session Creation Policies (`SessionCreationPolicy`)
- `ALWAYS`: An `HttpSession` will always be created if one does not exist.
- `NEVER`: Spring Security will never create an `HttpSession`, but will use one if it already exists.
- `IF_REQUIRED`: (Default for web apps) An `HttpSession` is created only if required (e.g., during login).
- `STATELESS`: Spring Security will never create or use an `HttpSession` to obtain the `SecurityContext`. Ideal for pure JWT/Token-based architectures.

### Session Fixation Protection
An attacker obtains a valid session ID, forces a victim to use it (via phishing or script), waits for the victim to authenticate, and then accesses the authorized account using the known session ID.
Spring Security mitigates this by generating a new session ID upon successful login:
- `changeSessionId()`: (Default in Servlet 3.1+) Keeps session attributes but changes the session identifier.
- `migrateSession()`: Creates a new session and copies all attributes over.
- `newSession()`: Creates an entirely clean session without copying attributes.
- `none()`: Disables fixation protection (insecure).

### Concurrent Session Control
To prevent multiple simultaneous logins with the same account credentials:

```java
package com.example.security.config;

import org.springframework.boot.web.servlet.ServletListenerRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.session.SessionRegistry;
import org.springframework.security.core.session.SessionRegistryImpl;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.session.HttpSessionEventPublisher;

@Configuration
public class SessionSecurityConfig {

    @Bean
    public SecurityFilterChain sessionFilterChain(HttpSecurity http) throws Exception {
        http
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
                .sessionFixation(fixation -> fixation.changeSessionId())
                .maximumSessions(1)                     // Only 1 concurrent session per user
                .maxSessionsPreventsLogin(true)         // Reject second login instead of expiring first
                .sessionRegistry(sessionRegistry())
            );

        return http.build();
    }

    @Bean
    public SessionRegistry sessionRegistry() {
        return new SessionRegistryImpl();
    }

    @Bean
    public ServletListenerRegistrationBean<HttpSessionEventPublisher> httpSessionEventPublisher() {
        return new ServletListenerRegistrationBean<>(new HttpSessionEventPublisher());
    }
}
```

---

## 12. Custom Authorization and Error Handling

When an unauthenticated user attempts to access a protected resource, or an authenticated user lacks the required permission, Spring Security delegates handling to specific entry points and access denied handlers.

### Custom AuthenticationEntryPoint (Handles 401 Unauthorized)
Triggered when an unauthenticated request attempts to access an endpoint requiring credentials.

```java
package com.example.security.exception;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.time.Instant;
import java.util.Map;

@Component
public class CustomAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void commence(
            HttpServletRequest request,
            HttpServletResponse response,
            AuthenticationException authException
    ) throws IOException {

        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);

        Map<String, Object> body = Map.of(
            "timestamp", Instant.now().toString(),
            "status", 401,
            "error", "Unauthorized",
            "message", authException.getMessage(),
            "path", request.getRequestURI()
        );

        response.getOutputStream().println(objectMapper.writeValueAsString(body));
    }
}
```

### Custom AccessDeniedHandler (Handles 403 Forbidden)
Triggered when an authenticated user does not hold sufficient privileges.

```java
package com.example.security.exception;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.time.Instant;
import java.util.Map;

@Component
public class CustomAccessDeniedHandler implements AccessDeniedHandler {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void handle(
            HttpServletRequest request,
            HttpServletResponse response,
            AccessDeniedException accessDeniedException
    ) throws IOException {

        response.setStatus(HttpServletResponse.SC_FORBIDDEN);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);

        Map<String, Object> body = Map.of(
            "timestamp", Instant.now().toString(),
            "status", 403,
            "error", "Forbidden",
            "message", "Access denied: insufficient permissions to access this resource",
            "path", request.getRequestURI()
        );

        response.getOutputStream().println(objectMapper.writeValueAsString(body));
    }
}
```

Registering them in `SecurityFilterChain`:
```java
http.exceptionHandling(exceptions -> exceptions
    .authenticationEntryPoint(customAuthenticationEntryPoint)
    .accessDeniedHandler(customAccessDeniedHandler)
);
```

---

## 13. Security Testing

Spring Security Test provides mock credentials and request post-processors to test secured endpoints without relying on database-backed users.

### Maven Dependency
```xml
<dependency>
    <groupId>org.springframework.security</groupId>
    <artifactId>spring-security-test</artifactId>
    <scope>test</scope>
</dependency>
```

### Writing Integration Tests with MockMvc
Use `@WithMockUser`, `@WithUserDetails`, or `SecurityMockMvcRequestPostProcessors` (`user()`, `jwt()`).

```java
package com.example.security;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
public class SecurityIntegrationTests {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("Unauthenticated request to protected endpoint returns 401")
    void unauthenticatedReturns401() throws Exception {
        mockMvc.perform(get("/api/account/balance"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("Standard user accessing user endpoint returns 200")
    @WithMockUser(username = "alice", roles = {"USER"})
    void standardUserAccessSuccess() throws Exception {
        mockMvc.perform(get("/api/user/profile"))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("Standard user accessing admin endpoint returns 403 Forbidden")
    @WithMockUser(username = "bob", roles = {"USER"})
    void standardUserForbiddenOnAdminEndpoint() throws Exception {
        mockMvc.perform(delete("/api/admin/system/cache"))
                .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("Testing JWT endpoint using security mock post-processor")
    void jwtSecuredEndpointWithMockJwt() throws Exception {
        mockMvc.perform(get("/api/orders")
                .with(jwt().jwt(builder -> builder
                        .claim("sub", "john.doe@company.com")
                        .claim("scope", "orders:read")
                )))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("Testing CSRF protected POST endpoint")
    @WithMockUser(username = "charlie", roles = {"USER"})
    void csrfProtectedPostRequest() throws Exception {
        mockMvc.perform(post("/api/user/settings")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"notificationsEnabled\": true}"))
                .andExpect(status().isOk());
    }
}
```

---

## 14. Common Security Vulnerabilities and Countermeasures

### 1. SQL Injection (SQLi)
- **Vulnerability**: Attacker injects malicious SQL statements into input fields that are concatenated into raw database queries.
- **Prevention**: Use Spring Data JPA, parameterized queries (`NamedParameterJdbcTemplate`), or Criteria APIs. Never concatenate strings into queries.
  ```java
  // SECURE: Parameterized JPQL
  @Query("SELECT u FROM UserEntity u WHERE u.username = :username AND u.status = :status")
  Optional<UserEntity> findUserSafe(@Param("username") String username, @Param("status") String status);
  ```

### 2. Cross-Site Scripting (XSS)
- **Vulnerability**: Attacker injects malicious HTML/JavaScript into data that is later rendered in another user's browser without sanitization.
- **Prevention**: 
  - Rest APIs returning `application/json` are generally protected against direct script execution unless front-ends unescapedly insert strings into DOM (`innerHTML`).
  - Configure Spring Security's `HeaderWriterFilter` for Content-Security-Policy:
    ```java
    http.headers(headers -> headers
        .contentSecurityPolicy(csp -> csp
            .policyDirectives("default-src 'self'; script-src 'self'; frame-ancestors 'none';")
        )
    );
    ```

### 3. Insecure Direct Object Reference (IDOR)
- **Vulnerability**: Application exposes a reference to an internal database identifier (e.g., `/api/invoices/1045`) without validating that the authenticated user owns that invoice.
- **Prevention**: Enforce tenant or ownership checks via `@PreAuthorize` or JPA query filters.
  ```java
  @PreAuthorize("@invoiceSecurity.isOwner(#invoiceId, authentication.name)")
  @GetMapping("/invoices/{invoiceId}")
  public InvoiceResponse getInvoice(@PathVariable Long invoiceId) {
      return invoiceService.getInvoice(invoiceId);
  }
  ```

### 4. Mass Assignment (Over-Posting)
- **Vulnerability**: Client binds HTTP request payloads directly to JPA entities. An attacker appends fields like `"isAdmin": true` or `"balance": 999999` to update statements.
- **Prevention**: Always decouple domain entities from incoming request models using dedicated DTOs (Data Transfer Objects) with Bean Validation. Never accept JPA entities directly in controller method signatures.

### 5. Broken Authentication and Credential Stuffing
- **Vulnerability**: Weak passwords, lack of brute force protection, or predictable password resets.
- **Prevention**:
  - Enforce strong password policies with regular expressions and validator checks.
  - Implement rate limiting (e.g., Bucket4j or Redis token bucket) on `/auth/login` and `/auth/register`.
  - Use `BCryptPasswordEncoder` with a work factor of at least 12.
  - Always implement constant-time comparison when verifying tokens to prevent side-channel timing attacks.

---

## 15. Complete Spring Security Configuration Blueprint

Below is an end-to-end, production-ready Spring Security configuration blueprint integrating stateless JWT authentication, custom exception handling, CORS, disabled CSRF for REST APIs, and method security.

```java
package com.example.security.config;

import com.example.security.exception.CustomAccessDeniedHandler;
import com.example.security.exception.CustomAuthenticationEntryPoint;
import com.example.security.jwt.JwtAuthenticationFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfigurationSource;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class ApplicationSecurityConfig {

    private final JwtAuthenticationFilter jwtAuthFilter;
    private final UserDetailsService userDetailsService;
    private final CustomAuthenticationEntryPoint authenticationEntryPoint;
    private final CustomAccessDeniedHandler accessDeniedHandler;
    private final CorsConfigurationSource corsConfigurationSource;

    public ApplicationSecurityConfig(
            JwtAuthenticationFilter jwtAuthFilter,
            UserDetailsService userDetailsService,
            CustomAuthenticationEntryPoint authenticationEntryPoint,
            CustomAccessDeniedHandler accessDeniedHandler,
            CorsConfigurationSource corsConfigurationSource
    ) {
        this.jwtAuthFilter = jwtAuthFilter;
        this.userDetailsService = userDetailsService;
        this.authenticationEntryPoint = authenticationEntryPoint;
        this.accessDeniedHandler = accessDeniedHandler;
        this.corsConfigurationSource = corsConfigurationSource;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .cors(cors -> cors.configurationSource(corsConfigurationSource))
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .exceptionHandling(exceptions -> exceptions
                .authenticationEntryPoint(authenticationEntryPoint)
                .accessDeniedHandler(accessDeniedHandler)
            )
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(
                    "/api/v1/auth/**",
                    "/v3/api-docs/**",
                    "/swagger-ui/**",
                    "/swagger-ui.html",
                    "/actuator/health"
                ).permitAll()
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/v1/manager/**").hasAnyRole("ADMIN", "MANAGER")
                .anyRequest().authenticated()
            )
            .authenticationProvider(authenticationProvider())
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public AuthenticationProvider authenticationProvider() {
        DaoAuthenticationProvider authProvider = new DaoAuthenticationProvider();
        authProvider.setUserDetailsService(userDetailsService);
        authProvider.setPasswordEncoder(passwordEncoder());
        return authProvider;
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }
}
```

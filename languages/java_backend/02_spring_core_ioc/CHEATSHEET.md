# Spring Core & IoC Quick Reference Cheatsheet

## 1. Bean Stereotype Annotations

| Annotation | Target Layer | Primary Purpose & Features |
|---|---|---|
| `@Component` | Generic / Cross-cutting | Base stereotype for any Spring-managed component |
| `@Service` | Business / Service | Encapsulates business logic, transactions, workflows |
| `@Repository` | Persistence / DAO | Data access; enables automatic `DataAccessException` translation |
| `@Controller` | Presentation (MVC) | Handles HTTP requests, web page routing, view resolution |
| `@RestController` | Presentation (REST) | `@Controller` + `@ResponseBody`; serializes return values to JSON |
| `@Configuration` | Infrastructure / Setup | Declares `@Bean` factory methods; enhanced with CGLIB proxy |

## 2. Bean Scopes Reference

| Scope Name | Target Lifecycle | Proxy Requirement |
|---|---|---|
| `singleton` (Default) | Single shared instance per `ApplicationContext` | None |
| `prototype` | New instance created per injection or lookup | Scoped proxy if injected into singleton |
| `request` | Single instance per HTTP request lifecycle | `ScopedProxyMode.TARGET_CLASS` |
| `session` | Single instance per HTTP session lifecycle | `ScopedProxyMode.TARGET_CLASS` |
| `application` | Single instance per `ServletContext` | `ScopedProxyMode.TARGET_CLASS` |

## 3. Bean Lifecycle Order

| Phase | Hook / Callback Mechanism | Execution Context |
|---|---|---|
| 1. Instantiation | Constructor invocation | Reflection via container |
| 2. Property Injection | Constructor / Setter / Field wiring | Dependencies populated |
| 3. Aware Interfaces | `BeanNameAware`, `BeanFactoryAware`, `ApplicationContextAware` | Injects container infrastructure |
| 4. BPP Pre-Init | `BeanPostProcessor.postProcessBeforeInitialization()` | Intercepts raw bean |
| 5. Initialization | `@PostConstruct` -> `InitializingBean.afterPropertiesSet()` -> `initMethod` | Custom initialization logic |
| 6. BPP Post-Init | `BeanPostProcessor.postProcessAfterInitialization()` | Generates AOP / transactional proxies |
| 7. Destruction | `@PreDestroy` -> `DisposableBean.destroy()` -> `destroyMethod` | Executed on context shutdown |

## 4. AOP Advice Types

| Advice Type | Annotation | Execution Timing Relative to JoinPoint |
|---|---|---|
| Before | `@Before("pointcut()")` | Runs prior to target method execution |
| After Returning | `@AfterReturning(pointcut = "...", returning = "ret")` | Runs only if target completes normally |
| After Throwing | `@AfterThrowing(pointcut = "...", throwing = "ex")` | Runs only if target throws exception |
| After (Finally) | `@After("pointcut()")` | Runs unconditionally after target method completes |
| Around | `@Around("pointcut()")` | Wraps execution; controls `joinPoint.proceed()` call |

## 5. Spring Expression Language (SpEL) Syntax

| Construct | Syntax Example | Meaning |
|---|---|---|
| Property Placeholder | `${server.port:8080}` | Resolves environment/property value with default |
| SpEL Expression | `#{2 * T(java.lang.Math).PI * 10}` | Evaluates runtime mathematical expression |
| Bean Reference | `#{@authService.isAdmin(#userId)}` | Invokes method on managed Spring bean |
| Elvis Operator | `#{systemProperties['ENV'] ?: 'DEV'}` | Fallback if left expression evaluates to null |
| Safe Navigation | `#{order?.customer?.email}` | Prevents `NullPointerException` on null property |
| Collection Filter | `#{employees.?[salary > 50000]}` | Filters collection elements matching predicate |

## 6. Conditional Bean Annotations

| Annotation | Activation Condition |
|---|---|
| `@Profile("prod")` | Matches active Spring environment profile |
| `@ConditionalOnProperty` | Matches configured property name, value, or presence |
| `@ConditionalOnClass` | Classpath contains specified class |
| `@ConditionalOnMissingBean` | No bean of target type or name currently registered |
| `@Conditional(CustomCondition.class)` | Custom `Condition.matches()` returns true |

# QnA: API Gateway and Service Mesh

1. What is an API Gateway? List 8 cross-cutting concerns it handles and explain why centralizing them is better than implementing them in each microservice.
An API Gateway is a server that acts as a single entry point into a system, sitting between external clients and internal microservices. The 8 primary cross-cutting concerns it handles are: 1) Routing traffic to correct downstream services, 2) Authentication and Authorization (validating JWTs/tokens), 3) Rate limiting to prevent abuse, 4) SSL/TLS termination to offload crypto work, 5) Request/response transformation (header manipulation), 6) Load balancing across service replicas, 7) Caching frequent responses, and 8) Observability injection (starting trace IDs). 
Centralizing these concerns is significantly better than implementing them in individual microservices because it adheres to the DRY (Don't Repeat Yourself) principle. If you implement rate limiting or SSL in every service, you force developers to maintain complex network code in multiple languages (Java, Go, Node.js). It also ensures a consistent security posture—policies are enforced globally at the edge before malicious traffic ever reaches internal networks. Furthermore, updating a security policy only requires changing the Gateway configuration rather than redeploying 50 different microservices.

2. What is the Backend for Frontend (BFF) pattern? What problem does a single API Gateway have when serving both web and mobile clients? Show the BFF aggregation pattern in Python.
The Backend for Frontend (BFF) pattern involves creating separate, dedicated API Gateways for different client types (e.g., one for Mobile, one for Web, one for 3rd-party APIs). 
A single, general-purpose API Gateway struggles when serving both web and mobile clients because their needs are drastically different. Web applications usually run on fast connections and require dense, rich data payloads to render complex UIs. Mobile devices often operate on slower, unreliable cellular networks and have smaller screens, meaning they need heavily optimized, aggregated endpoints that return only essential fields to save bandwidth and battery. A single gateway results in a bloated, compromised API.
```python
async def get_mobile_order_summary(order_id: str):
    # Fetch in parallel
    order, tracking = await asyncio.gather(
        client.get(f'/orders/{order_id}'),
        client.get(f'/tracking/{order_id}')
    )
    # Return minimal data for mobile
    return {
        'id': order_id,
        'status': order['status'],
        'delivery': tracking['date']
    }
```

3. What is a Service Mesh? What specific problem does it solve that an API Gateway does not? Describe the sidecar proxy pattern.
A Service Mesh is a dedicated infrastructure layer designed to handle East-West (service-to-service) communication within a cluster, whereas an API Gateway primarily handles North-South (external-to-internal) traffic. 
As a microservices architecture grows, services communicating directly with one another experience network instability. Developers often embed retry logic, timeouts, circuit breakers, and metrics collection directly into their application code. This leads to massive code duplication and inconsistent network behavior across the system. The Service Mesh solves this by extracting all network logic out of the application code.
It achieves this using the "sidecar proxy pattern." A lightweight proxy (like Envoy) is deployed alongside every single application container within the same Pod. The application only communicates with localhost; the sidecar intercepts the outbound request, applies policies (mTLS, retries, routing), and forwards it to the destination's sidecar, completely transparent to the application code.

4. What is Istio? What are the two components: data plane (Envoy) and control plane (Istiod)? What does each handle?
Istio is the most popular open-source service mesh implementation designed originally for Kubernetes. It provides traffic management, security, and observability out of the box. 
Istio is divided into two distinct components: the data plane and the control plane.
The **Data Plane** consists of thousands of Envoy proxies deployed as sidecars next to your application containers. These proxies are responsible for actually handling the bytes on the wire. They intercept all inbound and outbound network traffic, encrypt it, enforce rate limits, execute retries, and emit telemetry data (metrics and spans).
The **Control Plane** (specifically the `istiod` binary) is the brain of the mesh. It does not touch data traffic. Instead, it translates high-level YAML configuration into Envoy-specific configurations and pushes them to the sidecars dynamically. It also acts as a Certificate Authority (CA), generating and distributing TLS certificates to the sidecars to enable mTLS.

5. What is a VirtualService in Istio? Write a VirtualService that implements a canary deployment with 90/10 traffic split and 3 retries on gateway errors.
A `VirtualService` in Istio defines the routing rules for traffic sent to a specific service. It tells the mesh *how* to route traffic. You can use it to define retries, timeouts, fault injection, and complex routing logic like path-based routing or traffic splitting.
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: payment-route
spec:
  hosts:
  - payment-service
  http:
  - route:
    - destination:
        host: payment-service
        subset: v1
      weight: 90
    - destination:
        host: payment-service
        subset: v2
      weight: 10
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: gateway-error,503
```

6. What is a DestinationRule in Istio? Explain the outlierDetection (circuit breaking) configuration: consecutive5xxErrors, interval, baseEjectionTime, maxEjectionPercent.
While a `VirtualService` defines how to route traffic, a `DestinationRule` defines what happens to the traffic *after* it has been routed to a specific service. It is used to configure load balancing algorithms, TLS settings (mTLS), and circuit breaking parameters.
`outlierDetection` is Istio's implementation of a circuit breaker. It works passively by monitoring the health of individual endpoints.
- `consecutive5xxErrors`: The number of consecutive 5xx server errors a pod must return before the circuit breaker trips.
- `interval`: How often the proxy evaluates the error counter (e.g., every 10 seconds).
- `baseEjectionTime`: How long the failing pod is removed from the load balancing pool (e.g., 30s). Subsequent ejections multiply this time.
- `maxEjectionPercent`: The maximum percentage of pods in the upstream cluster that can be ejected at once. If set to 50%, and you have 4 pods, no more than 2 will be ejected, ensuring the service doesn't completely collapse under load due to aggressive circuit breaking.

7. What is mTLS in a service mesh? How does Istio's PeerAuthentication enforce it? What is the difference between PERMISSIVE and STRICT mode?
Mutual TLS (mTLS) is a security protocol where both the client and the server authenticate each other using cryptographic certificates, and the traffic between them is fully encrypted. In a service mesh, the control plane automatically provisions and rotates these certificates for every sidecar proxy. When Service A calls Service B, the sidecars intercept the call and establish an mTLS tunnel, completely transparently to the applications.
Istio enforces this using the `PeerAuthentication` custom resource, which defines how traffic will be tunneled to a specific workload or namespace.
- **PERMISSIVE mode**: The sidecar accepts both encrypted mTLS traffic and plaintext HTTP traffic. This is crucial during migrations when some services are in the mesh and others are not, preventing immediate outages.
- **STRICT mode**: The sidecar demands mTLS. Any plaintext traffic sent to the service is immediately rejected. This is the desired state for a zero-trust production environment.

8. What is an AuthorizationPolicy in Istio? Write a policy that allows only the Order Service to call the POST /payments/charge endpoint of the Payment Service.
An `AuthorizationPolicy` in Istio defines fine-grained access control rules for workloads in the mesh. Because Istio enforces mTLS, every service has a cryptographic identity (SPIFFE ID). An AuthorizationPolicy leverages these identities to explicitly allow or deny traffic, replacing brittle IP-based firewall rules with strong cryptographic identity verification.
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: payment-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: payment-service
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/order-service"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/payments/charge"]
```

9. What is fault injection in Istio? How do you inject a 2-second delay for 10% of requests and 503 errors for 5%? What is it used for?
Fault injection is a chaos engineering technique where deliberate errors or delays are introduced into a system to test its resilience. Instead of modifying application code to simulate failures, Istio's sidecar proxies can inject network faults transparently. This proves whether your timeouts, retries, and circuit breakers actually work in production under duress.
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: inventory-chaos
spec:
  hosts:
  - inventory-service
  http:
  - fault:
      delay:
        percentage: { value: 10 }
        fixedDelay: 2s
      abort:
        percentage: { value: 5 }
        httpStatus: 503
    route:
    - destination: { host: inventory-service }
```
It is used to ensure that a slow dependency (e.g., Inventory being 2 seconds slow) doesn't cause a cascading failure that brings down the entire Order API.

10. Explain token bucket rate limiting. How does Redis make it work across multiple API Gateway instances? Show the key naming strategy that implements sliding window per minute.
Token bucket is a rate-limiting algorithm where tokens are added to a "bucket" at a constant rate. A request must consume a token from the bucket to proceed. If the bucket is empty, the request is rejected. It allows for short bursts of traffic (up to the bucket's capacity) while enforcing a strict long-term rate.
In a distributed system, you run multiple instances of an API Gateway. If you rate-limit in memory, a user could bypass the limit by hitting different gateways. Redis acts as a centralized, highly-available in-memory datastore where all gateway instances read and write the token counts atomically.
For a simple sliding window or fixed window per minute, the Redis key naming strategy incorporates the time window directly into the string: `rate_limit:{client_api_key}:{timestamp_minute}` (e.g., `rate_limit:user123:2849302`). By using `INCR` and setting a TTL on this key, multiple gateways can instantly coordinate a user's request count without race conditions.

11. What is the difference between North-South traffic (external to cluster) and East-West traffic (service-to-service)? What handles each in a microservices architecture?
North-South traffic refers to data flowing in and out of your data center or Kubernetes cluster. This is traffic originating from end-users, mobile apps, or external third-party systems that must traverse the public internet to reach your system. It is handled by an **API Gateway** or Ingress Controller, which focuses on SSL termination, user authentication, global rate limiting, and routing edge traffic.
East-West traffic refers to the internal communication between different microservices within the secure boundary of your cluster. For example, when the Cart Service calls the Pricing Service. This traffic never touches the public internet. It is handled by a **Service Mesh** (like Istio), which focuses on internal mTLS, inter-service circuit breaking, fine-grained access control, and generating distributed traces for request paths.

12. How does Istio handle service discovery compared to client-side discovery with Consul? What Kubernetes resource does it build its service registry from?
In client-side service discovery (like older Netflix OSS Eureka or raw Consul SDKs), the application itself queries a registry to find the IP addresses of dependencies, then implements its own load balancing logic in code. This couples the application to the discovery tool.
Istio abstracts this completely. The application simply makes a standard DNS request for `http://payment-service`. The Istio control plane (`istiod`) constantly watches the Kubernetes API server for changes to `Service` and `EndpointSlice` resources. When pods scale up or down, Istio dynamically pushes the new IP addresses directly to the Envoy sidecar proxies. When the application sends traffic to the generic hostname, the Envoy sidecar intercepts it, looks at its internal routing table (populated by Istiod), and load balances the request to a specific healthy Pod IP, completely transparent to the app.

13. What is a Service Entry in Istio? When do you need one? Give an example of calling an external payment gateway (Stripe) through Istio.
By default, Istio's service registry only knows about internal services running within the Kubernetes cluster. If a microservice attempts to call an external API (like Stripe, Twilio, or an external database), the Envoy proxy might not know how to route it, or strict egress policies might block it.
A `ServiceEntry` is an Istio resource that adds external endpoints to the mesh's internal service registry. This allows you to apply mesh features (like timeouts, retries, and metrics) to external calls.
```yaml
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: stripe-api
spec:
  hosts:
  - api.stripe.com
  ports:
  - number: 443
    name: https
    protocol: HTTPS
  resolution: DNS
  location: MESH_EXTERNAL
```
You need this when you want observability into external dependencies or when you run a zero-trust network that explicitly blocks all outbound egress traffic unless documented via a ServiceEntry.

14. What is the difference between Kong, Nginx, and AWS API Gateway? When would you choose each? What is the main limitation of AWS API Gateway for microservices?
- **Nginx** is a traditional, highly-performant reverse proxy and web server. You choose it for simple ingress routing, basic rate limiting, and static file serving where complex API management features aren't needed.
- **Kong** is built on Nginx but adds a massive ecosystem of Lua-based plugins. It is a true API Management platform. You choose Kong when you need declarative configuration, complex auth plugins (OAuth, JWT, OIDC), developer portals, and cloud-agnostic deployments.
- **AWS API Gateway** is a fully managed, serverless gateway native to AWS. You choose it when you are heavily invested in the AWS ecosystem, particularly Serverless architectures (Lambda), and want zero infrastructure to manage.
The main limitation of AWS API Gateway for large microservice environments is its high cost at massive scale, vendor lock-in, and lack of flexibility for complex, on-premise, or hybrid multi-cloud routing scenarios compared to Kong or self-hosted Nginx.

15. What is header-based routing in a service mesh? Show how you would route users with the x-canary-user: true header to a new version of the Order Service for A/B testing.
Header-based routing allows a proxy to inspect the HTTP headers of an incoming request and make routing decisions based on their values, rather than just the URL path. This is immensely powerful for A/B testing, canary releases, and "dark launching" features to internal QA users in a live production environment.
By matching a specific header, Istio can direct a tiny fraction of specific traffic to a `v2` subset while keeping 100% of standard traffic on `v1`.
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-route
spec:
  hosts:
  - order-service
  http:
  - match:
    - headers:
        x-canary-user:
          exact: "true"
    route:
    - destination:
        host: order-service
        subset: v2
  - route:
    - destination:
        host: order-service
        subset: v1
```

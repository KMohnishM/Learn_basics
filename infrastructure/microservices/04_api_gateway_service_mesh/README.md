# Module 4: API Gateway and Service Mesh

## Introduction to Edge and Internal Traffic

In a microservices architecture, traffic is generally classified into two categories:
1. **North-South Traffic**: Traffic entering your cluster from the outside world (users, external systems).
2. **East-West Traffic**: Traffic moving horizontally within your cluster (service-to-service communication).

Managing these two types of traffic efficiently is critical to the security, scalability, and resilience of your system. This is where API Gateways and Service Meshes come in.

---

## 1. API Gateway — The Entry Point

An API Gateway is a reverse proxy that sits in front of all microservices and acts as a single entry point for external consumers. It handles cross-cutting concerns so that individual services can focus purely on business logic.

### Key Responsibilities
- **Routing**: Route `/orders` to the Order Service, `/payments` to the Payment Service.
- **Authentication/Authorization**: Validate JWTs, OAuth tokens, or API keys before forwarding requests.
- **Rate Limiting**: Protect backend services from abuse and DDoS attacks.
- **SSL Termination**: Decrypt HTTPS traffic at the edge, reducing computational overhead on internal services.
- **Request/Response Transformation**: Add internal headers (e.g., `X-User-ID`), strip sensitive external headers, or translate formats.
- **Load Balancing**: Distribute incoming requests across multiple instances of a service.
- **Caching**: Cache responses for identical, read-only requests.
- **Observability**: Centralized logging, metrics collection, and tracing injection.

### Architecture Diagram

```text
Internet
   |
   | (HTTPS)
   v
[API Gateway] <--- SSL termination, Auth, Rate limiting, Routing
   |         \
   |          \--- [Order Service]
   |           \
   |            \--- [Payment Service]
   |             \
   |              \--- [User Service]
   |               \
   |                \--- [Catalog Service]
```

---

## 2. Popular API Gateways

There are numerous options for API Gateways, ranging from traditional web servers to cloud-native, declarative proxies.

### Kong Gateway

Kong is one of the most popular open-source API Gateways, built on top of Nginx and OpenResty (Lua). It uses a plugin architecture.

#### Declarative Configuration Example (`kong.yml`)

```yaml
_format_version: "3.0"

services:
  - name: order-service
    url: http://order-service:8080
    routes:
      - name: orders-route
        paths: ["/api/v1/orders"]
        methods: ["GET", "POST", "PATCH", "DELETE"]

  - name: payment-service
    url: http://payment-service:8080
    routes:
      - name: payments-route
        paths: ["/api/v1/payments"]
        methods: ["POST"]

plugins:
  # Verify JWT token signature and expiration
  - name: jwt
    config:
      claims_to_verify: ["exp"]

  # Enforce rate limiting backed by Redis
  - name: rate-limiting
    config:
      minute: 100
      policy: redis
      redis_host: redis.infrastructure.local
      redis_port: 6379

  # Handle Cross-Origin Resource Sharing
  - name: cors
    config:
      origins: ["https://app.example.com"]
      methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
      headers: ["Authorization", "Content-Type"]
      max_age: 3600

  # Inject tracking headers
  - name: request-transformer
    config:
      add:
        headers: ["X-Gateway-Version: 3.0", "X-Trace-Enabled: true"]
```

### Nginx (As an API Gateway)

Nginx is traditionally a web server, but its robust reverse proxy capabilities make it a viable, high-performance API Gateway.

#### Nginx Configuration

```nginx
upstream order_service {
    # Distribute traffic based on active connections
    least_conn;
    
    # Load balancing with weights
    server order-service-1:8080 weight=3 max_fails=3 fail_timeout=30s;
    server order-service-2:8080 weight=3 max_fails=3 fail_timeout=30s;
    server order-service-3:8080 weight=1 max_fails=3 fail_timeout=30s;
    
    # Keep idle connections open to avoid TCP handshake overhead
    keepalive 32;
}

upstream payment_service {
    server payment-service-1:8080;
    server payment-service-2:8080;
    keepalive 16;
}

# Define rate limit zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL Configuration
    ssl_certificate     /etc/ssl/certs/api.crt;
    ssl_certificate_key /etc/ssl/private/api.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Apply rate limiting globally
    limit_req zone=api_limit burst=20 nodelay;

    # Order Service Routing
    location /api/v1/orders {
        proxy_pass         http://order_service;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Request-ID $request_id;
        
        # Timeouts
        proxy_read_timeout 10s;
        proxy_connect_timeout 2s;
    }

    # Payment Service Routing
    location /api/v1/payments {
        proxy_pass http://payment_service;
        
        # Payments might take longer to process via third-party gateways
        proxy_read_timeout 30s;
        proxy_connect_timeout 2s;
    }
    
    # Custom error pages
    error_page 429 /429.json;
    location = /429.json {
        return 429 '{"error": "Too Many Requests", "retry_after": 60}';
        default_type application/json;
    }
}
```

### AWS API Gateway (Serverless)

AWS API Gateway is a managed service that integrates deeply with AWS Lambda and IAM.

```yaml
# serverless.yml
service: order-api

provider:
  name: aws
  runtime: python3.9
  stage: production
  region: us-east-1

functions:
  createOrder:
    handler: handler.create_order
    events:
      - http:
          path: /orders
          method: post
          cors: true
          authorizer:
            name: jwtAuthorizer
            type: TOKEN
            identitySource: method.request.header.Authorization
          request:
            schemas:
              application/json:
                schema: ${file(schemas/create-order.json)}
                name: CreateOrderModel
          # Configure per-endpoint throttling
          throttle:
            burstLimit: 200
            rateLimit: 100

  jwtAuthorizer:
    handler: authorizer.verify_token
```

---

## 3. Backend for Frontend (BFF) Pattern

### The Problem
A single API Gateway serving all clients (web, iOS, Android, third-party partners) creates a one-size-fits-all API. 
- Mobile devices have limited bandwidth and screen space; they need smaller, optimized payloads.
- Web apps have more bandwidth and often require dense, detailed data.
- Third parties require strict versioning and backward compatibility.

### The Solution
Instead of one massive API Gateway, we create multiple, client-specific gateways known as **Backend for Frontends (BFFs)**.

```text
[Web App]        [Mobile App]        [Third-party]
     |                 |                   |
[Web BFF]        [Mobile BFF]      [Partner Gateway]
     |                 |                   |
     +---------+-------+-------------------+
               |
      [Internal Microservices]
         (Orders, Users, Inventory)
```

### BFF Responsibilities
- **Data Aggregation**: Fetch data from multiple internal services and combine it into a single response.
- **Data Transformation**: Filter out unneeded fields to reduce payload size.
- **Protocol Translation**: Translate external REST/GraphQL calls to internal gRPC or RPC.
- **Client-specific Caching**: Cache heavily used data specific to a platform.

### Implementation Example in Python (FastAPI)

```python
import asyncio
import httpx
from fastapi import FastAPI, HTTPException, Header

app = FastAPI(title="Mobile BFF")

# Simulated internal HTTP clients
order_client = httpx.AsyncClient(base_url="http://order-service:8080/internal")
shipping_client = httpx.AsyncClient(base_url="http://shipping-service:8080/internal")

@app.get("/api/mobile/orders/{order_id}/summary")
async def get_order_summary_for_mobile(
    order_id: str, 
    x_user_id: str = Header(...)
):
    """
    Mobile BFF endpoint: aggregates order + tracking data in one call.
    Mobile only needs: status, estimated delivery, item count, total.
    """
    try:
        # 1. Fire parallel requests to internal microservices
        order_req = order_client.get(f'/orders/{order_id}', headers={"X-User-ID": x_user_id})
        tracking_req = shipping_client.get(f'/shipments/{order_id}/tracking')
        
        # 2. Wait for both to complete concurrently
        order_res, tracking_res = await asyncio.gather(order_req, tracking_req)
        
        if order_res.status_code == 404:
            raise HTTPException(status_code=404, detail="Order not found")
            
        order_data = order_res.json()
        tracking_data = tracking_res.json() if tracking_res.status_code == 200 else {}
        
        # 3. Transform and filter data (Mobile-optimized response)
        # We drop heavy fields like individual item descriptions, images, 
        # and full billing history.
        return {
            'order_id': order_id,
            'status': order_data.get('status'),
            'estimated_delivery': tracking_data.get('estimated_delivery_date'),
            'item_count': len(order_data.get('items', [])),
            'total_amount': order_data.get('total_amount'),
            'tracking_url': tracking_data.get('carrier_tracking_url')
        }
        
    except httpx.RequestError as e:
        # Handle internal network failures gracefully
        raise HTTPException(status_code=503, detail="Downstream service unavailable")
```

---

## 4. Service Mesh — What and Why

### The Problem
API Gateways handle North-South traffic well, but what about East-West (service-to-service) traffic?
If the Order Service calls the Payment Service, it needs to handle:
- **Security**: Encrypting traffic (mTLS).
- **Resilience**: Retries, timeouts, circuit breaking.
- **Observability**: Emitting tracing spans and metrics.
- **Routing**: Canary deployments and A/B testing internally.

If developers implement this in application code, they end up with duplicated logic across hundreds of microservices, written in multiple languages (Java, Go, Python, Node).

### The Solution: Service Mesh
A Service Mesh offloads network concerns to an out-of-process **sidecar proxy** that runs alongside every instance of every microservice. 

The application only talks to `localhost`; the sidecar intercepts the traffic and handles all the complex networking rules.

```text
[Order Service Pod]                   [Payment Service Pod]
+-------------------+                 +-------------------+
| Order Container   |                 | Payment Container |
| (app code)        |                 | (app code)        |
|      |            |                 |      |            |
| [Envoy Sidecar]   |<===============>| [Envoy Sidecar]   |
|  mTLS, retry,     |   mTLS tunnel   |  circuit breaker, |
|  tracing          |                 |  tracing          |
+-------------------+                 +-------------------+
         |                                      |
         +------------------+-------------------+
                            |
                     [Control Plane]
                    (Istiod / Consul)
            (Pushes config, certs, policies)
```

**Two Core Components:**
1. **Data Plane**: The collection of sidecar proxies (e.g., Envoy) that actually intercept and forward the bytes.
2. **Control Plane**: The central management layer (e.g., Istiod) that configures the proxies and distributes certificates.

---

## 5. Istio Service Mesh Configuration

Istio is the leading service mesh for Kubernetes. It configures the Envoy proxies using Custom Resource Definitions (CRDs).

### VirtualService: Traffic Routing
A `VirtualService` defines *how* traffic is routed to a destination.

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: payment-service-route
spec:
  hosts:
  - payment-service.production.svc.cluster.local
  http:
  
  # 1. Advanced Routing: Canary deployment
  # Split traffic: 90% to stable (v1), 10% to canary (v2)
  - route:
    - destination:
        host: payment-service
        subset: v1
      weight: 90
    - destination:
        host: payment-service
        subset: v2
      weight: 10
      
    # 2. Resilience: Timeouts and Retries
    timeout: 10s
    retries:
      attempts: 3
      perTryTimeout: 3s
      # Only retry on network errors, not on application 4xx errors
      retryOn: gateway-error,connect-failure,503
```

### DestinationRule: Post-Routing Policies
A `DestinationRule` defines what happens to traffic *after* it has been routed to a specific service.

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: payment-service-dest
spec:
  host: payment-service.production.svc.cluster.local
  
  # Define the subsets used in the VirtualService
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
      
  trafficPolicy:
    # Upgrade all internal traffic to HTTP/2
    connectionPool:
      http:
        h2UpgradePolicy: UPGRADE
        http1MaxPendingRequests: 100
        maxRequestsPerConnection: 10
        
    # Circuit Breaker: Outlier Detection
    outlierDetection:
      # If a pod returns 5 consecutive 5xx errors...
      consecutive5xxErrors: 5
      # Check every 10 seconds...
      interval: 10s
      # Eject the failing pod from the load balancer pool for 30s
      baseEjectionTime: 30s
      # Never eject more than 50% of the pods to prevent cascading failures
      maxEjectionPercent: 50
```

### PeerAuthentication: Enforcing mTLS
Service meshes automatically issue identities (SPIFFE IDs) to workloads and rotate their certificates.

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: strict-mtls
  namespace: production
spec:
  mtls:
    # STRICT mode: Reject any plaintext HTTP traffic.
    # PERMISSIVE mode: Accept both mTLS and plaintext (used during migrations).
    mode: STRICT
```

### AuthorizationPolicy: Access Control
Once workloads have cryptographic identities, you can write network policies based on those identities, not just IP addresses.

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: payment-access-control
  namespace: production
spec:
  selector:
    matchLabels:
      app: payment-service
  rules:
  # Allow the Order Service to call the POST /payments/charge endpoint
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/order-service-sa"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/payments/charge"]
```

---

## 6. Advanced Traffic Management

### Fault Injection (Chaos Engineering)
You can intentionally inject failures at the network layer to test how resilient your microservices are.

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: inventory-service-chaos
spec:
  hosts:
  - inventory-service
  http:
  - fault:
      # Inject a 2-second delay into 10% of requests
      delay:
        percentage:
          value: 10.0
        fixedDelay: 2s
      # Inject an HTTP 503 error into 5% of requests
      abort:
        percentage:
          value: 5.0
        httpStatus: 503
    route:
    - destination:
        host: inventory-service
```

### Header-Based Routing (A/B Testing)
Route specific users to a different version of a service based on HTTP headers (e.g., a cookie or custom testing header).

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: recommendation-service
spec:
  hosts:
  - recommendation-service
  http:
  # If request contains 'x-beta-user: true', route to v2
  - match:
    - headers:
        x-beta-user:
          exact: "true"
    route:
    - destination:
        host: recommendation-service
        subset: v2
  
  # Default route for everyone else
  - route:
    - destination:
        host: recommendation-service
        subset: v1
```

---

## 7. Rate Limiting Deep Dive

Rate limiting is crucial to prevent abuse, manage quotas, and ensure fair usage.

### Common Algorithms
1. **Fixed Window**: Counters reset at fixed intervals (e.g., exactly at 12:00, 12:01). Subject to spikes at window edges.
2. **Sliding Window**: Smooths out traffic over a rolling timeframe. More memory intensive.
3. **Token Bucket**: Tokens are added to a bucket at a fixed rate. Requests consume tokens. Allows for short bursts.
4. **Leaky Bucket**: Requests enter a queue and are processed at a strictly constant rate. Smooths out traffic completely.

### Token Bucket Implementation with Redis (Python)

To support horizontal scaling, state must be shared across API Gateway instances. Redis is standard for this.

```python
import redis
import time
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()
redis_client = redis.Redis(host='redis', port=6379, db=0)

class DistributedRateLimiter:
    def __init__(self, redis_conn, rpm: int):
        self.redis = redis_conn
        self.rpm = rpm
        self.window = 60  # 1 minute

    def is_allowed(self, client_id: str) -> tuple[bool, dict]:
        """
        Implements a simple fixed-window counter in Redis using Pipelining.
        For production, a sliding window or Redis Cell (Token Bucket) module is preferred.
        """
        current_window = int(time.time() // self.window)
        key = f'rate_limit:{client_id}:{current_window}'
        
        # Use a transaction/pipeline to ensure atomicity
        pipeline = self.redis.pipeline()
        pipeline.incr(key)
        # Ensure the key expires after the window to save memory
        pipeline.expire(key, self.window * 2)
        
        results = pipeline.execute()
        count = results[0]
        
        remaining = max(0, self.rpm - count)
        allowed = count <= self.rpm
        reset_time = (current_window + 1) * self.window

        headers = {
            'X-RateLimit-Limit': str(self.rpm),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset_time)
        }
        
        return allowed, headers

rate_limiter = DistributedRateLimiter(redis_client, requests_per_minute=100)

@app.middleware('http')
async def rate_limit_middleware(request: Request, call_next):
    # Identify the client (by API key, JWT claim, or IP address)
    client_id = request.headers.get('X-API-Key') or request.client.host
    
    allowed, headers = rate_limiter.is_allowed(client_id)

    if not allowed:
        # Deny request and return 429 Too Many Requests
        return JSONResponse(
            status_code=429,
            content={'error': 'Rate limit exceeded'},
            headers={
                **headers,
                'Retry-After': str(int(headers['X-RateLimit-Reset']) - int(time.time()))
            }
        )

    # Process request if allowed
    response = await call_next(request)
    
    # Inject limit headers into the response
    for key, value in headers.items():
        response.headers[key] = value
        
    return response
```

### Production Checklist for Gateway & Mesh
- **Always set timeouts**: Never make network calls without a strict bounded timeout.
- **Limit Retries**: Implement exponential backoff and jitter. Cap total retries to avoid retry storms.
- **Fail Fast**: Use circuit breakers to stop calling failing dependencies immediately.
- **Secure by Default**: Default to STRICT mTLS and deny-all AuthorizationPolicies.
- **Trace Everything**: Ensure the API Gateway generates the initial trace ID and propagates it to all downstreams.

---

## 8. WebAssembly (Wasm) Plugins in Service Mesh

Modern service meshes like Istio use Envoy as the data plane. While Envoy is written in C++ for performance, extending it with custom C++ code is notoriously difficult. To solve this, Envoy supports WebAssembly (Wasm).

### Why Wasm?
- **Polyglot**: You can write proxy plugins in Go, Rust, AssemblyScript, or C++.
- **Secure**: Wasm runs in a secure, sandboxed memory environment. If a plugin crashes, it does not crash the proxy.
- **Dynamic**: Plugins can be loaded, updated, and unloaded dynamically without restarting the Envoy proxy.

### EnvoyFilter for Wasm

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: custom-auth-wasm
  namespace: production
spec:
  workloadSelector:
    labels:
      app: api-gateway
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: GATEWAY
      listener:
        filterChain:
          filter:
            name: "envoy.filters.network.http_connection_manager"
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.wasm
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.http.wasm.v3.Wasm
          config:
            name: "custom-auth"
            vm_config:
              runtime: "envoy.wasm.runtime.v8"
              code:
                local:
                  filename: "/var/local/lib/wasm-filters/custom-auth.wasm"
```

## 9. API Gateway vs Ingress Controllers

It's common to confuse API Gateways with Kubernetes Ingress Controllers.

### Kubernetes Ingress
- Primarily Layer 7 HTTP/HTTPS routing based on hostname and path.
- Standardized via the Kubernetes `Ingress` object (and now the `Gateway API`).
- Focuses purely on exposing services to the internet.

### API Gateway
- Sits above or alongside the Ingress Controller.
- Adds business-level logic: Rate limiting per user tier, API key validation, payload transformation, monetization.

Often, tools like Kong or Traefik serve dual purposes: acting as both the Kubernetes Ingress Controller and the API Gateway.

## 10. Conclusion
Mastering edge routing and internal service mesh policies is critical for scaling microservices. Remember that adding a mesh introduces latency (typically 1-3ms per hop) and significant memory overhead for the sidecars. Evaluate if your system's complexity justifies a mesh before adopting one globally.

# Microservices Traffic Management Cheatsheet

## API Gateway vs. Service Mesh

| Feature | API Gateway (North-South) | Service Mesh (East-West) |
| :--- | :--- | :--- |
| **Primary Traffic** | External users to internal cluster | Internal service to internal service |
| **Typical Tools** | Kong, Nginx, AWS API GW, Traefik | Istio, Linkerd, Consul Connect |
| **Security focus** | OAuth, API Keys, WAF, JWT | mTLS, SPIFFE identity, internal RBAC |
| **Topology** | Centralized proxy at edge | Decentralized sidecar proxies |
| **Rate Limiting** | Global/per-user quotas | Localized/per-service protections |
| **Knowledge** | Knows about users & devices | Knows about pods & namespaces |

## Popular API Gateways

| Gateway | Best For | Key Architecture | Limitations |
| :--- | :--- | :--- | :--- |
| **Kong** | Enterprise API Management | Nginx + OpenResty (Lua) plugins | Complex DB requirement (Postgres) for classic |
| **Nginx** | High-performance basic routing | C-based, event-driven | Lacks advanced API portal features natively |
| **AWS API GW** | Serverless / Lambda integrations | Managed AWS Service | Expensive at high volume, vendor lock-in |
| **Traefik** | Container-native environments | Go-based, dynamic discovery | Less extensive plugin ecosystem than Kong |

## Istio Core Resource Types

| Resource | Purpose | Code Keyword |
| :--- | :--- | :--- |
| **VirtualService** | How to route traffic (retries, splits) | `route`, `match`, `weight`, `retries` |
| **DestinationRule** | What happens after routing | `trafficPolicy`, `outlierDetection`, `subsets` |
| **PeerAuthentication** | Enforce mTLS (Strict/Permissive) | `mtls: mode: STRICT` |
| **AuthorizationPolicy**| Access control rules (Allow/Deny)| `rules`, `from`, `source`, `principals` |
| **ServiceEntry** | Add external APIs to mesh registry | `resolution: DNS`, `location: MESH_EXTERNAL` |

## Traffic Management Patterns

| Pattern | Description | Implementation Tool |
| :--- | :--- | :--- |
| **Canary Release** | Send 5% traffic to v2, 95% to v1 | `VirtualService` weights |
| **Blue/Green** | 100% switch from v1 to v2 | `VirtualService` weight toggle |
| **A/B Testing** | Route based on HTTP headers | `VirtualService` header matching |
| **Circuit Breaking** | Stop calling a failing pod | `DestinationRule` outlierDetection |
| **Fault Injection** | Inject latency or 500 errors | `VirtualService` fault delay/abort |
| **Traffic Mirroring** | Send copy of prod traffic to QA | `VirtualService` mirror |

## Rate Limiting Algorithms

| Algorithm | Mechanism | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Fixed Window** | Reset counter at top of minute | Simple to implement (Redis INCR) | Spikes at edge of windows |
| **Sliding Window** | Evaluates exact past 60s dynamically | Smooth enforcement | Memory heavy (logs timestamps) |
| **Token Bucket** | Replenish tokens at fixed rate | Allows temporary bursts | Complex tuning |
| **Leaky Bucket** | Process at strict constant rate | Smooths downstream traffic | Punishes bursty users (delays) |

## When to use a Backend for Frontend (BFF)

Use a BFF when:
- [ ] Mobile app requires significantly less data than Web app.
- [ ] You need to aggregate calls from 3+ services into a single UI payload.
- [ ] Mobile/Web use different authentication mechanisms.
- [ ] You want UI teams to own their specific gateway routing logic.

```text
[Mobile Client] ---> [Mobile BFF (NodeJS)] ---> [Orders], [Inventory]
[Web Client]    ---> [Web BFF (GraphQL)]   ---> [Orders], [Inventory], [History]
```

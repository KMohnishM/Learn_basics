# Module 5: Kubernetes Networking, Services, and Ingress Deep Dive

This module covers the comprehensive details of how networking functions within a Kubernetes cluster, from the lowest level network namespaces and Container Network Interfaces (CNI) up to layer 7 Ingress controllers and the modern Gateway API.

## 1. Kubernetes Networking Model

The Kubernetes networking model is defined by a set of foundational axioms that dictate how network traffic flows between the various entities in a cluster. The model abstracts away the underlying host network and provides a flat network space for all pods.

### The Axioms of Kubernetes Networking
1. All Pods can communicate with all other Pods without NAT.
2. All Nodes can communicate with all Pods without NAT.
3. The IP that a Pod sees itself as is the same IP that others see it as.

This means that Kubernetes expects a flat, routable network within the cluster. It does not mandate how this is achieved, only that it is achieved. 

### IP Address Management (IPAM)
A Kubernetes cluster typically requires three distinct, non-overlapping IP CIDR blocks:
- Node CIDR: The IP range from which the physical or virtual machines (nodes) receive their IP addresses. This is usually provided by the underlying infrastructure (AWS VPC, On-Prem DHCP, etc.).
- Pod CIDR: The IP range used for assigning IP addresses to individual Pods. A subset of this range (a /24 by default) is allocated to each Node as a `podCIDR`. When a Pod is scheduled on a Node, the CNI plugin assigns an IP address from that Node's `podCIDR` to the Pod.
- Service CIDR: A virtual IP range used entirely for Kubernetes Services (ClusterIPs). These IPs do not exist on any physical interface. They are intercepted by `kube-proxy` (via iptables or IPVS) and NATed to the actual Pod IPs backing the service.

```yaml
# Example: kube-controller-manager configuration demonstrating CIDR allocations
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
networking:
  dnsDomain: cluster.local
  serviceSubnet: 10.96.0.0/12
  podSubnet: 10.244.0.0/16
```

When a Node is registered, the Kubernetes controller-manager allocates a subnet (e.g., 10.244.1.0/24) to it. 
Node 1: 10.244.1.0/24
Node 2: 10.244.2.0/24
Node 3: 10.244.3.0/24

If a Pod on Node 1 wants to talk to a Pod on Node 2, the traffic must physically traverse the underlying Node network. How this traffic is encapsulated or routed is determined by the CNI.

## 2. Container Network Interface (CNI) Deep Dive

CNI (Container Network Interface) is a standard API that container runtimes (like containerd or CRI-O) use to set up network interfaces in containers. When a Pod is created, the container runtime calls the CNI plugin to configure the network namespace, create a veth pair, assign an IP, and set up routes.

### Overlay vs. Flat Networking
- Overlay Networking: Encapsulates Pod traffic within Node traffic. The underlying network only sees traffic between Node IPs. Examples: VXLAN, IP-in-IP. This is useful when the underlying network cannot route Pod IPs.
- Flat (Routable) Networking: Pod IPs are directly routable on the underlying network. This avoids encapsulation overhead but requires integration with the infrastructure router (e.g., via BGP or AWS VPC CNI).

### Flannel
Flannel is a simple and easy-to-configure layer 3 network fabric designed for Kubernetes. It is commonly used with VXLAN.
In VXLAN mode, Flannel creates a virtual network interface (flannel.1). When Pod A (10.244.1.2) sends a packet to Pod B (10.244.2.3), Flannel intercepts the packet, encapsulates it inside an outer UDP packet destined for Node 2's IP, and sends it over the host network. Node 2 receives the UDP packet, decapsulates it, and forwards the inner packet to Pod B.

### Calico
Calico provides both network connectivity and network policy enforcement. It can operate in several modes:
- BGP Mode (No Encapsulation): Calico acts as a virtual router on each Node, using BGP to peer with other Nodes or top-of-rack switches. Pod IPs are natively routable.
- IPIP or VXLAN Overlay: Used when BGP is not feasible (e.g., across public clouds).

```yaml
# Calico Installation CustomResource for VXLAN CrossSubnet mode
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
    - blockSize: 26
      cidr: 10.244.0.0/16
      encapsulation: VXLANCrossSubnet
      natOutgoing: Enabled
      nodeSelector: all()
```

### Cilium and eBPF
Cilium uses eBPF (Extended Berkeley Packet Filter) to provide highly efficient networking, observability, and security. eBPF allows running sandboxed programs within the Linux kernel without changing kernel source code or loading kernel modules.
Cilium can entirely replace `kube-proxy`, bypassing iptables overhead. By hooking directly into the kernel's socket layer, Cilium can route packets faster and provide deep layer 7 visibility.

## 3. Services and Traffic Routing

Pods are ephemeral; their IPs change when they are recreated. Kubernetes Services provide a stable virtual IP (ClusterIP) and DNS name that load balances traffic to a dynamic set of Pods.

### kube-proxy
`kube-proxy` runs on every Node. It watches the Kubernetes API for Service and EndpointSlice objects. When a Service is created, `kube-proxy` configures the host operating system to capture traffic destined for the Service IP and redirect it to one of the backing Pods.

- iptables mode (Default): `kube-proxy` installs a complex web of iptables NAT rules. Every time a Service or Pod is added/removed, iptables must be updated. For clusters with thousands of Services, iptables becomes a CPU bottleneck because it evaluates rules sequentially.
- IPVS mode: Uses the IP Virtual Server functionality built into the Linux kernel. IPVS uses hash tables for faster rule lookup, providing better performance and lower latency for large clusters.
- eBPF (Cilium): Bypasses iptables/IPVS entirely.

### Types of Services
1. ClusterIP: The default. Exposes the Service on a cluster-internal IP.
2. NodePort: Exposes the Service on each Node's IP at a static port (default range: 30000-32767).
3. LoadBalancer: Provisions an external load balancer (via cloud provider integration) that points to the NodePorts.
4. ExternalName: Maps the Service to a DNS name (e.g., db.example.com).

```yaml
# Example: ClusterIP Service with specific ports
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: app-tier
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: metrics
      port: 9090
      targetPort: 9090
```

### Headless Services
A Headless Service is created by explicitly setting `clusterIP: None`. 
Instead of providing a single load-balanced IP, the cluster DNS returns multiple A records, one for each Pod backing the Service. This is essential for StatefulSets (e.g., databases like Cassandra or MongoDB) where clients need to connect directly to individual replicas.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: stateful-db
spec:
  clusterIP: None
  selector:
    app: db
  ports:
    - port: 5432
```

### EndpointSlices
Historically, Kubernetes used a single `Endpoints` object for each Service. If a Service had 1000 Pods, the `Endpoints` object contained 1000 IP addresses. Updating one Pod meant sending the entire massive `Endpoints` object to every `kube-proxy` instance.
`EndpointSlices` solve this by breaking the endpoints into smaller, manageable chunks (default 100 endpoints per slice).

## 4. CoreDNS and In-Cluster Name Resolution

CoreDNS is the default DNS server for Kubernetes. It runs as a Deployment and exposes a ClusterIP Service (usually `kube-dns` at `10.96.0.10`). Every Pod is configured via `/etc/resolv.conf` to use this DNS server.

### The Corefile
CoreDNS is configured via a ConfigMap named `coredns`. The configuration is defined in a `Corefile`.

```text
# Default Corefile configuration
.:53 {
    errors
    health {
       lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
       max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
```

### The ndots:5 Issue
By default, Kubernetes configures Pod `/etc/resolv.conf` with `search` domains (e.g., `default.svc.cluster.local`, `svc.cluster.local`, `cluster.local`) and `options ndots:5`.
The `ndots:5` setting means that if a domain name has fewer than 5 dots, the DNS resolver will try appending the search domains before trying the name as an absolute domain.

If an application queries `google.com` (1 dot):
1. Tries `google.com.default.svc.cluster.local.` (NXDOMAIN)
2. Tries `google.com.svc.cluster.local.` (NXDOMAIN)
3. Tries `google.com.cluster.local.` (NXDOMAIN)
4. Tries `google.com.` (Success, via upstream forwarder)

This generates a massive amount of unnecessary DNS traffic and latency. 
Solutions:
- Always use Fully Qualified Domain Names (FQDNs) by appending a trailing dot: `google.com.`
- Override the `dnsConfig` in the Pod spec to reduce `ndots`.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-optimized-pod
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
  dnsConfig:
    options:
    - name: ndots
      value: "2"
```

## 5. Ingress Controllers and Gateway API

While Services handle layer 4 routing, Ingress handles layer 7 HTTP/HTTPS routing.

### Ingress Controllers
The Kubernetes Ingress resource by itself does nothing. You must install an Ingress Controller (e.g., NGINX Ingress, HAProxy, Traefik). The controller watches for Ingress resources, generates configuration for its reverse proxy engine, and reloads it.

```yaml
# Example: Standard Ingress Resource
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: minimal-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /testpath
        pathType: Prefix
        backend:
          service:
            name: test
            port:
              number: 80
```

### Gateway API (The Modern Evolution)
The Gateway API is the successor to Ingress. Ingress was too simple and required massive usage of custom annotations for advanced features (like header matching, weighted routing, etc.).
The Gateway API splits the configuration into distinct personas:
- GatewayClass: Defined by infrastructure providers.
- Gateway: Deployed by cluster operators to provision load balancers.
- HTTPRoute (and TCPRoute, TLSRoute): Deployed by application developers to define how traffic reaching a Gateway should be routed.

```yaml
# Example: Gateway API Configuration

# 1. The Gateway (Operator Persona)
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: external-https
  namespace: infra
spec:
  gatewayClassName: acme-lb
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    hostname: "*.example.com"
    tls:
      mode: Terminate
      certificateRefs:
      - name: example-com-cert

---
# 2. The HTTPRoute (Developer Persona)
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: store-route
  namespace: store-ns
spec:
  parentRefs:
  - name: external-https
    namespace: infra
  hostnames:
  - "store.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /v2
    backendRefs:
    - name: store-v2
      port: 8080
      weight: 90
    - name: store-v3-canary
      port: 8080
      weight: 10
```

The Gateway API supports true cross-namespace routing, allowing a Gateway in the `infra` namespace to route traffic to a Service in the `store-ns` namespace securely, governed by ReferenceGrants.

## 6. NetworkPolicies: Zero-Trust Security

By default, all Pods in a Kubernetes cluster can communicate with each other freely. NetworkPolicies allow you to isolate Pods using a zero-trust model. They are implemented by the CNI plugin (e.g., Calico, Cilium), NOT by Kubernetes itself. If your CNI does not support NetworkPolicies, the resources are accepted by the API but ignored.

### The Default Deny Strategy
The recommended approach for securing a cluster is to start by denying all traffic in every namespace, then explicitly allowing required traffic.

```yaml
# Default Deny All Policy for a Namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: secure-ns
spec:
  podSelector: {} # Selects all pods in the namespace
  policyTypes:
  - Ingress
  - Egress
```
Applying this policy instantly blocks all incoming and outgoing traffic for all Pods in `secure-ns`, including DNS resolution.

### Fine-Grained Allow Policies
Once default deny is in place, you must explicitly allow DNS, and then specific application traffic.

```yaml
# Allow DNS Egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: secure-ns
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

```yaml
# Allow Web to DB
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-allow-web
  namespace: secure-ns
spec:
  podSelector:
    matchLabels:
      app: db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web
    ports:
    - protocol: TCP
      port: 5432
```

NetworkPolicies are additive. If multiple policies apply to a Pod, the rules are combined. There is no concept of a "Deny" rule in standard Kubernetes NetworkPolicies; everything is implicit deny (if any policy selects the Pod) and explicit allow.

## Conclusion

Understanding Kubernetes networking is essential for designing resilient, secure, and high-performing clusters.
- The CNI handles low-level Pod IP assignment and routing.
- Services and `kube-proxy` handle reliable internal load balancing.
- CoreDNS provides the internal service discovery fabric.
- Ingress and Gateway API handle external edge routing and layer 7 features.
- NetworkPolicies enforce zero-trust security boundaries.

Always monitor `kube-proxy` rules, CNI health, and CoreDNS metrics, as these three components are the most frequent culprits in cluster communication failures. Mastering them elevates you from an operator to an architect.

## 7. Advanced Networking Concepts

### Deep Dive: Cilium eBPF Host Routing
Cilium dramatically changes Kubernetes networking by replacing iptables with Extended Berkeley Packet Filter (eBPF). EBPF allows sandboxed programs to execute in the Linux kernel without requiring changes to kernel source code or loading kernel modules.
When eBPF host routing is enabled, Cilium bypasses standard iptables completely. It attaches eBPF programs directly to the network interfaces (via XDP or eXpress Data Path) and the socket layer.
This enables socket-level load balancing. When an application writes to a socket destined for a ClusterIP, the eBPF program intercepts the syscall, translates the ClusterIP to a backend Pod IP using highly efficient eBPF maps, and forwards the packet directly.
This architecture eliminates massive latency spikes associated with sequential iptables rule evaluations, allowing large clusters to route traffic at line rate. This approach represents a massive performance boost over legacy networking mechanisms and avoids context switches that drag down application throughput.

### Complete Multi-Tier NetworkPolicy Architecture
Building a secure multi-tier application requires enforcing strict boundaries. The following manifest set demonstrates a comprehensive zero-trust approach for a web application and its database.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: prod
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-coredns-egress
  namespace: prod
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-allow-ingress
  namespace: prod
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  ingress:
  - ports:
    - protocol: TCP
      port: 8080
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-db-allow
  namespace: prod
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 5432
```
This architecture completely locks down the `prod` namespace, ensures DNS works via UDP/TCP port 53, exposes only port 8080 on the frontend, and guarantees that only the `backend` pods can communicate with the `database` pods on port 5432. All other connections, explicit or inferred, are denied entirely by the CNI engine operating on the node itself.

### Complete Gateway API Configuration with Canary Splitting
The Gateway API allows developers to easily configure advanced routing behaviors like header matching and canary deployments without complex annotations.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: istio
spec:
  controllerName: istio.io/gateway-controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: main-gateway
  namespace: default
spec:
  gatewayClassName: istio
  listeners:
  - name: http
    protocol: HTTP
    port: 80
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-route
  namespace: default
spec:
  parentRefs:
  - name: main-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api/v1
      headers:
      - name: x-canary
        value: "true"
    backendRefs:
    - name: api-canary
      port: 8080
  - matches:
    - path:
        type: PathPrefix
        value: /api/v1
    backendRefs:
    - name: api-stable
      port: 8080
      weight: 90
    - name: api-canary
      port: 8080
      weight: 10
```
This configuration sets up an HTTP listener, explicitly routes traffic containing the `x-canary: true` header to the canary backend, and distributes all other traffic with a 90/10 weight split between stable and canary endpoints. This makes progressive delivery much simpler and natively embedded in the object model instead of forcing administrators to rely on out of band configuration frameworks or fragile Nginx annotations that lack API validation.

### externalTrafficPolicy: Local vs Cluster Mechanics
When exposing services via NodePort or LoadBalancer, `externalTrafficPolicy` determines how traffic is routed internally.
By default, the policy is `Cluster`. External traffic hits a node, and `kube-proxy` load-balances it to a pod, which might reside on a different node. This cross-node hop requires Source NAT (SNAT), meaning the application pod sees the node's internal IP as the source, not the original client IP.
Setting `externalTrafficPolicy: Local` forces the node to only route external traffic to pods located on that specific node. This avoids the extra network hop and bypasses SNAT, allowing the pod to read the real client IP. However, if a node receives traffic and has no local pods for the service, it drops the connection. This requires careful load balancer health check configuration to only route to nodes with active pods, shifting complexity from the cluster out to the cloud provider's ingress layer.

### CoreDNS ndots: 5 Optimization
The default `ndots: 5` setting in `/etc/resolv.conf` means any domain query with fewer than 5 dots triggers a sequential search through all local cluster domains before resolving externally, causing severe latency and DNS load.
To fix this bottleneck at the pod level without altering application code, administrators can inject a `dnsConfig` block in the deployment specification:

```yaml
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:1.0
      dnsConfig:
        options:
        - name: ndots
          value: "2"
```
This optimization reduces the threshold, so queries for external domains (like `api.stripe.com`) are immediately treated as absolute, bypassing the exhaustive internal search and significantly decreasing DNS latency. This is one of the most vital tuning knobs for high traffic, highly connected microservices platforms processing intensive outbound payloads.

### Networking Summary

Kubernetes networking is a vast and complex topic, essential for building secure and scalable applications.

Mastering these concepts allows you to architect robust internal and external traffic routing mechanisms.

Understanding the nuances of CNIs, Services, Ingress, and NetworkPolicies is critical for any Kubernetes administrator.

With the evolution of the Gateway API and eBPF technologies like Cilium, the landscape is constantly improving.

Stay updated with the latest CNCF developments to leverage the full potential of Kubernetes networking capabilities.

The transition from iptables to programmable networking represents a massive leap forward in scalability.

As multi-cluster deployments become more common, service mesh patterns and cross-cluster routing will become standard.

Properly securing your network with default-deny policies is the most impactful security measure you can implement.

By understanding the underlying mechanisms of CoreDNS, kube-proxy, and CNI plugins, you can troubleshoot the most complex distributed system issues.

Network isolation, traffic shaping, and robust ingress are the pillars of a production-ready Kubernetes environment.


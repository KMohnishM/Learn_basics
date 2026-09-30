# CHEATSHEET: Kubernetes Networking & Ingress

## 1. Kubernetes Service Types Comparison Table

| Service Type | Routing Scope | Default Usage Scenario | IP Allocation | Routing Mechanism |
|---|---|---|---|---|
| **ClusterIP** | Internal Only | Microservice-to-microservice communication | Assigned from Service CIDR | kube-proxy (iptables/IPVS) |
| **NodePort** | External & Internal | Direct node access, simple local testing | ClusterIP + Node Port (30000+) | Node IP -> kube-proxy -> Pod |
| **LoadBalancer** | External & Internal | Production ingress traffic via Cloud Provider | ClusterIP + Node Port + Cloud IP | Cloud LB -> NodePort -> Pod |
| **ExternalName** | Internal Only | Routing internal pods to external legacy databases | None (CNAME record only) | CoreDNS CNAME resolution |
| **Headless** | Internal Only | StatefulSets, database clusters, peer discovery | None (`clusterIP: None`) | CoreDNS returns multiple Pod A records |

## 2. Ingress vs Gateway API Architecture (ASCII Diagram)

```text
=============================================================================
                          INGRESS API ARCHITECTURE
=============================================================================
[ External Client ]
        |
        v
[ Cloud Load Balancer ]
        |
        v
[ Ingress Controller Pod ] (Reads standard Ingress YAML + custom annotations)
        |
        +---> [ Service A ] ---> [ Pod A1, Pod A2 ] (via path /app1)
        |
        +---> [ Service B ] ---> [ Pod B1 ]         (via path /app2)

=============================================================================
                         GATEWAY API ARCHITECTURE
=============================================================================
                           [ GatewayClass ] (Infrastructure Provider)
                                  ^
                                  |
[ External Client ]         [ Gateway ] (Cluster Operator - provisions LB)
        |                         |
        v                         v
[ Cloud Load Balancer ] <--- (Configured by Gateway Controller)
        |
        v
[ HTTPRoute (App Team A) ] ---> [ Service A ] ---> [ Pod A1, Pod A2 ] (Cross-namespace supported)
        |
[ HTTPRoute (App Team B) ] ---> [ Service B ] ---> [ Pod B1 ]
```

## 3. NetworkPolicy Quick Templates

### Template: Default Deny All (Best Practice Starting Point)
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: my-namespace
spec:
  podSelector: {} # Selects all
  policyTypes:
  - Ingress
  - Egress
```

### Template: Allow DNS Resolution (Crucial if Default Deny is applied)
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-core-dns
  namespace: my-namespace
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
```

### Template: Allow Specific Ingress (e.g., Web to DB)
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-db
  namespace: my-namespace
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
          app: webserver
    ports:
    - protocol: TCP
      port: 5432
```

## 4. CoreDNS Troubleshooting Commands

| Goal | Command |
|---|---|
| Check CoreDNS Pod Status | `kubectl get pods -n kube-system -l k8s-app=kube-dns` |
| View CoreDNS Logs | `kubectl logs -n kube-system -l k8s-app=kube-dns -c coredns` |
| Spin up a debug pod | `kubectl run -it --rm debug --image=infoblox/dnstools --restart=Never` |
| Test internal DNS resolution | `nslookup my-service.my-namespace.svc.cluster.local` |
| Test external DNS resolution | `nslookup google.com` |
| View Pod DNS Config | `cat /etc/resolv.conf` (Inside a pod) |
| Force CoreDNS Restart | `kubectl rollout restart deployment coredns -n kube-system` |

## 5. CNI Plugin Verification

```text
# Check if Nodes are Ready (NotReady often indicates a CNI issue)
kubectl get nodes

# Check the Pod CIDR assigned to a specific Node
kubectl get node <node-name> -o jsonpath='{.spec.podCIDR}'

# View CNI configuration files on the host node
ls -la /etc/cni/net.d/
cat /etc/cni/net.d/10-calico.conflist
```

## 6. externalTrafficPolicy Visualized

```text
externalTrafficPolicy: Cluster (Default)
Client --> Node 1 (Port 32000) --> SNAT applied --> Pod on Node 2
(Extra hop, Source IP lost)

externalTrafficPolicy: Local
Client --> Node 1 (Port 32000) --> Pod on Node 1 (Direct delivery)
(No extra hop, Source IP preserved. If Node 1 has no pod, packet dropped)
```

# CHEATSHEET: Kubernetes Production Operations

## 1. QoS Classes Matrix

| QoS Class | Condition for Assignment | OOM Priority | Behavior under Node Pressure |
| :--- | :--- | :--- | :--- |
| **Guaranteed** | Requests == Limits for CPU & Mem for all containers | Highest Priority (Evicted Last) | Safe from OOM unless they exceed their limits. `oom_score_adj` is very low. |
| **Burstable** | Requests specified, but don't equal limits | Medium Priority | Allowed to burst up to limits. Evicted based on usage vs request ratio. |
| **BestEffort** | No requests or limits specified at all | Lowest Priority (Evicted First) | Can consume all free node memory, but instantly killed if node starves. |

---

## 2. Pod Termination Sequence Flowchart

```text
+---------------------+
| 1. API DELETE CALL  | -> Pod status changes to 'Terminating'
+---------------------+
           |
           v
+---------------------+    (Concurrent actions start)
| Endpoint Controller | -> Removes Pod IP from Service Endpoints. Stops new traffic.
+---------------------+
           |
           v
+---------------------+
|    preStop Hook     | -> Runs inside container (e.g., 'sleep 10' or deregister)
+---------------------+
           |
           v
+---------------------+
|   SIGTERM Signal    | -> Sent to PID 1. App must handle this for clean shutdown.
+---------------------+
           |
           |                  +----------------------------------------------+
           |                  | Grace Period (terminationGracePeriodSeconds) |
           |                  +----------------------------------------------+
           v
+---------------------+
|   SIGKILL Signal    | -> Sent forcefully if app still running after grace period.
+---------------------+
```

---

## 3. Node Maintenance Commands

| Command | Purpose | Behavior |
| :--- | :--- | :--- |
| `kubectl cordon <node>` | Mark Un-schedulable | Prevents new Pods from scheduling. Existing Pods run untouched. |
| `kubectl uncordon <node>` | Mark Schedulable | Allows scheduler to place new Pods on the node again. |
| `kubectl drain <node>` | Evict Workloads | Safely evicts all Pods. Respects PDBs and grace periods. |
| `kubectl drain <node> --ignore-daemonsets` | Evict (Standard) | Standard command. DaemonSets are managed by system, ignore them. |
| `kubectl drain <node> --delete-emptydir-data` | Evict (Force Data) | Force eviction even if Pod uses emptyDir (local ephemeral storage). |

---

## 4. Quick Templates

### HPA v2 (CPU + Custom Metric)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 500m
```

### PodDisruptionBudget (PDB)
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
spec:
  minAvailable: 2 
  selector:
    matchLabels:
      app: api-server
```

### Robust Probes Configuration
```yaml
containers:
- name: app
  image: backend:latest
  startupProbe:
    httpGet:
      path: /health/startup
      port: 8080
    failureThreshold: 30
    periodSeconds: 10
  livenessProbe:
    httpGet:
      path: /health/live
      port: 8080
    failureThreshold: 3
    periodSeconds: 10
  readinessProbe:
    httpGet:
      path: /health/ready
      port: 8080
    failureThreshold: 2
    periodSeconds: 5
```

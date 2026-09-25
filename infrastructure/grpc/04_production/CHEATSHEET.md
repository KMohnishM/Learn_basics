# gRPC Production Cheat Sheet

## 1. Production Interceptors Suite Template in Python

*Use this standard wrapper to chain essential observability and resilience middleware.*

```python
import grpc
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from grpc_interceptor import ExceptionToStatusInterceptor
from my_auth import JWTValidationInterceptor
from my_metrics import PrometheusMetricsInterceptor

def serve():
    # 1. Enable OpenTelemetry Distributed Tracing globally
    GrpcInstrumentorServer().instrument()

    # 2. Chain interceptors (Order matters: outermost first)
    interceptors = [
        PrometheusMetricsInterceptor(),         # RED Metrics
        JWTValidationInterceptor(SECRET_KEY),   # Auth Validation
        ExceptionToStatusInterceptor()          # Graceful Error Handling
    ]

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=50),
        interceptors=interceptors,
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
            ('grpc.keepalive_time_ms', 60000),
            ('grpc.keepalive_timeout_ms', 20000),
        ]
    )
    my_service_pb2_grpc.add_MyServiceServicer_to_server(MyServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
```

## 2. Kubernetes Native gRPC Probes YAML Configuration

*Requires Kubernetes 1.24+ and the `grpc.health.v1.Health` service implemented.*

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grpc-service
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-grpc-app:latest
        ports:
        - containerPort: 50051
          name: grpc
        # Liveness: Restart pod if dead
        livenessProbe:
          grpc:
            port: 50051
            service: "my.package.MyService"
          initialDelaySeconds: 15
          periodSeconds: 10
        # Readiness: Remove from LB pool if not serving
        readinessProbe:
          grpc:
            port: 50051
            service: "my.package.MyService"
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 3. grpcurl & grpcui Commands Reference

### ASCII Workflow Diagram
```text
+-----------+      (1) Reflection Request       +---------------+
|           | --------------------------------> |               |
|  grpcurl  |      (2) Schema Descriptors       |  gRPC Server  |
|           | <-------------------------------- |               |
+-----------+      (3) JSON -> Binary RPC       +---------------+
```

| Action | Command |
| :--- | :--- |
| List all services | `grpcurl -plaintext localhost:50051 list` |
| List methods | `grpcurl -plaintext localhost:50051 list my.Service` |
| Inspect payload | `grpcurl -plaintext localhost:50051 describe my.Request` |
| Call with JSON | `grpcurl -plaintext -d '{"id": 1}' localhost:50051 my.Service/Get` |
| Pass Metadata | `grpcurl -plaintext -rpc-header 'auth: token' ...` |
| Open Web UI | `grpcui -plaintext localhost:50051` |

## 4. Client-Side Load Balancing & mTLS Setup Snippets

### Client-Side DNS Load Balancing (Round Robin)
```python
import grpc
import json

# Configure client to load balance across multiple resolved IPs
service_config = json.dumps({"loadBalancingConfig": [{"round_robin": {}}]})
options = [('grpc.service_config', service_config)]

# Use 'dns:///' scheme to trigger DNS resolution
channel = grpc.insecure_channel('dns:///my-service.default.svc.cluster.local:50051', options=options)
```

### mTLS (Mutual TLS) Channel Setup
```python
import grpc

# Load PKI assets
with open('ca.pem', 'rb') as f: ca_cert = f.read()
with open('client-key.pem', 'rb') as f: client_key = f.read()
with open('client-cert.pem', 'rb') as f: client_cert = f.read()

credentials = grpc.ssl_channel_credentials(
    root_certificates=ca_cert,
    private_key=client_key,
    certificate_chain=client_cert
)
# Secure channel enforces TLS
channel = grpc.secure_channel('secure.backend.local:50051', credentials)
```

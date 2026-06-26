# Module 4 Exercise: Deploying an Internal Cache

In the labs, we deployed our Python API and exposed it to the internet using a `LoadBalancer` Service.
Most real-world applications also have backend databases or caches that should **never** be exposed to the internet.

## The Challenge

Your task is to write the Kubernetes YAML manifests to deploy a Redis cache. The Python API pods will talk to this Redis cache internally.

1. **Write `redis-deployment.yaml`**:
   - Name: `redis-deployment`
   - Replicas: 1
   - Image: `redis:alpine`
   - Container Port: 6379

2. **Write `redis-service.yaml`**:
   - Name: `redis-service`
   - **Crucial**: This service must NOT be accessible from the internet. It should only be accessible from inside the K8s cluster. (Hint: What is the default Service type in Kubernetes?)
   - Port: 6379
   - TargetPort: 6379

Good luck! Check the `solution/` folder when you are done.

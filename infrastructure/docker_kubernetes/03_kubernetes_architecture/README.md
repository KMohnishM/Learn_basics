# Module 3: Kubernetes Architecture

## 1. Declarative Orchestration Philosophy

### Imperative vs Declarative

The core of Kubernetes is its declarative model. In imperative systems, you specify the exact steps to achieve a desired state. In a declarative system like Kubernetes, you specify the desired state, and the system works to achieve and maintain it.

Imperative approaches often suffer from state drift. If a script fails halfway, the system is left in an unknown state. The next run of the script might not know how to recover. Declarative systems, however, are idempotent. You can apply the same configuration multiple times, and the system will simply ensure the actual state matches the desired state.

Consider the following imperative commands:
```bash
docker run -d --name web-server nginx
docker run -d --name db-server postgres
```

If `web-server` crashes, the system does not automatically restart it unless specific flags are used, and even then, complex dependencies are hard to manage.

Now consider the declarative Kubernetes manifest:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
```
Here, you declare that you want 3 replicas of the nginx container. Kubernetes constantly monitors the cluster, and if a pod dies, it automatically spins up a new one to maintain the desired state of 3 replicas.

### The Control Loop

At the heart of Kubernetes are control loops, also known as controllers. A control loop is a non-terminating loop that regulates the state of the system.

The basic logic of a control loop is:
1. Read the current state of the system (Actual State).
2. Read the desired state of the system (Desired State).
3. If Actual State != Desired State, take action to make them match.

In Go, a simplified version of a controller loop looks like this:

```go
for {
    actualState := getActualState()
    desiredState := getDesiredState()
    
    if actualState != desiredState {
        reconcile(actualState, desiredState)
    }
    
    time.Sleep(10 * time.Second)
}
```

However, Kubernetes controllers are much more sophisticated. They use a watch mechanism rather than simple polling.

### Level-triggered vs Edge-triggered

Kubernetes relies on level-triggered logic rather than edge-triggered logic.

- **Edge-triggered**: Action is taken only when a state change occurs (an event). If the event is missed (e.g., due to network issues), the system might stay out of sync forever.
- **Level-triggered**: Action is taken based on the current state (the level), regardless of how it got there. If an event is missed, the next reconciliation loop will still see the discrepancy and fix it.

Kubernetes controllers watch for events (edge) for efficiency, but they also perform periodic resyncs (level) to ensure the system reaches the desired state even if events are missed. This combination makes Kubernetes highly resilient.

## 2. Control Plane Components Deep Dive

The control plane is the brain of the Kubernetes cluster. It makes global decisions about the cluster, detects and responds to cluster events.

### kube-apiserver

The `kube-apiserver` is the front end of the Kubernetes control plane. It exposes the Kubernetes API. All communication between components, and external communication with the cluster, goes through the API server.

Key characteristics:
- It is stateless. It stores all data in etcd.
- It scales horizontally. You can run multiple instances to balance traffic and provide high availability.
- It provides authentication, authorization, and admission control.

A typical API request goes through several stages:
1. Authentication: Verifying the identity of the user or service account.
2. Authorization: Checking if the identity has permission to perform the action (e.g., RBAC).
3. Mutating Admission: Modifying the object before it is saved (e.g., injecting sidecars).
4. Object Schema Validation: Ensuring the object conforms to the OpenAPI schema.
5. Validating Admission: Final checks before saving (e.g., checking quotas).
6. Etcd Write: Saving the object to etcd.

### etcd

`etcd` is a consistent and highly-available key-value store used as Kubernetes' backing store for all cluster data.

Key characteristics:
- It uses the Raft consensus algorithm to maintain consistency across a cluster of nodes.
- It is strongly consistent, meaning reads always return the latest write.
- It watches for changes. The `kube-apiserver` can watch specific keys or prefixes and get notified instantly when they change.

Data in etcd is stored hierarchically. For example, a pod might be stored at `/registry/pods/default/my-pod`.

Etcd internal data structure is a B-tree, optimized for read operations and prefix scanning. This is crucial for Kubernetes, as controllers often list all objects of a certain type (e.g., all pods in a namespace).

### kube-scheduler

The `kube-scheduler` watches for newly created Pods that have no Node assigned, and selects a Node for them to run on.

The scheduling process happens in two phases:
1. **Filtering (Predicates)**: The scheduler filters out nodes that cannot run the pod. For example, if a pod requests 2GB of RAM, nodes with less than 2GB are filtered out. Other filters include node selectors, taints/tolerations, and port conflicts.
2. **Scoring (Priorities)**: The scheduler scores the remaining nodes based on various functions to find the optimal node. For example, it might prefer nodes that have the container image already downloaded, or it might try to spread pods of the same deployment across different nodes.

The node with the highest score is selected, and the scheduler creates a Binding object to assign the pod to the node.

### kube-controller-manager

The `kube-controller-manager` runs controller processes. Logically, each controller is a separate process, but to reduce complexity, they are all compiled into a single binary and run in a single process.

Some of the controllers included are:
- **Node controller**: Responsible for noticing and responding when nodes go down.
- **Job controller**: Watches for Job objects and creates Pods to run them to completion.
- **Endpoints controller**: Populates the Endpoints object (joins Services and Pods).
- **Service Account & Token controllers**: Create default accounts and API access tokens for new namespaces.

### cloud-controller-manager

The `cloud-controller-manager` embeds cloud-specific control logic. It allows you to link your cluster into your cloud provider's API, and separates out the components that interact with that cloud platform from components that only interact with your cluster.

Controllers included:
- **Node controller**: For checking the cloud provider to determine if a node has been deleted in the cloud after it stops responding.
- **Route controller**: For setting up routes in the underlying cloud infrastructure.
- **Service controller**: For creating, updating and deleting cloud provider load balancers.

## 3. Node Components Deep Dive

Node components run on every node, maintaining running pods and providing the Kubernetes runtime environment.

### kubelet

The `kubelet` is the primary "node agent" that runs on each node. It can register the node with the apiserver using one of: the hostname, a flag to override the hostname, or specific logic for a cloud provider.

The kubelet works in terms of a PodSpec. A PodSpec is a YAML or JSON object that describes a pod. The kubelet takes a set of PodSpecs that are provided through various mechanisms (primarily through the apiserver) and ensures that the containers described in those PodSpecs are running and healthy.

The kubelet does not manage containers which were not created by Kubernetes.

Key responsibilities:
- Pulling container images.
- Starting and stopping containers (via the Container Runtime Interface, CRI).
- Mounting volumes (via the Container Storage Interface, CSI).
- Executing liveness and readiness probes.
- Reporting node and pod status back to the apiserver.

### kube-proxy

`kube-proxy` is a network proxy that runs on each node in your cluster, implementing part of the Kubernetes Service concept.

`kube-proxy` maintains network rules on nodes. These network rules allow network communication to your Pods from network sessions inside or outside of your cluster.

It has several modes of operation:
1. **iptables mode (default)**: `kube-proxy` configures iptables rules to capture traffic to Service cluster IPs and ports, and redirects it to one of the Service's backend Pods. It chooses a backend randomly. It is highly scalable but can be slow to update if there are tens of thousands of services.
2. **IPVS mode**: `kube-proxy` uses IPVS (IP Virtual Server) for load balancing. IPVS is built into the Linux kernel and uses hash tables, making it much faster and more scalable than iptables for large clusters. It also supports various load balancing algorithms (round-robin, least connections, etc.).
3. **userspace mode (legacy)**: `kube-proxy` opens a port on the local node and forwards traffic to the backend pods. This is slow and rarely used anymore.

### Container Runtime Interface (CRI)

The CRI is a plugin interface which enables kubelet to use a wide variety of container runtimes, without the need to recompile.

Prior to CRI, Docker was deeply integrated into kubelet. With CRI, any runtime that implements the CRI gRPC API can be used. Common runtimes include:
- **containerd**: An industry-standard container runtime with an emphasis on simplicity, robustness and portability.
- **CRI-O**: A lightweight container runtime specifically designed for Kubernetes.

### Container Network Interface (CNI)

The CNI is a specification and libraries for writing plugins to configure network interfaces in Linux containers.

Kubernetes delegates the actual networking setup to CNI plugins. When a pod is scheduled on a node, the kubelet calls the CNI plugin to set up the network interface for the pod, assign it an IP address, and configure routes.

Common CNI plugins:
- **Calico**: Provides network policy enforcement and pure IP networking.
- **Flannel**: A simple and easy way to configure a layer 3 network fabric.
- **Cilium**: Uses eBPF for high-performance networking, observability, and security.

### Container Storage Interface (CSI)

The CSI is a standard for exposing arbitrary block and file storage systems to containerized workloads on Kubernetes.

Before CSI, storage drivers were "in-tree", meaning their code was part of the core Kubernetes repository. This made it difficult to add new storage providers and update existing ones.

With CSI, third-party storage providers can write and deploy plugins exposing new storage systems in Kubernetes without ever having to touch the core Kubernetes code.

## 4. The Complete Lifecycle of an API Request

Let's trace the lifecycle of a typical command: `kubectl apply -f pod.yaml`

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
spec:
  containers:
  - name: nginx
    image: nginx:latest
```

### Stage 1: The Client (kubectl)

1. `kubectl` reads the `pod.yaml` file.
2. It parses the YAML and converts it into a Go struct representing the Pod object.
3. It discovers the API server endpoint from the `kubeconfig` file.
4. It performs client-side validation (e.g., checking if required fields are present).
5. It negotiates the API version with the server.
6. It constructs an HTTP POST request to `/api/v1/namespaces/default/pods` and sends it to the apiserver.

### Stage 2: The API Server - Authentication and Authorization

1. The apiserver receives the HTTP request.
2. **Authentication**: The apiserver extracts the credentials from the request (e.g., client certificate, bearer token) and verifies the user's identity.
3. **Authorization**: The apiserver checks if the authenticated user has permission to create a Pod in the `default` namespace. This is typically done using Role-Based Access Control (RBAC).

### Stage 3: The API Server - Admission Control

1. **Mutating Admission Controllers**: The request passes through a chain of mutating admission webhooks. These can modify the Pod object. For example, a webhook might inject a sidecar container or add default resource limits.
2. **Object Schema Validation**: The apiserver validates the modified Pod object against the OpenAPI schema to ensure all fields are valid and correctly typed.
3. **Validating Admission Controllers**: The request passes through a chain of validating admission webhooks. These can reject the request based on custom policies (e.g., preventing the use of the `latest` tag).

### Stage 4: Etcd Storage

1. If all checks pass, the apiserver serializes the Pod object and writes it to etcd.
2. Etcd responds with success.
3. The apiserver returns an HTTP 201 Created response to `kubectl`.
At this point, the Pod exists in the cluster state, but it is not yet running.

### Stage 5: Scheduling

1. The `kube-scheduler`, which is constantly watching the apiserver for unassigned Pods, notices the new `nginx-pod`.
2. It runs its filtering and scoring algorithms to select the best node for the pod.
3. It creates a Binding object and sends it to the apiserver, effectively updating the Pod's `nodeName` field.

### Stage 6: The Kubelet

1. The `kubelet` on the selected node is watching the apiserver for Pods assigned to its node.
2. It sees the new `nginx-pod`.
3. It calls the CRI to pull the `nginx:latest` image if it's not already on the node.
4. It calls the CNI to set up the network namespace and IP address for the pod.
5. It calls the CSI to mount any required volumes.
6. It calls the CRI to start the container.
7. It reports the Pod's status (Running) back to the apiserver.

## 5. Kubeconfig and Cluster Access Management

The `kubeconfig` file is the standard way to configure access to Kubernetes clusters. By default, `kubectl` looks for a file named `config` in the `$HOME/.kube` directory.

### Anatomy of a Kubeconfig File

A kubeconfig file consists of three main sections: clusters, users, and contexts.

```yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: LS0tLS1...
    server: https://192.168.1.100:6443
  name: dev-cluster
users:
- name: dev-user
  user:
    client-certificate-data: LS0tLS1...
    client-key-data: LS0tLS1...
contexts:
- context:
    cluster: dev-cluster
    namespace: development
    user: dev-user
  name: dev-context
current-context: dev-context
```

- **clusters**: Defines the API server endpoints and certificate authorities for one or more clusters.
- **users**: Defines the credentials (certificates, tokens, passwords) for one or more users.
- **contexts**: Ties together a cluster, a user, and a default namespace.
- **current-context**: Specifies which context `kubectl` should use by default.

### Managing Kubeconfig Files

You can manage your kubeconfig file using the `kubectl config` commands.

```bash
# View the current configuration
kubectl config view

# View the current context
kubectl config current-context

# Use a specific context
kubectl config use-context dev-context

# Set the default namespace for the current context
kubectl config set-context --current --namespace=development
```

### Merging Kubeconfig Files

If you have multiple kubeconfig files, you can merge them using the `KUBECONFIG` environment variable.

```bash
export KUBECONFIG=~/.kube/config:~/.kube/dev-config:~/.kube/prod-config
kubectl config view --flatten > ~/.kube/merged-config
mv ~/.kube/merged-config ~/.kube/config
```
This is extremely useful when managing access to many different clusters across various environments.

### Service Accounts vs User Accounts

Kubernetes distinguishes between two types of accounts:
1. **User Accounts**: For humans. Kubernetes does not have objects representing user accounts. Users are typically managed externally (e.g., via OIDC, Active Directory, or client certificates).
2. **Service Accounts**: For processes running in pods. Kubernetes natively manages Service Account objects. They are used to give applications identity and permissions to interact with the Kubernetes API.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: default
```

When a pod is created, it is automatically assigned the `default` service account in its namespace unless a different one is specified.

## Conclusion

Understanding the architecture of Kubernetes is crucial for designing, deploying, and troubleshooting applications on the platform. By grasping the declarative philosophy, the roles of control plane and node components, and the lifecycle of API requests, you can leverage the full power of Kubernetes orchestration.

## Extended Content for In-Depth Understanding

### 6. Deep Dive into Etcd

Etcd's performance is fundamental to the stability of the entire Kubernetes cluster.
It relies heavily on storage speed and network latency between nodes.

When creating a production cluster, etcd should be deployed on dedicated nodes with SSDs.
If etcd is slow, API requests will time out, controllers will fail to reconcile state, and the cluster will become unresponsive.

Etcd uses the Raft protocol to achieve consensus. The cluster elects a leader, and all write requests go to the leader.
The leader then replicates the data to followers. A write is considered successful only when a majority (quorum) of nodes have acknowledged it.

### 7. Advanced Scheduler Configurations

The default scheduler is sufficient for most workloads, but you can customize it or run multiple schedulers.

**Taints and Tolerations:**
Taints are applied to nodes to repel certain pods.
Tolerations are applied to pods to allow them to schedule on tainted nodes.
This is useful for dedicating nodes to specific workloads (e.g., GPU nodes, or nodes for a specific team).

```yaml
# Tainting a node
kubectl taint nodes node1 key1=value1:NoSchedule
```

**Node Affinity:**
Node affinity is a more expressive way to constrain pods to specific nodes based on node labels.
It comes in two flavors: `requiredDuringSchedulingIgnoredDuringExecution` (hard constraint) and `preferredDuringSchedulingIgnoredDuringExecution` (soft constraint).

### 8. Custom Resource Definitions (CRDs)

CRDs allow you to extend the Kubernetes API with your own objects.
Once you create a CRD, the kube-apiserver will handle storing and validating instances of your custom resource.

To make CRDs useful, you need to write a custom controller (often called an Operator) that watches for changes to your custom resources and takes action.

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: crontabs.stable.example.com
spec:
  group: stable.example.com
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                cronSpec:
                  type: string
                image:
                  type: string
  scope: Namespaced
  names:
    plural: crontabs
    singular: crontab
    kind: CronTab
    shortNames:
    - ct
```

### 9. Operator Pattern

The Operator pattern combines CRDs and custom controllers to automate the management of complex, stateful applications (like databases or message queues) on Kubernetes.
Operators encode human operational knowledge into software.

An Operator watches the state of its associated CRDs and interacts with the Kubernetes API to reconcile the state of the application.
Tools like Kubebuilder and Operator SDK make it easier to develop Operators in Go.

### 10. Security Architecture

Kubernetes security operates at multiple layers:
1. **Code:** Image scanning, secure coding practices.
2. **Container:** Limiting privileges, setting resource quotas.
3. **Cluster:** RBAC, Network Policies, Pod Security Standards.
4. **Cloud/Corporate Datacenter:** Infrastructure security, network segmentation.

**Role-Based Access Control (RBAC):**
RBAC is the primary way to manage authorization in Kubernetes.
It uses four key objects:
- **Role**: Defines a set of permissions within a specific namespace.
- **ClusterRole**: Defines a set of permissions across the entire cluster.
- **RoleBinding**: Grants the permissions defined in a Role to a user or set of users within a namespace.
- **ClusterRoleBinding**: Grants the permissions defined in a ClusterRole to a user or set of users across the cluster.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""] # "" indicates the core API group
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

### 11. Networking Deep Dive

Kubernetes networking is governed by several core rules:
- All pods can communicate with all other pods without NAT.
- All nodes can communicate with all pods (and vice-versa) without NAT.
- The IP that a pod sees itself as is the same IP that others see it as.

The implementation of these rules is left to the CNI plugin.

**Services:**
Services provide a stable IP address and DNS name for a set of pods.
- **ClusterIP**: Exposes the service on an internal IP in the cluster.
- **NodePort**: Exposes the service on the same port of each selected Node's IP.
- **LoadBalancer**: Creates an external load balancer in the current cloud and assigns a fixed, external IP to the Service.
- **ExternalName**: Maps the service to a DNS name.

**Ingress:**
Ingress exposes HTTP and HTTPS routes from outside the cluster to services within the cluster.
Traffic routing is controlled by rules defined on the Ingress resource.
You need an Ingress Controller (like NGINX or Traefik) to implement the Ingress rules.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: minimal-ingress
spec:
  rules:
  - http:
      paths:
      - path: /testpath
        pathType: Prefix
        backend:
          service:
            name: test
            port:
              number: 80
```

### 12. Advanced Storage Concepts

Kubernetes provides powerful primitives for managing stateful applications.
Understanding Persistent Volumes (PVs) and Persistent Volume Claims (PVCs) is essential.

**Persistent Volumes (PV):**
A PV is a piece of storage in the cluster that has been provisioned by an administrator or dynamically provisioned using Storage Classes.
It is a resource in the cluster just like a node is a cluster resource.

**Persistent Volume Claims (PVC):**
A PVC is a request for storage by a user. It is similar to a Pod. Pods consume node resources and PVCs consume PV resources.
PVCs can request specific size and access modes (e.g., they can be mounted ReadWriteOnce, ReadOnlyMany or ReadWriteMany).

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myclaim
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Filesystem
  resources:
    requests:
      storage: 8Gi
  storageClassName: slow
```

**Storage Classes:**
A StorageClass provides a way for administrators to describe the "classes" of storage they offer.
Different classes might map to quality-of-service levels, or to backup policies, or to arbitrary policies determined by the cluster administrators.

### 13. Auto-scaling Mechanisms

Kubernetes provides three main types of auto-scaling:

1. **Horizontal Pod Autoscaler (HPA):**
   HPA automatically updates a workload resource (such as a Deployment or StatefulSet), with the aim of automatically scaling the workload to match demand.
   It relies on metrics, typically CPU or memory utilization, gathered from the metrics-server.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: php-apache
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

2. **Vertical Pod Autoscaler (VPA):**
   VPA automatically adjusts the CPU and memory reservations for your pods to help "right size" your applications.
   This can free up CPU and memory for other pods and helps you utilize your cluster more efficiently.

3. **Cluster Autoscaler:**
   The Cluster Autoscaler automatically adds or removes nodes in a cluster based on resource demands.
   If pods are failing to schedule due to lack of resources, it adds a node.
   If a node is underutilized for an extended period, and its pods can be placed elsewhere, it removes the node.

### 14. Network Policies

By default, pods are non-isolated; they accept traffic from any source.
NetworkPolicies allow you to specify how a pod is allowed to communicate with various network "entities".

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-network-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - ipBlock:
        cidr: 172.17.0.0/16
        except:
        - 172.17.1.0/24
    - namespaceSelector:
        matchLabels:
          project: myproject
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 6379
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.0.0/24
    ports:
    - protocol: TCP
      port: 5978
```

This policy isolates `role=db` pods in the default namespace, allowing them to receive traffic on port 6379 only from specific IP ranges, namespaces, or other pods.


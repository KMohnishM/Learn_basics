# Module 4: Container Orchestration (Kubernetes)

Docker Compose is great for running containers on a *single machine* (like your laptop). But what if your application goes viral and you need 50 copies of your API running across 10 different servers?

How do you manage them? If a server dies, who restarts the containers on a healthy server? How do you distribute network traffic evenly among them?

**You need an Orchestrator. You need Kubernetes (K8s).**

## What is Kubernetes?
Kubernetes is an open-source container orchestration platform originally developed by Google. It automates the deployment, scaling, and management of containerized applications.

### The Kubernetes Architecture
A Kubernetes Cluster consists of a set of worker machines, called **Nodes**, that run containerized applications. Every cluster has at least one worker node. The worker nodes are managed by the **Control Plane** (the master node).

1. **The Control Plane**: The brains. It makes global decisions (like scheduling).
   - **API Server**: The frontend of K8s. All your commands (`kubectl`) go here.
   - **etcd**: A highly available key-value store containing all cluster data/state.
   - **Scheduler**: Watches for newly created pods and assigns them to nodes.
   - **Controller Manager**: Runs background loops that watch the state of the cluster and make changes to drive the current state towards the desired state.

2. **Worker Nodes**: The brawn. They run your containers.
   - **Kubelet**: An agent that runs on each node and ensures containers are running in a Pod.
   - **Kube-Proxy**: Maintains network rules to allow communication to your Pods.

## Core Kubernetes Objects

You tell Kubernetes what you want by writing YAML manifests describing your "Desired State". Kubernetes works constantly to make the actual state match your desired state.

### 1. Pods
The smallest, most basic deployable object in K8s. A Pod represents a single instance of a running process in your cluster.
**Rule of thumb**: 1 Pod usually equals 1 Container (though a Pod *can* hold multiple tightly-coupled containers). 
You rarely create Pods directly; they are ephemeral. If they die, they die.

### 2. Deployments
You use a Deployment to tell Kubernetes: "I always want exactly 3 replicas of my Python API Pod running." 
If a node crashes and takes down 1 Pod, the Deployment Controller notices the current state (2 Pods) doesn't match the desired state (3 Pods), and spins up a new one on a healthy node.
Deployments also handle rolling updates (zero-downtime deployments of new versions).

### 3. Services
Because Pods are ephemeral, their IP addresses change constantly. A Service provides a stable IP address and DNS name for a set of Pods.
- **ClusterIP**: The default. Exposes the Service on an internal IP. Other Pods can reach it, but the outside world cannot.
- **NodePort**: Opens a specific port on every Worker Node and forwards traffic to the Service.
- **LoadBalancer**: Provisions an external load balancer (from AWS/GCP) to route traffic from the internet to your Service.

### 4. ConfigMaps & Secrets
You should never hardcode passwords or environment variables in your Docker images.
- **ConfigMap**: Stores non-confidential data (like `DEBUG=True`).
- **Secret**: Stores confidential data (like Database passwords) as base64-encoded strings. K8s injects them into your Pods as environment variables or files.

---

## Next Steps
In the `labs/` directory, we will write our first K8s Deployment and Service YAML manifests to deploy the Python API we built in Module 2!

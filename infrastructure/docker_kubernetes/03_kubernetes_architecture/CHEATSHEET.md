# Kubernetes Architecture Cheatsheet

## Control Plane Components

| Component | Role | Description |
| :--- | :--- | :--- |
| **kube-apiserver** | The Brain | Exposes the K8s API. Handles AuthN/AuthZ, Admission Control, and etcd communication. |
| **etcd** | The Memory | Highly available, strongly consistent key-value store for all cluster data. Uses Raft. |
| **kube-scheduler** | The Matchmaker | Assigns newly created Pods to Nodes based on filtering (predicates) and scoring (priorities). |
| **kube-controller-manager** | The Enforcer | Runs control loops (Node, ReplicaSet, Endpoints, etc.) to reconcile actual state to desired state. |
| **cloud-controller-manager** | The Cloud Liaison | Interacts with underlying cloud providers (AWS, GCP, Azure) for nodes, routing, and load balancing. |

## Node Components

| Component | Role | Description |
| :--- | :--- | :--- |
| **kubelet** | The Captain | Node agent. Ensures containers are running and healthy. Interacts with CRI, CNI, CSI. |
| **kube-proxy** | The Networker | Maintains network rules on nodes. Implements Services (iptables, IPVS). |
| **Container Runtime (CRI)** | The Engine | Software that runs containers (containerd, CRI-O, Docker Engine). |

## Core Interfaces

*   **CRI (Container Runtime Interface):** Plugin interface for kubelet to manage containers.
*   **CNI (Container Network Interface):** Plugin interface for pod networking (Calico, Flannel, Cilium).
*   **CSI (Container Storage Interface):** Standard for exposing storage to containers (EBS, Persistent Disks).

## API Request Pipeline

```ascii
Client Request -> AuthN -> AuthZ -> Mutating Admission -> Object Validation -> Validating Admission -> etcd
```

## Essential CLI Commands

### etcdctl (Interacting directly with etcd)

*   `ETCDCTL_API=3 etcdctl get / --prefix --keys-only` (List all keys)
*   `ETCDCTL_API=3 etcdctl endpoint status --write-out=table` (Check cluster health)
*   `ETCDCTL_API=3 etcdctl snapshot save snapshot.db` (Backup etcd)

### kubectl config (Managing Kubeconfig)

*   `kubectl config view` (View current merged configuration)
*   `kubectl config current-context` (Show current context)
*   `kubectl config get-contexts` (List all contexts)
*   `kubectl config use-context <name>` (Switch to a different context)
*   `kubectl config set-context --current --namespace=<ns>` (Set default namespace)

## Key Concepts

*   **Declarative vs Imperative:** State desired outcome (Declarative) vs specific steps (Imperative).
*   **Level-Triggered vs Edge-Triggered:** Act on current state (Level) vs act only on events (Edge). K8s relies on level-triggered logic for resilience.
*   **Control Loop:** `Observe -> Compare -> Reconcile`. Continually running to ensure Actual State = Desired State.

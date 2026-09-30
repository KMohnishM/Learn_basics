# Module 3: QnA

## 1. What is the fundamental difference between imperative and declarative systems in the context of Kubernetes?
The fundamental difference lies in how state is managed and maintained.
In an imperative system, you provide a sequence of specific commands to achieve a goal.
For instance, you might run a script that creates a container, maps a port, and starts a service.
If the system state changes unexpectedly, the imperative script might fail.
It could leave the system in an inconsistent or unknown state.
The next run of the script might not know how to recover without complex error handling.
In a declarative system like Kubernetes, you declare the desired end state.
You might state, "I want 3 instances of this container running at all times."
The system continuously monitors the actual state of the cluster.
It automatically takes action to reconcile the actual state with the desired state.
This continuous reconciliation loop makes declarative systems highly resilient to failures.
It prevents state drift and reduces the need for manual intervention.
They are constantly working to correct discrepancies automatically.

## 2. Explain the concept of a control loop in Kubernetes.
A control loop is a continuous, non-terminating process that regulates system state.
In Kubernetes, various components called "controllers" implement these control loops.
The core logic of a control loop involves three main steps.
First, it observes the current state of the system by watching the API server.
Second, it compares this actual state to the desired state specified by the user.
The desired state is typically stored in etcd as part of the object's Spec.
Third, it takes action to reconcile the two states if they differ.
For example, the ReplicaSet controller watches the number of running pods.
If the desired state is 3 replicas and only 2 are running, it detects this discrepancy.
It then requests the API server to create a new pod.
This continuous monitoring and reconciliation ensure high availability.
It provides the self-healing capabilities that make Kubernetes so robust.
The cluster constantly works towards the desired configuration autonomously.

## 3. Why does Kubernetes use level-triggered logic instead of edge-triggered logic?
Kubernetes uses level-triggered logic for maximum robustness and reliability.
In edge-triggered systems, actions are taken only in response to specific events or state changes.
If an event is missed due to network partitions, the system can remain out of sync.
Component crashes or bugs can also cause edge-triggered systems to fail silently.
Level-triggered systems, on the other hand, periodically re-evaluate the entire current state.
They compare this current state level against the desired state level.
Even if an event is completely missed, the next evaluation cycle will catch it.
It will detect the discrepancy and trigger the necessary reconciliation actions.
Kubernetes controllers do primarily react to events for efficiency and speed.
However, they also perform periodic resyncs to guarantee consistency.
This ensures that the system eventually converges on the desired state.
It makes Kubernetes highly resilient to temporary failures and missed notifications.
This combination provides both fast response times and long-term reliability.

## 4. Describe the role of the kube-apiserver.
The kube-apiserver is the central brain and primary front end of the Kubernetes control plane.
It exposes the Kubernetes REST API to users, administrators, and internal components.
It is the only component in the entire cluster that communicates directly with etcd.
All other components, including controllers and kubelets, communicate with etcd through it.
Its primary responsibilities include authenticating all incoming requests.
It then authorizes these requests based on defined policies, such as RBAC.
It validates the structure and content of objects against OpenAPI schemas.
It also mutates objects via admission controllers before persisting them.
Because it is completely stateless, it stores all its data in etcd.
This stateless nature allows it to be scaled horizontally for high availability.
Multiple instances can run simultaneously to handle the load of a large cluster.
It acts as the single source of truth and central communication hub.

## 5. What makes etcd crucial for a Kubernetes cluster?
etcd is a strongly consistent, distributed key-value store.
It serves as the single source of truth and the backing store for all Kubernetes cluster data.
It stores the configuration, state, and metadata of all objects in the entire cluster.
Its importance lies primarily in its strict reliability and consistency guarantees.
These guarantees are achieved through the implementation of the Raft consensus algorithm.
This ensures that even if a minority of nodes in the etcd cluster fail, data remains safe.
The data remains accessible and consistent across the remaining nodes.
Furthermore, etcd provides a powerful "watch" feature that Kubernetes relies on.
The kube-apiserver heavily utilizes this watch feature to monitor for changes.
When changes occur, etcd immediately pushes notifications to the apiserver.
This enables the fast, event-driven architecture that powers Kubernetes controllers.
Without etcd, the cluster would have no memory of its desired or actual state.

## 6. How does the kube-scheduler determine where a pod should run?
The kube-scheduler determines the optimal node for a pod using a two-step process.
This process consists of a filtering phase and a scoring phase.
During the filtering phase, it evaluates all available nodes against specific predicates.
These predicates check for hard constraints that must be satisfied.
For example, it checks if a node has sufficient CPU and memory resources.
It also checks for port conflicts, node selectors, and required taints/tolerations.
Nodes that fail any of these hard checks are immediately eliminated from consideration.
In the scoring phase, the remaining feasible nodes are ranked based on priority functions.
These functions evaluate soft constraints to find the absolute best node.
For instance, it prefers nodes that already have the required container images downloaded.
It might try to spread pods of the same deployment across different availability zones.
The node with the highest overall score is ultimately selected.
The scheduler then binds the pod to that specific node by updating the apiserver.

## 7. What is the kube-controller-manager and what does it do?
The kube-controller-manager is a daemon that embeds the core control loops of Kubernetes.
These control loops are known as controllers.
While logically each controller is a separate, independent process, they are bundled together.
They are compiled into a single binary and run as a single process to reduce complexity.
The controller-manager continuously monitors the state of the cluster through the kube-apiserver.
It takes corrective action when the actual state drifts from the desired state.
It runs various critical controllers, including the Node controller.
The Node controller is responsible for noticing and responding when nodes go down.
It also runs the Replication controller, which maintains the correct number of pod replicas.
The Endpoints controller joins services and pods together to enable routing.
The Service Account controller creates default accounts and tokens for new namespaces.
It is absolutely essential for maintaining the overall health and desired state of the cluster.

## 8. Explain the purpose of the cloud-controller-manager.
The cloud-controller-manager abstracts cloud-specific logic from the core Kubernetes control plane.
It allows cluster administrators to link their cluster into a specific cloud provider's API.
This includes cloud providers like AWS, Google Cloud, Azure, or DigitalOcean.
It cleanly separates the components that interact with the cloud platform from core components.
This ensures that the core Kubernetes code can evolve independently of various cloud platforms.
The cloud-controller-manager runs controllers that interact exclusively with the cloud infrastructure.
For instance, its Node controller checks the cloud provider to verify actual node deletion.
Its Route controller configures routes in the underlying cloud provider's network.
Its Service controller creates, updates, and deletes cloud provider load balancers.
This happens when LoadBalancer-type services are defined and requested in Kubernetes.
It is only needed if you are running Kubernetes in a public cloud environment.
It is typically not used in bare-metal, on-premises deployments.

## 9. What are the primary responsibilities of the kubelet?
The kubelet is the primary node agent that runs on every single node in a Kubernetes cluster.
Its main responsibility is to ensure that the containers described in PodSpecs are running.
It receives these PodSpecs primarily from the apiserver, but can also read local files.
It continuously ensures that the containers are healthy and operating as expected.
To start containers, it instructs the container runtime via the Container Runtime Interface (CRI).
It interacts with the Container Network Interface (CNI) to set up pod networking and IP addresses.
It interacts with the Container Storage Interface (CSI) to mount any required persistent storage volumes.
Furthermore, it continuously executes liveness, readiness, and startup probes defined in the PodSpec.
If a liveness probe fails, the kubelet automatically restarts the failed container.
It is also responsible for reporting the status of both the pods and the node itself.
It reports this vital health information back to the kube-apiserver on a regular basis.
This ensures the control plane always has an accurate view of the node's capacity and health.

## 10. Compare the different modes of kube-proxy.
kube-proxy is responsible for maintaining network rules on nodes to enable Service communication.
Its default and most common mode of operation is **iptables** mode.
In iptables mode, it creates rules to capture traffic destined for service IPs.
It then sequentially forwards that traffic to the appropriate backend pods.
While reliable, it can suffer performance degradation when managing tens of thousands of services.
The **IPVS (IP Virtual Server)** mode addresses these scalability and performance limitations.
IPVS uses kernel-level hash tables instead of sequential rule evaluation.
This offers significantly faster performance and much better scalability for large clusters.
IPVS also supports multiple sophisticated load-balancing algorithms natively.
These include least connections, source hashing, and shortest expected delay.
The legacy **userspace** mode is obsolete and rarely used in modern clusters.
It routes traffic through the kube-proxy process itself in user space.
This introduces significant latency and context-switching overhead, making it very slow.

## 11. What is the Container Runtime Interface (CRI) and why was it introduced?
The Container Runtime Interface (CRI) is a plugin interface introduced to decouple Kubernetes from specific runtimes.
It allows the kubelet to use various container runtimes without requiring recompilation of core code.
Initially, Kubernetes was tightly and directly coupled exclusively with the Docker Engine.
As alternative container runtimes emerged, maintaining these "in-tree" integrations became a heavy burden.
It became unsustainable for the core Kubernetes team to manage all these different integrations.
The CRI was introduced to provide a standard, stable gRPC API for managing containers and images.
By implementing the CRI, alternative runtimes like containerd and CRI-O can seamlessly integrate.
This decoupled architecture fosters rapid innovation in the container runtime ecosystem.
It allows users to choose the runtime that best fits their specific security and performance needs.
For example, users can choose runtimes specialized for enhanced isolation like Kata Containers.
It significantly reduces the maintenance burden on the core Kubernetes open-source project.
It ultimately led to the deprecation and removal of the direct Docker integration (dockershim).

## 12. Describe the role of admission controllers in the API request lifecycle.
Admission controllers are a critical security, governance, and policy mechanism within the kube-apiserver.
They intercept requests to the API server after the request has been authenticated and authorized.
However, they act before the object is actually persisted to the etcd database.
They are broadly divided into two distinct phases: mutating and validating.
**Mutating admission controllers** have the ability to modify incoming object requests.
For example, they might automatically inject a sidecar container, like Istio's Envoy proxy.
They can also enforce default resource requests and limits on a pod if none were specified.
**Validating admission controllers** inspect the request and can outright reject it.
They reject requests if they violate predefined cluster policies or organizational standards.
For instance, they can block the creation of pods that attempt to use the `latest` image tag.
They can also ensure that all created objects possess mandatory specific labels for billing.
They act as the final gatekeepers to ensure that all objects entering the cluster are compliant.

## 13. What happens between a Pod being saved to etcd and its containers starting?
After a Pod object is validated and successfully saved to etcd, a complex orchestration process begins.
First, the kube-scheduler detects the new, unassigned Pod by watching the apiserver.
It evaluates all available nodes, selects the best one, and creates a Binding object.
This Binding object updates the Pod's state to reflect its newly assigned node.
Next, the kubelet running on that specific node detects the newly assigned Pod.
The kubelet then orchestrates the intricate setup required before the container can run.
It calls the Container Storage Interface (CSI) plugin to attach and mount any required volumes.
It calls the Container Network Interface (CNI) plugin to allocate an IP address for the pod.
The CNI plugin also configures the pod's isolated network namespace.
Finally, the kubelet uses the Container Runtime Interface (CRI) to pull the necessary container images.
Once the images are pulled locally, it commands the CRI to actually start the containers.
The kubelet then updates the apiserver that the pod is now in the Running state.

## 14. What are the key components of a kubeconfig file?
A kubeconfig file is the standard YAML file used to configure access to Kubernetes clusters.
It is structured around three main, interrelated components: clusters, users, and contexts.
The **clusters** section defines the API server endpoint URLs for one or more clusters.
It also contains the certificate authority data required to securely connect to those specific clusters.
The **users** section contains the authentication credentials for interacting with the clusters.
These credentials can be client certificates, bearer tokens, or basic usernames and passwords.
They represent the different identities that can access the defined clusters.
The **contexts** section is the glue that ties these elements together into a usable profile.
A context explicitly combines a specific cluster, a specific user identity, and a default namespace.
By switching the `current-context` field in the kubeconfig, a developer can seamlessly transition.
They can move between interacting with a local development cluster using admin credentials.
And immediately switch to a remote production cluster using highly restricted credentials.

## 15. How do Service Accounts differ from User Accounts in Kubernetes?
The primary difference lies in who they are intended for and how they are managed by the system.
**User Accounts** are intended for human operators, administrators, or external automated systems.
Crucially, Kubernetes does not natively manage user accounts as internal API objects.
They are typically handled by external identity providers like Active Directory, OIDC, or cloud IAM.
Humans authenticate via certificates, tokens, or SSO proxies that the apiserver trusts.
**Service Accounts**, on the other hand, are intended for processes running within Pods inside the cluster.
Kubernetes natively creates and completely manages Service Account objects via the API.
When a pod is created, it is associated with a service account (defaulting to the 'default' account).
This provides the pod with a cryptographic identity and a secure token mounted into the container.
The application running in the pod can use this token to authenticate with the kube-apiserver.
It allows the pod to perform authorized actions, like reading secrets or listing other pods, based on RBAC.
Service accounts are bound to specific namespaces, whereas users are global.

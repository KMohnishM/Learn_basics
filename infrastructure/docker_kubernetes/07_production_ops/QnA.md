# Kubernetes Production Operations Q&A

## 1. Explain Resource requests vs limits (scheduling vs cgroup enforcement).
In Kubernetes, resource requests and limits are critical mechanisms for managing compute resources.
They are used for managing resources like CPU and memory, but they serve fundamentally different purposes.
A resource **request** represents the minimum amount of a resource that a container requires to operate normally.
This value is used exclusively by the Kubernetes scheduler during the pod placement phase.
The scheduler evaluates the total requests of all containers in a pod.
It only places the pod on a node that has enough unallocated capacity to satisfy those requests.
This ensures the pod has the resources it needs to start and run.
Conversely, a resource **limit** defines the absolute maximum amount of a resource that a container is permitted to consume.
Limits are not used for scheduling; instead, they are enforced at runtime by the Linux kernel's cgroup mechanisms.
If a container attempts to exceed its CPU limit, the kernel will throttle its execution.
This causes performance degradation but not an outright crash of the container.
However, if a container attempts to exceed its memory limit, the kernel's Out-Of-Memory (OOM) killer will intervene.
It will terminate the process to protect the stability of the host node.

## 2. What are QoS classes (Guaranteed, Burstable, BestEffort) and how do they affect OOM killer scoring?
Kubernetes automatically assigns a Quality of Service (QoS) class to every Pod.
This is based entirely on the configuration of its resource requests and limits.
This classification is vital for node stability because it dictates the eviction priority during severe resource pressure.
The **Guaranteed** class is assigned when every container in a pod has both memory and CPU requests and limits explicitly set.
Additionally, the requests must perfectly equal the limits.
These pods have the highest priority and the lowest `oom_score_adj`.
This means the kernel will only kill them as an absolute last resort.
The **Burstable** class applies when at least one container has a memory or CPU request specified, but not equal to the limit.
These pods have intermediate priority; they are allowed to burst up to their limits.
However, they will be killed if the node runs out of resources and no lower-priority pods exist.
The **BestEffort** class is assigned when no container in the pod has any requests or limits defined.
These pods have the lowest priority and the highest `oom_score_adj`.
In a resource starvation scenario, the node will indiscriminately terminate BestEffort pods first.

## 3. Detail CPU CFS throttling mechanics when a container exceeds its CPU limit.
When a container in Kubernetes is configured with a CPU limit, the kubelet enforces this restriction.
It uses the Linux kernel's Completely Fair Scheduler (CFS) quota mechanism via cgroups.
CPU is considered a compressible resource, meaning that exceeding the limit does not result in termination.
Instead, the CFS mechanism employs a time-based accounting system using two primary parameters.
These are `cpu.cfs_period_us` (the length of the accounting period, typically 100 milliseconds).
And `cpu.cfs_quota_us` (the amount of CPU time the container is allowed to use within that period).
When a container consumes its allocated quota within the current period, the kernel intervenes.
It forcibly pauses the container's execution, a process known as CPU throttling.
The container remains paused, unable to process requests or execute code, until the current period expires.
Once the next 100ms period begins, its quota is replenished and execution resumes.
From the application's perspective, this throttling manifests as severe latency spikes.
It results in slow response times and generally degraded performance due to freezing and thawing.

## 4. How does HPA v2 calculate the desired number of replicas mathematically?
The Horizontal Pod Autoscaler (HPA) automatically adjusts the number of replicas based on observed metrics.
In HPA v2, the autoscaler controller operates on a continuous control loop.
This loop typically runs every 15 seconds to evaluate the current state.
During each iteration, the controller queries the metrics API to retrieve the current value of the targeted metric.
The controller then uses a specific mathematical formula to calculate the desired number of replicas.
This is required to bring the metric back to the target value defined in the HPA configuration.
The core formula is: `desiredReplicas = ceil[currentReplicas * ( currentMetricValue / desiredMetricValue )]`.
For instance, if you have 2 replicas currently running, and the target CPU utilization is 50%.
If the current observed average CPU utilization is 100%, the calculation would proceed.
`ceil[2 * ( 100 / 50 )] = ceil[2 * 2] = 4`.
The controller determines that 4 replicas are needed to handle the load and issues a scale-up command.
The HPA also incorporates a tolerance factor (usually 10%) to prevent rapid, continuous scaling (thrashing).

## 5. How does KEDA enable event-driven autoscaling down to zero?
Kubernetes Event-driven Autoscaling (KEDA) is an open-source operator that significantly extends native HPA capabilities.
While HPA primarily scales based on internal cluster metrics like CPU and memory utilization, KEDA is different.
It is designed to scale workloads based on the volume of events originating from external systems.
These systems include Kafka topics, RabbitMQ queues, or AWS SQS queues.
KEDA operates by utilizing a concept called Scalers, which are adapters connecting to external systems.
The most critical architectural distinction of KEDA is its ability to scale workloads down to zero.
The native HPA cannot scale a deployment below one replica because it relies on the pods themselves to generate metrics.
KEDA circumvents this limitation by taking over the monitoring responsibility when the deployment has zero replicas.
It continuously polls the external event source independently.
When it detects incoming events (e.g., the queue length rises above zero), KEDA proactively acts.
It scales the deployment from zero to one replica.
Once the first pod is running, KEDA delegates the ongoing scaling responsibilities to the native HPA.

## 6. Contrast the architecture of Cluster Autoscaler with AWS Karpenter.
Both the Kubernetes Cluster Autoscaler (CA) and AWS Karpenter solve the problem of node-level autoscaling.
However, they employ fundamentally different architectural approaches to achieve this goal.
The traditional Cluster Autoscaler operates by monitoring the Kubernetes scheduler for pending pods.
When it detects un-schedulable pods, CA calculates whether adding a new node would satisfy requirements.
Crucially, CA relies heavily on the cloud provider's abstraction layers.
Specifically, Auto Scaling Groups (ASGs) in AWS or Managed Instance Groups (MIGs) in GCP.
This means you must pre-configure multiple ASGs with specific instance types to handle diverse workloads.
In contrast, Karpenter takes a more direct, intent-based approach that is more efficient.
It bypasses ASGs entirely and interacts directly with the cloud provider's compute API.
Karpenter observes the specific resource requests, node selectors, and affinities of pending pods.
It then dynamically provisions a node with the precise instance type, size, and architecture needed.
This dynamic, just-in-time provisioning leads to significantly faster scaling times and better bin-packing.

## 7. What are the risks of confusing startupProbe, livenessProbe, and readinessProbe?
Kubernetes utilizes probes to assess the health and readiness of containers, and misconfiguring them is dangerous.
The **startupProbe** is designed specifically for legacy or slow-starting applications.
If configured, it disables the other probes until the application successfully starts.
A major risk here is setting the failure threshold too low, causing premature termination.
If the application takes longer to initialize, the kubelet will repeatedly kill and restart it.
The **livenessProbe** is intended to detect unrecoverable states, like deadlocks, triggering a restart.
A common, catastrophic mistake is configuring a livenessProbe to check external dependencies (like a database).
If the database experiences a brief hiccup, the livenessProbe will fail for all pods.
This causes Kubernetes to ruthlessly restart every single application pod simultaneously, causing an outage.
The **readinessProbe** indicates if a container is ready to accept HTTP traffic from Services.
Confusing this with a livenessProbe means a completely frozen application might remain running indefinitely.
It will consume resources but remain hidden from the load balancer, requiring manual intervention.

## 8. Detail the Pod termination sequence and why the preStop hook is necessary.
When a Kubernetes Pod is deleted, the system initiates a strict, coordinated termination sequence.
First, the pod's status changes to `Terminating` in the API server.
Simultaneously, the endpoint controller removes the pod's IP address from all associated Services.
This ensures no new external traffic is routed to the dying pod from the load balancer.
Next, if a `preStop` hook is defined in the pod specification, it is executed synchronously.
This hook is absolutely necessary for achieving true zero-downtime deployments in complex environments.
It takes a few seconds for the endpoint removal update to propagate through the network components.
If the application shuts down immediately, inflight requests will be abruptly severed.
A simple `preStop` hook executing a `sleep 15` command artificially pauses the shutdown process.
This grants the network sufficient time to route traffic away from the pod.
Only after the hook completes does the kubelet send a `SIGTERM` signal to gracefully close connections.
If the application runs past the `terminationGracePeriodSeconds`, a `SIGKILL` is issued.

## 9. Explain nodeSelector vs nodeAffinity vs topologySpreadConstraints.
Kubernetes provides a spectrum of tools to control pod placement, ranging from simple to sophisticated.
The **nodeSelector** is the simplest mechanism, consisting of a basic key-value map.
The scheduler will only place the pod on a node that possesses labels exactly matching the map.
It is a hard requirement, but its expressiveness is limited to simple equality checks.
**nodeAffinity** offers a significantly more expressive syntax and supports a variety of operators.
It allows administrators to define both hard rules (`requiredDuringScheduling...`) that must be met.
And it allows soft rules (`preferredDuringScheduling...`) that the scheduler will attempt to honor.
Finally, **topologySpreadConstraints** address a different dimension: high availability across fault domains.
While affinity draws pods to specific nodes, spread constraints ensure even distribution.
They ensure a group of pods is distributed evenly across distinct failure domains, such as zones.
By defining a `maxSkew`, you instruct the scheduler to prevent any single zone from hosting too many replicas.
This ensures that the failure of a single data center zone does not result in total failure.

## 10. How do Taints and Tolerations work together for dedicated nodes?
Taints and tolerations are a complementary mechanism in Kubernetes designed to repel pods from nodes.
They ensure specific hardware is reserved for specific workloads and prevent unauthorized pods.
A **Taint** is an attribute applied to a Node; it acts as a repellent.
For example, an administrator might apply a taint to nodes equipped with expensive GPUs.
Once this taint is applied, the Kubernetes scheduler will absolutely refuse to schedule any standard pod onto that node.
The node is effectively quarantined from the general compute pool.
A **Toleration**, on the other hand, is an attribute applied to a Pod specification.
It acts as an exemption pass for the pod.
If a developer needs their application to run on those GPU nodes, they must configure a toleration.
The toleration must explicitly match the key, value, and effect of the node's taint.
When the scheduler evaluates the pod, it sees the toleration and recognizes the authorization.
It then schedules the pod onto the dedicated node, ensuring only explicitly authorized pods consume those resources.

## 11. Describe using podAntiAffinity for multi-AZ high availability.
To achieve robust High Availability (HA) in a Kubernetes cluster spanning multiple Availability Zones (AZs), careful scheduling is needed.
It is critical to ensure that multiple replicas of a critical application do not end up on the same physical node.
They must also not end up within the same AZ, as a localized hardware failure could take down the entire service.
**podAntiAffinity** is the scheduling mechanism used to explicitly prevent this co-location.
It allows you to instruct the scheduler that a pod should not be co-located with other specific pods.
For multi-AZ HA, you configure a `podAntiAffinity` rule targeting the application's own labels.
Critically, you set the `topologyKey` to a label representing the zone (e.g., `topology.kubernetes.io/zone`).
You can configure this as a hard requirement (`requiredDuringScheduling...`).
This forces the scheduler to place the replica in a different AZ, even if it means leaving the pod pending.
Alternatively, you can use a soft preference (`preferredDuringScheduling...`).
The scheduler will make a best-effort attempt to distribute the pods across zones but will compromise if necessary.
This prioritizes running the workload over strict physical separation if resources are tight.

## 12. How do PodDisruptionBudgets (PDB) protect availability during a node drain?
In a dynamic Kubernetes environment, nodes frequently require maintenance, such as kernel upgrades.
This requires evicting (draining) the running pods from the node, considered "voluntary disruptions."
Without safeguards, a script draining multiple nodes simultaneously could inadvertently evict all replicas.
This could cause a complete service outage for a critical application.
A **PodDisruptionBudget (PDB)** is a policy object designed to prevent exactly this scenario.
It acts as a safety valve, defining the minimum number of replicas that must be maintained.
Or it defines a maximum number of unavailable replicas during voluntary disruptions.
When a cluster administrator issues a `kubectl drain` command, the eviction API intercepts the request.
It consults any associated PDBs for the pods running on that node.
If evicting a pod would cause the number of available replicas to drop below the threshold, it acts.
The API will strictly reject the eviction request, and the drain process will block.
It will wait until a new replica has been scheduled and becomes fully ready on a different node.

## 13. Walk through a step-by-step node maintenance procedure using cordon and drain.
Performing maintenance on a Kubernetes node requires a careful, systematic approach.
This ensures that running workloads are safely relocated without disruption to the end user.
The process begins with the `kubectl cordon <node-name>` command.
Cordoning simply marks the target node as "unschedulable" in the Kubernetes API.
Existing pods continue to run perfectly fine, but the scheduler ignores this node for new pods.
This effectively stops the influx of new workloads onto the node undergoing maintenance.
The critical step is `kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data`.
The drain command systematically requests the eviction of every pod running on the node.
It inherently respects PodDisruptionBudgets (PDBs), meaning it will pause and wait if necessary.
The `--ignore-daemonsets` flag is necessary because DaemonSet pods cannot be evicted normally.
The `--delete-emptydir-data` flag explicitly acknowledges that any local, ephemeral data will be permanently lost.
Once the drain completes successfully, the node is completely empty of workload pods.
It is then safe to power down, reboot, or upgrade before using `uncordon` to return it to service.

## 14. Contrast LimitRange and ResourceQuota for multi-tenancy controls.
In a multi-tenant Kubernetes cluster, multiple teams share the same infrastructure.
Administrators must implement strict guardrails to prevent a single team from consuming all available resources.
This is achieved through a combination of `LimitRange` and `ResourceQuota` objects, operating at different levels.
A **LimitRange** enforces policies at the individual Pod or Container level within a specific namespace.
It establishes minimum and maximum constraints for resource requests and limits.
For example, it prohibits any single container from requesting more than 2 CPUs.
Crucially, a LimitRange can also define default requests and limits, automatically injecting them into pods.
This ensures no pod runs unbounded if a developer forgets to specify resources.
In contrast, a **ResourceQuota** operates at the aggregate level for an entire namespace.
It acts as a strict budget, capping the total sum of resources that all pods within that namespace can consume.
For example, it stipulates that the "development" namespace cannot consume more than 20 CPUs in total.
Together, LimitRange dictates the size of individual workloads, while ResourceQuota limits the total footprint.

## 15. Provide examples of Prometheus PromQL alert queries for Kubernetes.
Prometheus is the standard monitoring solution for Kubernetes, utilizing PromQL for alerting.
A fundamental alert is detecting pods caught in a continuous restart loop.
The query `rate(kube_pod_container_status_restarts_total[5m]) > 0` analyzes the rate of container restarts.
If the rate is greater than zero, it indicates a pod is repeatedly crashing into a `CrashLoopBackOff` state.
Monitoring CPU throttling is essential for performance tuning and capacity planning.
The query `rate(container_cpu_cfs_throttled_seconds_total[5m]) / rate(container_cpu_usage_seconds_total[5m]) > 0.2` calculates this.
It calculates the ratio of throttled time to actual usage time; an alert indicates severe constraint.
To protect node stability, monitoring disk pressure is absolutely critical for the cluster.
The query `(node_filesystem_avail_bytes{fstype!~"tmpfs|ramfs"} / node_filesystem_size_bytes{fstype!~"tmpfs|ramfs"}) * 100 < 15` is used.
It calculates the percentage of available disk space, alerting if it drops below 15%.
Finally, monitoring node health is paramount to ensure capacity.
The query `kube_node_status_condition{condition="Ready", status="true"} == 0` instantly identifies issues.
It signals a potential hardware failure or network partition requiring immediate administrative intervention.

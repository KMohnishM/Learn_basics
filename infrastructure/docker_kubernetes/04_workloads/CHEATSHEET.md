# Kubernetes Workloads Cheatsheet

## Workloads Decision Matrix

| Workload Type | Use Case | Statefulness | Identity | Update Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Deployment** | Web servers, APIs, Microservices | Stateless | Ephemeral (Random) | RollingUpdate, Recreate |
| **StatefulSet** | Databases, Message Queues (Kafka) | Stateful | Stable (Ordinal) | RollingUpdate, OnDelete |
| **DaemonSet** | Logs, Monitoring, CNI, Storage Daemons | Stateless/Host-bound | Host-mapped | RollingUpdate, OnDelete |
| **Job** | Batch processing, data migrations | N/A | Ephemeral | N/A (Runs to completion) |
| **CronJob** | Scheduled backups, periodic reports | N/A | Ephemeral | N/A (Triggers Jobs) |

---

## Deployment Rolling Update Formula

During a `RollingUpdate`, the control plane uses these formulas to manage Pod counts:

**Max Pods Alive** = `Replicas` + `maxSurge`
**Min Pods Available** = `Replicas` - `maxUnavailable`

*Example with Replicas=10, maxSurge=20% (2), maxUnavailable=20% (2):*
- Max Pods during rollout: 12
- Min Pods available to serve traffic: 8

---

## StatefulSet Architecture Diagram

```text
+-------------------------------------------------------------+
|                     Headless Service                        |
|                     (clusterIP: None)                       |
+--------+--------------------+--------------------+----------+
         |                    |                    |
         v                    v                    v
+------------------+ +------------------+ +------------------+
| Pod: db-0        | | Pod: db-1        | | Pod: db-2        |
| IP: 10.1.0.5     | | IP: 10.1.0.9     | | IP: 10.2.0.4     |
| Identity: Stable | | Identity: Stable | | Identity: Stable |
+--------+---------+ +--------+---------+ +--------+---------+
         |                    |                    |
         v                    v                    v
+------------------+ +------------------+ +------------------+
| PVC: data-db-0   | | PVC: data-db-1   | | PVC: data-db-2   |
| Bound to db-0    | | Bound to db-1    | | Bound to db-2    |
+--------+---------+ +--------+---------+ +--------+---------+
         |                    |                    |
         v                    v                    v
+------------------+ +------------------+ +------------------+
| PV: vol-xxxxx    | | PV: vol-yyyyy    | | PV: vol-zzzzz    |
| (AWS EBS, etc)   | | (AWS EBS, etc)   | | (AWS EBS, etc)   |
+------------------+ +------------------+ +------------------+
```
*Note: Scaling up creates db-0, then db-1, then db-2. Scaling down removes db-2, then db-1, then db-0.*

---

## Essential `kubectl rollout` Commands

Manage the lifecycle of Deployments, StatefulSets, and DaemonSets.

| Command | Action |
| :--- | :--- |
| `kubectl rollout status deploy/my-app` | Watch the real-time progress of an ongoing rollout. |
| `kubectl rollout history deploy/my-app` | View previous revisions and their change causes. |
| `kubectl rollout history deploy/my-app --revision=3` | View detailed information about a specific past revision. |
| `kubectl rollout undo deploy/my-app` | Instantly rollback to the immediate previous revision. |
| `kubectl rollout undo deploy/my-app --to-revision=2` | Rollback to a specific historical revision. |
| `kubectl rollout pause deploy/my-app` | Pause an active rollout (useful for canary testing). |
| `kubectl rollout resume deploy/my-app` | Resume a previously paused rollout. |
| `kubectl rollout restart deploy/my-app` | Force a rolling restart of all Pods without changing the image. |

---

## Pod Container Types Quick Reference

- **App Container**: The main workload. Runs continuously. `restartPolicy` applies.
- **Init Container**: Runs strictly before app containers. Must complete sequentially.
- **Sidecar Container** (1.28+): Native `restartPolicy: Always` inside `initContainers`. Starts early, terminates automatically when main apps finish (fixes Job hanging).
- **Ephemeral Container**: Inserted dynamically into a running Pod for live debugging (`kubectl debug`).

## Resource Constraints Quick Guide

- **Requests**: What the Pod is guaranteed. The Scheduler uses this to find a Node with enough capacity.
- **Limits**: The hard ceiling. If CPU hits limit, the container is throttled. If RAM hits limit, the container is OOMKilled.

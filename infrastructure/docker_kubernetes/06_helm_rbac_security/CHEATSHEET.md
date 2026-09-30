# Kubernetes Helm, RBAC & Security Cheatsheet

## RBAC Manifests

### Role & RoleBinding (Namespace Scoped)
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: app-ns
  name: app-reader
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-app
  namespace: app-ns
subjects:
- kind: User
  name: jane
roleRef:
  kind: Role
  name: app-reader
  apiGroup: rbac.authorization.k8s.io
```

### ClusterRole & ClusterRoleBinding (Cluster Scoped)
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-node-reader
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-nodes
subjects:
- kind: Group
  name: devops-team
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-node-reader
  apiGroup: rbac.authorization.k8s.io
```

## Pod Security Standards (PSS) Matrix

| Profile    | Description | Primary Use Case | Key Restrictions |
|------------|-------------|------------------|------------------|
| **Privileged** | Unrestricted, highest privilege. | System agents, CNI plugins. | None |
| **Baseline**   | Prevents known escalations. | General workloads, easy migration. | No hostNetwork, no privileged mode, restricted HostPath. |
| **Restricted** | Heavily restricted, best practices. | Production applications, untrusted code. | Must runAsNonRoot, drop ALL capabilities, require seccomp RuntimeDefault. |

### Enforcing via Namespace Labels
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: strict-env
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

## Helm Go Template Cheat Sheet

| Function / Syntax | Description | Example |
|-------------------|-------------|---------|
| `{{ .Values.key }}` | Access a value from `values.yaml` | `replicas: {{ .Values.replicaCount }}` |
| `{{- ... }}` | Remove leading whitespace | `{{- if .Values.ingress.enabled }}` |
| `{{ ... -}}` | Remove trailing whitespace | `{{ .Values.name -}}` |
| `\| default "val"` | Provide a default fallback value | `{{ .Values.tag \| default "latest" }}` |
| `\| quote` | Wrap the value in double quotes | `image: {{ .Values.image \| quote }}` |
| `\| nindent 4` | Prepend newline and indent by N spaces | `{{- include "labels" . \| nindent 4 }}` |
| `if/else` | Conditional logic | `{{- if .Values.enabled }} true {{- else }} false {{- end }}` |
| `with` | Scopes the current context | `{{- with .Values.image }} {{ .repository }} {{- end }}` |
| `range` | Iterate over lists/maps | `{{- range $key, $val := .Values.env }} ... {{- end }}` |

## External Secrets Operator (ESO) Architecture

```text
+----------------------+         +-----------------------+         +-----------------------+
|  External Provider   |         | Kubernetes Cluster    |         |  Application Pod      |
|  (AWS, Vault, GCP)   |         |                       |         |                       |
+----------+-----------+         |                       |         |                       |
           |                     |                       |         |                       |
           | API Auth            |                       |         |                       |
           | (IAM, Token)        |                       |         |                       |
           v                     |                       |         |                       |
+----------+-----------+         |  +-----------------+  |         |                       |
|   SecretStore        | <----------| External Secret |  |         |                       |
| (Connection details) |         |  | (Defines what   |  |         |                       |
+----------------------+         |  |  to sync)       |  |         |                       |
                                 |  +--------+--------+  |         |                       |
                                 |           |           |         |                       |
                                 |           | ESO syncs |         |                       |
                                 |           v           |         |                       |
                                 |  +-----------------+  | Mounts  |  +-----------------+  |
                                 |  | Standard K8s    |----------->|  | Container       |  |
                                 |  | Secret          |  |         |  |                 |  |
                                 |  +-----------------+  |         |  +-----------------+  |
                                 +-----------------------+         +-----------------------+
```

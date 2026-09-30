# Kubernetes Security and Helm Q&A

## 1. Explain Role vs ClusterRole and when to use each.
In Kubernetes Role-Based Access Control, both Role and ClusterRole are used to define a set of permissions, but they differ fundamentally in their scope.
A Role is a namespaced object, meaning it is strictly bound to a specific namespace.
It can only grant access to resources within that namespace, such as Pods, Services, or ConfigMaps.
You would use a Role when you want to restrict a user or application to operate solely within an isolated environment.
For example, a specific development or testing namespace.
Conversely, a ClusterRole is a non-namespaced object that applies cluster-wide.
It is essential for granting access to cluster-scoped resources like Nodes, PersistentVolumes, and Namespaces themselves.
Additionally, a ClusterRole can grant access to non-resource endpoints such as `/healthz`.
Another powerful feature of a ClusterRole is that it can be used to grant permissions across all namespaces simultaneously.
For example, allowing a security auditor to view all pods across the entire cluster.
Choosing between them depends entirely on whether the resources you are securing are cluster-level or namespace-level.
It also depends on how broadly you need the permissions applied across the cluster.

## 2. How does a RoleBinding interact with a ClusterRole in a single namespace?
While a ClusterRole defines cluster-wide permissions, the way it is bound determines its actual scope in practice.
If you bind a ClusterRole using a ClusterRoleBinding, the permissions apply globally across all namespaces.
However, if you bind a ClusterRole using a standard RoleBinding, the permissions defined in the ClusterRole are restricted.
They are restricted to only the namespace where the RoleBinding is created.
This specific interaction is incredibly useful for defining common, reusable roles without duplicating configuration.
For example, cluster administrators can define a single `admin` or `edit` ClusterRole containing standard permissions.
Instead of creating identical Roles in every single namespace, they can create a RoleBinding in a target namespace.
This RoleBinding references the global ClusterRole.
The subjects in that RoleBinding will then have the `admin` permissions, but only within that specific namespace.
This pattern significantly reduces administrative overhead.
It also ensures consistency across namespace role definitions throughout the cluster.

## 3. What is the security risk of ServiceAccount token automounting and how do you mitigate it?
By default, Kubernetes automatically provisions a ServiceAccount named `default` in every namespace.
More critically, the kubelet automatically mounts the API token for this ServiceAccount into every container.
This occurs in every container running in that namespace at the path `/var/run/secrets/kubernetes.io/serviceaccount`.
This behavior poses a significant security risk because many applications do not actually need to communicate with the API.
If an attacker compromises a container running a vulnerable application, they can extract this automounted token.
They can then use it to authenticate against the Kubernetes API server.
Depending on the RBAC permissions bound to that ServiceAccount, the attacker could perform malicious actions.
They could escalate privileges or access sensitive information within the cluster.
To mitigate this risk, the best practice is to disable automatic token mounting.
This is done by setting the `automountServiceAccountToken: false` directive.
This can be configured globally on the ServiceAccount object itself.
Or, it can be done on a per-Pod basis within the Pod specification, ensuring only required workloads receive a token.

## 4. How can administrators audit RBAC permissions using kubectl auth can-i?
The `kubectl auth can-i` command is a built-in utility that allows administrators to query the API authorization layer directly.
It evaluates RBAC policies and returns a simple "yes" or "no" answer.
This answer indicates whether a specific subject can perform a specific action on a specific resource.
Administrators can use it to verify their own permissions.
For example, running `kubectl auth can-i create deployments` to check if they have deployment creation rights.
More importantly, administrators can impersonate other users or ServiceAccounts using the `--as` flag.
This allows them to verify exactly what a different entity can do without needing their credentials.
For example, `kubectl auth can-i list secrets --namespace default --as system:serviceaccount:default:my-app-sa`.
This will definitively state whether that ServiceAccount has the ability to read secrets.
This tool is invaluable for troubleshooting "Forbidden" errors.
It is also essential for auditing existing RBAC policies.
Finally, it helps verify that new roles and bindings follow the principle of least privilege before deploying them.

## 5. Why were PodSecurityPolicies (PSP) removed and how do Pod Security Standards (PSS) replace them?
PodSecurityPolicies (PSP) were a complex, cluster-level resource used to control security-sensitive aspects of Pod specification.
They were deprecated in Kubernetes v1.21 and fully removed in v1.25.
This happened because they were fundamentally flawed in their design.
PSPs were extremely difficult to deploy and manage correctly, often leading to unintended lockouts.
The authorization model was confusing and hard to debug.
It relied on the user or ServiceAccount creating the Pod having the `use` verb on the PSP.
In their place, Kubernetes introduced Pod Security Standards (PSS) and the Pod Security Admission (PSA) controller.
PSS is not an API resource, but rather a set of clear, predefined, standard security profiles.
These profiles (Privileged, Baseline, Restricted) are defined in documentation.
The PSA controller enforces these standards.
Instead of writing complex policy objects, administrators simply apply labels to Namespaces.
These labels instruct the PSA controller which PSS profile to enforce, audit, or warn on, significantly simplifying administration.

## 6. Describe the three Pod Security Standards (PSS) profiles (Privileged, Baseline, Restricted).
The Pod Security Standards (PSS) define three distinct profiles that represent different levels of restriction.
The **Privileged** profile is entirely unrestricted and allows for known privilege escalations.
It allows deep access to the host node and is intended only for highly trusted system components.
It should never be used for standard application workloads.
The **Baseline** profile provides a minimally restrictive policy that prevents known privilege escalations.
However, it allows the default, unconfigured Pod settings to run.
It serves as a good starting point for migrating legacy applications that lack explicit security contexts.
It blocks egregious violations like running privileged containers without breaking typical workloads.
The **Restricted** profile is the most secure and enforces current Kubernetes security best practices.
It requires explicit security configurations, such as forcing containers to run as non-root users.
It also mandates dropping all Linux capabilities and requiring secure seccomp profiles.
This profile is strongly recommended for all new and standard application workloads to minimize the attack surface.

## 7. How do you configure Pod Security Admission namespace labeling for enforcement and auditing?
Pod Security Admission (PSA) is configured by applying specific labels to a Kubernetes Namespace.
The labels dictate the mode of operation and the specific Pod Security Standard (PSS) profile to apply.
The three available modes are `enforce`, `audit`, and `warn`.
The `enforce` mode outright rejects the creation of a Pod that violates the policy.
The `audit` mode allows the Pod to be created but logs an event in the API server audit log.
The `warn` mode allows the Pod but returns a warning message directly to the client creating it.
A typical robust configuration uses a combination of these modes for comprehensive security.
For example, you might label a namespace with `pod-security.kubernetes.io/enforce: baseline`.
This strictly blocks obvious privilege escalations.
Simultaneously, you might set `pod-security.kubernetes.io/warn: restricted` and `pod-security.kubernetes.io/audit: restricted`.
This configuration provides immediate security by enforcing the baseline.
It also proactively warns developers and audits logs for workloads failing the higher standard.

## 8. Explain the architecture of a Helm 3 Chart and the purpose of its core files.
A Helm 3 Chart is a standardized directory structure containing all necessary files for a Kubernetes application.
The architecture separates package metadata from configurable parameters and templated YAML manifests.
At the root of the directory is the `Chart.yaml` file.
This file contains crucial metadata such as the chart's name, version, description, and dependencies.
The `values.yaml` file serves as the default configuration file.
It defines variables like image repositories, resource limits, and service types.
Users can override these default values during the installation process.
The `templates/` directory is the core of the chart, containing Go template files.
These templates define Kubernetes resources like deployments, services, and ingresses.
When Helm evaluates the chart, it combines these templates with the values to generate valid YAML manifests.
Additionally, the `templates/_helpers.tpl` file stores reusable template snippets.
The `crds/` directory is designated for Custom Resource Definitions, which are installed prior to templates.

## 9. How does Go template syntax handle whitespace, specifically using the nindent function?
Helm utilizes the Go templating engine to dynamically construct YAML manifests.
A significant challenge in generating YAML is that it is highly sensitive to indentation and whitespace.
Go templates generate output exactly as formatted in the template file, including newlines and spaces.
This can often lead to invalid YAML if not managed carefully.
To address this, Helm provides specific syntax and functions like the dash character.
The dash character inside template brackets, `{{-` or `-}}`, strips all leading or trailing whitespace.
Even more critical is the `nindent` function.
When injecting blocks of YAML configuration from the `values.yaml` file, alignment is essential.
The injected text must be aligned perfectly with the surrounding template.
The `nindent` function takes an integer argument and prepends a newline followed by that exact number of spaces.
This applies to every line of the piped input.
For example, `{{- toYaml .Values.resources | nindent 12 }}` ensures perfect alignment.
It guarantees structural validity in the final output by starting on a new line and indenting precisely.

## 10. What are Helm Hooks and how are they used for database migrations?
Helm Hooks are a mechanism that allows you to intervene at specific points in a release's lifecycle.
Instead of simply creating resources when a chart is installed, hooks provide custom execution control.
They let you dictate that certain resources, typically Kubernetes Jobs, should be executed at specific times.
This could be before or after the main installation, upgrade, or deletion phases.
This is achieved by adding specific annotations, such as `helm.sh/hook: pre-install`, to a resource's metadata.
A primary and crucial use case for Helm Hooks is executing database migrations.
When deploying a new version of an application, the database schema often needs updating first.
By defining a Job with a `pre-install` or `pre-upgrade` hook, Helm will deploy that Job first.
It will then monitor the Job and completely pause the deployment of the rest of the chart.
Once the database migration Job finishes successfully, Helm proceeds to deploy the updated application.
This ensures that the application always connects to a schema that matches its codebase.

## 11. Why is Base64 encoding insufficient for security in native Kubernetes Secrets?
A dangerous and widespread misconception is that native Kubernetes Secret objects provide cryptographic security.
When you create a Secret and define data, Kubernetes requires those values to be Base64 encoded.
However, Base64 is strictly an encoding format designed to represent binary data in an ASCII string.
It is not an encryption algorithm and provides no confidentiality whatsoever.
It uses no cryptographic keys and involves no mathematical security.
It can be instantly and trivially reversed by anyone using standard command-line tools like `base64 --decode`.
Consequently, if a malicious actor gains read access to the Secret object via the Kubernetes API, they have the data.
Or, if they gain access to the raw YAML manifest file containing the Secret, they immediately have the plaintext password.
Relying on Base64 encoding for security provides zero protection.
True security requires robust Role-Based Access Control to restrict who can read the Secret object.
It must also be combined with encryption at rest within the etcd database and external key management.

## 12. How do you configure etcd encryption at rest with a KMS provider?
By default, the Kubernetes API server stores all cluster state in plain text within the backend `etcd` database.
If an attacker gains access to the underlying storage volumes of the control plane nodes, they can extract secrets.
Or if they steal an etcd backup file, they can extract all cluster secrets.
To prevent this, administrators must configure encryption at rest.
This is accomplished by providing an `EncryptionConfiguration` file to the `kube-apiserver` process.
This file dictates which resources (specifically `secrets`) should be encrypted before being written to etcd.
A production-grade setup integrates with a Key Management Service (KMS) provider.
Examples include AWS KMS, Google Cloud KMS, or HashiCorp Vault.
In this setup, the `EncryptionConfiguration` points to a KMS plugin socket.
When a user creates a Secret, the API server generates a unique data encryption key (DEK) to encrypt it.
It sends the DEK to the external KMS to be encrypted with a master key (KEK).
It then stores the encrypted secret alongside the encrypted DEK in etcd.

## 13. Describe the Bitnami Sealed Secrets GitOps workflow using the kubeseal CLI.
In a modern GitOps methodology, the entire desired state of the cluster is stored in a Git repository.
Committing standard, Base64-encoded Kubernetes Secret YAML files to Git is a severe security violation.
Bitnami Sealed Secrets addresses this by employing asymmetric encryption to create a workflow safe for Git.
The architecture consists of an in-cluster controller and a client-side CLI tool called `kubeseal`.
The controller generates an asymmetric key pair, keeping the private key secure within the cluster.
It publishes the public key for developers to use.
Developers write standard Kubernetes Secret manifests locally.
Instead of committing them, they pipe them through the `kubeseal` CLI tool.
This tool uses the public key to encrypt the sensitive values.
The output is a `SealedSecret` Custom Resource containing mathematically secure, encrypted payloads.
This `SealedSecret` file can be safely committed to the public or internal Git repository.
When deployed, the in-cluster controller decrypts it and dynamically generates the standard Kubernetes Secret.

## 14. Explain the architecture of the External Secrets Operator (ESO) and its core resources.
Enterprise environments typically rely on centralized, external secret management systems.
Examples include AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault.
The External Secrets Operator (ESO) bridges the gap between these external vaults and the Kubernetes ecosystem.
Its architecture relies on a controller that continuously monitors custom resources to synchronize secrets.
The workflow involves two primary Custom Resources.
First, the administrator defines a `SecretStore` (or a cluster-wide `ClusterSecretStore`).
This configures the connection details and authentication mechanisms required to access the external provider.
Second, the developer creates an `ExternalSecret` resource.
This object acts as a blueprint, specifying exactly which secret to fetch from the configured `SecretStore`.
It defines how those values should be mapped into a resulting, native Kubernetes `Secret`.
The ESO controller continuously polls the external provider.
If the value changes upstream, it automatically updates the Kubernetes Secret.
This enables seamless, automated secret rotation without application downtime.

## 15. How do you design a least-privilege CI/CD pipeline security model using RBAC?
Securing a CI/CD pipeline interacting with a Kubernetes cluster demands strict adherence to the principle of least privilege.
The pipeline should never be granted cluster admin rights.
Instead, the architecture should utilize granular Role-Based Access Control (RBAC).
This should be focused on the specific actions required for deployment.
The first step is to create a dedicated `ServiceAccount` specifically for the CI/CD system.
Next, you construct a `Role` that defines the absolute minimum permissions required.
A deployment pipeline typically only needs verbs like `get`, `list`, `create`, `update`, and `patch`.
It only needs these on resources such as `deployments`, `services`, `configmaps`, and `secrets`.
It should not have permissions to delete resources entirely unless explicitly required.
It certainly should not have permissions to modify RBAC rules or access cluster-scoped resources like nodes.
Finally, a `RoleBinding` binds this restricted `Role` to the CI/CD `ServiceAccount`.
The CI/CD system authenticates to the cluster using the token associated with this specific ServiceAccount.
By scoping permissions strictly, the blast radius of a compromised CI/CD pipeline is severely constrained.

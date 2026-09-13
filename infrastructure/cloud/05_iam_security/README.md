# Module 5: IAM and Security

## IAM (Identity and Access Management) Core Concepts
IAM allows you to manage access to AWS services and resources securely. It is globally scoped.

### IAM Principals
*   **Users:** Long-term credentials (password, access key). Best practice: Do NOT use IAM users for applications. Only use them for human administrative access, and strictly enforce MFA.
*   **Groups:** A collection of IAM users. Groups cannot be nested (you cannot put a group inside a group). You assign policies to groups to manage permissions at scale.
*   **Roles:** Entities with temporary credentials generated via the Security Token Service (STS). Roles are assumed by:
    *   AWS Services (e.g., EC2, Lambda).
    *   Federated users (e.g., login via corporate Active Directory).
    *   Cross-account access (Account A assuming a role in Account B).

### IAM Policies
Policies define permissions and are written in JSON.
*   **Identity-based policies:** Attached to IAM users, groups, or roles.
    *   *AWS managed:* Pre-defined by AWS (e.g., `AdministratorAccess`, `AmazonS3ReadOnlyAccess`).
    *   *Customer managed:* Created by you for fine-grained control.
    *   *Inline:* Embedded directly into a single user/group/role (discouraged; hard to manage).
*   **Resource-based policies:** Attached directly to an AWS resource.
    *   Examples: S3 Bucket Policies, SQS Queue Policies, KMS Key Policies, Lambda Resource Policies.
    *   *Crucial use case:* Granting cross-account access without requiring the caller to assume a role.
*   **Permission Boundaries:** An advanced feature that sets the *maximum* permissions an IAM entity can have. It does not grant permissions on its own; it restricts them. Used to safely delegate IAM management to developers.
*   **Service Control Policies (SCPs):** Managed via AWS Organizations. They restrict what member accounts CAN do. They apply to all principals in the account, *including the root user*. They do NOT grant permissions.
*   **Session Policies:** Passed dynamically when assuming a role programmatically via CLI/SDK to further restrict the session.

### Policy Evaluation Logic
1.  **Explicit Deny:** By default, all requests are implicitly denied. If there is an *explicit Deny* anywhere (SCP, Resource Policy, Identity Policy, Boundary), the request is blocked immediately. **Explicit Deny ALWAYS wins.**
2.  If no explicit deny, AWS checks all applicable policies.
3.  **Allow:** If any policy grants an explicit Allow (and no boundary/SCP restricts it), the request is allowed.

### Policy Structure
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-public-bucket/*",
      "Condition": {
        "IpAddress": {"aws:SourceIp": "203.0.113.0/24"}
      }
    }
  ]
}
```
*   **Condition Keys:** `aws:RequestedRegion`, `aws:MultiFactorAuthPresent`, `s3:prefix`, `aws:CurrentTime`.

### IAM Roles in Depth
*   **EC2 Instance Profile:** A container for an IAM role that you attach to an EC2 instance. The EC2 metadata service (IMDS) automatically rotates the temporary credentials. **Never hardcode AWS keys on an EC2 instance.**
*   **Lambda Execution Role:** Grants the Lambda function permission to access AWS services (e.g., read from DynamoDB, write logs to CloudWatch).
*   **Cross-Account Roles:** 
    1. Account A creates a Role and a Trust Policy allowing Account B's ID to assume it. 
    2. Account B attaches an Identity Policy to its user allowing `sts:AssumeRole` on Account A's role.
*   **AssumeRole with MFA:** You can add a condition to a Trust Policy demanding `aws:MultiFactorAuthPresent: true` for highly sensitive roles.

### STS (Security Token Service)
*   **AssumeRole:** Returns a set of temporary security credentials (access key ID, secret access key, and security token) valid for 15 mins to 12 hours.
*   **AssumeRoleWithWebIdentity:** Used for federation with OIDC providers (Google, Facebook, Auth0).
*   **AssumeRoleWithSAML:** Used for enterprise SSO (Active Directory via ADFS, Okta).

---

## AWS Organizations and SSO
*   **AWS Organizations:** Allows you to centrally manage billing, control access, compliance, and security across multiple AWS accounts. Contains a Management account and Member accounts.
*   **Organizational Units (OUs):** Logical groupings of accounts (e.g., `Prod-OU`, `Dev-OU`).
*   **SCPs:** Applied at the Root, OU, or Account level. Common patterns: Deny leaving the organization, deny launching EC2 in expensive regions, require MFA for specific actions.
*   **IAM Identity Center (SSO):** The recommended way to manage workforce access. Centralizes login across all AWS accounts and integrates with external IdPs (Okta, Azure AD, Google Workspace).

---

## Secrets Management

Never hardcode database passwords or API keys in code or AMIs.

### AWS Secrets Manager
*   Stores secrets securely.
*   **Automatic Rotation:** Deeply integrated with RDS/Aurora. It uses a Lambda function to automatically connect to the DB and rotate the password on a schedule (e.g., every 30 days).
*   Costs $0.40 per secret per month + API call costs.

### AWS Systems Manager (SSM) Parameter Store
*   Stores configuration data and secrets.
*   Hierarchical naming (e.g., `/prod/app1/db-password`).
*   **SecureString:** Values are encrypted via KMS.
*   Standard parameters are **FREE**. Advanced parameters cost money.
*   **Difference:** Parameter Store does NOT support automatic built-in rotation (you have to build it yourself using EventBridge and Lambda).

---

## KMS (Key Management Service)
Managed service to create and control cryptographic keys.

### Customer Master Keys (CMKs)
*   **AWS Managed Keys:** Created by AWS services (e.g., `aws/s3`, `aws/rds`). Free. AWS rotates them automatically every year. You cannot change the rotation policy or the key policy.
*   **Customer Managed Keys:** You create these. Costs $1/month/key. You define the key policy, and you can enable automatic rotation (every 1 year) or rotate manually.

### Envelope Encryption
KMS is designed to encrypt small amounts of data (up to 4KB). For large data (like a 10GB S3 file), AWS uses Envelope Encryption:
1.  KMS generates a Data Key.
2.  The plaintext data is encrypted locally using the plaintext Data Key.
3.  The plaintext Data Key is discarded. The *encrypted* Data Key is stored alongside the encrypted data.
4.  To decrypt: KMS decrypts the Data Key using the CMK, and the app uses the plaintext Data Key to decrypt the data.
*   *Benefit:* The CMK never leaves KMS, and KMS doesn't have to handle gigabytes of data transfer.

### Key Policies vs IAM Policies
*   A KMS key **must** have a Key Policy.
*   An IAM policy granting `kms:Decrypt` is **NOT sufficient** on its own unless the KMS Key Policy explicitly delegates access to the account's IAM policies (`"Principal": {"AWS": "arn:aws:iam::111122223333:root"}`).

### S3 Encryption Options (SSE)
*   **SSE-S3:** AWS manages the data keys and master keys. (AES-256).
*   **SSE-KMS:** Uses a KMS CMK. Provides an audit trail in CloudTrail for who used the key. Allows enforcing role-based access control.
*   **SSE-C:** Customer Provided Key. AWS does not store the key; you must provide it with every HTTP request.
*   **DSSE-KMS:** Dual-layer server-side encryption.

---

## AWS CloudTrail
Governance, compliance, and operational auditing. Records all API calls made in your account (who, what, when, from where).

*   **Management Events:** Control plane operations (e.g., `CreateBucket`, `RunInstances`, `AttachRolePolicy`). Logged by default, 90-day history is free.
*   **Data Events:** Data plane operations (e.g., S3 `GetObject`, Lambda `Invoke`). High volume. **Not logged by default.** You must configure and pay extra for them.
*   **Trails:** Deliver log files to an S3 bucket (and optionally CloudWatch Logs/EventBridge) for long-term retention.
*   **Multi-Region Trail:** Recommended best practice. Creates one trail that logs events from all regions to a single S3 bucket.
*   **Log File Integrity Validation:** Creates a SHA-256 hash chain of log files. If a hacker alters a log file in S3 to cover their tracks, the validation will fail and alert you.
*   **CloudTrail Lake:** A managed data store that lets you run SQL-based queries across your CloudTrail logs without needing Athena.

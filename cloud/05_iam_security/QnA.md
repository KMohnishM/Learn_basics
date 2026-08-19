# QnA: IAM and Security

1. **What is the IAM policy evaluation logic? What always takes precedence?**
   AWS evaluates all applicable policies (Identity-based, Resource-based, SCPs, Permission Boundaries). By default, all access is implicitly denied. The evaluation engine looks for an explicit `Deny`. If an explicit `Deny` is found in *any* policy, the request is immediately blocked. **An explicit Deny always takes precedence over any explicit Allow.**

2. **What is the difference between an IAM Role and an IAM User? Why should applications use roles not users?**
   An IAM User represents a specific person or service and has long-term credentials (password, static access keys). An IAM Role is an entity that does not have long-term credentials; instead, it provides temporary, auto-rotating credentials via STS. Applications (like EC2 or Lambda) should use roles because embedding long-term static access keys in code or config files is a massive security risk.

3. **What is a Permission Boundary and when would you use it?**
   A Permission Boundary is an advanced IAM feature that uses a managed policy to set the *maximum* permissions an IAM entity (user/role) can possess. It does not grant permissions. You use it to safely delegate IAM management. For example, you can allow a developer to create new IAM roles for their Lambda functions, but apply a Permission Boundary to ensure those new roles can never be granted Administrator access.

4. **What is the difference between SCPs and IAM policies? Can SCPs grant permissions?**
   IAM policies are attached to users/roles and grant or deny specific actions. Service Control Policies (SCPs) are applied at the AWS Organizations level (to accounts or OUs) and act as a filter or guardrail. **SCPs cannot grant permissions.** Even if an IAM policy grants `AdministratorAccess`, if an SCP denies `s3:*`, the user will be blocked from accessing S3.

5. **How does cross-account access work in IAM? Walk through the steps.**
   Assuming Account A needs to access a bucket in Account B:
   1. In Account B, create an IAM Role with a Trust Policy specifying Account A's ARN as the Principal allowed to `sts:AssumeRole`.
   2. Attach a permissions policy to that Role in Account B allowing S3 access.
   3. In Account A, attach a policy to the IAM User/Role allowing `sts:AssumeRole` targeting the ARN of the Role in Account B.
   4. The user in Account A calls `AssumeRole`, receives temporary credentials, and uses them to access the bucket.

6. **What is the difference between Secrets Manager and SSM Parameter Store? When would you choose each?**
   Both store secrets securely. Choose **Secrets Manager** when you need automated, built-in credential rotation (especially for RDS/Aurora) and are willing to pay $0.40 per secret/month. Choose **SSM Parameter Store** (Standard) when you want a free service for storing configuration data and secrets (SecureString via KMS), and you don't mind writing custom Lambda functions if rotation is required.

7. **Explain envelope encryption in KMS. Why is it used instead of encrypting everything directly with KMS?**
   KMS APIs are designed to encrypt tiny amounts of data (up to 4KB) and have rate limits. Encrypting a 10GB file directly through the KMS API would be slow and expensive. Envelope encryption solves this: KMS generates a plaintext Data Key and an encrypted Data Key. The application uses the plaintext Data Key to encrypt the 10GB file locally at high speed, throws away the plaintext key, and stores the encrypted Data Key alongside the ciphertext file.

8. **What is the difference between SSE-S3, SSE-KMS, and SSE-C for S3 object encryption?**
   *   **SSE-S3:** AWS manages both the data keys and the master keys transparently. Free.
   *   **SSE-KMS:** Uses a Customer Master Key (CMK) in KMS. Provides strict IAM control over who can use the key and logs every usage in CloudTrail. Costs money per KMS API call.
   *   **SSE-C:** Customer provides their own encryption key in the HTTP header of every request. AWS encrypts/decrypts the data in memory and immediately discards the key.

9. **What is CloudTrail and what is the difference between management events and data events?**
   CloudTrail records API activity in your AWS account. 
   *   **Management events** (Control Plane) log actions that modify resources, like configuring security groups or creating buckets. These are logged by default. 
   *   **Data events** (Data Plane) log high-volume data operations within a resource, like S3 `GetObject` or Lambda `Invoke`. These are not logged by default and incur significant additional charges.

10. **What is IAM Identity Center (SSO) and what problem does it solve?**
    IAM Identity Center replaces the need to create individual IAM Users in every AWS account. It solves the problem of decentralized identity management by providing a single portal for users to log in (using corporate credentials via SAML/OIDC) and access all assigned AWS accounts and business applications with temporary credentials.

11. **What is AWS Organizations and how do SCPs work with OUs?**
    AWS Organizations centrally manages multiple AWS accounts. Accounts are grouped into Organizational Units (OUs). Service Control Policies (SCPs) apply restrictions. If you apply an SCP denying `ec2:RunInstances` to a "Dev" OU, all AWS accounts inside that OU inherit the restriction, meaning no user or role in those accounts can launch an EC2 instance, regardless of their local IAM policies.

12. **How would you detect if someone is using root account credentials in your AWS account?**
    The root account should never be used for daily tasks. To detect its use, you would configure an Amazon EventBridge rule that listens for AWS CloudTrail events where the `userIdentity.type` is `Root`. This rule would trigger an SNS topic to immediately send high-priority SMS and email alerts to the security team.

13. **What is an EC2 Instance Profile and why is it better than storing access keys on EC2?**
    An Instance Profile is a container for an IAM role attached to an EC2 instance. Storing static IAM access keys (`~/.aws/credentials`) on an EC2 instance is highly dangerous because if the instance is compromised, the keys are stolen and remain valid permanently. An Instance Profile uses the Instance Metadata Service (IMDS) to provide temporary, automatically rotating credentials, heavily reducing the blast radius of a compromise.

14. **What is AssumeRoleWithWebIdentity used for? Give a practical example.**
    It is used for web identity federation. Instead of creating IAM users for mobile app users, the mobile app authenticates with a third-party Identity Provider (IdP) like Google, Facebook, or Auth0. The app receives an OIDC token, passes it to AWS STS via `AssumeRoleWithWebIdentity`, and receives temporary AWS credentials allowing the app to read/write directly to DynamoDB or S3.

15. **How would you implement least privilege for a Lambda function that reads from one S3 bucket and writes to DynamoDB?**
    Create a specific IAM Role for the Lambda function. Attach an inline or customer-managed policy that explicitly allows `s3:GetObject` with the Resource set strictly to `arn:aws:s3:::my-input-bucket/*`. Add a second statement allowing `dynamodb:PutItem` with the Resource set strictly to `arn:aws:dynamodb:REGION:ACCOUNT:table/my-output-table`. Do not use wildcards (`*`) for actions or resources.

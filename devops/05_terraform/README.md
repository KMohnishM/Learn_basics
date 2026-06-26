# Module 5: Infrastructure as Code (Terraform)

So far, we have automated the building of our application (Docker), the testing of it (CI/CD), and the orchestrating of it (Kubernetes).
But where does that Kubernetes cluster actually run? Where do the databases live?

Historically, "Operations" people would log into the AWS Console, click "Create EC2 Instance", click "Create Database", type in some names, and click Save. 

This is called **ClickOps**. It is terrible.
If the region goes down, nobody remembers exactly which checkboxes they clicked to rebuild it. It cannot be version-controlled, reviewed, or audited.

**Enter Infrastructure as Code (IaC).**

## What is Terraform?
Terraform (created by HashiCorp) is the industry standard for IaC. It allows you to define your cloud infrastructure (servers, networks, databases) in text files, commit them to Git, and apply them systematically.

## Imperative vs. Declarative
- **Imperative (Bash scripts)**: You tell the computer *how* to do something. ("Create a server. Wait 5 minutes. Check if it's there. If not, retry..."). This is brittle.
- **Declarative (Terraform)**: You tell the computer *what* you want. ("I want 3 AWS EC2 instances."). Terraform figures out the "how". If you already have 2 instances running, and you apply the code, Terraform doesn't create 3 new ones—it creates exactly 1 new one to reach your desired state of 3.

## Terraform Architecture

### 1. Providers
Terraform itself doesn't know how to talk to AWS, GCP, or Azure. It uses **Providers** (plugins). You declare which provider you need (e.g., `hashicorp/aws`), and Terraform downloads the plugin that translates your code into AWS API calls.

### 2. State (`terraform.tfstate`)
This is the most critical concept in Terraform.
When Terraform creates your 3 servers, it saves their actual Cloud IDs in a JSON file called the **State File**. 
Next time you run Terraform, it compares your `.tf` code against the State File to see what changed.
**Warning:** In a team environment, you must store this State file in a remote, locked location (like an AWS S3 bucket) so two developers don't overwrite it simultaneously.

## Core Concepts in HCL (HashiCorp Configuration Language)

### Blocks
Terraform code is written in blocks.
```hcl
# This tells Terraform to create an actual piece of infrastructure
resource "aws_instance" "web_server" {
  ami           = "ami-123456"
  instance_type = "t2.micro"
}
```

### Variables & Outputs
- **Variables (`variable`)**: Make your code reusable. Instead of hardcoding `"t2.micro"`, you use `var.instance_type`.
- **Outputs (`output`)**: When Terraform finishes, it can print useful information to the console, like the Public IP address of the server it just created.

## The Terraform Workflow
1. `terraform init`: Initializes the directory, downloads the Provider plugins.
2. `terraform plan`: Does a dry-run. Shows you exactly what it *will* create/modify/delete without actually doing it.
3. `terraform apply`: Executes the plan and provisions the infrastructure.
4. `terraform destroy`: Tears down everything defined in the state file.

---

## Next Steps
In the `labs/` directory, we have a `main.tf` file that provisions an AWS VPC, Security Group, and EC2 instance.

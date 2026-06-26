# Module 5 Exercise: Provisioning Cloud Storage

In the labs, we provisioned a virtual machine (EC2) using Terraform. 
Another very common task for a DevOps engineer is provisioning cloud storage for the application to save files (like user-uploaded images).

In AWS, this is done using **S3 (Simple Storage Service)**.

## The Challenge

Your task is to write the Terraform code (`main.tf`) to create an S3 bucket.

**Requirements:**
1. Define the `aws` provider in the `us-east-1` region.
2. Create an `aws_s3_bucket` resource. Give it a unique name (S3 bucket names must be globally unique across all of AWS, so add some random numbers to the end, e.g., `my-devops-app-bucket-987123`).
3. Add a tag to the bucket: `Environment = "Dev"`.

*Bonus Challenge:* 
Can you figure out how to output the bucket's Amazon Resource Name (ARN) after it is created? (Check the Terraform documentation for `aws_s3_bucket` to see what attributes it exports!)

Good luck! Check the `solution/` folder when you are done.

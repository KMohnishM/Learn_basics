provider "aws" {
  region = "us-east-1"
}

# The main S3 Bucket Resource
resource "aws_s3_bucket" "app_storage" {
  # Change this to something unique!
  bucket = "my-devops-app-bucket-987123"

  tags = {
    Environment = "Dev"
    ManagedBy   = "Terraform"
  }
}

# Bonus: Output the ARN
output "bucket_arn" {
  value       = aws_s3_bucket.app_storage.arn
  description = "The ARN of the newly created S3 bucket"
}

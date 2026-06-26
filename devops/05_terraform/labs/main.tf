# 1. Define the Provider
# We are telling Terraform we want to use AWS, and we want to deploy in the us-east-1 region.
provider "aws" {
  region = "us-east-1"
}

# 2. Variables
# This allows us to easily change the instance type without hunting through the code
variable "instance_type" {
  description = "The type of EC2 instance to run"
  type        = string
  default     = "t2.micro" # Free tier!
}

# 3. Security Group Resource
# This acts as a virtual firewall for our server
resource "aws_security_group" "web_sg" {
  name        = "allow_web_traffic"
  description = "Allow inbound HTTP and SSH"

  # Inbound rules
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow from anywhere
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Warning: In production, limit SSH to your VPN's IP!
  }

  # Outbound rules (allow server to reach the internet to download updates)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 4. EC2 Instance Resource
# This is the actual virtual machine
resource "aws_instance" "web_server" {
  # Ubuntu 22.04 AMI in us-east-1
  ami           = "ami-053b0d53c279acc90" 
  instance_type = var.instance_type
  
  # Attach the security group we created above!
  # Notice we reference the resource by its type and name: aws_security_group.web_sg.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  # Tag the server so we can find it in the AWS Console
  tags = {
    Name = "DevOps-Lab-WebServer"
  }
}

# 5. Output
# Once Terraform finishes, print the public IP so we can SSH into it
output "server_public_ip" {
  value       = aws_instance.web_server.public_ip
  description = "The public IP address of the web server"
}

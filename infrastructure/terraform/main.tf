provider "aws" {
  region = "us-east-1"
}

resource "aws_security_group" "volatria_sg" {
  name        = "volatria_security_group"
  description = "Allow inbound web traffic"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "volatria_node" {
  ami           = "ami-0c7217cdde317cfec" # Amazon Linux 2 AMI
  instance_type = "t3.medium"
  security_groups = [aws_security_group.volatria_sg.name]

  tags = {
    Name = "VolatriaQuantPlatformNode"
  }
}

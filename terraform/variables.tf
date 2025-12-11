variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "urlshort"
}
variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}
variable "db_password" {
  description = "RDS master password"
  sensitive   = true
  type        = string
}
variable "db_username" {
  description = "Username for RDS"
  type        = string
  default     = "urlshort_user"
}
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "urlshortener"
}
variable "secret_key" {
  description = "JWT secret key for url-shortener app"
  type        = string
  sensitive   = true
}
variable "aws_access_key_id" {
  description = "AWS access key credentials"
  type        = string
  sensitive   = true
}
variable "aws_secret_access_key" {
  description = "AWS secret access key credential"
  type        = string
  sensitive   = true
}
variable "key_name" {
  description = "EC2 key pair name"
  type        = string
  default     = "urlshortener-key"
}
variable "github_repo" {
  description = "Github project repo URL"
  type        = string
  default     = "https://github.com/odysian/url-shortener.git"
}
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}
variable "allowed_ssh_cidr" {
  description = "SSH from anywhere(dev)"
  type        = string
  default     = "0.0.0.0/0"
}

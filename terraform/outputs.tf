output "database_endpoint" {
  description = "DNS endpoing for RDS instance"
  value       = aws_db_instance.postgres.endpoint
}
output "redis_endpoint" {
  description = "Endpoint for ElastiCache cluster"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
}
output "ec2_ip" {
  description = "IP address for EC2 instance"
  value       = data.aws_eip.static.public_ip
}
output "api_url" {
  description = "URL to access the URL shortener API"
  value       = "http://${data.aws_eip.static.public_ip}:8000"
}
output "api_docs_url" {
  description = "API documentation"
  value       = "http://${data.aws_eip.static.public_ip}:8000/docs"
}
output "ssh_command" {
  description = "SSH into EC2"
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ec2-user@${data.aws_eip.static.public_ip}"
}
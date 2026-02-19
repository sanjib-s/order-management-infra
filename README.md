
# Order Management Infrastructure (AWS CDK)

This repository contains the infrastructure-as-code (IaC) implementation for the Order Management demo solution using AWS CDK (Python).

The solution demonstrates modern API design patterns for application workloads, including secure private connectivity and separation of read and write responsibilities. Secure, scalable API-driven backend architecture supporting:

- GET → Read order details
- POST → Create order via microservice and persist to DynamoDB

---
##  Use Case: Order Management 

GET /orders/{orderId}
Read-optimized path:
API Gateway → Lambda → DynamoDB
Fast, stateless, scalable


POST /orders
Write-processing path:

API Gateway → Lambda → Internal ALB → EKS
EKS applies business logic
Lambda writes final order to DynamoDB


##  Architecture Overview

The solution demonstrates:

- Amazon API Gateway (HTTP API)
- AWS Lambda (inside private subnets)
- Amazon EKS (Order Orchestrator microservice) - EKS Setup is outside of the repo CDK stack
- Internal Application Load Balancer (Ingress) - is outside of the repo CDK stack
- Amazon DynamoDB
- AWS Systems Manager Parameter Store (SSM) - Using existing SSM Store
- Amazon Cognito (optional auth layer)
- VPC Endpoints (Private-only connectivity) is outside of the repo CDK stack

---

##  Use Case

**eCommerce Order Processing**

### GET /orders/{orderId}
- Lambda reads order details from DynamoDB
- Optimized for fast, stateless reads

### POST /orders
- Lambda calls EKS microservice via internal ALB
- Microservice generates order details
- Lambda writes order to DynamoDB

---

## Private Architecture Design

- Lambda runs in private subnets
- No NAT required (VPC endpoints used)
- DynamoDB accessed via Gateway Endpoint
- SSM accessed via Interface Endpoint
- Internal ALB exposes EKS service
- API Gateway acts as controlled entry point

---



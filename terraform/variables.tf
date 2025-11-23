# Variables for Azure UEMS Infrastructure

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "uems"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US 2"
}

variable "aks_node_count" {
  description = "Initial number of nodes in the AKS cluster"
  type        = number
  default     = 1  # Optimized for Azure Free Tier - use 1 node
}

variable "aks_node_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_B1s"  # Optimized for Azure Free Tier (~$7.59/month)
  # Options: B1s ($7.59/mo), B2s ($30/mo), B2ms ($60/mo)
}

variable "aks_kubernetes_version" {
  description = "Kubernetes version for AKS"
  type        = string
  default     = "1.33.2"
}

variable "acr_sku" {
  description = "SKU for Azure Container Registry"
  type        = string
  default     = "Basic"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "UEMS"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}

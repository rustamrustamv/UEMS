# Terraform configuration for UEMS Azure Infrastructure

terraform {
  required_version = ">= 1.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Uncomment and configure for remote state
  # backend "azurerm" {
  #   resource_group_name  = "terraform-state-rg"
  #   storage_account_name = "terraformstateXXXX"
  #   container_name       = "tfstate"
  #   key                  = "uems.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Random suffix for globally unique names
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# =============================================================================
# Resource Group
# =============================================================================

resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
  tags     = var.tags
}

# =============================================================================
# Azure Container Registry (ACR)
# =============================================================================

resource "azurerm_container_registry" "acr" {
  name                = "acr${var.project_name}${var.environment}${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku
  admin_enabled       = true  # Enable admin for simplified access (disable in production)

  tags = var.tags
}

# =============================================================================
# Azure Kubernetes Service (AKS)
# =============================================================================

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "aks-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "${var.project_name}-${var.environment}"
  kubernetes_version  = var.aks_kubernetes_version

  # Free tier for control plane
  sku_tier = "Free"

  # Default node pool
  default_node_pool {
    name                = "default"
    node_count          = var.aks_node_count
    vm_size             = var.aks_node_vm_size
    os_disk_size_gb     = 30
    type                = "VirtualMachineScaleSets"

    # Auto-scaling disabled for cost optimization (Azure Free Tier)
    # Enable if you need auto-scaling: set to true and uncomment min/max
    enable_auto_scaling = false
    # min_count           = 1
    # max_count           = 4

    # Network settings
    vnet_subnet_id = null  # Uses kubenet networking

    tags = var.tags
  }

  # System-assigned managed identity
  identity {
    type = "SystemAssigned"
  }

  # Network profile
  network_profile {
    network_plugin    = "kubenet"
    load_balancer_sku = "standard"
    network_policy    = "calico"
  }

  # Enable HTTP application routing (for development/testing)
  http_application_routing_enabled = false

  # Monitoring
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.aks.id
  }

  tags = var.tags

  depends_on = [
    azurerm_resource_group.main
  ]
}

# =============================================================================
# Log Analytics Workspace for AKS Monitoring
# =============================================================================

resource "azurerm_log_analytics_workspace" "aks" {
  name                = "law-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30  # Reduced from 30 for cost optimization (Azure Free Tier)
  daily_quota_gb      = 1  # Limit to 1GB/day to stay within 5GB/month free tier

  tags = var.tags
}

# =============================================================================
# Role Assignment: Grant AKS access to pull from ACR
# =============================================================================

resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.acr.id
  skip_service_principal_aad_check = true
}

# =============================================================================
# Outputs
# =============================================================================

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "aks_cluster_fqdn" {
  description = "FQDN of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.fqdn
}

output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = azurerm_container_registry.acr.name
}

output "acr_login_server" {
  description = "Login server for ACR"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_admin_username" {
  description = "Admin username for ACR"
  value       = azurerm_container_registry.acr.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "Admin password for ACR"
  value       = azurerm_container_registry.acr.admin_password
  sensitive   = true
}

output "get_aks_credentials_command" {
  description = "Command to get AKS credentials"
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_kubernetes_cluster.aks.name}"
}

output "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID for monitoring"
  value       = azurerm_log_analytics_workspace.aks.id
}

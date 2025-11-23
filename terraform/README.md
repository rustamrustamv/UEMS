# UEMS Terraform Infrastructure

This directory contains Terraform code to provision Azure infrastructure for the University Education Management System.

## Resources Provisioned

1. **Azure Resource Group** - Container for all resources
2. **Azure Container Registry (ACR)** - For storing Docker images
3. **Azure Kubernetes Service (AKS)** - Kubernetes cluster (Free tier control plane)
4. **Log Analytics Workspace** - For AKS monitoring and logs
5. **IAM Role Assignment** - Grants AKS permission to pull images from ACR

## Prerequisites

1. **Azure CLI** installed and configured
   ```bash
   az login
   az account set --subscription "your-subscription-id"
   ```

2. **Terraform** installed (>= 1.0)
   ```bash
   terraform version
   ```

3. **Azure subscription** with appropriate permissions

## Usage

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Configure Variables

Copy the example variables file and customize:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Plan Infrastructure

Review what Terraform will create:

```bash
terraform plan
```

### 4. Apply Infrastructure

Create the infrastructure:

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 5. Get Outputs

After successful apply, retrieve important outputs:

```bash
# Get all outputs
terraform output

# Get AKS credentials
terraform output -raw get_aks_credentials_command
az aks get-credentials --resource-group rg-uems-prod --name aks-uems-prod
```

### 6. Verify AKS Access

```bash
kubectl get nodes
kubectl get namespaces
```

## Accessing ACR

Get ACR credentials:

```bash
# Get ACR login server
terraform output acr_login_server

# Get ACR admin credentials (for CI/CD)
terraform output acr_admin_username
terraform output -raw acr_admin_password

# Login to ACR
az acr login --name $(terraform output -raw acr_name)
```

## Cost Considerations

- **AKS Control Plane**: Free tier ($0/month)
- **AKS Nodes**: 2 x Standard_B2s VMs (~$30/month each)
- **ACR Basic**: ~$5/month
- **Log Analytics**: Pay-per-GB ingested (~$2-10/month depending on usage)

**Estimated Total**: ~$65-70/month

### Cost Optimization Tips

1. **Reduce node count**: Set `aks_node_count = 1` in `terraform.tfvars`
2. **Use smaller VMs**: Change `aks_node_vm_size = "Standard_B1s"` (not recommended for production)
3. **Enable auto-scaling**: Already configured (min: 1, max: 4)
4. **Stop AKS when not in use**: `az aks stop --resource-group rg-uems-prod --name aks-uems-prod`

## Destroying Infrastructure

When you're done testing:

```bash
terraform destroy
```

**WARNING**: This will delete all resources and data. Make sure you have backups!

## Remote State Configuration

For team collaboration, configure remote state storage:

1. Create Azure Storage Account for Terraform state:

```bash
az group create --name terraform-state-rg --location "East US"
az storage account create --name tfstateuems --resource-group terraform-state-rg --location "East US" --sku Standard_LRS
az storage container create --name tfstate --account-name tfstateuems
```

2. Uncomment the backend configuration in `main.tf`:

```hcl
backend "azurerm" {
  resource_group_name  = "terraform-state-rg"
  storage_account_name = "tfstateuems"
  container_name       = "tfstate"
  key                  = "uems.terraform.tfstate"
}
```

3. Initialize with backend:

```bash
terraform init -migrate-state
```

## Troubleshooting

### Issue: "Insufficient permissions"

**Solution**: Ensure your Azure account has Contributor role on the subscription:

```bash
az role assignment create --assignee your-email@example.com --role Contributor --scope /subscriptions/your-subscription-id
```

### Issue: "Quota exceeded"

**Solution**: Check your Azure subscription quotas:

```bash
az vm list-usage --location "East US" --output table
```

Request quota increase if needed.

### Issue: "Kubernetes version not supported"

**Solution**: List available versions and update `aks_kubernetes_version`:

```bash
az aks get-versions --location "East US" --output table
```

## Next Steps

After infrastructure is provisioned:

1. Configure kubectl to use the AKS cluster
2. Deploy Kubernetes manifests for the application
3. Configure Prometheus and Grafana for monitoring
4. Set up GitLab CI/CD pipeline to push images to ACR

## Security Best Practices

- [ ] Disable ACR admin user in production (`admin_enabled = false`)
- [ ] Use Azure AD for AKS authentication
- [ ] Enable Azure Policy for AKS
- [ ] Configure Network Security Groups
- [ ] Enable Azure Defender for container scanning
- [ ] Rotate ACR credentials regularly
- [ ] Use Azure Key Vault for secrets

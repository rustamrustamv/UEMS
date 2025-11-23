# Deployment Guide

This guide covers deploying the UEMS application to Azure Kubernetes Service for testing and demonstration purposes.

## Prerequisites

- Azure account with active subscription
- Azure CLI installed and configured
- Terraform installed (version 1.0+)
- kubectl installed
- Helm 3 installed
- Docker installed
- Git installed

## Deployment Overview

1. Create Azure infrastructure with Terraform
2. Build and push Docker images
3. Deploy application to Kubernetes
4. Set up monitoring with Prometheus and Grafana
5. Access and test the application
6. Clean up resources when done

**Estimated time**: 2-3 hours
**Estimated cost**: $1-2 (for short-term testing)

## Step 1: Azure Account Setup

### Create Azure Account

1. Go to https://azure.microsoft.com/free/
2. Sign up for free account ($200 credit for 30 days)
3. Complete verification (credit card required but not charged)
4. Wait for account activation

### Configure Azure CLI

```bash
# Login to Azure
az login

# Verify subscription
az account show

# Set subscription if you have multiple
az account set --subscription "your-subscription-id"
```

## Step 2: Infrastructure Deployment

### Configure Terraform

```bash
cd terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit if needed (defaults are optimized for testing)
nano terraform.tfvars
```

Default configuration:
- 1 AKS node (Standard_B1s)
- Basic Load Balancer
- Basic tier Container Registry
- 7-day log retention

### Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Deploy (takes 10-15 minutes)
terraform apply

# Type 'yes' when prompted
```

### Get Infrastructure Details

```bash
# Save important outputs
terraform output

# Get AKS credentials
az aks get-credentials --resource-group rg-uems-prod --name aks-uems-prod

# Verify connection
kubectl get nodes
```

Expected output: 1 node in Ready status

## Step 3: Configure GitHub Actions

### Create Azure Service Principal

```bash
# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create service principal with RBAC auth
az ad sp create-for-rbac \
  --name "github-actions-uems" \
  --role Contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --sdk-auth

# Save the JSON output for GitHub secrets
```

### Configure GitHub Secrets

Go to GitHub repository > Settings > Secrets and variables > Actions

Add the following secrets:

| Secret Name | Value | How to Get |
|-------------|-------|------------|
| `AZURE_CREDENTIALS` | Service principal JSON | Output from command above |
| `ACR_NAME` | Container registry name | `terraform output acr_name` |
| `ACR_LOGIN_SERVER` | ACR login server | `terraform output acr_login_server` |
| `AKS_RESOURCE_GROUP` | Resource group name | `rg-uems-prod` |
| `AKS_CLUSTER_NAME` | AKS cluster name | `aks-uems-prod` |

## Step 4: Build and Push Docker Images

### Login to Container Registry

```bash
# Get ACR name
ACR_NAME=$(cd terraform && terraform output -raw acr_name)

# Login
az acr login --name $ACR_NAME
```

### Build and Push Backend

```bash
cd backend

# Get ACR login server
ACR_SERVER=$(cd ../terraform && terraform output -raw acr_login_server)

# Build image
docker build -t $ACR_SERVER/uems-backend:latest .

# Push to ACR
docker push $ACR_SERVER/uems-backend:latest
```

### Build and Push Frontend

```bash
cd ../frontend

# Build image
docker build -t $ACR_SERVER/uems-frontend:latest .

# Push to ACR
docker push $ACR_SERVER/uems-frontend:latest
```

## Step 5: Deploy Application to Kubernetes

### Create Namespace

```bash
kubectl create namespace uems-prod
```

### Create Kubernetes Secrets

```bash
# Database credentials
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 32) \
  --from-literal=POSTGRES_DB=uems \
  --namespace=uems-prod

# Application secrets
POSTGRES_PASSWORD=$(kubectl get secret postgres-secret -n uems-prod -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)

kubectl create secret generic backend-secret \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=DATABASE_URL=postgresql+asyncpg://postgres:$POSTGRES_PASSWORD@postgres:5432/uems \
  --from-literal=STRIPE_API_KEY=sk_test_your_key_here \
  --from-literal=STRIPE_WEBHOOK_SECRET=whsec_your_secret_here \
  --namespace=uems-prod
```

### Create Kubernetes Manifests

Create `k8s/application/postgres.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        envFrom:
        - secretRef:
            name: postgres-secret
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
```

Create `k8s/application/backend.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: backend
        image: YOUR_ACR_SERVER/uems-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: backend-secret
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: backend
  ports:
  - port: 8000
```

Create `k8s/application/frontend.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: YOUR_ACR_SERVER/uems-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "http://backend:8000/api/v1"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 3000
```

### Update ACR Server in Manifests

```bash
# Get ACR server
ACR_SERVER=$(cd terraform && terraform output -raw acr_login_server)

# Update manifests
sed -i "s|YOUR_ACR_SERVER|$ACR_SERVER|g" k8s/application/*.yaml
```

### Deploy to Kubernetes

```bash
kubectl apply -f k8s/application/ --namespace=uems-prod

# Watch deployment
kubectl get pods -n uems-prod -w

# Press Ctrl+C when all pods are Running
```

### Seed Database

```bash
# Get backend pod name
BACKEND_POD=$(kubectl get pod -n uems-prod -l app=backend -o jsonpath='{.items[0].metadata.name}')

# Run seed script
kubectl exec -it $BACKEND_POD -n uems-prod -- python seed.py
```

### Access Application

```bash
# Get LoadBalancer IP
kubectl get svc frontend -n uems-prod

# Wait for EXTERNAL-IP (2-3 minutes)
# Access: http://EXTERNAL-IP
```

Login with: `admin@university.edu` / `admin123`

## Step 6: Set Up Monitoring

### Install Prometheus and Grafana

```bash
# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Create monitoring namespace
kubectl create namespace monitoring

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values k8s/monitoring/prometheus-grafana-values.yaml \
  --wait
```

### Import Custom Dashboard

```bash
# Create ConfigMap from dashboard JSON
kubectl create configmap grafana-uems-dashboard \
  --from-file=k8s/monitoring/uems-dashboard.json \
  --namespace monitoring

# Label for auto-discovery
kubectl label configmap grafana-uems-dashboard \
  grafana_dashboard=1 \
  --namespace monitoring

# Restart Grafana
kubectl rollout restart deployment prometheus-grafana -n monitoring
```

### Access Grafana

```bash
# Port forward
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Open: http://localhost:3000
# Username: admin
# Password: admin123
```

Navigate to Dashboards > Browse > UEMS folder > "UEMS - Production Dashboard"

## Step 7: Testing

### Verify Application

1. Access frontend via LoadBalancer IP
2. Login as admin
3. View Analytics Dashboard
4. Check that metrics are populated

### Verify Metrics

```bash
# Port forward backend
kubectl port-forward svc/backend 8000:8000 -n uems-prod

# Check metrics endpoint
curl http://localhost:8000/metrics
```

### Verify Logs

```bash
# View backend logs
kubectl logs -f deployment/backend -n uems-prod

# Check for JSON formatted logs
```

## Step 8: Clean Up Resources

When finished testing:

```bash
# Delete Kubernetes resources
kubectl delete namespace uems-prod
kubectl delete namespace monitoring

# Delete Azure infrastructure
cd terraform
terraform destroy

# Type 'yes' when prompted
```

This removes all Azure resources and stops billing.

## GitHub Actions Deployment

Once secrets are configured, the GitHub Actions workflow automatically:

1. Runs on push to `main` branch
2. Lints and tests code
3. Builds Docker images
4. Pushes to ACR
5. Deploys to AKS

View workflow runs at: GitHub repository > Actions

## Cost Management

### Expected Costs

| Resource | Daily Cost |
|----------|-----------|
| AKS node (B1s) | $0.25 |
| ACR Basic | $0.17 |
| Storage | $0.05 |
| **Total** | **~$0.47/day** |

For 2-3 days of testing: ~$1-1.50

### Verify Costs

```bash
# Check current costs
az consumption usage list \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --output table
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n uems-prod

# View pod details
kubectl describe pod POD_NAME -n uems-prod

# Check logs
kubectl logs POD_NAME -n uems-prod
```

### Cannot access application

```bash
# Verify LoadBalancer service
kubectl get svc frontend -n uems-prod

# Check that EXTERNAL-IP is assigned (not pending)
```

### Grafana shows no data

1. Verify backend pods have Prometheus annotations
2. Check Prometheus targets: http://localhost:9090/targets
3. Wait 1-2 minutes for metrics to accumulate

### Image pull errors

```bash
# Verify ACR credentials
az acr login --name $(terraform output -raw acr_name)

# Check image exists
az acr repository list --name $(terraform output -raw acr_name)
```

## Additional Resources

- Terraform README: `terraform/README.md`
- Monitoring README: `k8s/monitoring/README.md`
- Architecture Details: `ARCHITECTURE.md`
- Azure Documentation: https://learn.microsoft.com/azure/
- Kubernetes Documentation: https://kubernetes.io/docs/

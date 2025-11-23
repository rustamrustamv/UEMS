# UEMS Monitoring Setup with Prometheus & Grafana

This directory contains configuration for monitoring the UEMS application using Prometheus and Grafana.

## Overview

The monitoring stack includes:

- **Prometheus** - Metrics collection and storage
- **Grafana** - Metrics visualization and dashboards
- **Alert Manager** - Alert routing and notifications
- **Node Exporter** - Host-level metrics
- **Kube State Metrics** - Kubernetes cluster metrics

## Prerequisites

1. AKS cluster running and accessible via kubectl
2. Helm 3 installed
3. kubectl configured to access your cluster

## Installation

### Step 1: Add Prometheus Helm Repository

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

### Step 2: Create Monitoring Namespace

```bash
kubectl create namespace monitoring
```

### Step 3: Install kube-prometheus-stack

```bash
cd k8s/monitoring

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values prometheus-grafana-values.yaml
```

This will install:
- Prometheus Operator
- Prometheus Server
- Grafana
- Alert Manager
- Node Exporter
- Kube State Metrics

### Step 4: Create ConfigMap for Custom Dashboard

```bash
kubectl create configmap grafana-uems-dashboard \
  --from-file=uems-dashboard.json \
  --namespace monitoring

# Label the ConfigMap so Grafana can discover it
kubectl label configmap grafana-uems-dashboard \
  grafana_dashboard=1 \
  --namespace monitoring
```

### Step 5: Restart Grafana to Load Dashboard

```bash
kubectl rollout restart deployment prometheus-grafana --namespace monitoring
```

## Accessing Grafana

### Option 1: Port Forward (Quick Access)

```bash
kubectl port-forward svc/prometheus-grafana 3000:80 --namespace monitoring
```

Then open: http://localhost:3000

- **Username**: admin
- **Password**: admin123 (or check values file)

### Option 2: LoadBalancer (Production)

If you configured Grafana service as LoadBalancer:

```bash
kubectl get svc prometheus-grafana --namespace monitoring
```

Get the EXTERNAL-IP and access Grafana at `http://EXTERNAL-IP`

### Option 3: Ingress (Recommended for Production)

Create an Ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana-ingress
  namespace: monitoring
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - grafana.yourdomain.com
      secretName: grafana-tls
  rules:
    - host: grafana.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: prometheus-grafana
                port:
                  number: 80
```

## Accessing Prometheus

### Port Forward to Prometheus

```bash
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 --namespace monitoring
```

Then open: http://localhost:9090

## Verifying Metrics Collection

### Check Prometheus Targets

1. Access Prometheus UI (port-forward method above)
2. Go to Status > Targets
3. Verify `uems-backend` job shows UP status

### Test UEMS Metrics

In Prometheus UI, run these queries:

```promql
# Check if UEMS metrics are being scraped
up{job="uems-backend"}

# View active users
uems_active_users_total

# View HTTP requests
rate(http_requests_total[5m])

# View request latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Viewing the UEMS Dashboard

1. Access Grafana UI
2. Go to Dashboards > Browse
3. Look for "UEMS - Production Dashboard" in the "UEMS" folder
4. Dashboard auto-refreshes every 30 seconds

### Dashboard Panels

The UEMS dashboard includes:

1. **Request Latency (p50, p95, p99)** - API response times
2. **Error Rate (%)** - Percentage of failed requests
3. **Active Users by Role** - Pie chart of users by role
4. **Total Active Users** - Current active user count
5. **Total Enrollments** - Course enrollment count
6. **Total Revenue** - Sum of successful payments
7. **Request Throughput** - Requests per second by endpoint
8. **Enrollment Status Distribution** - Enrollments by status
9. **Payment Status Distribution** - Payment success/failure rates
10. **Database Query Duration (p95)** - DB performance by table
11. **Login Rate by Role** - Login activity trends
12. **Application Errors by Type** - Error distribution

## Configuring Alerts

### Create Alert Rules

Create a file `uems-alerts.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: uems-alert-rules
  namespace: monitoring
data:
  uems-alerts.yaml: |
    groups:
      - name: uems
        interval: 30s
        rules:
          - alert: HighErrorRate
            expr: (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100 > 5
            for: 5m
            labels:
              severity: critical
            annotations:
              summary: "High error rate detected"
              description: "Error rate is {{ $value }}% over the last 5 minutes"

          - alert: HighRequestLatency
            expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler)) > 1
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "High request latency detected"
              description: "95th percentile latency is {{ $value }}s for {{ $labels.handler }}"

          - alert: PaymentFailureSpike
            expr: sum(increase(uems_payments_total{status="failed"}[15m])) > 10
            for: 5m
            labels:
              severity: critical
            annotations:
              summary: "Payment failure spike detected"
              description: "{{ $value }} payment failures in the last 15 minutes"
```

Apply it:

```bash
kubectl apply -f uems-alerts.yaml
```

### Configure Notification Channels

Edit the Helm values file to add notification receivers (Slack, email, etc.):

```yaml
alertmanager:
  config:
    receivers:
      - name: 'slack-notifications'
        slack_configs:
          - api_url: 'YOUR_SLACK_WEBHOOK_URL'
            channel: '#uems-alerts'
            title: 'UEMS Alert'
            text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

      - name: 'email-notifications'
        email_configs:
          - to: 'ops@university.edu'
            from: 'alertmanager@university.edu'
            smarthost: 'smtp.gmail.com:587'
            auth_username: 'your-email@gmail.com'
            auth_password: 'your-app-password'

    route:
      receiver: 'slack-notifications'
      routes:
        - match:
            severity: critical
          receiver: 'email-notifications'
```

Upgrade the Helm release:

```bash
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values prometheus-grafana-values.yaml
```

## Troubleshooting

### Issue: Prometheus not scraping UEMS metrics

**Check 1**: Verify backend pods have the correct annotations

```bash
kubectl get pods -n uems-prod -o yaml | grep -A 5 "annotations:"
```

Expected annotations:
```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

**Check 2**: Verify /metrics endpoint is accessible

```bash
kubectl port-forward deployment/backend 8000:8000 -n uems-prod
curl http://localhost:8000/metrics
```

You should see Prometheus metrics output.

**Check 3**: Check Prometheus logs

```bash
kubectl logs -l app=prometheus --namespace monitoring | grep uems
```

### Issue: Dashboard shows "No Data"

**Solution**:
1. Ensure metrics are being collected (check Prometheus targets)
2. Verify the time range in Grafana (top-right corner)
3. Check if the data source is correctly configured (Prometheus)
4. Wait a few minutes for data to accumulate

### Issue: Grafana dashboard not showing up

**Solution**:
```bash
# Verify ConfigMap was created
kubectl get configmap grafana-uems-dashboard -n monitoring

# Check ConfigMap has correct label
kubectl get configmap grafana-uems-dashboard -n monitoring --show-labels

# Restart Grafana
kubectl rollout restart deployment prometheus-grafana -n monitoring
```

## Uninstalling

To remove the monitoring stack:

```bash
# Delete the Helm release
helm uninstall prometheus --namespace monitoring

# Delete the namespace (optional - removes all resources)
kubectl delete namespace monitoring
```

## Production Recommendations

- [ ] Change Grafana admin password
- [ ] Configure persistent volumes for Prometheus and Grafana
- [ ] Set up automated backups for Grafana dashboards
- [ ] Configure alert notification channels (Slack, PagerDuty, email)
- [ ] Implement log aggregation (Loki + Promtail)
- [ ] Enable Prometheus remote write for long-term storage
- [ ] Configure resource limits and requests
- [ ] Set up Grafana authentication (OAuth, LDAP)
- [ ] Enable HTTPS for Grafana (Ingress + cert-manager)
- [ ] Configure retention policies based on storage capacity

## Useful PromQL Queries

### HTTP Metrics

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate percentage
(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# Latency p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### UEMS Business Metrics

```promql
# Active users
sum(uems_active_users_total)

# Enrollment rate
rate(uems_enrollments_total[1h])

# Payment success rate
sum(rate(uems_payments_total{status="succeeded"}[5m])) / sum(rate(uems_payments_total[5m]))

# Revenue growth
increase(uems_payments_amount_usd_total[24h])
```

### Database Metrics

```promql
# DB query duration p95 by table
histogram_quantile(0.95, rate(uems_database_query_duration_seconds_bucket[5m]))

# Slow queries (> 100ms)
uems_database_query_duration_seconds > 0.1
```

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)

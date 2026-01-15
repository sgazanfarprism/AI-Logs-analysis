# Kubernetes Deployment Guide

## Prerequisites

1. Kubernetes cluster (EKS, GKE, AKS, or local)
2. kubectl configured
3. Docker image built and pushed to registry

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build image
docker build -t ai-log-analysis:latest .

# Tag for your registry
docker tag ai-log-analysis:latest YOUR_REGISTRY/ai-log-analysis:latest

# Push to registry
docker push YOUR_REGISTRY/ai-log-analysis:latest
```

### 2. Update Secrets

Edit `secrets.yaml` with your actual credentials:

```bash
# Encode secrets (if using base64)
echo -n "your-api-key" | base64
```

Or use kubectl to create secrets:

```bash
kubectl create secret generic log-analyzer-secrets \
  --namespace=log-analyzer \
  --from-literal=GEMINI_API_KEY=your-key \
  --from-literal=SMTP_USERNAME=your-email \
  --from-literal=SMTP_PASSWORD=your-password \
  --from-literal=AWS_ACCESS_KEY_ID=your-aws-key \
  --from-literal=AWS_SECRET_ACCESS_KEY=your-aws-secret
```

### 3. Deploy with Kustomize

```bash
# Preview what will be deployed
kubectl kustomize k8s/

# Apply all resources
kubectl apply -k k8s/

# Or apply individually
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n log-analyzer

# Check logs
kubectl logs -f deployment/log-analyzer-scheduler -n log-analyzer

# Check services
kubectl get svc -n log-analyzer
```

## Architecture Options

### Option 1: Continuous Scheduler (Default)
Uses a Deployment running `hourly_scheduler.py` which schedules analysis every hour internally.

**Pros:** Simple, always running, immediate startup analysis
**Cons:** Uses resources continuously

### Option 2: Kubernetes CronJob
Uses a CronJob to run analysis every hour.

**Pros:** Resource efficient, native K8s scheduling
**Cons:** Cold start each hour

To use CronJob instead:
1. Edit `kustomization.yaml` to include `cronjob.yaml`
2. Remove or scale down the scheduler deployment

## Monitoring

### Check Status
```bash
# Pod status
kubectl get pods -n log-analyzer -w

# Recent logs
kubectl logs -f deployment/log-analyzer-scheduler -n log-analyzer --tail=100

# Describe pod for events
kubectl describe pod -l app=log-analyzer -n log-analyzer
```

### View Results
```bash
# Access results PVC
kubectl exec -it deployment/log-analyzer-scheduler -n log-analyzer -- ls -la /app/results
```

## Scaling

```bash
# Scale API servers (scheduler should stay at 1)
kubectl scale deployment log-analyzer-api --replicas=3 -n log-analyzer
```

## Cleanup

```bash
kubectl delete -k k8s/
# or
kubectl delete namespace log-analyzer
```

## Troubleshooting

### Pod CrashLoopBackOff
```bash
kubectl logs -p deployment/log-analyzer-scheduler -n log-analyzer
```

### Check ConfigMap/Secrets
```bash
kubectl get configmap log-analyzer-config -n log-analyzer -o yaml
kubectl get secret log-analyzer-secrets -n log-analyzer -o yaml
```

### Test AWS Connectivity
```bash
kubectl exec -it deployment/log-analyzer-scheduler -n log-analyzer -- \
  python -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

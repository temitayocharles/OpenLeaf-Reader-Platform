# OpenLeaf Kubernetes Apply Order + Argo Sync-Wave Mapping

This file defines both:
1. manual apply order for `kubectl apply`
2. Argo CD `argocd.argoproj.io/sync-wave` ordering for GitOps

## Preflight Checks

1. Confirm target namespace exists.
2. Confirm image registry credentials exist in namespace when using private images.
3. Confirm required secret keys are prepared before workload rollout.
4. Confirm ingress controller is available (`kong` or your configured class).

## Canonical Apply Order

1. Runtime configuration
   - `app-config.yaml`
   - `app-secrets.yaml`
2. Core workloads
   - `user-deployment.yaml`
   - `services-deployments.yaml`
3. Kong plugin resources
   - `kong-config.yaml`
   - `analytics-acl-plugin.yaml`
   - `kong-prometheus.yaml`
4. Ingress hardening (optional)
   - `kong-hardened-advanced.yaml`
5. Observability extras (optional)
   - `grafana-dashboards-configmap.yaml`
6. Chaos manifests (test windows only)
   - `chaos/*.yaml`
   - `chaos/kong/*.yaml`

## Argo Sync-Wave Mapping

1. Wave `-20` (runtime prerequisites)
   - `app-config.yaml`
   - `app-secrets.yaml`
2. Wave `0` (core workloads)
   - `user-deployment.yaml`
   - `services-deployments.yaml`
3. Wave `10` (Kong plugins)
   - `kong-config.yaml` plugins
   - `analytics-acl-plugin.yaml`
   - `kong-prometheus.yaml`
4. Wave `20` (ingress and hardened ingress chain)
   - `kong-config.yaml` ingress
   - `kong-hardened-advanced.yaml`
5. Wave `30` (observability extras)
   - `grafana-dashboards-configmap.yaml`
6. Wave `90` (chaos test resources)
   - `chaos/*.yaml`
   - `chaos/kong/*.yaml`

Argo note:
- Keep chaos resources disabled or excluded in production-style apps unless intentionally running failure tests.

## Example Command Sequence

```bash
kubectl apply -f k8s/app-config.yaml
kubectl apply -f k8s/app-secrets.yaml

kubectl apply -f k8s/user-deployment.yaml
kubectl apply -f k8s/services-deployments.yaml

kubectl apply -f k8s/kong-config.yaml
kubectl apply -f k8s/analytics-acl-plugin.yaml
kubectl apply -f k8s/kong-prometheus.yaml

# Optional hardened route
kubectl apply -f k8s/kong-hardened-advanced.yaml

# Optional Grafana dashboards
kubectl apply -f k8s/grafana-dashboards-configmap.yaml
```

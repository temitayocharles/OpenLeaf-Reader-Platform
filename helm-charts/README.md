# OpenLeaf Helm Charts

This directory contains first-party Helm charts for OpenLeaf workloads.

## Charts

- `charts/openleaf-config`
  - Runtime configuration resources (`ConfigMap`, optional `Secret`)
- `charts/openleaf-user-service`
  - `user-service` deployment, service, HPA, and PDB
- `charts/openleaf-services-bundle`
  - `book-service`, `publishing-service`, `subscription-service`, `payment-service`, `analytics-service`
- `charts/openleaf-gateway`
  - Kong plugins, base ingress, and optional hardened ingress chain

## Validate Locally

```bash
cd <openleaf-repo-root>

helm lint helm-charts/charts/openleaf-config
helm lint helm-charts/charts/openleaf-user-service
helm lint helm-charts/charts/openleaf-services-bundle
helm lint helm-charts/charts/openleaf-gateway
```

## Render Examples

```bash
helm template openleaf-config helm-charts/charts/openleaf-config -f helm-charts/charts/openleaf-config/values-staging.yaml
helm template openleaf-user helm-charts/charts/openleaf-user-service -f helm-charts/charts/openleaf-user-service/values-staging.yaml
helm template openleaf-services helm-charts/charts/openleaf-services-bundle -f helm-charts/charts/openleaf-services-bundle/values-staging.yaml
helm template openleaf-gateway helm-charts/charts/openleaf-gateway -f helm-charts/charts/openleaf-gateway/values-staging.yaml
```

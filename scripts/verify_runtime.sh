#!/usr/bin/env bash
set -euo pipefail

KUBE_NS="${KUBE_NS:-default}"
KONG_PROXY_URL="${KONG_PROXY_URL:-http://localhost:8000}"

echo "Checking required config objects in namespace: $KUBE_NS"
kubectl get configmap app-config -n "$KUBE_NS" >/dev/null
kubectl get secret app-secrets -n "$KUBE_NS" >/dev/null

services=(user-service book-service publishing-service subscription-service payment-service analytics-service)

echo "Checking deployments rollout"
for svc in "${services[@]}"; do
  kubectl rollout status deployment/"$svc" -n "$KUBE_NS" --timeout=180s
done

echo "Checking services"
for svc in "${services[@]}"; do
  kubectl get svc "$svc" -n "$KUBE_NS" >/dev/null
done

echo "Smoke-checking Kong-routed health endpoints at $KONG_PROXY_URL"
for path in users books publish subscriptions payments analytics; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$KONG_PROXY_URL/$path/health" || true)
  echo "$path/health -> $code"
done

echo "Runtime verification completed."

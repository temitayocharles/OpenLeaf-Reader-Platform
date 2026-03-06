#!/usr/bin/env bash
set -euo pipefail

KUBE_NS="${KUBE_NS:-default}"
KONG_PROXY_URL="${KONG_PROXY_URL:-}"

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

echo "Smoke-checking in-cluster service health endpoints"
declare -A service_ports=(
  [user-service]=5001
  [book-service]=5002
  [publishing-service]=5003
  [subscription-service]=5004
  [payment-service]=5005
  [analytics-service]=5006
)

for svc in "${services[@]}"; do
  port="${service_ports[$svc]}"
  code=$(kubectl run verify-curl --rm -i --restart=Never --image=curlimages/curl:8.12.1 -n "$KUBE_NS" -- \
    sh -lc "curl -s -o /dev/null -w \"%{http_code}\" --max-time 10 http://$svc:$port/health" 2>/dev/null || true)
  echo "$svc/health -> $code"
done

if [ -n "$KONG_PROXY_URL" ]; then
  echo "Optional Kong checks at $KONG_PROXY_URL"
  for path in users books publish subscriptions payments analytics; do
    code=$(curl -s -o /dev/null -w "%{http_code}" "$KONG_PROXY_URL/$path/health" || true)
    echo "$path/health -> $code"
  done
fi

echo "Runtime verification completed."

#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
KUBE_NS="${KUBE_NS:-default}"
ARGOCD_NS="${ARGOCD_NS:-argocd}"
CHAOS_NS="${CHAOS_NS:-chaos-testing}"
TARGET_PLATFORMS="${TARGET_PLATFORMS:-linux/amd64,linux/arm64}"

required_cmds=(kubectl helm docker python3 node npm)
missing=()

for cmd in "${required_cmds[@]}"; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    missing+=("$cmd")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Missing required tools: ${missing[*]}"
  echo "Install missing dependencies first, then re-run setup."
  exit 1
fi

echo "Project root: $PROJECT_ROOT"
echo "Using namespaces:"
echo "  KUBE_NS=$KUBE_NS"
echo "  ARGOCD_NS=$ARGOCD_NS"
echo "  CHAOS_NS=$CHAOS_NS"
echo "Target platforms: $TARGET_PLATFORMS"

mkdir -p "$PROJECT_ROOT/chaos-logs" "$PROJECT_ROOT/services/tests" "$PROJECT_ROOT/helm-charts"

if [ ! -f "$PROJECT_ROOT/frontend/.env" ] && [ -f "$PROJECT_ROOT/frontend/.env.example" ]; then
  cp "$PROJECT_ROOT/frontend/.env.example" "$PROJECT_ROOT/frontend/.env"
  echo "Created frontend/.env from .env.example"
fi

echo "Helm repo bootstrap"
helm repo add bitnami https://charts.bitnami.com/bitnami >/dev/null 2>&1 || true
helm repo add kong https://charts.konghq.com >/dev/null 2>&1 || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
helm repo add grafana https://grafana.github.io/helm-charts >/dev/null 2>&1 || true
helm repo add chaos-mesh https://charts.chaos-mesh.org >/dev/null 2>&1 || true
helm repo update >/dev/null 2>&1 || true

echo "Setup checks complete."
echo "Next: follow README.md sections in order to deploy the stack."

# Cluster CPU Warning Triage (OpenLeaf Platform)

This document captures observed high-CPU behavior and a remediation plan. It does not apply changes directly.

## Observed Signals

From cluster diagnostics:
- Node CPU reached high utilization (observed near saturation in one sampling window).
- Highest consumer was Argo CD application controller.
- Repeated OutOfSync/reconcile loops were present.
- Drift-heavy apps included:
  - `platform-tools`
  - `minio-access`
  - `loki`
  - selected `autodesk-*` apps
- Occasional Vault readiness timeout event was present.

## Current Snapshot (2026-03-06)

Read-only sample:
- Node CPU: `3608m` (`51%`)
- Top pod CPU:
  - `argocd/argo-cd-argocd-application-controller-0`: `1543m`
  - `observability/prometheus-kube-prometheus-stack-prometheus-0`: `135m`
  - `argocd/argo-cd-argocd-repo-server-78cb69f46d-2b6kr`: `90m`
  - `vault/vault-0`: `85m`

Observed non-healthy sync states:
- `platform-tools`: `OutOfSync`
- `platform-root`: `OutOfSync`
- `minio-access`: `OutOfSync`
- `loki`: `OutOfSync`
- `autodesk-data-ingestion-service`: `OutOfSync`
- `autodesk-data-processing-service`: `OutOfSync`

Event stream showed repeated rapid Argo operation start/complete cycles and sync status oscillation for these apps.

## Likely Root Causes

1. Reconcile churn:
- Frequent automated sync operations repeatedly re-queuing affected apps.

2. Persistent drift:
- Resources stay OutOfSync due mutable status/managed fields or ownership overlap.

3. Ownership boundary violations:
- Same resources managed by more than one app/source can continuously oscillate desired state.

4. Health probe pressure:
- Intermittent readiness failures (for example Vault) can trigger additional controller work.

## Remediation Plan (No Direct Runtime Apply in This Task)

### A) Remove Persistent Drift Sources
1. For each OutOfSync app, inspect exact diff fields:
   - `kubectl -n argocd get app <app> -o yaml`
2. Separate expected-runtime-mutated fields from true config drift.
3. Fix source-of-truth ownership where overlapping apps render the same objects.

### B) Reduce Noisy Diffs in Argo
1. Add `ignoreDifferences` only for safe noisy fields:
   - status blocks
   - controller-added annotations/managed fields that should not force resync
2. Keep spec-level drift visible.

### C) Tune Sync Behavior for Churn-Prone Apps
1. For non-critical apps with known transient mutation, review aggressive self-heal settings.
2. Retain safety while preventing continuous no-op sync loops.

### D) Add CPU Guardrails
1. Alert when:
   - controller CPU exceeds sustained threshold
   - node CPU exceeds threshold
   - OutOfSync count remains above threshold duration
2. Dashboard top controller workloads and top namespaces by CPU.

## Diagnostic Commands (Read-Only)

```bash
kubectl top nodes
kubectl top pods -A --sort-by=cpu | head -n 30
kubectl -n argocd get applications
kubectl -n argocd get app <app> -o yaml
kubectl get events -A --sort-by=.lastTimestamp | tail -n 100
```

## PR Backlog (Suggested)

1. GitOps PR: resolve OutOfSync ownership and source overlap for `platform-tools` and `minio-access`.
2. GitOps PR: add narrowly-scoped `ignoreDifferences` for known mutable non-spec fields.
3. Observability PR: alerts and dashboard panels for controller CPU + OutOfSync duration.
4. Platform PR: validate Vault readiness probe timeout thresholds and startup behavior.

## Evidence Template

```text
CPU Triage Evidence
- timestamp:
- node CPU snapshot:
- top 10 pods by CPU:
- out-of-sync apps:
- representative diff field(s):
- readiness warnings observed:
- proposed fix PR links:
- post-fix expected CPU target:
```

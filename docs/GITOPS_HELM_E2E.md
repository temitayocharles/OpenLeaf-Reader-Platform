# OpenLeaf GitOps Helm E2E Runbook (Chart Change to Browser Verification)

This runbook defines the release and verification path when OpenLeaf is deployed via Helm charts + GitOps.

Scope:
- Build and publish images
- Update chart values
- Promote via GitOps repo
- Verify Argo sync, workload health, and browser/API behavior
- Roll back safely

This runbook does not require direct `kubectl apply` of app manifests for normal operations.

## CI/CD Pipeline Entry Points

- CI workflow: `.github/workflows/ci-cd.yaml`
- CD workflow: `.github/workflows/cd-release.yaml`

CD workflow behavior:
1. validates Helm charts (`lint` + `template`) for selected environment
2. builds and pushes multi-arch images to GHCR
3. uploads release evidence artifact (render checksums + image tags)

Manual release trigger:
- GitHub Actions -> `CD Release` -> `Run workflow`
- choose `environment` (`dev`, `staging`, `prod`)
- optionally provide `image_tag`
- optional: set `promote_gitops=true` to auto-open a GitOps PR

Tag-driven trigger examples:
- `staging-20260306`
- `prod-20260306`
- `release-20260306`

GitOps auto-promotion requirements:
- recommended GHCR publish secrets:
  - `GHCR_TOKEN` (PAT with `write:packages`, `read:packages`)
  - `GHCR_USERNAME` (optional; falls back to `github.actor`)
- repository secret: `GITOPS_REPO_TOKEN`
- workflow input `gitops_repo` set to the target repo (`owner/name`)
- workflow input `gitops_base_branch` set to target branch (default `main`)

GitOps auto-promotion behavior:
- checks out the GitOps repo
- scans `values-<env>.yaml` files
- updates `image.tag` for repositories that contain `/openleaf-`
- opens a PR with the updated tags

## 1) Preconditions

1. Helm chart source:
   - `<openleaf-repo-root>/helm-charts`
2. GitOps repo with Argo `Application` manifests and values overrides.
3. Image registry credentials configured in-cluster.
4. Argo CD has access to chart + values repos.
5. Ingress DNS or hosts-file mapping is available for test hostname.

## 2) Build and Push Multi-Arch Images (Immutable Tags)

Use immutable tags (for example, commit SHA):

```bash
export TAG="$(git rev-parse --short HEAD)"
export PLATFORMS="linux/amd64,linux/arm64"

docker buildx build --platform "$PLATFORMS" -t ghcr.io/<org>/openleaf-user-service:${TAG} --push services/user-service
docker buildx build --platform "$PLATFORMS" -t ghcr.io/<org>/openleaf-book-service:${TAG} --push services/book-service
docker buildx build --platform "$PLATFORMS" -t ghcr.io/<org>/openleaf-publishing-service:${TAG} --push services/publishing-service
docker buildx build --platform "$PLATFORMS" -t ghcr.io/<org>/openleaf-subscription-service:${TAG} --push services/subscription-service
docker buildx build --platform "$PLATFORMS" -t ghcr.io/<org>/openleaf-payment-service:${TAG} --push services/payment-service
docker buildx build --platform "$PLATFORMS" -t ghcr.io/<org>/openleaf-analytics-service:${TAG} --push services/analytics-service
```

## 3) Update Helm Values in Chart Repo

Update environment overlay values:
- `helm-charts/charts/openleaf-user-service/values-<env>.yaml`
- `helm-charts/charts/openleaf-services-bundle/values-<env>.yaml`
- `helm-charts/charts/openleaf-gateway/values-<env>.yaml` (host/path changes only when needed)

Example:

```yaml
image:
  tag: "<immutable-tag>"
```

## 4) Validate Chart Renders Before Push

```bash
cd <openleaf-repo-root>

helm lint helm-charts/charts/openleaf-config
helm lint helm-charts/charts/openleaf-user-service
helm lint helm-charts/charts/openleaf-services-bundle
helm lint helm-charts/charts/openleaf-gateway

helm template openleaf-config helm-charts/charts/openleaf-config -f helm-charts/charts/openleaf-config/values-staging.yaml >/tmp/openleaf-config.render.yaml
helm template openleaf-user helm-charts/charts/openleaf-user-service -f helm-charts/charts/openleaf-user-service/values-staging.yaml >/tmp/openleaf-user.render.yaml
helm template openleaf-services helm-charts/charts/openleaf-services-bundle -f helm-charts/charts/openleaf-services-bundle/values-staging.yaml >/tmp/openleaf-services.render.yaml
helm template openleaf-gateway helm-charts/charts/openleaf-gateway -f helm-charts/charts/openleaf-gateway/values-staging.yaml >/tmp/openleaf-gateway.render.yaml
```

## 5) Commit/Push Chart Repo

```bash
git add helm-charts/
git commit -m "feat(helm): promote OpenLeaf images to <tag>"
git push origin main
```

## 6) Update GitOps Repo to Consume New Chart/Tag

In your GitOps repo:
1. Pin chart source revision (if required by your workflow).
2. Update values reference or value file tag fields.
3. Commit and push.

## 7) Verify Argo and Runtime Health

```bash
kubectl -n argocd get applications
kubectl -n argocd get application <openleaf-app> -o yaml | rg -n "sync:|health:"
kubectl -n <app-namespace> get deploy,po,svc,ingress
```

Check app endpoints:

```bash
curl -sS http://<gateway-host>/users/health
curl -sS http://<gateway-host>/books/health
curl -sS http://<gateway-host>/publish/health
curl -sS http://<gateway-host>/subscriptions/health
curl -sS http://<gateway-host>/payments/health
curl -sS http://<gateway-host>/analytics/health
```

Browser check:
- Open `http(s)://<gateway-host>/...` and verify frontend route loads and can call APIs through Kong.

## 8) Rollback Procedure

1. Revert the offending commit in chart or GitOps repo.
2. Push revert.
3. Confirm Argo reconciles to previous healthy revision.

```bash
git revert <bad-commit-sha>
git push origin main
kubectl -n argocd get application <openleaf-app>
```

## 9) Evidence Block Template (Attach to Release Notes)

```text
Release Evidence
- App repo SHA:
- Helm charts repo SHA:
- GitOps repo SHA:
- Image tags:
- Render checksum(s):
  - /tmp/openleaf-user.render.yaml: <sha256>
  - /tmp/openleaf-services.render.yaml: <sha256>
  - /tmp/openleaf-gateway.render.yaml: <sha256>
- Argo status:
  - app: <name>, sync: <Synced/OutOfSync>, health: <Healthy/Degraded>
- Runtime status:
  - pods ready:
  - services:
  - ingress:
- Smoke tests:
  - users health:
  - books health:
  - payment health:
- Browser verification:
  - URL:
  - timestamp:
- Rollback tested:
  - yes/no
```

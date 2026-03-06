# Readiness Gap Log

Date: 2026-03-06
Scope: full repository audit for partial/minimal/stub files.

## Must-Fix (Completed)

1. `scripts/setup.sh`
- Issue: placeholder-only script with no real bootstrap behavior.
- Risk: onboarding friction and inconsistent environment setup.
- Remediation: replaced with operational bootstrap checks (tool validation, namespace/platform variables, optional env bootstrap, Helm repo setup).
- Status: completed.

2. `k8s/grafana-dashboards-configmap.yaml` and `k8s/grafana-dashboards/openleaf-overview.json`
- Issue: dashboard payload was placeholder content.
- Risk: invalid/no-op dashboard provisioning in Grafana.
- Remediation: replaced with valid starter dashboard JSON containing gateway request and 5xx panels.
- Status: completed.

3. `.github/workflows/ci-cd.yaml`
- Issue: test stage risked failure from missing frontend dependency install and no-tests behavior.
- Risk: avoidable CI failures.
- Remediation: added `npm ci` before frontend test and `--passWithNoTests`; kept service test invocation in place.
- Status: completed.

4. `services/tests/`
- Issue: empty test directory.
- Risk: CI pytest run on empty suite can fail by configuration.
- Remediation: added `services/tests/test_scaffold.py` to validate expected service entrypoints exist.
- Status: completed.

5. Empty scaffold directories lacked intent markers
- Paths: `chaos-logs/`, `helm-charts/`, `services/tests/`
- Issue: empty directories looked accidental.
- Remediation: added README files documenting intended use.
- Status: completed.

## Should-Fix (Completed)

1. `services/payment-service/app.py`
- Item: Stripe price IDs were hardcoded placeholders.
- Action: switched to required env vars `STRIPE_PRICE_BASIC` / `STRIPE_PRICE_PREMIUM` with explicit config guard.
- Status: completed.

2. `frontend/src/components/SubscriptionPage.js`
- Item: publishable key fallback was placeholder-based.
- Action: removed placeholder fallback; component now requires `REACT_APP_STRIPE_PUBLISHABLE_KEY` and shows clear config message when missing.
- Status: completed.

3. Service-level tests
- Item: test coverage was scaffold-level only.
- Action: added endpoint/auth contract tests in `services/tests/test_endpoints.py` (user, book, publishing, subscription, payment including webhook guard).
- Status: completed.

4. CI dependency/test execution consistency
- Item: CI test stage did not install service dependencies before running pytest.
- Action: updated workflow to install each service `requirements.txt` before `pytest services/tests/`.
- Status: completed.

5. Kubernetes runtime wiring for all services
- Item: only `user-service` had deployment manifest and runtime env wiring.
- Action: added `k8s/app-config.yaml`, `k8s/app-secrets.yaml`, and `k8s/services-deployments.yaml`; updated `user-deployment.yaml` to include `app-config`; added runtime verification script `scripts/verify_runtime.sh`; updated README deployment/apply flow.
- Status: completed.

## Defer (Intentional)

1. `helm-charts/`
- Reason: reserved for future custom chart packaging.

2. `chaos-logs/`
- Reason: remains empty until experiment runs are documented.

## Validation Run Notes

- `bash -n scripts/setup.sh`: pass
- `python3 -m json.tool k8s/grafana-dashboards/openleaf-overview.json`: pass
- `python3 -m py_compile services/tests/test_scaffold.py`: pass
- `python3 -m py_compile services/tests/test_endpoints.py`: pass
- `pytest` runtime not executed in this shell because `pytest` is not installed locally in the current environment.

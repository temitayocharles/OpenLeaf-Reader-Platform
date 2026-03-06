Apply order suggested by the guide:
1) Runtime config (`app-config.yaml`, `app-secrets.local.yaml`)
2) Core service deployments/services/HPA/PDB
3) Kong plugins + ingress
4) Hardened Kong route
5) Chaos manifests (only when ready to test)

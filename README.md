# Bangi Monorepo

Bangi is now organized as a monorepo with separate application boundaries for the API and web UI.

## Repository layout

- `apps/api` Flask backend API
- `apps/web` Mithril frontend dashboard
- `infra` shared runtime infrastructure such as MariaDB and Nginx config
- `landings` local uploaded landing page assets used by the development environment
- `_bmad` BMAD workflows and project-level agent assets
- `_bmad-output` generated BMAD artifacts
- `.github/workflows` CI pipelines

## Working with the apps

### Backend API

From the repository root:

```bash
make api-test
make api-lint
make api-pytest
docker compose up
```

Or work directly inside `apps/api`.

### Web UI

From the repository root:

```bash
make web-install
make web-build
make web-start
make web-openapi-check
```

Or work directly inside `apps/web`.

## Monorepo rules

- Applications stay isolated under `apps/`
- Backend and frontend keep separate tooling and dependency graphs
- Shared runtime/service configuration lives under `infra/`
- BMAD/spec/process assets live at the repository root
- Cross-stack feature PRs are allowed, but the app boundaries stay explicit

## Host Provisioning

Fresh Ubuntu 24.04 LTS host installation starts from the pinned installer documented in
[docs/host-provisioning.md](docs/host-provisioning.md).

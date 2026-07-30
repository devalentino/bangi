# Bangi Monorepo

Bangi (Bangi CPA Tracker) is a self-hosted CPA tracker for learning, testing, and running early CPA campaigns without paying for an expensive tracker subscription before the traffic is profitable. Install it on a small VPS, connect your own domains, send traffic to landing pages or redirects, receive leads and postbacks, and read the numbers that tell you whether a campaign is working.

Bangi does not try to match every feature of mature commercial trackers. The goal is to cover the core workflow clearly and keep the fixed cost low while you test offers, traffic sources, landing pages, and routing ideas.

With Bangi you can:

- Route ad traffic through a campaign domain, using flows and rules to split visitors by country, device, browser, bot status, or split-test percentage.
- Host a landing page inside the tracker or redirect visitors to an external page.
- Receive lead and postback events from advertiser or affiliate systems.
- Compare clicks, leads, payouts, expenses, profit, and ROI in the statistics report.
- Monitor system health, certificates, and campaign discards from the dashboard.

This repository holds the application code (API and web UI).

This monorepo is organized with separate application boundaries for the API and web UI.

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

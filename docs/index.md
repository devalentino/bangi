# bangi-backend Documentation Index

**Type:** Monorepo with 2 application parts  
**Primary Languages:** Python and JavaScript  
**Architecture:** API backend + browser dashboard with shared local runtime infrastructure  
**Last Updated:** 2026-04-14

## Project Overview

Bangi is a monorepo for a CPA tracking product. The backend exposes a Flask API for authentication, campaign and flow management, tracking, reports, alerts, and Facebook PACS integrations. The web app is a Mithril dashboard that consumes that API and presents the operational interface. Shared infrastructure lives at the repository root, including Docker Compose, MariaDB tuning, Nginx config, and local landing-page assets.

## Project Structure

### Backend API (`api`)

- **Type:** backend
- **Location:** `apps/api`
- **Stack:** Python 3.12, Flask, Flask-Smorest, Peewee, MariaDB, Pytest
- **Entry Point:** `apps/api/src/api.py`

### Web UI (`web`)

- **Type:** web
- **Location:** `apps/web`
- **Stack:** JavaScript, Mithril, esbuild, Chart.js
- **Entry Point:** `apps/web/index.js`

## Cross-Part Integration

- The web app calls the backend using `BACKEND_API_BASE_URL` from `app-config.js`.
- The backend serves the domain API under `/api/v2/*` and exposes Swagger UI under `/openapi/swagger-ui`.
- Local development depends on MariaDB and a PHP-based landing renderer through `docker-compose.yml`.

## Generated Documentation

- [Project Overview](./project-overview.md) - High-level classification, stack, and development summary
- [Source Tree Analysis](./source-tree-analysis.md) - Directory map and critical folders
- [Project Parts Metadata](./project-parts.json) - Machine-readable monorepo structure
- [Project Scan State](./project-scan-report.json) - Workflow state for future refreshes

## Existing Documentation

- [README.md](../README.md) - Monorepo orientation and top-level commands
- [apps/api/README.md](../apps/api/README.md) - Backend setup, migrations, and test commands
- [apps/web/README.md](../apps/web/README.md) - Frontend setup, bundling, and runtime config

## Getting Started

### Backend API

- **Lint:** `make api-lint`
- **Tests:** `make api-pytest`
- **Migrations:** `make api-migrate`

### Web UI

- **Install:** `make web-install`
- **Build:** `make web-build`
- **Dev Watch:** `make web-start`
- **OpenAPI Check:** `make web-openapi-check`

### Local Runtime

```bash
docker compose up
```

## How To Use This With BMad

- Use this doc set as the baseline context before choosing a small bugfix or improvement.
- For tiny implementation work, the next practical step is `bmad-quick-dev`.
- If you later want stronger AI context for coding, run `bmad-generate-project-context` after this first documentation pass.

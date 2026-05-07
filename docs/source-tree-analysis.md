# bangi-backend - Source Tree Analysis

**Date:** 2026-04-14

## Overview

The repository is organized as a two-app monorepo with shared infrastructure and product assets at the root. The critical engineering paths are `apps/api` for the Flask backend, `apps/web` for the Mithril dashboard, `infra` for runtime configuration, and `landings` for local landing-page content.

## Multi-Part Structure

- **Backend API** (`apps/api`): tracking/reporting/authentication/business logic
- **Web UI** (`apps/web`): browser dashboard and API client

## Complete Directory Structure

```text
.
├── .agents/
├── .github/
│   └── workflows/
│       └── pr-pipelines.yaml
├── _bmad/
├── apps/
│   ├── api/
│   │   ├── migrations/
│   │   ├── perf/
│   │   ├── src/
│   │   │   ├── alerts/
│   │   │   ├── auth/
│   │   │   ├── core/
│   │   │   ├── facebook_pacs/
│   │   │   ├── health/
│   │   │   ├── reports/
│   │   │   └── tracker/
│   │   └── tests/
│   │       └── integration/
│   └── web/
│       ├── bin/
│       ├── css/
│       ├── lib/
│       ├── scripts/
│       ├── src/
│       │   ├── components/
│       │   ├── models/
│       │   ├── utils/
│       │   └── views/
│       └── styles/
├── docs/
├── infra/
│   ├── mariadb/
│   └── nginx/
├── landings/
│   └── 1/
├── docker-compose.yml
├── Makefile
└── README.md
```

## Critical Directories

### `apps/api/src`

Primary backend source tree.

**Purpose:** Holds the Flask application, domain routes, schemas, services, repositories, and core utilities.  
**Contains:** auth, core business entities, tracking, reporting, alerts, Facebook PACS integrations.  
**Entry Points:** `apps/api/src/api.py`, `apps/api/src/container.py`

### `apps/api/tests/integration`

Backend integration test suite.

**Purpose:** Verifies endpoint behavior and domain workflows against the API stack.  
**Contains:** domain-grouped test modules for auth, core, facebook_pacs, reports, and track flows.

### `apps/api/migrations`

Database evolution history.

**Purpose:** Tracks schema changes for MariaDB using migration scripts.  
**Contains:** numbered migration files describing schema increments.

### `apps/web/src`

Primary frontend source tree.

**Purpose:** Holds dashboard routes, page views, data models, and shared components.  
**Contains:** `views/` for route pages, `models/` for API-facing client logic, `components/` for reusable UI pieces.  
**Entry Points:** `apps/web/index.js`

### `apps/web/scripts`

Frontend build and API-sync utilities.

**Purpose:** Encapsulates esbuild bundling and OpenAPI cache utilities.  
**Contains:** `esbuild.js`, `openapi.js`

### `infra`

Shared runtime infrastructure.

**Purpose:** Stores service-level configuration used by local runtime or deployments.  
**Contains:** MariaDB tuning and Nginx config.  
**Integration:** Used by Docker Compose and image/runtime setup.

### `landings`

Landing-page content storage.

**Purpose:** Stores local uploaded landing assets and PHP pages used by the landing renderer service.  
**Contains:** page variants, static assets, and configuration PHP files.

### `_bmad`

BMad framework installation.

**Purpose:** Provides structured planning, documentation, and implementation workflows inside the repo.  
**Contains:** module manifests, configuration, and workflow help tables.

## Entry Points

### Backend API

- **Entry Point:** `apps/api/src/api.py`
- **Bootstrap:** Creates the Flask app, configures JSON/CORS/OpenAPI, and registers domain blueprints.

### Web UI

- **Entry Point:** `apps/web/index.js`
- **Bootstrap:** Loads CSS, configures Mithril routes, and wraps most pages in an authenticated layout.

## File Organization Patterns

- Backend code is domain-first: each domain owns routes, services, schemas, and related support code.
- Frontend code is page- and model-oriented: route views pair with model files that wrap backend interaction.
- Root-level files control shared workflows: compose, CI, BMad configuration, and repository commands.
- Infrastructure and runtime assets remain outside app folders, so environment changes can affect both apps.

## Key File Types

### Python backend source

- **Pattern:** `apps/api/src/**/*.py`
- **Purpose:** API routes, service layer, domain entities, repositories, and runtime wiring
- **Examples:** `apps/api/src/api.py`, `apps/api/src/reports/services.py`

### Backend tests

- **Pattern:** `apps/api/tests/integration/**/*.py`
- **Purpose:** Integration verification across domain routes and behavior
- **Examples:** `apps/api/tests/integration/test_auth.py`, `apps/api/tests/integration/track/test_click.py`

### Frontend views and models

- **Pattern:** `apps/web/src/{views,models,components}/**/*.js`
- **Purpose:** Client routes, API access models, and reusable dashboard UI
- **Examples:** `apps/web/src/views/statistics.js`, `apps/web/src/models/api.js`

### Runtime configuration

- **Pattern:** `docker-compose.yml`, `infra/**/*.cnf`, `infra/**/*.conf`, `.env`
- **Purpose:** Local orchestration and service configuration
- **Examples:** `docker-compose.yml`, `infra/nginx/nginx.conf`

## Configuration Files

- **`.env`**: local development environment variables for backend, database, and frontend runtime API URL
- **`docker-compose.yml`**: local service orchestration for MariaDB, backend, and landing renderer
- **`apps/api/pyproject.toml`**: minimal backend project metadata and pytest path configuration
- **`apps/web/package.json`**: frontend dependencies and build scripts
- **`.github/workflows/pr-pipelines.yaml`**: backend formatting, lint, and test checks in pull requests

## Notes for Development

- The backend test and lint workflows are more mature than the frontend test posture; that makes backend bugfixes a good first BMad exercise.
- The frontend has a clear route map and model/view mirroring, which is useful for tracing small UI issues once you pick a screen.
- `landings/` and `infra/` are operationally important but should usually stay out of the first small improvement unless the bug is environment-specific.

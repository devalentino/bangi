# bangi-backend - Project Overview

**Date:** 2026-04-14  
**Type:** Multi-part monorepo  
**Architecture:** Flask API and Mithril dashboard with shared local runtime services

## Executive Summary

This repository contains the operational software for Bangi CPA tracking. It combines a Python backend focused on tracking and reporting workflows with a JavaScript dashboard used to manage campaigns, PACS entities, alerts, and reports. The repository also stores runtime assets such as landing pages, MariaDB configuration, and container orchestration needed for local development.

## Project Classification

- **Repository Type:** monorepo
- **Project Types:** backend API, web dashboard
- **Primary Languages:** Python, JavaScript
- **Architecture Pattern:** modular backend services plus a client-side routed single-page app

## Multi-Part Structure

### Backend API

- **Type:** backend
- **Location:** `apps/api`
- **Purpose:** exposes authenticated APIs for tracking, reporting, alerts, core entities, and Facebook PACS operations
- **Tech Stack:** Python 3.12, Flask, Flask-Smorest, Peewee ORM, MariaDB, Pytest

### Web UI

- **Type:** web
- **Location:** `apps/web`
- **Purpose:** provides the internal dashboard for sign-in, statistics, reports, campaigns, flows, and Facebook PACS management
- **Tech Stack:** JavaScript, Mithril, esbuild, Chart.js, SortableJS, Tabulator

### How Parts Integrate

The web app is configured at runtime through `app-config.js` and consumes the backend API through a configurable base URL. The backend composes route blueprints under `/api/v2/*` and depends on MariaDB plus local assets such as landing pages and the IP2Location database. Docker Compose currently orchestrates MariaDB, the backend container, and a PHP landing renderer for local environments.

## Technology Stack Summary

### Backend API Stack

| Category | Technology | Notes |
| --- | --- | --- |
| Language | Python 3.12 | Declared in README and CI |
| Web framework | Flask | Main application object in `src/api.py` |
| API layer | Flask-Smorest | OpenAPI and blueprint registration |
| Persistence | Peewee | ORM and database proxy wiring |
| Database | MariaDB | Local dev and CI service dependency |
| DI / composition | wireup | Service container in `src/container.py` |
| Testing | Pytest | Integration-heavy test suite under `apps/api/tests` |

### Web UI Stack

| Category | Technology | Notes |
| --- | --- | --- |
| Language | JavaScript | CommonJS-style source layout |
| UI framework | Mithril | Route table starts in `index.js` |
| Bundler | esbuild | Custom build script in `scripts/esbuild.js` |
| Data visualization | Chart.js | Used for reporting/statistics views |
| API config | `app-config.js` | Runtime backend URL injection |
| Package manager | npm | Lockfile committed in repo |

## Key Features

- Basic-auth-backed sign-in flow for the dashboard
- Tracking and processing endpoints for clicks and leads
- Reporting modules for expenses, leads, and statistics
- Core campaign and flow management
- Facebook PACS business portfolio, business page, ad cabinet, campaign, and executor management
- Alerting support around business portfolio access URL expiry

## Architecture Highlights

- Backend modules are organized by domain: `auth`, `core`, `tracker`, `reports`, `alerts`, and `facebook_pacs`.
- The Flask app registers each domain as a separate blueprint, keeping the route map explicit.
- The backend container wires services through a central dependency container, which is a useful seam for small fixes and incremental refactors.
- The web app mirrors backend domains in its `models/` and `views/` folders, which lowers navigation cost when tracing bugs across API and UI.
- Shared runtime concerns are still centralized at repo root, so cross-cutting changes often touch both an app folder and infrastructure files.

## Development Overview

### Prerequisites

- Python 3.12 for `apps/api`
- Node.js 20+ for `apps/web`
- Docker and Docker Compose for the local runtime stack
- MariaDB-compatible environment variables in the root `.env`

### Getting Started

Read the root README first, then work inside the app you are changing. Backend workflows mostly run via the `apps/api` Makefile, while frontend workflows run through npm scripts from `apps/web`. For local end-to-end behavior, the current setup expects Docker Compose.

### Key Commands

#### Backend API

- **Install:** `pip install -r requirements.txt && pip install -r requirements-dev.txt`
- **Dev/Test:** `make -C apps/api pytest`
- **Lint:** `make -C apps/api lint`

#### Web UI

- **Install:** `npm --prefix apps/web ci`
- **Dev:** `npm --prefix apps/web run start`
- **Build:** `npm --prefix apps/web run build`

## Repository Structure

The repository is intentionally split by application boundary. `apps/api` holds the backend, `apps/web` holds the dashboard, `infra` holds shared runtime configuration, `landings` stores uploaded/local landing assets, and `_bmad` contains the installed BMad framework assets and workflow configuration.

## Documentation Map

- [index.md](./index.md) - Master documentation index
- [source-tree-analysis.md](./source-tree-analysis.md) - Directory structure and critical folders
- [project-parts.json](./project-parts.json) - Machine-readable project part inventory

# Bangi UI

Frontend dashboard application of Bangi CPA tracker. Built with Mithril and bundled with esbuild.

This application now lives inside the Bangi monorepo at `apps/web`.

## Project Overview

- Entry point: `index.html` + `index.js`
- Source code: `src/`
- Production bundle output: `bin/main.js`
- API base URL defaults to `/api/v2` and can be overridden at runtime via `app-config.js`

## Local Development

### Prerequisites

- Node.js 20+
- npm

### Install

From `apps/web`:

```bash
npm ci
```

### Build

From `apps/web`:

```bash
npm run build
```

### Watch Mode

From `apps/web`:

```bash
npm run start
```

## Configuration

### Runtime API URL (post-deploy configurable)

The app uses `/api/v2` by default. For custom deployments, override it with:

- `window.APP_CONFIG.BACKEND_API_BASE_URL` from `app-config.js`
- `window.APP_CONFIG.DEBUG_PERSIST_AUTH` from `app-config.js`

Example:

```js
window.APP_CONFIG = window.APP_CONFIG || {
  BACKEND_API_BASE_URL: "http://localhost:8080",
  DEBUG_PERSIST_AUTH: false,
};
```

## Docker

The repo includes a multi-stage Docker build:

- Build stage: Node + esbuild
- Runtime stage: Nginx serving static assets
- The pre-built image works without `BACKEND_API_BASE_URL` when the host routes `/api/v2` to the backend.

### Build Image

#### Development

From the monorepo root:

```bash
docker build -f apps/web/Dockerfile -t ghcr.io/devalentino/bangi-web:dev-$(git rev-parse --short HEAD) .
```

Deploy Image

```bash
docker push ghcr.io/devalentino/bangi-web:dev-$(git rev-parse --short HEAD)
```

#### Release

From the monorepo root:

```bash
docker build -f apps/web/Dockerfile -t ghcr.io/devalentino/bangi-web:$(git describe --tags --exact-match) .
```

Deploy Image

```bash
docker push ghcr.io/devalentino/bangi-web:$(git describe --tags --exact-match)
```

## Deploy Notes

- Override `app-config.js` when a deployment needs a non-default API URL.
- For non-Docker deployments, edit `app-config.js` on the server and reload the page.

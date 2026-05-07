# Bangi Backend API

This application now lives inside the Bangi monorepo at `apps/api`.

Backend for Bangi CPA.

## Tech stack

- Python 3.12
- Flask + Flask-Smorest (OpenAPI/Swagger)
- Peewee ORM + `peewee-migrate`
- MariaDB
- Gunicorn
- Pytest

## Project structure

- `src/` application code (`auth`, `core`, `facebook_pacs`, `reports`, `tracker`, `health`)
- `tests/integration/` integration test suite
- `migrations/` database migrations
- `Dockerfile` backend container image

The `landings/` directory lives at the monorepo root because it stores local uploaded assets rather than API source code.

## Environment variables

This project uses the monorepo root `.env` file for local development (already included in `Makefile` and `docker-compose.yml`).

Main variables used by the backend:

- `MARIADB_HOST`
- `MARIADB_PORT`
- `MARIADB_USER`
- `MARIADB_PASSWORD`
- `MARIADB_DATABASE`
- `BASIC_AUTHENTICATION_USERNAME`
- `BASIC_AUTHENTICATION_PASSWORD`
- `LANDING_PAGES_BASE_PATH`
- `IP2LOCATION_DB_PATH`
- `LANDING_PAGE_RENDERER_BASE_URL`
- `INTERNAL_PROCESS_BASE_URL`

## Database migrations

Apply migrations from `apps/api`:

```bash
make migrate
```

Generate a migration:

```bash
make generate-migration name=<migration_name>
```

## Testing and linting

Run integration tests from `apps/api`:

```bash
make pytest
```

Run full checks (format checks + lint + tests) from `apps/api`:

```bash
make test
```

Format and lint from `apps/api`:

```bash
make lint
```

## Build Image

### Development

Build the latest development image on the `develop` branch

```bash
docker build -f Dockerfile -t ghcr.io/devalentino/bangi-api:dev-$(git rev-parse --short HEAD) .
```

## Deploy Image
```bash
docker push ghcr.io/devalentino/bangi-api:dev-$(git rev-parse --short HEAD)
```

### Release

For release please merge code to the `master` and create tag. Then build image with the tag

```bash
docker build -f Dockerfile -t ghcr.io/devalentino/bangi-api:$(git describe --tags --exact-match) .
```

## Deploy Image
```bash
docker push ghcr.io/devalentino/bangi-api:$(git describe --tags --exact-match)
```

## Useful endpoints:

- Health check: `/api/v2/health`
- Disk utilization history: `/api/v2/health/disk-utilization/history?days=30`
- OpenAPI docs: `/openapi/swagger-ui`

## Storage monitoring ingestion

The internal disk telemetry command lives at:

```bash
python -m src.health.ingest.disk_utilization \
  --filesystem "/dev/sda1" \
  --mountpoint "/var/lib/docker" \
  --total-bytes 21474836480 \
  --used-bytes 15032385536 \
  --available-bytes 6442450944 \
  --used-percent 70.0
```

The host-side wrapper script and cron setup notes live in [`infra/scripts/README.md`](../../infra/scripts/README.md).

# Bangi Backend

Backend for Bangi CPA Tracker.

## Architecture and runtime goals

This application is intentionally tuned for low memory consumption. It is expected to run on a low-cost VDS with only 512 MB RAM, so the backend is designed to keep the number of moving parts and background components to a minimum.

The application is also designed so that API Gateway endpoints respond as fast as possible. Because the service runs with a minimal number of Gunicorn workers, time-consuming work such as aggregations, database writes, and database updates should be delegated to background workers instead of being handled in the request-response path.

Architecture diagram:

- https://drive.google.com/file/d/13CfFY14BtT2e4UQYVebablKzKO9AsOd5/view?usp=sharing

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
- `infra/core.Dockerfile` backend container image

## Environment variables

This project uses a local `.env` file (already included in `Makefile` and `docker-compose.yml`).

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

Apply migrations:

```bash
make migrate
```

Generate a migration:

```bash
make generate-migration name=<migration_name>
```

## Testing and linting

Run integration tests:

```bash
make pytest
```

Run full checks (format checks + lint + tests):

```bash
make test
```

Format and lint:

```bash
make lint
```

## Build Image

### Development

Build the latest development image on the `develop` branch

```bash
docker build -f infra/core.Dockerfile -t ghcr.io/devalentino/bangi-backend:dev-$(git rev-parse --short HEAD) .
```

## Deploy Image
```bash
docker push ghcr.io/devalentino/bangi-backend:dev-$(git rev-parse --short HEAD)
```

### Release

For release please merge code to the `master` and create tag. Then build image with the tag

```bash
docker build -f infra/core.Dockerfile -t ghcr.io/devalentino/bangi-backend:$(git describe --tags --exact-match) .
```

## Deploy Image
```bash
docker push ghcr.io/devalentino/bangi-backend:$(git describe --tags --exact-match)
```

## Useful endpoints:

- Health check: `/api/v2/health`
- OpenAPI docs: `/openapi/swagger-ui`

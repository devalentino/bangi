# Bangi Backend

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

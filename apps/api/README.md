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

## Development

### Reaching a remote database over SSH

Staging and other external hosts do not publish the MariaDB port. The `mariadb`
container is only reachable on the internal `bangi` Docker network, and the host
firewall drops inbound traffic to everything except ports 22, 80, and 443. To run
seed scripts, apply an ad-hoc migration, or connect a database GUI against such a
host, publish the container port to the host loopback and forward it over SSH.
This exposes nothing publicly and needs no firewall change.

#### Step 1 — publish MariaDB to loopback on the host

On the remote host, add a loopback-only port mapping to the running compose file
(`/opt/bangi/current/compose.yml`):

```yaml
  mariadb:
    image: mariadb:latest
    restart: always
    ports:
      - '127.0.0.1:3306:3306'
```

Recreate the container and confirm the mapping is live:

```bash
docker ps --format '{{.Names}}\t{{.Ports}}' | grep -i maria
# expected: 127.0.0.1:3306->3306/tcp
```

Loopback-published ports are not routed through the `BANGI-DOCKER-USER` firewall
chain, so the host firewall stays closed. This edit lives in the per-release
compose copy and is reset on the next deploy — re-apply it when you need the
tunnel again, or fold it into the deployed template if the access is permanent.

#### Step 2 — open the tunnel from your machine

```bash
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 3306:127.0.0.1:3306 root@YOUR_SERVER_IP
```

Flags:

- `-N` — no remote shell; SSH just holds the tunnel open. The terminal will
  appear to hang. Keep it open; closing it drops the connection.
- `-L 3306:127.0.0.1:3306` — maps `127.0.0.1:3306` on your machine to
  `127.0.0.1:3306` on the remote host, where Docker published the container port.
- `-o ExitOnForwardFailure=yes` — fail immediately if the forward cannot be set
  up, instead of connecting with no tunnel.
- `-o ServerAliveInterval=30` — keep-alive so idle tunnels are not silently
  dropped.

#### Step 3 — connect through the tunnel

With the tunnel open, use a second terminal.

CLI:

```bash
mariadb -h 127.0.0.1 -P 3306 -u <db_user> -p
```

Use `-h 127.0.0.1`, not `localhost`. `localhost` makes the client look for a
local Unix socket instead of the forwarded TCP port.


#### Teardown and troubleshooting

- Close the tunnel: `Ctrl+C` in the `ssh -N` terminal.
- `docker ps` shows `3306/tcp` without a `127.0.0.1:3306->` prefix — the port
  mapping is not in effect. Re-check the edit to `/opt/bangi/current/compose.yml`
  and rerun the `up -d mariadb` recreate.
- `ERROR 2013 (HY000): Lost connection ... reading initial communication packet`
  — the client reached a local server instead of the tunnel because `ssh -L`
  could not bind port `3306`. Use `13306:` as above and connect with `-P 13306`.
- `bind: Address already in use` — local port taken; use `13306:` as above.
- `channel 2: open failed: connect failed` — nothing is listening on the remote
  `127.0.0.1:3306`; Step 1 did not take.

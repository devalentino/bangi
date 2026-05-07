# Storage Monitoring Scripts

## Disk utilization ingestion

`ingest_disk_utilization.sh` collects host disk telemetry with `df`, normalizes it, and pushes it into the backend through the internal command:

```bash
docker compose exec -T api python -m src.health.ingest.disk_utilization ...
```

Default behavior:

- `MONITOR_PATH=/var/lib/docker`
- `COMPOSE_SERVICE=api`
- `PYTHON_BIN=python`
- `DOCKER_COMPOSE_BIN="docker compose"`

Manual run from the repo root:

```bash
./infra/scripts/ingest_disk_utilization.sh
```

Example cron entry for hourly collection:

```cron
0 * * * * cd /path/to/bangi && ./infra/scripts/ingest_disk_utilization.sh >> /var/log/bangi-disk-utilization.log 2>&1
```

Operational notes:

- run the script on the Docker host, not inside the container
- a non-zero exit code means ingestion failed and cron should treat it as an error
- override `MONITOR_PATH` if Bangi data lives on a different host mount

## IP2Location refresh

`refresh_ip2location_db.sh` downloads the IP2Location LITE DB1 IPv6 archive, validates it, atomically replaces the managed database file, and restarts the API service after a successful replacement.

The installer schedules it only when `/etc/bangi/ops.env` contains `IP2LOCATION_DOWNLOAD_TOKEN`. Cron sources `/etc/bangi/ops.env`; the token is not written into `/etc/cron.d/bangi`.

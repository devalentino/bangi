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
./scripts/ingest_disk_utilization.sh
```

Example cron entry for hourly collection:

```cron
0 * * * * cd /path/to/bangi && ./scripts/ingest_disk_utilization.sh >> /var/log/bangi-disk-utilization.log 2>&1
```

Operational notes:

- run the script on the Docker host, not inside the container
- a non-zero exit code means ingestion failed and cron should treat it as an error
- override `MONITOR_PATH` if Bangi data lives on a different host mount

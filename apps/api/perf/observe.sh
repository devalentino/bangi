#!/usr/bin/env bash

set -euo pipefail

OUT_DIR="${1:-perf/out}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-5}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

stats_file="$OUT_DIR/docker-stats.csv"
health_file="$OUT_DIR/container-health.log"
logs_file="$OUT_DIR/compose-logs.log"

echo "timestamp,name,cpu_perc,mem_usage,mem_perc,net_io,block_io,pids" > "$stats_file"
: > "$health_file"
: > "$logs_file"

collect_stats() {
  while true; do
    docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}" \
      | while IFS= read -r line; do
          printf '%s,%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$line"
        done >> "$stats_file"
    sleep "$INTERVAL_SECONDS"
  done
}

collect_health() {
  while true; do
    docker compose ps >> "$health_file" 2>&1
    echo "--- $(date -u +%Y-%m-%dT%H:%M:%SZ) ---" >> "$health_file"
    sleep "$INTERVAL_SECONDS"
  done
}

stream_logs() {
  docker compose logs -f --since "$STARTED_AT" --timestamps backend mariadb >> "$logs_file" 2>&1
}

cleanup() {
  kill "$stats_pid" "$health_pid" "$logs_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

collect_stats &
stats_pid=$!

collect_health &
health_pid=$!

stream_logs &
logs_pid=$!

wait

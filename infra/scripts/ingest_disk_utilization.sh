#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

MONITOR_PATH="${MONITOR_PATH:-/var/lib/docker}"
COMPOSE_SERVICE="${COMPOSE_SERVICE:-api}"
PYTHON_BIN="${PYTHON_BIN:-python}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-docker compose}"
DOCKER_COMPOSE_PROJECT_NAME="${DOCKER_COMPOSE_PROJECT_NAME:-bangi}"

if [[ ! -d "${MONITOR_PATH}" && ! -e "${MONITOR_PATH}" ]]; then
  echo "MONITOR_PATH does not exist: ${MONITOR_PATH}" >&2
  exit 1
fi

mapfile -t DF_VALUES < <(df -B1 -P "${MONITOR_PATH}" | awk 'NR==2 {print $1; print $2; print $3; print $4; print $6}')

if [[ "${#DF_VALUES[@]}" -ne 5 ]]; then
  echo "Failed to read disk metrics for ${MONITOR_PATH}" >&2
  exit 1
fi

FILESYSTEM="${DF_VALUES[0]}"
TOTAL_BYTES="${DF_VALUES[1]}"
USED_BYTES="${DF_VALUES[2]}"
AVAILABLE_BYTES="${DF_VALUES[3]}"
MOUNTPOINT="${DF_VALUES[4]}"
USED_PERCENT="$(awk -v used="${USED_BYTES}" -v total="${TOTAL_BYTES}" 'BEGIN { if (total == 0) { print "0.00"; exit } printf "%.2f", (used / total) * 100 }')"

cd "${REPO_ROOT}"
${DOCKER_COMPOSE_BIN} \
  --project-name "${DOCKER_COMPOSE_PROJECT_NAME}" \
  --project-directory "${REPO_ROOT}" \
  -f "${REPO_ROOT}/compose.yml" \
  exec -T "${COMPOSE_SERVICE}" "${PYTHON_BIN}" -m src.health.ingest.disk_utilization \
  --filesystem "${FILESYSTEM}" \
  --mountpoint "${MOUNTPOINT}" \
  --total-bytes "${TOTAL_BYTES}" \
  --used-bytes "${USED_BYTES}" \
  --available-bytes "${AVAILABLE_BYTES}" \
  --used-percent "${USED_PERCENT}"

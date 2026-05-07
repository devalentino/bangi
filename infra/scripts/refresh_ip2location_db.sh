#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

IP2LOCATION_DOWNLOAD_FILE="${IP2LOCATION_DOWNLOAD_FILE:-DB1LITEBINIPV6}"
IP2LOCATION_DATABASE_FILE="${IP2LOCATION_DATABASE_FILE:-IP2LOCATION-LITE-DB1.IPV6.BIN}"
IP2LOCATION_DB_DIR="${IP2LOCATION_DB_DIR:-/opt/bangi/shared/ip2location}"
IP2LOCATION_DOWNLOAD_MAX_TIME="${IP2LOCATION_DOWNLOAD_MAX_TIME:-300}"
COMPOSE_SERVICE="${COMPOSE_SERVICE:-api}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-docker compose}"
DOCKER_COMPOSE_PROJECT_NAME="${DOCKER_COMPOSE_PROJECT_NAME:-bangi}"
OPS_ENV_FILE="${OPS_ENV_FILE:-/etc/bangi/ops.env}"

if [[ -z "${IP2LOCATION_DOWNLOAD_TOKEN:-}" && -f "${OPS_ENV_FILE}" ]]; then
  # shellcheck source=/dev/null
  source "${OPS_ENV_FILE}"
fi

if [[ -z "${IP2LOCATION_DOWNLOAD_TOKEN:-}" ]]; then
  echo "IP2LOCATION_DOWNLOAD_TOKEN is required" >&2
  exit 1
fi

TEMP_DIR="$(mktemp -d)"
ZIP_PATH="${TEMP_DIR}/ip2location.zip"
TEMP_DATABASE_PATH="${IP2LOCATION_DB_DIR}/${IP2LOCATION_DATABASE_FILE}.tmp"
DATABASE_PATH="${IP2LOCATION_DB_DIR}/${IP2LOCATION_DATABASE_FILE}"

cleanup() {
  rm -rf "${TEMP_DIR}"
  rm -f "${TEMP_DATABASE_PATH}"
}
trap cleanup EXIT

install -d -m 0755 -o root -g root "${IP2LOCATION_DB_DIR}"

curl -fL --max-time "${IP2LOCATION_DOWNLOAD_MAX_TIME}" \
  "https://www.ip2location.com/download?token=${IP2LOCATION_DOWNLOAD_TOKEN}&file=${IP2LOCATION_DOWNLOAD_FILE}" \
  -o "${ZIP_PATH}"

unzip -tq "${ZIP_PATH}" >/dev/null

DATABASE_MEMBER="$(unzip -Z -1 "${ZIP_PATH}" | awk -F/ -v database_file="${IP2LOCATION_DATABASE_FILE}" '$NF == database_file { print; exit }')"
if [[ -z "${DATABASE_MEMBER}" ]]; then
  echo "IP2Location archive does not contain ${IP2LOCATION_DATABASE_FILE}" >&2
  exit 1
fi

unzip -p "${ZIP_PATH}" "${DATABASE_MEMBER}" >"${TEMP_DATABASE_PATH}"
chown root:root "${TEMP_DATABASE_PATH}"
chmod 0644 "${TEMP_DATABASE_PATH}"
mv -f "${TEMP_DATABASE_PATH}" "${DATABASE_PATH}"

cd "${REPO_ROOT}"
${DOCKER_COMPOSE_BIN} \
  --project-name "${DOCKER_COMPOSE_PROJECT_NAME}" \
  --project-directory "${REPO_ROOT}" \
  -f "${REPO_ROOT}/compose.yml" \
  restart "${COMPOSE_SERVICE}"

#!/usr/bin/env bash

BANGI_COMPOSE_FILE="${BANGI_RELEASE_DIR}/compose.yml"
BANGI_COMPOSE_PROJECT_NAME="bangi"

bangi_compose() {
    docker compose \
        --project-name "${BANGI_COMPOSE_PROJECT_NAME}" \
        --project-directory "${BANGI_RELEASE_DIR}" \
        -f "${BANGI_COMPOSE_FILE}" \
        "$@"
}

bangi_install_compose() {
    bangi_log "Validating production Docker Compose assets"

    [[ -f "${BANGI_COMPOSE_FILE}" ]] \
        || bangi_fatal "Production compose file is missing: ${BANGI_COMPOSE_FILE}"
    [[ -s "${BANGI_RUNTIME_ENV_FILE}" ]] \
        || bangi_fatal "Runtime environment file is missing or empty: ${BANGI_RUNTIME_ENV_FILE}"
    [[ -f "${BANGI_RELEASE_MARIADB_DIR}/low-memory.cnf" ]] \
        || bangi_fatal "MariaDB low-memory config is missing: ${BANGI_RELEASE_MARIADB_DIR}/low-memory.cnf"

    bangi_compose config >/dev/null \
        || bangi_fatal "Production compose configuration validation failed"
}

bangi_start_compose() {
    bangi_log "Starting Bangi production Docker Compose stack"

    bangi_compose up -d --remove-orphans \
        || bangi_fatal "Production compose startup failed"
}

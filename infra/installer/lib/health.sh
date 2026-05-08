#!/usr/bin/env bash

BANGI_HEALTH_REQUIRED_SERVICES=(
    web
    api
    mariadb
    landing-renderer
)

bangi_retry_healthcheck() {
    local description="$1"
    local failure_message="$2"
    shift 2

    local attempt=1
    local max_attempts=30

    while (( attempt <= max_attempts )); do
        if "$@"; then
            return 0
        fi

        sleep 2
        attempt=$((attempt + 1))
    done

    bangi_log "${description} did not pass after $((max_attempts * 2)) seconds"
    bangi_compose logs --tail=80 api mariadb >&2 || true
    bangi_fatal "${failure_message}"
}

bangi_verify_compose_services_running() {
    local service=""
    local running_services=""

    bangi_log "Checking Docker Compose service status"
    bangi_compose ps \
        || bangi_fatal "Docker Compose status check failed"

    running_services="$(bangi_compose ps --services --filter status=running)" \
        || bangi_fatal "Docker Compose running-service check failed"

    for service in "${BANGI_HEALTH_REQUIRED_SERVICES[@]}"; do
        if ! grep -Fxq "${service}" <<<"${running_services}"; then
            bangi_fatal "Required Docker Compose service is not running: ${service}"
        fi
    done
}

bangi_verify_mariadb_health() {
    bangi_log "Checking MariaDB health"

    bangi_compose exec -T mariadb sh -ec 'mariadb -u root -p"${MARIADB_ROOT_PASSWORD}" -e "SELECT 1"' >/dev/null \
        || bangi_fatal "MariaDB health check failed"
}

bangi_verify_backend_health() {
    bangi_log "Checking backend health through local compose port"

    bangi_retry_healthcheck \
        "Backend health check through local compose port" \
        "Backend health check failed through local compose port" \
        curl -fsS --max-time 10 http://127.0.0.1:8000/api/v2/health >/dev/null
}

bangi_verify_nginx_health() {
    bangi_log "Checking Nginx configuration and local HTTP routing"

    nginx -t \
        || bangi_fatal "Nginx configuration check failed during health verification"

    bangi_retry_healthcheck \
        "Frontend HTTP check through Nginx" \
        "Frontend HTTP check failed through Nginx" \
        curl -fsS --max-time 10 http://127.0.0.1/ >/dev/null

    bangi_retry_healthcheck \
        "Backend health check through Nginx" \
        "Backend health check failed through Nginx" \
        curl -fsS --max-time 10 http://127.0.0.1/api/v2/health >/dev/null
}

bangi_verify_cron_health() {
    declare -A ops_values=()
    local ip2location_download_token=""

    bangi_log "Checking managed cron installation"

    [[ -f "${BANGI_CRON_FILE}" ]] \
        || bangi_fatal "Managed cron file is missing: ${BANGI_CRON_FILE}"

    grep -Fq "cd ${BANGI_CURRENT_LINK} && scripts/ingest_disk_utilization.sh" "${BANGI_CRON_FILE}" \
        || bangi_fatal "Managed cron file is missing disk telemetry ingestion job"

    bangi_env_load_file "${BANGI_OPS_ENV_FILE}" ops_values
    ip2location_download_token="${ops_values[IP2LOCATION_DOWNLOAD_TOKEN]:-}"

    if [[ -n "${ip2location_download_token}" ]]; then
        grep -Fq ". ${BANGI_OPS_ENV_FILE} && ${BANGI_CURRENT_LINK}/scripts/refresh_ip2location_db.sh" "${BANGI_CRON_FILE}" \
            || bangi_fatal "Managed cron file is missing IP2Location refresh job"
        return 0
    fi

    if grep -Fq "refresh_ip2location_db.sh" "${BANGI_CRON_FILE}"; then
        bangi_fatal "Managed cron file contains IP2Location refresh job without configured token"
    fi
}

bangi_verify_health() {
    bangi_log "Verifying Bangi host health before release activation"

    bangi_verify_compose_services_running
    bangi_verify_mariadb_health
    bangi_verify_backend_health
    bangi_verify_nginx_health
    bangi_verify_cron_health
}

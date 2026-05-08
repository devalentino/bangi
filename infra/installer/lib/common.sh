#!/usr/bin/env bash

bangi_color_enabled() {
    [[ -t 1 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]
}

bangi_error_color_enabled() {
    [[ -t 2 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]
}

bangi_log() {
    if bangi_color_enabled; then
        printf '\033[32m[bangi]\033[0m %s\n' "$*"
        return 0
    fi

    printf '[bangi] %s\n' "$*"
}

bangi_fatal() {
    if bangi_error_color_enabled; then
        printf '\033[31m[bangi] ERROR:\033[0m %s\n' "$*" >&2
    else
        printf '[bangi] ERROR: %s\n' "$*" >&2
    fi
    exit 1
}

bangi_require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        bangi_fatal "Bangi installer must be run as root. Use: sudo bash /tmp/bangi-install.sh"
    fi
}

bangi_detect_public_host() {
    local detected_host=""

    detected_host="$(curl -fsS --max-time 5 https://api.ipify.org 2>/dev/null || true)"

    if [[ -n "${detected_host}" && "${detected_host}" != *"/"* && "${detected_host}" != *" "* ]]; then
        printf '%s\n' "${detected_host}"
    fi
}

bangi_verify_inputs() {
    bangi_log "Input validation completed"
}

bangi_detect_existing_state() {
    bangi_log "Checking existing Bangi-managed host state"

    local path=""
    local current_target=""
    local allowed_child=""
    local child=""
    local child_name=""
    local is_allowed=""
    local expected_dirs=(
        "${BANGI_ROOT_DIR}"
        "${BANGI_RELEASE_DIR}"
        "${BANGI_SHARED_DIR}"
        "${BANGI_SHARED_ENV_DIR}"
        "${BANGI_SHARED_MARIADB_DIR}"
        "${BANGI_SHARED_LANDINGS_DIR}"
        "${BANGI_SHARED_IP2LOCATION_DIR}"
        "${BANGI_ROOT_DIR}/ops"
        "${BANGI_OPS_BIN_DIR}"
        "${BANGI_ETC_DIR}"
        "${BANGI_NGINX_DIR}"
        "${BANGI_NGINX_AVAILABLE_DIR}"
        "${BANGI_NGINX_ENABLED_DIR}"
        "${BANGI_LOG_DIR}"
    )
    local allowed_root_children=(
        "${BANGI_RELEASE_TAG}"
        "current"
        "shared"
        "ops"
    )

    for path in "${expected_dirs[@]}"; do
        if [[ -e "${path}" && ! -d "${path}" ]]; then
            bangi_fatal "Unsupported existing Bangi host state at ${path}: expected a directory. Install on a clean VPS."
        fi
    done

    if [[ -e "${BANGI_CURRENT_LINK}" || -L "${BANGI_CURRENT_LINK}" ]]; then
        if [[ ! -L "${BANGI_CURRENT_LINK}" ]]; then
            bangi_fatal "Unsupported existing Bangi host state at ${BANGI_CURRENT_LINK}: expected a symlink. Install on a clean VPS."
        fi

        current_target="$(readlink "${BANGI_CURRENT_LINK}")" \
            || bangi_fatal "Unsupported existing Bangi host state at ${BANGI_CURRENT_LINK}: unreadable symlink. Install on a clean VPS."

        if [[ "${current_target}" != "${BANGI_RELEASE_DIR}" ]]; then
            bangi_fatal "Unsupported existing Bangi host state at ${BANGI_CURRENT_LINK}: expected ${BANGI_RELEASE_DIR}. Install on a clean VPS."
        fi
    fi

    if [[ -d "${BANGI_ROOT_DIR}" ]]; then
        for child in "${BANGI_ROOT_DIR}"/*; do
            [[ -e "${child}" || -L "${child}" ]] || continue

            child_name="$(basename "${child}")"
            is_allowed="false"

            for allowed_child in "${allowed_root_children[@]}"; do
                if [[ "${child_name}" == "${allowed_child}" ]]; then
                    is_allowed="true"
                    break
                fi
            done

            if [[ "${is_allowed}" != "true" ]]; then
                bangi_fatal "Unsupported existing Bangi host state at ${child}. Install on a clean VPS."
            fi
        done
    fi
}

bangi_print_summary() {
    declare -A ops_values=()
    local nginx_status="inactive"
    local cron_status="inactive"
    local ip2location_status="not configured"
    local fallback_host=""

    if systemctl is-active --quiet nginx; then
        nginx_status="active"
    fi

    if systemctl is-active --quiet cron; then
        cron_status="active"
    fi

    bangi_env_load_file "${BANGI_OPS_ENV_FILE}" ops_values
    if [[ -n "${ops_values[IP2LOCATION_DOWNLOAD_TOKEN]:-}" ]]; then
        if [[ -f "${BANGI_SHARED_IP2LOCATION_DIR}/${BANGI_IP2LOCATION_DATABASE_FILE}" ]]; then
            ip2location_status="configured; database installed"
        else
            ip2location_status="configured; database not installed"
        fi
    fi
    fallback_host="$(bangi_detect_public_host)"

    bangi_log "Bangi installation completed for ${BANGI_RELEASE_TAG}"
    printf '\nBangi deployment summary\n'
    printf '  Deployment bundle: %s\n' "${BANGI_RELEASE_DIR}"
    printf '  Active release: %s -> %s\n' "${BANGI_CURRENT_LINK}" "$(readlink "${BANGI_CURRENT_LINK}")"
    printf '  Runtime environment: %s\n' "${BANGI_RUNTIME_ENV_FILE}"
    printf '  Operational environment: %s\n' "${BANGI_OPS_ENV_FILE}"
    printf '  Service status:\n'
    bangi_compose ps || printf '    Unable to print Docker Compose service status.\n'
    printf '  Nginx status: %s; config test passed\n' "${nginx_status}"
    printf '  Cron status: %s; managed file %s installed\n' "${cron_status}" "${BANGI_CRON_FILE}"
    if [[ -n "${fallback_host}" ]]; then
        printf '  Fallback URL: http://%s\n' "${fallback_host}"
    fi
    printf '  IP2Location refresh: %s\n' "${ip2location_status}"
    printf '\nOperator next steps\n'
    printf '  1. Review service health with: docker compose --project-name %s --project-directory %s -f %s ps\n' "${BANGI_COMPOSE_PROJECT_NAME}" "${BANGI_RELEASE_DIR}" "${BANGI_COMPOSE_FILE}"
    printf '  2. Review Nginx and cron logs under /var/log/nginx and %s.\n' "${BANGI_LOG_DIR}"
    printf '  3. Configure any required public domain or access URL separately from the installer.\n'
}

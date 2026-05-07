#!/usr/bin/env bash

BANGI_IP2LOCATION_DOWNLOAD_FILE="DB1LITEBINIPV6"
BANGI_IP2LOCATION_DOWNLOAD_MAX_TIME=300

bangi_ip2location_download_database() {
    local token="$1"
    local temporary_dir=""
    local zip_path=""
    local database_member=""
    local temporary_database_path=""
    local download_url="https://www.ip2location.com/download?token=${token}&file=${BANGI_IP2LOCATION_DOWNLOAD_FILE}"

    [[ -n "${token}" ]] || return 1

    temporary_dir="$(mktemp -d)" \
        || bangi_fatal "Cannot create temporary directory for IP2Location download"
    zip_path="${temporary_dir}/ip2location.zip"
    temporary_database_path="${BANGI_SHARED_IP2LOCATION_DIR}/${BANGI_IP2LOCATION_DATABASE_FILE}.tmp"

    if ! curl -fL --max-time "${BANGI_IP2LOCATION_DOWNLOAD_MAX_TIME}" "${download_url}" -o "${zip_path}"; then
        rm -rf "${temporary_dir}"
        return 1
    fi

    if ! unzip -tq "${zip_path}" >/dev/null; then
        rm -rf "${temporary_dir}"
        return 1
    fi

    database_member="$(unzip -Z -1 "${zip_path}" | awk -F/ -v database_file="${BANGI_IP2LOCATION_DATABASE_FILE}" '$NF == database_file { print; exit }')"
    if [[ -z "${database_member}" ]]; then
        rm -rf "${temporary_dir}"
        bangi_fatal "IP2Location archive does not contain ${BANGI_IP2LOCATION_DATABASE_FILE}"
    fi

    install -d -m 0755 -o root -g root "${BANGI_SHARED_IP2LOCATION_DIR}" \
        || bangi_fatal "Cannot create IP2Location database directory: ${BANGI_SHARED_IP2LOCATION_DIR}"
    unzip -p "${zip_path}" "${database_member}" >"${temporary_database_path}" \
        || bangi_fatal "Cannot extract IP2Location database from downloaded archive"
    chown root:root "${temporary_database_path}" \
        || bangi_fatal "Cannot set ownership on IP2Location database"
    chmod 0644 "${temporary_database_path}" \
        || bangi_fatal "Cannot set permissions on IP2Location database"
    mv -f "${temporary_database_path}" "${BANGI_SHARED_IP2LOCATION_DIR}/${BANGI_IP2LOCATION_DATABASE_FILE}" \
        || bangi_fatal "Cannot install IP2Location database"

    rm -rf "${temporary_dir}"
}

bangi_install_ip2location_database() {
    declare -A ops_values=()
    local token=""

    bangi_env_load_file "${BANGI_OPS_ENV_FILE}" ops_values
    token="${ops_values[IP2LOCATION_DOWNLOAD_TOKEN]:-}"

    if [[ -z "${token}" ]]; then
        bangi_log "Skipping IP2Location database download; no download token configured"
        return 0
    fi

    if [[ -f "${BANGI_SHARED_IP2LOCATION_DIR}/${BANGI_IP2LOCATION_DATABASE_FILE}" ]]; then
        bangi_log "IP2Location database already exists"
        return 0
    fi

    bangi_log "Downloading IP2Location LITE database"
    bangi_ip2location_download_database "${token}" \
        || bangi_fatal "IP2Location database download failed"
}

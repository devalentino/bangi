#!/usr/bin/env bash

BANGI_CRON_FILE="/etc/cron.d/bangi"

bangi_install_cron() {
    declare -A ops_values=()
    local temporary_path="${BANGI_CRON_FILE}.tmp"
    local ip2location_download_token=""

    bangi_log "Installing managed Bangi cron jobs"

    bangi_env_load_file "${BANGI_OPS_ENV_FILE}" ops_values
    ip2location_download_token="${ops_values[IP2LOCATION_DOWNLOAD_TOKEN]:-}"

    cat >"${temporary_path}" <<EOF \
        || bangi_fatal "Cannot write managed cron file: ${temporary_path}"
# Managed by Bangi installer. Local edits may be overwritten.
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Hourly disk telemetry ingestion for the active Bangi deployment.
0 * * * * root cd ${BANGI_CURRENT_LINK} && scripts/ingest_disk_utilization.sh >> ${BANGI_LOG_DIR}/disk-utilization.log 2>&1
EOF

    if [[ -n "${ip2location_download_token}" ]]; then
        cat >>"${temporary_path}" <<EOF \
            || bangi_fatal "Cannot write IP2Location refresh cron job: ${temporary_path}"

# Semi-monthly IP2Location LITE refresh. Credentials stay in ${BANGI_OPS_ENV_FILE}.
0 3 1,15 * * root . ${BANGI_OPS_ENV_FILE} && ${BANGI_CURRENT_LINK}/scripts/refresh_ip2location_db.sh >> ${BANGI_LOG_DIR}/ip2location-refresh.log 2>&1
EOF
    fi

    chown root:root "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on managed cron file: ${temporary_path}"
    chmod 0644 "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on managed cron file: ${temporary_path}"
    mv -f "${temporary_path}" "${BANGI_CRON_FILE}" \
        || bangi_fatal "Cannot install managed cron file: ${BANGI_CRON_FILE}"
}

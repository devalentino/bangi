#!/usr/bin/env bash

BANGI_ROOT_DIR="/opt/bangi"
BANGI_RELEASE_DIR="${BANGI_ROOT_DIR}/${BANGI_RELEASE_TAG}"
BANGI_CURRENT_LINK="${BANGI_ROOT_DIR}/current"
BANGI_SHARED_DIR="${BANGI_ROOT_DIR}/shared"
BANGI_SHARED_ENV_DIR="${BANGI_SHARED_DIR}/env"
BANGI_SHARED_MARIADB_DIR="${BANGI_SHARED_DIR}/mariadb"
BANGI_SHARED_LANDINGS_DIR="${BANGI_SHARED_DIR}/landings"
BANGI_SHARED_IP2LOCATION_DIR="${BANGI_SHARED_DIR}/ip2location"
BANGI_OPS_BIN_DIR="${BANGI_ROOT_DIR}/ops/bin"
BANGI_RELEASE_INFRA_DIR="${BANGI_RELEASE_DIR}/infra"
BANGI_RELEASE_INSTALLER_DIR="${BANGI_RELEASE_INFRA_DIR}/installer"
BANGI_RELEASE_TEMPLATE_DIR="${BANGI_RELEASE_INSTALLER_DIR}/templates"
BANGI_RELEASE_MARIADB_DIR="${BANGI_RELEASE_INFRA_DIR}/mariadb"
BANGI_RELEASE_SCRIPTS_DIR="${BANGI_RELEASE_DIR}/scripts"
BANGI_ETC_DIR="/etc/bangi"
BANGI_NGINX_DIR="/etc/nginx/bangi"
BANGI_NGINX_AVAILABLE_DIR="/etc/nginx/bangi/sites-available"
BANGI_NGINX_ENABLED_DIR="/etc/nginx/bangi/sites-enabled"
BANGI_LOG_DIR="/var/log/bangi"

bangi_create_paths() {
    local path=""
    local managed_dirs=(
        "${BANGI_RELEASE_DIR}"
        "${BANGI_SHARED_ENV_DIR}"
        "${BANGI_SHARED_MARIADB_DIR}"
        "${BANGI_SHARED_LANDINGS_DIR}"
        "${BANGI_SHARED_IP2LOCATION_DIR}"
        "${BANGI_OPS_BIN_DIR}"
        "${BANGI_RELEASE_TEMPLATE_DIR}"
        "${BANGI_RELEASE_MARIADB_DIR}"
        "${BANGI_RELEASE_SCRIPTS_DIR}"
        "${BANGI_ETC_DIR}"
        "${BANGI_NGINX_AVAILABLE_DIR}"
        "${BANGI_NGINX_ENABLED_DIR}"
        "${BANGI_LOG_DIR}"
    )

    bangi_log "Creating Bangi host directory layout"

    for path in "${managed_dirs[@]}"; do
        install -d -m 0755 -o root -g root "${path}" \
            || bangi_fatal "Path creation failed for ${path}"
    done
}

bangi_activate_release() {
    bangi_log "Release activation phase pending implementation"
}

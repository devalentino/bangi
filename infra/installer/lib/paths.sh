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
BANGI_ETC_DIR="/etc/bangi"
BANGI_NGINX_AVAILABLE_DIR="/etc/nginx/bangi/sites-available"
BANGI_NGINX_ENABLED_DIR="/etc/nginx/bangi/sites-enabled"
BANGI_LOG_DIR="/var/log/bangi"

bangi_create_paths() {
    bangi_log "Path creation phase pending implementation"
}

bangi_activate_release() {
    bangi_log "Release activation phase pending implementation"
}

#!/usr/bin/env bash

BANGI_GITHUB_OWNER="devalentino"
BANGI_GITHUB_REPO="bangi"
BANGI_RAW_BASE_URL="https://raw.githubusercontent.com/${BANGI_GITHUB_OWNER}/${BANGI_GITHUB_REPO}/${BANGI_RELEASE_TAG}"
BANGI_DEPLOYMENT_ASSETS=(
    "infra/installer/templates/compose.prod.yml|${BANGI_RELEASE_DIR}/compose.yml|0644"
    "infra/installer/templates/compose.prod.yml|${BANGI_RELEASE_TEMPLATE_DIR}/compose.prod.yml|0644"
    "infra/installer/templates/nginx.default.conf|${BANGI_RELEASE_TEMPLATE_DIR}/nginx.default.conf|0644"
    "infra/mariadb/low-memory.cnf|${BANGI_RELEASE_MARIADB_DIR}/low-memory.cnf|0644"
    "scripts/ingest_disk_utilization.sh|${BANGI_RELEASE_SCRIPTS_DIR}/ingest_disk_utilization.sh|0755"
    "scripts/refresh_ip2location_db.sh|${BANGI_RELEASE_SCRIPTS_DIR}/refresh_ip2location_db.sh|0755"
)

bangi_raw_asset_url() {
    local asset_path="$1"
    printf '%s/%s\n' "${BANGI_RAW_BASE_URL}" "${asset_path}"
}

bangi_fetch_required_asset() {
    local source_path="$1"
    local destination_path="$2"
    local mode="$3"
    local destination_dir=""
    local temporary_path=""

    destination_dir="$(dirname "${destination_path}")"
    temporary_path="${destination_path}.tmp"

    install -d -m 0755 -o root -g root "${destination_dir}" \
        || bangi_fatal "Cannot create asset destination directory: ${destination_dir}"

    bangi_log "Fetching ${source_path} from ${BANGI_RELEASE_TAG}"
    curl -fsSL "$(bangi_raw_asset_url "${source_path}")" -o "${temporary_path}" \
        || bangi_fatal "Cannot fetch required deployment asset ${source_path} for ${BANGI_RELEASE_TAG}"

    chmod "${mode}" "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on deployment asset ${destination_path}"
    chown root:root "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on deployment asset ${destination_path}"
    mv -f "${temporary_path}" "${destination_path}" \
        || bangi_fatal "Cannot install deployment asset ${destination_path}"
}

bangi_fetch_assets() {
    local asset_spec=""
    local source_path=""
    local destination_path=""
    local mode=""

    bangi_log "Fetching deployment assets from pinned release ${BANGI_RELEASE_TAG}"

    for asset_spec in "${BANGI_DEPLOYMENT_ASSETS[@]}"; do
        IFS='|' read -r source_path destination_path mode <<<"${asset_spec}"
        bangi_fetch_required_asset "${source_path}" "${destination_path}" "${mode}"
    done
}

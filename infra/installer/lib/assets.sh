#!/usr/bin/env bash

BANGI_GITHUB_OWNER="devalentino"
BANGI_GITHUB_REPO="bangi"
BANGI_RAW_BASE_URL="https://raw.githubusercontent.com/${BANGI_GITHUB_OWNER}/${BANGI_GITHUB_REPO}/${BANGI_RELEASE_TAG}"

bangi_raw_asset_url() {
    local asset_path="$1"
    printf '%s/%s\n' "${BANGI_RAW_BASE_URL}" "${asset_path}"
}

bangi_fetch_assets() {
    bangi_log "Asset fetch phase pending implementation"
}

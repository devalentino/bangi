#!/usr/bin/env bash

bangi_validate_supported_os() {
    local os_release_path="${1:-/etc/os-release}"
    local os_id=""
    local version_id=""

    if [[ ! -r "${os_release_path}" ]]; then
        bangi_fatal "Unsupported operating system: cannot read ${os_release_path}. Bangi requires Ubuntu 24.04 LTS."
    fi

    # shellcheck disable=SC1090
    source "${os_release_path}"
    os_id="${ID:-}"
    version_id="${VERSION_ID:-}"

    if [[ "${os_id}" != "ubuntu" || "${version_id}" != "24.04" ]]; then
        bangi_fatal "Unsupported operating system: Bangi requires Ubuntu 24.04 LTS."
    fi

    bangi_log "Validated Ubuntu 24.04 LTS host"
}

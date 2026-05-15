#!/usr/bin/env bash
set -Eeuo pipefail

BANGI_RELEASE_TAG="0.0.1a34"
BANGI_GITHUB_OWNER="devalentino"
BANGI_GITHUB_REPO="bangi"
BANGI_RAW_BASE_URL="https://raw.githubusercontent.com/${BANGI_GITHUB_OWNER}/${BANGI_GITHUB_REPO}/${BANGI_RELEASE_TAG}"

INSTALLER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER_LIB_DIR="${INSTALLER_DIR}/lib"
if [[ "${INSTALLER_DIR}" == "/tmp" ]]; then
    INSTALLER_LIB_DIR="/tmp/installer-lib"
fi
BANGI_INSTALLER_MODULES=(
    common.sh
    os.sh
    paths.sh
    packages.sh
    assets.sh
    env.sh
    acme.sh
    ip2location.sh
    compose.sh
    nginx.sh
    cron.sh
    ops_user.sh
    health.sh
)

bangi_bootstrap_fatal() {
    printf '[bangi] ERROR: %s\n' "$*" >&2
    exit 1
}

bangi_bootstrap_module_url() {
    local module_name="$1"
    printf '%s/infra/installer/lib/%s\n' "${BANGI_RAW_BASE_URL}" "${module_name}"
}

bangi_bootstrap_common_module() {
    local common_module_path="${INSTALLER_LIB_DIR}/common.sh"

    if [[ -r "${common_module_path}" ]]; then
        return 0
    fi

    mkdir -p "${INSTALLER_LIB_DIR}" \
        || bangi_bootstrap_fatal "Cannot create installer module directory: ${INSTALLER_LIB_DIR}"
    curl -fsSL "$(bangi_bootstrap_module_url common.sh)" -o "${common_module_path}" \
        || bangi_bootstrap_fatal "Cannot fetch required installer module common.sh for ${BANGI_RELEASE_TAG}"
}

bangi_bootstrap_installer_modules() {
    local module_name=""
    local module_path=""
    local missing_module="false"

    for module_name in "${BANGI_INSTALLER_MODULES[@]}"; do
        module_path="${INSTALLER_LIB_DIR}/${module_name}"
        if [[ ! -r "${module_path}" ]]; then
            missing_module="true"
            break
        fi
    done

    if [[ "${missing_module}" != "true" ]]; then
        return 0
    fi

    bangi_log "Fetching installer modules for ${BANGI_RELEASE_TAG}"

    mkdir -p "${INSTALLER_LIB_DIR}" \
        || bangi_fatal "Cannot create installer module directory: ${INSTALLER_LIB_DIR}"

    for module_name in "${BANGI_INSTALLER_MODULES[@]}"; do
        module_path="${INSTALLER_LIB_DIR}/${module_name}"
        curl -fsSL "$(bangi_bootstrap_module_url "${module_name}")" -o "${module_path}" \
            || bangi_fatal "Cannot fetch required installer module ${module_name} for ${BANGI_RELEASE_TAG}"
    done
}

bangi_bootstrap_common_module
# shellcheck source=infra/installer/lib/common.sh
source "${INSTALLER_LIB_DIR}/common.sh"
bangi_bootstrap_installer_modules

# shellcheck source=infra/installer/lib/os.sh
source "${INSTALLER_LIB_DIR}/os.sh"
# shellcheck source=infra/installer/lib/paths.sh
source "${INSTALLER_LIB_DIR}/paths.sh"
# shellcheck source=infra/installer/lib/packages.sh
source "${INSTALLER_LIB_DIR}/packages.sh"
# shellcheck source=infra/installer/lib/assets.sh
source "${INSTALLER_LIB_DIR}/assets.sh"
# shellcheck source=infra/installer/lib/env.sh
source "${INSTALLER_LIB_DIR}/env.sh"
# shellcheck source=infra/installer/lib/acme.sh
source "${INSTALLER_LIB_DIR}/acme.sh"
# shellcheck source=infra/installer/lib/ip2location.sh
source "${INSTALLER_LIB_DIR}/ip2location.sh"
# shellcheck source=infra/installer/lib/compose.sh
source "${INSTALLER_LIB_DIR}/compose.sh"
# shellcheck source=infra/installer/lib/nginx.sh
source "${INSTALLER_LIB_DIR}/nginx.sh"
# shellcheck source=infra/installer/lib/cron.sh
source "${INSTALLER_LIB_DIR}/cron.sh"
# shellcheck source=infra/installer/lib/ops_user.sh
source "${INSTALLER_LIB_DIR}/ops_user.sh"
# shellcheck source=infra/installer/lib/health.sh
source "${INSTALLER_LIB_DIR}/health.sh"

main() {
    bangi_require_root
    bangi_validate_supported_os

    bangi_log "Starting Bangi host provisioning for ${BANGI_RELEASE_TAG}"
    bangi_verify_inputs
    bangi_detect_existing_state
    bangi_install_packages
    bangi_create_paths
    bangi_fetch_assets
    bangi_write_environment
    bangi_install_acme
    bangi_install_ip2location_database
    bangi_install_ops_user
    bangi_install_compose
    bangi_install_nginx
    bangi_install_cron
    bangi_start_compose
    bangi_verify_health
    bangi_activate_release
    bangi_print_summary
}

main "$@"

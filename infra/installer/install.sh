#!/usr/bin/env bash
set -Eeuo pipefail

BANGI_RELEASE_TAG="0.0.1a8"

INSTALLER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=infra/installer/lib/common.sh
source "${INSTALLER_DIR}/lib/common.sh"
# shellcheck source=infra/installer/lib/os.sh
source "${INSTALLER_DIR}/lib/os.sh"
# shellcheck source=infra/installer/lib/paths.sh
source "${INSTALLER_DIR}/lib/paths.sh"
# shellcheck source=infra/installer/lib/packages.sh
source "${INSTALLER_DIR}/lib/packages.sh"
# shellcheck source=infra/installer/lib/assets.sh
source "${INSTALLER_DIR}/lib/assets.sh"
# shellcheck source=infra/installer/lib/env.sh
source "${INSTALLER_DIR}/lib/env.sh"
# shellcheck source=infra/installer/lib/compose.sh
source "${INSTALLER_DIR}/lib/compose.sh"
# shellcheck source=infra/installer/lib/nginx.sh
source "${INSTALLER_DIR}/lib/nginx.sh"
# shellcheck source=infra/installer/lib/cron.sh
source "${INSTALLER_DIR}/lib/cron.sh"
# shellcheck source=infra/installer/lib/ops_user.sh
source "${INSTALLER_DIR}/lib/ops_user.sh"
# shellcheck source=infra/installer/lib/health.sh
source "${INSTALLER_DIR}/lib/health.sh"

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
    bangi_install_compose
    bangi_install_nginx
    bangi_install_ops_user
    bangi_install_cron
    bangi_start_compose
    bangi_verify_health
    bangi_activate_release
    bangi_print_summary
}

main "$@"

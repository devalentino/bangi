#!/usr/bin/env bash

BANGI_ACME_INSTALL_URL="https://get.acme.sh"

bangi_acme_load_runtime_environment() {
    declare -gA BANGI_ACME_ENV_VALUES=()
    bangi_env_load_file "${BANGI_RUNTIME_ENV_FILE}" BANGI_ACME_ENV_VALUES
}

bangi_acme_enabled() {
    [[ "${BANGI_ACME_ENV_VALUES[BANGI_ACME_ENABLED]:-true}" == "true" ]]
}

bangi_acme_server() {
    if [[ "${BANGI_ACME_ENV_VALUES[BANGI_ACME_USE_STAGING]:-false}" == "true" ]]; then
        printf '%s\n' "${BANGI_ACME_ENV_VALUES[BANGI_ACME_STAGING_SERVER]}"
        return 0
    fi

    printf '%s\n' "${BANGI_ACME_ENV_VALUES[BANGI_ACME_SERVER]}"
}

bangi_install_acme_client() {
    local account_email="${BANGI_ACME_ENV_VALUES[BANGI_ACME_ACCOUNT_EMAIL]:-}"

    [[ -n "${account_email}" ]] \
        || bangi_fatal "Cannot install ACME support without BANGI_ACME_ACCOUNT_EMAIL"

    bangi_log "Installing acme.sh without automatic cron renewal"
    curl -fsSL "${BANGI_ACME_INSTALL_URL}" | sh -s email="${account_email}" --home "${BANGI_ACME_HOME_DIR}" --accountemail "${account_email}" --nocron \
        || bangi_fatal "acme.sh installation failed"

    "${BANGI_ACME_HOME_DIR}/acme.sh" --uninstall-cronjob >/dev/null 2>&1 || true
}

bangi_register_acme_account() {
    local account_email="${BANGI_ACME_ENV_VALUES[BANGI_ACME_ACCOUNT_EMAIL]:-}"
    local acme_server=""

    acme_server="$(bangi_acme_server)"

    bangi_log "Registering Let's Encrypt ACME account"
    "${BANGI_ACME_HOME_DIR}/acme.sh" \
        --home "${BANGI_ACME_HOME_DIR}" \
        --server "${acme_server}" \
        --accountemail "${account_email}" \
        --register-account \
        -m "${account_email}" \
        || bangi_fatal "ACME account registration failed for ${account_email}"
}

bangi_prepare_acme_directories() {
    install -d -m 0755 -o root -g root "${BANGI_ACME_CHALLENGE_WEBROOT}" \
        || bangi_fatal "Cannot create ACME challenge webroot: ${BANGI_ACME_CHALLENGE_WEBROOT}"
    install -d -m 0755 -o root -g root "${BANGI_CERTIFICATE_BASE_DIR}" \
        || bangi_fatal "Cannot create certificate base directory: ${BANGI_CERTIFICATE_BASE_DIR}"
}

bangi_install_acme() {
    bangi_acme_load_runtime_environment

    if ! bangi_acme_enabled; then
        bangi_log "ACME support disabled by BANGI_ACME_ENABLED=false"
        return 0
    fi

    bangi_prepare_acme_directories
    bangi_install_acme_client
    bangi_register_acme_account
}

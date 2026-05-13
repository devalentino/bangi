#!/usr/bin/env bash

BANGI_RUNTIME_ENV_FILE="${BANGI_SHARED_ENV_DIR}/.env"
BANGI_OPS_ENV_FILE="${BANGI_ETC_DIR}/ops.env"
BANGI_IP2LOCATION_DATABASE_FILE="IP2LOCATION-LITE-DB1.IPV6.BIN"
BANGI_ACME_DEFAULT_SERVER="https://acme-v02.api.letsencrypt.org/directory"
BANGI_ACME_DEFAULT_STAGING_SERVER="https://acme-staging-v02.api.letsencrypt.org/directory"

bangi_env_secret() {
    od -An -N32 -tx1 /dev/urandom | tr -d ' \n'
}

bangi_env_load_file() {
    local file_path="$1"
    local -n target_values="$2"
    local line=""
    local key=""
    local value=""

    [[ -f "${file_path}" ]] || return 0

    while IFS= read -r line || [[ -n "${line}" ]]; do
        [[ -n "${line}" && "${line}" != \#* && "${line}" == *=* ]] || continue

        key="${line%%=*}"
        value="${line#*=}"
        key="${key#export }"

        [[ "${key}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
        target_values["${key}"]="${value}"
    done <"${file_path}"
}

bangi_env_set_if_missing() {
    local -n target_values="$1"
    local key="$2"
    local value="$3"

    if [[ -z "${target_values[${key}]+x}" || -z "${target_values[${key}]}" ]]; then
        target_values["${key}"]="${value}"
    fi
}

bangi_env_write_file() {
    local file_path="$1"
    local mode="$2"
    shift 2

    local temporary_path="${file_path}.tmp"
    local previous_umask=""
    local key=""

    previous_umask="$(umask)"
    umask 077
    if ! : >"${temporary_path}"; then
        umask "${previous_umask}"
        bangi_fatal "Cannot create temporary environment file: ${temporary_path}"
    fi
    umask "${previous_umask}"

    for key in "$@"; do
        printf '%s=%s\n' "${key}" "${BANGI_ENV_VALUES[${key}]}" >>"${temporary_path}" \
            || bangi_fatal "Cannot write environment value ${key} to ${temporary_path}"
    done

    chown root:root "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on environment file ${file_path}"
    chmod "${mode}" "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on environment file ${file_path}"
    mv -f "${temporary_path}" "${file_path}" \
        || bangi_fatal "Cannot install environment file ${file_path}"
}

bangi_env_validate_required() {
    local key=""

    for key in "$@"; do
        if [[ -z "${BANGI_ENV_VALUES[${key}]+x}" || -z "${BANGI_ENV_VALUES[${key}]}" ]]; then
            bangi_fatal "Required runtime environment value ${key} is blank"
        fi
    done
}

bangi_env_prompt_secret() {
    local prompt="$1"
    local value=""

    if [[ ! -t 0 ]]; then
        printf '\n'
        return 0
    fi

    printf '%s' "${prompt}" >&2
    IFS= read -r -s value
    printf '\n' >&2
    printf '%s\n' "${value}"
}

bangi_env_read_ip2location_token() {
    local token="${IP2LOCATION_DOWNLOAD_TOKEN:-}"

    while true; do
        if [[ -z "${token}" ]]; then
            bangi_log "IP2Location download token is optional; leave blank to skip automated refresh credentials." >&2
            token="$(bangi_env_prompt_secret "IP2Location download token: ")"
        fi

        if [[ -z "${token}" ]]; then
            printf '\n'
            return 0
        fi

        printf '%s\n' "${token}"
        return 0
    done
}

bangi_env_validate_email_syntax() {
    local email="$1"

    [[ "${email}" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$ ]]
}

bangi_env_read_acme_account_email() {
    local email="${BANGI_ACME_ACCOUNT_EMAIL:-}"

    while true; do
        if [[ -z "${email}" ]]; then
            if [[ ! -t 0 ]]; then
                printf '\n'
                return 0
            fi
            bangi_log "Let's Encrypt account email is required for managed HTTPS certificates." >&2
            printf 'ACME account email: ' >&2
            IFS= read -r email
        fi

        if bangi_env_validate_email_syntax "${email}"; then
            printf '%s\n' "${email}"
            return 0
        fi

        bangi_log "Invalid ACME account email syntax. Enter a valid email address." >&2
        email=""
    done
}

bangi_write_runtime_environment() {
    local runtime_keys=(
        MARIADB_ROOT_PASSWORD
        MARIADB_USER
        MARIADB_PASSWORD
        MARIADB_HOST
        MARIADB_PORT
        MARIADB_DATABASE
        BASIC_AUTHENTICATION_USERNAME
        BASIC_AUTHENTICATION_PASSWORD
        LANDING_PAGES_BASE_PATH
        IP2LOCATION_DB_PATH
        LANDING_PAGE_RENDERER_BASE_URL
        BANGI_PUBLIC_HOST_IP
        BANGI_ACME_ENABLED
        BANGI_ACME_CA
        BANGI_ACME_SERVER
        BANGI_ACME_STAGING_SERVER
        BANGI_ACME_USE_STAGING
        BANGI_ACME_ACCOUNT_EMAIL
        BANGI_ACME_CHALLENGE_WEBROOT
        BANGI_CERTIFICATE_BASE_DIR
        BANGI_CERTIFICATE_RENEWAL_WINDOW_DAYS
        BANGI_CERTIFICATE_WARNING_DAYS
        BANGI_CERTIFICATE_ERROR_DAYS
        BANGI_CERTIFICATE_MAX_BACKOFF_SECONDS
        BANGI_CERTIFICATE_RETRY_JITTER_SECONDS
    )

    local runtime_required_keys=(
        MARIADB_ROOT_PASSWORD
        MARIADB_USER
        MARIADB_PASSWORD
        MARIADB_HOST
        MARIADB_PORT
        MARIADB_DATABASE
        BASIC_AUTHENTICATION_USERNAME
        BASIC_AUTHENTICATION_PASSWORD
        LANDING_PAGES_BASE_PATH
        IP2LOCATION_DB_PATH
        LANDING_PAGE_RENDERER_BASE_URL
    )
    local acme_account_email=""

    declare -gA BANGI_ENV_VALUES=()
    bangi_env_load_file "${BANGI_RUNTIME_ENV_FILE}" BANGI_ENV_VALUES

    bangi_env_set_if_missing BANGI_ENV_VALUES MARIADB_ROOT_PASSWORD "$(bangi_env_secret)"
    bangi_env_set_if_missing BANGI_ENV_VALUES MARIADB_USER "bangi"
    bangi_env_set_if_missing BANGI_ENV_VALUES MARIADB_PASSWORD "$(bangi_env_secret)"
    bangi_env_set_if_missing BANGI_ENV_VALUES MARIADB_HOST "mariadb"
    bangi_env_set_if_missing BANGI_ENV_VALUES MARIADB_PORT "3306"
    bangi_env_set_if_missing BANGI_ENV_VALUES MARIADB_DATABASE "bangi"
    bangi_env_set_if_missing BANGI_ENV_VALUES BASIC_AUTHENTICATION_USERNAME "admin"
    bangi_env_set_if_missing BANGI_ENV_VALUES BASIC_AUTHENTICATION_PASSWORD "$(bangi_env_secret)"
    bangi_env_set_if_missing BANGI_ENV_VALUES LANDING_PAGES_BASE_PATH "${BANGI_SHARED_LANDINGS_DIR}"
    bangi_env_set_if_missing BANGI_ENV_VALUES IP2LOCATION_DB_PATH "${BANGI_SHARED_IP2LOCATION_DIR}/IP2LOCATION-LITE-DB1.IPV6.BIN"
    bangi_env_set_if_missing BANGI_ENV_VALUES LANDING_PAGE_RENDERER_BASE_URL "http://landing-renderer"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_PUBLIC_HOST_IP "$(bangi_detect_public_host)"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_ACME_ENABLED "true"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_ACME_CA "letsencrypt"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_ACME_SERVER "${BANGI_ACME_DEFAULT_SERVER}"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_ACME_STAGING_SERVER "${BANGI_ACME_DEFAULT_STAGING_SERVER}"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_ACME_USE_STAGING "false"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_ACME_ACCOUNT_EMAIL ""
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_ACME_CHALLENGE_WEBROOT "${BANGI_ACME_CHALLENGE_WEBROOT}"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_CERTIFICATE_BASE_DIR "${BANGI_CERTIFICATE_BASE_DIR}"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_CERTIFICATE_RENEWAL_WINDOW_DAYS "30"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_CERTIFICATE_WARNING_DAYS "14"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_CERTIFICATE_ERROR_DAYS "7"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_CERTIFICATE_MAX_BACKOFF_SECONDS "86400"
    bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_CERTIFICATE_RETRY_JITTER_SECONDS "120"

    if [[ "${BANGI_ENV_VALUES[BANGI_ACME_ENABLED]}" == "true" ]]; then
        if [[ "${BANGI_ENV_VALUES[BANGI_ACME_CA]}" != "letsencrypt" ]]; then
            bangi_fatal "Unsupported BANGI_ACME_CA value: ${BANGI_ENV_VALUES[BANGI_ACME_CA]}"
        fi
        if [[ -z "${BANGI_ENV_VALUES[BANGI_ACME_ACCOUNT_EMAIL]+x}" || -z "${BANGI_ENV_VALUES[BANGI_ACME_ACCOUNT_EMAIL]}" ]]; then
            acme_account_email="$(bangi_env_read_acme_account_email)"
            bangi_env_set_if_missing BANGI_ENV_VALUES BANGI_ACME_ACCOUNT_EMAIL "${acme_account_email}"
        fi
        if ! bangi_env_validate_email_syntax "${BANGI_ENV_VALUES[BANGI_ACME_ACCOUNT_EMAIL]:-}"; then
            bangi_fatal "Required runtime environment value BANGI_ACME_ACCOUNT_EMAIL must be a valid email address when ACME is enabled"
        fi
    fi

    bangi_env_validate_required "${runtime_required_keys[@]}"
    bangi_env_write_file "${BANGI_RUNTIME_ENV_FILE}" "0600" "${runtime_keys[@]}"
}

bangi_write_ops_environment() {
    local ops_keys=(
        IP2LOCATION_DOWNLOAD_TOKEN
    )
    local ip2location_download_token=""

    declare -gA BANGI_ENV_VALUES=()
    bangi_env_load_file "${BANGI_OPS_ENV_FILE}" BANGI_ENV_VALUES

    if [[ -z "${BANGI_ENV_VALUES[IP2LOCATION_DOWNLOAD_TOKEN]+x}" || -z "${BANGI_ENV_VALUES[IP2LOCATION_DOWNLOAD_TOKEN]}" ]]; then
        ip2location_download_token="$(bangi_env_read_ip2location_token)"
        bangi_env_set_if_missing BANGI_ENV_VALUES IP2LOCATION_DOWNLOAD_TOKEN "${ip2location_download_token}"
    fi

    bangi_env_write_file "${BANGI_OPS_ENV_FILE}" "0600" "${ops_keys[@]}"
}

bangi_write_environment() {
    bangi_log "Materializing Bangi runtime and operational environment files"

    install -d -m 0755 -o root -g root "${BANGI_SHARED_ENV_DIR}" \
        || bangi_fatal "Cannot create runtime environment directory: ${BANGI_SHARED_ENV_DIR}"
    install -d -m 0755 -o root -g root "${BANGI_ETC_DIR}" \
        || bangi_fatal "Cannot create operational environment directory: ${BANGI_ETC_DIR}"

    bangi_write_runtime_environment
    bangi_write_ops_environment
}

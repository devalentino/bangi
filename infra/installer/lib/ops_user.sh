#!/usr/bin/env bash

BANGI_OPS_USER="bangi-ops"
BANGI_OPS_HOME_DIR="/var/lib/bangi-ops"
BANGI_OPS_SSH_DIR="${BANGI_OPS_HOME_DIR}/.ssh"
BANGI_OPS_AUTHORIZED_KEYS_FILE="${BANGI_OPS_SSH_DIR}/authorized_keys"
BANGI_OPS_ETC_DIR="${BANGI_ETC_DIR}/ops"
BANGI_OPS_ETC_SSH_DIR="${BANGI_OPS_ETC_DIR}/ssh"
BANGI_OPS_SSH_KEY_FILE="${BANGI_OPS_ETC_SSH_DIR}/id_ed25519"
BANGI_OPS_SSH_PUBLIC_KEY_FILE="${BANGI_OPS_SSH_KEY_FILE}.pub"
BANGI_OPS_KNOWN_HOSTS_FILE="${BANGI_OPS_ETC_SSH_DIR}/known_hosts"
BANGI_OPS_SUDOERS_FILE="/etc/sudoers.d/bangi-ops"
BANGI_OPS_DISPATCHER="${BANGI_OPS_BIN_DIR}/dispatch"
BANGI_OPS_WRAPPERS=(
    nginx-validate
    nginx-reload
    refresh-ip2location
)

bangi_ensure_ops_user() {
    local ops_group=""

    if id -u "${BANGI_OPS_USER}" >/dev/null 2>&1; then
        bangi_log "Operations user already exists: ${BANGI_OPS_USER}"
        usermod \
            --home "${BANGI_OPS_HOME_DIR}" \
            --shell /bin/sh \
            "${BANGI_OPS_USER}" \
            || bangi_fatal "Cannot update operations user login boundary: ${BANGI_OPS_USER}"
        ops_group="$(id -gn "${BANGI_OPS_USER}")" \
            || bangi_fatal "Cannot resolve operations user group: ${BANGI_OPS_USER}"
        install -d -m 0750 -o "${BANGI_OPS_USER}" -g "${ops_group}" "${BANGI_OPS_HOME_DIR}" \
            || bangi_fatal "Cannot create operations user home: ${BANGI_OPS_HOME_DIR}"
        return 0
    fi

    useradd \
        --system \
        --home-dir "${BANGI_OPS_HOME_DIR}" \
        --create-home \
        --shell /bin/sh \
        "${BANGI_OPS_USER}" \
        || bangi_fatal "Cannot create operations user: ${BANGI_OPS_USER}"

    chmod 0750 "${BANGI_OPS_HOME_DIR}" \
        || bangi_fatal "Cannot set permissions on operations user home: ${BANGI_OPS_HOME_DIR}"
}

bangi_write_ops_wrapper() {
    local wrapper_name="$1"
    local wrapper_path="${BANGI_OPS_BIN_DIR}/${wrapper_name}"
    local temporary_path="${wrapper_path}.tmp"

    case "${wrapper_name}" in
        nginx-validate)
            cat >"${temporary_path}" <<'EOF' \
                || bangi_fatal "Cannot write operations wrapper: nginx-validate"
#!/usr/bin/env bash
set -Eeuo pipefail

exec /usr/sbin/nginx -t
EOF
            ;;
        nginx-reload)
            cat >"${temporary_path}" <<'EOF' \
                || bangi_fatal "Cannot write operations wrapper: nginx-reload"
#!/usr/bin/env bash
set -Eeuo pipefail

/usr/sbin/nginx -t
exec /usr/bin/systemctl reload nginx
EOF
            ;;
        refresh-ip2location)
            cat >"${temporary_path}" <<'EOF' \
                || bangi_fatal "Cannot write operations wrapper: refresh-ip2location"
#!/usr/bin/env bash
set -Eeuo pipefail

refresh_script="/opt/bangi/current/scripts/refresh_ip2location_db.sh"

if [[ ! -x "${refresh_script}" ]]; then
    printf 'IP2Location refresh script is not installed: %s\n' "${refresh_script}" >&2
    exit 1
fi

exec "${refresh_script}"
EOF
            ;;
        *)
            bangi_fatal "Unsupported operations wrapper requested: ${wrapper_name}"
            ;;
    esac

    chown root:root "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on operations wrapper: ${wrapper_path}"
    chmod 0755 "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on operations wrapper: ${wrapper_path}"
    mv -f "${temporary_path}" "${wrapper_path}" \
        || bangi_fatal "Cannot install operations wrapper: ${wrapper_path}"
}

bangi_install_ops_dispatcher() {
    local temporary_path="${BANGI_OPS_DISPATCHER}.tmp"

    cat >"${temporary_path}" <<'EOF' \
        || bangi_fatal "Cannot write operations dispatcher"
#!/usr/bin/env bash
set -Eeuo pipefail

case "${SSH_ORIGINAL_COMMAND:-}" in
    nginx-validate)
        exec sudo -n /opt/bangi/ops/bin/nginx-validate
        ;;
    nginx-reload)
        exec sudo -n /opt/bangi/ops/bin/nginx-reload
        ;;
    refresh-ip2location)
        exec sudo -n /opt/bangi/ops/bin/refresh-ip2location
        ;;
    *)
        printf 'Unsupported Bangi ops command\n' >&2
        exit 126
        ;;
esac
EOF

    chown root:root "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on operations dispatcher: ${BANGI_OPS_DISPATCHER}"
    chmod 0755 "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on operations dispatcher: ${BANGI_OPS_DISPATCHER}"
    mv -f "${temporary_path}" "${BANGI_OPS_DISPATCHER}" \
        || bangi_fatal "Cannot install operations dispatcher: ${BANGI_OPS_DISPATCHER}"
}

bangi_install_ops_wrappers() {
    local wrapper_name=""

    install -d -m 0755 -o root -g root "${BANGI_OPS_BIN_DIR}" \
        || bangi_fatal "Cannot create operations wrapper directory: ${BANGI_OPS_BIN_DIR}"

    for wrapper_name in "${BANGI_OPS_WRAPPERS[@]}"; do
        bangi_write_ops_wrapper "${wrapper_name}"
    done

    bangi_install_ops_dispatcher
}

bangi_install_ops_ssh_key() {
    install -d -m 0700 -o root -g root "${BANGI_OPS_ETC_SSH_DIR}" \
        || bangi_fatal "Cannot create operations SSH key directory: ${BANGI_OPS_ETC_SSH_DIR}"

    if [[ ! -f "${BANGI_OPS_SSH_KEY_FILE}" ]]; then
        ssh-keygen -q -t ed25519 -N "" -C "bangi-api@host-ops" -f "${BANGI_OPS_SSH_KEY_FILE}" \
            || bangi_fatal "Cannot generate operations SSH key: ${BANGI_OPS_SSH_KEY_FILE}"
    fi

    chown root:root "${BANGI_OPS_SSH_KEY_FILE}" "${BANGI_OPS_SSH_PUBLIC_KEY_FILE}" \
        || bangi_fatal "Cannot set ownership on operations SSH keypair"
    chmod 0600 "${BANGI_OPS_SSH_KEY_FILE}" \
        || bangi_fatal "Cannot set permissions on operations SSH private key"
    chmod 0644 "${BANGI_OPS_SSH_PUBLIC_KEY_FILE}" \
        || bangi_fatal "Cannot set permissions on operations SSH public key"
}

bangi_install_ops_authorized_key() {
    local ops_group=""
    local public_key=""
    local temporary_path="${BANGI_OPS_AUTHORIZED_KEYS_FILE}.tmp"

    public_key="$(cat "${BANGI_OPS_SSH_PUBLIC_KEY_FILE}")" \
        || bangi_fatal "Cannot read operations SSH public key: ${BANGI_OPS_SSH_PUBLIC_KEY_FILE}"
    ops_group="$(id -gn "${BANGI_OPS_USER}")" \
        || bangi_fatal "Cannot resolve operations user group: ${BANGI_OPS_USER}"

    install -d -m 0700 -o "${BANGI_OPS_USER}" -g "${ops_group}" "${BANGI_OPS_SSH_DIR}" \
        || bangi_fatal "Cannot create operations SSH directory: ${BANGI_OPS_SSH_DIR}"

    printf 'restrict,no-pty,no-port-forwarding,no-agent-forwarding,no-X11-forwarding,command="%s" %s\n' \
        "${BANGI_OPS_DISPATCHER}" \
        "${public_key}" >"${temporary_path}" \
        || bangi_fatal "Cannot write operations authorized_keys: ${temporary_path}"

    chown "${BANGI_OPS_USER}:${ops_group}" "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on operations authorized_keys"
    chmod 0600 "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on operations authorized_keys"
    mv -f "${temporary_path}" "${BANGI_OPS_AUTHORIZED_KEYS_FILE}" \
        || bangi_fatal "Cannot install operations authorized_keys"
}

bangi_install_ops_known_hosts() {
    local temporary_path="${BANGI_OPS_KNOWN_HOSTS_FILE}.tmp"
    local host_key_file=""

    : >"${temporary_path}" \
        || bangi_fatal "Cannot create operations known_hosts file: ${temporary_path}"

    for host_key_file in /etc/ssh/ssh_host_*_key.pub; do
        [[ -f "${host_key_file}" ]] || continue
        awk '{ print "host.docker.internal " $1 " " $2 }' "${host_key_file}" >>"${temporary_path}" \
            || bangi_fatal "Cannot add host SSH key to operations known_hosts: ${host_key_file}"
    done

    [[ -s "${temporary_path}" ]] \
        || bangi_fatal "No host SSH public keys found for operations known_hosts"

    chown root:root "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on operations known_hosts"
    chmod 0644 "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on operations known_hosts"
    mv -f "${temporary_path}" "${BANGI_OPS_KNOWN_HOSTS_FILE}" \
        || bangi_fatal "Cannot install operations known_hosts"
}

bangi_install_ops_ssh_access() {
    bangi_install_ops_ssh_key
    bangi_install_ops_authorized_key
    bangi_install_ops_known_hosts
}

bangi_install_ops_sudoers() {
    local temporary_path="${BANGI_OPS_SUDOERS_FILE}.tmp"

    cat >"${temporary_path}" <<EOF \
        || bangi_fatal "Cannot write sudoers allowlist: ${temporary_path}"
# Managed by Bangi installer. Local edits may be overwritten.
Defaults:${BANGI_OPS_USER} secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Cmnd_Alias BANGI_OPS_WRAPPERS = ${BANGI_OPS_BIN_DIR}/nginx-validate, ${BANGI_OPS_BIN_DIR}/nginx-reload, ${BANGI_OPS_BIN_DIR}/refresh-ip2location
${BANGI_OPS_USER} ALL=(root) NOPASSWD: BANGI_OPS_WRAPPERS
EOF

    chown root:root "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on sudoers allowlist: ${temporary_path}"
    chmod 0440 "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on sudoers allowlist: ${temporary_path}"

    if ! visudo -cf "${temporary_path}" >/dev/null; then
        rm -f "${temporary_path}"
        bangi_fatal "Invalid sudoers allowlist; refusing to activate ${BANGI_OPS_SUDOERS_FILE}"
    fi

    mv -f "${temporary_path}" "${BANGI_OPS_SUDOERS_FILE}" \
        || bangi_fatal "Cannot install sudoers allowlist: ${BANGI_OPS_SUDOERS_FILE}"
}

bangi_install_ops_user() {
    bangi_log "Installing restricted Bangi operations user and wrapper allowlist"

    bangi_ensure_ops_user
    bangi_install_ops_wrappers
    bangi_install_ops_ssh_access
    bangi_install_ops_sudoers
}

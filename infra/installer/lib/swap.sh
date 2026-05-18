#!/usr/bin/env bash

BANGI_SWAP_FILE="${BANGI_SWAP_FILE:-/swapfile}"
BANGI_SWAP_SIZE="${BANGI_SWAP_SIZE:-1G}"
BANGI_SWAP_THRESHOLD_KB="${BANGI_SWAP_THRESHOLD_KB:-2097152}"
BANGI_SWAP_SWAPPINESS="${BANGI_SWAP_SWAPPINESS:-10}"
BANGI_SWAP_FORCE="${BANGI_SWAP_FORCE:-false}"
BANGI_SWAP_SYSCTL_FILE="/etc/sysctl.d/99-bangi-swap.conf"
BANGI_SWAP_FSTAB_OPTIONS="none swap sw 0 0"
BANGI_SWAP_INSTALL_STATUS="not checked"

bangi_swap_active_entries() {
    swapon --noheadings --show=NAME,SIZE 2>/dev/null || true
}

bangi_swap_active_summary() {
    local entries=""

    entries="$(bangi_swap_active_entries)"
    if [[ -z "${entries}" ]]; then
        printf 'inactive'
        return 0
    fi

    printf 'active: %s' "$(tr '\n' ';' <<<"${entries}" | sed 's/;$//')"
}

bangi_swap_host_memory_kb() {
    awk '/^MemTotal:/ { print $2; exit }' /proc/meminfo
}

bangi_swap_should_create() {
    local memory_kb="$1"

    if [[ "${BANGI_SWAP_FORCE}" == "true" ]]; then
        return 0
    fi

    [[ "${memory_kb}" -le "${BANGI_SWAP_THRESHOLD_KB}" ]]
}

bangi_swap_ensure_file() {
    if [[ -f "${BANGI_SWAP_FILE}" ]]; then
        chmod 0600 "${BANGI_SWAP_FILE}" \
            || bangi_fatal "Cannot set secure permissions on swap file: ${BANGI_SWAP_FILE}"
        return 0
    fi

    bangi_log "Creating Bangi-managed swap file at ${BANGI_SWAP_FILE}"

    install -m 0600 -o root -g root /dev/null "${BANGI_SWAP_FILE}" \
        || bangi_fatal "Cannot create swap file: ${BANGI_SWAP_FILE}"

    if ! fallocate -l "${BANGI_SWAP_SIZE}" "${BANGI_SWAP_FILE}"; then
        dd if=/dev/zero of="${BANGI_SWAP_FILE}" bs=1M count=1024 status=none \
            || bangi_fatal "Cannot allocate swap file: ${BANGI_SWAP_FILE}"
    fi

    chmod 0600 "${BANGI_SWAP_FILE}" \
        || bangi_fatal "Cannot set secure permissions on swap file: ${BANGI_SWAP_FILE}"
    mkswap "${BANGI_SWAP_FILE}" >/dev/null \
        || bangi_fatal "Cannot initialize swap file: ${BANGI_SWAP_FILE}"
}

bangi_swap_persist_fstab() {
    local fstab_line="${BANGI_SWAP_FILE} ${BANGI_SWAP_FSTAB_OPTIONS}"

    if awk -v swap_file="${BANGI_SWAP_FILE}" '$1 == swap_file { found = 1 } END { exit found ? 0 : 1 }' /etc/fstab; then
        return 0
    fi

    printf '%s\n' "${fstab_line}" >>/etc/fstab \
        || bangi_fatal "Cannot persist swap file in /etc/fstab"
}

bangi_swap_write_sysctl() {
    local temporary_path="${BANGI_SWAP_SYSCTL_FILE}.tmp"

    if ! cat >"${temporary_path}" <<EOF
vm.swappiness=${BANGI_SWAP_SWAPPINESS}
EOF
    then
        bangi_fatal "Cannot write swap sysctl configuration: ${BANGI_SWAP_SYSCTL_FILE}"
    fi

    chown root:root "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on swap sysctl configuration: ${BANGI_SWAP_SYSCTL_FILE}"
    chmod 0644 "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on swap sysctl configuration: ${BANGI_SWAP_SYSCTL_FILE}"
    mv -f "${temporary_path}" "${BANGI_SWAP_SYSCTL_FILE}" \
        || bangi_fatal "Cannot install swap sysctl configuration: ${BANGI_SWAP_SYSCTL_FILE}"
    sysctl -p "${BANGI_SWAP_SYSCTL_FILE}" >/dev/null \
        || bangi_fatal "Cannot apply swap sysctl configuration: ${BANGI_SWAP_SYSCTL_FILE}"
}

bangi_install_managed_swap() {
    local memory_kb=""

    bangi_log "Checking host swap configuration"

    if [[ -n "$(bangi_swap_active_entries)" ]]; then
        bangi_log "Active swap detected; leaving existing swap unchanged"
        BANGI_SWAP_INSTALL_STATUS="pre-existing; $(bangi_swap_active_summary)"
        return 0
    fi

    memory_kb="$(bangi_swap_host_memory_kb)" \
        || bangi_fatal "Cannot detect host memory size"

    if ! bangi_swap_should_create "${memory_kb}"; then
        bangi_log "No active swap detected; host memory ${memory_kb} KiB is above Bangi managed-swap threshold ${BANGI_SWAP_THRESHOLD_KB} KiB"
        BANGI_SWAP_INSTALL_STATUS="not created; no active swap; host memory ${memory_kb} KiB above threshold ${BANGI_SWAP_THRESHOLD_KB} KiB"
        return 0
    fi

    bangi_swap_ensure_file
    swapon "${BANGI_SWAP_FILE}" \
        || bangi_fatal "Cannot enable swap file: ${BANGI_SWAP_FILE}"
    bangi_swap_persist_fstab
    bangi_swap_write_sysctl
    BANGI_SWAP_INSTALL_STATUS="created; $(bangi_swap_active_summary)"
}

#!/usr/bin/env bash

BANGI_FIREWALL_ALLOWED_TCP_PORTS="22,80,443"
BANGI_FIREWALL_UFW_CONFIRM_ENV="BANGI_DISABLE_UFW_CONFIRMED"

bangi_firewall_is_ufw_active() {
    command -v ufw >/dev/null 2>&1 || return 1
    ufw status 2>/dev/null | grep -Eiq '^Status:[[:space:]]+active$'
}

bangi_firewall_confirm_disable_ufw() {
    local answer=""

    if [[ "${!BANGI_FIREWALL_UFW_CONFIRM_ENV:-}" == "true" ]]; then
        return 0
    fi

    if [[ ! -t 0 ]]; then
        bangi_fatal "Active ufw detected. Bangi manages host firewall policy with iptables; rerun with ${BANGI_FIREWALL_UFW_CONFIRM_ENV}=true to allow disabling ufw."
    fi

    bangi_log "Active ufw detected. Bangi manages firewall policy directly with iptables and must disable ufw before continuing."
    printf 'Disable ufw and continue? Type "yes" to continue: ' >&2
    IFS= read -r answer

    if [[ "${answer}" != "yes" ]]; then
        bangi_fatal "Firewall setup cancelled because ufw is active."
    fi
}

bangi_firewall_disable_ufw_if_active() {
    if ! bangi_firewall_is_ufw_active; then
        return 0
    fi

    bangi_firewall_confirm_disable_ufw
    ufw disable || bangi_fatal "Failed to disable ufw before applying Bangi iptables policy"
}

bangi_write_iptables_rules() {
    bangi_log "Writing Bangi-managed iptables rules to ${BANGI_IPTABLES_RULES_FILE}"

    install -d -m 0755 -o root -g root "${BANGI_SHARED_FIREWALL_DIR}" \
        || bangi_fatal "Cannot create firewall directory: ${BANGI_SHARED_FIREWALL_DIR}"

    if ! cat >"${BANGI_IPTABLES_RULES_FILE}.tmp" <<EOF
*filter
:BANGI-INPUT -
:BANGI-DOCKER-USER -
-A BANGI-INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
-A BANGI-INPUT -i lo -j RETURN
-A BANGI-INPUT -p tcp -m multiport --dports ${BANGI_FIREWALL_ALLOWED_TCP_PORTS} -j RETURN
-A BANGI-INPUT -j DROP

-A BANGI-DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
-A BANGI-DOCKER-USER -i lo -j RETURN
-A BANGI-DOCKER-USER -i docker0 -j RETURN
-A BANGI-DOCKER-USER -i br+ -j RETURN
-A BANGI-DOCKER-USER -p tcp -j DROP
-A BANGI-DOCKER-USER -j RETURN
COMMIT
EOF
    then
        bangi_fatal "Cannot write temporary iptables rules file: ${BANGI_IPTABLES_RULES_FILE}.tmp"
    fi

    chown root:root "${BANGI_IPTABLES_RULES_FILE}.tmp" \
        || bangi_fatal "Cannot set ownership on iptables rules file"
    chmod 0644 "${BANGI_IPTABLES_RULES_FILE}.tmp" \
        || bangi_fatal "Cannot set permissions on iptables rules file"
    mv -f "${BANGI_IPTABLES_RULES_FILE}.tmp" "${BANGI_IPTABLES_RULES_FILE}" \
        || bangi_fatal "Cannot install iptables rules file"
}

bangi_write_iptables_apply_script() {
    bangi_log "Installing Bangi iptables apply command at ${BANGI_IPTABLES_APPLY_SCRIPT}"

    install -d -m 0755 -o root -g root "${BANGI_OPS_BIN_DIR}" \
        || bangi_fatal "Cannot create ops bin directory: ${BANGI_OPS_BIN_DIR}"

    if ! cat >"${BANGI_IPTABLES_APPLY_SCRIPT}.tmp" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail

rules_file="${BANGI_IPTABLES_RULES_FILE}"

[[ -f "\${rules_file}" ]] || {
    printf '[bangi] ERROR: missing iptables rules file: %s\n' "\${rules_file}" >&2
    exit 1
}

iptables -N DOCKER-USER 2>/dev/null || true
iptables -D INPUT -j BANGI-INPUT 2>/dev/null || true
iptables -D DOCKER-USER -j BANGI-DOCKER-USER 2>/dev/null || true
iptables -F BANGI-INPUT 2>/dev/null || true
iptables -X BANGI-INPUT 2>/dev/null || true
iptables -F BANGI-DOCKER-USER 2>/dev/null || true
iptables -X BANGI-DOCKER-USER 2>/dev/null || true
iptables-restore --noflush "\${rules_file}"
iptables -C INPUT -j BANGI-INPUT 2>/dev/null || iptables -I INPUT 1 -j BANGI-INPUT
iptables -C DOCKER-USER -j BANGI-DOCKER-USER 2>/dev/null || iptables -I DOCKER-USER 1 -j BANGI-DOCKER-USER
EOF
    then
        bangi_fatal "Cannot write temporary iptables apply command: ${BANGI_IPTABLES_APPLY_SCRIPT}.tmp"
    fi

    chown root:root "${BANGI_IPTABLES_APPLY_SCRIPT}.tmp" \
        || bangi_fatal "Cannot set ownership on iptables apply command"
    chmod 0755 "${BANGI_IPTABLES_APPLY_SCRIPT}.tmp" \
        || bangi_fatal "Cannot set permissions on iptables apply command"
    mv -f "${BANGI_IPTABLES_APPLY_SCRIPT}.tmp" "${BANGI_IPTABLES_APPLY_SCRIPT}" \
        || bangi_fatal "Cannot install iptables apply command"
}

bangi_apply_firewall() {
    bangi_log "Applying Bangi-managed firewall policy"
    "${BANGI_IPTABLES_APPLY_SCRIPT}" \
        || bangi_fatal "Failed to apply Bangi-managed iptables policy"
}

bangi_install_bangi_service() {
    bangi_log "Installing Bangi systemd lifecycle service"

    if ! cat >"${BANGI_SYSTEMD_SERVICE_FILE}.tmp" <<EOF
[Unit]
Description=Bangi application stack
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${BANGI_CURRENT_LINK}
ExecStartPre=${BANGI_IPTABLES_APPLY_SCRIPT}
ExecStart=/usr/bin/docker compose --project-name ${BANGI_COMPOSE_PROJECT_NAME} --project-directory ${BANGI_CURRENT_LINK} -f ${BANGI_CURRENT_LINK}/compose.yml up -d --remove-orphans
ExecStop=/usr/bin/docker compose --project-name ${BANGI_COMPOSE_PROJECT_NAME} --project-directory ${BANGI_CURRENT_LINK} -f ${BANGI_CURRENT_LINK}/compose.yml down
ExecReload=/usr/bin/docker compose --project-name ${BANGI_COMPOSE_PROJECT_NAME} --project-directory ${BANGI_CURRENT_LINK} -f ${BANGI_CURRENT_LINK}/compose.yml up -d --remove-orphans
TimeoutStartSec=300
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
EOF
    then
        bangi_fatal "Cannot write temporary systemd service file: ${BANGI_SYSTEMD_SERVICE_FILE}.tmp"
    fi

    chown root:root "${BANGI_SYSTEMD_SERVICE_FILE}.tmp" \
        || bangi_fatal "Cannot set ownership on Bangi systemd service"
    chmod 0644 "${BANGI_SYSTEMD_SERVICE_FILE}.tmp" \
        || bangi_fatal "Cannot set permissions on Bangi systemd service"
    mv -f "${BANGI_SYSTEMD_SERVICE_FILE}.tmp" "${BANGI_SYSTEMD_SERVICE_FILE}" \
        || bangi_fatal "Cannot install Bangi systemd service"

    systemctl daemon-reload \
        || bangi_fatal "Failed to reload systemd after installing bangi.service"
    systemctl enable bangi.service \
        || bangi_fatal "Failed to enable bangi.service"
}

bangi_start_bangi_service() {
    bangi_log "Starting Bangi through systemd"

    systemctl restart bangi.service \
        || bangi_fatal "Bangi systemd service startup failed. Inspect with: systemctl status bangi.service && journalctl -u bangi.service"
}

bangi_install_firewall() {
    bangi_firewall_disable_ufw_if_active
    bangi_write_iptables_rules
    bangi_write_iptables_apply_script
    bangi_apply_firewall
}

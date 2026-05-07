#!/usr/bin/env bash

BANGI_NGINX_INCLUDE_FILE="/etc/nginx/conf.d/bangi.conf"
BANGI_NGINX_DEFAULT_SITE_NAME="bangi-default.conf"
BANGI_NGINX_DEFAULT_SITE_AVAILABLE="${BANGI_NGINX_AVAILABLE_DIR}/${BANGI_NGINX_DEFAULT_SITE_NAME}"
BANGI_NGINX_DEFAULT_SITE_ENABLED="${BANGI_NGINX_ENABLED_DIR}/${BANGI_NGINX_DEFAULT_SITE_NAME}"
BANGI_NGINX_DEFAULT_TEMPLATE="${BANGI_RELEASE_TEMPLATE_DIR}/nginx.default.conf"

bangi_write_nginx_include() {
    local temporary_path="${BANGI_NGINX_INCLUDE_FILE}.tmp"

    install -d -m 0755 -o root -g root "$(dirname "${BANGI_NGINX_INCLUDE_FILE}")" \
        || bangi_fatal "Cannot create Nginx include directory: $(dirname "${BANGI_NGINX_INCLUDE_FILE}")"

    cat >"${temporary_path}" <<EOF \
        || bangi_fatal "Cannot write Nginx include configuration: ${BANGI_NGINX_INCLUDE_FILE}"
# Managed by Bangi installer. Local edits may be overwritten.
include ${BANGI_NGINX_ENABLED_DIR}/*;
EOF

    chown root:root "${temporary_path}" \
        || bangi_fatal "Cannot set ownership on Nginx include configuration: ${BANGI_NGINX_INCLUDE_FILE}"
    chmod 0644 "${temporary_path}" \
        || bangi_fatal "Cannot set permissions on Nginx include configuration: ${BANGI_NGINX_INCLUDE_FILE}"
    mv -f "${temporary_path}" "${BANGI_NGINX_INCLUDE_FILE}" \
        || bangi_fatal "Cannot install Nginx include configuration: ${BANGI_NGINX_INCLUDE_FILE}"
}

bangi_install_default_nginx_site() {
    [[ -f "${BANGI_NGINX_DEFAULT_TEMPLATE}" ]] \
        || bangi_fatal "Default Nginx site template is missing: ${BANGI_NGINX_DEFAULT_TEMPLATE}"

    install -m 0644 -o root -g root "${BANGI_NGINX_DEFAULT_TEMPLATE}" "${BANGI_NGINX_DEFAULT_SITE_AVAILABLE}" \
        || bangi_fatal "Cannot install default Bangi Nginx site: ${BANGI_NGINX_DEFAULT_SITE_AVAILABLE}"

    ln -sfn "${BANGI_NGINX_DEFAULT_SITE_AVAILABLE}" "${BANGI_NGINX_DEFAULT_SITE_ENABLED}" \
        || bangi_fatal "Cannot enable default Bangi Nginx site: ${BANGI_NGINX_DEFAULT_SITE_ENABLED}"
}

bangi_disable_packaged_nginx_default_site() {
    local packaged_default="/etc/nginx/sites-enabled/default"

    if [[ -L "${packaged_default}" ]]; then
        rm -f "${packaged_default}" \
            || bangi_fatal "Cannot disable packaged Nginx default site: ${packaged_default}"
    fi
}

bangi_validate_nginx() {
    bangi_log "Validating Nginx configuration"

    nginx -t \
        || bangi_fatal "Invalid Nginx configuration; fix Nginx errors before rerunning the installer"
}

bangi_reload_or_start_nginx() {
    bangi_log "Reloading or starting Nginx"

    if systemctl is-active --quiet nginx; then
        systemctl reload nginx \
            || bangi_fatal "Nginx reload failed after successful validation"
        return 0
    fi

    systemctl start nginx \
        || bangi_fatal "Nginx start failed after successful validation"
}

bangi_install_nginx() {
    bangi_log "Installing Bangi host Nginx baseline"

    install -d -m 0755 -o root -g root "${BANGI_NGINX_AVAILABLE_DIR}" "${BANGI_NGINX_ENABLED_DIR}" \
        || bangi_fatal "Cannot create Bangi Nginx workspace"

    bangi_write_nginx_include
    bangi_install_default_nginx_site
    bangi_disable_packaged_nginx_default_site
    bangi_validate_nginx
    bangi_reload_or_start_nginx
}

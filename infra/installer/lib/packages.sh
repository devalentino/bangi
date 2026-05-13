#!/usr/bin/env bash

BANGI_APT_BASE_PACKAGES=(
    ca-certificates
    curl
    gnupg
    sudo
    nginx
    cron
    openssl
    unzip
)

BANGI_DOCKER_PACKAGES=(
    docker-ce
    docker-ce-cli
    containerd.io
    docker-buildx-plugin
    docker-compose-plugin
)

bangi_package_step() {
    local description="$1"
    shift

    bangi_log "${description}"
    "$@" || bangi_fatal "Package installation failed during: ${description}"
}

bangi_configure_docker_apt_repository() {
    local codename="${VERSION_CODENAME:-${UBUNTU_CODENAME:-}}"
    local architecture=""
    local docker_source="/etc/apt/sources.list.d/docker.sources"

    if [[ -z "${codename}" ]]; then
        bangi_fatal "Package installation failed during: resolve Ubuntu package codename"
    fi

    architecture="$(dpkg --print-architecture)" \
        || bangi_fatal "Package installation failed during: resolve package architecture"

    bangi_package_step "create Docker apt keyring directory" install -m 0755 -d /etc/apt/keyrings

    if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
        bangi_package_step "download Docker apt signing key" \
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    fi

    bangi_package_step "set Docker apt signing key permissions" chmod a+r /etc/apt/keyrings/docker.asc

    if ! cat >"${docker_source}" <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${codename}
Components: stable
Architectures: ${architecture}
Signed-By: /etc/apt/keyrings/docker.asc
EOF
    then
        bangi_fatal "Package installation failed during: write Docker apt source"
    fi
}

bangi_enable_service() {
    local service_name="$1"

    bangi_package_step "enable and start ${service_name}" systemctl enable --now "${service_name}"
}

bangi_install_packages() {
    bangi_package_step "refresh apt package index" apt-get update
    bangi_package_step "install base host packages" apt-get install -y "${BANGI_APT_BASE_PACKAGES[@]}"
    bangi_configure_docker_apt_repository
    bangi_package_step "refresh apt package index with Docker repository" apt-get update
    bangi_package_step "install Docker Engine and Compose plugin" apt-get install -y "${BANGI_DOCKER_PACKAGES[@]}"

    bangi_enable_service docker
    bangi_enable_service nginx
    bangi_enable_service cron
    bangi_enable_service ssh
}

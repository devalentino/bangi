# Bangi Host Provisioning

The Bangi host provisioner installs a pinned Bangi release onto a fresh Ubuntu 24.04 LTS host.

## Install Command

Download the pinned installer to `/tmp` and run it with root privileges:

```bash
curl -fsSL https://raw.githubusercontent.com/devalentino/bangi/X.Y.Z/infra/installer/install.sh -o /tmp/bangi-install.sh
sudo bash /tmp/bangi-install.sh
```

The installer must run as root and validates Ubuntu 24.04 LTS before any package installation phase starts.

## Manual Verification

Installer behavior is verified manually on host environments for the MVP. Automated installer test coverage is out of scope.

For the installer skeleton, verify:

- running without root privileges fails before host changes
- running on a non-Ubuntu 24.04 host fails before package installation
- running on Ubuntu 24.04 as root reaches the installer phase orchestration

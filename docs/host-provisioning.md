# Bangi Host Provisioning

The Bangi host provisioner installs a pinned Bangi release onto a fresh Ubuntu 24.04 LTS host.

## Install Command

Download the pinned installer to `/tmp` and run it with root privileges:

```bash
curl -fsSL https://raw.githubusercontent.com/devalentino/bangi/X.Y.Z/infra/installer/install.sh -o /tmp/bangi-install.sh
sudo bash /tmp/bangi-install.sh
```

During installation, the wizard asks for the optional IP2Location download token. Leave it blank to skip automated refresh credentials. If a token is entered, the installer validates it against IP2Location and asks again when validation fails.

The installer writes the token to `/etc/bangi/ops.env`, not to the application runtime `.env`. On rerun, an existing value in `/etc/bangi/ops.env` is preserved.

The installer must run as root and validates Ubuntu 24.04 LTS before any package installation phase starts.

## Manual Verification

Installer behavior is verified manually on host environments for the MVP. Automated installer test coverage is out of scope.

For the installer skeleton, verify:

- running without root privileges fails before host changes
- running on a non-Ubuntu 24.04 host fails before package installation
- running on Ubuntu 24.04 as root reaches the installer phase orchestration

For managed cron installation, verify:

- `/etc/cron.d/bangi` exists after installer completion and contains a single Bangi-managed file body
- disk telemetry runs hourly from `/opt/bangi/current` through `scripts/ingest_disk_utilization.sh` and logs under `/var/log/bangi`
- with an empty `IP2LOCATION_DOWNLOAD_TOKEN` in `/etc/bangi/ops.env`, no IP2Location refresh cron entry is present
- with a non-empty `IP2LOCATION_DOWNLOAD_TOKEN`, the IP2Location refresh cron entry is `0 3 1,15 * *`, sources `/etc/bangi/ops.env`, and does not include the token value in the cron command

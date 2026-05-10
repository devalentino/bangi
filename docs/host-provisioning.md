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

## Host Operations From API Container

The API container can run a small allowlist of host operations through the `bangi-ops` SSH dispatcher. This is intentionally restricted; arbitrary shell commands are not allowed.

Enter the API container from the host:

```bash
cd /opt/bangi/current
sudo docker compose --project-name bangi --project-directory /opt/bangi/current -f /opt/bangi/current/compose.yml exec api sh
```

Run an allowed host operation from inside the API container:

```bash
ssh \
  -i "$BANGI_HOST_OPS_SSH_KEY_PATH" \
  -o UserKnownHostsFile="$BANGI_HOST_OPS_SSH_KNOWN_HOSTS_PATH" \
  -o StrictHostKeyChecking=yes \
  "$BANGI_HOST_OPS_SSH_USER@$BANGI_HOST_OPS_SSH_HOST" \
  nginx-validate
```

Allowed commands:

- `nginx-validate`: run `nginx -t` on the host
- `nginx-reload`: validate and reload host Nginx
- `refresh-ip2location`: run the installed IP2Location refresh script

Unsupported commands return `Unsupported Bangi ops command`.

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

For release activation and final health verification, verify:

- forcing any required health check to fail causes the installer to exit non-zero before `/opt/bangi/current` changes
- successful health verification checks `docker compose ps`, MariaDB, direct backend health, `nginx -t`, local frontend HTTP, Nginx `/api/v2/health`, and managed cron content
- after a successful run, `/opt/bangi/current` points to `/opt/bangi/${BANGI_RELEASE_TAG}`
- the completion summary prints the deployment bundle path, runtime and operational environment paths, compose service status, Nginx status, cron status, detected fallback URL when public IP detection succeeds, IP2Location refresh status, and operator next steps

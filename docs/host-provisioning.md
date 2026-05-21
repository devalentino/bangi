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

## Managed Swap

Before package installation, the provisioner checks active host swap. If active swap already exists, the installer leaves it unchanged and reports the detected swap status in the completion summary.

When no active swap exists and host memory is at or below `2 GB`, the installer creates a Bangi-managed `1G` swap file at `/swapfile`, secures it with `0600` permissions, enables it immediately, persists it in `/etc/fstab`, and writes Bangi swap tuning to `/etc/sysctl.d/99-bangi-swap.conf`.

Hosts above the memory threshold do not receive managed swap by default. Operators can force managed swap creation by running the installer with `BANGI_SWAP_FORCE=true`.

## Host Firewall And Lifecycle

The provisioner installs `iptables` and stores the canonical Bangi-managed firewall policy at `/opt/bangi/shared/firewall/iptables.rules`. The policy allows inbound TCP `22`, `80`, and `443`, allows established and loopback traffic, and drops other host inbound traffic. Production Compose keeps `web`, `api`, and `landing-renderer` bound to loopback so host Nginx remains the public edge.

The installer also installs `/opt/bangi/ops/bin/apply-iptables` and `/etc/systemd/system/bangi.service`. `bangi.service` runs the apply command before starting Docker Compose, so firewall rules are reapplied on boot and before each stack start. Operators should manage the stack with:

```bash
sudo systemctl start bangi
sudo systemctl stop bangi
sudo systemctl restart bangi
```

If active `ufw` is detected, an interactive install explains the switch to Bangi-managed `iptables` and continues only after the operator types `yes`. Non-interactive installs fail unless `BANGI_DISABLE_UFW_CONFIRMED=true` is set.

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

## Landing Renderer Path

The production stack mounts landing assets into the renderer at `/var/www/html/landings`, and new installs set `LANDING_PAGE_RENDERER_BASE_URL=http://landing-renderer/landings` in `/opt/bangi/shared/env/.env`.

For existing installs created with `LANDING_PAGE_RENDERER_BASE_URL=http://landing-renderer`, update `/opt/bangi/shared/env/.env` to:

```bash
LANDING_PAGE_RENDERER_BASE_URL=http://landing-renderer/landings
```

Then restart the API or stack so API renderer requests use `/landings/{flow_id}/`.

Campaign domain Nginx configs also proxy sticky-flow renderer requests through `/landings/{flow_id}`. Existing campaign configs generated before this fix must be republished or regenerated and reloaded after deploying the updated templates.

## Manual Verification

Host-level installer behavior is verified manually on host environments for the MVP.

For the installer skeleton, verify:

- running without root privileges fails before host changes
- running on a non-Ubuntu 24.04 host fails before package installation
- running on Ubuntu 24.04 as root reaches the installer phase orchestration

For managed swap installation, verify:

- on a fresh Ubuntu 24.04 host with no active swap and `2 GB` RAM or less, the installer creates `/swapfile`, sets permissions to `0600`, enables it in `swapon --show`, and writes a single `/swapfile none swap sw 0 0` entry to `/etc/fstab`
- rerunning the installer does not duplicate the `/etc/fstab` entry or duplicate sysctl configuration in `/etc/sysctl.d/99-bangi-swap.conf`
- on a host with existing active swap, the installer does not modify the existing swap device or file and reports it in the completion summary
- on a host above `2 GB` RAM with no active swap, the installer does not create `/swapfile` unless `BANGI_SWAP_FORCE=true` is set
- after reboot, `swapon --show` includes `/swapfile` when Bangi-managed swap was created

For managed cron installation, verify:

- `/etc/cron.d/bangi` exists after installer completion and contains a single Bangi-managed file body
- disk telemetry runs hourly from `/opt/bangi/current` through `scripts/ingest_disk_utilization.sh` and logs under `/var/log/bangi`
- with an empty `IP2LOCATION_DOWNLOAD_TOKEN` in `/etc/bangi/ops.env`, no IP2Location refresh cron entry is present
- with a non-empty `IP2LOCATION_DOWNLOAD_TOKEN`, the IP2Location refresh cron entry is `0 3 1,15 * *`, sources `/etc/bangi/ops.env`, and does not include the token value in the cron command

For release activation and final health verification, verify:

- forcing any required health check to fail causes the installer to exit non-zero before `/opt/bangi/current` changes
- successful health verification checks Bangi firewall installation, `docker compose ps`, MariaDB, direct backend health, `nginx -t`, local frontend HTTP, Nginx `/api/v2/health`, and managed cron content
- after a successful run, `/opt/bangi/current` points to `/opt/bangi/${BANGI_RELEASE_TAG}`
- the completion summary prints the deployment bundle path, runtime and operational environment paths, compose service status, Nginx status, cron status, firewall status, swap status, detected fallback URL when public IP detection succeeds, IP2Location refresh status, and operator next steps

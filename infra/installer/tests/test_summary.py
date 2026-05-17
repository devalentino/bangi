import shlex
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
INSTALL_SCRIPT = REPO_ROOT / "infra/installer/install.sh"


def run_summary(runtime_env: str) -> str:
    runtime_env_content = textwrap.dedent(runtime_env).strip() + "\n"
    ops_env_content = "IP2LOCATION_DOWNLOAD_TOKEN=\n"
    script = f"""
    set -Eeuo pipefail
    workdir="$(mktemp -d)"
    export BANGI_RELEASE_TAG="test-release"
    export BANGI_SHARED_DIR="${{workdir}}/shared"
    export BANGI_SHARED_ENV_DIR="${{BANGI_SHARED_DIR}}/env"
    export BANGI_SHARED_IP2LOCATION_DIR="${{BANGI_SHARED_DIR}}/ip2location"
    export BANGI_SHARED_FIREWALL_DIR="${{BANGI_SHARED_DIR}}/firewall"
    export BANGI_ETC_DIR="${{workdir}}/etc"
    mkdir -p "${{BANGI_SHARED_ENV_DIR}}" "${{BANGI_SHARED_IP2LOCATION_DIR}}" "${{BANGI_SHARED_FIREWALL_DIR}}" "${{BANGI_ETC_DIR}}"
    printf %s {shlex.quote(runtime_env_content)} >"${{BANGI_SHARED_ENV_DIR}}/.env"
    printf %s {shlex.quote(ops_env_content)} >"${{BANGI_ETC_DIR}}/ops.env"
    export BANGI_ROOT_DIR="${{workdir}}/opt/bangi"
    export BANGI_RELEASE_DIR="${{BANGI_ROOT_DIR}}/test-release"
    export BANGI_CURRENT_LINK="${{BANGI_ROOT_DIR}}/current"
    export BANGI_IPTABLES_RULES_FILE="${{BANGI_SHARED_FIREWALL_DIR}}/iptables.rules"
    export BANGI_OPS_BIN_DIR="${{BANGI_ROOT_DIR}}/ops/bin"
    export BANGI_IPTABLES_APPLY_SCRIPT="${{BANGI_OPS_BIN_DIR}}/apply-iptables"
    export BANGI_OPS_ENV_FILE="${{BANGI_ETC_DIR}}/ops.env"
    export BANGI_CRON_FILE="${{workdir}}/cron.d/bangi"
    export BANGI_LOG_DIR="${{workdir}}/log/bangi"
    export BANGI_COMPOSE_PROJECT_NAME="bangi"
    mkdir -p "${{BANGI_RELEASE_DIR}}" "${{BANGI_OPS_BIN_DIR}}" "$(dirname "${{BANGI_CRON_FILE}}")"
    ln -s "${{BANGI_RELEASE_DIR}}" "${{BANGI_CURRENT_LINK}}"
    touch "${{BANGI_IPTABLES_RULES_FILE}}" "${{BANGI_IPTABLES_APPLY_SCRIPT}}"
    chmod +x "${{BANGI_IPTABLES_APPLY_SCRIPT}}"
    source "{REPO_ROOT / 'infra/installer/lib/env.sh'}"
    source "{REPO_ROOT / 'infra/installer/lib/common.sh'}"
    systemctl() {{ return 1; }}
    iptables() {{ return 1; }}
    bangi_compose() {{ printf 'NAME STATUS\\nweb running\\napi running\\n'; }}
    bangi_detect_public_host() {{ printf '198.51.100.44\\n'; }}
    bangi_print_summary
    """
    result = subprocess.run(
        ["bash", "-c", textwrap.dedent(script)],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def test_summary_prints_distinct_dashboard_sign_in_block_with_current_credentials():
    output = run_summary(
        """
        BASIC_AUTHENTICATION_USERNAME=admin
        BASIC_AUTHENTICATION_PASSWORD=generated-password
        BANGI_PUBLIC_HOST_IP=203.0.113.10
        """
    )

    assert (
        "============================================================\n"
        "  BANGI DASHBOARD SIGN-IN\n"
        "============================================================\n"
        "  Dashboard URL: http://203.0.113.10\n"
        "  Username:      admin\n"
        "  Password:      generated-password\n"
        "============================================================\n"
        "  API health URL: http://203.0.113.10/api/v2/health\n"
    ) in output
    assert output.index("BANGI DASHBOARD SIGN-IN") < output.index("Bangi deployment summary")


def test_summary_prints_preserved_password_from_existing_runtime_env():
    output = run_summary(
        """
        BASIC_AUTHENTICATION_USERNAME=operator
        BASIC_AUTHENTICATION_PASSWORD=preserved-password
        BANGI_PUBLIC_HOST_IP=203.0.113.20
        """
    )

    assert "  Username:      operator\n" in output
    assert "  Password:      preserved-password\n" in output


def test_summary_uses_detected_host_when_runtime_host_is_blank():
    output = run_summary(
        """
        BASIC_AUTHENTICATION_USERNAME=admin
        BASIC_AUTHENTICATION_PASSWORD=generated-password
        BANGI_PUBLIC_HOST_IP=
        """
    )

    assert "  Dashboard URL: http://198.51.100.44\n" in output
    assert "  API health URL: http://198.51.100.44/api/v2/health\n" in output


def test_install_script_prints_summary_only_after_health_verification():
    install_script = INSTALL_SCRIPT.read_text(encoding="utf-8")

    assert install_script.index("bangi_verify_health") < install_script.index("bangi_print_summary")

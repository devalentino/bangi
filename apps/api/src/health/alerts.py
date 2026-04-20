from datetime import datetime, timezone

from src.alerts import Alert, AlertCode, AlertSeverity, register_alert_callback
from src.health.services import HealthService


@register_alert_callback
def collect_disk_utilization_alerts(container):
    summary = container.get(HealthService).latest_disk_utilization_summary()

    if summary.stale:
        last_received_at = datetime.fromtimestamp(summary.last_received_at, tz=timezone.utc).isoformat()
        return [
            Alert(
                code=AlertCode.SYSTEM_HEALTH_TELEMETRY_STALE,
                severity=AlertSeverity.ERROR,
                message=f'Host disk telemetry is stale. Last successful report was {last_received_at}.',
                payload={
                    'filesystem': summary.filesystem,
                    'mountpoint': summary.mountpoint,
                    'lastReceivedAt': summary.last_received_at,
                },
            )
        ]

    if summary.severity == 'critical':
        return [
            Alert(
                code=AlertCode.SYSTEM_HEALTH_DISK_CRITICAL,
                severity=AlertSeverity.ERROR,
                message=f'Host disk usage is critical at {summary.used_percent:.1f}% on {summary.mountpoint}.',
                payload={
                    'filesystem': summary.filesystem,
                    'mountpoint': summary.mountpoint,
                    'usedPercent': summary.used_percent,
                },
            )
        ]

    if summary.severity == 'warning':
        return [
            Alert(
                code=AlertCode.SYSTEM_HEALTH_DISK_WARNING,
                severity=AlertSeverity.WARNING,
                message=f'Host disk usage is at {summary.used_percent:.1f}% on {summary.mountpoint}.',
                payload={
                    'filesystem': summary.filesystem,
                    'mountpoint': summary.mountpoint,
                    'usedPercent': summary.used_percent,
                },
            )
        ]

    return []

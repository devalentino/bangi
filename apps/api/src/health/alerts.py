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


@register_alert_callback
def collect_nginx_validation_alerts(container):
    snapshot = container.get(HealthService).latest_nginx_validation_snapshot()

    if snapshot is None or snapshot.validation_status != 'failed':
        return []

    validation_timestamp = int(snapshot.created_at.timestamp())
    message = 'Latest Nginx validation failed.'
    if snapshot.domain_id is not None:
        message = f'Latest Nginx validation failed for domain {snapshot.domain_id}.'
    if snapshot.validation_error:
        message = f'{message} {snapshot.validation_error}'

    return [
        Alert(
            code=AlertCode.SYSTEM_HEALTH_NGINX_VALIDATION_FAILED,
            severity=AlertSeverity.ERROR,
            message=message,
            payload={
                'domainId': snapshot.domain_id,
                'validationTimestamp': validation_timestamp,
                'validationError': snapshot.validation_error,
            },
        )
    ]

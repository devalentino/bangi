from time import time as time_timestamp

from src.alerts import Alert, AlertCode, AlertSeverity, register_alert_callback
from src.domains.enums import DomainCertificateStatus
from src.health.services import HealthService


@register_alert_callback
def collect_certificate_alerts(container) -> list[Alert]:
    health_service = container.get(HealthService)
    now = int(time_timestamp())
    warning_cutoff = now + health_service.certificate_warning_days * 24 * 60 * 60
    error_cutoff = now + health_service.certificate_error_days * 24 * 60 * 60
    alerts = []

    for diagnostic in health_service.certificate_diagnostics():
        expires_at = diagnostic['expires_at']
        if diagnostic['status'] == DomainCertificateStatus.failed.value and diagnostic['last_issued_at'] is None:
            if diagnostic['failure_count'] < 2:
                continue
            code = AlertCode.SYSTEM_HEALTH_CERTIFICATE_ISSUANCE_FAILED
            severity = AlertSeverity.WARNING
            message = f'Certificate issuance failed repeatedly for {diagnostic["hostname"]}.'
        elif expires_at is not None and (
            diagnostic['status'] == DomainCertificateStatus.expired.value or int(expires_at.timestamp()) <= now
        ):
            code = AlertCode.SYSTEM_HEALTH_CERTIFICATE_EXPIRED
            severity = AlertSeverity.ERROR
            message = f'Certificate for {diagnostic["hostname"]} is expired.'
        elif (
            diagnostic['status'] == DomainCertificateStatus.failed.value
            and diagnostic['last_issued_at'] is not None
            and expires_at is not None
            and int(expires_at.timestamp()) <= error_cutoff
        ):
            code = AlertCode.SYSTEM_HEALTH_CERTIFICATE_RENEWAL_ERROR
            severity = AlertSeverity.ERROR
            message = f'Certificate renewal failed for {diagnostic["hostname"]} and expires within 7 days.'
        elif (
            diagnostic['status'] == DomainCertificateStatus.failed.value
            and diagnostic['last_issued_at'] is not None
            and expires_at is not None
            and int(expires_at.timestamp()) <= warning_cutoff
        ):
            code = AlertCode.SYSTEM_HEALTH_CERTIFICATE_RENEWAL_WARNING
            severity = AlertSeverity.WARNING
            message = f'Certificate renewal failed for {diagnostic["hostname"]} and expires within 14 days.'
        else:
            continue

        alerts.append(
            Alert(
                code=code,
                message=message,
                severity=severity,
                payload={
                    'domainId': diagnostic['domain_id'],
                    'hostname': diagnostic['hostname'],
                    'status': diagnostic['status'],
                    'expiresAt': None if expires_at is None else int(expires_at.timestamp()),
                    'lastAttemptedAt': (
                        None
                        if diagnostic['last_attempted_at'] is None
                        else int(diagnostic['last_attempted_at'].timestamp())
                    ),
                    'failureCount': diagnostic['failure_count'],
                    'failureReason': diagnostic['failure_reason'],
                },
            )
        )

    return alerts

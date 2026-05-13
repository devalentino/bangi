import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

from src.container import container
from src.core.supervisor import WorkerContext, register_worker
from src.domains.enums import DomainCertificateStatus
from src.domains.services import (
    AcmeExecutionSnapshot,
    AcmeService,
    CertificateService,
    DnsService,
    WebserverService,
)

logger = logging.getLogger(__name__)

LAST_EXECUTED_AT_STATE_KEY = 'last_executed_at'
CERTIFICATE_RENEWAL_PERIOD_SECONDS = 10 * 60
CERTIFICATE_RENEWAL_MAX_CANDIDATES = 2
CERTIFICATE_RENEWAL_WINDOW_DAYS = 30


def _is_acme_enabled() -> bool:
    return os.getenv('BANGI_ACME_ENABLED', 'true').lower() == 'true'


def _get_public_host_ip() -> str:
    return os.getenv('BANGI_PUBLIC_HOST_IP', '')


def _fetch_certificate_candidates(database, now: int) -> list[dict[str, object]]:
    renewal_window_at = now + int(timedelta(days=CERTIFICATE_RENEWAL_WINDOW_DAYS).total_seconds())
    cursor = database.execute_sql(
        (
            'SELECT domain.id, domain.hostname, domain.purpose, domain.campaign_id, '
            'domain.is_a_record_set, domain.is_disabled, '
            'domain_certificate.id AS certificate_id, domain_certificate.status AS certificate_status, '
            'domain_certificate.certificate_path, domain_certificate.private_key_path, '
            'domain_certificate.expires_at, domain_certificate.next_retry_at '
            'FROM domain '
            'LEFT JOIN domain_certificate ON domain_certificate.domain_id = domain.id '
            'WHERE domain.is_disabled = FALSE '
            'AND ('
            '  (domain_certificate.id IS NOT NULL '
            '    AND domain_certificate.status IN (%s, %s) '
            '    AND (domain_certificate.expires_at IS NULL OR domain_certificate.expires_at <= %s)) '
            '  OR (domain_certificate.id IS NOT NULL '
            '    AND domain_certificate.status = %s '
            '    AND (domain_certificate.next_retry_at IS NULL OR domain_certificate.next_retry_at <= %s)) '
            '  OR domain_certificate.id IS NULL'
            ') '
            'ORDER BY '
            'CASE '
            '  WHEN domain_certificate.id IS NOT NULL '
            '    AND domain_certificate.status IN (%s, %s) '
            '    AND (domain_certificate.expires_at IS NULL OR domain_certificate.expires_at <= %s) THEN 0 '
            '  WHEN domain_certificate.id IS NOT NULL AND domain_certificate.status = %s THEN 1 '
            '  ELSE 2 '
            'END ASC, '
            'domain_certificate.expires_at ASC, domain.id ASC '
            'LIMIT %s'
        ),
        (
            DomainCertificateStatus.active.value,
            DomainCertificateStatus.expired.value,
            renewal_window_at,
            DomainCertificateStatus.failed.value,
            now,
            DomainCertificateStatus.active.value,
            DomainCertificateStatus.expired.value,
            renewal_window_at,
            DomainCertificateStatus.failed.value,
            CERTIFICATE_RENEWAL_MAX_CANDIDATES,
        ),
    )
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def _get_or_create_flow_id_cookie_name(database, domain_id: int) -> str | None:
    cursor = database.execute_sql(
        'SELECT opaque_name FROM domain_cookie WHERE domain_id = %s AND name = %s',
        (domain_id, 'flow_id'),
    )
    row = cursor.fetchone()
    return None if row is None else row[0]


def _flush_nginx_validation_snapshot(database, domain_id: int, snapshot) -> None:
    database.execute_sql(
        (
            'INSERT INTO health_nginx_validation_snapshot '
            '(created_at, domain_id, validation_status, validation_error, sites_available_files, sites_enabled_refs) '
            'VALUES (UTC_TIMESTAMP(), %s, %s, %s, %s, %s)'
        ),
        (
            domain_id,
            snapshot.validation_status,
            snapshot.validation_error,
            json.dumps(snapshot.sites_available_files),
            json.dumps(snapshot.sites_enabled_refs),
        ),
    )
    database.commit()


def _pending_snapshot(hostname: str, is_renewal: bool) -> AcmeExecutionSnapshot:
    return AcmeExecutionSnapshot(
        status=DomainCertificateStatus.pending.value,
        hostname=hostname,
        certificate_path=None,
        private_key_path=None,
        issued_at=None,
        expires_at=None,
        error=None,
        is_renewal=is_renewal,
    )


def _should_renew(candidate: dict[str, object]) -> bool:
    return candidate['certificate_status'] in {
        DomainCertificateStatus.active.value,
        DomainCertificateStatus.expired.value,
    }


def _publish_https_config(database, candidate: dict[str, object], certificate) -> None:
    flow_id_cookie_name = None
    if candidate['purpose'] == 'campaign':
        flow_id_cookie_name = _get_or_create_flow_id_cookie_name(database, int(candidate['id']))
        if flow_id_cookie_name is None:
            logger.warning(
                'Skipping managed certificate HTTPS publish because campaign flow cookie is missing',
                extra={'domain_id': candidate['id'], 'hostname': candidate['hostname']},
            )
            return

    webserver_service = container.get(WebserverService)
    snapshot = webserver_service.publish(
        candidate['hostname'],
        candidate['purpose'],
        candidate['campaign_id'],
        flow_id_cookie_name,
        False,
        True,
        certificate.certificate_path,
        certificate.private_key_path,
    )
    _flush_nginx_validation_snapshot(database, int(candidate['id']), snapshot)


@register_worker
def renew_ca_certificates_worker(context: WorkerContext) -> None:
    state = context.get_state(renew_ca_certificates_worker)

    started_at = time.monotonic()
    last_executed_at = state.get(LAST_EXECUTED_AT_STATE_KEY)
    if last_executed_at and started_at - last_executed_at < CERTIFICATE_RENEWAL_PERIOD_SECONDS:
        return

    if not _is_acme_enabled():
        logger.info('Managed certificate renewal skipped because BANGI_ACME_ENABLED=false')
        state[LAST_EXECUTED_AT_STATE_KEY] = started_at
        return

    public_host_ip = _get_public_host_ip()
    if not public_host_ip:
        logger.warning('Managed certificate renewal skipped because BANGI_PUBLIC_HOST_IP is blank')
        state[LAST_EXECUTED_AT_STATE_KEY] = started_at
        return

    now = int(datetime.now(timezone.utc).timestamp())
    database = context.database
    certificate_service = container.get(CertificateService)
    acme_service = container.get(AcmeService)

    processed_domain_ids = []
    skipped_domain_ids = []
    for candidate in _fetch_certificate_candidates(database, now):
        domain_id = int(candidate['id'])
        hostname = candidate['hostname']
        if not DnsService.has_a_record(hostname, public_host_ip):
            skipped_domain_ids.append(domain_id)
            continue

        is_renewal = _should_renew(candidate)
        certificate_service.update_status(domain_id, _pending_snapshot(hostname, is_renewal))
        snapshot = acme_service.renew(hostname) if is_renewal else acme_service.issue(hostname)
        certificate = certificate_service.update_status(domain_id, snapshot)
        processed_domain_ids.append(domain_id)

        if certificate.status == DomainCertificateStatus.active.value:
            _publish_https_config(database, candidate, certificate)

    logger.info(
        'Managed certificate renewal is completed',
        extra={'processed_domain_ids': processed_domain_ids, 'skipped_domain_ids': skipped_domain_ids},
    )
    state[LAST_EXECUTED_AT_STATE_KEY] = started_at

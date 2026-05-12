import json
import logging
import os
import time

from src.container import container
from src.core.supervisor import WorkerContext, register_worker
from src.domains.services import DnsService, NginxService

logger = logging.getLogger(__name__)

LAST_EXECUTED_AT_STATE_KEY = 'last_executed_at'
DOMAIN_DNS_REFRESH_PERIOD_SECONDS = 5 * 60


def _get_public_host_ip() -> str:
    return os.getenv('BANGI_PUBLIC_HOST_IP', '')


def _fetch_domains_needing_refresh(database):
    cursor = database.execute_sql(
        (
            'SELECT id, hostname, purpose, campaign_id, is_a_record_set, is_disabled '
            'FROM domain WHERE is_a_record_set IS NULL OR is_a_record_set = FALSE ORDER BY id ASC'
        )
    )
    return cursor.fetchall()


def _bulk_update_domain_dns_states(database, updates: list[tuple[int, bool]]) -> None:
    if not updates:
        return

    true_domain_ids = [domain_id for domain_id, current_state in updates if current_state]
    false_domain_ids = [domain_id for domain_id, current_state in updates if not current_state]

    if true_domain_ids:
        placeholders = ', '.join(['%s'] * len(true_domain_ids))
        database.execute_sql(
            f'UPDATE domain SET is_a_record_set = TRUE WHERE id IN ({placeholders})',
            true_domain_ids,
        )

    if false_domain_ids:
        placeholders = ', '.join(['%s'] * len(false_domain_ids))
        database.execute_sql(
            f'UPDATE domain SET is_a_record_set = FALSE WHERE id IN ({placeholders})',
            false_domain_ids,
        )

    database.commit()


def _flush_nginx_validation_snapshots(database, snapshots: list[dict[str, object]]) -> None:
    if not snapshots:
        return

    rows = [
        (
            snapshot['domain_id'],
            snapshot['validation_status'],
            snapshot['validation_error'],
            snapshot['sites_available_files'],
            snapshot['sites_enabled_refs'],
        )
        for snapshot in snapshots
    ]

    placeholders = ', '.join(['(UTC_TIMESTAMP(), %s, %s, %s, %s, %s)'] * len(rows))
    params: list[object] = []
    for domain_id, validation_status, validation_error, sites_available_files, sites_enabled_refs in rows:
        params.extend([domain_id, validation_status, validation_error, sites_available_files, sites_enabled_refs])

    database.execute_sql(
        (
            'INSERT INTO health_nginx_validation_snapshot '
            '(created_at, domain_id, validation_status, validation_error, sites_available_files, sites_enabled_refs) '
            f'VALUES {placeholders}'
        ),
        params,
    )
    database.commit()


@register_worker
def refresh_domain_dns_worker(context: WorkerContext) -> None:
    state = context.get_state(refresh_domain_dns_worker)

    started_at = time.monotonic()
    last_executed_at = state.get(LAST_EXECUTED_AT_STATE_KEY)
    if last_executed_at and started_at - last_executed_at < DOMAIN_DNS_REFRESH_PERIOD_SECONDS:
        return

    public_host_ip = _get_public_host_ip()
    if not public_host_ip:
        logger.warning('Managed domain DNS refresh skipped because BANGI_PUBLIC_HOST_IP is blank')
        return

    logger.info(
        'Refreshing managed domain DNS state',
        extra={'cadence_seconds': DOMAIN_DNS_REFRESH_PERIOD_SECONDS, 'public_host_ip': public_host_ip},
    )

    database = context.database
    nginx_service = container.get(NginxService)
    pending_updates = []
    processed_domain_ids = []
    pending_snapshots = []

    for domain_id, hostname, purpose, campaign_id, is_a_record_set, is_disabled in _fetch_domains_needing_refresh(
        database
    ):
        current_state = DnsService.has_a_record(hostname, public_host_ip)
        previous_state = None if is_a_record_set is None else bool(is_a_record_set)

        if previous_state is not None and previous_state == current_state:
            continue

        if current_state:
            snapshot = nginx_service.publish(
                hostname,
                domain_id,
                purpose,
                campaign_id,
                bool(is_disabled),
                current_state,
            )
            if snapshot.validation_status != 'success':
                logger.warning(
                    'Managed domain publish failed during DNS refresh',
                    extra={
                        'domain_id': domain_id,
                        'hostname': hostname,
                        'validation_error': snapshot.validation_error,
                    },
                )
            pending_snapshots.append(
                {
                    'domain_id': domain_id,
                    'validation_status': snapshot.validation_status,
                    'validation_error': snapshot.validation_error,
                    'sites_available_files': json.dumps(snapshot.sites_available_files),
                    'sites_enabled_refs': json.dumps(snapshot.sites_enabled_refs),
                }
            )

        processed_domain_ids.append(domain_id)
        pending_updates.append((domain_id, current_state))

    _bulk_update_domain_dns_states(database, pending_updates)
    _flush_nginx_validation_snapshots(database, pending_snapshots)

    logger.info(
        'Managed domain DNS refresh is completed',
        extra={
            'processed_domain_ids': processed_domain_ids,
            'updated_domain_ids': [domain_id for domain_id, _ in pending_updates],
        },
    )

    state[LAST_EXECUTED_AT_STATE_KEY] = started_at

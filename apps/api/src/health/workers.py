import logging
import time

from src.core.supervisor import WorkerContext, register_worker
from src.health.entities import DiskUtilization

logger = logging.getLogger(__name__)

LAST_EXECUTED_AT_STATE_KEY = 'last_executed_at'
DISK_UTILIZATION_HISTORY_RETENTION_DAYS = 30
DISK_UTILIZATION_HISTORY_CLEANUP_PERIOD_SECONDS = 60 * 60


@register_worker
def cleanup_disk_utilization_worker(context: WorkerContext) -> None:
    state = context.get_state(cleanup_disk_utilization_worker)

    started_at = time.monotonic()
    last_executed_at = state.get(LAST_EXECUTED_AT_STATE_KEY)
    if last_executed_at and started_at - last_executed_at < DISK_UTILIZATION_HISTORY_CLEANUP_PERIOD_SECONDS:
        return

    cutoff = int(time.time()) - DISK_UTILIZATION_HISTORY_RETENTION_DAYS * 24 * 60 * 60
    logger.info(
        'Cleaning up health_disk_utilization table',
        extra={
            'cutoff': cutoff,
            'retention_days': DISK_UTILIZATION_HISTORY_RETENTION_DAYS,
        },
    )

    deleted_rows = DiskUtilization.delete().where(DiskUtilization.created_at < cutoff).execute()
    duration_ms = int((time.monotonic() - started_at) * 1000)

    logger.info(
        'health_disk_utilization cleanup is completed',
        extra={
            'cutoff': cutoff,
            'retention_days': DISK_UTILIZATION_HISTORY_RETENTION_DAYS,
            'deleted_rows': deleted_rows,
            'duration_ms': duration_ms,
        },
    )

    state[LAST_EXECUTED_AT_STATE_KEY] = started_at

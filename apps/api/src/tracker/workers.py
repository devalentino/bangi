import logging
import time

from src.core.supervisor import WorkerContext, register_worker
from src.tracker.entities import TrackDiscard

logger = logging.getLogger(__name__)

LAST_EXECUTED_AT_STATE_KEY = 'last_executed_at'
DISCARD_RETENTION_SECONDS = 30 * 60 * 60
DISCARD_CLEANUP_PERIOD_SECONDS = 5 * 60


@register_worker
def cleanup_discard_worker(context: WorkerContext) -> None:
    state = context.get_state(cleanup_discard_worker)

    started_at = time.monotonic()
    last_executed_at = state.get(LAST_EXECUTED_AT_STATE_KEY)
    if last_executed_at and started_at - last_executed_at < DISCARD_CLEANUP_PERIOD_SECONDS:
        return

    cutoff = int(time.time()) - DISCARD_RETENTION_SECONDS
    logger.info(
        'Cleaning up track_discard table',
        extra={
            'cutoff': cutoff,
            'retention_seconds': DISCARD_RETENTION_SECONDS,
        },
    )

    deleted_rows = TrackDiscard.delete().where(TrackDiscard.created_at < cutoff).execute()
    duration_ms = int((time.monotonic() - started_at) * 1000)

    logger.info(
        'track_discard cleanup is completed',
        extra={
            'cutoff': cutoff,
            'retention_seconds': DISCARD_RETENTION_SECONDS,
            'deleted_rows': deleted_rows,
            'duration_ms': duration_ms,
        },
    )

    state[LAST_EXECUTED_AT_STATE_KEY] = started_at

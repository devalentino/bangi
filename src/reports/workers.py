import logging
from queue import Empty
from time import monotonic

from peewee import JOIN
from src.core.supervisor import WorkerContext, register_worker
from src.reports.entities import ReportLead
from src.tracker.entities import TrackClick, TrackPostback
from src.tracker.enums import TrackSource

logger = logging.getLogger(__name__)

LAST_EXECUTED_AT_STATE_KEY = 'last_executed_at'
MIN_QUEUE_SIZE = 10
AGGREGATION_PERIOD_SECONDS = 10


@register_worker
def refresh_report_leads_worker(context: WorkerContext) -> None:
    queue = context.get_queue(refresh_report_leads_worker)
    state = context.get_state(refresh_report_leads_worker)
    if queue.qsize() == 0:
        return

    now = monotonic()
    last_executed_at = state.get(LAST_EXECUTED_AT_STATE_KEY)
    if queue.qsize() < MIN_QUEUE_SIZE and last_executed_at and now - last_executed_at < AGGREGATION_PERIOD_SECONDS:
        return

    lead_click_ids = set()
    postback_click_ids = set()
    while True:
        try:
            payload = queue.get_nowait()
        except Empty:
            break

        click_id = payload.get('click_id')
        source = payload.get('source')
        if click_id is None or source not in {TrackSource.lead.value, TrackSource.postback.value}:
            logger.warning('Tracked bad report lead payload', extra={'payload': payload})
            continue

        if source == TrackSource.lead.value:
            lead_click_ids.add(click_id)
        elif source == TrackSource.postback.value:
            postback_click_ids.add(click_id)

    logger.info(
        'Refreshing report_lead table',
        extra={'lead_click_ids': list(lead_click_ids), 'postback_click_ids': list(postback_click_ids)},
    )

    try:
        _upsert_report_leads_for_leads(lead_click_ids)
    except Exception:
        logger.exception('Failed to report_lead table from lead events', extra={'click_ids': list(lead_click_ids)})

    try:
        _upsert_report_leads_for_postbacks(postback_click_ids)
    except Exception:
        logger.exception(
            'Failed to report_lead table from postback events',
            extra={'click_ids': list(postback_click_ids)},
        )

    logger.info(
        'Refreshing report_lead table is completed',
        extra={'lead_click_ids': list(lead_click_ids), 'postback_click_ids': list(postback_click_ids)},
    )

    state[LAST_EXECUTED_AT_STATE_KEY] = now


def _upsert_report_leads_for_leads(click_ids: set) -> None:
    if not click_ids:
        return

    select_query = TrackClick.select(
        TrackClick.click_id,
        TrackClick.campaign_id,
        TrackClick.created_at,
    ).where(TrackClick.click_id.in_(click_ids))

    insert_query = ReportLead.insert_from(
        select_query,
        fields=[
            ReportLead.click_id,
            ReportLead.campaign_id,
            ReportLead.click_created_at,
        ],
    )
    insert_query.on_conflict_ignore().execute()


def _upsert_report_leads_for_postbacks(click_ids: set) -> None:
    if not click_ids:
        return

    query = (
        TrackClick.select(
            TrackClick.click_id,
            TrackClick.campaign_id,
            TrackClick.created_at,
            TrackPostback.status,
            TrackPostback.cost_value,
            TrackPostback.currency,
        )
        .join(TrackPostback, JOIN.INNER, on=(TrackClick.click_id == TrackPostback.click_id))
        .where(TrackClick.click_id.in_(click_ids))
        .order_by(TrackClick.click_id, TrackPostback.id.desc())
    )

    rows = []
    processed_click_ids = set()
    for row in query.dicts():
        click_id = row['click_id']
        if click_id in processed_click_ids:
            continue

        processed_click_ids.add(click_id)
        rows.append(
            {
                'click_id': row['click_id'],
                'campaign_id': row['campaign_id'],
                'click_created_at': row['created_at'],
                'status': row['status'],
                'cost_value': row['cost_value'],
                'currency': row['currency'],
            }
        )

    if not rows:
        return

    insert_query = ReportLead.insert_many(rows)
    insert_query.on_conflict(
        conflict_target=[ReportLead.click_id],
        update={
            ReportLead.campaign_id: insert_query.inserted.campaign_id,
            ReportLead.click_created_at: insert_query.inserted.click_created_at,
            ReportLead.status: insert_query.inserted.status,
            ReportLead.cost_value: insert_query.inserted.cost_value,
            ReportLead.currency: insert_query.inserted.currency,
        },
    ).execute()

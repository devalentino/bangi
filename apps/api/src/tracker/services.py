import logging
from typing import Optional

from peewee import fn
from wireup import injectable

from src.core.entities import Campaign
from src.core.enums import LeadStatus
from src.core.supervisor import WorkerSupervisor
from src.reports.workers import refresh_report_leads_worker
from src.tracker.entities import TrackClick, TrackDiscard, TrackLead, TrackPostback
from src.tracker.enums import TrackSource

logger = logging.getLogger(__name__)


@injectable
class TrackService:
    def __init__(self, worker_supervisor: WorkerSupervisor):
        self.worker_supervisor = worker_supervisor

    def _get_campaign_by_click_id(self, click_id: str) -> Optional[Campaign]:
        click = TrackClick.get_or_none(TrackClick.click_id == click_id)
        if click is None:
            logger.warning('Failed to find click', extra={'click_id': click_id})
            return None

        campaign = Campaign.get_or_none(Campaign.id == click.campaign_id)
        if campaign is None:
            logger.warning('Failed to find campaign', extra={'campaign_id': click.campaign_id})
            return None

        return campaign

    def _map_status(self, parameters: dict, status_mapper) -> str:
        if not isinstance(status_mapper, dict):
            logger.warning('Failed to get status mapper', extra={'status_mapper': status_mapper})
            return LeadStatus.trash.value

        status_parameter = status_mapper.get('parameter')
        if not status_parameter:
            logger.warning('Failed to get external status parameter', extra={'status_mapper': status_mapper})
            return LeadStatus.trash.value

        external_status = parameters.get(status_parameter)
        if external_status is None:
            logger.warning(
                'Failed to get external status', extra={'status_parameter': status_parameter, 'parameters': parameters}
            )
            return LeadStatus.trash.value

        status_mapping = status_mapper.get('mapping') or {}
        internal_status = status_mapping.get(external_status)

        if internal_status in {s.value for s in LeadStatus}:
            return internal_status

        logger.warning(
            'Failed to mapped status', extra={'status_mapping': status_mapping, 'external_status': external_status}
        )
        return LeadStatus.trash.value

    def track_click(self, click_id: str, campaign_id: int, parameters: dict) -> None:
        click = TrackClick(click_id=click_id, campaign_id=campaign_id, parameters=parameters)
        click.save()

    def track_discard(self, click_id: str, campaign_id: int, client) -> None:
        discard = TrackDiscard(
            click_id=click_id,
            campaign_id=campaign_id,
            country=client.country,
            browser_family=client.browser_family,
            os_family=client.os_family,
            device_family=client.device_family,
            is_mobile=client.is_mobile,
            is_bot=client.is_bot,
        )
        discard.save()

    def track_postback(self, click_id: str, parameters: dict) -> None:
        status = None
        cost_value = None
        currency = None

        campaign = self._get_campaign_by_click_id(click_id)
        if campaign:
            status = self._map_status(parameters, campaign.status_mapper)
            if status in {LeadStatus.accept.value, LeadStatus.expect.value}:
                cost_value = campaign.cost_value
                currency = campaign.currency
        else:
            logger.warning(
                'Tracking postback for not found campaign', extra={'click_id': click_id, 'parameters': parameters}
            )

        postback = TrackPostback(
            click_id=click_id,
            parameters=parameters,
            status=status,
            cost_value=cost_value,
            currency=currency,
        )
        postback.save()
        self.worker_supervisor.enqueue(
            refresh_report_leads_worker,
            {'click_id': click_id, 'source': TrackSource.postback.value},
        )

    def track_lead(self, click_id: str, parameters: dict) -> None:
        lead = TrackLead(click_id=click_id, parameters=parameters)
        lead.save()
        self.worker_supervisor.enqueue(
            refresh_report_leads_worker,
            {'click_id': click_id, 'source': TrackSource.lead.value},
        )

    def get_click_dates(self, campaign_id, start_period, end_period):
        date = fn.date(fn.from_unixtime(TrackClick.created_at)).distinct().alias('date')
        query = (
            TrackClick.select(date)
            .where(
                (TrackClick.campaign_id == campaign_id)
                & (TrackClick.created_at >= start_period)
                & (TrackClick.created_at <= end_period)
            )
            .order_by(date)
        )

        return [tc.date for tc in query]

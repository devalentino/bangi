import logging
from typing import Optional

from wireup import service

from peewee import fn
from src.core.entities import Campaign
from src.core.enums import LeadStatus
from src.tracker.entities import TrackClick, TrackPostback

logger = logging.getLogger(__name__)


@service
class TrackService:

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

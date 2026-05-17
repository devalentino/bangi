from peewee import JOIN

from src.alerts import Alert, AlertCode, AlertSeverity, register_alert_callback
from src.core.entities import Campaign, Flow
from src.core.services import IpLocator


@register_alert_callback
def collect_ip2location_alerts(container) -> list[Alert]:
    ip_locator = container.get(IpLocator)
    if ip_locator.is_configured():
        return []

    return [
        Alert(
            code=AlertCode.CORE_IP2LOCATION_DATABASE_MISSING,
            message='Country targeting is unavailable until the IP2Location database is configured.',
            severity=AlertSeverity.WARNING,
            payload={'countryTargetingAvailable': False},
        )
    ]


@register_alert_callback
def collect_default_flow_alerts(container) -> list[Alert]:
    missing_campaigns = []
    invalid_campaigns = []
    default_flow = Flow.alias()

    campaign_rows = (
        Campaign.select(
            Campaign.id.alias('campaign_id'),
            Campaign.name.alias('campaign_name'),
            Campaign.default_flow_id,
            default_flow.id.alias('default_flow_row_id'),
            default_flow.is_enabled.alias('default_flow_is_enabled'),
            default_flow.is_deleted.alias('default_flow_is_deleted'),
        )
        .join(
            default_flow,
            JOIN.LEFT_OUTER,
            on=((default_flow.id == Campaign.default_flow_id) & (default_flow.campaign_id == Campaign.id)),
        )
        .where(
            (Campaign.default_flow_id.is_null(True))
            | (default_flow.id.is_null(True))
            | (default_flow.is_deleted == True)
            | (default_flow.is_enabled == False)
        )
        .order_by(Campaign.id.asc())
        .dicts()
    )

    for campaign in campaign_rows:
        if campaign['default_flow_id'] is None:
            missing_campaigns.append({'campaignId': campaign['campaign_id'], 'campaignName': campaign['campaign_name']})
            continue

        if campaign['default_flow_row_id'] is None:
            reason = 'missing'
        elif campaign['default_flow_is_deleted']:
            reason = 'deleted'
        elif not campaign['default_flow_is_enabled']:
            reason = 'disabled'
        else:
            continue

        invalid_campaigns.append(
            {
                'campaignId': campaign['campaign_id'],
                'campaignName': campaign['campaign_name'],
                'defaultFlowId': campaign['default_flow_id'],
                'reason': reason,
            }
        )

    if not missing_campaigns and not invalid_campaigns:
        return []

    message_parts = []
    if missing_campaigns:
        campaign_names = ', '.join(campaign['campaignName'] for campaign in missing_campaigns)
        message_parts.append(f'Missing default flow: {campaign_names}.')
    if invalid_campaigns:
        campaign_names = ', '.join(campaign['campaignName'] for campaign in invalid_campaigns)
        message_parts.append(f'Invalid default flow: {campaign_names}.')

    return [
        Alert(
            code=AlertCode.CORE_CAMPAIGN_DEFAULT_FLOW_CONFIGURATION,
            message=' '.join(message_parts),
            severity=AlertSeverity.WARNING,
            payload={
                'missingDefaultFlowCampaigns': missing_campaigns,
                'invalidDefaultFlowCampaigns': invalid_campaigns,
            },
        )
    ]

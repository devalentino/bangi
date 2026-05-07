from enum import StrEnum


class AlertCode(StrEnum):
    UNKNOWN = 'unknown'
    CORE_CAMPAIGN_DISCARD = 'core_campaign_discard'
    FACEBOOK_PACS_BUSINESS_PORTFOLIO_ACCESS_URL_MISSING = 'facebook_pacs_business_portfolio_access_url_missing'
    FACEBOOK_PACS_BUSINESS_PORTFOLIO_ACCESS_URL_EXPIRED = 'facebook_pacs_business_portfolio_access_url_expired'
    FACEBOOK_PACS_BUSINESS_PORTFOLIO_ACCESS_URL_EXPIRING_SOON = (
        'facebook_pacs_business_portfolio_access_url_expiring_soon'
    )
    SYSTEM_HEALTH_DISK_WARNING = 'system_health_disk_warning'
    SYSTEM_HEALTH_DISK_CRITICAL = 'system_health_disk_critical'
    SYSTEM_HEALTH_TELEMETRY_STALE = 'system_health_telemetry_stale'


class AlertSeverity(StrEnum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'

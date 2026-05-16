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
    SYSTEM_HEALTH_CERTIFICATE_ISSUANCE_FAILED = 'system_health_certificate_issuance_failed'
    SYSTEM_HEALTH_CERTIFICATE_RENEWAL_WARNING = 'system_health_certificate_renewal_warning'
    SYSTEM_HEALTH_CERTIFICATE_RENEWAL_ERROR = 'system_health_certificate_renewal_error'
    SYSTEM_HEALTH_CERTIFICATE_EXPIRED = 'system_health_certificate_expired'
    SYSTEM_HEALTH_NGINX_VALIDATION_FAILED = 'system_health_nginx_validation_failed'


class AlertSeverity(StrEnum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'

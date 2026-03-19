from enum import StrEnum


class AlertCode(StrEnum):
    UNKNOWN = 'unknown'
    FACEBOOK_PACS_BUSINESS_PORTFOLIO_ACCESS_URL_EXPIRED = 'facebook_pacs_business_portfolio_access_url_expired'
    FACEBOOK_PACS_BUSINESS_PORTFOLIO_ACCESS_URL_EXPIRING_SOON = (
        'facebook_pacs_business_portfolio_access_url_expiring_soon'
    )


class AlertSeverity(StrEnum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'

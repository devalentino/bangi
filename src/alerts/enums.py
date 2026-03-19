from enum import StrEnum


class AlertCode(StrEnum):
    UNKNOWN = 'unknown'


class AlertSeverity(StrEnum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'

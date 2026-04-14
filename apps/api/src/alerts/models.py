from dataclasses import dataclass, field

from src.alerts.enums import AlertCode, AlertSeverity


@dataclass(slots=True)
class Alert:
    code: AlertCode
    message: str
    severity: AlertSeverity = AlertSeverity.INFO
    source: str | None = None
    payload: dict = field(default_factory=dict)

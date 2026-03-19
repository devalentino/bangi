from src.alerts.enums import AlertCode, AlertSeverity
from src.alerts.models import Alert
from src.alerts.services import AlertCallback


def register_alert_callback(callback: AlertCallback) -> AlertCallback:
    from src.alerts.services import AlertService
    from src.container import container

    return container.get(AlertService).register_callback(callback)


__all__ = ['Alert', 'AlertCode', 'AlertSeverity', 'register_alert_callback']

import dataclasses
import logging
from collections.abc import Callable, Iterable
from typing import TypeAlias

from wireup import injectable

from src.alerts.models import Alert

logger = logging.getLogger(__name__)

AlertCallbackResult: TypeAlias = Alert | Iterable[Alert] | None
AlertCallback: TypeAlias = Callable[[object], AlertCallbackResult]
_REGISTERED_ALERT_CALLBACKS: list[AlertCallback] = []


def register_alert_callback(callback: AlertCallback) -> AlertCallback:
    if callback not in _REGISTERED_ALERT_CALLBACKS:
        _REGISTERED_ALERT_CALLBACKS.append(callback)
    return callback


@injectable(lifetime='singleton')
class AlertService:
    def __init__(self):
        self._callbacks = _REGISTERED_ALERT_CALLBACKS

    def register_callback(self, callback: AlertCallback) -> AlertCallback:
        return register_alert_callback(callback)

    def collect(self, container) -> list[Alert]:
        alerts: list[Alert] = []

        for callback in self._callbacks:
            try:
                result = callback(container)
            except Exception:
                logger.exception('Failed to collect alerts from callback %s', callback)
                continue

            if result is None:
                continue
            if isinstance(result, Alert):
                alerts.append(self._populate_source(result, callback))
                continue

            for alert in result:
                if not isinstance(alert, Alert):
                    raise TypeError(f'Alert callback {callback} returned unsupported item: {type(alert)!r}')
                alerts.append(self._populate_source(alert, callback))

        return alerts

    @staticmethod
    def serialize(alerts: list[Alert]) -> list[dict]:
        return [
            dataclasses.asdict(alert) | {'code': alert.code.value, 'severity': alert.severity.value} for alert in alerts
        ]

    @staticmethod
    def _populate_source(alert: Alert, callback: AlertCallback) -> Alert:
        if alert.source is not None:
            return alert
        return dataclasses.replace(alert, source=callback.__module__)

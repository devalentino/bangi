from decimal import Decimal
from time import time as time_timestamp
from typing import Annotated

from wireup import Inject, injectable

from src.health.entities import DiskUtilization, DiskUtilizationSummary


@injectable
class HealthService:
    def __init__(
        self,
        stale_after_seconds: Annotated[int, Inject(config='HEALTH_STALE_AFTER_SECONDS')],
        warning_percent: Annotated[int, Inject(config='HEALTH_WARNING_PERCENT')],
        critical_percent: Annotated[int, Inject(config='HEALTH_CRITICAL_PERCENT')],
    ):
        self.stale_after_seconds = stale_after_seconds
        self.warning_percent = warning_percent
        self.critical_percent = critical_percent

    def ingest_disk_utilization(
        self,
        filesystem: str,
        mountpoint: str,
        total_bytes: int,
        used_bytes: int,
        available_bytes: int,
        used_percent: Decimal,
    ) -> DiskUtilization:
        snapshot = DiskUtilization(
            filesystem=filesystem,
            mountpoint=mountpoint,
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            available_bytes=available_bytes,
            used_percent=used_percent,
        )
        snapshot.save()
        return snapshot

    def disk_utilization_history(self, *, days: int) -> tuple[DiskUtilizationSummary, list[DiskUtilization]]:
        now_timestamp = int(time_timestamp())
        history_start_timestamp = now_timestamp - days * 24 * 60 * 60

        rows = list(
            DiskUtilization.select()
            .where(DiskUtilization.created_at >= history_start_timestamp)
            .order_by(DiskUtilization.created_at.asc())
        )
        latest_snapshot = rows[-1] if rows else None

        if latest_snapshot is None:
            return (
                DiskUtilizationSummary(
                    stale=False,
                    severity=None,
                    filesystem=None,
                    mountpoint=None,
                    total_bytes=None,
                    used_bytes=None,
                    available_bytes=None,
                    used_percent=None,
                    last_received_at=None,
                ),
                [],
            )

        latest_received_at = int(latest_snapshot.created_at.timestamp())
        stale = now_timestamp - latest_received_at >= self.stale_after_seconds

        if latest_snapshot.used_percent >= self.critical_percent:
            severity = 'critical'
        elif latest_snapshot.used_percent >= self.warning_percent:
            severity = 'warning'
        else:
            severity = 'normal'

        return (
            DiskUtilizationSummary(
                stale=stale,
                severity=severity,
                filesystem=latest_snapshot.filesystem,
                mountpoint=latest_snapshot.mountpoint,
                total_bytes=latest_snapshot.total_bytes,
                used_bytes=latest_snapshot.used_bytes,
                available_bytes=latest_snapshot.available_bytes,
                used_percent=float(latest_snapshot.used_percent),
                last_received_at=latest_received_at,
            ),
            rows,
        )

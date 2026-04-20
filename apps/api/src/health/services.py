from decimal import Decimal

from wireup import injectable

from src.health.entities import DiskUtilization


@injectable
class HealthService:
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

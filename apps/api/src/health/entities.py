from dataclasses import dataclass

from peewee import BigIntegerField, CharField, DecimalField

from src.core.entities import Entity


@dataclass(slots=True)
class DiskUtilizationSummary:
    stale: bool
    severity: str | None
    filesystem: str | None
    mountpoint: str | None
    total_bytes: int | None
    used_bytes: int | None
    available_bytes: int | None
    used_percent: float | None
    last_received_at: int | None


class DiskUtilization(Entity):
    filesystem = CharField(max_length=255)
    mountpoint = CharField(max_length=255)
    total_bytes = BigIntegerField()
    used_bytes = BigIntegerField()
    available_bytes = BigIntegerField()
    used_percent = DecimalField(max_digits=5, decimal_places=2, auto_round=True)

    class Meta:
        table_name = 'health_disk_utilization'
        table_settings = ('ENGINE=Aria', 'TRANSACTIONAL=0')

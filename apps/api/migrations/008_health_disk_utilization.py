"""Peewee migrations -- 008_health_disk_utilization.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


HEALTH_DISK_UTILIZATION_TABLE = 'health_disk_utilization'


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class DiskUtilization(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        filesystem = pw.CharField(max_length=255)
        mountpoint = pw.CharField(max_length=255)
        total_bytes = pw.BigIntegerField()
        used_bytes = pw.BigIntegerField()
        available_bytes = pw.BigIntegerField()
        used_percent = pw.DecimalField(max_digits=5, decimal_places=2, auto_round=True)

        class Meta:
            table_name = HEALTH_DISK_UTILIZATION_TABLE
            table_settings = ('ENGINE=Aria', 'TRANSACTIONAL=0')


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model(HEALTH_DISK_UTILIZATION_TABLE)

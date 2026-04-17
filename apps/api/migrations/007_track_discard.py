"""Peewee migrations -- 007_track_discard.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


class BinaryUUIDField(pw.Field):
    field_type = 'BINARY(16)'


TRACK_DISCARD_TABLE = 'track_discard'


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class TrackDiscard(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        click_id = BinaryUUIDField()
        campaign_id = pw.IntegerField()
        country = pw.CharField(max_length=2, null=True)
        browser_family = pw.CharField(max_length=255, null=True)
        os_family = pw.CharField(max_length=255, null=True)
        device_family = pw.CharField(max_length=255, null=True)
        is_mobile = pw.BooleanField()
        is_bot = pw.BooleanField()

        class Meta:
            table_name = TRACK_DISCARD_TABLE
            table_settings = ('ENGINE=Aria', 'TRANSACTIONAL=0')
            indexes = (
                (('campaign_id', 'created_at'), False),
                (('created_at',), False),
            )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model(TRACK_DISCARD_TABLE)

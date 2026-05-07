"""Peewee migrations -- 002_track_lead.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class TrackLead(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        click_id = pw.CharField(max_length=255)
        parameters = pw.TextField()

        class Meta:
            table_name = "track_lead"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model('track_lead')

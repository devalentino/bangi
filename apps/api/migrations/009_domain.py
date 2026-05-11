"""Peewee migrations -- 009_domain.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


DOMAIN_TABLE = 'domain'


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class Domain(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        hostname = pw.CharField(max_length=255, unique=True)
        purpose = pw.CharField(max_length=32)
        campaign = pw.ForeignKeyField(column_name='campaign_id', field='id', model=migrator.orm['campaign'], null=True, unique=True)
        is_a_record_set = pw.BooleanField(null=True)
        is_disabled = pw.BooleanField(default=False)

        class Meta:
            table_name = DOMAIN_TABLE


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model(DOMAIN_TABLE)

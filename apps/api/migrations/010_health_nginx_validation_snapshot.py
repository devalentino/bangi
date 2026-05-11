"""Peewee migrations -- 010_health_nginx_validation_snapshot.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


HEALTH_NGINX_VALIDATION_SNAPSHOT_TABLE = 'health_nginx_validation_snapshot'


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class NginxValidationSnapshot(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        domain_id = pw.IntegerField(null=True)
        validation_status = pw.CharField(max_length=16)
        validation_error = pw.TextField(null=True)
        sites_available_files = pw.TextField()
        sites_enabled_refs = pw.TextField()

        class Meta:
            table_name = HEALTH_NGINX_VALIDATION_SNAPSHOT_TABLE


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model(HEALTH_NGINX_VALIDATION_SNAPSHOT_TABLE)

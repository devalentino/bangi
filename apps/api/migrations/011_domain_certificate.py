"""Peewee migrations -- 011_domain_certificate.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


DOMAIN_CERTIFICATE_TABLE = 'domain_certificate'


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class DomainCertificate(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        domain = pw.ForeignKeyField(
            column_name='domain_id',
            field='id',
            model=migrator.orm['domain'],
            on_delete='CASCADE',
            unique=True,
        )
        status = pw.CharField(max_length=32)
        ca = pw.CharField(max_length=32)
        validation_method = pw.CharField(max_length=32)
        certificate_path = pw.CharField(max_length=512, null=True)
        private_key_path = pw.CharField(max_length=512, null=True)
        issued_at = pw.TimestampField(null=True)
        expires_at = pw.TimestampField(null=True)
        last_attempted_at = pw.TimestampField(null=True)
        last_issued_at = pw.TimestampField(null=True)
        last_renewed_at = pw.TimestampField(null=True)
        next_retry_at = pw.TimestampField(null=True)
        failure_count = pw.IntegerField(default=0)
        failure_reason = pw.TextField(null=True)

        class Meta:
            table_name = DOMAIN_CERTIFICATE_TABLE


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model(DOMAIN_CERTIFICATE_TABLE)

"""Peewee migrations -- 005_report_leads.py."""

from contextlib import suppress
from decimal import Decimal, ROUND_HALF_EVEN

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class ReportLead(pw.Model):
        id = pw.AutoField()
        created_at = pw.TimestampField(null=True)
        click_id = pw.UUIDField()
        campaign_id = pw.IntegerField()
        click_created_at = pw.TimestampField(null=True)
        status = pw.CharField(max_length=255, null=True)
        cost_value = pw.DecimalField(auto_round=False, decimal_places=5, max_digits=10, null=True, rounding=ROUND_HALF_EVEN)
        currency = pw.CharField(max_length=255, null=True)

        class Meta:
            table_name = "report_lead"
            indexes = [
                (('click_id',), True),
                (('campaign_id', 'click_created_at'), False),
            ]


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model('report_lead')

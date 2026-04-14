"""Peewee migrations -- 003_business_portfolio_access_url_expires_at_not_null.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    migrator.add_fields(
        'facebook_pacs_business_portfolio_access_url',
        email=pw.CharField(max_length=255, null=True),
    )

    business_portfolio_access_url = migrator.orm['facebook_pacs_business_portfolio_access_url']

    (
        business_portfolio_access_url.update(expires_at=pw.fn.UNIX_TIMESTAMP())
        .where(business_portfolio_access_url.expires_at.is_null(True))
        .execute()
    )

    migrator.add_not_null('facebook_pacs_business_portfolio_access_url', 'expires_at')


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.drop_not_null('facebook_pacs_business_portfolio_access_url', 'expires_at')
    migrator.remove_fields('facebook_pacs_business_portfolio_access_url', 'email')

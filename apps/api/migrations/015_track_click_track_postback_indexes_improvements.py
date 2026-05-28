"""Peewee migrations -- 015_track_click_track_postback_indexes_improvements.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    migrator.add_index('track_postback', 'click_id', 'id', unique=False)
    migrator.add_index('track_click', 'campaign_id', 'created_at', 'click_id', unique=False)


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.drop_index('track_click', 'campaign_id', 'created_at', 'click_id')
    migrator.drop_index('track_postback', 'click_id', 'id')

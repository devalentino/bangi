"""Peewee migrations -- 012_flow_show_once_per_visitor.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    migrator.sql('ALTER TABLE flow ADD COLUMN show_once_per_visitor BOOLEAN NOT NULL DEFAULT FALSE')


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_fields('flow', 'show_once_per_visitor')

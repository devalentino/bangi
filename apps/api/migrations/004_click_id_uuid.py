"""Peewee migrations -- 004_click_id_uuid.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


TRACK_TABLES = ('track_click', 'track_postback', 'track_lead')
TRACK_CLICK_INDEX_NAME = 'track_click_click_id'


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    for table_name in TRACK_TABLES:
        database.execute_sql(f'ALTER TABLE `{table_name}` MODIFY COLUMN `click_id` UUID NOT NULL')
        database.execute_sql(f'ALTER TABLE `{table_name}` ENGINE=Aria TRANSACTIONAL=0')
    database.execute_sql(f'CREATE INDEX `{TRACK_CLICK_INDEX_NAME}` ON `track_click` (`click_id`)')


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    database.execute_sql(f'DROP INDEX `{TRACK_CLICK_INDEX_NAME}` ON `track_click`')
    for table_name in TRACK_TABLES:
        database.execute_sql(f'ALTER TABLE `{table_name}` ENGINE=InnoDB')
        database.execute_sql(f'ALTER TABLE `{table_name}` MODIFY COLUMN `click_id` VARCHAR(255) NOT NULL')

"""Peewee migrations -- 006_click_id_binary.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


TRACK_TABLES = ('track_click', 'track_postback', 'track_lead')
CLICK_ID_TABLES = TRACK_TABLES + ('report_lead',)


def _drop_click_id_indexes(database: pw.Database, table_name: str) -> None:
    query = """
        SELECT DISTINCT INDEX_NAME
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND column_name = 'click_id'
    """
    cursor = database.execute_sql(query, (table_name,))
    index_names = [row[0] for row in cursor.fetchall() if row[0] != 'PRIMARY']
    for index_name in index_names:
        database.execute_sql(f'ALTER TABLE `{table_name}` DROP INDEX `{index_name}`')


def _convert_click_id_to_binary(database: pw.Database, table_name: str) -> None:
    database.execute_sql(f'ALTER TABLE `{table_name}` ADD COLUMN `click_id_binary` BINARY(16) NULL')
    database.execute_sql(
        f"""
        UPDATE `{table_name}`
        SET `click_id_binary` = UNHEX(REPLACE(`click_id`, '-', ''))
        WHERE `click_id` IS NOT NULL
        """
    )
    database.execute_sql(f'ALTER TABLE `{table_name}` DROP COLUMN `click_id`')
    database.execute_sql(
        f'ALTER TABLE `{table_name}` CHANGE COLUMN `click_id_binary` `click_id` BINARY(16) NOT NULL'
    )


def _convert_click_id_to_varchar(database: pw.Database, table_name: str) -> None:
    database.execute_sql(f'ALTER TABLE `{table_name}` ADD COLUMN `click_id_varchar` VARCHAR(40) NULL')
    database.execute_sql(
        f"""
        UPDATE `{table_name}`
        SET `click_id_varchar` = LOWER(CONCAT(
            SUBSTR(HEX(`click_id`), 1, 8), '-',
            SUBSTR(HEX(`click_id`), 9, 4), '-',
            SUBSTR(HEX(`click_id`), 13, 4), '-',
            SUBSTR(HEX(`click_id`), 17, 4), '-',
            SUBSTR(HEX(`click_id`), 21, 12)
        ))
        WHERE `click_id` IS NOT NULL
        """
    )
    database.execute_sql(f'ALTER TABLE `{table_name}` DROP COLUMN `click_id`')
    database.execute_sql(
        f'ALTER TABLE `{table_name}` CHANGE COLUMN `click_id_varchar` `click_id` VARCHAR(40) NOT NULL'
    )


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    for table_name in CLICK_ID_TABLES:
        _drop_click_id_indexes(database, table_name)
        _convert_click_id_to_binary(database, table_name)

    database.execute_sql('CREATE INDEX `track_click_click_id` ON `track_click` (`click_id`)')
    database.execute_sql('CREATE UNIQUE INDEX `report_lead_click_id` ON `report_lead` (`click_id`)')


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""
    for table_name in CLICK_ID_TABLES:
        _drop_click_id_indexes(database, table_name)
        _convert_click_id_to_varchar(database, table_name)

    database.execute_sql('CREATE INDEX `track_click_click_id` ON `track_click` (`click_id`)')
    database.execute_sql('CREATE UNIQUE INDEX `report_lead_click_id` ON `report_lead` (`click_id`)')

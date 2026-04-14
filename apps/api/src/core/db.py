from typing import Annotated

from playhouse.shortcuts import ReconnectMixin
from wireup import Inject, injectable

from peewee import InterfaceError, MySQLDatabase


class ReconnectPooledMySQLDatabase(ReconnectMixin, MySQLDatabase):
    reconnect_errors = ReconnectMixin.reconnect_errors + ((InterfaceError, ''),)


@injectable(lifetime='singleton')
def database(
    host: Annotated[str, Inject(config='MARIADB_HOST')],
    port: Annotated[int, Inject(config='MARIADB_PORT')],
    username: Annotated[str, Inject(config='MARIADB_USER')],
    password: Annotated[str, Inject(config='MARIADB_PASSWORD')],
    db_name: Annotated[str, Inject(config='MARIADB_DATABASE')],
) -> MySQLDatabase:
    return ReconnectPooledMySQLDatabase(
        db_name,
        user=username,
        password=password,
        host=host,
        port=port,
    )

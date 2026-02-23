from typing import Annotated

from playhouse.shortcuts import ReconnectMixin
from wireup import Inject, service

from peewee import MySQLDatabase


class ReconnectingMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


@service(lifetime='singleton')
def database(
    host: Annotated[str, Inject(param='MARIADB_HOST')],
    port: Annotated[str, Inject(param='MARIADB_PORT')],
    username: Annotated[str, Inject(param='MARIADB_USER')],
    password: Annotated[str, Inject(param='MARIADB_PASSWORD')],
    db_name: Annotated[str, Inject(param='MARIADB_DATABASE')],
) -> MySQLDatabase:
    return ReconnectingMySQLDatabase(db_name, user=username, password=password, host=host, port=int(port))

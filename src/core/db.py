from typing import Annotated

from wireup import Inject, service

from peewee import MySQLDatabase


@service(lifetime='singleton')
def database(
    host: Annotated[str, Inject(param='MYSQL_HOST')],
    port: Annotated[str, Inject(param='MYSQL_PORT')],
    username: Annotated[str, Inject(param='MYSQL_USERNAME')],
    password: Annotated[str, Inject(param='MYSQL_PASSWORD')],
    db_name: Annotated[str, Inject(param='MYSQL_DB')],
) -> MySQLDatabase:
    return MySQLDatabase(db_name, user=username, password=password, host=host, port=int(port))

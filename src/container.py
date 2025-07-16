import os

from peewee import MySQLDatabase
from wireup import create_sync_container

from src.core.db import database
from src.core.entities import database_proxy
from src.tracker.services import TrackClickService


container = create_sync_container(
    parameters={
        'MYSQL_HOST': os.getenv('MYSQL_HOST'),
        'MYSQL_PORT': os.getenv('MYSQL_PORT'),
        'MYSQL_USERNAME': os.getenv('MYSQL_USERNAME'),
        'MYSQL_PASSWORD': os.getenv('MYSQL_PASSWORD'),
        'MYSQL_DB': os.getenv('MYSQL_DB'),
    },
    services=[database, TrackClickService],
)

database_proxy.initialize(container.get(MySQLDatabase))

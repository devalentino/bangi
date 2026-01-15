import base64
import os
import pathlib
from unittest import mock

import pytest
from peewee_migrate import Router
from pytest_mysql import factories

from peewee import MySQLDatabase

mysql_in_docker = factories.mysql_noproc(
    host='localhost',
    port=int(os.getenv('MARIADB_PORT')),
    user=os.getenv('MARIADB_USER'),
)

mysql = factories.mysql('mysql_in_docker', passwd=os.getenv('MARIADB_PASSWORD'))


@pytest.fixture(autouse=True)
def mock_database(mysql):
    environ = os.environ | {'MARIADB_HOST': mysql.host, 'MARIADB_PORT': str(mysql.port), 'MARIADB_DATABASE': 'test'}
    with mock.patch.dict(os.environ, environ):
        yield


@pytest.fixture(autouse=True)
def create_tables(mock_database, mysql):
    db = MySQLDatabase(
        'test',
        user=mysql.user.decode(),
        password=mysql.password.decode(),
        host=mysql.host,
        port=mysql.port,
    )

    router = Router(db, migrate_dir=pathlib.Path(__file__).parent.parent.parent / 'migrations')
    router.run()


@pytest.fixture
def client():
    from src.api import app

    app.config.update({'DEBUG': True})

    yield app.test_client()


@pytest.fixture
def authorization():
    payload = f'{os.getenv("BASIC_AUTHENTICATION_USERNAME")}:{os.getenv("BASIC_AUTHENTICATION_PASSWORD")}'.encode()
    return f'Basic {base64.b64encode(payload).decode()}'

import os
import pathlib
from unittest import mock

import pytest
from peewee import MySQLDatabase
from peewee_migrate import Router
from pytest_mysql import factories

mysql_in_docker = factories.mysql_noproc()
mysql = factories.mysql("mysql_in_docker")


@pytest.fixture
def mysql_credentials(mysql):
    return {
        'MYSQL_HOST': mysql.host,
        'MYSQL_PORT': str(mysql.port),
        'MYSQL_USERNAME': mysql.user.decode(),
        'MYSQL_PASSWORD': mysql.password.decode(),
        'MYSQL_DB': 'test',
    }


@pytest.fixture(autouse=True)
def mock_env_variables(mysql_credentials):
    environ = os.environ | mysql_credentials

    with mock.patch.dict(os.environ, environ):
        yield


@pytest.fixture(autouse=True)
def create_tables(mysql_credentials):
    db = MySQLDatabase(
        mysql_credentials['MYSQL_DB'],
        user=mysql_credentials['MYSQL_USERNAME'],
        password=mysql_credentials['MYSQL_PASSWORD'],
        host=mysql_credentials['MYSQL_HOST'],
        port=int(mysql_credentials['MYSQL_PORT']),
    )

    router = Router(db, migrate_dir=pathlib.Path(__file__).parent.parent.parent / 'migrations')
    router.run()


@pytest.fixture
def client():
    from src.api import app

    app.config.update({'DEBUG': True})

    yield app.test_client()

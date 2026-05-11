import base64
import os
import pathlib
from unittest import mock

import pytest
from peewee import MySQLDatabase
from peewee_migrate import Router
from pytest_mysql import factories

mysql_in_docker = factories.mysql_noproc(
    host='localhost',
    port=int(os.getenv('MARIADB_PORT')),
    user=os.getenv('MARIADB_USER'),
)

mysql = factories.mysql('mysql_in_docker', passwd=os.getenv('MARIADB_PASSWORD'))


@pytest.fixture(autouse=True, scope='session')
def landing_pages_base_path(tmpdir_factory):
    return str(tmpdir_factory.mktemp('landings'))


@pytest.fixture(autouse=True, scope='session')
def nginx_workspace_base_dir(tmpdir_factory):
    return str(tmpdir_factory.mktemp('nginx-workspace'))


@pytest.fixture(autouse=True)
def mock_environment(mysql, landing_pages_base_path, nginx_workspace_base_dir):
    environ = os.environ | {
        'MARIADB_HOST': mysql.host,
        'MARIADB_PORT': str(mysql.port),
        'MARIADB_DATABASE': 'test',
        'LANDING_PAGES_BASE_PATH': landing_pages_base_path,
        'NGINX_WORKSPACE_BASE_DIR': nginx_workspace_base_dir,
        'BANGI_HOST_OPS_SSH_KEY_PATH': '/tmp/bangi-ops-id_ed25519',
        'BANGI_HOST_OPS_SSH_KNOWN_HOSTS_PATH': '/tmp/bangi-ops-known_hosts',
    }
    with mock.patch.dict(os.environ, environ):
        yield


@pytest.fixture(autouse=True)
def mock_subprocess_run():
    with mock.patch('src.domains.services.subprocess.run') as subprocess_run:
        subprocess_run.return_value = mock.Mock(returncode=0, stdout='', stderr='')
        yield subprocess_run


@pytest.fixture(autouse=True)
def assert_all_external_http_calls_are_mocked(respx_mock):
    yield


@pytest.fixture(autouse=True)
def create_tables(mock_environment, mysql):
    db = MySQLDatabase(
        'test',
        user=mysql.user.decode(),
        password=mysql.password.decode(),
        host=mysql.host,
        port=mysql.port,
    )

    try:
        router = Router(db, migrate_dir=pathlib.Path(__file__).parent.parent.parent / 'migrations')
        router.run()
    finally:
        db.close()


@pytest.fixture
def client():
    from src.api import app

    app.config.update({'DEBUG': True})

    yield app.test_client()


@pytest.fixture
def authorization():
    payload = f'{os.getenv("BASIC_AUTHENTICATION_USERNAME")}:{os.getenv("BASIC_AUTHENTICATION_PASSWORD")}'.encode()
    return f'Basic {base64.b64encode(payload).decode()}'


@pytest.fixture
def environment():
    from src.container import container

    return container.params._ConfigStore__bag

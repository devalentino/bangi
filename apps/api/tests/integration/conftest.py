import base64
import functools
import gc
import hashlib
import os
import pathlib
import shutil
from unittest import mock

import pytest
from peewee import MySQLDatabase
from peewee_migrate import Router
from pymysql import cursors
from pytest_mysql import factories

mysql_in_docker = factories.mysql_noproc(
    host='localhost',
    port=int(os.getenv('MARIADB_PORT')),
    user=os.getenv('MARIADB_USER'),
)

mysql = factories.mysql('mysql_in_docker', passwd=os.getenv('MARIADB_PASSWORD'))


@pytest.fixture
def public_ip():
    return '203.0.113.10'


@pytest.fixture(autouse=True)
def landing_pages_base_path(tmpdir_factory):
    landing_pages_path = tmpdir_factory.mktemp('landings')

    yield str(landing_pages_path)

    shutil.rmtree(landing_pages_path, ignore_errors=True)


@pytest.fixture(autouse=True, scope='session')
def nginx_workspace_base_dir(tmpdir_factory):
    return str(tmpdir_factory.mktemp('nginx-workspace'))


@pytest.fixture(autouse=True)
def mock_environment(mysql, public_ip, landing_pages_base_path, nginx_workspace_base_dir):
    environ = os.environ | {
        'MARIADB_HOST': mysql.host,
        'MARIADB_PORT': str(mysql.port),
        'MARIADB_DATABASE': 'test',
        'LANDING_PAGES_BASE_PATH': landing_pages_base_path,
        'NGINX_WORKSPACE_BASE_DIR': nginx_workspace_base_dir,
        'BANGI_PUBLIC_HOST_IP': public_ip,
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
def ip2location_configured():
    with mock.patch('src.core.services.Ip2LocationLocator.is_configured', return_value=True):
        yield


@pytest.fixture
def ip2location_unavailable():
    with mock.patch('src.core.services.Ip2LocationLocator.is_configured', return_value=False):
        yield


@pytest.fixture(autouse=True)
def assert_all_external_http_calls_are_mocked(respx_mock):
    yield


@pytest.fixture(autouse=True)
def clear_lru_caches():
    gc.collect()
    for cached_object in gc.get_objects():
        if isinstance(cached_object, functools._lru_cache_wrapper):
            cached_object.cache_clear()

    yield

    gc.collect()
    for cached_object in gc.get_objects():
        if isinstance(cached_object, functools._lru_cache_wrapper):
            cached_object.cache_clear()


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
def pat_token(write_to_db):
    token = 'test-pat-token-0123456789abcdef'
    write_to_db(
        'pat_token',
        {
            'name': 'Test PAT token',
            'token_hash': hashlib.sha256(token.encode()).hexdigest(),
            'token_prefix': token[:8],
            'token_suffix': token[-4:],
            'revoked_at': None,
        },
    )
    return token


@pytest.fixture
def bearer_authorization(pat_token):
    return f'Bearer {pat_token}'


@pytest.fixture
def environment():
    from src.container import container

    return container.params._ConfigStore__bag


@pytest.fixture
def set_default_flow_id(mysql):
    def _set_default_flow_id(campaign_id, flow_id):
        with mysql.cursor(cursors.DictCursor) as cur:
            cur.execute('UPDATE campaign SET default_flow_id = %s WHERE id = %s', (flow_id, campaign_id))

        mysql.commit()

    return _set_default_flow_id

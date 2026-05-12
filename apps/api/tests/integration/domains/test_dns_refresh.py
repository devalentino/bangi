from time import sleep
from unittest import mock

import pytest


@pytest.fixture
def dns_resolver_mock():
    with mock.patch("src.domains.services.dns.resolver") as resolver:
        resolver.resolve.return_value = [mock.Mock(address='203.0.113.10')]
        yield resolver


@pytest.mark.usefixtures('dns_resolver_mock')
class TestDnsRefreshWorker:
    @pytest.fixture(autouse=True)
    def mock_cleanup_discard_worker_settings(self, monkeypatch):
        monkeypatch.setattr('src.domains.workers.DOMAIN_DNS_REFRESH_PERIOD_SECONDS', 0.1)

    @pytest.fixture
    def domain(self, write_to_db):
        return write_to_db(
            'domain',
            {
                'hostname': 'example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': False,
            },
        )

    @pytest.mark.usefixtures('domain')
    def test_refreshes_unknown_domain_state_and_publishes_when_a_record_points_to_public_ip(
        self, client, domain, read_from_db, mock_subprocess_run
    ):
        client.get('/api/v2/health')
        sleep(0.3)

        updated = read_from_db('domain', filters={'id': domain['id']})
        snapshot = read_from_db('health_nginx_validation_snapshot', filters={'domain_id': domain['id']})

        assert updated['is_a_record_set']
        assert snapshot['validation_status'] == 'success'
        assert snapshot['validation_error'] is None
        assert snapshot['domain_id'] == domain['id']
        assert mock_subprocess_run.call_count == 2

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

    def test_refreshes_unknown_domain_state_and_publishes_when_a_record_points_to_public_ip(
        self, client, read_from_db, write_to_db, monkeypatch, mock_subprocess_run
    ):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': False,
            },
        )

        client.get('/api/v2/health')
        sleep(0.3)

        updated = read_from_db('domain', filters={'id': domain['id']})
        snapshot = read_from_db('health_nginx_validation_snapshot', filters={'domain_id': domain['id']})

        assert updated['is_a_record_set'] is True
        assert snapshot['validation_status'] == 'success'
        assert snapshot['validation_error'] is None
        assert snapshot['domain_id'] == domain['id']
        assert mock_subprocess_run.call_count == 2

    def test_refresh_worker_updates_multiple_domains(self, client, read_from_db, write_to_db, monkeypatch):
        true_domain = write_to_db(
            'domain',
            {
                'hostname': 'true.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': False,
            },
        )
        false_domain = write_to_db(
            'domain',
            {
                'hostname': 'false.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': False,
            },
        )

        def fake_resolve(hostname, *args, **kwargs):
            if hostname == 'true.example.com':
                return _fake_a_record('203.0.113.10')
            return _fake_a_record('198.51.100.25')

        monkeypatch.setattr('dns.resolver.resolve', fake_resolve)

        client.get('/api/v2/health')
        sleep(0.3)

        updated_true = read_from_db('domain', filters={'id': true_domain['id']})
        updated_false = read_from_db('domain', filters={'id': false_domain['id']})

        assert updated_true['is_a_record_set'] is True
        assert updated_false['is_a_record_set'] is False

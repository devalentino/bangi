from time import sleep

import pytest

UNIX_TIMESTAMP_YEAR_2100 = 4_102_444_800


@pytest.mark.usefixtures('dns_resolver_mock')
class TestDnsRefreshWorker:
    @pytest.fixture(autouse=True)
    def mock_cleanup_discard_worker_settings(self, monkeypatch):
        monkeypatch.setattr('src.domains.workers.refresh_domain_dns.DOMAIN_DNS_REFRESH_PERIOD_SECONDS', 0.1)

    @pytest.fixture
    def domain(self, write_to_db):
        return write_to_db(
            'domain',
            {
                'hostname': 'example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_enabled': True,
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
        assert isinstance(snapshot['created_at'], int)
        assert snapshot['created_at'] < UNIX_TIMESTAMP_YEAR_2100
        assert snapshot['validation_status'] == 'success'
        assert snapshot['validation_error'] is None
        assert snapshot['domain_id'] == domain['id']
        assert mock_subprocess_run.call_count == 2

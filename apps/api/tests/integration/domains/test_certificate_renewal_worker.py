import json
from datetime import datetime, timedelta, timezone
from time import sleep
from unittest import mock

import pytest


def _certificate_output(hostname):
    return (
        f'Your cert is in: /etc/nginx/bangi/certs/{hostname}/fullchain.pem\n'
        f'Your cert key is in: /etc/nginx/bangi/certs/{hostname}/privkey.pem\n'
        'notBefore=May 13 00:00:00 2026 GMT\n'
        'notAfter=Aug 11 00:00:00 2026 GMT\n'
    )


@pytest.fixture
def certificate_worker_settings(monkeypatch):
    monkeypatch.setattr('src.domains.workers.renew_ca_certificates.CERTIFICATE_RENEWAL_PERIOD_SECONDS', 0.1)


@pytest.fixture
def is_disabled():
    return False


@pytest.fixture
def dashboard_domain(is_disabled, write_to_db):
    return write_to_db(
        'domain',
        {
            'hostname': 'dashboard.example.com',
            'purpose': 'dashboard',
            'campaign_id': None,
            'is_a_record_set': True,
            'is_disabled': is_disabled,
        },
    )


@pytest.mark.usefixtures('certificate_worker_settings', 'dns_resolver_mock')
class TestCertificateRenewalWorker:
    def test_successful_first_issuance_stores_metadata_and_republishes_https(
        self, client, dashboard_domain, read_from_db, mock_subprocess_run
    ):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = _certificate_output(dashboard_domain['hostname'])
        mock_subprocess_run.return_value.stderr = ''

        client.get('/api/v2/health')
        sleep(0.3)

        certificate = read_from_db('domain_certificate', filters={'domain_id': dashboard_domain['id']})
        snapshots = read_from_db(
            'health_nginx_validation_snapshot',
            filters={'domain_id': dashboard_domain['id']},
            fetchall=True,
        )

        assert certificate == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'domain_id': dashboard_domain['id'],
            'status': 'active',
            'ca': 'letsencrypt',
            'validation_method': 'http-01-webroot',
            'certificate_path': '/etc/nginx/bangi/certs/dashboard.example.com/fullchain.pem',
            'private_key_path': '/etc/nginx/bangi/certs/dashboard.example.com/privkey.pem',
            'issued_at': mock.ANY,
            'expires_at': mock.ANY,
            'last_attempted_at': mock.ANY,
            'last_issued_at': mock.ANY,
            'last_renewed_at': None,
            'next_retry_at': None,
            'failure_count': 0,
            'failure_reason': None,
        }
        assert certificate['issued_at'] is not None
        assert certificate['expires_at'] is not None
        assert certificate['last_attempted_at'] is not None
        assert certificate['last_issued_at'] is not None

        assert [call.args[0][-1] for call in mock_subprocess_run.call_args_list] == [
            'acme-issue-certificate dashboard.example.com',
            'nginx-validate',
            'nginx-reload',
        ]

        assert snapshots[-1] == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'domain_id': dashboard_domain['id'],
            'validation_status': 'success',
            'validation_error': None,
            'sites_available_files': mock.ANY,
            'sites_enabled_refs': mock.ANY,
        }
        assert json.loads(snapshots[-1]['sites_available_files']) != []
        assert json.loads(snapshots[-1]['sites_enabled_refs']) != []

    def test_failed_first_issuance_records_failed_metadata_and_backoff(
        self, client, dashboard_domain, read_from_db, mock_subprocess_run
    ):
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = 'ACME challenge failed'

        client.get('/api/v2/health')
        sleep(0.3)

        certificate = read_from_db('domain_certificate', filters={'domain_id': dashboard_domain['id']})

        assert certificate == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'domain_id': dashboard_domain['id'],
            'status': 'failed',
            'ca': 'letsencrypt',
            'validation_method': 'http-01-webroot',
            'certificate_path': None,
            'private_key_path': None,
            'issued_at': None,
            'expires_at': None,
            'last_attempted_at': mock.ANY,
            'last_issued_at': None,
            'last_renewed_at': None,
            'next_retry_at': mock.ANY,
            'failure_count': 1,
            'failure_reason': 'ACME challenge failed',
        }
        assert certificate['last_attempted_at'] is not None
        assert certificate['next_retry_at'] is not None
        assert [call.args[0][-1] for call in mock_subprocess_run.call_args_list] == [
            'acme-issue-certificate dashboard.example.com',
        ]

    def test_missing_a_record_skips_without_changing_certificate_status(
        self, client, dashboard_domain, read_from_db, mock_subprocess_run, dns_resolver_mock
    ):
        dns_resolver_mock.resolve.return_value = [mock.Mock(address='198.51.100.9')]

        client.get('/api/v2/health')
        sleep(0.3)

        assert read_from_db('domain_certificate', filters={'domain_id': dashboard_domain['id']}) is None
        assert mock_subprocess_run.call_count == 0

    def test_failed_renewal_keeps_existing_certificate_file_usage(
        self, client, dashboard_domain, read_from_db, write_to_db, mock_subprocess_run
    ):
        initial_certificate = write_to_db(
            'domain_certificate',
            {
                'domain_id': dashboard_domain['id'],
                'status': 'active',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': '/etc/nginx/bangi/certs/dashboard.example.com/fullchain.pem',
                'private_key_path': '/etc/nginx/bangi/certs/dashboard.example.com/privkey.pem',
                'expires_at': int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
                'last_attempted_at': None,
                'last_issued_at': int((datetime.now(timezone.utc) - timedelta(days=60)).timestamp()),
                'last_renewed_at': None,
                'next_retry_at': None,
                'failure_count': 0,
                'failure_reason': None,
            },
        )
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = 'renewal failed'

        client.get('/api/v2/health')
        sleep(0.3)

        certificate = read_from_db('domain_certificate', filters={'domain_id': dashboard_domain['id']})

        assert certificate == {
            'id': initial_certificate['id'],
            'created_at': initial_certificate['created_at'],
            'domain_id': dashboard_domain['id'],
            'status': 'failed',
            'ca': 'letsencrypt',
            'validation_method': 'http-01-webroot',
            'certificate_path': '/etc/nginx/bangi/certs/dashboard.example.com/fullchain.pem',
            'private_key_path': '/etc/nginx/bangi/certs/dashboard.example.com/privkey.pem',
            'issued_at': initial_certificate['issued_at'],
            'expires_at': initial_certificate['expires_at'],
            'last_attempted_at': mock.ANY,
            'last_issued_at': initial_certificate['last_issued_at'],
            'last_renewed_at': None,
            'next_retry_at': mock.ANY,
            'failure_count': 1,
            'failure_reason': 'renewal failed',
        }
        assert certificate['last_attempted_at'] is not None
        assert certificate['next_retry_at'] is not None
        assert [call.args[0][-1] for call in mock_subprocess_run.call_args_list] == [
            'acme-renew-certificate dashboard.example.com',
        ]

    def test_worker_limits_candidates_to_two_per_run(self, client, write_to_db, mock_subprocess_run):
        for index in range(3):
            write_to_db(
                'domain',
                {
                    'hostname': f'candidate-{index}.example.com',
                    'purpose': 'dashboard',
                    'campaign_id': None,
                    'is_a_record_set': True,
                    'is_disabled': False,
                },
            )
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = 'ACME failed'

        client.get('/api/v2/health')
        sleep(0.3)

        assert [call.args[0][-1] for call in mock_subprocess_run.call_args_list] == [
            'acme-issue-certificate candidate-0.example.com',
            'acme-issue-certificate candidate-1.example.com',
        ]


@pytest.mark.usefixtures('certificate_worker_settings', 'dns_resolver_mock')
class TestCertificateRenewalWorkerDisabledDomains:
    @pytest.fixture
    def is_disabled(self):
        return True

    @pytest.fixture
    def active_certificate(self, dashboard_domain, write_to_db):
        return write_to_db(
            'domain_certificate',
            {
                'domain_id': dashboard_domain['id'],
                'status': 'active',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': '/etc/nginx/bangi/certs/dashboard.example.com/fullchain.pem',
                'private_key_path': '/etc/nginx/bangi/certs/dashboard.example.com/privkey.pem',
                'expires_at': int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
                'last_attempted_at': None,
                'last_issued_at': None,
                'last_renewed_at': None,
                'next_retry_at': None,
                'failure_count': 0,
                'failure_reason': None,
            },
        )

    def test_disabled_domains_are_skipped_and_existing_metadata_is_retained(
        self, client, active_certificate, read_from_db, mock_subprocess_run
    ):
        client.get('/api/v2/health')
        sleep(0.3)

        assert read_from_db('domain_certificate', filters={'id': active_certificate['id']}) == active_certificate
        assert mock_subprocess_run.call_count == 0

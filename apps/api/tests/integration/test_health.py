from datetime import datetime, timezone
from decimal import Decimal
from time import sleep
from unittest import mock

import pytest


def test_health(client):
    response = client.get('/api/v2/health')
    assert response.status_code == 200, response.text
    assert response.json == {'healthy': True}


class TestDiskUtilizationIngestionCommand:
    def test_persists_snapshot_for_valid_payload(self, read_from_db):
        from src.health.ingest.disk_utilization import main as ingest_disk_utilization

        exit_code = ingest_disk_utilization(
            [
                '--filesystem',
                '/dev/sda1',
                '--mountpoint',
                '/var/lib/docker',
                '--total-bytes',
                '21474836480',
                '--used-bytes',
                '15032385536',
                '--available-bytes',
                '6442450944',
                '--used-percent',
                '70.0',
            ]
        )

        row = read_from_db('health_disk_utilization')

        assert exit_code == 0
        assert row == {
            'id': 1,
            'created_at': row['created_at'],
            'filesystem': '/dev/sda1',
            'mountpoint': '/var/lib/docker',
            'total_bytes': 21474836480,
            'used_bytes': 15032385536,
            'available_bytes': 6442450944,
            'used_percent': Decimal('70.00'),
        }
        assert row['created_at'] is not None

    def test_returns_non_zero_and_does_not_persist_invalid_payload__used_percent_101(self, capsys, read_from_db):
        from src.health.ingest.disk_utilization import main as ingest_disk_utilization

        exit_code = ingest_disk_utilization(
            [
                '--filesystem',
                '/dev/sda1',
                '--mountpoint',
                '/var/lib/docker',
                '--total-bytes',
                '100',
                '--used-bytes',
                '100',
                '--available-bytes',
                '0',
                '--used-percent',
                '101',
            ]
        )

        captured = capsys.readouterr()

        assert exit_code == 2
        assert read_from_db('health_disk_utilization') is None
        assert captured.err == '{"errors": {"used_percent": ["used_percent must be between 0 and 100."]}}\n'

    def test_returns_non_zero_and_does_not_persist_payload_with_used_bytes_above_total(self, capsys, read_from_db):
        from src.health.ingest.disk_utilization import main as ingest_disk_utilization

        exit_code = ingest_disk_utilization(
            [
                '--filesystem',
                '/dev/sda1',
                '--mountpoint',
                '/var/lib/docker',
                '--total-bytes',
                '100',
                '--used-bytes',
                '101',
                '--available-bytes',
                '0',
                '--used-percent',
                '100',
            ]
        )

        captured = capsys.readouterr()

        assert exit_code == 2
        assert read_from_db('health_disk_utilization') is None
        assert captured.err == '{"errors": {"used_bytes": ["used_bytes must be less than or equal to total_bytes."]}}\n'


class TestDiskUtilizationHistory:
    def test_returns_never_reported_summary_when_no_telemetry_exists(self, client, authorization):
        response = client.get(
            '/api/v2/health/disk-utilization/history',
            headers={'Authorization': authorization},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'summary': {
                'stale': False,
                'severity': None,
                'filesystem': None,
                'mountpoint': None,
                'totalBytes': None,
                'usedBytes': None,
                'availableBytes': None,
                'usedPercent': None,
                'lastReceivedAt': None,
            },
            'content': [],
        }

    def test_returns_ordered_history_and_fresh_summary(self, client, authorization, write_to_db, timestamp):
        write_to_db(
            'health_disk_utilization',
            {
                'created_at': timestamp - 35 * 24 * 60 * 60,
                'filesystem': '/dev/old',
                'mountpoint': '/old',
                'total_bytes': 1000,
                'used_bytes': 900,
                'available_bytes': 100,
                'used_percent': 90.0,
            },
        )
        first_history_row = write_to_db(
            'health_disk_utilization',
            {
                'created_at': timestamp - 2 * 24 * 60 * 60,
                'filesystem': '/dev/sda1',
                'mountpoint': '/var/lib/docker',
                'total_bytes': 1000,
                'used_bytes': 650,
                'available_bytes': 350,
                'used_percent': 65.0,
            },
        )
        latest_row = write_to_db(
            'health_disk_utilization',
            {
                'created_at': timestamp - 60,
                'filesystem': '/dev/sda1',
                'mountpoint': '/var/lib/docker',
                'total_bytes': 1000,
                'used_bytes': 720,
                'available_bytes': 280,
                'used_percent': 72.0,
            },
        )

        response = client.get(
            '/api/v2/health/disk-utilization/history?days=30',
            headers={'Authorization': authorization},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'summary': {
                'stale': False,
                'severity': 'warning',
                'filesystem': latest_row['filesystem'],
                'mountpoint': latest_row['mountpoint'],
                'totalBytes': latest_row['total_bytes'],
                'usedBytes': latest_row['used_bytes'],
                'availableBytes': latest_row['available_bytes'],
                'usedPercent': latest_row['used_percent'],
                'lastReceivedAt': timestamp - 60,
            },
            'content': [
                {
                    'date': mock.ANY,
                    'usedPercent': first_history_row['used_percent'],
                    'usedBytes': first_history_row['used_bytes'],
                    'availableBytes': first_history_row['available_bytes'],
                },
                {
                    'date': mock.ANY,
                    'usedPercent': latest_row['used_percent'],
                    'usedBytes': latest_row['used_bytes'],
                    'availableBytes': latest_row['available_bytes'],
                },
            ],
        }

    def test_returns_stale_summary_when_latest_telemetry_is_two_hours_old(
        self, client, authorization, write_to_db, timestamp
    ):
        stale_timestamp = timestamp - 3 * 60 * 60
        write_to_db(
            'health_disk_utilization',
            {
                'created_at': stale_timestamp,
                'filesystem': '/dev/sda1',
                'mountpoint': '/var/lib/docker',
                'total_bytes': 1000,
                'used_bytes': 800,
                'available_bytes': 200,
                'used_percent': 80.0,
            },
        )

        response = client.get(
            '/api/v2/health/disk-utilization/history',
            headers={'Authorization': authorization},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'summary': {
                'stale': True,
                'severity': 'critical',
                'filesystem': '/dev/sda1',
                'mountpoint': '/var/lib/docker',
                'totalBytes': 1000,
                'usedBytes': 800,
                'availableBytes': 200,
                'usedPercent': 80.0,
                'lastReceivedAt': stale_timestamp,
            },
            'content': [
                {
                    'date': mock.ANY,
                    'usedPercent': 80.0,
                    'usedBytes': 800,
                    'availableBytes': 200,
                }
            ],
        }


class TestDiskUtilizationAlerts:
    def test_returns_no_alerts_when_telemetry_has_never_been_reported(self, client, authorization):
        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {'content': []}

    def test_returns_warning_alert_when_latest_telemetry_is_in_warning_state(
        self, client, authorization, write_to_db, timestamp
    ):
        disk_utilization_snapshot = write_to_db(
            'health_disk_utilization',
            {
                'created_at': timestamp - 60,
                'filesystem': '/dev/sda1',
                'mountpoint': '/var/lib/docker',
                'total_bytes': 1000,
                'used_bytes': 720,
                'available_bytes': 280,
                'used_percent': 72.0,
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'system_health_disk_warning',
                    'message': 'Host disk usage is at 72.0% on /var/lib/docker.',
                    'severity': 'warning',
                    'source': 'src.health.alerts',
                    'payload': {
                        'filesystem': disk_utilization_snapshot['filesystem'],
                        'mountpoint': disk_utilization_snapshot['mountpoint'],
                        'usedPercent': disk_utilization_snapshot['used_percent'],
                    },
                }
            ]
        }

    def test_returns_critical_alert_when_latest_telemetry_is_in_critical_state(
        self, client, authorization, write_to_db, timestamp
    ):
        disk_utilization_snapshot = write_to_db(
            'health_disk_utilization',
            {
                'created_at': timestamp - 60,
                'filesystem': '/dev/sda1',
                'mountpoint': '/var/lib/docker',
                'total_bytes': 1000,
                'used_bytes': 820,
                'available_bytes': 180,
                'used_percent': 82.0,
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'system_health_disk_critical',
                    'message': 'Host disk usage is critical at 82.0% on /var/lib/docker.',
                    'severity': 'error',
                    'source': 'src.health.alerts',
                    'payload': {
                        'filesystem': disk_utilization_snapshot['filesystem'],
                        'mountpoint': disk_utilization_snapshot['mountpoint'],
                        'usedPercent': disk_utilization_snapshot['used_percent'],
                    },
                }
            ]
        }

    def test_returns_stale_alert_when_latest_telemetry_is_stale(self, client, authorization, write_to_db, timestamp):
        stale_timestamp = timestamp - 3 * 60 * 60
        stale_iso_timestamp = datetime.fromtimestamp(stale_timestamp, tz=timezone.utc).isoformat()
        disk_utilization_snapshot = write_to_db(
            'health_disk_utilization',
            {
                'created_at': stale_timestamp,
                'filesystem': '/dev/sda1',
                'mountpoint': '/var/lib/docker',
                'total_bytes': 1000,
                'used_bytes': 820,
                'available_bytes': 180,
                'used_percent': 82.0,
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'system_health_telemetry_stale',
                    'message': f'Host disk telemetry is stale. Last successful report was {stale_iso_timestamp}.',
                    'severity': 'error',
                    'source': 'src.health.alerts',
                    'payload': {
                        'filesystem': disk_utilization_snapshot['filesystem'],
                        'lastReceivedAt': disk_utilization_snapshot['created_at'],
                        'mountpoint': disk_utilization_snapshot['mountpoint'],
                    },
                }
            ]
        }


class TestCertificateHealthDiagnostics:
    def test_returns_certificate_risk_states_for_enabled_domains(
        self, client, authorization, write_to_db, campaign, timestamp
    ):
        missing_domain = write_to_db(
            'domain',
            {
                'hostname': 'missing-cert.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        failed_issuance_domain = write_to_db(
            'domain',
            {
                'hostname': 'failed-issuance.example.com',
                'purpose': 'campaign',
                'campaign_id': campaign['id'],
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        failed_renewal_domain = write_to_db(
            'domain',
            {
                'hostname': 'failed-renewal.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        expired_domain = write_to_db(
            'domain',
            {
                'hostname': 'expired.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        dns_not_ready_domain = write_to_db(
            'domain',
            {
                'hostname': 'dns-not-ready.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': False,
                'is_disabled': False,
            },
        )
        disabled_domain = write_to_db(
            'domain',
            {
                'hostname': 'disabled.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': True,
            },
        )

        write_to_db(
            'domain_certificate',
            {
                'domain_id': failed_issuance_domain['id'],
                'status': 'failed',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': None,
                'private_key_path': None,
                'issued_at': None,
                'expires_at': None,
                'last_attempted_at': timestamp - 600,
                'last_issued_at': None,
                'last_renewed_at': None,
                'next_retry_at': timestamp + 600,
                'failure_count': 1,
                'failure_reason': 'ACME challenge failed',
            },
        )
        write_to_db(
            'domain_certificate',
            {
                'domain_id': failed_renewal_domain['id'],
                'status': 'failed',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': '/etc/nginx/bangi/certs/failed-renewal.example.com/fullchain.pem',
                'private_key_path': '/etc/nginx/bangi/certs/failed-renewal.example.com/privkey.pem',
                'issued_at': timestamp - 90 * 24 * 60 * 60,
                'expires_at': timestamp + 10 * 24 * 60 * 60,
                'last_attempted_at': timestamp - 300,
                'last_issued_at': timestamp - 90 * 24 * 60 * 60,
                'last_renewed_at': None,
                'next_retry_at': timestamp + 600,
                'failure_count': 2,
                'failure_reason': 'renewal failed',
            },
        )
        write_to_db(
            'domain_certificate',
            {
                'domain_id': expired_domain['id'],
                'status': 'expired',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': '/etc/nginx/bangi/certs/expired.example.com/fullchain.pem',
                'private_key_path': '/etc/nginx/bangi/certs/expired.example.com/privkey.pem',
                'issued_at': timestamp - 90 * 24 * 60 * 60,
                'expires_at': timestamp - 60,
                'last_attempted_at': timestamp - 120,
                'last_issued_at': timestamp - 90 * 24 * 60 * 60,
                'last_renewed_at': timestamp - 30 * 24 * 60 * 60,
                'next_retry_at': timestamp,
                'failure_count': 0,
                'failure_reason': None,
            },
        )
        write_to_db(
            'domain_certificate',
            {
                'domain_id': disabled_domain['id'],
                'status': 'failed',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': None,
                'private_key_path': None,
                'issued_at': None,
                'expires_at': None,
                'last_attempted_at': timestamp - 600,
                'last_issued_at': None,
                'last_renewed_at': None,
                'next_retry_at': timestamp + 600,
                'failure_count': 1,
                'failure_reason': 'disabled domain failure',
            },
        )

        response = client.get('/api/v2/health/certificates', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'domainId': expired_domain['id'],
                    'hostname': 'expired.example.com',
                    'status': 'expired',
                    'isARecordSet': True,
                    'expiresAt': timestamp - 60,
                    'lastAttemptedAt': timestamp - 120,
                    'failureCount': 0,
                    'failureReason': None,
                },
                {
                    'domainId': failed_issuance_domain['id'],
                    'hostname': 'failed-issuance.example.com',
                    'status': 'failed',
                    'isARecordSet': True,
                    'expiresAt': None,
                    'lastAttemptedAt': timestamp - 600,
                    'failureCount': 1,
                    'failureReason': 'ACME challenge failed',
                },
                {
                    'domainId': failed_renewal_domain['id'],
                    'hostname': 'failed-renewal.example.com',
                    'status': 'failed',
                    'isARecordSet': True,
                    'expiresAt': timestamp + 10 * 24 * 60 * 60,
                    'lastAttemptedAt': timestamp - 300,
                    'failureCount': 2,
                    'failureReason': 'renewal failed',
                },
                {
                    'domainId': dns_not_ready_domain['id'],
                    'hostname': 'dns-not-ready.example.com',
                    'status': None,
                    'isARecordSet': False,
                    'expiresAt': None,
                    'lastAttemptedAt': None,
                    'failureCount': None,
                    'failureReason': None,
                },
                {
                    'domainId': missing_domain['id'],
                    'hostname': 'missing-cert.example.com',
                    'status': None,
                    'isARecordSet': True,
                    'expiresAt': None,
                    'lastAttemptedAt': None,
                    'failureCount': None,
                    'failureReason': None,
                },
            ]
        }


class TestCertificateAlerts:
    def test_first_issuance_failure_does_not_create_alert(
        self, client, authorization, write_to_db, campaign, timestamp
    ):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'first-issue-failed.example.com',
                'purpose': 'campaign',
                'campaign_id': campaign['id'],
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        write_to_db(
            'domain_certificate',
            {
                'domain_id': domain['id'],
                'status': 'failed',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': None,
                'private_key_path': None,
                'issued_at': None,
                'expires_at': None,
                'last_attempted_at': timestamp - 60,
                'last_issued_at': None,
                'last_renewed_at': None,
                'next_retry_at': timestamp + 600,
                'failure_count': 1,
                'failure_reason': 'ACME challenge failed',
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {'content': []}

    def test_repeated_first_issuance_failure_creates_warning_alert(
        self, client, authorization, write_to_db, campaign, timestamp
    ):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'repeated-first-issue-failed.example.com',
                'purpose': 'campaign',
                'campaign_id': campaign['id'],
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        write_to_db(
            'domain_certificate',
            {
                'domain_id': domain['id'],
                'status': 'failed',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': None,
                'private_key_path': None,
                'issued_at': None,
                'expires_at': None,
                'last_attempted_at': timestamp - 60,
                'last_issued_at': None,
                'last_renewed_at': None,
                'next_retry_at': timestamp + 600,
                'failure_count': 2,
                'failure_reason': 'ACME rate limit',
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'system_health_certificate_issuance_failed',
                    'message': 'Certificate issuance failed repeatedly for repeated-first-issue-failed.example.com.',
                    'severity': 'warning',
                    'source': 'src.domains.alerts',
                    'payload': {
                        'domainId': domain['id'],
                        'hostname': 'repeated-first-issue-failed.example.com',
                        'status': 'failed',
                        'expiresAt': None,
                        'lastAttemptedAt': timestamp - 60,
                        'failureCount': 2,
                        'failureReason': 'ACME rate limit',
                    },
                }
            ]
        }

    def test_failed_renewal_within_warning_window_creates_warning_alert(
        self, client, authorization, write_to_db, timestamp
    ):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'renewal-warning.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        write_to_db(
            'domain_certificate',
            {
                'domain_id': domain['id'],
                'status': 'failed',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': '/etc/nginx/bangi/certs/renewal-warning.example.com/fullchain.pem',
                'private_key_path': '/etc/nginx/bangi/certs/renewal-warning.example.com/privkey.pem',
                'issued_at': timestamp - 80 * 24 * 60 * 60,
                'expires_at': timestamp + 10 * 24 * 60 * 60,
                'last_attempted_at': timestamp - 60,
                'last_issued_at': timestamp - 80 * 24 * 60 * 60,
                'last_renewed_at': None,
                'next_retry_at': timestamp + 600,
                'failure_count': 1,
                'failure_reason': 'ACME renewal failed',
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'system_health_certificate_renewal_warning',
                    'message': 'Certificate renewal failed for renewal-warning.example.com and expires within 14 days.',
                    'severity': 'warning',
                    'source': 'src.domains.alerts',
                    'payload': {
                        'domainId': domain['id'],
                        'hostname': 'renewal-warning.example.com',
                        'status': 'failed',
                        'expiresAt': timestamp + 10 * 24 * 60 * 60,
                        'lastAttemptedAt': timestamp - 60,
                        'failureCount': 1,
                        'failureReason': 'ACME renewal failed',
                    },
                }
            ]
        }

    def test_failed_renewal_within_error_window_creates_error_alert(
        self, client, authorization, write_to_db, timestamp
    ):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'renewal-error.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        write_to_db(
            'domain_certificate',
            {
                'domain_id': domain['id'],
                'status': 'failed',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': '/etc/nginx/bangi/certs/renewal-error.example.com/fullchain.pem',
                'private_key_path': '/etc/nginx/bangi/certs/renewal-error.example.com/privkey.pem',
                'issued_at': timestamp - 80 * 24 * 60 * 60,
                'expires_at': timestamp + 5 * 24 * 60 * 60,
                'last_attempted_at': timestamp - 60,
                'last_issued_at': timestamp - 80 * 24 * 60 * 60,
                'last_renewed_at': None,
                'next_retry_at': timestamp + 600,
                'failure_count': 1,
                'failure_reason': 'ACME renewal failed',
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'system_health_certificate_renewal_error',
                    'message': 'Certificate renewal failed for renewal-error.example.com and expires within 7 days.',
                    'severity': 'error',
                    'source': 'src.domains.alerts',
                    'payload': {
                        'domainId': domain['id'],
                        'hostname': 'renewal-error.example.com',
                        'status': 'failed',
                        'expiresAt': timestamp + 5 * 24 * 60 * 60,
                        'lastAttemptedAt': timestamp - 60,
                        'failureCount': 1,
                        'failureReason': 'ACME renewal failed',
                    },
                }
            ]
        }

    def test_expired_certificate_creates_error_alert(self, client, authorization, write_to_db, timestamp):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'expired-alert.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        write_to_db(
            'domain_certificate',
            {
                'domain_id': domain['id'],
                'status': 'expired',
                'ca': 'letsencrypt',
                'validation_method': 'http-01-webroot',
                'certificate_path': '/etc/nginx/bangi/certs/expired-alert.example.com/fullchain.pem',
                'private_key_path': '/etc/nginx/bangi/certs/expired-alert.example.com/privkey.pem',
                'issued_at': timestamp - 80 * 24 * 60 * 60,
                'expires_at': timestamp - 60,
                'last_attempted_at': timestamp - 120,
                'last_issued_at': timestamp - 80 * 24 * 60 * 60,
                'last_renewed_at': None,
                'next_retry_at': timestamp,
                'failure_count': 0,
                'failure_reason': None,
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'system_health_certificate_expired',
                    'message': 'Certificate for expired-alert.example.com is expired.',
                    'severity': 'error',
                    'source': 'src.domains.alerts',
                    'payload': {
                        'domainId': domain['id'],
                        'hostname': 'expired-alert.example.com',
                        'status': 'expired',
                        'expiresAt': timestamp - 60,
                        'lastAttemptedAt': timestamp - 120,
                        'failureCount': 0,
                        'failureReason': None,
                    },
                }
            ]
        }


class TestCleanupDiskUtilizationWorker:
    @pytest.fixture(autouse=True)
    def mock_cleanup_worker_settings(self, monkeypatch):
        monkeypatch.setattr('src.health.workers.DISK_UTILIZATION_HISTORY_CLEANUP_PERIOD_SECONDS', 0.1)

    @pytest.fixture
    def fresh_snapshot_timestamp(self, timestamp):
        return timestamp - 60

    @pytest.fixture
    def disk_utilization_snapshots(self, write_to_db, timestamp, fresh_snapshot_timestamp):
        old_snapshot_timestamp = timestamp - 31 * 24 * 60 * 60

        write_to_db(
            'health_disk_utilization',
            {
                'created_at': old_snapshot_timestamp,
                'filesystem': '/dev/old',
                'mountpoint': '/old',
                'total_bytes': 1000,
                'used_bytes': 900,
                'available_bytes': 100,
                'used_percent': 90.0,
            },
        )
        write_to_db(
            'health_disk_utilization',
            {
                'created_at': fresh_snapshot_timestamp,
                'filesystem': '/dev/sda1',
                'mountpoint': '/var/lib/docker',
                'total_bytes': 1000,
                'used_bytes': 700,
                'available_bytes': 300,
                'used_percent': 70.0,
            },
        )

    @pytest.mark.usefixtures('disk_utilization_snapshots')
    def test_cleanup_worker_deletes_expired_snapshots(self, client, fresh_snapshot_timestamp, read_from_db):
        client.get('/api/v2/health')  # triggers application start

        sleep(0.3)

        snapshots = read_from_db('health_disk_utilization', fetchall=True)
        assert len(snapshots) == 1
        assert snapshots[0]['created_at'] == fresh_snapshot_timestamp


class TestNginxValidationHealth:
    def test_returns_null_snapshot_when_no_publish_attempts_exist(self, client, authorization):
        response = client.get('/api/v2/health/nginx', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {'content': None}

    def test_returns_latest_nginx_validation_snapshot(self, client, authorization, write_to_db, timestamp):
        older_timestamp = timestamp - 120
        write_to_db(
            'health_nginx_validation_snapshot',
            {
                'created_at': older_timestamp,
                'domain_id': 7,
                'validation_status': 'failed',
                'validation_error': 'nginx: [emerg] bad config',
                'sites_available_files': ['sites-available/example.com/old.conf'],
                'sites_enabled_refs': ['sites-enabled/example.com.conf -> ../sites-available/example.com/old.conf'],
            },
        )
        latest_snapshot = write_to_db(
            'health_nginx_validation_snapshot',
            {
                'created_at': timestamp - 10,
                'domain_id': 9,
                'validation_status': 'success',
                'validation_error': None,
                'sites_available_files': [
                    'sites-available/example.com/20260510T010101Z-abc12345.conf',
                    'sites-available/example.com/20260510T010202Z-def67890.conf',
                ],
                'sites_enabled_refs': [
                    'sites-enabled/example.com.conf -> ../sites-available/example.com/20260510T010202Z-def67890.conf'
                ],
            },
        )

        response = client.get('/api/v2/health/nginx', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': {
                'domainId': latest_snapshot['domain_id'],
                'validationStatus': latest_snapshot['validation_status'],
                'validationError': latest_snapshot['validation_error'],
                'validationTimestamp': timestamp - 10,
                'sitesAvailableFiles': [
                    'sites-available/example.com/20260510T010101Z-abc12345.conf',
                    'sites-available/example.com/20260510T010202Z-def67890.conf',
                ],
                'sitesEnabledRefs': [
                    'sites-enabled/example.com.conf -> ../sites-available/example.com/20260510T010202Z-def67890.conf'
                ],
            }
        }

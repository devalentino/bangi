from decimal import Decimal


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
                    'createdAt': first_history_row['created_at'],
                    'usedPercent': first_history_row['used_percent'],
                    'usedBytes': first_history_row['used_bytes'],
                    'availableBytes': first_history_row['available_bytes'],
                },
                {
                    'createdAt': latest_row['created_at'],
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
                    'createdAt': stale_timestamp,
                    'usedPercent': 80.0,
                    'usedBytes': 800,
                    'availableBytes': 200,
                }
            ],
        }

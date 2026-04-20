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

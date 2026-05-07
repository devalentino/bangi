from time import sleep

import pytest
from fixtures.utils import click_uuid


class TestCleanupDiscardWorker:
    @pytest.fixture(autouse=True)
    def mock_cleanup_discard_worker_settings(self, monkeypatch):
        monkeypatch.setattr('src.tracker.workers.DISCARD_RETENTION_SECONDS', 300)
        monkeypatch.setattr('src.tracker.workers.DISCARD_CLEANUP_PERIOD_SECONDS', 0.1)

    def test_cleanup_discard_worker__deletes_expired_discards(
        self, client, campaign, write_to_db, read_from_db, monkeypatch
    ):
        monkeypatch.setattr('src.tracker.workers.time.time', lambda: 2000)

        write_to_db(
            'track_discard',
            {
                'click_id': click_uuid(1),
                'campaign_id': campaign['id'],
                'country': 'MD',
                'browser_family': 'Mobile Safari',
                'os_family': 'iOS',
                'device_family': 'iPhone',
                'is_mobile': True,
                'is_bot': False,
                'created_at': 1000,
            },
        )
        fresh_discard = write_to_db(
            'track_discard',
            {
                'click_id': click_uuid(2),
                'campaign_id': campaign['id'],
                'country': 'UA',
                'browser_family': 'Chrome',
                'os_family': 'Android',
                'device_family': 'Pixel 8',
                'is_mobile': True,
                'is_bot': False,
                'created_at': 1900,
            },
        )

        sleep(0.3)

        discards = read_from_db('track_discard', fetchall=True)
        assert discards == [fresh_discard]

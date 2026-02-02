from uuid import uuid4

import pytest


@pytest.fixture
def click(campaign, timestamp, write_to_db):
    return write_to_db(
        'track_click',
        {
            'campaign_id': campaign['id'],
            'click_id': str(uuid4()),
            'parameters': {},
            'created_at': timestamp,
        },
    )

from uuid import uuid4

import pytest


@pytest.fixture
def click(campaign, timestamp, write_to_db):
    return write_to_db(
        'track_click',
        {
            'campaign_id': campaign['id'],
            'click_id': uuid4().hex,
            'parameters': {},
            'created_at': timestamp,
        },
    )

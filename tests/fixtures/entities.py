import pytest


@pytest.fixture
def campaign(write_to_db, campaign_payload):
    return write_to_db('campaign', campaign_payload)

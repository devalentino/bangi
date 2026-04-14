import pytest


@pytest.fixture
def campaign(write_to_db, campaign_payload):
    return write_to_db('campaign', campaign_payload)


@pytest.fixture
def flow(write_to_db, flow_payload, campaign):
    return write_to_db('flow', flow_payload | {'campaign_id': campaign['id']})

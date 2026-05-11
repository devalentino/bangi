import pytest


@pytest.fixture
def campaign(write_to_db, campaign_payload):
    return write_to_db('campaign', campaign_payload)


@pytest.fixture
def flow(write_to_db, flow_payload, campaign):
    return write_to_db('flow', flow_payload | {'campaign_id': campaign['id']})


@pytest.fixture
def domain(write_to_db, campaign):
    return write_to_db(
        'domain',
        {
            'hostname': 'campaign.example.com',
            'purpose': 'campaign',
            'campaign_id': campaign['id'],
            'is_a_record_set': True,
            'is_disabled': False,
        },
    )

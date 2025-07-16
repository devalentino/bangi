import pytest


@pytest.fixture
def campaign_name():
    return 'Test Campaign'


@pytest.fixture
def campaign_payload(campaign_name):
    return {'name': campaign_name}

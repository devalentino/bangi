import pytest


@pytest.fixture
def campaign_name():
    return 'Test Campaign'


@pytest.fixture
def flow_name():
    return 'White flow'


@pytest.fixture
def flow_is_deleted():
    return False


@pytest.fixture
def status_mapper():
    return {
        'parameter': 'state',
        'mapping': {'executed': 'accept', 'failed': 'reject'},
    }


@pytest.fixture
def flow_rule():
    return 'country == "MD"'


@pytest.fixture
def expenses_distribution_parameter():
    return None


@pytest.fixture
def campaign_payload(campaign_name, status_mapper, expenses_distribution_parameter):
    return {
        'name': campaign_name,
        'cost_model': 'cpa',
        'cost_value': 10,
        'currency': 'usd',
        'status_mapper': status_mapper,
        'expenses_distribution_parameter': expenses_distribution_parameter,
    }


@pytest.fixture
def flow_payload(flow_name, flow_rule, flow_is_deleted):
    return {
        'name': flow_name,
        'order_value': 1,
        'rule': flow_rule,
        'action_type': 'redirect',
        'redirect_url': 'https://example.com',
        'is_enabled': True,
        'is_deleted': flow_is_deleted,
    }

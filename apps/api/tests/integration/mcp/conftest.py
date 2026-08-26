import pytest


@pytest.fixture
def mcp_headers(pat_token):
    return {'Authorization': f'Bearer {pat_token}', 'MCP-Protocol-Version': '2026-07-28'}


@pytest.fixture
def alert_free_campaign(write_to_db, campaign_payload, flow_payload, set_default_flow_id):
    def _create(name):
        campaign = write_to_db('campaign', campaign_payload | {'name': name})
        flow = write_to_db('flow', flow_payload | {'campaign_id': campaign['id'], 'rule': None})
        set_default_flow_id(campaign['id'], flow['id'])
        return campaign

    return _create

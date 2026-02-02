import json
from unittest import mock
from uuid import uuid4


def test_track_click(client, campaign, read_from_db):
    request_payload = {
        'clickId': str(uuid4()),
        'campaignId': campaign['id'],
        'campaign_name': 'test campaign',
        'adset_name': 'adset1',
        'ad_name': 'ad_1',
        'pixel': '0001',
    }

    response = client.post('/api/v2/track/click', json=request_payload)
    assert response.status_code == 201, response.text

    click = read_from_db('track_click')
    assert click == {
        'id': mock.ANY,
        'campaign_id': campaign['id'],
        'click_id': request_payload['clickId'],
        'parameters': mock.ANY,
        'created_at': mock.ANY,
    }

    assert json.loads(click['parameters']) == {
        'campaign_name': request_payload['campaign_name'],
        'adset_name': request_payload['adset_name'],
        'ad_name': request_payload['ad_name'],
        'pixel': request_payload['pixel'],
    }

from unittest import mock
from uuid import uuid4


def test_track_click(client, read_from_db):
    click_id = uuid4()
    request_payload = {
        'click_id': str(click_id),
        'campaign_name': 'test campaign',
        'adset_name': 'adset1',
        'ad_name': 'ad_1',
        'pixel': '0001',
    }

    response = client.post('/api/v2/track/click', json=request_payload)
    assert response.status_code == 201, response.text

    r = read_from_db('track_click')
    assert r == request_payload | {'id': mock.ANY, 'click_id': click_id.hex}

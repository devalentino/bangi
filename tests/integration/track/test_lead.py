import json
from unittest import mock
from uuid import uuid4


class TestLead:
    def test_track_lead__post(self, client, read_from_db):
        request_payload = {
            'clickId': str(uuid4()),
            'status': 'accept',
            'tid': '123',
            'offer_id': '456',
            'from': 'terraleads.com',
        }

        response = client.post('/api/v2/track/lead', json=request_payload)
        assert response.status_code == 201, response.text

        lead = read_from_db('track_lead')
        assert lead == {
            'id': mock.ANY,
            'click_id': request_payload['clickId'],
            'parameters': mock.ANY,
            'created_at': mock.ANY,
        }

        assert json.loads(lead['parameters']) == {
            'from': request_payload['from'],
            'offer_id': request_payload['offer_id'],
            'status': request_payload['status'],
            'tid': request_payload['tid'],
        }

    def test_track_lead__get(self, client, read_from_db):
        request_payload = {
            'clickId': str(uuid4()),
            'status': 'accept',
            'tid': '123',
            'offer_id': '456',
            'from': 'terraleads.com',
        }

        response = client.get('/api/v2/track/lead', query_string=request_payload)
        assert response.status_code == 201, response.text

        lead = read_from_db('track_lead')
        assert lead == {
            'id': mock.ANY,
            'click_id': request_payload['clickId'],
            'parameters': mock.ANY,
            'created_at': mock.ANY,
        }

        assert json.loads(lead['parameters']) == {
            'from': request_payload['from'],
            'offer_id': request_payload['offer_id'],
            'status': request_payload['status'],
            'tid': request_payload['tid'],
        }

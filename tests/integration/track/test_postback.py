import json
from unittest import mock
from uuid import uuid4


class TestPostback:
    def test_track_postback__post(self, client, campaign, read_from_db):
        request_payload = {
            'clickId': str(uuid4()),
            'status': 'accept',
            'tid': '123',
            'payout': 10,
            'offer_id': '456',
            'lead_status': 'accept,expect',
            'sale_status': 'confirm',
            'rejected_status': 'reject,fail,trash,error',
            'return': 'OK',
            'from': 'terraleads.com',
        }

        response = client.post('/api/v2/track/postback', json=request_payload)
        assert response.status_code == 201, response.text

        postback = read_from_db('track_postback')
        assert postback == {
            'id': mock.ANY,
            'click_id': request_payload['clickId'],
            'parameters': mock.ANY,
            'status': None,
            'cost_value': None,
            'currency': None,
            'created_at': mock.ANY,
        }

        assert json.loads(postback['parameters']) == {
            'from': request_payload['from'],
            'lead_status': request_payload['lead_status'],
            'offer_id': request_payload['offer_id'],
            'payout': request_payload['payout'],
            'rejected_status': request_payload['rejected_status'],
            'return': request_payload['return'],
            'sale_status': request_payload['sale_status'],
            'status': request_payload['status'],
            'tid': request_payload['tid'],
        }

    def test_track_postback__get(self, client, campaign, read_from_db):
        request_payload = {
            'clickId': str(uuid4()),
            'status': 'accept',
            'tid': '123',
            'payout': 10,
            'offer_id': '456',
            'lead_status': 'accept,expect',
            'sale_status': 'confirm',
            'rejected_status': 'reject,fail,trash,error',
            'return': 'OK',
            'from': 'terraleads.com',
        }

        response = client.get('/api/v2/track/postback', query_string=request_payload)
        assert response.status_code == 201, response.text

        postback = read_from_db('track_postback')
        assert postback == {
            'id': mock.ANY,
            'click_id': request_payload['clickId'],
            'parameters': mock.ANY,
            'status': None,
            'cost_value': None,
            'currency': None,
            'created_at': mock.ANY,
        }

        assert json.loads(postback['parameters']) == {
            'from': request_payload['from'],
            'lead_status': request_payload['lead_status'],
            'offer_id': request_payload['offer_id'],
            'payout': str(request_payload['payout']),
            'rejected_status': request_payload['rejected_status'],
            'return': request_payload['return'],
            'sale_status': request_payload['sale_status'],
            'status': request_payload['status'],
            'tid': request_payload['tid'],
        }

    def test_track_postback__maps_status(self, client, click, campaign, read_from_db):
        response = client.post('/api/v2/track/postback', json={'clickId': click['click_id'], 'state': 'executed'})
        assert response.status_code == 201, response.text

        postback = read_from_db('track_postback')
        assert postback['status'] == 'accept'
        assert postback['cost_value'] == campaign['cost_value']
        assert postback['currency'] == campaign['currency']

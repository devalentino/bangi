import json
from unittest import mock


class TestPostbacksReport:
    def test_get_postbacks_report(self, client, authorization, campaign, campaign_payload, timestamp, write_to_db):
        other_campaign = write_to_db('campaign', campaign_payload | {'name': 'Other Campaign'})

        first_click = write_to_db(
            'track_click',
            {
                'click_id': 'click-1',
                'campaign_id': campaign['id'],
                'parameters': {'source': 'fb'},
                'created_at': timestamp - 20,
            },
        )
        second_click = write_to_db(
            'track_click',
            {
                'click_id': 'click-2',
                'campaign_id': campaign['id'],
                'parameters': {'source': 'tt'},
                'created_at': timestamp - 10,
            },
        )
        other_click = write_to_db(
            'track_click',
            {
                'click_id': 'click-3',
                'campaign_id': other_campaign['id'],
                'parameters': {'source': 'native'},
                'created_at': timestamp,
            },
        )

        first_postback = write_to_db(
            'track_postback',
            {
                'click_id': first_click['click_id'],
                'parameters': {'state': 'executed'},
                'status': 'accept',
                'cost_value': 10,
                'currency': 'usd',
                'created_at': timestamp - 5,
            },
        )
        second_postback = write_to_db(
            'track_postback',
            {
                'click_id': second_click['click_id'],
                'parameters': {'state': 'failed'},
                'status': 'reject',
                'cost_value': None,
                'currency': None,
                'created_at': timestamp,
            },
        )
        write_to_db(
            'track_postback',
            {
                'click_id': other_click['click_id'],
                'parameters': {'state': 'executed'},
                'status': 'accept',
                'cost_value': 15,
                'currency': 'usd',
                'created_at': timestamp + 5,
            },
        )

        response = client.get(
            '/api/v2/reports/leads',
            headers={'Authorization': authorization},
            query_string={
                'campaignId': campaign['id'],
                'page': 1,
                'pageSize': 10,
                'sortBy': 'createdAt',
                'sortOrder': 'desc',
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'clickId': second_postback['click_id'],
                    'status': second_postback['status'],
                    'costValue': second_postback['cost_value'],
                    'currency': second_postback['currency'],
                    'createdAt': mock.ANY,  # TODO: handle correct timestamps
                },
                {
                    'clickId': first_postback['click_id'],
                    'status': first_postback['status'],
                    'costValue': float(first_postback['cost_value']),
                    'currency': first_postback['currency'],
                    'createdAt': mock.ANY,
                },
            ],
            'pagination': {'page': 1, 'pageSize': 10, 'sortBy': 'createdAt', 'sortOrder': 'desc', 'total': 2},
            'filters': {'campaignId': 1},
        }

    def test_get_lead(self, client, authorization, campaign, timestamp, write_to_db):
        click = write_to_db(
            'track_click',
            {
                'click_id': 'click-1',
                'campaign_id': campaign['id'],
                'parameters': {'source': 'fb', 'ad_name': 'ad-1'},
                'created_at': timestamp - 20,
            },
        )
        older_postback = write_to_db(
            'track_postback',
            {
                'click_id': click['click_id'],
                'parameters': {'state': 'queued'},
                'status': 'expect',
                'cost_value': 10,
                'currency': 'usd',
                'created_at': timestamp - 10,
            },
        )
        newer_postback = write_to_db(
            'track_postback',
            {
                'click_id': click['click_id'],
                'parameters': {'state': 'executed'},
                'status': 'accept',
                'cost_value': 10,
                'currency': 'usd',
                'created_at': timestamp,
            },
        )

        response = client.get(f'/api/v2/reports/leads/{click["click_id"]}', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'clickId': click['click_id'],
            'campaignId': click['campaign_id'],
            'parameters': json.loads(click['parameters']),
            'createdAt': mock.ANY,
            'postbacks': [
                {
                    'clickId': newer_postback['click_id'],
                    'parameters': json.loads(newer_postback['parameters']),
                    'status': newer_postback['status'],
                    'costValue': float(newer_postback['cost_value']),
                    'currency': newer_postback['currency'],
                    'createdAt': mock.ANY,
                },
                {
                    'clickId': older_postback['click_id'],
                    'parameters': json.loads(older_postback['parameters']),
                    'status': older_postback['status'],
                    'costValue': float(older_postback['cost_value']),
                    'currency': older_postback['currency'],
                    'createdAt': mock.ANY,
                },
            ],
        }

    def test_get_lead__non_existent(self, client, authorization):
        response = client.get('/api/v2/reports/leads/missing-click', headers={'Authorization': authorization})

        assert response.status_code == 404, response.text
        assert response.json == {'message': 'Click does not exist'}

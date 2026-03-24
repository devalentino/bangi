import json
from unittest import mock
from uuid import uuid4

from tests.fixtures.utils import click_uuid


class TestGetLeads:
    def test_get_leads(self, client, authorization, campaign, campaign_payload, timestamp, write_to_db):
        other_campaign = write_to_db('campaign', campaign_payload | {'name': 'Other Campaign'})

        first_report_lead = write_to_db(
            'report_leads',
            {
                'click_id': click_uuid(1),
                'campaign_id': campaign['id'],
                'click_created_at': timestamp - 20,
                'status': 'accept',
                'cost_value': 10,
                'currency': 'usd',
            },
        )
        second_report_lead = write_to_db(
            'report_leads',
            {
                'click_id': click_uuid(2),
                'campaign_id': campaign['id'],
                'click_created_at': timestamp - 10,
                'status': 'reject',
                'cost_value': None,
                'currency': None,
            },
        )
        third_report_lead = write_to_db(
            'report_leads',
            {
                'click_id': click_uuid(4),
                'campaign_id': campaign['id'],
                'click_created_at': timestamp - 5,
                'status': None,
                'cost_value': None,
                'currency': None,
            },
        )
        write_to_db(
            'report_leads',
            {
                'click_id': click_uuid(3),
                'campaign_id': other_campaign['id'],
                'click_created_at': timestamp,
                'status': 'accept',
                'cost_value': 15,
                'currency': 'usd',
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
                    'clickId': third_report_lead['click_id'],
                    'status': None,
                    'costValue': None,
                    'currency': None,
                    'createdAt': mock.ANY,
                },
                {
                    'clickId': second_report_lead['click_id'],
                    'status': second_report_lead['status'],
                    'costValue': second_report_lead['cost_value'],
                    'currency': second_report_lead['currency'],
                    'createdAt': mock.ANY,  # TODO: handle correct timestamps
                },
                {
                    'clickId': first_report_lead['click_id'],
                    'status': first_report_lead['status'],
                    'costValue': float(first_report_lead['cost_value']),
                    'currency': first_report_lead['currency'],
                    'createdAt': mock.ANY,
                },
            ],
            'pagination': {'page': 1, 'pageSize': 10, 'sortBy': 'createdAt', 'sortOrder': 'desc', 'total': 3},
            'filters': {'campaignId': 1},
        }

    def test_get_lead(self, client, authorization, campaign, timestamp, write_to_db):
        click = write_to_db(
            'track_click',
            {
                'click_id': click_uuid(21),
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
        older_lead = write_to_db(
            'track_lead',
            {
                'click_id': click['click_id'],
                'parameters': {'state': 'queued'},
                'created_at': timestamp - 15,
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
        newer_lead = write_to_db(
            'track_lead',
            {
                'click_id': click['click_id'],
                'parameters': {'state': 'executed'},
                'created_at': timestamp - 5,
            },
        )

        response = client.get(f'/api/v2/reports/leads/{click["click_id"]}', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'clickId': click['click_id'],
            'campaignId': click['campaign_id'],
            'campaignName': campaign['name'],
            'parameters': json.loads(click['parameters']),
            'createdAt': mock.ANY,
            'leads': [
                {
                    'parameters': json.loads(newer_lead['parameters']),
                    'createdAt': mock.ANY,
                },
                {
                    'parameters': json.loads(older_lead['parameters']),
                    'createdAt': mock.ANY,
                },
            ],
            'postbacks': [
                {
                    'parameters': json.loads(newer_postback['parameters']),
                    'status': newer_postback['status'],
                    'costValue': float(newer_postback['cost_value']),
                    'currency': newer_postback['currency'],
                    'createdAt': mock.ANY,
                },
                {
                    'parameters': json.loads(older_postback['parameters']),
                    'status': older_postback['status'],
                    'costValue': float(older_postback['cost_value']),
                    'currency': older_postback['currency'],
                    'createdAt': mock.ANY,
                },
            ],
        }

    def test_get_lead__non_existent(self, client, authorization):
        response = client.get(f'/api/v2/reports/leads/{uuid4()}', headers={'Authorization': authorization})

        assert response.status_code == 404, response.text
        assert response.json == {'message': 'Click does not exist'}

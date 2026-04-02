import json
from time import sleep
from unittest import mock
from uuid import uuid4

import pytest

from tests.fixtures.utils import click_uuid


class TestGetLeads:
    def test_get_leads(self, client, authorization, campaign, campaign_payload, timestamp, write_to_db):
        other_campaign = write_to_db('campaign', campaign_payload | {'name': 'Other Campaign'})

        first_report_lead = write_to_db(
            'report_lead',
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
            'report_lead',
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
            'report_lead',
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
            'report_lead',
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
                    'clickId': str(third_report_lead['click_id']),
                    'status': None,
                    'costValue': None,
                    'currency': None,
                    'createdAt': mock.ANY,
                },
                {
                    'clickId': str(second_report_lead['click_id']),
                    'status': second_report_lead['status'],
                    'costValue': second_report_lead['cost_value'],
                    'currency': second_report_lead['currency'],
                    'createdAt': mock.ANY,  # TODO: handle correct timestamps
                },
                {
                    'clickId': str(first_report_lead['click_id']),
                    'status': first_report_lead['status'],
                    'costValue': float(first_report_lead['cost_value']),
                    'currency': first_report_lead['currency'],
                    'createdAt': mock.ANY,
                },
            ],
            'pagination': {'page': 1, 'pageSize': 10, 'sortBy': 'createdAt', 'sortOrder': 'desc', 'total': 3},
            'filters': {'campaignId': 1},
        }


class TestGetLead:
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
            'clickId': str(click['click_id']),
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


class TestReportLeadWorker:
    @pytest.fixture(autouse=True)
    def mock_report_lead_worker_settings(self, monkeypatch):
        monkeypatch.setattr('src.reports.workers.AGGREGATION_PERIOD_SECONDS', 0.1)
        monkeypatch.setattr('src.reports.workers.MIN_QUEUE_SIZE', 1)

    def test_track_click__does_not_create_report_lead(self, client, campaign, read_from_db):
        click_id = uuid4()

        client.post(
            '/api/v2/track/click',
            json={
                'clickId': str(click_id),
                'campaignId': campaign['id'],
                'source': 'fb',
            },
        )

        sleep(0.3)

        report_lead = read_from_db('report_lead')

        assert report_lead is None

    def test_track_lead_without_click__does_not_create_report_lead(self, client, read_from_db):
        click_id = uuid4()

        client.post(
            '/api/v2/track/lead',
            json={
                'clickId': str(click_id),
                'status': 'accept',
            },
        )

        sleep(0.3)

        report_lead = read_from_db('report_lead')

        assert report_lead is None

    def test_track_postback_without_click__does_not_create_report_lead(self, client, read_from_db):
        click_id = uuid4()

        client.post(
            '/api/v2/track/postback',
            json={
                'clickId': str(click_id),
                'state': 'executed',
            },
        )

        sleep(0.3)

        report_lead = read_from_db('report_lead')

        assert report_lead is None

    def test_track_click_and_lead__creates_report_lead(self, client, campaign, read_from_db):
        click_id = uuid4()

        client.post(
            '/api/v2/track/click',
            json={
                'clickId': str(click_id),
                'campaignId': campaign['id'],
                'source': 'fb',
            },
        )

        client.post(
            '/api/v2/track/lead',
            json={
                'clickId': str(click_id),
                'status': 'accept',
            },
        )

        sleep(0.3)

        report_lead = read_from_db('report_lead')

        assert report_lead == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'click_id': click_id,
            'campaign_id': campaign['id'],
            'click_created_at': mock.ANY,
            'status': None,
            'cost_value': None,
            'currency': None,
        }

    def test_track_click_and_postback__creates_report_lead(self, client, campaign, read_from_db):
        click_id = uuid4()

        client.post(
            '/api/v2/track/click',
            json={
                'clickId': str(click_id),
                'campaignId': campaign['id'],
                'source': 'fb',
            },
        )

        client.post(
            '/api/v2/track/postback',
            json={
                'clickId': str(click_id),
                'state': 'executed',
            },
        )

        sleep(0.3)

        report_lead = read_from_db('report_lead')

        assert report_lead == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'click_id': click_id,
            'campaign_id': campaign['id'],
            'click_created_at': mock.ANY,
            'status': 'accept',
            'cost_value': campaign['cost_value'],
            'currency': campaign['currency'],
        }

    def test_track_lead_with_existing_report_lead__does_not_update_report_lead(
        self, client, campaign, timestamp, write_to_db, read_from_db
    ):
        click_id = uuid4()
        click_created_at = timestamp - 20

        write_to_db(
            'track_click',
            {
                'click_id': click_id,
                'campaign_id': campaign['id'],
                'parameters': {'source': 'fb'},
                'created_at': click_created_at,
            },
        )
        existing_report_lead = write_to_db(
            'report_lead',
            {
                'click_id': click_id,
                'campaign_id': campaign['id'],
                'click_created_at': click_created_at,
                'status': 'reject',
                'cost_value': 5,
                'currency': 'eur',
            },
        )

        client.post(
            '/api/v2/track/lead',
            json={
                'clickId': str(click_id),
                'status': 'accept',
            },
        )

        sleep(0.3)

        report_lead = read_from_db('report_lead', filters={'click_id': click_id})

        assert report_lead == existing_report_lead

    def test_track_postback_with_existing_report_lead__updates_report_lead(
        self, client, campaign, timestamp, write_to_db, read_from_db
    ):
        click_id = uuid4()
        click_created_at = timestamp - 20

        write_to_db(
            'track_click',
            {
                'click_id': click_id,
                'campaign_id': campaign['id'],
                'parameters': {'source': 'fb'},
                'created_at': click_created_at,
            },
        )
        existing_report_lead = write_to_db(
            'report_lead',
            {
                'click_id': click_id,
                'campaign_id': campaign['id'],
                'click_created_at': click_created_at,
                'status': None,
                'cost_value': None,
                'currency': None,
            },
        )

        client.post(
            '/api/v2/track/postback',
            json={
                'clickId': str(click_id),
                'state': 'executed',
            },
        )

        sleep(0.3)

        report_lead = read_from_db('report_lead', filters={'click_id': click_id})

        assert report_lead == {
            'id': existing_report_lead['id'],
            'created_at': existing_report_lead['created_at'],
            'click_id': click_id,
            'campaign_id': campaign['id'],
            'click_created_at': click_created_at,
            'status': 'accept',  # status is updated
            'cost_value': campaign['cost_value'],  # cost value is updated
            'currency': campaign['currency'],  # currency is updated
        }

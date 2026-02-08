import json
from datetime import timedelta
from unittest import mock

import pytest


class TestExpensesReport:
    @pytest.fixture
    def expenses_distribution_parameter(self):
        return 'ad_name'

    def test_post_expenses_report(self, client, authorization, campaign, today, read_from_db):
        request_payload = {
            'campaignId': campaign['id'],
            'distributionParameter': 'ad_name',
            'dates': [
                {'date': today.isoformat(), 'distribution': {'ad1': 12.5, 'ad2': 7.5}},
            ],
        }

        assert request_payload['distributionParameter'] == campaign['expenses_distribution_parameter']

        response = client.post(
            '/api/v2/reports/expenses',
            headers={'Authorization': authorization},
            json=request_payload,
        )

        assert response.status_code == 200, response.text

        expense = read_from_db('expense')
        assert expense == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'campaign_id': campaign['id'],
            'date': today,
            'distribution': mock.ANY,
        }

        assert json.loads(expense['distribution']) == request_payload['dates'][0]['distribution']

    def test_post_expenses_report__expense_exists(
        self, client, authorization, campaign, today, read_from_db, write_to_db
    ):
        existing_expense = write_to_db(
            'expense',
            {'campaign_id': campaign['id'], 'date': today, 'distribution': json.dumps({'ad1': 1.5, 'ad2': 0.5})},
        )

        request_payload = {
            'campaignId': campaign['id'],
            'distributionParameter': 'ad_name',
            'dates': [
                {'date': today.isoformat(), 'distribution': {'ad1': 12.5, 'ad2': 7.5}},
            ],
        }

        assert existing_expense['distribution'] != request_payload['dates'][0]['distribution']

        response = client.post(
            '/api/v2/reports/expenses',
            headers={'Authorization': authorization},
            json=request_payload,
        )

        assert response.status_code == 200, response.text

        expense = read_from_db('expense')

        assert json.loads(expense['distribution']) != json.loads(existing_expense['distribution'])
        assert json.loads(expense['distribution']) == request_payload['dates'][0]['distribution']

    def test_get_expenses_report(self, client, authorization, campaign, campaign_payload, today, write_to_db):
        other_campaign = write_to_db('campaign', campaign_payload | {'name': 'Other Campaign'})

        date_end = today
        date_start = today - timedelta(days=1)
        older_date = today - timedelta(days=2)

        date_end_expenses = write_to_db(
            'expense',
            {'campaign_id': campaign['id'], 'date': date_end, 'distribution': {'ad1': 12.5}},
        )
        date_start_expenses = write_to_db(
            'expense',
            {'campaign_id': campaign['id'], 'date': date_start, 'distribution': {'ad1': 7.5}},
        )
        write_to_db(
            'expense',
            {'campaign_id': campaign['id'], 'date': older_date, 'distribution': {'ad1': 1.5}},
        )
        write_to_db(
            'expense',
            {'campaign_id': other_campaign['id'], 'date': date_end, 'distribution': {'ad1': 99.0}},
        )

        response = client.get(
            '/api/v2/reports/expenses',
            headers={'Authorization': authorization},
            query_string={
                'campaignId': campaign['id'],
                'periodStart': date_start.isoformat(),
                'periodEnd': date_end.isoformat(),
                'page': 1,
                'pageSize': 10,
                'sortBy': 'date',
                'sortOrder': 'asc',
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'date': date_start_expenses['date'].isoformat(),
                    'distribution': json.loads(date_start_expenses['distribution']),
                },
                {
                    'date': date_end_expenses['date'].isoformat(),
                    'distribution': json.loads(date_end_expenses['distribution']),
                },
            ],
            'pagination': {'page': 1, 'pageSize': 10, 'sortBy': 'date', 'sortOrder': 'asc', 'total': 2},
            'filters': {
                'campaignId': campaign['id'],
                'periodStart': date_start.isoformat(),
                'periodEnd': date_end.isoformat(),
            },
        }

    def test_get_expenses_report__no_expenses__clicks_exist(
        self, client, authorization, campaign, today, read_from_db, write_to_db
    ):
        write_to_db(
            'track_click',
            {
                'click_id': 'click-1',
                'campaign_id': campaign['id'],
                'parameters': {'utm_source': 'fb', 'ad_name': 'ad1'},
            },
        )

        response = client.get(
            '/api/v2/reports/expenses',
            headers={'Authorization': authorization},
            query_string={
                'campaignId': campaign['id'],
                'periodStart': today.isoformat(),
                'periodEnd': today.isoformat(),
                'page': 1,
                'pageSize': 10,
                'sortBy': 'date',
                'sortOrder': 'asc',
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [  # default template is returned
                {'date': today.isoformat(), 'distribution': {'ad_name': 0, 'utm_source': 0}}
            ],
            'pagination': {'page': 1, 'pageSize': 10, 'sortBy': 'date', 'sortOrder': 'asc', 'total': 0},
            'filters': {
                'campaignId': campaign['id'],
                'periodStart': today.isoformat(),
                'periodEnd': today.isoformat(),
            },
        }

        expenses = read_from_db('expense')
        assert expenses is None

    def test_get_expenses_report__no_expenses__no_clicks(self, client, authorization, campaign, today, read_from_db):
        response = client.get(
            '/api/v2/reports/expenses',
            headers={'Authorization': authorization},
            query_string={
                'campaignId': campaign['id'],
                'periodStart': today.isoformat(),
                'periodEnd': today.isoformat(),
                'page': 1,
                'pageSize': 10,
                'sortBy': 'date',
                'sortOrder': 'asc',
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [  # default template is returned, no default distribution
                {'date': today.isoformat(), 'distribution': {}}
            ],
            'pagination': {'page': 1, 'pageSize': 10, 'sortBy': 'date', 'sortOrder': 'asc', 'total': 0},
            'filters': {
                'campaignId': campaign['id'],
                'periodStart': today.isoformat(),
                'periodEnd': today.isoformat(),
            },
        }

        expenses = read_from_db('expense')
        assert expenses is None


class TestExpensesReportExpensesDistributionParameterNotSet:
    def test_post_expenses_report(self, client, authorization, campaign, today, read_from_db):
        assert campaign['expenses_distribution_parameter'] is None

        request_payload = {
            'campaignId': campaign['id'],
            'distributionParameter': 'ad_name',
            'dates': [
                {'date': today.isoformat(), 'distribution': {'ad1': 12.5, 'ad2': 7.5}},
            ],
        }

        response = client.post(
            '/api/v2/reports/expenses',
            headers={'Authorization': authorization},
            json=request_payload,
        )

        assert response.status_code == 200, response.text

        expense = read_from_db('expense')
        assert expense == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'campaign_id': campaign['id'],
            'date': today,
            'distribution': mock.ANY,
        }

        assert json.loads(expense['distribution']) == request_payload['dates'][0]['distribution']


class TestDistributionParameterIsChanged:
    @pytest.fixture
    def expenses_distribution_parameter(self):
        return 'adset_name'

    def test_post_expenses_report(self, client, authorization, campaign, today):
        request_payload = {
            'campaignId': campaign['id'],
            'distributionParameter': 'ad_name',
            'dates': [
                {'date': today.isoformat(), 'distribution': {'ad1': 12.5, 'ad2': 7.5}},
            ],
        }

        assert request_payload['distributionParameter'] != campaign['expenses_distribution_parameter']

        response = client.post(
            '/api/v2/reports/expenses',
            headers={'Authorization': authorization},
            json=request_payload,
        )

        assert response.status_code == 400, response.text
        assert response.json == {'message': 'Bad distribution parameter'}

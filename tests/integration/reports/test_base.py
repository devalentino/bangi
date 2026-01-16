from datetime import datetime, timedelta

import pytest


@pytest.fixture
def campaign_id(statistics):
    return next(iter(statistics.keys()))


def test_get_report(client, authorization, campaign_id, timestamp):
    start_timestamp = timestamp - 5 * 24 * 60 * 60
    end_timestamp = timestamp

    response = client.get(
        '/api/v2/reports/base',
        headers={'Authorization': authorization},
        query_string={
            'campaignId': campaign_id,
            'periodStart': start_timestamp,
            'periodEnd': end_timestamp,
        },
    )
    assert response.status_code == 200, response.text

    start_date = datetime.fromtimestamp(start_timestamp)
    end_date = datetime.fromtimestamp(end_timestamp)

    assert response.json == {
        'content': {
            'parameters': [
                'utm_source',
                'utm_content',
                'utm_campaign',
                'utm_medium',
                'ad_name',
                'utm_id',
                'redirect_url',
                'pixel',
                'utm_term',
                'adset_name',
                'fbclid',
            ],
            'report': {
                start_date.strftime('%Y-%m-%d'): {'clicks': 0},
                (start_date + timedelta(days=1)).strftime('%Y-%m-%d'): {'clicks': 0},
                (start_date + timedelta(days=2)).strftime('%Y-%m-%d'): {'clicks': 0},
                (start_date + timedelta(days=3)).strftime('%Y-%m-%d'): {'clicks': 2, 'leads': {'expect': 2}},
                (start_date + timedelta(days=4)).strftime('%Y-%m-%d'): {'clicks': 2, 'leads': {'expect': 2}},
                end_date.strftime('%Y-%m-%d'): {'clicks': 2, 'leads': {'expect': 1, 'reject': 1}},
            },
        }
    }


def test_get_report__group_by_parameter(client, authorization, campaign_id, timestamp):
    start_timestamp = timestamp - 4 * 24 * 60 * 60
    end_timestamp = timestamp

    response = client.get(
        '/api/v2/reports/base',
        headers={'Authorization': authorization},
        query_string={
            'campaignId': campaign_id,
            'periodStart': timestamp - 4 * 24 * 60 * 60,
            'periodEnd': timestamp,
            'groupParameters': 'ad_name,adset_name',
        },
    )

    assert response.status_code == 200, response.text

    start_date = datetime.fromtimestamp(start_timestamp)
    end_date = datetime.fromtimestamp(end_timestamp)

    assert response.json == {
        'content': {
            'parameters': [
                'utm_source',
                'utm_content',
                'utm_campaign',
                'utm_medium',
                'ad_name',
                'utm_id',
                'redirect_url',
                'pixel',
                'utm_term',
                'adset_name',
                'fbclid',
            ],
            'report': {
                start_date.strftime('%Y-%m-%d'): {'clicks': 0},
                (start_date + timedelta(days=1)).strftime('%Y-%m-%d'): {'clicks': 0},
                (start_date + timedelta(days=2)).strftime('%Y-%m-%d'): {
                    'clicks': 2,
                    'leads': {'expect': 1},
                    'parameters': {'ad_name': 'ad0_1', 'adset_name': 'adset9'},
                },
                (start_date + timedelta(days=3)).strftime('%Y-%m-%d'): {
                    'clicks': 2,
                    'leads': {'expect': 1},
                    'parameters': {'ad_name': 'ad0_1', 'adset_name': 'adset9'},
                },
                end_date.strftime('%Y-%m-%d'): {
                    'clicks': 2,
                    'leads': {'expect': 1, 'reject': 1},
                    'parameters': {'ad_name': 'ad0_0', 'adset_name': 'adset9'},
                },
            },
        }
    }


def test_get_report__no_statistics(client, authorization, timestamp):
    start_timestamp = timestamp - 4 * 24 * 60 * 60
    end_timestamp = timestamp

    response = client.get(
        '/api/v2/reports/base',
        headers={'Authorization': authorization},
        query_string={
            'campaignId': 100500,
            'periodStart': start_timestamp,
            'periodEnd': end_timestamp,
        },
    )
    assert response.status_code == 200, response.text

    start_date = datetime.fromtimestamp(start_timestamp)
    end_date = datetime.fromtimestamp(end_timestamp)

    assert response.json == {
        'content': {
            'parameters': [],
            'report': {
                start_date.strftime('%Y-%m-%d'): {'clicks': 0},
                (start_date + timedelta(days=1)).strftime('%Y-%m-%d'): {'clicks': 0},
                (start_date + timedelta(days=2)).strftime('%Y-%m-%d'): {'clicks': 0},
                (start_date + timedelta(days=3)).strftime('%Y-%m-%d'): {'clicks': 0},
                end_date.strftime('%Y-%m-%d'): {'clicks': 0},
            },
        }
    }

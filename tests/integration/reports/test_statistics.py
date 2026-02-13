from datetime import datetime, timedelta
from unittest import mock


def test_get_report(client, authorization, campaign, statistics_expenses, timestamp):
    start_timestamp = timestamp - 5 * 24 * 60 * 60
    end_timestamp = timestamp

    response = client.get(
        '/api/v2/reports/statistics',
        headers={'Authorization': authorization},
        query_string={
            'campaignId': campaign['id'],
            'periodStart': start_timestamp,
            'periodEnd': end_timestamp,
        },
    )
    assert response.status_code == 200, response.text

    start_date = datetime.fromtimestamp(start_timestamp).date()
    end_date = datetime.fromtimestamp(end_timestamp).date()
    cost_value = float(campaign['cost_value'])

    assert response.json == {
        'content': {
            'groupParameters': [],
            'report': {
                start_date.isoformat(): {},
                (start_date + timedelta(days=1)).isoformat(): {},
                (start_date + timedelta(days=2)).isoformat(): {},
                (start_date + timedelta(days=3)).isoformat(): {
                    'statuses': {
                        'accept': {'leads': 1, 'payouts': 1 * cost_value},
                        'trash': {'leads': 1, 'payouts': 0.0},
                    },
                    'clicks': 30,
                    'expenses': sum(statistics_expenses[start_date + timedelta(days=3)].values()),
                    'roi_accepted': (
                        (1 * cost_value - sum(statistics_expenses[start_date + timedelta(days=3)].values()))
                        / sum(statistics_expenses[start_date + timedelta(days=3)].values())
                        * 100
                    ),
                    'roi_expected': (
                        (1 * cost_value - sum(statistics_expenses[start_date + timedelta(days=3)].values()))
                        / sum(statistics_expenses[start_date + timedelta(days=3)].values())
                        * 100
                    ),
                },
                (start_date + timedelta(days=4)).isoformat(): {
                    'statuses': {
                        'accept': {'leads': 1, 'payouts': 1 * cost_value},
                        'expect': {'leads': 1, 'payouts': 1 * cost_value},
                        'reject': {'leads': 1, 'payouts': 0.0},
                    },
                    'clicks': 25,
                    'expenses': sum(statistics_expenses[start_date + timedelta(days=4)].values()),
                    'roi_accepted': (
                        (1 * cost_value - sum(statistics_expenses[start_date + timedelta(days=4)].values()))
                        / sum(statistics_expenses[start_date + timedelta(days=4)].values())
                        * 100
                    ),
                    'roi_expected': (
                        (
                            1 * cost_value
                            + 1 * cost_value
                            - sum(statistics_expenses[start_date + timedelta(days=4)].values())
                        )
                        / sum(statistics_expenses[start_date + timedelta(days=4)].values())
                        * 100
                    ),
                },
                end_date.isoformat(): {
                    'statuses': {'accept': {'leads': 1, 'payouts': 1 * cost_value}},
                    'clicks': 8,
                    'expenses': sum(statistics_expenses[end_date].values()),
                    'roi_accepted': (
                        (1 * cost_value - sum(statistics_expenses[end_date].values()))
                        / sum(statistics_expenses[end_date].values())
                        * 100
                    ),
                    'roi_expected': (
                        (1 * cost_value - sum(statistics_expenses[end_date].values()))
                        / sum(statistics_expenses[end_date].values())
                        * 100
                    ),
                },
            },
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
        }
    }


def test_get_report__group_by_parameter(client, authorization, statistics_expenses, campaign, timestamp):
    start_timestamp = timestamp - 4 * 24 * 60 * 60
    end_timestamp = timestamp

    response = client.get(
        '/api/v2/reports/statistics',
        headers={'Authorization': authorization},
        query_string={
            'campaignId': campaign['id'],
            'periodStart': timestamp - 4 * 24 * 60 * 60,
            'periodEnd': timestamp,
            'groupParameters': 'utm_source,ad_name',
        },
    )

    assert response.status_code == 200, response.text

    start_date = datetime.fromtimestamp(start_timestamp).date()
    end_date = datetime.fromtimestamp(end_timestamp).date()
    cost_value = float(campaign['cost_value'])

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
            'groupParameters': ['ad_name', 'utm_source'],
            'report': {
                start_date.isoformat(): {},
                (start_date + timedelta(days=1)).isoformat(): {},
                (start_date + timedelta(days=2)).isoformat(): {
                    'ad_1': {
                        'fb': {'statuses': {}, 'clicks': mock.ANY},
                        'inst': {'statuses': {}, 'clicks': mock.ANY},
                        'expenses': statistics_expenses[start_date + timedelta(days=2)]['ad_1'],
                        'roi_accepted': -100.0,
                        'roi_expected': -100.0,
                    },
                    'ad_2': {
                        'fb': {
                            'statuses': {
                                'accept': {'leads': 1, 'payouts': 1 * cost_value},
                                'trash': {'leads': 1, 'payouts': 0.0},
                            },
                            'clicks': mock.ANY,
                        },
                        'inst': {'statuses': {}, 'clicks': mock.ANY},
                        'expenses': statistics_expenses[start_date + timedelta(days=2)]['ad_2'],
                        'roi_accepted': (
                            (1 * cost_value - statistics_expenses[start_date + timedelta(days=2)]['ad_2'])
                            / statistics_expenses[start_date + timedelta(days=2)]['ad_2']
                            * 100
                        ),
                        'roi_expected': (
                            (1 * cost_value - statistics_expenses[start_date + timedelta(days=2)]['ad_2'])
                            / statistics_expenses[start_date + timedelta(days=2)]['ad_2']
                            * 100
                        ),
                    },
                },
                (start_date + timedelta(days=3)).isoformat(): {
                    'ad_1': {
                        'fb': {'statuses': {'reject': {'leads': 1, 'payouts': 0.0}}, 'clicks': mock.ANY},
                        'inst': {'statuses': {}, 'clicks': mock.ANY},
                        'expenses': statistics_expenses[start_date + timedelta(days=3)]['ad_1'],
                        'roi_accepted': -100.0,
                        'roi_expected': -100.0,
                    },
                    'ad_2': {
                        'fb': {
                            'statuses': {
                                'accept': {'leads': 1, 'payouts': 1 * cost_value},
                                'expect': {'leads': 1, 'payouts': 1 * cost_value},
                            },
                            'clicks': mock.ANY,
                        },
                        'inst': {'statuses': {}, 'clicks': mock.ANY},
                        'expenses': statistics_expenses[start_date + timedelta(days=3)]['ad_2'],
                        'roi_accepted': (
                            (1 * cost_value - statistics_expenses[start_date + timedelta(days=3)]['ad_2'])
                            / statistics_expenses[start_date + timedelta(days=3)]['ad_2']
                            * 100
                        ),
                        'roi_expected': (
                            (
                                1 * cost_value
                                + 1 * cost_value
                                - statistics_expenses[start_date + timedelta(days=3)]['ad_2']
                            )
                            / statistics_expenses[start_date + timedelta(days=3)]['ad_2']
                            * 100
                        ),
                    },
                },
                end_date.isoformat(): {
                    'ad_1': {
                        'fb': {'statuses': {'accept': {'leads': 1, 'payouts': 1 * cost_value}}, 'clicks': mock.ANY},
                        'inst': {'statuses': {}, 'clicks': mock.ANY},
                        'expenses': statistics_expenses[end_date]['ad_1'],
                        'roi_accepted': (
                            (1 * cost_value - statistics_expenses[end_date]['ad_1'])
                            / statistics_expenses[end_date]['ad_1']
                            * 100
                        ),
                        'roi_expected': (
                            (1 * cost_value - statistics_expenses[end_date]['ad_1'])
                            / statistics_expenses[end_date]['ad_1']
                            * 100
                        ),
                    }
                },
            },
        }
    }


def test_get_report__no_statistics(client, authorization, timestamp):
    start_timestamp = timestamp - 4 * 24 * 60 * 60
    end_timestamp = timestamp

    response = client.get(
        '/api/v2/reports/statistics',
        headers={'Authorization': authorization},
        query_string={
            'campaignId': 100500,
            'periodStart': start_timestamp,
            'periodEnd': end_timestamp,
        },
    )
    assert response.status_code == 404, response.text
    assert response.json == {'message': 'Campaign does not exist'}

import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from uuid import uuid4

import pytest


@pytest.fixture
def expenses_distribution_parameter():
    return 'ad_name'


@pytest.fixture
def click_parameters():
    return {
        'utm_source': 'fb',
        'utm_content': '000000000000000000',
        'utm_campaign': 'offer-1',
        'utm_medium': 'paid',
        'ad_name': 'ad1_1',
        'utm_id': '000000000000000000',
        'redirect_url': 'http://localhost/',
        'pixel': '0000000000000000',
        'utm_term': '000000000000000000',
        'adset_name': 'adset9',
        'fbclid': '0-0-0-0',
    }


@pytest.fixture
def postback_parameters():
    return {
        'sale_status': 'confirm',
        'lead_status': 'accept,expect',
        'check_sum': '0000000000000000000000000000000000000000',
        'payout': '0',
        'status': 'accept',
        'from': 'Terraleads.com',
        'return': 'OK',
        'offer_id': '0000',
        'rejected_status': 'reject,fail,trash,error',
        'tid': '00000000',
    }


@pytest.fixture
def statistics_clicks(write_to_db, campaign, click_parameters, postback_parameters, timestamp):
    clicks = []

    # ad_1 10 clicks, no leads 2 days ago
    for _ in range(10):
        click = write_to_db(
            'track_click',
            {
                'click_id': uuid4(),
                'campaign_id': campaign['id'],
                'parameters': click_parameters
                | {
                    'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                    'ad_name': 'ad_1',
                    'utm_source': random.choice(['fb', 'inst']),
                },
                'created_at': timestamp - timedelta(days=2).total_seconds(),
            },
        )
        clicks.append(click)

    # ad_1 15 clicks, 1 rejected lead 1 day ago
    for _ in range(14):
        click = write_to_db(
            'track_click',
            {
                'click_id': uuid4(),
                'campaign_id': campaign['id'],
                'parameters': click_parameters
                | {
                    'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                    'ad_name': 'ad_1',
                    'utm_source': random.choice(['fb', 'inst']),
                },
                'created_at': timestamp - timedelta(days=1).total_seconds(),
            },
        )
        clicks.append(click)

    click = write_to_db(
        'track_click',
        {
            'click_id': uuid4(),
            'campaign_id': campaign['id'],
            'parameters': click_parameters
            | {
                'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                'ad_name': 'ad_1',
                'utm_source': 'fb',
            },
            'created_at': timestamp - timedelta(days=1).total_seconds(),
        },
    )
    clicks.append(click)

    write_to_db(
        'track_postback',
        {
            'click_id': click['click_id'],
            'status': 'reject',
            'parameters': postback_parameters,
            'cost_value': campaign['cost_value'],
            'created_at': timestamp - timedelta(days=1).total_seconds(),
        },
    )

    # ad_1 8 clicks, 1 accepted lead today
    for _ in range(7):
        click = write_to_db(
            'track_click',
            {
                'click_id': uuid4(),
                'campaign_id': campaign['id'],
                'parameters': click_parameters
                | {
                    'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                    'ad_name': 'ad_1',
                    'utm_source': random.choice(['fb', 'inst']),
                },
                'created_at': timestamp,
            },
        )
        clicks.append(click)

    click = write_to_db(
        'track_click',
        {
            'click_id': uuid4(),
            'campaign_id': campaign['id'],
            'parameters': click_parameters
            | {
                'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                'ad_name': 'ad_1',
                'utm_source': 'fb',
            },
            'created_at': timestamp,
        },
    )
    clicks.append(click)

    write_to_db(
        'track_postback',
        {
            'click_id': click['click_id'],
            'status': 'accept',
            'parameters': postback_parameters,
            'cost_value': campaign['cost_value'],
            'created_at': timestamp,
        },
    )

    # ad_2 20 clicks, 1 accepted, 1 expected lead 2 days ago
    for _ in range(18):
        click = write_to_db(
            'track_click',
            {
                'click_id': uuid4(),
                'campaign_id': campaign['id'],
                'parameters': click_parameters
                | {
                    'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                    'ad_name': 'ad_2',
                    'utm_source': random.choice(['fb', 'inst']),
                },
                'created_at': timestamp - timedelta(days=2).total_seconds(),
            },
        )
        clicks.append(click)

    click_accepted = write_to_db(
        'track_click',
        {
            'click_id': uuid4(),
            'campaign_id': campaign['id'],
            'parameters': click_parameters
            | {
                'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                'ad_name': 'ad_2',
                'utm_source': 'fb',
            },
            'created_at': timestamp - timedelta(days=2).total_seconds(),
        },
    )
    clicks.append(click_accepted)

    click_trash = write_to_db(
        'track_click',
        {
            'click_id': uuid4(),
            'campaign_id': campaign['id'],
            'parameters': click_parameters
            | {
                'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                'ad_name': 'ad_2',
                'utm_source': 'fb',
            },
            'created_at': timestamp - timedelta(days=2).total_seconds(),
        },
    )
    clicks.append(click_trash)

    write_to_db(
        'track_postback',
        {
            'click_id': click_accepted['click_id'],
            'status': 'accept',
            'parameters': postback_parameters,
            'cost_value': campaign['cost_value'],
            'created_at': timestamp - timedelta(days=2).total_seconds(),
        },
    )

    write_to_db(
        'track_postback',
        {
            'click_id': click_trash['click_id'],
            'status': 'trash',
            'parameters': postback_parameters,
            'cost_value': campaign['cost_value'],
            'created_at': timestamp - timedelta(days=2).total_seconds(),
        },
    )

    # ad_2 10 clicks, 1 accepted, 1 expected lead 1 day ago
    for _ in range(8):
        click = write_to_db(
            'track_click',
            {
                'click_id': uuid4(),
                'campaign_id': campaign['id'],
                'parameters': click_parameters
                | {
                    'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                    'ad_name': 'ad_2',
                    'utm_source': random.choice(['fb', 'inst']),
                },
                'created_at': timestamp - timedelta(days=1).total_seconds(),
            },
        )
        clicks.append(click)

    click_accepted = write_to_db(
        'track_click',
        {
            'click_id': uuid4(),
            'campaign_id': campaign['id'],
            'parameters': click_parameters
            | {
                'redirect_url': 'http://localhost/?ci={campaign["id"]}',
                'ad_name': 'ad_2',
                'utm_source': 'fb',
            },
            'created_at': timestamp - timedelta(days=1).total_seconds(),
        },
    )
    clicks.append(click_accepted)

    click_expect = write_to_db(
        'track_click',
        {
            'click_id': uuid4(),
            'campaign_id': campaign['id'],
            'parameters': click_parameters
            | {'redirect_url': 'http://localhost/?ci={campaign["id"]}', 'ad_name': 'ad_2', 'utm_source': 'fb'},
            'created_at': timestamp - timedelta(days=1).total_seconds(),
        },
    )
    clicks.append(click_expect)

    write_to_db(
        'track_postback',
        {
            'click_id': click_accepted['click_id'],
            'status': 'accept',
            'parameters': postback_parameters,
            'cost_value': campaign['cost_value'],
            'created_at': timestamp - timedelta(days=1).total_seconds(),
        },
    )

    write_to_db(
        'track_postback',
        {
            'click_id': click_expect['click_id'],
            'status': 'expect',
            'parameters': postback_parameters,
            'cost_value': campaign['cost_value'],
            'created_at': timestamp - timedelta(days=1).total_seconds(),
        },
    )

    return clicks


@pytest.fixture
def statistics_expenses(campaign, statistics_clicks, timestamp, write_to_db):
    date2distribution = defaultdict(dict)
    for click in statistics_clicks:
        date = datetime.fromtimestamp(click['created_at']).date()
        click_parameters = json.loads(click['parameters'])
        ad_name = click_parameters['ad_name']

        date2distribution[date][ad_name] = round(random.uniform(5, 10), 2)

    for date, distribution in date2distribution.items():
        write_to_db(
            'expense',
            {'campaign_id': campaign['id'], 'date': date, 'distribution': distribution, 'created_at': timestamp},
        )

    return date2distribution

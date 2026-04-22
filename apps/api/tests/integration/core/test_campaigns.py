import json
from unittest import mock

import pytest

from tests.fixtures.utils import click_uuid


def test_create_campaign(client, authorization, campaign_payload, read_from_db):
    campaigns = read_from_db('campaign', fetchall=True)
    assert len(campaigns) == 0

    request_payload = {
        'name': campaign_payload['name'],
        'costModel': campaign_payload['cost_model'],
        'costValue': campaign_payload['cost_value'],
        'currency': campaign_payload['currency'],
        'statusMapper': campaign_payload['status_mapper'],
    }

    response = client.post('/api/v2/core/campaigns', headers={'Authorization': authorization}, json=request_payload)

    assert response.status_code == 201, response.text

    campaign = read_from_db('campaign')
    assert campaign == {
        'id': mock.ANY,
        'name': request_payload['name'],
        'cost_model': request_payload['costModel'],
        'cost_value': request_payload['costValue'],
        'currency': request_payload['currency'],
        'expenses_distribution_parameter': None,
        'status_mapper': mock.ANY,
        'created_at': mock.ANY,
    }

    assert json.loads(campaign['status_mapper']) == request_payload['statusMapper']


def test_campaigns_list(client, authorization, environment, campaign_payload, write_to_db):
    campaigns = []
    for ci in range(25):
        campaigns.append(
            write_to_db('campaign', {'name': f'Campaign {ci}', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'})
        )

    response = client.get('/api/v2/core/campaigns', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'costModel': campaign['cost_model'],
                'costValue': campaign['cost_value'],
                'currency': campaign['currency'],
                'expensesDistributionParameter': campaign['expenses_distribution_parameter'],
                'id': campaign['id'],
                'name': campaign['name'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{campaign["id"]}',
                'summary': {
                    'clickCount': 0,
                    'clickShare': 0.0,
                    'lastActivityAt': None,
                },
                'statusMapper': campaign['status_mapper'],
            }
            for campaign in campaigns[:20]
        ],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 25},
    }


def test_get_campaign(client, authorization, campaign, environment):
    response = client.get(f'/api/v2/core/campaigns/{campaign["id"]}', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {
        'id': campaign['id'],
        'name': campaign['name'],
        'costModel': campaign['cost_model'],
        'costValue': campaign['cost_value'],
        'currency': campaign['currency'],
        'expensesDistributionParameter': campaign['expenses_distribution_parameter'],
        'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{campaign["id"]}',
        'summary': {
            'clickCount': 0,
            'clickShare': 0.0,
            'lastActivityAt': None,
        },
        'statusMapper': json.loads(campaign['status_mapper']),
    }


def test_get_campaign__non_existent(client, authorization):
    response = client.get('/api/v2/core/campaigns/100500', headers={'Authorization': authorization})

    assert response.status_code == 404, response.text
    assert response.json == {'message': 'Campaign does not exist'}


@pytest.mark.parametrize(
    'request_key,db_key,request_value',
    [
        ('name', 'name', 'Campaign updated'),
        ('costModel', 'cost_model', 'cpc'),
        ('costValue', 'cost_value', 11.50),
        ('currency', 'currency', 'eur'),
    ],
)
def test_update_campaign(client, authorization, campaign, read_from_db, request_key, db_key, request_value):
    assert campaign[db_key] != request_value

    response = client.patch(
        f'/api/v2/core/campaigns/{campaign["id"]}',
        headers={'Authorization': authorization},
        json={request_key: request_value},
    )

    assert response.status_code == 200, response.text

    campaign = read_from_db('campaign')
    assert campaign[db_key] == request_value


def test_campaigns_list__returns_click_summary(
    client,
    authorization,
    environment,
    timestamp,
    write_to_db,
):
    first_campaign = write_to_db(
        'campaign', {'name': 'Campaign 1', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'}
    )
    second_campaign = write_to_db(
        'campaign',
        {'name': 'Campaign 2', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'},
    )
    idle_campaign = write_to_db(
        'campaign', {'name': 'Campaign 3', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'}
    )

    write_to_db(
        'track_click',
        {
            'campaign_id': first_campaign['id'],
            'click_id': click_uuid(1),
            'parameters': {},
            'created_at': timestamp - 20,
        },
    )
    write_to_db(
        'track_click',
        {
            'campaign_id': first_campaign['id'],
            'click_id': click_uuid(2),
            'parameters': {},
            'created_at': timestamp - 10,
        },
    )
    write_to_db(
        'track_click',
        {
            'campaign_id': second_campaign['id'],
            'click_id': click_uuid(3),
            'parameters': {},
            'created_at': timestamp - 5,
        },
    )

    response = client.get('/api/v2/core/campaigns', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'costModel': first_campaign['cost_model'],
                'costValue': first_campaign['cost_value'],
                'currency': first_campaign['currency'],
                'expensesDistributionParameter': first_campaign['expenses_distribution_parameter'],
                'id': first_campaign['id'],
                'name': first_campaign['name'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{first_campaign["id"]}',
                'summary': {
                    'clickCount': 2,
                    'clickShare': pytest.approx(2 / 3),
                    'lastActivityAt': timestamp - 10,
                },
                'statusMapper': first_campaign['status_mapper'],
            },
            {
                'costModel': second_campaign['cost_model'],
                'costValue': second_campaign['cost_value'],
                'currency': second_campaign['currency'],
                'expensesDistributionParameter': second_campaign['expenses_distribution_parameter'],
                'id': second_campaign['id'],
                'name': second_campaign['name'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{second_campaign["id"]}',
                'summary': {
                    'clickCount': 1,
                    'clickShare': pytest.approx(1 / 3),
                    'lastActivityAt': timestamp - 5,
                },
                'statusMapper': second_campaign['status_mapper'],
            },
            {
                'costModel': idle_campaign['cost_model'],
                'costValue': idle_campaign['cost_value'],
                'currency': idle_campaign['currency'],
                'expensesDistributionParameter': idle_campaign['expenses_distribution_parameter'],
                'id': idle_campaign['id'],
                'name': idle_campaign['name'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{idle_campaign["id"]}',
                'summary': {
                    'clickCount': 0,
                    'clickShare': 0.0,
                    'lastActivityAt': None,
                },
                'statusMapper': idle_campaign['status_mapper'],
            },
        ],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 3},
    }


def test_get_campaign__returns_click_summary(client, authorization, campaign, environment, timestamp, write_to_db):
    write_to_db(
        'track_click',
        {
            'campaign_id': campaign['id'],
            'click_id': click_uuid(1),
            'parameters': {},
            'created_at': timestamp - 100,
        },
    )
    write_to_db(
        'track_click',
        {
            'campaign_id': campaign['id'],
            'click_id': click_uuid(2),
            'parameters': {},
            'created_at': timestamp - 1,
        },
    )

    response = client.get(f'/api/v2/core/campaigns/{campaign["id"]}', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {
        'id': campaign['id'],
        'name': campaign['name'],
        'costModel': campaign['cost_model'],
        'costValue': campaign['cost_value'],
        'currency': campaign['currency'],
        'expensesDistributionParameter': campaign['expenses_distribution_parameter'],
        'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{campaign["id"]}',
        'summary': {
            'clickCount': 2,
            'clickShare': 1.0,
            'lastActivityAt': timestamp - 1,
        },
        'statusMapper': json.loads(campaign['status_mapper']),
    }


def test_campaigns_list__sorts_by_click_share(client, authorization, environment, timestamp, write_to_db):
    high_share_campaign = write_to_db(
        'campaign',
        {'name': 'High share', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'},
    )
    low_share_campaign = write_to_db(
        'campaign',
        {'name': 'Low share', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'},
    )
    no_clicks_campaign = write_to_db(
        'campaign',
        {'name': 'No clicks', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'},
    )

    for click_id, created_at in (
        (click_uuid(1), timestamp - 30),
        (click_uuid(2), timestamp - 20),
        (click_uuid(3), timestamp - 10),
    ):
        write_to_db(
            'track_click',
            {
                'campaign_id': high_share_campaign['id'],
                'click_id': click_id,
                'parameters': {},
                'created_at': created_at,
            },
        )

    write_to_db(
        'track_click',
        {
            'campaign_id': low_share_campaign['id'],
            'click_id': click_uuid(4),
            'parameters': {},
            'created_at': timestamp - 5,
        },
    )

    response = client.get(
        '/api/v2/core/campaigns?page=1&pageSize=20&sortBy=clickShare&sortOrder=desc',
        headers={'Authorization': authorization},
    )

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'costModel': high_share_campaign['cost_model'],
                'costValue': high_share_campaign['cost_value'],
                'currency': high_share_campaign['currency'],
                'expensesDistributionParameter': high_share_campaign['expenses_distribution_parameter'],
                'id': high_share_campaign['id'],
                'name': high_share_campaign['name'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{high_share_campaign["id"]}',
                'summary': {
                    'clickCount': 3,
                    'clickShare': 0.75,
                    'lastActivityAt': timestamp - 10,
                },
                'statusMapper': high_share_campaign['status_mapper'],
            },
            {
                'costModel': low_share_campaign['cost_model'],
                'costValue': low_share_campaign['cost_value'],
                'currency': low_share_campaign['currency'],
                'expensesDistributionParameter': low_share_campaign['expenses_distribution_parameter'],
                'id': low_share_campaign['id'],
                'name': low_share_campaign['name'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{low_share_campaign["id"]}',
                'summary': {
                    'clickCount': 1,
                    'clickShare': 0.25,
                    'lastActivityAt': timestamp - 5,
                },
                'statusMapper': low_share_campaign['status_mapper'],
            },
            {
                'costModel': no_clicks_campaign['cost_model'],
                'costValue': no_clicks_campaign['cost_value'],
                'currency': no_clicks_campaign['currency'],
                'expensesDistributionParameter': no_clicks_campaign['expenses_distribution_parameter'],
                'id': no_clicks_campaign['id'],
                'name': no_clicks_campaign['name'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{no_clicks_campaign["id"]}',
                'summary': {
                    'clickCount': 0,
                    'clickShare': 0.0,
                    'lastActivityAt': None,
                },
                'statusMapper': no_clicks_campaign['status_mapper'],
            },
        ],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'clickShare', 'sortOrder': 'desc', 'total': 3},
    }


def test_campaigns_list__sorts_by_last_activity_at(client, authorization, environment, timestamp, write_to_db):
    newest_campaign = write_to_db(
        'campaign',
        {'name': 'Newest activity', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'},
    )
    older_campaign = write_to_db(
        'campaign',
        {'name': 'Older activity', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'},
    )
    no_activity_campaign = write_to_db(
        'campaign',
        {'name': 'No activity', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'},
    )

    write_to_db(
        'track_click',
        {
            'campaign_id': newest_campaign['id'],
            'click_id': click_uuid(1),
            'parameters': {},
            'created_at': timestamp - 1,
        },
    )
    write_to_db(
        'track_click',
        {
            'campaign_id': older_campaign['id'],
            'click_id': click_uuid(2),
            'parameters': {},
            'created_at': timestamp - 100,
        },
    )

    response = client.get(
        '/api/v2/core/campaigns?page=1&pageSize=20&sortBy=lastActivityAt&sortOrder=desc',
        headers={'Authorization': authorization},
    )

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'costModel': newest_campaign['cost_model'],
                'costValue': newest_campaign['cost_value'],
                'currency': newest_campaign['currency'],
                'expensesDistributionParameter': newest_campaign['expenses_distribution_parameter'],
                'id': newest_campaign['id'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{newest_campaign["id"]}',
                'name': newest_campaign['name'],
                'statusMapper': newest_campaign['status_mapper'],
                'summary': {'clickCount': 1, 'clickShare': 0.5, 'lastActivityAt': timestamp - 1},
            },
            {
                'costModel': older_campaign['cost_model'],
                'costValue': older_campaign['cost_value'],
                'currency': older_campaign['currency'],
                'expensesDistributionParameter': older_campaign['expenses_distribution_parameter'],
                'id': older_campaign['id'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{older_campaign["id"]}',
                'name': older_campaign['name'],
                'statusMapper': older_campaign['status_mapper'],
                'summary': {'clickCount': 1, 'clickShare': 0.5, 'lastActivityAt': timestamp - 100},
            },
            {
                'costModel': no_activity_campaign['cost_model'],
                'costValue': no_activity_campaign['cost_value'],
                'currency': no_activity_campaign['currency'],
                'expensesDistributionParameter': no_activity_campaign['expenses_distribution_parameter'],
                'id': no_activity_campaign['id'],
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{no_activity_campaign["id"]}',
                'name': no_activity_campaign['name'],
                'statusMapper': no_activity_campaign['status_mapper'],
                'summary': {'clickCount': 0, 'clickShare': 0.0, 'lastActivityAt': None},
            },
        ],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'lastActivityAt', 'sortOrder': 'desc', 'total': 3},
    }

import json
from decimal import Decimal
from unittest import mock

import pytest


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
    for ci in range(25):
        write_to_db('campaign', {'name': f'Campaign {ci}', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'})

    response = client.get('/api/v2/core/campaigns', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'costModel': 'cpm',
                'costValue': '1.00',
                'currency': 'usd',
                'expensesDistributionParameter': None,
                'id': index + 1,
                'name': f'Campaign {index}',
                'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{index + 1}',
                'statusMapper': None,
            }
            for index in range(20)
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
        'costValue': str(campaign['cost_value'].quantize(Decimal('0.01'))),
        'currency': campaign['currency'],
        'expensesDistributionParameter': campaign['expenses_distribution_parameter'],
        'internalProcessUrl': f'{environment["INTERNAL_PROCESS_BASE_URL"]}/{campaign["id"]}',
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

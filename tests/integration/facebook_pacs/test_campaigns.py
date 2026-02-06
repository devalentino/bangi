import json
from unittest import mock


def test_get_campaigns(client, authorization, campaign, campaign_fa):
    response = client.get('/api/v2/facebook/pacs/campaigns', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text

    assert response.json == {
        'content': [
            {
                'id': campaign_fa['id'],
                'name': campaign['name'],
                'adCabinet': {
                    'businessPortfolio': mock.ANY,
                    'id': campaign_fa['ad_cabinet_id'],
                    'isBanned': mock.ANY,
                    'name': mock.ANY,
                },
                'businessPage': {'id': campaign_fa['business_page_id'], 'isBanned': mock.ANY, 'name': mock.ANY},
                'executor': {'id': campaign_fa['executor_id'], 'isBanned': mock.ANY, 'name': mock.ANY},
            }
        ],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 1},
    }


def test_create_campaign(client, authorization, ad_cabinet, executor, business_page, read_from_db):
    request_payload = {
        'name': 'pacs Campaign',
        'costModel': 'cpm',
        'costValue': 12,
        'currency': 'eur',
        'statusMapper': {'parameter': 'state', 'mapping': {'executed': 'approved'}},
        'executorId': executor['id'],
        'adCabinetId': ad_cabinet['id'],
        'businessPageId': business_page['id'],
    }

    response = client.post(
        '/api/v2/facebook/pacs/campaigns', headers={'Authorization': authorization}, json=request_payload
    )
    assert response.status_code == 201, response.text

    core_campaign = read_from_db('campaign')
    assert core_campaign == {
        'id': mock.ANY,
        'name': request_payload['name'],
        'cost_model': request_payload['costModel'],
        'cost_value': request_payload['costValue'],
        'currency': request_payload['currency'],
        'status_mapper': mock.ANY,
        'expenses_distribution_parameter': None,
        'created_at': mock.ANY,
    }
    assert json.loads(core_campaign['status_mapper']) == request_payload['statusMapper']

    pacs_campaign = read_from_db('facebook_pacs_ad_campaign')
    assert pacs_campaign == {
        'id': mock.ANY,
        'created_at': mock.ANY,
        'core_campaign_id': core_campaign['id'],
        'ad_cabinet_id': ad_cabinet['id'],
        'executor_id': executor['id'],
        'business_page_id': business_page['id'],
    }


def test_get_campaign(client, authorization, campaign, campaign_fa):
    response = client.get(
        f'/api/v2/facebook/pacs/campaigns/{campaign_fa["id"]}',
        headers={'Authorization': authorization},
    )
    assert response.status_code == 200, response.text

    assert response.json == {
        'id': campaign_fa['id'],
        'name': campaign['name'],
        'adCabinet': {
            'id': campaign_fa['ad_cabinet_id'],
            'businessPortfolio': mock.ANY,
            'isBanned': mock.ANY,
            'name': mock.ANY,
        },
        'businessPage': {'id': campaign_fa['business_page_id'], 'isBanned': mock.ANY, 'name': mock.ANY},
        'executor': {'id': campaign_fa['executor_id'], 'isBanned': mock.ANY, 'name': mock.ANY},
    }


def test_get_campaign__non_existent(client, authorization):
    response = client.get('/api/v2/facebook/pacs/campaigns/100500', headers={'Authorization': authorization})
    assert response.status_code == 404, response.text
    assert response.json == {'message': 'Campaign does not exist'}


def test_update_campaign(client, authorization, campaign_fa, ad_cabinet, executor, read_from_db, write_to_db):
    new_business_page = write_to_db(
        'facebook_pacs_business_page',
        {'name': 'Al-Idrisi', 'is_banned': False},
    )
    request_payload = {
        'name': 'Campaign Updated',
        'costModel': 'cpa',
        'costValue': 7,
        'currency': 'usd',
        'statusMapper': {'parameter': 'status', 'mapping': {'ok': 'approved'}},
        'executorId': executor['id'],
        'adCabinetId': ad_cabinet['id'],
        'businessPageId': new_business_page['id'],
    }

    response = client.patch(
        f'/api/v2/facebook/pacs/campaigns/{campaign_fa["id"]}',
        headers={'Authorization': authorization},
        json=request_payload,
    )
    assert response.status_code == 200, response.text

    core_campaign = read_from_db('campaign', filters={'id': campaign_fa['core_campaign_id']})
    assert core_campaign == {
        'id': campaign_fa['core_campaign_id'],
        'name': request_payload['name'],
        'cost_model': request_payload['costModel'],
        'cost_value': request_payload['costValue'],
        'currency': request_payload['currency'],
        'status_mapper': mock.ANY,
        'expenses_distribution_parameter': mock.ANY,
        'created_at': mock.ANY,
    }
    assert json.loads(core_campaign['status_mapper']) == request_payload['statusMapper']

    pacs_campaign = read_from_db('facebook_pacs_ad_campaign', filters={'id': campaign_fa['id']})
    assert pacs_campaign['business_page_id'] == new_business_page['id']

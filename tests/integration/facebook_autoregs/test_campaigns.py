from unittest import mock


def test_get_campaigns(client, authorization, campaign_fa):
    response = client.get('/api/v2/facebook/autoregs/campaigns', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text

    assert response.json == {
        'content': [
            {
                'id': campaign_fa['id'],
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
        'pagination': {'page': 1, 'page_size': 20, 'sort_by': 'id', 'sort_order': 'asc', 'total': 1},
    }


def test_create_campaign(client, authorization, ad_cabinet, executor, business_page, read_from_db):
    request_payload = {
        'name': 'Autoregs Campaign',
        'executorId': executor['id'],
        'adCabinetId': ad_cabinet['id'],
        'businessPageId': business_page['id'],
    }

    response = client.post(
        '/api/v2/facebook/autoregs/campaigns', headers={'Authorization': authorization}, json=request_payload
    )
    assert response.status_code == 201, response.text

    core_campaign = read_from_db('campaign')
    assert core_campaign == {
        'id': mock.ANY,
        'name': request_payload['name'],
        'cost_model': 'cpa',
        'cost_value': 0,
        'currency': 'usd',
        'created_at': mock.ANY,
    }

    autoregs_campaign = read_from_db('facebook_autoregs_ad_campaign')
    assert autoregs_campaign == {
        'id': mock.ANY,
        'created_at': mock.ANY,
        'core_campaign_id': core_campaign['id'],
        'ad_cabinet_id': ad_cabinet['id'],
        'executor_id': executor['id'],
        'business_page_id': business_page['id'],
    }


def test_get_campaign(client, authorization, campaign_fa):
    response = client.get(
        f'/api/v2/facebook/autoregs/campaigns/{campaign_fa["id"]}',
        headers={'Authorization': authorization},
    )
    assert response.status_code == 200, response.text

    assert response.json == {
        'id': campaign_fa['id'],
        'adCabinet': {
            'id': campaign_fa['ad_cabinet_id'],
            'businessPortfolio': mock.ANY,
            'isBanned': mock.ANY,
            'name': mock.ANY,
        },
        'businessPage': {'id': campaign_fa['business_page_id'], 'isBanned': mock.ANY, 'name': mock.ANY},
        'executor': {'id': campaign_fa['executor_id'], 'isBanned': mock.ANY, 'name': mock.ANY},
    }


def test_update_campaign(client, authorization, campaign_fa, ad_cabinet, executor, read_from_db, write_to_db):
    new_business_page = write_to_db(
        'facebook_autoregs_business_page',
        {'name': 'Al-Idrisi', 'is_banned': False},
    )
    request_payload = {
        'name': 'Campaign Updated',
        'executorId': executor['id'],
        'adCabinetId': ad_cabinet['id'],
        'businessPageId': new_business_page['id'],
    }

    response = client.patch(
        f'/api/v2/facebook/autoregs/campaigns/{campaign_fa["id"]}',
        headers={'Authorization': authorization},
        json=request_payload,
    )
    assert response.status_code == 200, response.text

    core_campaign = read_from_db('campaign', filters={'id': campaign_fa['core_campaign_id']})
    assert core_campaign['name'] == request_payload['name']

    autoregs_campaign = read_from_db('facebook_autoregs_ad_campaign', filters={'id': campaign_fa['id']})
    assert autoregs_campaign['business_page_id'] == new_business_page['id']

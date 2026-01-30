from unittest import mock


def test_get_business_pages(client, authorization, business_page):
    response = client.get('/api/v2/facebook/autoregs/business-pages', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [{'id': business_page['id'], 'name': business_page['name'], 'isBanned': business_page['is_banned']}],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 1},
    }


def test_create_business_page(client, authorization, business_page_name, read_from_db):
    request_payload = {'name': business_page_name, 'isBanned': False}

    response = client.post(
        '/api/v2/facebook/autoregs/business-pages', headers={'Authorization': authorization}, json=request_payload
    )
    assert response.status_code == 201, response.text
    assert response.json == {
        'id': mock.ANY,
        'name': request_payload['name'],
        'isBanned': request_payload['isBanned'],
    }

    db_payload = read_from_db('facebook_autoregs_business_page')
    assert db_payload == {
        'id': mock.ANY,
        'created_at': mock.ANY,
        'name': request_payload['name'],
        'is_banned': int(request_payload['isBanned']),
    }


def test_get_business_page(client, authorization, business_page):
    response = client.get(
        f'/api/v2/facebook/autoregs/business-pages/{business_page["id"]}',
        headers={'Authorization': authorization},
    )
    assert response.status_code == 200, response.text
    assert response.json == {
        'id': business_page['id'],
        'name': business_page['name'],
        'isBanned': business_page['is_banned'],
    }


def test_get_business_page__non_existent(client, authorization):
    response = client.get('/api/v2/facebook/autoregs/business-pages/100500', headers={'Authorization': authorization})
    assert response.status_code == 404, response.text
    assert response.json == {'message': 'Does not exist'}


def test_update_business_page(client, authorization, business_page, read_from_db):
    request_payload = {'name': 'Al-Maari', 'isBanned': True}
    assert business_page['name'] != request_payload['name']
    assert business_page['is_banned'] != request_payload['isBanned']

    response = client.patch(
        f'/api/v2/facebook/autoregs/business-pages/{business_page["id"]}',
        headers={'Authorization': authorization},
        json=request_payload,
    )
    assert response.status_code == 200, response.text
    assert response.json == {
        'id': mock.ANY,
        'isBanned': request_payload['isBanned'],
        'name': request_payload['name'],
    }

    db_payload = read_from_db('facebook_autoregs_business_page', filters={'id': business_page['id']})
    assert db_payload == {
        'id': mock.ANY,
        'created_at': mock.ANY,
        'name': request_payload['name'],
        'is_banned': request_payload['isBanned'],
    }

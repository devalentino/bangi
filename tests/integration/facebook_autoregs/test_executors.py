from unittest import mock


def test_get_executors(client, authorization, executor, read_from_db):
    response = client.get('/api/v2/facebook/autoregs/executors', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [{'id': executor['id'], 'name': executor['name'], 'isBanned': executor['is_banned']}],
        'pagination': {'page': 1, 'page_size': 20, 'sort_by': 'id', 'sort_order': 'asc', 'total': 1},
    }


def test_create_executor(client, authorization, executor_name, read_from_db):
    request_payload = {'name': executor_name, 'isBanned': False}

    response = client.post(
        '/api/v2/facebook/autoregs/executors', headers={'Authorization': authorization}, json=request_payload
    )
    assert response.status_code == 201, response.text
    assert response.json == {
        'id': mock.ANY,
        'name': request_payload['name'],
        'isBanned': request_payload['isBanned'],
    }

    db_payload = read_from_db('facebook_autoregs_executor')
    assert db_payload == {
        'id': mock.ANY,
        'created_at': mock.ANY,
        'name': request_payload['name'],
        'is_banned': int(request_payload['isBanned']),
    }


def test_get_executor(client, authorization, executor):
    response = client.get(
        f'/api/v2/facebook/autoregs/executors/{executor["id"]}',
        headers={'Authorization': authorization},
    )
    assert response.status_code == 200, response.text
    assert response.json == {'id': executor['id'], 'name': executor['name'], 'isBanned': executor['is_banned']}


def test_update_executor(client, authorization, executor, read_from_db):
    request_payload = {'name': 'Al-Malik al-Zahir Rukn al-Din Baybars al-Bunduqdari', 'isBanned': True}
    assert executor['name'] != request_payload['name']
    assert executor['is_banned'] != request_payload['isBanned']

    response = client.patch(
        f'/api/v2/facebook/autoregs/executors/{executor["id"]}',
        headers={'Authorization': authorization},
        json=request_payload,
    )
    assert response.status_code == 200, response.text
    assert response.json == {'id': mock.ANY, 'isBanned': request_payload['isBanned'], 'name': request_payload['name']}

    db_payload = read_from_db('facebook_autoregs_executor', filters={'id': executor['id']})
    assert db_payload == {
        'id': mock.ANY,
        'created_at': mock.ANY,
        'is_banned': request_payload['isBanned'],
        'name': request_payload['name'],
    }

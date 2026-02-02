from datetime import datetime, timezone
from unittest import mock


def test_get_executors(client, authorization, executor, read_from_db):
    response = client.get('/api/v2/facebook/pacs/executors', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [{'id': executor['id'], 'name': executor['name'], 'isBanned': executor['is_banned']}],
        'filters': {'partialName': None},
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 1},
    }


def test_get_executors__filters_by_partial_name(client, authorization, write_to_db):
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).timestamp()
    alpha = write_to_db('facebook_pacs_executor', {'name': 'Alpha One', 'is_banned': False, 'created_at': timestamp})
    write_to_db('facebook_pacs_executor', {'name': 'Beta Two', 'is_banned': False, 'created_at': timestamp})
    alphanumeric = write_to_db(
        'facebook_pacs_executor', {'name': 'Alphanumeric', 'is_banned': False, 'created_at': timestamp}
    )

    response = client.get(
        '/api/v2/facebook/pacs/executors',
        headers={'Authorization': authorization},
        query_string={'partialName': 'Alp'},
    )
    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {'id': alpha['id'], 'name': alpha['name'], 'isBanned': alpha['is_banned']},
            {'id': alphanumeric['id'], 'name': alphanumeric['name'], 'isBanned': alphanumeric['is_banned']},
        ],
        'filters': {'partialName': 'Alp'},
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 2},
    }


def test_create_executor(client, authorization, executor_name, read_from_db):
    request_payload = {'name': executor_name, 'isBanned': False}

    response = client.post(
        '/api/v2/facebook/pacs/executors', headers={'Authorization': authorization}, json=request_payload
    )
    assert response.status_code == 201, response.text
    assert response.json == {
        'id': mock.ANY,
        'name': request_payload['name'],
        'isBanned': request_payload['isBanned'],
    }

    db_payload = read_from_db('facebook_pacs_executor')
    assert db_payload == {
        'id': mock.ANY,
        'created_at': mock.ANY,
        'name': request_payload['name'],
        'is_banned': int(request_payload['isBanned']),
    }


def test_get_executor(client, authorization, executor):
    response = client.get(
        f'/api/v2/facebook/pacs/executors/{executor["id"]}',
        headers={'Authorization': authorization},
    )
    assert response.status_code == 200, response.text
    assert response.json == {'id': executor['id'], 'name': executor['name'], 'isBanned': executor['is_banned']}


def test_get_executor__non_existent(client, authorization):
    response = client.get('/api/v2/facebook/pacs/executors/100500', headers={'Authorization': authorization})

    assert response.status_code == 404, response.text
    assert response.json == {'message': 'Does not exist'}


def test_update_executor(client, authorization, executor, read_from_db):
    request_payload = {'name': 'Al-Malik al-Zahir Rukn al-Din Baybars al-Bunduqdari', 'isBanned': True}
    assert executor['name'] != request_payload['name']
    assert executor['is_banned'] != request_payload['isBanned']

    response = client.patch(
        f'/api/v2/facebook/pacs/executors/{executor["id"]}',
        headers={'Authorization': authorization},
        json=request_payload,
    )
    assert response.status_code == 200, response.text
    assert response.json == {'id': mock.ANY, 'isBanned': request_payload['isBanned'], 'name': request_payload['name']}

    db_payload = read_from_db('facebook_pacs_executor', filters={'id': executor['id']})
    assert db_payload == {
        'id': mock.ANY,
        'created_at': mock.ANY,
        'is_banned': request_payload['isBanned'],
        'name': request_payload['name'],
    }

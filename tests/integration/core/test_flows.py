import io
import pathlib
import zipfile
from unittest import mock


def _zip_bytes():
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as zip_file:
        zip_file.writestr('index.html', '<html></html>')
    archive.seek(0)
    return archive


def test_flows_list(client, authorization, campaign, flow_rule, write_to_db):
    for index in range(25):
        write_to_db(
            'flow',
            {
                'name': f'Flow {index}',
                'campaign_id': campaign['id'],
                'rule': flow_rule,
                'order_value': index + 1,
                'action_type': 'redirect',
                'redirect_url': f'https://example.com/{index}',
                'is_enabled': True,
                'is_deleted': False,
            },
        )

    response = client.get('/api/v2/core/flows', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'id': index + 1,
                'name': f'Flow {index}',
                'campaignId': campaign['id'],
                'campaignName': campaign['name'],
                'rule': 'country == "MD"',
                'orderValue': index + 1,
                'actionType': 'redirect',
                'redirectUrl': f'https://example.com/{index}',
                'landingPath': None,
                'isEnabled': True,
            }
            for index in range(20)
        ],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 25},
    }


def test_get_flow(client, authorization, campaign, flow):
    response = client.get(f'/api/v2/core/flows/{flow["id"]}', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {
        'id': flow['id'],
        'name': flow['name'],
        'campaignId': flow['campaign_id'],
        'campaignName': campaign['name'],
        'rule': 'country == "MD"',
        'orderValue': flow['order_value'],
        'actionType': flow['action_type'],
        'redirectUrl': flow['redirect_url'],
        'landingPath': None,
        'isEnabled': bool(flow['is_enabled']),
    }


def test_get_flow__non_existent(client, authorization):
    response = client.get('/api/v2/core/flows/100500', headers={'Authorization': authorization})

    assert response.status_code == 404, response.text
    assert response.json == {'message': 'Does not exist'}


def test_create_flow__redirect_action_success(client, authorization, campaign, flow_rule, read_from_db):
    request_payload = {
        'name': 'Black flow',
        'campaignId': campaign['id'],
        'rule': flow_rule,
        'orderValue': 1,
        'actionType': 'redirect',
        'redirectUrl': 'https://example.com',
        'isEnabled': True,
    }

    response = client.post(
        '/api/v2/core/flows',
        headers={'Authorization': authorization},
        data=request_payload,
        content_type='multipart/form-data',
    )

    assert response.status_code == 201, response.text

    flow = read_from_db('flow')
    assert flow == {
        'id': mock.ANY,
        'name': request_payload['name'],
        'created_at': mock.ANY,
        'rule': request_payload['rule'],
        'campaign_id': request_payload['campaignId'],
        'order_value': request_payload['orderValue'],
        'action_type': request_payload['actionType'],
        'redirect_url': request_payload['redirectUrl'],
        'is_enabled': request_payload['isEnabled'],
        'is_deleted': False,
    }


def test_create_flow__render_action_success(
    client, authorization, campaign, environment, flow_name, flow_rule, landing_pages_base_path, read_from_db
):
    request_payload = {
        'name': flow_name,
        'campaignId': campaign['id'],
        'orderValue': 2,
        'actionType': 'render',
        'landingArchive': (_zip_bytes(), 'landing.zip'),
        'rule': flow_rule,
    }

    response = client.post(
        '/api/v2/core/flows',
        headers={'Authorization': authorization},
        data=request_payload,
        content_type='multipart/form-data',
    )

    assert response.status_code == 201, response.text

    flow = read_from_db('flow')
    expected_landing_path = str(pathlib.Path(landing_pages_base_path) / str(flow['id']))
    assert flow == {
        'id': mock.ANY,
        'name': request_payload['name'],
        'created_at': mock.ANY,
        'rule': request_payload['rule'],
        'campaign_id': request_payload['campaignId'],
        'order_value': request_payload['orderValue'],
        'action_type': request_payload['actionType'],
        'redirect_url': None,
        'is_enabled': 1,
        'is_deleted': 0,
    }
    assert (pathlib.Path(expected_landing_path) / 'index.html').exists()


def test_create_flow__requires_redirect_url_for_redirect_action(client, authorization, campaign, flow_name, flow_rule):
    response = client.post(
        '/api/v2/core/flows',
        headers={'Authorization': authorization},
        data={
            'name': flow_name,
            'campaignId': campaign['id'],
            'orderValue': 1,
            'actionType': 'redirect',
            'rule': flow_rule,
        },
        content_type='multipart/form-data',
    )

    assert response.status_code == 422, response.text
    assert response.json == {
        'code': 422,
        'errors': {'form': {'redirectUrl': ['redirectUrl is required for redirect action.']}},
        'status': 'Unprocessable Entity',
    }


def test_create_flow__requires_landing_archive_for_render_action(client, authorization, campaign, flow_name, flow_rule):
    response = client.post(
        '/api/v2/core/flows',
        headers={'Authorization': authorization},
        data={
            'name': flow_name,
            'campaignId': campaign['id'],
            'rule': flow_rule,
            'orderValue': 1,
            'actionType': 'render',
            'redirectUrl': 'https://example.com',
        },
        content_type='multipart/form-data',
    )

    assert response.status_code == 422, response.text
    assert response.json == {
        'code': 422,
        'errors': {'form': {'landingArchive': ['landingArchive is required for render action.']}},
        'status': 'Unprocessable Entity',
    }


def test_create_flow__rejects_non_zip_landing_archive(client, authorization, campaign, flow_name, flow_rule):
    response = client.post(
        '/api/v2/core/flows',
        headers={'Authorization': authorization},
        data={
            'name': flow_name,
            'campaignId': campaign['id'],
            'rule': flow_rule,
            'orderValue': 1,
            'actionType': 'render',
            'landingArchive': (io.BytesIO(b'not-a-zip'), 'landing.txt'),
        },
        content_type='multipart/form-data',
    )

    assert response.status_code == 422, response.text
    assert response.json == {
        'code': 422,
        'errors': {'form': {'landingArchive': ['landingArchive must be a .zip file.']}},
        'status': 'Unprocessable Entity',
    }


def test_create_flow__rejects_rule_with_unsupported_term(client, authorization, campaign, flow_name):
    request_payload = {
        'name': flow_name,
        'campaignId': campaign['id'],
        'rule': 'countri == "US"',
        'orderValue': 1,
        'actionType': 'redirect',
        'redirectUrl': 'https://example.com',
        'isEnabled': True,
    }

    response = client.post(
        '/api/v2/core/flows',
        headers={'Authorization': authorization},
        data=request_payload,
        content_type='multipart/form-data',
    )

    assert response.status_code == 422, response.text
    assert response.json == {
        'code': 422,
        'errors': {'form': {'rule': ["unknown symbol: 'countri'"]}},
        'status': 'Unprocessable Entity',
    }


def test_update_flow__redirect_action_success(client, authorization, flow, read_from_db):
    request_payload = {
        'name': 'Black flow',
        'orderValue': 3,
        'rule': 'country == "RO"',
        'actionType': 'redirect',
        'redirectUrl': 'https://example.org',
        'isEnabled': False,
    }

    response = client.patch(
        f'/api/v2/core/flows/{flow["id"]}',
        headers={'Authorization': authorization},
        data=request_payload,
        content_type='multipart/form-data',
    )

    assert response.status_code == 200, response.text

    updated = read_from_db('flow')
    assert updated == {
        'id': flow['id'],
        'name': request_payload['name'],
        'created_at': mock.ANY,
        'campaign_id': flow['campaign_id'],
        'rule': request_payload['rule'],
        'order_value': request_payload['orderValue'],
        'action_type': request_payload['actionType'],
        'redirect_url': request_payload['redirectUrl'],
        'is_enabled': request_payload['isEnabled'],
        'is_deleted': False,
    }


def test_update_flow__render_action_success(
    client, authorization, flow, environment, read_from_db, flow_rule, landing_pages_base_path
):
    request_payload = {
        'name': 'Black flow',
        'rule': flow_rule,
        'orderValue': 4,
        'actionType': 'render',
        'isEnabled': True,
        'landingArchive': (_zip_bytes(), 'landing.zip'),
    }

    response = client.patch(
        f'/api/v2/core/flows/{flow["id"]}',
        headers={'Authorization': authorization},
        data=request_payload,
        content_type='multipart/form-data',
    )

    assert response.status_code == 200, response.text

    updated = read_from_db('flow')
    expected_landing_path = str(pathlib.Path(landing_pages_base_path) / str(updated['id']))
    assert updated == {
        'id': flow['id'],
        'name': request_payload['name'],
        'created_at': mock.ANY,
        'campaign_id': flow['campaign_id'],
        'rule': request_payload['rule'],
        'order_value': request_payload['orderValue'],
        'action_type': request_payload['actionType'],
        'redirect_url': None,
        'is_enabled': request_payload['isEnabled'],
        'is_deleted': False,
    }
    assert (pathlib.Path(expected_landing_path) / 'index.html').exists()


def test_update_flow__requires_redirect_url_for_redirect_action(client, authorization, flow):
    response = client.patch(
        f'/api/v2/core/flows/{flow["id"]}',
        headers={'Authorization': authorization},
        data={
            'actionType': 'redirect',
            'rule': flow['rule'],
        },
        content_type='multipart/form-data',
    )

    assert response.status_code == 422, response.text
    assert response.json == {
        'code': 422,
        'errors': {'form': {'redirectUrl': ['redirectUrl is required for redirect action.']}},
        'status': 'Unprocessable Entity',
    }


def test_update_flow__requires_landing_archive_for_render_action(client, authorization, flow):
    response = client.patch(
        f'/api/v2/core/flows/{flow["id"]}',
        headers={'Authorization': authorization},
        data={'actionType': 'render', 'rule': flow['rule']},
        content_type='multipart/form-data',
    )

    assert response.status_code == 422, response.text
    assert response.json == {
        'code': 422,
        'errors': {'form': {'landingArchive': ['landingArchive is required for render action.']}},
        'status': 'Unprocessable Entity',
    }


def test_update_flow__rejects_non_zip_landing_archive(client, authorization, flow):
    response = client.patch(
        f'/api/v2/core/flows/{flow["id"]}',
        headers={'Authorization': authorization},
        data={
            'rule': flow['rule'],
            'actionType': 'render',
            'landingArchive': (io.BytesIO(b'not-a-zip'), 'landing.txt'),
        },
        content_type='multipart/form-data',
    )

    assert response.status_code == 422, response.text
    assert response.json == {
        'code': 422,
        'errors': {'form': {'landingArchive': ['landingArchive must be a .zip file.']}},
        'status': 'Unprocessable Entity',
    }


def test_update_flow__rejects_unsupported_rule_term(client, authorization, flow):
    response = client.patch(
        f'/api/v2/core/flows/{flow["id"]}',
        headers={'Authorization': authorization},
        data={
            'rule': 'country ==',
            'actionType': 'redirect',
            'redirectUrl': 'https://example.org',
        },
        content_type='multipart/form-data',
    )

    assert response.status_code == 422, response.text
    assert response.json == {
        'code': 422,
        'errors': {'form': {'rule': ['syntax error at: EOF']}},
        'status': 'Unprocessable Entity',
    }

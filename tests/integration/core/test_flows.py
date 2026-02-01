import io
import pathlib
import zipfile
from unittest import mock

import pytest


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

    response = client.get(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows',
        headers={'Authorization': authorization},
    )

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


def test_flows_list__filters_by_campaign(client, authorization, campaign, campaign_payload, flow_rule, write_to_db):
    for index in range(3):
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

    other_campaign = write_to_db('campaign', campaign_payload | {'name': 'Other Campaign'})
    for index in range(2):
        write_to_db(
            'flow',
            {
                'name': f'Other Flow {index}',
                'campaign_id': other_campaign['id'],
                'rule': flow_rule,
                'order_value': index + 10,
                'action_type': 'redirect',
                'redirect_url': f'https://example.com/other/{index}',
                'is_enabled': True,
                'is_deleted': False,
            },
        )

    response = client.get(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows',
        headers={'Authorization': authorization},
    )

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'id': index + 1,
                'name': f'Flow {index}',
                'campaignId': campaign['id'],
                'campaignName': campaign['name'],
                'rule': flow_rule,
                'orderValue': index + 1,
                'actionType': 'redirect',
                'redirectUrl': f'https://example.com/{index}',
                'landingPath': None,
                'isEnabled': True,
            }
            for index in range(3)
        ],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 3},
    }


def test_flows_list__ordered_by_order_value_desc(client, authorization, campaign, flow_rule, write_to_db):
    first = write_to_db(
        'flow',
        {
            'name': 'Flow A',
            'campaign_id': campaign['id'],
            'rule': flow_rule,
            'order_value': 2,
            'action_type': 'redirect',
            'redirect_url': 'https://example.com/a',
            'is_enabled': True,
            'is_deleted': False,
        },
    )
    second = write_to_db(
        'flow',
        {
            'name': 'Flow B',
            'campaign_id': campaign['id'],
            'rule': flow_rule,
            'order_value': -1,
            'action_type': 'redirect',
            'redirect_url': 'https://example.com/b',
            'is_enabled': True,
            'is_deleted': False,
        },
    )
    third = write_to_db(
        'flow',
        {
            'name': 'Flow C',
            'campaign_id': campaign['id'],
            'rule': flow_rule,
            'order_value': 10,
            'action_type': 'redirect',
            'redirect_url': 'https://example.com/c',
            'is_enabled': True,
            'is_deleted': False,
        },
    )

    response = client.get(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows?page=1&pageSize=20&sortBy=orderValue&sortOrder=desc',
        headers={'Authorization': authorization},
    )

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'id': third['id'],
                'name': third['name'],
                'campaignId': third['campaign_id'],
                'campaignName': mock.ANY,
                'rule': third['rule'],
                'orderValue': third['order_value'],
                'actionType': third['action_type'],
                'redirectUrl': third['redirect_url'],
                'landingPath': mock.ANY,
                'isEnabled': third['is_enabled'],
            },
            {
                'id': first['id'],
                'name': first['name'],
                'campaignId': first['campaign_id'],
                'campaignName': mock.ANY,
                'rule': first['rule'],
                'orderValue': first['order_value'],
                'actionType': first['action_type'],
                'redirectUrl': first['redirect_url'],
                'landingPath': mock.ANY,
                'isEnabled': first['is_enabled'],
            },
            {
                'id': second['id'],
                'name': second['name'],
                'campaignId': second['campaign_id'],
                'campaignName': mock.ANY,
                'rule': second['rule'],
                'orderValue': second['order_value'],
                'actionType': second['action_type'],
                'redirectUrl': second['redirect_url'],
                'landingPath': mock.ANY,
                'isEnabled': second['is_enabled'],
            },
        ],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'orderValue', 'sortOrder': 'desc', 'total': 3},
    }


def test_flows_list__filter_out_deleted(client, authorization, campaign, flow_rule, write_to_db):
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
                'is_deleted': True,
            },
        )

    response = client.get(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows',
        headers={'Authorization': authorization},
    )

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [],
        'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 0},
    }


def test_get_flow(client, authorization, campaign, flow):
    response = client.get(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows/{flow["id"]}',
        headers={'Authorization': authorization},
    )

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


def test_get_flow__non_existent(client, authorization, campaign):
    response = client.get(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows/100500',
        headers={'Authorization': authorization},
    )

    assert response.status_code == 404, response.text
    assert response.json == {'message': 'Does not exist'}


def test_get_flow__non_related_campaign(client, authorization, flow, campaign_payload, write_to_db):
    other_campaign = write_to_db('campaign', campaign_payload | {'name': 'Another Campaign'})

    response = client.get(
        f'/api/v2/core/campaigns/{other_campaign["id"]}/flows/{flow["id"]}',
        headers={'Authorization': authorization},
    )

    assert response.status_code == 404, response.text
    assert response.json == {'message': 'Does not exist'}


def test_delete_flow(client, authorization, flow, campaign, flow_rule, write_to_db, read_from_db):
    response = client.delete(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows/{flow["id"]}',
        headers={'Authorization': authorization},
    )

    assert response.status_code == 204, response.text
    assert read_from_db('flow', filters={'id': flow['id']})['is_deleted'] == 1


@pytest.mark.parametrize('flow_rule', ['country == "MD"', ''])
def test_create_flow__redirect_action_success(client, authorization, campaign, flow_rule, read_from_db):
    request_payload = {
        'name': 'Black flow',
        'rule': flow_rule,
        'actionType': 'redirect',
        'redirectUrl': 'https://example.com',
        'isEnabled': True,
    }

    response = client.post(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows',
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
        'rule': mock.ANY,
        'campaign_id': campaign['id'],
        'order_value': -1,
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
        'actionType': 'render',
        'landingArchive': (_zip_bytes(), 'landing.zip'),
        'rule': flow_rule,
    }

    response = client.post(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows',
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
        'campaign_id': campaign['id'],
        'order_value': -1,
        'action_type': request_payload['actionType'],
        'redirect_url': None,
        'is_enabled': 1,
        'is_deleted': 0,
    }
    assert (pathlib.Path(expected_landing_path) / 'index.html').exists()


def test_create_flow__requires_redirect_url_for_redirect_action(client, authorization, campaign, flow_name, flow_rule):
    response = client.post(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows',
        headers={'Authorization': authorization},
        data={
            'name': flow_name,
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
        f'/api/v2/core/campaigns/{campaign["id"]}/flows',
        headers={'Authorization': authorization},
        data={
            'name': flow_name,
            'rule': flow_rule,
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
        f'/api/v2/core/campaigns/{campaign["id"]}/flows',
        headers={'Authorization': authorization},
        data={
            'name': flow_name,
            'rule': flow_rule,
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
        'rule': 'countri == "US"',
        'actionType': 'redirect',
        'redirectUrl': 'https://example.com',
        'isEnabled': True,
    }

    response = client.post(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows',
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
        'rule': 'country == "RO"',
        'actionType': 'redirect',
        'redirectUrl': 'https://example.org',
        'isEnabled': False,
    }

    response = client.patch(
        f'/api/v2/core/campaigns/{flow["campaign_id"]}/flows/{flow["id"]}',
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
        'order_value': flow['order_value'],
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
        'actionType': 'render',
        'isEnabled': True,
        'landingArchive': (_zip_bytes(), 'landing.zip'),
    }

    response = client.patch(
        f'/api/v2/core/campaigns/{flow["campaign_id"]}/flows/{flow["id"]}',
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
        'order_value': flow['order_value'],
        'action_type': request_payload['actionType'],
        'redirect_url': None,
        'is_enabled': request_payload['isEnabled'],
        'is_deleted': False,
    }
    assert (pathlib.Path(expected_landing_path) / 'index.html').exists()


def test_update_flow__requires_redirect_url_for_redirect_action(client, authorization, flow):
    response = client.patch(
        f'/api/v2/core/campaigns/{flow["campaign_id"]}/flows/{flow["id"]}',
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
        f'/api/v2/core/campaigns/{flow["campaign_id"]}/flows/{flow["id"]}',
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
        f'/api/v2/core/campaigns/{flow["campaign_id"]}/flows/{flow["id"]}',
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
        f'/api/v2/core/campaigns/{flow["campaign_id"]}/flows/{flow["id"]}',
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


def test_bulk_update_flow_order_values(
    client, authorization, campaign, campaign_payload, flow_rule, write_to_db, read_from_db
):
    flow_one = write_to_db(
        'flow',
        {
            'name': 'Flow 1',
            'campaign_id': campaign['id'],
            'rule': flow_rule,
            'order_value': 1,
            'action_type': 'redirect',
            'redirect_url': 'https://example.com/1',
            'is_enabled': True,
            'is_deleted': False,
        },
    )
    flow_two = write_to_db(
        'flow',
        {
            'name': 'Flow 2',
            'campaign_id': campaign['id'],
            'rule': flow_rule,
            'order_value': 2,
            'action_type': 'redirect',
            'redirect_url': 'https://example.com/2',
            'is_enabled': True,
            'is_deleted': False,
        },
    )
    flow_three = write_to_db(
        'flow',
        {
            'name': 'Flow 3',
            'campaign_id': campaign['id'],
            'rule': flow_rule,
            'order_value': 3,
            'action_type': 'redirect',
            'redirect_url': 'https://example.com/3',
            'is_enabled': True,
            'is_deleted': False,
        },
    )
    other_campaign = write_to_db('campaign', campaign_payload | {'name': 'Other Campaign'})
    other_flow = write_to_db(
        'flow',
        {
            'name': 'Other Flow',
            'campaign_id': other_campaign['id'],
            'rule': flow_rule,
            'order_value': 9,
            'action_type': 'redirect',
            'redirect_url': 'https://example.com/other',
            'is_enabled': True,
            'is_deleted': False,
        },
    )

    request_payload = {
        'order': {
            flow_one['id']: 10,
            flow_three['id']: 30,
            other_flow['id']: 999,
        },
    }

    response = client.patch(
        f'/api/v2/core/campaigns/{campaign["id"]}/flows/order',
        headers={'Authorization': authorization},
        json=request_payload,
    )

    assert response.status_code == 200, response.text

    assert (
        read_from_db('flow', filters={'id': flow_one['id']})['order_value'] == request_payload['order'][flow_one['id']]
    )
    assert read_from_db('flow', filters={'id': flow_two['id']})['order_value'] == -1  # since it was not in mapping
    assert (
        read_from_db('flow', filters={'id': flow_three['id']})['order_value']
        == request_payload['order'][flow_three['id']]
    )
    assert read_from_db('flow', filters={'id': other_flow['id']})['order_value'] == other_flow['order_value']


class TestGetDeletedFlow:
    @pytest.fixture
    def flow_is_deleted(self):
        return True

    def test_get_flow(self, client, authorization, campaign, flow):
        response = client.get(
            f'/api/v2/core/campaigns/{campaign["id"]}/flows/{flow["id"]}',
            headers={'Authorization': authorization},
        )

        assert response.status_code == 404, response.text
        assert response.json == {'message': 'Does not exist'}

import hashlib
import json
from unittest import mock
from uuid import UUID, uuid4

import numpy as np
import pytest

from tests.fixtures.utils import click_uuid

INSTRUCTIONS = (
    "Whenever discussing or analyzing a campaign with the user, start the conversation by calling the "
    "summary tool — it is the only tool that surfaces active alerts, so calling it first ensures the "
    "user is warned about risks before any analysis begins.\n\n"
    "Before every response you give the user during a campaign-analysis conversation, call "
    "store_analysis_note with a complete summary of the conversation so far — reasoning, data points "
    "considered, and hypotheses discussed, not just the final conclusion. On the first call in a "
    "conversation, omit session_handle. On every subsequent call, pass back exactly the session_handle "
    "value received from the previous call.\n\n"
    "When searching past notes with search_notes, write a query describing what you're looking for — "
    "a campaign name, a geo, a topic — rather than assuming it only works for the current campaign."
)


class TestDiscover:
    def test_discover_returns_supported_versions_capabilities_and_instructions(self, client, mcp_headers):
        response = client.post(
            '/mcp', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}}
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {
                'protocolVersions': ['2025-11-25', '2026-07-28'],
                'capabilities': {'tools': {'listChanged': False}},
                'instructions': INSTRUCTIONS,
            },
        }

    def test_discover_route_accepts_trailing_slash(self, client, mcp_headers):
        response = client.post(
            '/mcp/', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}}
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {
                'protocolVersions': ['2025-11-25', '2026-07-28'],
                'capabilities': {'tools': {'listChanged': False}},
                'instructions': INSTRUCTIONS,
            },
        }


class TestInitialize:
    def test_initialize_responds_with_the_handshake_protocol_version(self, client, bearer_authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization},
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'initialize',
                'params': {'protocolVersion': '2025-11-25', 'capabilities': {}, 'clientInfo': {'name': 'test-client'}},
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {
                'protocolVersion': '2025-11-25',
                'capabilities': {'tools': {'listChanged': False}},
                'serverInfo': {'name': 'bangi', 'version': '1.0.0'},
                'instructions': INSTRUCTIONS,
            },
        }

    def test_initialize_ignores_an_unsupported_requested_version(self, client, bearer_authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization},
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'initialize',
                'params': {'protocolVersion': '1999-01-01', 'capabilities': {}, 'clientInfo': {'name': 'test-client'}},
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {
                'protocolVersion': '2025-11-25',
                'capabilities': {'tools': {'listChanged': False}},
                'serverInfo': {'name': 'bangi', 'version': '1.0.0'},
                'instructions': INSTRUCTIONS,
            },
        }

    def test_initialize_ignores_a_missing_protocol_version(self, client, bearer_authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {
                'protocolVersion': '2025-11-25',
                'capabilities': {'tools': {'listChanged': False}},
                'serverInfo': {'name': 'bangi', 'version': '1.0.0'},
                'instructions': INSTRUCTIONS,
            },
        }

    def test_initialize_does_not_require_the_protocol_version_header(self, client, bearer_authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-11-25'}},
        )

        assert response.status_code == 200, response.text


class TestNotificationsInitialized:
    def test_notifications_initialized_returns_an_empty_202_without_the_protocol_version_header(
        self, client, bearer_authorization
    ):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization},
            json={'jsonrpc': '2.0', 'method': 'notifications/initialized'},
        )

        assert response.status_code == 202, response.text
        assert response.data == b''


class TestToolsList:
    def test_tools_list_returns_the_five_tool_definitions_with_schemas(self, client, mcp_headers):
        response = client.post(
            '/mcp', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}}
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {
                'tools': [
                    {
                        'name': 'summary',
                        'description': (
                            'Campaigns with activity in the last 7 days, together with the current alert feed. '
                            'The entry point for any campaign-analysis conversation.'
                        ),
                        'inputSchema': {
                            'type': 'object',
                            'additionalProperties': False,
                            'properties': {
                                'page': {'title': 'page', 'type': 'integer'},
                                'pageSize': {'title': 'pageSize', 'type': 'integer'},
                            },
                        },
                    },
                    {
                        'name': 'campaign_list',
                        'description': 'Paginated list of all campaigns on this Bangi instance, active or dormant.',
                        'inputSchema': {
                            'type': 'object',
                            'additionalProperties': False,
                            'properties': {
                                'page': {'title': 'page', 'type': 'integer', 'default': 1},
                                'pageSize': {'title': 'pageSize', 'type': 'integer', 'default': 20},
                                'sortBy': {
                                    'title': 'sortBy',
                                    'type': 'string',
                                    'default': 'id',
                                    'enum': ['id', 'createdAt', 'clickCount', 'clickShare', 'lastActivityAt'],
                                },
                                'sortOrder': {
                                    'title': 'sortOrder',
                                    'type': 'string',
                                    'default': 'asc',
                                    'enum': ['asc', 'desc'],
                                },
                            },
                        },
                    },
                    {
                        'name': 'campaign_statistics',
                        'description': (
                            'The statistics report for one campaign over a period, matching the Bangi dashboard.'
                        ),
                        'inputSchema': {
                            'type': 'object',
                            'additionalProperties': False,
                            'properties': {
                                'campaignId': {'title': 'campaignId', 'type': 'integer'},
                                'periodStart': {'title': 'periodStart', 'type': 'string', 'format': 'date'},
                                'periodEnd': {'title': 'periodEnd', 'type': 'string', 'format': 'date'},
                                'groupParameters': {
                                    'title': 'groupParameters',
                                    'type': 'array',
                                    'default': [],
                                    'items': {'title': 'groupParameters', 'type': 'string'},
                                },
                            },
                            'required': ['campaignId', 'periodStart'],
                        },
                    },
                    {
                        'name': 'store_analysis_note',
                        'description': 'Persist a running summary of the current analysis conversation.',
                        'inputSchema': {
                            'type': 'object',
                            'additionalProperties': False,
                            'properties': {
                                'summary': {'title': 'summary', 'type': 'string'},
                                'sessionId': {'title': 'sessionId', 'type': ['string', 'null']},
                            },
                            'required': ['summary'],
                        },
                    },
                    {
                        'name': 'search_notes',
                        'description': (
                            'Search stored conversation summaries by semantic similarity to a free-text query.'
                        ),
                        'inputSchema': {
                            'type': 'object',
                            'additionalProperties': False,
                            'properties': {'query': {'title': 'query', 'type': 'string'}},
                            'required': ['query'],
                        },
                    },
                ]
            },
        }


class TestToolsCall:
    def test_unrecognized_tool_name_returns_invalid_params(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'delete_campaign'}

        response = client.post(
            '/mcp',
            headers=headers,
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'delete_campaign'}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32602, 'message': 'InvalidParams'}}


class TestUnknownMethod:
    def test_unrecognized_method_returns_method_not_found(self, client, mcp_headers):
        response = client.post(
            '/mcp', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/ping', 'params': {}}
        )

        assert response.status_code == 404, response.text
        assert response.json == {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32601, 'message': 'MethodNotFound'}}


class TestJsonRpcEnvelope:
    def test_success_response_wraps_the_result_and_echoes_a_numeric_request_id(self, client, mcp_headers):
        response = client.post(
            '/mcp', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 7, 'method': 'server/discover', 'params': {}}
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 7,
            'result': {
                'protocolVersions': ['2025-11-25', '2026-07-28'],
                'capabilities': {'tools': {'listChanged': False}},
                'instructions': INSTRUCTIONS,
            },
        }

    def test_success_response_echoes_a_string_request_id(self, client, mcp_headers):
        response = client.post(
            '/mcp',
            headers=mcp_headers,
            json={'jsonrpc': '2.0', 'id': 'req-abc', 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 'req-abc',
            'result': {
                'protocolVersions': ['2025-11-25', '2026-07-28'],
                'capabilities': {'tools': {'listChanged': False}},
                'instructions': INSTRUCTIONS,
            },
        }

    def test_error_response_wraps_the_error_and_echoes_the_request_id(self, client, mcp_headers):
        response = client.post(
            '/mcp', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 'req-err', 'method': 'server/ping', 'params': {}}
        )

        assert response.status_code == 404, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 'req-err',
            'error': {'code': -32601, 'message': 'MethodNotFound'},
        }

    def test_error_response_before_dispatch_still_carries_the_request_id(self, client, bearer_authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization},
            json={'jsonrpc': '2.0', 'id': 99, 'method': 'tools/list', 'params': {}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'jsonrpc': '2.0', 'id': 99, 'error': {'code': -32020, 'message': 'HeaderMismatch'}}


class TestHeaderValidation:
    def test_missing_protocol_version_header_is_rejected_before_tool_logic_runs(self, client, bearer_authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32020, 'message': 'HeaderMismatch'}}

    def test_unsupported_protocol_version_header_is_rejected(self, client, bearer_authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization, 'MCP-Protocol-Version': '1999-01-01'},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32020, 'message': 'HeaderMismatch'}}

    def test_tools_call_with_mismatched_mcp_method_header_is_rejected_before_dispatch(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/list', 'Mcp-Name': 'summary'}

        response = client.post(
            '/mcp',
            headers=headers,
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'summary'}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32020, 'message': 'HeaderMismatch'}}

    def test_tools_call_with_mismatched_mcp_name_header_is_rejected_before_dispatch(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'campaign_list'}

        response = client.post(
            '/mcp',
            headers=headers,
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'summary'}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'jsonrpc': '2.0', 'id': 1, 'error': {'code': -32020, 'message': 'HeaderMismatch'}}


class TestAuthentication:
    def test_mcp_route_requires_bearer_token(self, client):
        response = client.post(
            '/mcp',
            headers={'MCP-Protocol-Version': '2026-07-28'},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 401, response.text

    def test_basic_auth_credentials_do_not_authenticate_the_mcp_route(self, client, authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': authorization, 'MCP-Protocol-Version': '2026-07-28'},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 401, response.text

    def test_valid_token_via_query_parameter_authenticates_when_no_header_is_present(self, client, pat_token):
        response = client.post(
            '/mcp',
            query_string={'token': pat_token},
            headers={'MCP-Protocol-Version': '2026-07-28'},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 200, response.text

    def test_invalid_token_via_query_parameter_is_rejected(self, client):
        response = client.post(
            '/mcp',
            query_string={'token': 'not-a-real-token'},
            headers={'MCP-Protocol-Version': '2026-07-28'},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 401, response.text

    def test_revoked_token_via_query_parameter_is_rejected(self, client, write_to_db):
        revoked_token = 'revoked-query-param-token-0123456789'
        write_to_db(
            'pat_token',
            {
                'name': 'Revoked token',
                'token_hash': hashlib.sha256(revoked_token.encode()).hexdigest(),
                'token_prefix': revoked_token[:8],
                'token_suffix': revoked_token[-4:],
                'revoked_at': 1778587200,
            },
        )

        response = client.post(
            '/mcp',
            query_string={'token': revoked_token},
            headers={'MCP-Protocol-Version': '2026-07-28'},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 401, response.text

    def test_header_takes_precedence_over_query_parameter_when_both_are_present(
        self, client, bearer_authorization, write_to_db
    ):
        revoked_token = 'revoked-query-param-token-0123456789'
        write_to_db(
            'pat_token',
            {
                'name': 'Revoked token',
                'token_hash': hashlib.sha256(revoked_token.encode()).hexdigest(),
                'token_prefix': revoked_token[:8],
                'token_suffix': revoked_token[-4:],
                'revoked_at': 1778587200,
            },
        )

        response = client.post(
            '/mcp',
            query_string={'token': revoked_token},
            headers={'Authorization': bearer_authorization, 'MCP-Protocol-Version': '2026-07-28'},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 200, response.text


class TestRequestBodyValidation:
    def test_request_missing_method_is_rejected_with_422(self, client, mcp_headers):
        response = client.post('/mcp', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 1, 'params': {}})

        assert response.status_code == 422, response.text
        assert response.json == {
            'code': 422,
            'errors': {'json': {'method': ['Missing data for required field.']}},
            'status': 'Unprocessable Entity',
        }


class TestSummaryTool:
    def test_summary_returns_paginated_campaigns_with_activity_in_the_last_7_days(
        self, client, mcp_headers, timestamp, write_to_db, alert_free_campaign
    ):
        recent_campaign = alert_free_campaign('Recent campaign')
        dormant_campaign = alert_free_campaign('Dormant campaign')

        write_to_db(
            'track_click',
            {
                'campaign_id': recent_campaign['id'],
                'click_id': click_uuid(1),
                'parameters': {},
                'created_at': timestamp - 60,
            },
        )
        write_to_db(
            'track_click',
            {
                'campaign_id': dormant_campaign['id'],
                'click_id': click_uuid(2),
                'parameters': {},
                'created_at': timestamp - 8 * 24 * 60 * 60,
            },
        )

        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'summary'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {'name': 'summary', 'arguments': {'page': 1, 'pageSize': 20}},
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': [
                {
                    'id': recent_campaign['id'],
                    'name': recent_campaign['name'],
                    'summary': {'clickCount': 1, 'clickShare': 0.5, 'lastActivityAt': timestamp - 60},
                },
            ],
            'pagination': {'page': 1, 'pageSize': 20, 'total': 1},
            'alerts': [],
        }

    def test_summary_paginates_recent_campaigns_ordered_by_last_activity(
        self, client, mcp_headers, timestamp, write_to_db, alert_free_campaign
    ):
        campaigns = [alert_free_campaign(f'Campaign {i}') for i in range(3)]
        for index, campaign in enumerate(campaigns):
            write_to_db(
                'track_click',
                {
                    'campaign_id': campaign['id'],
                    'click_id': click_uuid(index + 1),
                    'parameters': {},
                    'created_at': timestamp - index,
                },
            )

        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'summary'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {'name': 'summary', 'arguments': {'page': 2, 'pageSize': 2}},
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': [
                {
                    'id': campaigns[2]['id'],
                    'name': campaigns[2]['name'],
                    'summary': {'clickCount': 1, 'clickShare': 1 / 3, 'lastActivityAt': timestamp - 2},
                },
            ],
            'pagination': {'page': 2, 'pageSize': 2, 'total': 3},
            'alerts': [],
        }

    def test_summary_bundles_the_current_alert_feed_on_every_call(self, client, mcp_headers, authorization, campaign):
        alerts_response = client.get('/api/v2/alerts', headers={'Authorization': authorization})
        assert alerts_response.json['content'] != []  # campaign has missing default flow

        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'summary'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'summary', 'arguments': {}}},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': [],
            'pagination': {'page': 1, 'pageSize': 20, 'total': 0},
            'alerts': alerts_response.json['content'],
        }

    def test_summary_returns_a_schema_valid_result_when_there_are_no_campaigns(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'summary'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'summary', 'arguments': {}}},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': [],
            'pagination': {'page': 1, 'pageSize': 20, 'total': 0},
            'alerts': [],
        }


class TestCampaignListTool:
    def test_campaign_list_matches_the_campaigns_endpoint_and_includes_dormant_campaigns(
        self, client, mcp_headers, timestamp, write_to_db
    ):
        active_campaign = write_to_db(
            'campaign', {'name': 'Active campaign', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'}
        )
        dormant_campaign = write_to_db(
            'campaign', {'name': 'Dormant campaign', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'}
        )
        write_to_db(
            'track_click',
            {
                'campaign_id': active_campaign['id'],
                'click_id': click_uuid(1),
                'parameters': {},
                'created_at': timestamp - 8 * 24 * 60 * 60,
            },
        )

        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'campaign_list'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {'name': 'campaign_list', 'arguments': {}},
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': [
                {
                    'id': active_campaign['id'],
                    'name': active_campaign['name'],
                    'summary': {'clickCount': 1, 'clickShare': 1.0, 'lastActivityAt': timestamp - 8 * 24 * 60 * 60},
                },
                {
                    'id': dormant_campaign['id'],
                    'name': dormant_campaign['name'],
                    'summary': {'clickCount': 0, 'clickShare': 0.0, 'lastActivityAt': None},
                },
            ],
            'pagination': {'page': 1, 'pageSize': 20, 'total': 2},
        }

    def test_campaign_list_honors_pagination_and_sort_parameters(self, client, mcp_headers, write_to_db):
        campaigns = [
            write_to_db('campaign', {'name': f'Campaign {i}', 'cost_model': 'cpm', 'cost_value': 1, 'currency': 'usd'})
            for i in range(3)
        ]

        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'campaign_list'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {
                    'name': 'campaign_list',
                    'arguments': {'page': 2, 'pageSize': 1, 'sortBy': 'id', 'sortOrder': 'desc'},
                },
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': [
                {
                    'id': campaigns[1]['id'],
                    'name': campaigns[1]['name'],
                    'summary': {'clickCount': 0, 'clickShare': 0.0, 'lastActivityAt': None},
                },
            ],
            'pagination': {'page': 2, 'pageSize': 1, 'total': 3},
        }

    def test_campaign_list_returns_a_schema_valid_result_when_there_are_no_campaigns(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'campaign_list'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {'name': 'campaign_list', 'arguments': {}},
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert response.json['result']['content'][0]['text'] != ''
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': [],
            'pagination': {'page': 1, 'pageSize': 20, 'total': 0},
        }


class TestCampaignStatisticsTool:
    def test_campaign_statistics_reports_the_days_click_count(
        self, client, mcp_headers, campaign, today, timestamp, write_to_db
    ):
        for i in range(3):
            write_to_db(
                'track_click',
                {
                    'campaign_id': campaign['id'],
                    'click_id': click_uuid(i + 1),
                    'parameters': {'ad_name': 'Ad 1'},
                    'created_at': timestamp - i,
                },
            )

        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'campaign_statistics'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {
                    'name': 'campaign_statistics',
                    'arguments': {
                        'campaignId': campaign['id'],
                        'periodStart': today.isoformat(),
                        'periodEnd': today.isoformat(),
                    },
                },
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': {
                'report': {
                    today.isoformat(): {
                        'expenses': 0,
                        'roi_accepted': 0,
                        'roi_expected': 0,
                        'profit_accepted': 0,
                        'profit_expected': 0,
                        'statuses': {
                            'accept': {'leads': 0, 'payouts': 0},
                            'expect': {'leads': 0, 'payouts': 0},
                            'reject': {'leads': 0, 'payouts': 0},
                            'trash': {'leads': 0, 'payouts': 0},
                        },
                        'clicks': 3,
                    },
                },
                'total': {
                    'clicks': 3,
                    'statuses': {
                        'accept': {'leads': 0, 'payouts': 0},
                        'expect': {'leads': 0, 'payouts': 0},
                        'reject': {'leads': 0, 'payouts': 0},
                        'trash': {'leads': 0, 'payouts': 0},
                    },
                    'expenses': 0,
                    'profit_accepted': 0,
                    'profit_expected': 0,
                    'roi_accepted': 0,
                    'roi_expected': 0,
                },
                'parameters': ['ad_name'],
                'groupParameters': [],
            }
        }

    def test_campaign_statistics_groups_clicks_by_the_requested_parameter(
        self, client, mcp_headers, campaign, today, timestamp, write_to_db
    ):
        for click_id, ad_name in ((1, 'Ad 1'), (2, 'Ad 1'), (3, 'Ad 2')):
            write_to_db(
                'track_click',
                {
                    'campaign_id': campaign['id'],
                    'click_id': click_uuid(click_id),
                    'parameters': {'ad_name': ad_name},
                    'created_at': timestamp,
                },
            )

        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'campaign_statistics'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {
                    'name': 'campaign_statistics',
                    'arguments': {
                        'campaignId': campaign['id'],
                        'periodStart': today.isoformat(),
                        'periodEnd': today.isoformat(),
                        'groupParameters': ['ad_name'],
                    },
                },
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': {
                'report': {
                    today.isoformat(): {
                        'expenses': 0,
                        'roi_accepted': 0,
                        'roi_expected': 0,
                        'profit_accepted': 0,
                        'profit_expected': 0,
                        'Ad 1': {
                            'statuses': {
                                'accept': {'leads': 0, 'payouts': 0},
                                'expect': {'leads': 0, 'payouts': 0},
                                'reject': {'leads': 0, 'payouts': 0},
                                'trash': {'leads': 0, 'payouts': 0},
                            },
                            'clicks': 2,
                        },
                        'Ad 2': {
                            'statuses': {
                                'accept': {'leads': 0, 'payouts': 0},
                                'expect': {'leads': 0, 'payouts': 0},
                                'reject': {'leads': 0, 'payouts': 0},
                                'trash': {'leads': 0, 'payouts': 0},
                            },
                            'clicks': 1,
                        },
                    },
                },
                'total': {
                    'clicks': 3,
                    'statuses': {
                        'accept': {'leads': 0, 'payouts': 0},
                        'expect': {'leads': 0, 'payouts': 0},
                        'reject': {'leads': 0, 'payouts': 0},
                        'trash': {'leads': 0, 'payouts': 0},
                    },
                    'expenses': 0,
                    'profit_accepted': 0,
                    'profit_expected': 0,
                    'roi_accepted': 0,
                    'roi_expected': 0,
                },
                'parameters': ['ad_name'],
                'groupParameters': ['ad_name'],
            }
        }


class TestStoreAnalysisNoteTool:
    @pytest.fixture
    def existing_note(self, mysql, timestamp):
        session_id = uuid4()
        embedding_hex = np.arange(1, 65, dtype=np.float32).tobytes().hex()

        # write_to_db can't be used here: its underlying pymysql connection sends bytes params
        # without the `_binary` marker, which VECTOR columns reject outright (unlike BINARY(16)).
        # UNHEX() on a hex string sidesteps that; raw connection since write_to_db builds queries
        # from plain %(key)s placeholders and can't wrap one column in UNHEX(...).
        with mysql.cursor() as cursor:
            cursor.execute(
                'INSERT INTO agent_note (session_id, note_text, embedding, updated_at) '
                'VALUES (UNHEX(%s), %s, UNHEX(%s), %s)',
                (session_id.hex, 'First draft of the analysis.', embedding_hex, timestamp),
            )
        mysql.commit()

        return session_id

    def test_first_call_without_a_session_id_mints_a_new_one_and_persists_the_note(
        self, client, mcp_headers, read_from_db
    ):
        summary = 'Campaign X is scaling well on Facebook.'
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'store_analysis_note'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {
                    'name': 'store_analysis_note',
                    'arguments': {'summary': summary},
                },
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        payload = json.loads(response.json['result']['content'][0]['text'])
        assert payload == {'content': {'sessionId': mock.ANY}}

        stored = read_from_db('agent_note', filters={'session_id': UUID(payload['content']['sessionId'])})
        assert stored == {
            'embedding': mock.ANY,
            'note_text': 'Campaign X is scaling well on Facebook.',
            'session_id': mock.ANY,
            'updated_at': mock.ANY,
        }

    def test_calling_again_with_the_same_session_id_replaces_rather_than_duplicates_the_note(
        self, client, mcp_headers, read_from_db, existing_note
    ):
        session_id = existing_note
        updated_summary = 'Updated analysis with more detail.'
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'store_analysis_note'}
        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {
                    'name': 'store_analysis_note',
                    'arguments': {'summary': updated_summary, 'sessionId': str(session_id)},
                },
            },
        )

        assert response.status_code == 200, response.text
        assert json.loads(response.json['result']['content'][0]['text']) == {'content': {'sessionId': str(session_id)}}
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }

        rows = read_from_db('agent_note', filters={'session_id': session_id}, fetchall=True)
        assert rows == [
            {
                'embedding': mock.ANY,
                'note_text': updated_summary,
                'session_id': session_id,
                'updated_at': mock.ANY,
            }
        ]


class TestSearchNotesTool:
    @pytest.fixture
    def stored_note(self, mysql, timestamp):
        note_summary = 'Facebook campaign targeting Germany is underperforming this week.'
        embedding_hex = np.arange(1, 65, dtype=np.float32).tobytes().hex()

        # write_to_db can't be used here: its underlying pymysql connection sends bytes params
        # without the `_binary` marker, which VECTOR columns reject outright (unlike BINARY(16)).
        # UNHEX() on a hex string sidesteps that; raw connection since write_to_db builds queries
        # from plain %(key)s placeholders and can't wrap one column in UNHEX(...).
        with mysql.cursor() as cursor:
            cursor.execute(
                'INSERT INTO agent_note (session_id, note_text, embedding, updated_at) '
                'VALUES (UNHEX(%s), %s, UNHEX(%s), %s)',
                (uuid4().hex, note_summary, embedding_hex, timestamp),
            )
        mysql.commit()

        return note_summary

    def test_search_notes_returns_the_stored_note_matching_the_query(self, client, mcp_headers, stored_note, timestamp):
        search_headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'search_notes'}
        response = client.post(
            '/mcp',
            headers=search_headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {'name': 'search_notes', 'arguments': {'query': 'Facebook Germany campaign performance'}},
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {
            'content': [{'noteText': stored_note, 'updatedAt': timestamp}]
        }

    def test_search_notes_returns_no_content_when_no_notes_are_stored(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'search_notes'}

        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {'name': 'search_notes', 'arguments': {'query': 'anything'}},
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'jsonrpc': '2.0',
            'id': 1,
            'result': {'content': [{'type': 'text', 'text': mock.ANY}]},
        }
        assert json.loads(response.json['result']['content'][0]['text']) == {'content': []}

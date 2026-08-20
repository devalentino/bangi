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
            'protocolVersions': ['2026-07-28'],
            'capabilities': {'tools': {'listChanged': False}},
            'instructions': INSTRUCTIONS,
        }


class TestToolsList:
    def test_tools_list_returns_the_five_tool_definitions_with_schemas(self, client, mcp_headers):
        response = client.post(
            '/mcp', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}}
        )

        assert response.status_code == 200, response.text
        assert response.json == {
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
        }


class TestToolsCall:
    def test_recognized_tool_name_dispatches_with_its_arguments(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'search_notes'}

        response = client.post(
            '/mcp',
            headers=headers,
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {'name': 'search_notes', 'arguments': {'query': 'facebook geo US'}},
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {'name': 'search_notes', 'arguments': {'query': 'facebook geo US'}}

    def test_unrecognized_tool_name_returns_invalid_params(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'delete_campaign'}

        response = client.post(
            '/mcp',
            headers=headers,
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'delete_campaign'}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'error': {'code': -32602, 'message': 'InvalidParams'}}


class TestUnknownMethod:
    def test_unrecognized_method_returns_method_not_found(self, client, mcp_headers):
        response = client.post(
            '/mcp', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/ping', 'params': {}}
        )

        assert response.status_code == 404, response.text
        assert response.json == {'error': {'code': -32601, 'message': 'MethodNotFound'}}


class TestHeaderValidation:
    def test_missing_protocol_version_header_is_rejected_before_tool_logic_runs(self, client, bearer_authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'error': {'code': -32020, 'message': 'HeaderMismatch'}}

    def test_unsupported_protocol_version_header_is_rejected(self, client, bearer_authorization):
        response = client.post(
            '/mcp',
            headers={'Authorization': bearer_authorization, 'MCP-Protocol-Version': '1999-01-01'},
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover', 'params': {}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'error': {'code': -32020, 'message': 'HeaderMismatch'}}

    def test_tools_call_with_mismatched_mcp_method_header_is_rejected_before_dispatch(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/list', 'Mcp-Name': 'summary'}

        response = client.post(
            '/mcp',
            headers=headers,
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'summary'}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'error': {'code': -32020, 'message': 'HeaderMismatch'}}

    def test_tools_call_with_mismatched_mcp_name_header_is_rejected_before_dispatch(self, client, mcp_headers):
        headers = mcp_headers | {'Mcp-Method': 'tools/call', 'Mcp-Name': 'campaign_list'}

        response = client.post(
            '/mcp',
            headers=headers,
            json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'summary'}},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'error': {'code': -32020, 'message': 'HeaderMismatch'}}


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


class TestRequestBodyValidation:
    def test_request_missing_method_is_rejected_with_422(self, client, mcp_headers):
        response = client.post('/mcp', headers=mcp_headers, json={'jsonrpc': '2.0', 'id': 1, 'params': {}})

        assert response.status_code == 422, response.text
        assert response.json == {
            'code': 422,
            'errors': {'json': {'method': ['Missing data for required field.']}},
            'status': 'Unprocessable Entity',
        }

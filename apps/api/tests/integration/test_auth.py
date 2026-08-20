import hashlib
from unittest import mock

import pytest


def test_authentication(client, authorization):
    response = client.post('/api/v2/auth/authenticate', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text


class TestCreatePatToken:
    def test_create_token_requires_name(self, client, authorization):
        response = client.post('/api/v2/auth/tokens', headers={'Authorization': authorization}, json={})

        assert response.status_code == 422, response.text
        assert response.json == {
            'code': 422,
            'errors': {'json': {'name': ['Missing data for required field.']}},
            'status': 'Unprocessable Entity',
        }

    def test_create_token_rejects_blank_name(self, client, authorization):
        response = client.post('/api/v2/auth/tokens', headers={'Authorization': authorization}, json={'name': '   '})

        assert response.status_code == 422, response.text
        assert response.json == {
            'code': 422,
            'errors': {'json': {'name': ['name cannot be blank.']}},
            'status': 'Unprocessable Entity',
        }

    def test_create_token_rejects_name_over_max_length(self, client, authorization):
        response = client.post(
            '/api/v2/auth/tokens', headers={'Authorization': authorization}, json={'name': 'x' * 101}
        )

        assert response.status_code == 422, response.text
        assert response.json == {
            'code': 422,
            'errors': {'json': {'name': ['Longer than maximum length 100.']}},
            'status': 'Unprocessable Entity',
        }

    def test_create_token_returns_raw_value_once_and_persists_only_its_hash(self, client, authorization, read_from_db):
        response = client.post(
            '/api/v2/auth/tokens',
            headers={'Authorization': authorization},
            json={'name': 'Claude Desktop — laptop'},
        )

        assert response.status_code == 201, response.text
        assert response.json == {'token': mock.ANY, 'name': 'Claude Desktop — laptop'}

        token = response.json['token']
        row = read_from_db('pat_token')
        assert row == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'name': 'Claude Desktop — laptop',
            'token_hash': hashlib.sha256(token.encode()).hexdigest(),
            'token_prefix': token[:8],
            'token_suffix': token[-4:],
            'revoked_at': None,
        }


class TestListPatTokens:
    def test_list_tokens_returns_active_and_revoked_tokens(self, client, authorization, write_to_db):
        active = write_to_db(
            'pat_token',
            {
                'name': 'Claude Code — VPS',
                'token_hash': 'a' * 64,
                'token_prefix': 'AbCd1234',
                'token_suffix': 'WxYz',
                'revoked_at': None,
            },
        )
        revoked = write_to_db(
            'pat_token',
            {
                'name': 'Leaked token',
                'token_hash': 'b' * 64,
                'token_prefix': 'EfGh5678',
                'token_suffix': 'UvWx',
                'revoked_at': 1778587200,
            },
        )

        response = client.get('/api/v2/auth/tokens', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'id': active['id'],
                    'name': 'Claude Code — VPS',
                    'createdAt': mock.ANY,
                    'revokedAt': None,
                    'tokenPrefix': 'AbCd1234',
                    'tokenSuffix': 'WxYz',
                },
                {
                    'id': revoked['id'],
                    'name': 'Leaked token',
                    'createdAt': mock.ANY,
                    'revokedAt': 1778587200,
                    'tokenPrefix': 'EfGh5678',
                    'tokenSuffix': 'UvWx',
                },
            ]
        }
        assert 'tokenHash' not in response.json['content'][0]

    def test_list_tokens_returns_empty_content_when_none_exist(self, client, authorization):
        response = client.get('/api/v2/auth/tokens', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {'content': []}


class TestRevokePatToken:
    def test_revoke_token_sets_revoked_at_and_keeps_the_row(self, client, authorization, write_to_db, read_from_db):
        token = write_to_db(
            'pat_token',
            {
                'name': 'Claude Code — VPS',
                'token_hash': 'a' * 64,
                'token_prefix': 'AbCd1234',
                'token_suffix': 'WxYz',
                'revoked_at': None,
            },
        )

        response = client.delete(f'/api/v2/auth/tokens/{token["id"]}', headers={'Authorization': authorization})

        assert response.status_code == 204, response.text

        row = read_from_db('pat_token', filters={'id': token['id']})
        assert row['revoked_at'] is not None

    def test_revoke_unknown_token_is_a_no_op(self, client, authorization):
        response = client.delete('/api/v2/auth/tokens/100500', headers={'Authorization': authorization})

        assert response.status_code == 204, response.text

    @pytest.mark.parametrize('method', ['post', 'get', 'delete'])
    def test_token_routes_require_basic_auth(self, client, method):
        response = getattr(client, method)('/api/v2/auth/tokens' if method != 'delete' else '/api/v2/auth/tokens/1')

        assert response.status_code == 401, response.text

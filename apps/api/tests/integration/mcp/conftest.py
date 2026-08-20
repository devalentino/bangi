import pytest


@pytest.fixture
def mcp_headers(pat_token):
    return {'Authorization': f'Bearer {pat_token}', 'MCP-Protocol-Version': '2026-07-28'}

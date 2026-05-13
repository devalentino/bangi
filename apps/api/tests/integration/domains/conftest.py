from unittest import mock

import pytest


@pytest.fixture
def dns_resolver_mock(public_ip):
    with mock.patch('src.domains.services.dns.resolver') as resolver:
        resolver.resolve.return_value = [mock.Mock(address=public_ip)]
        yield resolver

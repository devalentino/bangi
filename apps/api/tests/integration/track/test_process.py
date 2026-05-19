import json
import time
from unittest import mock
from uuid import UUID, uuid4

import httpx
import pytest

from tests.fixtures.utils import decode_flow_timestamp_cookie, encode_flow_timestamp_cookie

MOBILE_SAFARI_USER_AGENT = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
)


@pytest.fixture
def ip2location_mock(environment):
    assert environment['IP2LOCATION_DB_PATH'] is not None, 'IP2LOCATION_DB_PATH is not set'

    from src.container import container
    from src.core.services import IpLocator

    ip2location_mock = mock.MagicMock()
    ip2location_mock.get_country_short.return_value = 'MD'

    ip_locator = container.get(IpLocator)
    with mock.patch.object(ip_locator, 'ip2location', ip2location_mock):
        yield ip2location_mock


class TestTrackRedirect:
    def test_track_redirect__evaluates_current_flow_first_when_cookie_flow_is_valid(
        self, client, campaign, domain, write_to_db, ip2location_mock
    ):
        write_to_db(
            'flow',
            {
                'name': 'Higher priority fallback',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/higher',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        current_flow = write_to_db(
            'flow',
            {
                'name': 'Current repeatable flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/current',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': False,
            },
        )
        cookie_flow_id = write_to_db(
            'domain_cookie',
            {'domain_id': domain['id'], 'name': 'flow_id', 'opaque_name': 'sticky_flow'},
        )
        client.set_cookie(cookie_flow_id['opaque_name'], str(current_flow['id']))

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == current_flow['redirect_url']

    def test_track_redirect__skips_show_once_current_flow_after_visit(
        self, client, campaign, domain, write_to_db, ip2location_mock
    ):
        write_to_db(
            'flow',
            {
                'name': 'Already passed show-once flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 30,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/previous',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': True,
            },
        )
        current_flow = write_to_db(
            'flow',
            {
                'name': 'Current show-once flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/current',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': True,
            },
        )
        next_flow = write_to_db(
            'flow',
            {
                'name': 'Next repeatable flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/next',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': False,
            },
        )
        cookie_flow_id = write_to_db(
            'domain_cookie',
            {'domain_id': domain['id'], 'name': 'flow_id', 'opaque_name': 'sticky_flow'},
        )
        client.set_cookie(cookie_flow_id['opaque_name'], str(current_flow['id']))

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == next_flow['redirect_url']

    def test_track_redirect__keeps_show_once_current_flow_with_valid_timestamp_cookie(
        self, client, campaign, domain, write_to_db, ip2location_mock
    ):
        current_flow = write_to_db(
            'flow',
            {
                'name': 'Current show-once flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/current',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': True,
            },
        )
        write_to_db(
            'flow',
            {
                'name': 'Next repeatable flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/next',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': False,
            },
        )

        first_response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})
        assert first_response.status_code == 302, first_response.text
        assert first_response.headers['Location'] == current_flow['redirect_url']

        second_response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert second_response.status_code == 302, second_response.text
        assert second_response.headers['Location'] == current_flow['redirect_url']

    def test_track_redirect__skips_show_once_current_flow_after_timestamp_expires(
        self, client, campaign, domain, write_to_db, ip2location_mock
    ):
        current_flow = write_to_db(
            'flow',
            {
                'name': 'Current show-once flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/current',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': True,
            },
        )
        next_flow = write_to_db(
            'flow',
            {
                'name': 'Next repeatable flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/next',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': False,
            },
        )

        flow_id_cookie_row = write_to_db(
            'domain_cookie',
            {'domain_id': domain['id'], 'name': 'flow_id', 'opaque_name': 'sticky_flow'},
        )
        timestamp_cookie_row = write_to_db(
            'domain_cookie',
            {
                'domain_id': domain['id'],
                'name': 'flow_timestamp',
                'opaque_name': 'sticky_time',
                'encryption_key': 'a' * 64,
            },
        )
        expired_timestamp = int(time.time()) - 60 * 60 * 24
        client.set_cookie(flow_id_cookie_row['opaque_name'], str(current_flow['id']))
        client.set_cookie(
            timestamp_cookie_row['opaque_name'],
            encode_flow_timestamp_cookie(expired_timestamp, timestamp_cookie_row['encryption_key']),
        )

        second_response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert second_response.status_code == 302, second_response.text
        assert second_response.headers['Location'] == next_flow['redirect_url']

    @pytest.mark.parametrize('timestamp_cookie_value', ['not-base62!', '0000', '1'])
    def test_track_redirect__malformed_timestamp_cookie_resets_when_flow_is_selected(
        self, client, campaign, domain, write_to_db, read_from_db, ip2location_mock, timestamp_cookie_value
    ):
        current_flow = write_to_db(
            'flow',
            {
                'name': 'Current show-once flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/current',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': True,
            },
        )
        next_flow = write_to_db(
            'flow',
            {
                'name': 'Next repeatable flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/next',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': False,
            },
        )
        cookie_flow_id = write_to_db(
            'domain_cookie',
            {'domain_id': domain['id'], 'name': 'flow_id', 'opaque_name': 'sticky_flow'},
        )
        cookie_flow_timestamp = write_to_db(
            'domain_cookie',
            {
                'domain_id': domain['id'],
                'name': 'flow_timestamp',
                'opaque_name': 'sticky_time',
                'encryption_key': 'a' * 64,
            },
        )
        client.set_cookie(cookie_flow_id['opaque_name'], str(current_flow['id']))
        client.set_cookie(cookie_flow_timestamp['opaque_name'], timestamp_cookie_value)

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == next_flow['redirect_url']
        refreshed_timestamp_cookie = client.get_cookie(cookie_flow_timestamp['opaque_name'])
        assert refreshed_timestamp_cookie.value != timestamp_cookie_value

    def test_track_redirect__skips_current_flow_when_rule_no_longer_matches(
        self, client, campaign, domain, write_to_db, ip2location_mock
    ):
        current_flow = write_to_db(
            'flow',
            {
                'name': 'Current non-matching flow',
                'campaign_id': campaign['id'],
                'rule': 'country == "US"',
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/current',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': False,
            },
        )
        next_flow = write_to_db(
            'flow',
            {
                'name': 'Next matching flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/next',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        cookie_flow_id = write_to_db(
            'domain_cookie',
            {'domain_id': domain['id'], 'name': 'flow_id', 'opaque_name': 'sticky_flow'},
        )
        client.set_cookie(cookie_flow_id['opaque_name'], str(current_flow['id']))

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == next_flow['redirect_url']

    def test_track_redirect__invalid_cookie_resets_to_first_visit_selection(
        self, client, campaign, domain, write_to_db, ip2location_mock
    ):
        first_flow = write_to_db(
            'flow',
            {
                'name': 'First flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/first',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        write_to_db(
            'flow',
            {
                'name': 'Second flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/second',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        cookie_flow_id = write_to_db(
            'domain_cookie',
            {'domain_id': domain['id'], 'name': 'flow_id', 'opaque_name': 'sticky_flow'},
        )
        client.set_cookie(cookie_flow_id['opaque_name'], '100500')

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == first_flow['redirect_url']

    def test_track_redirect__returns_no_match_when_remaining_progression_flows_are_blocked(
        self, client, campaign, domain, write_to_db, read_from_db, ip2location_mock
    ):
        current_flow = write_to_db(
            'flow',
            {
                'name': 'Current show-once flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/current',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': True,
            },
        )
        write_to_db(
            'flow',
            {
                'name': 'Remaining non-matching flow',
                'campaign_id': campaign['id'],
                'rule': 'country == "US"',  # ip2location_mock resolves the request IP to MD
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/remaining',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        cookie_flow_id = write_to_db(
            'domain_cookie',
            {'domain_id': domain['id'], 'name': 'flow_id', 'opaque_name': 'sticky_flow'},
        )
        click_id = uuid4()
        client.set_cookie(cookie_flow_id['opaque_name'], str(current_flow['id']))

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(click_id)})

        assert response.status_code == 200, response.text
        assert response.text == ''
        assert read_from_db('track_discard')['click_id'] == click_id

    def test_track_redirect__uses_default_flow_when_no_normal_flow_matches(
        self, client, authorization, campaign, domain, write_to_db, read_from_db, set_default_flow_id, ip2location_mock
    ):
        click_id = uuid4()
        write_to_db(
            'flow',
            {
                'name': 'US only',
                'campaign_id': campaign['id'],
                'rule': 'country == "US"',
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/us',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        default_flow = write_to_db(
            'flow',
            {
                'name': 'Campaign default',
                'campaign_id': campaign['id'],
                'rule': 'country == "US"',
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/default',
                'is_enabled': True,
                'is_deleted': False,
                'show_once_per_visitor': True,
            },
        )
        set_default_flow_id(campaign['id'], default_flow['id'])

        cookie_flow_id = write_to_db(
            'domain_cookie',
            {'domain_id': domain['id'], 'name': 'flow_id', 'opaque_name': 'sticky_flow'},
        )
        client.set_cookie(cookie_flow_id['opaque_name'], str(default_flow['id']))

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(click_id)})

        assert response.status_code == 302, response.text

        # rules had not been evaluated for default flow, redirected despite MD IP address
        assert response.headers['Location'] == default_flow['redirect_url']
        assert read_from_db('track_discard') is None

    def test_track_redirect__normal_match_takes_precedence_over_default_flow(
        self, client, authorization, campaign, domain, write_to_db, set_default_flow_id, ip2location_mock
    ):
        normal_flow = write_to_db(
            'flow',
            {
                'name': 'Normal match',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/normal',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        default_flow = write_to_db(
            'flow',
            {
                'name': 'Campaign default',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/default',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        set_default_flow_id(campaign['id'], default_flow['id'])

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == normal_flow['redirect_url']

    @pytest.mark.parametrize(
        'default_flow_values',
        [
            {'is_enabled': False, 'is_deleted': False},
            {'is_enabled': True, 'is_deleted': True},
        ],
    )
    def test_track_redirect__does_not_use_unrunnable_default_flow(
        self,
        client,
        authorization,
        campaign,
        domain,
        write_to_db,
        read_from_db,
        set_default_flow_id,
        ip2location_mock,
        default_flow_values,
    ):
        click_id = uuid4()
        default_flow = write_to_db(
            'flow',
            {
                'name': 'Unrunnable default',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/default',
                **default_flow_values,
            },
        )
        set_default_flow_id(campaign['id'], default_flow['id'])

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(click_id)})

        assert response.status_code == 200, response.text
        assert response.text == ''
        assert read_from_db('track_discard')['click_id'] == click_id

    def test_track_redirect__does_not_use_missing_default_flow(
        self, client, domain, campaign_payload, write_to_db, read_from_db, ip2location_mock
    ):
        click_id = uuid4()
        campaign_with_missing_default = write_to_db(
            'campaign',
            campaign_payload | {'name': 'Missing default campaign', 'default_flow_id': 100500},
        )
        write_to_db(
            'domain',
            {
                'hostname': 'missing-default.example.com',
                'purpose': 'campaign',
                'campaign_id': campaign_with_missing_default['id'],
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )

        response = client.get(
            f'/process/{campaign_with_missing_default["id"]}', query_string={'clickId': str(click_id)}
        )

        assert response.status_code == 200, response.text
        assert response.text == ''
        assert read_from_db('track_discard')['click_id'] == click_id

    def test_track_redirect__tracks_discard_when_no_flow_matches(
        self, client, campaign, domain, write_to_db, read_from_db, ip2location_mock
    ):
        click_id = uuid4()
        write_to_db(
            'flow',
            {
                'name': 'US only',
                'campaign_id': campaign['id'],
                'rule': 'country == "US"',
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/us',
                'is_enabled': True,
                'is_deleted': False,
            },
        )

        response = client.get(
            f'/process/{campaign["id"]}',
            query_string={'clickId': str(click_id)},
            headers={'User-Agent': MOBILE_SAFARI_USER_AGENT},
        )

        assert response.status_code == 200, response.text
        assert response.text == ''

        click = read_from_db('track_click')
        assert click == {
            'id': mock.ANY,
            'click_id': click_id,
            'campaign_id': campaign['id'],
            'parameters': '{}',
            'created_at': mock.ANY,
        }

        discard = read_from_db('track_discard')
        assert discard == {
            'id': mock.ANY,
            'click_id': click_id,
            'campaign_id': campaign['id'],
            'country': 'MD',
            'browser_family': 'Mobile Safari',
            'os_family': 'iOS',
            'device_family': 'iPhone',
            'is_mobile': True,
            'is_bot': False,
            'created_at': mock.ANY,
        }

    def test_track_redirect(self, client, campaign, domain, flow, read_from_db, ip2location_mock):
        click_id = uuid4()
        request_payload = {
            'clickId': str(click_id),
            'status': 'accept',
            'tid': '123',
            'payout': 10,
            'offer_id': '456',
            'lead_status': 'accept,expect',
            'sale_status': 'confirm',
            'rejected_status': 'reject,fail,trash,error',
            'return': 'OK',
            'from': 'terraleads.com',
        }

        started_at = int(time.time())
        response = client.get(f'/process/{campaign["id"]}', query_string=request_payload)
        completed_at = int(time.time())
        assert response.status_code == 302, response.text
        assert response.headers['Location'] == flow['redirect_url']  # user gets redirected
        cookie_flow_id = read_from_db('domain_cookie', filters={'domain_id': domain['id'], 'name': 'flow_id'})
        assert cookie_flow_id == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'domain_id': domain['id'],
            'name': 'flow_id',
            'opaque_name': mock.ANY,
            'encryption_key': None,
        }
        flow_id_cookie = client.get_cookie(cookie_flow_id['opaque_name'])
        assert flow_id_cookie.value == str(flow['id'])

        cookie_flow_timestamp = read_from_db(
            'domain_cookie',
            filters={'domain_id': domain['id'], 'name': 'flow_timestamp'},
        )
        assert cookie_flow_timestamp == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'domain_id': domain['id'],
            'name': 'flow_timestamp',
            'opaque_name': mock.ANY,
            'encryption_key': mock.ANY,
        }
        timestamp_cookie = client.get_cookie(cookie_flow_timestamp['opaque_name'])
        timestamp_cookie_value = decode_flow_timestamp_cookie(
            timestamp_cookie.value,
            cookie_flow_timestamp['encryption_key'],
        )
        assert started_at <= timestamp_cookie_value <= completed_at

        assert ip2location_mock.get_country_short.called

        click = read_from_db('track_click')
        assert click == {
            'id': mock.ANY,
            'click_id': click_id,
            'campaign_id': campaign['id'],
            'parameters': mock.ANY,
            'created_at': mock.ANY,
        }

        assert json.loads(click['parameters']) == {
            'from': request_payload['from'],
            'lead_status': request_payload['lead_status'],
            'offer_id': request_payload['offer_id'],
            'payout': str(request_payload['payout']),
            'rejected_status': request_payload['rejected_status'],
            'return': request_payload['return'],
            'sale_status': request_payload['sale_status'],
            'status': request_payload['status'],
            'tid': request_payload['tid'],
        }

    def test_track_redirect__matches_flow_without_rule(self, client, campaign, domain, write_to_db, ip2location_mock):
        write_to_db(
            'flow',
            {
                'name': 'US only',
                'campaign_id': campaign['id'],
                'rule': 'country == "US"',
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/us',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        fallback_flow = write_to_db(
            'flow',
            {
                'name': 'No rule',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 5,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/any',
                'is_enabled': True,
                'is_deleted': False,
            },
        )

        request_payload = {'click_id': str(uuid4())}

        response = client.get(f'/process/{campaign["id"]}', query_string=request_payload)
        assert response.status_code == 302, response.text
        assert response.headers['Location'] == fallback_flow['redirect_url']

    def test_track_redirect__missing_click_id(self, client, campaign, domain, flow, ip2location_mock):
        response = client.get(f'/process/{campaign["id"]}')

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == flow['redirect_url']

    def test_track_redirect__ignores_disabled_and_deleted_flows(
        self, client, campaign, domain, write_to_db, ip2location_mock
    ):
        write_to_db(
            'flow',
            {
                'name': 'Disabled fallback',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 50,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/disabled',
                'is_enabled': False,
                'is_deleted': False,
            },
        )
        write_to_db(
            'flow',
            {
                'name': 'Deleted fallback',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 40,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/deleted',
                'is_enabled': True,
                'is_deleted': True,
            },
        )
        runnable_flow = write_to_db(
            'flow',
            {
                'name': 'Runnable fallback',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 30,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/runnable',
                'is_enabled': True,
                'is_deleted': False,
            },
        )

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == runnable_flow['redirect_url']

    def test_track_redirect__returns_no_match_when_only_non_runnable_flows_remain(
        self, client, campaign, domain, write_to_db, ip2location_mock
    ):
        write_to_db(
            'flow',
            {
                'name': 'Disabled fallback',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 50,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/disabled',
                'is_enabled': False,
                'is_deleted': False,
            },
        )
        write_to_db(
            'flow',
            {
                'name': 'Deleted fallback',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 40,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/deleted',
                'is_enabled': True,
                'is_deleted': True,
            },
        )

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 200, response.text
        assert response.text == ''

    @pytest.mark.usefixtures('ip2location_unavailable')
    def test_track_redirect__skips_country_rule_flow_when_ip2location_is_unavailable(
        self, client, campaign, domain, write_to_db
    ):
        write_to_db(
            'flow',
            {
                'name': 'Country flow',
                'campaign_id': campaign['id'],
                'rule': 'country == "MD"',
                'order_value': 20,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/country',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        fallback_flow = write_to_db(
            'flow',
            {
                'name': 'Fallback flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/fallback',
                'is_enabled': True,
                'is_deleted': False,
            },
        )

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == fallback_flow['redirect_url']

    def test_track_redirect__does_not_track_discard_when_flow_matches(
        self, client, campaign, domain, flow, read_from_db, ip2location_mock
    ):
        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == flow['redirect_url']
        assert read_from_db('track_discard') is None

    def test_track_redirect__generates_click_id_when_missing(
        self, client, campaign, domain, write_to_db, read_from_db, ip2location_mock
    ):
        write_to_db(
            'flow',
            {
                'name': 'US only',
                'campaign_id': campaign['id'],
                'rule': 'country == "US"',
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/us',
                'is_enabled': True,
                'is_deleted': False,
            },
        )

        response = client.get(
            f'/process/{campaign["id"]}',
            headers={'User-Agent': MOBILE_SAFARI_USER_AGENT},
        )

        assert response.status_code == 200, response.text
        assert response.text == ''

        click = read_from_db('track_click')
        assert click == {
            'id': mock.ANY,
            'click_id': mock.ANY,
            'campaign_id': campaign['id'],
            'parameters': '{}',
            'created_at': mock.ANY,
        }
        assert isinstance(click['click_id'], UUID)

        discard = read_from_db('track_discard')
        assert discard['click_id'] == click['click_id']

    def test_track_redirect__uses_deterministic_order_for_runnable_flows(
        self, client, campaign, domain, write_to_db, ip2location_mock
    ):
        first_inserted_flow = write_to_db(
            'flow',
            {
                'name': 'First runnable fallback',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/first',
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        write_to_db(
            'flow',
            {
                'name': 'Second runnable fallback',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 10,
                'action_type': 'redirect',
                'redirect_url': 'https://example.com/second',
                'is_enabled': True,
                'is_deleted': False,
            },
        )

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == first_inserted_flow['redirect_url']


class TestTrackLanding:
    @pytest.fixture
    def landing_page_content(self):
        return '<html>Uber landing page</html>'

    @pytest.fixture
    def flow_payload(self, flow_rule):
        return {
            'order_value': 1,
            'rule': flow_rule,
            'action_type': 'render',
            'redirect_url': None,
            'is_enabled': True,
            'is_deleted': False,
        }

    @pytest.fixture
    def landing_render_mock(self, flow, environment, landing_page_content, respx_mock):
        assert environment["LANDING_PAGE_RENDERER_BASE_URL"] is not None, 'LANDING_PAGE_RENDERER_BASE_URL is not set'
        return respx_mock.get(f'{environment["LANDING_PAGE_RENDERER_BASE_URL"]}/{flow["id"]}/').mock(
            httpx.Response(
                status_code=200,
                text=landing_page_content,
                headers={'Content-Type': 'text/html; charset=utf-8'},
            )
        )

    def test_track_landing(self, client, campaign, domain, flow, read_from_db, ip2location_mock, landing_render_mock):
        click_id = uuid4()
        request_payload = {
            'clickId': str(click_id),
            'status': 'accept',
            'tid': '123',
            'payout': 10,
            'offer_id': '456',
            'lead_status': 'accept,expect',
            'sale_status': 'confirm',
            'rejected_status': 'reject,fail,trash,error',
            'return': 'OK',
            'from': 'terraleads.com',
        }

        response = client.get(f'/process/{campaign["id"]}', query_string=request_payload)
        assert response.status_code == 200, response.text
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'

        assert ip2location_mock.get_country_short.called
        assert landing_render_mock.called

        click = read_from_db('track_click')
        assert click == {
            'id': mock.ANY,
            'click_id': click_id,
            'campaign_id': campaign['id'],
            'parameters': mock.ANY,
            'created_at': mock.ANY,
        }

        assert json.loads(click['parameters']) == {
            'from': request_payload['from'],
            'lead_status': request_payload['lead_status'],
            'offer_id': request_payload['offer_id'],
            'payout': str(request_payload['payout']),
            'rejected_status': request_payload['rejected_status'],
            'return': request_payload['return'],
            'sale_status': request_payload['sale_status'],
            'status': request_payload['status'],
            'tid': request_payload['tid'],
        }

    def test_track_landing__proxies_request_and_response_exchange(
        self, client, campaign, domain, flow, environment, ip2location_mock, respx_mock
    ):
        renderer_body = b'rendered payload'
        query_string = [('tag', 'one'), ('tag', 'two'), ('empty', '')]
        request_headers = {'X-Landing-Header': 'forward-me'}
        response_status_code = 307
        response_headers = {
            'Content-Type': 'text/plain; charset=utf-8',
            'Location': '/next-step',
            'X-Renderer-Meta': 'preserved',
            'Set-Cookie': 'renderer_session=abc; Path=/; HttpOnly',
            'Connection': 'close',
            'Content-Length': '9999',
        }
        renderer_route = respx_mock.get(
            f'{environment["LANDING_PAGE_RENDERER_BASE_URL"]}/{flow["id"]}/?tag=one&tag=two&empty='
        ).mock(
            httpx.Response(
                status_code=response_status_code,
                content=renderer_body,
                headers=response_headers,
            )
        )
        client.set_cookie('visitor', 'cookie-value')

        response = client.get(
            f'/process/{campaign["id"]}',
            query_string=query_string,
            headers=request_headers,
        )

        assert response.status_code == response_status_code, response.text

        assert renderer_route.called
        assert response.data == renderer_body
        assert response.headers['Content-Type'] == response_headers['Content-Type']
        assert response.headers['Location'] == response_headers['Location']
        assert response.headers['X-Renderer-Meta'] == response_headers['X-Renderer-Meta']
        assert response.headers['Set-Cookie'] == response_headers['Set-Cookie']
        assert 'Connection' not in response.headers
        assert response.headers['Content-Length'] == str(len(renderer_body))

        renderer_request = renderer_route.calls[0].request
        assert renderer_request.method == 'GET'
        assert str(renderer_request.url).endswith(f'/{flow["id"]}/?tag=one&tag=two&empty=')
        assert renderer_request.headers['X-Landing-Header'] == request_headers['X-Landing-Header']
        assert 'visitor=cookie-value' in renderer_request.headers['Cookie']
        assert renderer_request.content == b''

    def test_track_landing__sets_domain_sticky_cookie_on_first_visit(
        self, client, campaign, domain, environment, write_to_db, read_from_db, ip2location_mock, respx_mock
    ):
        render_flow = write_to_db(
            'flow',
            {
                'name': 'Render flow',
                'campaign_id': campaign['id'],
                'rule': None,
                'order_value': 1,
                'action_type': 'render',
                'redirect_url': None,
                'is_enabled': True,
                'is_deleted': False,
            },
        )
        respx_mock.get(f'{environment["LANDING_PAGE_RENDERER_BASE_URL"]}/{render_flow["id"]}/').mock(
            httpx.Response(status_code=200, text='<html>Sticky landing</html>')
        )

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 200, response.text
        assert response.text == '<html>Sticky landing</html>'
        cookie_flow_id = read_from_db('domain_cookie', filters={'domain_id': domain['id'], 'name': 'flow_id'})
        assert cookie_flow_id == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'domain_id': domain['id'],
            'name': 'flow_id',
            'opaque_name': mock.ANY,
            'encryption_key': None,
        }
        flow_id_cookie = client.get_cookie(cookie_flow_id['opaque_name'])
        assert flow_id_cookie.value == str(render_flow['id'])

    def test_track_landing__returns_404_when_campaign_domain_is_missing(self, client, campaign, read_from_db):
        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 404, response.text
        assert response.json == {'message': 'Domain does not exist'}
        assert read_from_db('track_click') is None

    def test_track_landing__returns_404_when_campaign_domain_is_disabled(
        self, client, campaign, read_from_db, write_to_db
    ):
        write_to_db(
            'domain',
            {
                'hostname': 'campaign.example.com',
                'purpose': 'campaign',
                'campaign_id': campaign['id'],
                'is_a_record_set': True,
                'is_disabled': True,
            },
        )

        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 404, response.text
        assert response.json == {'message': 'Domain does not exist'}
        assert read_from_db('track_click') is None

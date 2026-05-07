import json
from unittest import mock
from uuid import UUID, uuid4

import httpx
import pytest

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
    def test_track_redirect__tracks_discard_when_no_flow_matches(
        self, client, campaign, write_to_db, read_from_db, ip2location_mock
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

    def test_track_redirect(self, client, campaign, flow, read_from_db, ip2location_mock):
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
        assert response.status_code == 302, response.text
        assert response.headers['Location'] == flow['redirect_url']  # user gets redirected

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

    def test_track_redirect__matches_flow_without_rule(self, client, campaign, write_to_db, ip2location_mock):
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

    def test_track_redirect__missing_click_id(self, client, campaign, flow, ip2location_mock):
        response = client.get(f'/process/{campaign["id"]}')

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == flow['redirect_url']

    def test_track_redirect__ignores_disabled_and_deleted_flows(self, client, campaign, write_to_db, ip2location_mock):
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
        self, client, campaign, write_to_db, ip2location_mock
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

    def test_track_redirect__does_not_track_discard_when_flow_matches(
        self, client, campaign, flow, read_from_db, ip2location_mock
    ):
        response = client.get(f'/process/{campaign["id"]}', query_string={'clickId': str(uuid4())})

        assert response.status_code == 302, response.text
        assert response.headers['Location'] == flow['redirect_url']
        assert read_from_db('track_discard') is None

    def test_track_redirect__generates_click_id_when_missing(
        self, client, campaign, write_to_db, read_from_db, ip2location_mock
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
        self, client, campaign, write_to_db, ip2location_mock
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
            httpx.Response(status_code=200, text=landing_page_content)
        )

    def test_track_landing(self, client, campaign, flow, read_from_db, ip2location_mock, landing_render_mock):
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

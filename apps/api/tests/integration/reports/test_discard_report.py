import pytest
from fixtures.utils import click_uuid


class TestDiscardReport:
    @pytest.fixture
    def discard_country_report_preconditions(self, campaign, timestamp, write_to_db):
        # Recent clicks should contribute to the selected 1h totals.
        for index in range(50):
            write_to_db(
                'track_click',
                {
                    'click_id': click_uuid(index + 1),
                    'campaign_id': campaign['id'],
                    'parameters': {},
                    'created_at': timestamp - 60,
                },
                returning=False,
            )

        # Older clicks stay outside 1h so the test proves window filtering.
        for index in range(20):
            write_to_db(
                'track_click',
                {
                    'click_id': click_uuid(index + 1001),
                    'campaign_id': campaign['id'],
                    'parameters': {},
                    'created_at': timestamp - 7200,
                },
                returning=False,
            )

        # Recent discards should appear in the 1h grouping result.
        for click_number, country, created_at in (
            (1, 'UA', timestamp - 60),
            (2, 'UA', timestamp - 60),
            (3, 'MD', timestamp - 60),
            (1001, 'RO', timestamp - 7200),
            (1002, 'RO', timestamp - 7200),
        ):
            write_to_db(
                'track_discard',
                {
                    'click_id': click_uuid(click_number),
                    'campaign_id': campaign['id'],
                    'country': country,
                    'browser_family': None,
                    'os_family': None,
                    'device_family': None,
                    'is_mobile': False,
                    'is_bot': False,
                    'created_at': created_at,
                },
                returning=False,
            )

    @pytest.fixture
    def discard_country_report_with_null_group_preconditions(self, campaign, timestamp, write_to_db):
        for index in range(20):
            write_to_db(
                'track_click',
                {
                    'click_id': click_uuid(index + 1),
                    'campaign_id': campaign['id'],
                    'parameters': {},
                    'created_at': timestamp - 60,
                },
                returning=False,
            )

        for click_number, country in ((1, 'UA'), (2, None)):
            write_to_db(
                'track_discard',
                {
                    'click_id': click_uuid(click_number),
                    'campaign_id': campaign['id'],
                    'country': country,
                    'browser_family': None,
                    'os_family': None,
                    'device_family': None,
                    'is_mobile': False,
                    'is_bot': False,
                    'created_at': timestamp - 60,
                },
                returning=False,
            )

    @pytest.fixture
    def discard_mobile_report_preconditions(self, campaign, timestamp, write_to_db):
        # Recent clicks define the 5m denominator for this report.
        for index in range(25):
            write_to_db(
                'track_click',
                {
                    'click_id': click_uuid(index + 1),
                    'campaign_id': campaign['id'],
                    'parameters': {},
                    'created_at': timestamp - 60,
                },
                returning=False,
            )

        # Older clicks stay outside 5m so only recent rows count in totals.
        for index in range(10):
            write_to_db(
                'track_click',
                {
                    'click_id': click_uuid(index + 1001),
                    'campaign_id': campaign['id'],
                    'parameters': {},
                    'created_at': timestamp - 1200,
                },
                returning=False,
            )

        # Mixed recent and older discards verify raw boolean grouping and window filtering together.
        for click_number, is_mobile, created_at in (
            (1, True, timestamp - 60),
            (2, True, timestamp - 60),
            (3, False, timestamp - 60),
            (1001, False, timestamp - 1200),
        ):
            write_to_db(
                'track_discard',
                {
                    'click_id': click_uuid(click_number),
                    'campaign_id': campaign['id'],
                    'country': 'UA',
                    'browser_family': None,
                    'os_family': None,
                    'device_family': None,
                    'is_mobile': is_mobile,
                    'is_bot': False,
                    'created_at': created_at,
                },
                returning=False,
            )

    @pytest.mark.usefixtures('discard_country_report_preconditions')
    def test_get_discard_report__returns_selected_window_totals_and_country_rows(self, client, authorization, campaign):
        response = client.get(
            '/api/v2/reports/discard',
            headers={'Authorization': authorization},
            query_string={'campaignId': campaign['id'], 'window': '1h', 'groupBy': 'country'},
        )

        assert response.status_code == 200, response.text
        # Older discard rows are outside the selected 1h window and must not affect totals or grouped rows.
        assert response.json == {
            'content': {
                'window': '1h',
                'groupBy': 'country',
                'totals': {'discardCount': 3, 'totalCount': 50, 'rate': 0.06, 'eligible': True},
                'rows': [
                    {'value': 'UA', 'count': 2, 'share': 0.6667},
                    {'value': 'MD', 'count': 1, 'share': 0.3333},
                ],
            }
        }

    @pytest.mark.usefixtures('discard_country_report_with_null_group_preconditions')
    def test_get_discard_report__returns_raw_null_when_group_value_is_null(self, client, authorization, campaign):
        response = client.get(
            '/api/v2/reports/discard',
            headers={'Authorization': authorization},
            query_string={'campaignId': campaign['id'], 'window': '1h', 'groupBy': 'country'},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': {
                'window': '1h',
                'groupBy': 'country',
                'totals': {'discardCount': 2, 'totalCount': 20, 'rate': 0.1, 'eligible': True},
                'rows': [
                    {'value': 'UA', 'count': 1, 'share': 0.5},
                    {'value': None, 'count': 1, 'share': 0.5},
                ],
            }
        }

    @pytest.mark.usefixtures('discard_mobile_report_preconditions')
    def test_get_discard_report__returns_raw_boolean_grouping_values(self, client, authorization, campaign):
        response = client.get(
            '/api/v2/reports/discard',
            headers={'Authorization': authorization},
            query_string={'campaignId': campaign['id'], 'window': '5m', 'groupBy': 'isMobile'},
        )

        assert response.status_code == 200, response.text
        # Older discard rows are outside the selected 5m window and must not affect totals or grouped rows.
        assert response.json == {
            'content': {
                'window': '5m',
                'groupBy': 'isMobile',
                'totals': {'discardCount': 3, 'totalCount': 25, 'rate': 0.12, 'eligible': True},
                'rows': [
                    {'value': True, 'count': 2, 'share': 0.6667},
                    {'value': False, 'count': 1, 'share': 0.3333},
                ],
            }
        }

    @pytest.mark.parametrize(
        ('group_by', 'discard_payload', 'expected_value'),
        [
            ('browserFamily', {'browser_family': 'Mobile Safari'}, 'Mobile Safari'),
            ('osFamily', {'os_family': 'iOS'}, 'iOS'),
            ('deviceFamily', {'device_family': 'iPhone'}, 'iPhone'),
            ('isBot', {'is_bot': True}, True),
        ],
    )
    def test_get_discard_report__supports_each_dimension(
        self,
        client,
        authorization,
        campaign,
        campaign_payload,
        timestamp,
        write_to_db,
        group_by,
        discard_payload,
        expected_value,
    ):
        report_campaign = write_to_db('campaign', campaign_payload | {'name': f'{campaign["name"]}-{group_by}'})

        # All clicks are recent so the selected 1d totals are unambiguous for each dimension.
        for index in range(20):
            write_to_db(
                'track_click',
                {
                    'click_id': click_uuid(10000 + index + 1),
                    'campaign_id': report_campaign['id'],
                    'parameters': {},
                    'created_at': timestamp - 60,
                },
                returning=False,
            )

        # A single discard row isolates the grouped value returned for the current dimension.
        write_to_db(
            'track_discard',
            {
                'click_id': click_uuid(10001),
                'campaign_id': report_campaign['id'],
                'country': 'UA',
                'browser_family': discard_payload.get('browser_family'),
                'os_family': discard_payload.get('os_family'),
                'device_family': discard_payload.get('device_family'),
                'is_mobile': discard_payload.get('is_mobile', False),
                'is_bot': discard_payload.get('is_bot', False),
                'created_at': timestamp - 60,
            },
            returning=False,
        )

        response = client.get(
            '/api/v2/reports/discard',
            headers={'Authorization': authorization},
            query_string={'campaignId': report_campaign['id'], 'window': '1d', 'groupBy': group_by},
        )

        assert response.status_code == 200, response.text
        # All discard rows for this case are inside the selected 1d window, so the response should reflect the full setup.
        assert response.json == {
            'content': {
                'window': '1d',
                'groupBy': group_by,
                'totals': {'discardCount': 1, 'totalCount': 20, 'rate': 0.05, 'eligible': True},
                'rows': [{'value': expected_value, 'count': 1, 'share': 1.0}],
            }
        }

from fixtures.utils import click_uuid


def test_get_alerts__suppresses_discard_alert_when_1h_total_is_too_low(
    client, authorization, campaign, write_to_db, timestamp
):
    for index in range(19):
        click = write_to_db(
            'track_click',
            {
                'click_id': click_uuid(index + 1),
                'campaign_id': campaign['id'],
                'parameters': {},
                'created_at': timestamp - 60,
            },
        )
        write_to_db(
            'track_discard',
            {
                'click_id': click['click_id'],
                'campaign_id': campaign['id'],
                'country': 'MD',
                'browser_family': 'Mobile Safari',
                'os_family': 'iOS',
                'device_family': 'iPhone',
                'is_mobile': True,
                'is_bot': False,
                'created_at': timestamp - 60,
            },
            returning=False,
        )

    response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {'content': []}


def test_get_alerts__returns_info_discard_alert(client, authorization, campaign, write_to_db, timestamp):
    for index in range(100):
        click = write_to_db(
            'track_click',
            {
                'click_id': click_uuid(index + 1),
                'campaign_id': campaign['id'],
                'parameters': {},
                'created_at': timestamp - 60,
            },
        )
        if index == 0:
            write_to_db(
                'track_discard',
                {
                    'click_id': click['click_id'],
                    'campaign_id': campaign['id'],
                    'country': 'MD',
                    'browser_family': 'Mobile Safari',
                    'os_family': 'iOS',
                    'device_family': 'iPhone',
                    'is_mobile': True,
                    'is_bot': False,
                    'created_at': timestamp - 60,
                },
                returning=False,
            )

    response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'code': 'core_campaign_discard',
                'message': (
                    f'Campaign "{campaign["name"]}" has discards. '
                    '5m: 1/100 (1.0%), 1h: 1/100 (1.0%), 1d: 1/100 (1.0%). Review flow routing.'
                ),
                'severity': 'info',
                'source': 'src.reports.services',
                'payload': {
                    'campaignId': campaign['id'],
                    'campaignName': campaign['name'],
                    'severityWindow': '1h',
                    'metrics': {
                        '5m': {'discardCount': 1, 'totalCount': 100, 'rate': 0.01, 'eligible': True},
                        '1h': {'discardCount': 1, 'totalCount': 100, 'rate': 0.01, 'eligible': True},
                        '1d': {'discardCount': 1, 'totalCount': 100, 'rate': 0.01, 'eligible': True},
                    },
                },
            }
        ]
    }


def test_get_alerts__returns_warning_discard_alert(client, authorization, campaign, write_to_db, timestamp):
    # Inside all windows: contributes to 5m, 1h, and 1d.
    for index in range(25):
        click = write_to_db(
            'track_click',
            {
                'click_id': click_uuid(index + 1),
                'campaign_id': campaign['id'],
                'parameters': {},
                'created_at': timestamp - 120,
            },
        )
        if index == 0:
            write_to_db(
                'track_discard',
                {
                    'click_id': click['click_id'],
                    'campaign_id': campaign['id'],
                    'country': 'MD',
                    'browser_family': 'Mobile Safari',
                    'os_family': 'iOS',
                    'device_family': 'iPhone',
                    'is_mobile': True,
                    'is_bot': False,
                    'created_at': timestamp - 120,
                },
                returning=False,
            )

    # Older than 5m but inside 1h and 1d: contributes only to 1h and 1d.
    for index in range(20):
        click = write_to_db(
            'track_click',
            {
                'click_id': click_uuid(index + 101),
                'campaign_id': campaign['id'],
                'parameters': {},
                'created_at': timestamp - 1200,
            },
        )
        if index < 2:
            write_to_db(
                'track_discard',
                {
                    'click_id': click['click_id'],
                    'campaign_id': campaign['id'],
                    'country': 'MD',
                    'browser_family': 'Mobile Safari',
                    'os_family': 'iOS',
                    'device_family': 'iPhone',
                    'is_mobile': True,
                    'is_bot': False,
                    'created_at': timestamp - 1200,
                },
                returning=False,
            )

    # Older than 1h but inside 1d: contributes only to 1d.
    for index in range(10):
        click = write_to_db(
            'track_click',
            {
                'click_id': click_uuid(index + 201),
                'campaign_id': campaign['id'],
                'parameters': {},
                'created_at': timestamp - 7200,
            },
        )
        if index < 9:
            write_to_db(
                'track_discard',
                {
                    'click_id': click['click_id'],
                    'campaign_id': campaign['id'],
                    'country': 'MD',
                    'browser_family': 'Mobile Safari',
                    'os_family': 'iOS',
                    'device_family': 'iPhone',
                    'is_mobile': True,
                    'is_bot': False,
                    'created_at': timestamp - 7200,
                },
                returning=False,
            )

    response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'code': 'core_campaign_discard',
                'message': (
                    f'Campaign "{campaign["name"]}" has discards. '
                    '5m: 1/25 (4.0%), 1h: 3/45 (6.7%), 1d: 12/55 (21.8%). Review flow routing.'
                ),
                'severity': 'warning',
                'source': 'src.reports.services',
                'payload': {
                    'campaignId': campaign['id'],
                    'campaignName': campaign['name'],
                    'severityWindow': '1h',
                    'metrics': {
                        '5m': {'discardCount': 1, 'totalCount': 25, 'rate': 0.04, 'eligible': True},
                        '1h': {'discardCount': 3, 'totalCount': 45, 'rate': 0.0667, 'eligible': True},
                        '1d': {'discardCount': 12, 'totalCount': 55, 'rate': 0.2182, 'eligible': True},
                    },
                },
            }
        ]
    }


def test_get_alerts__returns_error_discard_alert(client, authorization, campaign, write_to_db, timestamp):
    for index in range(25):
        click = write_to_db(
            'track_click',
            {
                'click_id': click_uuid(index + 1),
                'campaign_id': campaign['id'],
                'parameters': {},
                'created_at': timestamp - 60,
            },
        )
        if index < 5:
            write_to_db(
                'track_discard',
                {
                    'click_id': click['click_id'],
                    'campaign_id': campaign['id'],
                    'country': 'MD',
                    'browser_family': 'Mobile Safari',
                    'os_family': 'iOS',
                    'device_family': 'iPhone',
                    'is_mobile': True,
                    'is_bot': False,
                    'created_at': timestamp - 60,
                },
                returning=False,
            )

    response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json['content'][0]['severity'] == 'error'

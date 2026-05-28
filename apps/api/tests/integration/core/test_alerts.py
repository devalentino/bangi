import pytest


@pytest.mark.usefixtures('ip2location_unavailable')
def test_get_alerts__returns_ip2location_database_missing_alert(
    client, authorization, campaign, set_default_flow_id, flow
):
    set_default_flow_id(campaign['id'], flow['id'])

    response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'code': 'core_ip2location_database_missing',
                'message': 'Country targeting is unavailable until the IP2Location database is configured.',
                'severity': 'warning',
                'source': 'src.core.alerts',
                'payload': {'countryTargetingAvailable': False},
            }
        ]
    }


def test_get_alerts__returns_campaign_default_flow_configuration_alert(
    client, authorization, campaign, campaign_payload, write_to_db, flow_payload, set_default_flow_id
):
    disabled_default_flow_campaign = write_to_db(
        'campaign',
        campaign_payload | {'name': 'Disabled default flow campaign'},
    )
    disabled_default_flow = write_to_db(
        'flow',
        flow_payload
        | {
            'name': 'Disabled default',
            'campaign_id': disabled_default_flow_campaign['id'],
            'rule': None,
            'redirect_url': 'https://example.com/default',
            'is_enabled': False,
        },
    )

    set_default_flow_id(disabled_default_flow_campaign['id'], disabled_default_flow['id'])

    response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {
        'content': [
            {
                'code': 'core_campaign_default_flow_configuration',
                'message': (
                    f'Missing default flow: {campaign["name"]}. '
                    f'Invalid default flow: {disabled_default_flow_campaign["name"]}.'
                ),
                'severity': 'warning',
                'source': 'src.core.alerts',
                'payload': {
                    'missingDefaultFlowCampaigns': [
                        {
                            'campaignId': campaign['id'],
                            'campaignName': campaign['name'],
                        }
                    ],
                    'invalidDefaultFlowCampaigns': [
                        {
                            'campaignId': disabled_default_flow_campaign['id'],
                            'campaignName': disabled_default_flow_campaign['name'],
                            'defaultFlowId': disabled_default_flow['id'],
                            'reason': 'disabled',
                        }
                    ],
                },
            }
        ]
    }


def test_get_alerts__does_not_return_campaign_default_flow_alert_when_default_is_runnable(
    client, authorization, campaign_payload, write_to_db, flow_payload, set_default_flow_id
):
    campaign_with_default_flow = write_to_db('campaign', campaign_payload | {'name': 'Configured campaign'})
    default_flow = write_to_db(
        'flow',
        flow_payload
        | {
            'name': 'Configured default',
            'campaign_id': campaign_with_default_flow['id'],
            'rule': None,
            'redirect_url': 'https://example.com/default',
        },
    )

    set_default_flow_id(campaign_with_default_flow['id'], default_flow['id'])

    response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {'content': []}

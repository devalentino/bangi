from pymysql import cursors


def test_get_alerts__returns_campaign_default_flow_configuration_alert(
    client, authorization, campaign, campaign_payload, write_to_db
):
    disabled_default_flow_campaign = write_to_db(
        'campaign',
        campaign_payload | {
            'name': 'Disabled default flow campaign',
            'default_flow_id': 1,  # id of disabled_default_flow
        },
    )
    disabled_default_flow = write_to_db(
        'flow',
        {
            'name': 'Disabled default',
            'campaign_id': disabled_default_flow_campaign['id'],
            'rule': None,
            'order_value': 1,
            'action_type': 'redirect',
            'redirect_url': 'https://example.com/default',
            'is_enabled': False,
            'is_deleted': False,
        },
    )

    assert disabled_default_flow_campaign['default_flow_id'] == disabled_default_flow['id']

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
    client, authorization, campaign_payload, write_to_db
):
    campaign_with_default_flow = write_to_db(
        'campaign',
        campaign_payload | {
            'name': 'Configured campaign',
            'default_flow_id': 1,  # id of disabled_default_flow
        },
    )
    default_flow = write_to_db(
        'flow',
        {
            'name': 'Configured default',
            'campaign_id': campaign_with_default_flow['id'],
            'rule': None,
            'order_value': 1,
            'action_type': 'redirect',
            'redirect_url': 'https://example.com/default',
            'is_enabled': True,
            'is_deleted': False,
        },
    )

    assert campaign_with_default_flow['default_flow_id'] == default_flow['id']

    response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

    assert response.status_code == 200, response.text
    assert response.json == {'content': []}

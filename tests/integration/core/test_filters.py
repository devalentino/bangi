def test_get_campaigns(client, authorization, campaign):
    response = client.get('/api/v2/core/filters/campaigns', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text
    assert response.json == [{'id': 1, 'name': 'Test Campaign'}]


def test_get_expenses_distribution_parameters(client, authorization, campaign, write_to_db):
    write_to_db(
        'track_click',
        {'click_id': 'click-1', 'campaign_id': campaign['id'], 'parameters': {'utm_source': 'fb', 'ad_name': 'a1'}},
    )
    write_to_db(
        'track_click',
        {'click_id': 'click-2', 'campaign_id': campaign['id'], 'parameters': {'utm_source': 'ig', 'adset': 'set1'}},
    )
    write_to_db(
        'track_click',
        {'click_id': 'click-3', 'campaign_id': campaign['id'] + 1, 'parameters': {'ignored': 'value'}},
    )

    response = client.get(
        f'/api/v2/core/filters/campaigns/{campaign["id"]}/expenses-distribution-parameters',
        headers={'Authorization': authorization},
    )

    assert response.status_code == 200, response.text
    assert response.json == [{'parameter': 'ad_name'}, {'parameter': 'adset'}, {'parameter': 'utm_source'}]

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
        '/api/v2/reports/helpers/expenses-distribution-parameters',
        query_string={'campaignId': campaign['id']},
        headers={'Authorization': authorization},
    )

    assert response.status_code == 200, response.text
    assert response.json == [{'parameter': 'ad_name'}, {'parameter': 'adset'}, {'parameter': 'utm_source'}]


def test_get_expenses_distribution_parameter_values(client, authorization, campaign, write_to_db):
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
        {'click_id': 'click-3', 'campaign_id': campaign['id'] + 1, 'parameters': {'utm_source': 'ignored'}},
    )

    response = client.get(
        '/api/v2/reports/helpers/expenses-distribution-parameter-values',
        query_string={'campaignId': campaign['id'], 'parameter': 'utm_source'},
        headers={'Authorization': authorization},
    )

    assert response.status_code == 200, response.text
    assert response.json == [{'value': 'fb'}, {'value': 'ig'}]

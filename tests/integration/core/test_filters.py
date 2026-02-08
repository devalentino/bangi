def test_get_campaigns(client, authorization, campaign):
    response = client.get('/api/v2/core/filters/campaigns', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text
    assert response.json == [{'id': 1, 'name': 'Test Campaign'}]

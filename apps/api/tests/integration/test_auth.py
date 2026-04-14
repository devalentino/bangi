def test_health(client, authorization):
    response = client.post('/api/v2/auth/authenticate', headers={'Authorization': authorization})
    assert response.status_code == 200, response.text

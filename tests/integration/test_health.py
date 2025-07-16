def test_health(client):
    response = client.get('/api/v2/health')
    assert response.status_code == 200, response.text
    assert response.json == {'healthy': True}

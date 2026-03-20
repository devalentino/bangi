class TestAlerts:
    def test_get_alerts__business_portfolio_without_access_urls(self, client, authorization, business_portfolio):
        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'facebook_pacs_business_portfolio_access_url_missing',
                    'message': f'Business portfolio "{business_portfolio["name"]}" does not have access URLs',
                    'severity': 'warning',
                    'source': 'src.facebook_pacs.services',
                    'payload': {
                        'businessPortfolioId': business_portfolio['id'],
                        'businessPortfolioName': business_portfolio['name'],
                    },
                }
            ]
        }

    def test_get_alerts__business_portfolio_with_only_expired_access_urls(
        self, client, authorization, business_portfolio, timestamp, write_to_db
    ):
        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-1',
                'email': 'owner@example.com',
                'expires_at': timestamp - 1,
            },
        )

        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-2',
                'email': 'owner@example.com',
                'expires_at': timestamp - 1,
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'facebook_pacs_business_portfolio_access_url_expired',
                    'message': f'Business portfolio access URLs "{business_portfolio["name"]}" expired',
                    'severity': 'warning',
                    'source': 'src.facebook_pacs.services',
                    'payload': {
                        'businessPortfolioId': business_portfolio['id'],
                        'businessPortfolioName': business_portfolio['name'],
                    },
                }
            ]
        }

    def test_get_alerts__business_portfolio_with_one_expiring_soon_access_url(
        self, client, authorization, business_portfolio, timestamp, write_to_db
    ):
        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-1',
                'email': 'owner@example.com',
                'expires_at': timestamp - 1,
            },
        )

        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-2',
                'email': 'owner@example.com',
                'expires_at': timestamp - 1,
            },
        )

        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-3',
                'email': 'owner@example.com',
                'expires_at': timestamp + 24 * 60 * 60,
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'facebook_pacs_business_portfolio_access_url_expiring_soon',
                    'message': f'Business portfolio access URL "{business_portfolio["name"]}" expires soon',
                    'severity': 'info',
                    'source': 'src.facebook_pacs.services',
                    'payload': {
                        'businessPortfolioId': business_portfolio['id'],
                        'businessPortfolioName': business_portfolio['name'],
                    },
                }
            ]
        }

    def test_get_alerts__business_portfolio_with_one_in_date_access_url(
        self, client, authorization, business_portfolio, timestamp, write_to_db
    ):
        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-1',
                'email': 'owner@example.com',
                'expires_at': timestamp - 1,
            },
        )

        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-2',
                'email': 'owner@example.com',
                'expires_at': timestamp - 1,
            },
        )

        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-3',
                'email': 'owner@example.com',
                'expires_at': timestamp + 6 * 24 * 60 * 60,
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {'content': []}

    def test_get_alerts__business_portfolio_with_expiring_soon_and_in_date_access_urls(
        self, client, authorization, business_portfolio, timestamp, write_to_db
    ):
        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-1',
                'email': 'owner@example.com',
                'expires_at': timestamp - 1,
            },
        )

        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-2',
                'email': 'owner@example.com',
                'expires_at': timestamp - 1,
            },
        )

        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-3',
                'email': 'owner@example.com',
                'expires_at': timestamp + 24 * 60 * 60,
            },
        )

        write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost/expired-4',
                'email': 'owner@example.com',
                'expires_at': timestamp + 6 * 24 * 60 * 60,
            },
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {'content': []}

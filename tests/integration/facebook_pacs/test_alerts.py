from datetime import datetime, timezone


class TestAlerts:
    def test_get_alerts__expired_business_portfolio_access_url(
        self, client, authorization, business_portfolio, timestamp, write_to_db
    ):
        access_url = write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost',
                'email': 'owner@example.com',
                'expires_at': timestamp,
            },
        )
        expires_at_iso = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc).isoformat()

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'facebook_pacs_business_portfolio_access_url_expired',
                    'message': (
                        f'Business portfolio access URL expired for "{business_portfolio["name"]}" on {expires_at_iso}.'
                    ),
                    'severity': 'warning',
                    'source': 'src.facebook_pacs.services',
                    'payload': {
                        'accessUrlId': access_url['id'],
                        'businessPortfolioId': business_portfolio['id'],
                        'businessPortfolioName': business_portfolio['name'],
                        'url': access_url['url'],
                        'email': access_url['email'],
                        'expiresAt': timestamp,
                    },
                }
            ]
        }

    def test_get_alerts__business_portfolio_access_url_expires_soon(
        self, client, authorization, business_portfolio, timestamp, write_to_db
    ):
        access_url = write_to_db(
            'facebook_pacs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost',
                'email': 'owner@example.com',
                'expires_at': timestamp + 5 * 24 * 60 * 60,
            },
        )
        expires_at_iso = (
            datetime.utcfromtimestamp(timestamp + 5 * 24 * 60 * 60).replace(tzinfo=timezone.utc).isoformat()
        )

        response = client.get('/api/v2/alerts', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'code': 'facebook_pacs_business_portfolio_access_url_expiring_soon',
                    'message': (
                        f'Business portfolio access URL for "{business_portfolio["name"]}" '
                        f'expires on {expires_at_iso}.'
                    ),
                    'severity': 'info',
                    'source': 'src.facebook_pacs.services',
                    'payload': {
                        'accessUrlId': access_url['id'],
                        'businessPortfolioId': business_portfolio['id'],
                        'businessPortfolioName': business_portfolio['name'],
                        'url': access_url['url'],
                        'email': access_url['email'],
                        'expiresAt': timestamp + 5 * 24 * 60 * 60,
                        'daysUntilExpiration': 5,
                    },
                }
            ]
        }

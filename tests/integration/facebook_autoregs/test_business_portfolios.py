from datetime import date, datetime, time, timedelta
from unittest import mock

import pytest


class TestBusinessPortfolio:
    def test_get_business_portfolios(self, client, authorization, business_portfolio, read_from_db):
        response = client.get('/api/v2/facebook/autoregs/business-portfolios', headers={'Authorization': authorization})
        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'id': business_portfolio['id'],
                    'name': business_portfolio['name'],
                    'isBanned': False,
                    'executors': [],
                    'adCabinets': [],
                }
            ],
            'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 1},
        }

    def test_create_business_portfolio(self, client, authorization, business_portfolio_name, read_from_db):
        request_payload = {'name': business_portfolio_name, 'isBanned': False}

        response = client.post(
            '/api/v2/facebook/autoregs/business-portfolios',
            headers={'Authorization': authorization},
            json=request_payload,
        )
        assert response.status_code == 201, response.text
        assert response.json == {
            'id': mock.ANY,
            'isBanned': request_payload['isBanned'],
            'name': request_payload['name'],
            'adCabinets': [],
            'executors': [],
        }

        db_payload = read_from_db('facebook_autoregs_business_portfolio')
        assert db_payload == {
            'id': mock.ANY,
            'name': request_payload['name'],
            'is_banned': request_payload['isBanned'],
            'created_at': mock.ANY,
        }

    def test_get_business_portfolio(self, client, authorization, business_portfolio):
        response = client.get(
            f'/api/v2/facebook/autoregs/business-portfolios/{business_portfolio["id"]}',
            headers={'Authorization': authorization},
        )
        assert response.status_code == 200, response.text
        assert response.json == {
            'id': business_portfolio['id'],
            'name': business_portfolio['name'],
            'isBanned': business_portfolio['is_banned'],
            'adCabinets': [],
            'executors': [],
        }

    def test_get_business_portfolio__non_existent(self, client, authorization):
        response = client.get(
            '/api/v2/facebook/autoregs/business-portfolios/100500',
            headers={'Authorization': authorization},
        )
        assert response.status_code == 404, response.text
        assert response.json == {'message': 'Does not exist'}

    def test_update_business_portfolio(self, client, authorization, business_portfolio, read_from_db):
        request_payload = {'name': 'Umar ibn al-Khattab', 'isBanned': True}
        assert business_portfolio['name'] != request_payload['name']
        assert business_portfolio['is_banned'] != request_payload['isBanned']

        response = client.patch(
            f'/api/v2/facebook/autoregs/business-portfolios/{business_portfolio["id"]}',
            headers={'Authorization': authorization},
            json=request_payload,
        )
        assert response.status_code == 200, response.text
        assert response.json == {
            'id': business_portfolio['id'],
            'isBanned': request_payload['isBanned'],
            'name': request_payload['name'],
            'adCabinets': mock.ANY,
            'executors': mock.ANY,
        }

        db_payload = read_from_db('facebook_autoregs_business_portfolio', filters={'id': business_portfolio['id']})
        assert db_payload == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'name': request_payload['name'],
            'is_banned': int(request_payload['isBanned']),
        }

    def test_bind_business_portfolio_with_executor(
        self, client, authorization, business_portfolio, executor, write_to_db, read_from_db
    ):
        response = client.post(
            f'/api/v2/facebook/autoregs/business-portfolios/{business_portfolio["id"]}/executors/{executor["id"]}',
            headers={'Authorization': authorization},
        )
        assert response.status_code == 201
        assert response.json == {
            'id': business_portfolio['id'],
            'name': business_portfolio['name'],
            'isBanned': business_portfolio['is_banned'],
            'adCabinets': mock.ANY,
            'executors': [
                {'id': executor['id'], 'name': executor['name'], 'isBanned': executor['is_banned']}
            ],  # business manager has executor
        }

        db_payload = read_from_db(
            'facebook_autoregs_business_portfolio2executor',
            filters={'businessportfolio_id': business_portfolio['id'], 'executor_id': executor['id']},
        )
        assert db_payload

    def test_unbind_business_portfolio_with_executor(
        self, client, authorization, business_portfolio, executor, write_to_db, read_from_db
    ):
        write_to_db(
            'facebook_autoregs_business_portfolio2executor',
            {'businessportfolio_id': business_portfolio['id'], 'executor_id': executor['id']},
        )

        response = client.delete(
            f'/api/v2/facebook/autoregs/business-portfolios/{business_portfolio["id"]}/executors/{executor["id"]}',
            headers={'Authorization': authorization},
        )
        assert response.status_code == 204

        db_payload = read_from_db(
            'facebook_autoregs_business_portfolio2executor',
            filters={'businessportfolio_id': business_portfolio['id'], 'executor_id': executor['id']},
        )
        assert db_payload is None

    def test_unbind_business_portfolio_with_executor__non_existent_executor(
        self, client, authorization, business_portfolio, write_to_db, read_from_db
    ):
        non_existent_executor = 100500

        response = client.delete(
            '/api/v2/facebook/autoregs/business-portfolios'
            f'/{business_portfolio["id"]}/executors/{non_existent_executor}',
            headers={'Authorization': authorization},
        )
        assert response.status_code == 404
        assert response.json == {'message': 'Does not exist'}


class TestBusinessPortfolioWithExecutorAndAdCabinet:
    @pytest.fixture
    def ad_cabinet(self, executor, business_portfolio, ad_cabinet_payload, write_to_db):
        ad_cabinet = write_to_db(
            'facebook_autoregs_ad_cabinet', ad_cabinet_payload | {'business_portfolio_id': business_portfolio['id']}
        )

        write_to_db(
            'facebook_autoregs_business_portfolio2executor',
            {'businessportfolio_id': business_portfolio['id'], 'executor_id': executor['id']},
        )

        return ad_cabinet

    def test_get_business_portfolio(self, client, authorization, business_portfolio, executor, ad_cabinet, write_to_db):
        response = client.get(
            f'/api/v2/facebook/autoregs/business-portfolios/{business_portfolio["id"]}',
            headers={'Authorization': authorization},
        )
        assert response.status_code == 200, response.text
        assert response.json == {
            'id': business_portfolio['id'],
            'name': business_portfolio['name'],
            'isBanned': business_portfolio['is_banned'],
            'executors': [{'id': executor['id'], 'name': executor['name'], 'isBanned': executor['is_banned']}],
            'adCabinets': [
                {
                    'id': ad_cabinet['id'],
                    'name': ad_cabinet['name'],
                    'isBanned': ad_cabinet['is_banned'],
                    'businessPortfolio': {
                        'id': business_portfolio['id'],
                        'isBanned': business_portfolio['is_banned'],
                        'name': business_portfolio['name'],
                    },
                }
            ],
        }


class TestBusinessPortfolioManageAccessUrls:
    @pytest.fixture
    def access_url(self, business_portfolio, timestamp, write_to_db):
        return write_to_db(
            'facebook_autoregs_business_portfolio_access_url',
            {
                'business_portfolio_id': business_portfolio['id'],
                'url': 'http://localhost',
                'expires_at': timestamp + 30 * 24 * 60 * 60,
            },
        )

    def test_get_access_urls(self, client, authorization, access_url):
        response = client.get(
            f'/api/v2/facebook/autoregs/business-portfolios/{access_url["business_portfolio_id"]}/access-urls',
            headers={'Authorization': authorization},
        )
        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'id': access_url['id'],
                    'url': access_url['url'],
                    'expiresAt': date.fromtimestamp(access_url['expires_at']).isoformat(),
                }
            ],
            'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 1},
        }

    def test_create_access_url(self, client, authorization, business_portfolio, read_from_db):
        expires_at = (datetime.now() + timedelta(days=30)).date()

        request_payload = {
            'url': 'http://localhost',
            'expiresAt': expires_at.isoformat(),
        }
        response = client.post(
            f'/api/v2/facebook/autoregs/business-portfolios/{business_portfolio["id"]}/access-urls',
            headers={'Authorization': authorization},
            json=request_payload,
        )
        assert response.status_code == 201, response.text
        assert response.json == {
            'id': mock.ANY,
            'url': request_payload['url'],
            'expiresAt': request_payload['expiresAt'],
        }

        db_payload = read_from_db('facebook_autoregs_business_portfolio_access_url')
        assert db_payload == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'business_portfolio_id': business_portfolio['id'],
            'url': request_payload['url'],
            'expires_at': datetime.combine(expires_at, time.min).timestamp(),
        }

    def test_delete_access_url(self, client, authorization, access_url, read_from_db):
        response = client.delete(
            (
                '/api/v2/facebook/autoregs/business-portfolios'
                f'/{access_url["business_portfolio_id"]}/access-urls/{access_url["id"]}'
            ),
            headers={'Authorization': authorization},
        )
        assert response.status_code == 204, response.text

        db_payload = read_from_db('facebook_autoregs_business_portfolio_access_url')
        assert db_payload is None

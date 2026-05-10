import hashlib
from unittest import mock

import pytest


def _cookie_name(hostname, length=6):
    return hashlib.sha256(hostname.encode()).hexdigest()[:length]


class TestDomains:
    def test_create_domain_normalizes_hostname_and_returns_cookie_name(self, client, authorization, read_from_db):
        request_payload = {
            'hostname': 'Example.COM.',
            'purpose': 'campaign',
            'isDisabled': False,
        }

        response = client.post('/api/v2/domains', headers={'Authorization': authorization}, json=request_payload)

        assert response.status_code == 201, response.text
        assert response.json == {
            'id': mock.ANY,
            'hostname': 'example.com',
            'purpose': 'campaign',
            'campaignId': None,
            'isARecordSet': None,
            'isDisabled': False,
            'cookieName': _cookie_name('example.com'),
        }

        domain = read_from_db('domain')
        assert domain == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'hostname': 'example.com',
            'purpose': 'campaign',
            'campaign_id': None,
            'is_a_record_set': None,
            'is_disabled': False,
        }

    def test_list_domains_returns_campaign_and_dashboard_domains(self, client, authorization, campaign, write_to_db):
        for index in range(19):
            write_to_db(
                'domain',
                {
                    'hostname': f'padding-{index}.example.com',
                    'purpose': 'campaign',
                    'campaign_id': None,
                    'is_a_record_set': None,
                    'is_disabled': False,
                },
            )
        campaign_domain = write_to_db(
            'domain',
            {
                'hostname': 'example.com',
                'purpose': 'campaign',
                'campaign_id': campaign['id'],
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        dashboard_domain = write_to_db(
            'domain',
            {
                'hostname': 'dashboard.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': True,
            },
        )

        response = client.get('/api/v2/domains', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'id': mock.ANY,
                    'hostname': 'padding-0.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-0.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-1.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-1.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-2.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-2.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-3.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-3.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-4.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-4.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-5.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-5.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-6.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-6.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-7.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-7.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-8.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-8.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-9.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-9.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-10.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-10.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-11.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-11.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-12.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-12.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-13.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-13.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-14.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-14.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-15.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-15.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-16.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-16.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-17.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-17.example.com'),
                },
                {
                    'id': mock.ANY,
                    'hostname': 'padding-18.example.com',
                    'purpose': 'campaign',
                    'campaignId': None,
                    'isARecordSet': None,
                    'isDisabled': False,
                    'cookieName': _cookie_name('padding-18.example.com'),
                },
                {
                    'id': campaign_domain['id'],
                    'hostname': campaign_domain['hostname'],
                    'purpose': campaign_domain['purpose'],
                    'campaignId': campaign_domain['campaign_id'],
                    'isARecordSet': campaign_domain['is_a_record_set'],
                    'isDisabled': campaign_domain['is_disabled'],
                    'cookieName': _cookie_name(campaign_domain['hostname']),
                },
                {
                    'id': dashboard_domain['id'],
                    'hostname': dashboard_domain['hostname'],
                    'purpose': dashboard_domain['purpose'],
                    'campaignId': dashboard_domain['campaign_id'],
                    'isARecordSet': dashboard_domain['is_a_record_set'],
                    'isDisabled': dashboard_domain['is_disabled'],
                    'cookieName': None,
                },
            ],
            'pagination': {'page': 1, 'pageSize': 20, 'sortBy': 'id', 'sortOrder': 'asc', 'total': 21},
        }

    def test_list_domains_supports_sorting(self, client, authorization, write_to_db):
        first = write_to_db(
            'domain',
            {
                'hostname': 'bravo.example.com',
                'purpose': 'campaign',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': False,
            },
        )
        second = write_to_db(
            'domain',
            {
                'hostname': 'alpha.example.com',
                'purpose': 'campaign',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': False,
            },
        )
        third = write_to_db(
            'domain',
            {
                'hostname': 'charlie.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': False,
            },
        )

        response = client.get(
            '/api/v2/domains',
            headers={'Authorization': authorization},
            query_string={'pageSize': 3, 'sortBy': 'hostname', 'sortOrder': 'desc'},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'content': [
                {
                    'id': third['id'],
                    'hostname': third['hostname'],
                    'purpose': third['purpose'],
                    'campaignId': third['campaign_id'],
                    'isARecordSet': third['is_a_record_set'],
                    'isDisabled': third['is_disabled'],
                    'cookieName': None,
                },
                {
                    'id': first['id'],
                    'hostname': first['hostname'],
                    'purpose': first['purpose'],
                    'campaignId': first['campaign_id'],
                    'isARecordSet': first['is_a_record_set'],
                    'isDisabled': first['is_disabled'],
                    'cookieName': _cookie_name(first['hostname']),
                },
                {
                    'id': second['id'],
                    'hostname': second['hostname'],
                    'purpose': second['purpose'],
                    'campaignId': second['campaign_id'],
                    'isARecordSet': second['is_a_record_set'],
                    'isDisabled': second['is_disabled'],
                    'cookieName': _cookie_name(second['hostname']),
                },
            ],
            'pagination': {'page': 1, 'pageSize': 3, 'sortBy': 'hostname', 'sortOrder': 'desc', 'total': 3},
        }

    def test_get_domain_returns_full_payload(self, client, authorization, domain):
        response = client.get(f'/api/v2/domains/{domain["id"]}', headers={'Authorization': authorization})

        assert response.status_code == 200, response.text
        assert response.json == {
            'id': domain['id'],
            'hostname': domain['hostname'],
            'purpose': domain['purpose'],
            'campaignId': domain['campaign_id'],
            'isARecordSet': domain['is_a_record_set'],
            'isDisabled': domain['is_disabled'],
            'cookieName': _cookie_name(domain['hostname']),
        }

    def test_get_domain__non_existent(self, client, authorization):
        response = client.get('/api/v2/domains/100500', headers={'Authorization': authorization})

        assert response.status_code == 404, response.text
        assert response.json == {'message': 'Domain does not exist'}

    def test_update_domain_resets_dns_when_hostname_changes(self, client, authorization, write_to_db, read_from_db):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'old.example.com',
                'purpose': 'campaign',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )

        response = client.patch(
            f'/api/v2/domains/{domain["id"]}',
            headers={'Authorization': authorization},
            json={
                'hostname': 'New.Example.com.',
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'id': domain['id'],
            'hostname': 'new.example.com',
            'purpose': 'campaign',
            'campaignId': None,
            'isARecordSet': None,
            'isDisabled': False,
            'cookieName': _cookie_name('new.example.com'),
        }

        updated = read_from_db('domain', filters={'id': domain['id']})
        assert updated == {
            'id': domain['id'],
            'created_at': mock.ANY,
            'hostname': 'new.example.com',
            'purpose': 'campaign',
            'campaign_id': None,
            'is_a_record_set': None,
            'is_disabled': False,
        }

    def test_update_domain_attaches_campaign(self, client, authorization, campaign, write_to_db, read_from_db):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'old.example.com',
                'purpose': 'campaign',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )

        response = client.patch(
            f'/api/v2/domains/{domain["id"]}',
            headers={'Authorization': authorization},
            json={
                'campaignId': campaign['id'],
            },
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'id': domain['id'],
            'hostname': domain['hostname'],
            'purpose': 'campaign',
            'campaignId': campaign['id'],
            'isARecordSet': True,
            'isDisabled': False,
            'cookieName': _cookie_name(domain['hostname']),
        }

        updated = read_from_db('domain', filters={'id': domain['id']})
        assert updated == {
            'id': domain['id'],
            'created_at': mock.ANY,
            'hostname': domain['hostname'],
            'purpose': 'campaign',
            'campaign_id': campaign['id'],
            'is_a_record_set': True,
            'is_disabled': False,
        }

    def test_update_domain_rejects_dashboard_domain_campaign_binding(
        self, client, authorization, campaign, write_to_db
    ):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'dashboard.example.com',
                'purpose': 'dashboard',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': True,
            },
        )

        update_response = client.patch(
            f'/api/v2/domains/{domain["id"]}',
            headers={'Authorization': authorization},
            json={'campaignId': campaign['id']},
        )

        assert update_response.status_code == 400, update_response.text
        assert update_response.json == {'message': 'Dashboard domains cannot be attached to campaigns'}

    def test_update_domain_rejects_duplicate_campaign_binding(self, client, authorization, campaign, write_to_db):
        first_domain = write_to_db(
            'domain',
            {
                'hostname': 'first.example.com',
                'purpose': 'campaign',
                'campaign_id': campaign['id'],
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )
        second_domain = write_to_db(
            'domain',
            {
                'hostname': 'second.example.com',
                'purpose': 'campaign',
                'campaign_id': None,
                'is_a_record_set': False,
                'is_disabled': False,
            },
        )

        response = client.patch(
            f'/api/v2/domains/{second_domain["id"]}',
            headers={'Authorization': authorization},
            json={'campaignId': campaign['id']},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'message': 'Campaign is already attached to a domain'}

        assert first_domain['campaign_id'] == campaign['id']

    @pytest.mark.parametrize(
        'hostname',
        ['https://example.com', 'example..com', 'foo_bar.example.com', 'example'],
    )
    def test_create_domain_rejects_invalid_hostname(self, client, authorization, hostname):
        response = client.post(
            '/api/v2/domains',
            headers={'Authorization': authorization},
            json={'hostname': hostname, 'purpose': 'campaign'},
        )

        assert response.status_code == 422, response.text
        assert response.json == {
            'code': 422,
            'errors': {'json': {'hostname': ['hostname is invalid.']}},
            'status': 'Unprocessable Entity',
        }

    def test_create_domain_rejects_duplicate_normalized_hostname(self, client, authorization, write_to_db):
        write_to_db(
            'domain',
            {
                'hostname': 'example.com',
                'purpose': 'campaign',
                'campaign_id': None,
                'is_a_record_set': None,
                'is_disabled': False,
            },
        )

        response = client.post(
            '/api/v2/domains',
            headers={'Authorization': authorization},
            json={
                'hostname': 'Example.COM.',
                'purpose': 'campaign',
                'isDisabled': False,
            },
        )

        assert response.status_code == 409, response.text
        assert response.json == {'message': 'Domain already exists'}

    def test_update_domain_can_detach_campaign_and_switch_to_dashboard(
        self, client, authorization, campaign, write_to_db, read_from_db
    ):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'campaign.example.com',
                'purpose': 'campaign',
                'campaign_id': campaign['id'],
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )

        response = client.patch(
            f'/api/v2/domains/{domain["id"]}',
            headers={'Authorization': authorization},
            json={'purpose': 'dashboard', 'campaignId': None},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'id': domain['id'],
            'hostname': domain['hostname'],
            'purpose': 'dashboard',
            'campaignId': None,
            'isARecordSet': True,
            'isDisabled': False,
            'cookieName': None,
        }

        updated = read_from_db('domain', filters={'id': domain['id']})
        assert updated == {
            'id': domain['id'],
            'created_at': mock.ANY,
            'hostname': domain['hostname'],
            'purpose': 'dashboard',
            'campaign_id': None,
            'is_a_record_set': True,
            'is_disabled': False,
        }

    def test_update_domain_rejects_switching_attached_campaign_domain_to_dashboard(
        self, client, authorization, campaign, write_to_db
    ):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'campaign.example.com',
                'purpose': 'campaign',
                'campaign_id': campaign['id'],
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )

        response = client.patch(
            f'/api/v2/domains/{domain["id"]}',
            headers={'Authorization': authorization},
            json={'purpose': 'dashboard', 'campaignId': campaign['id']},
        )

        assert response.status_code == 400, response.text
        assert response.json == {'message': 'Dashboard domains cannot be attached to campaigns'}

    def test_update_domain_switches_purpose_to_dashboard(self, client, authorization, write_to_db, read_from_db):
        domain = write_to_db(
            'domain',
            {
                'hostname': 'dashboard.example.com',
                'purpose': 'campaign',
                'campaign_id': None,
                'is_a_record_set': True,
                'is_disabled': False,
            },
        )

        response = client.patch(
            f'/api/v2/domains/{domain["id"]}',
            headers={'Authorization': authorization},
            json={'purpose': 'dashboard', 'campaignId': None},
        )

        assert response.status_code == 200, response.text
        assert response.json == {
            'id': domain['id'],
            'hostname': domain['hostname'],
            'purpose': 'dashboard',
            'campaignId': None,
            'isARecordSet': True,
            'isDisabled': False,
            'cookieName': None,
        }

        updated = read_from_db('domain', filters={'id': domain['id']})
        assert updated == {
            'id': domain['id'],
            'created_at': mock.ANY,
            'hostname': domain['hostname'],
            'purpose': 'dashboard',
            'campaign_id': None,
            'is_a_record_set': True,
            'is_disabled': False,
        }

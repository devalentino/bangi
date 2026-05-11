from unittest import mock

import pytest


class TestDomains:
    def test_create_domain_normalizes_hostname_and_returns_full_payload(self, client, authorization, read_from_db):
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
            'campaignName': None,
            'validationFailed': False,
            'isARecordSet': None,
            'isDisabled': False,
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
        assert len(response.json['content']) == 20
        assert response.json['content'][0] == {
            'id': mock.ANY,
            'hostname': 'padding-0.example.com',
            'purpose': 'campaign',
            'campaignId': None,
            'campaignName': None,
            'validationFailed': False,
            'isARecordSet': None,
            'isDisabled': False,
        }
        assert response.json['content'][-1] == {
            'id': mock.ANY,
            'hostname': campaign_domain['hostname'],
            'purpose': campaign_domain['purpose'],
            'campaignId': campaign_domain['campaign_id'],
            'campaignName': campaign['name'],
            'validationFailed': False,
            'isARecordSet': campaign_domain['is_a_record_set'],
            'isDisabled': campaign_domain['is_disabled'],
        }
        assert dashboard_domain['hostname'] not in {item['hostname'] for item in response.json['content']}
        assert response.json['pagination'] == {
            'page': 1,
            'pageSize': 20,
            'sortBy': 'id',
            'sortOrder': 'asc',
            'total': 21,
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
                    'campaignName': None,
                    'validationFailed': False,
                    'isARecordSet': third['is_a_record_set'],
                    'isDisabled': third['is_disabled'],
                },
                {
                    'id': first['id'],
                    'hostname': first['hostname'],
                    'purpose': first['purpose'],
                    'campaignId': first['campaign_id'],
                    'campaignName': None,
                    'validationFailed': False,
                    'isARecordSet': first['is_a_record_set'],
                    'isDisabled': first['is_disabled'],
                },
                {
                    'id': second['id'],
                    'hostname': second['hostname'],
                    'purpose': second['purpose'],
                    'campaignId': second['campaign_id'],
                    'campaignName': None,
                    'validationFailed': False,
                    'isARecordSet': second['is_a_record_set'],
                    'isDisabled': second['is_disabled'],
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
            'campaignName': None,
            'validationFailed': False,
            'isARecordSet': domain['is_a_record_set'],
            'isDisabled': domain['is_disabled'],
        }

    def test_get_domain__non_existent(self, client, authorization):
        response = client.get('/api/v2/domains/100500', headers={'Authorization': authorization})

        assert response.status_code == 404, response.text
        assert response.json == {'message': 'Domain does not exist'}

    def test_update_domain_resets_dns_when_hostname_changes(
        self, client, authorization, write_to_db, read_from_db, nginx_workspace_base_dir
    ):
        from pathlib import Path

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
            'campaignName': None,
            'validationFailed': False,
            'isARecordSet': None,
            'isDisabled': False,
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

        old_enabled_link = Path(nginx_workspace_base_dir) / 'sites-enabled' / 'old.example.com.conf'
        new_enabled_link = Path(nginx_workspace_base_dir) / 'sites-enabled' / 'new.example.com.conf'

        assert old_enabled_link.exists() is False
        assert new_enabled_link.is_symlink()

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
            'campaignName': campaign['name'],
            'validationFailed': False,
            'isARecordSet': True,
            'isDisabled': False,
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
        'hostname, expected_message',
        [
            ('https://example.com', 'hostname is invalid.'),
            ('example..com', 'hostname is invalid.'),
            ('foo_bar.example.com', 'hostname is invalid.'),
            ('example', 'hostname must contain a valid domain and top-level domain.'),
        ],
    )
    def test_create_domain_rejects_invalid_hostname(self, client, authorization, hostname, expected_message):
        response = client.post(
            '/api/v2/domains',
            headers={'Authorization': authorization},
            json={'hostname': hostname, 'purpose': 'campaign'},
        )

        assert response.status_code == 422, response.text
        assert response.json == {
            'code': 422,
            'errors': {'json': {'hostname': [expected_message]}},
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
            'campaignName': None,
            'validationFailed': False,
            'isARecordSet': True,
            'isDisabled': False,
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
            'campaignName': None,
            'validationFailed': False,
            'isARecordSet': True,
            'isDisabled': False,
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

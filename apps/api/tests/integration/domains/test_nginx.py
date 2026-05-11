import json
import os
import shutil
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def nginx_workspace_base_dir_cleanup(nginx_workspace_base_dir):
    yield
    shutil.rmtree(nginx_workspace_base_dir)
    os.makedirs(nginx_workspace_base_dir)


class TestDomainNginxPublication:
    def test_create_domain_publishes_versioned_config(
        self, client, authorization, nginx_workspace_base_dir, mock_subprocess_run
    ):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = ''

        request_payload = {
            'hostname': 'Example.COM.',
            'purpose': 'campaign',
            'isDisabled': False,
        }

        response = client.post('/api/v2/domains', headers={'Authorization': authorization}, json=request_payload)

        assert response.status_code == 201, response.text
        available_dir = Path(nginx_workspace_base_dir) / 'sites-available' / 'example.com'
        enabled_link = Path(nginx_workspace_base_dir) / 'sites-enabled' / 'example.com.conf'
        versioned_configs = sorted(available_dir.glob('*.conf'))

        assert len(versioned_configs) == 1
        assert versioned_configs[0].read_text(encoding='utf-8') == (
            '# Managed by Bangi. Disabled or unroutable domain.\n'
            'server {\n'
            '    listen 80;\n'
            '    listen [::]:80;\n'
            '    server_name example.com;\n'
            '    return 503;\n'
            '}\n'
        )
        assert enabled_link.is_symlink()
        assert enabled_link.readlink().as_posix() == f'../sites-available/example.com/{versioned_configs[0].name}'

    def test_create_domain_records_success_snapshot(
        self, client, authorization, nginx_workspace_base_dir, read_from_db, mock_subprocess_run
    ):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = ''

        request_payload = {
            'hostname': 'Example.COM.',
            'purpose': 'campaign',
            'isDisabled': False,
        }

        response = client.post('/api/v2/domains', headers={'Authorization': authorization}, json=request_payload)

        assert response.status_code == 201, response.text
        domain_id = read_from_db('domain', filters={'hostname': 'example.com'})['id']
        available_dir = Path(nginx_workspace_base_dir) / 'sites-available' / 'example.com'
        versioned_configs = sorted(available_dir.glob('*.conf'))
        snapshot = read_from_db('health_nginx_validation_snapshot')

        assert snapshot == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'domain_id': domain_id,
            'validation_status': 'success',
            'validation_error': None,
            'sites_available_files': json.dumps([f'sites-available/example.com/{versioned_configs[0].name}']),
            'sites_enabled_refs': json.dumps(
                [f'sites-enabled/example.com.conf -> ../sites-available/example.com/{versioned_configs[0].name}']
            ),
        }

    def test_failed_publish_keeps_previous_active_version(
        self, client, authorization, campaign, nginx_workspace_base_dir, write_to_db, mock_subprocess_run
    ):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = ''

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

        available_dir = Path(nginx_workspace_base_dir) / 'sites-available' / 'campaign.example.com'
        enabled_link = Path(nginx_workspace_base_dir) / 'sites-enabled' / 'campaign.example.com.conf'
        available_dir.mkdir(parents=True, exist_ok=True)
        first_version = available_dir / '20260510T010101Z-abc12345.conf'
        second_version = available_dir / '20260510T010202Z-def67890.conf'
        first_version.write_text('# version 1\n', encoding='utf-8')
        second_version.write_text('# version 2\n', encoding='utf-8')
        enabled_link.parent.mkdir(parents=True, exist_ok=True)
        enabled_link.symlink_to(Path('..') / 'sites-available' / 'campaign.example.com' / second_version.name)
        second_target = enabled_link.readlink().as_posix()
        assert second_target == f'../sites-available/campaign.example.com/{second_version.name}'

        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = 'nginx: [emerg] invalid configuration'

        response = client.patch(
            f'/api/v2/domains/{domain["id"]}',
            headers={'Authorization': authorization},
            json={'purpose': 'dashboard', 'campaignId': None},
        )

        assert response.status_code == 200, response.text
        assert enabled_link.is_symlink()
        assert enabled_link.readlink().as_posix() == second_target  # link still refers second_version
        assert len(sorted(available_dir.glob('*.conf'))) == 3
        assert first_version.exists()
        assert second_version.exists()

    def test_failed_publish_records_failure_snapshot(
        self, client, authorization, campaign, nginx_workspace_base_dir, read_from_db, write_to_db, mock_subprocess_run
    ):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = ''

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

        available_dir = Path(nginx_workspace_base_dir) / 'sites-available' / 'campaign.example.com'
        enabled_link = Path(nginx_workspace_base_dir) / 'sites-enabled' / 'campaign.example.com.conf'
        available_dir.mkdir(parents=True, exist_ok=True)
        first_version = available_dir / '20260510T010101Z-abc12345.conf'
        second_version = available_dir / '20260510T010202Z-def67890.conf'
        first_version.write_text('# version 1\n', encoding='utf-8')
        second_version.write_text('# version 2\n', encoding='utf-8')
        enabled_link.parent.mkdir(parents=True, exist_ok=True)
        enabled_link.symlink_to(Path('..') / 'sites-available' / 'campaign.example.com' / second_version.name)
        second_target = enabled_link.readlink().as_posix()
        assert second_target == f'../sites-available/campaign.example.com/{second_version.name}'

        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = 'nginx: [emerg] invalid configuration'

        response = client.patch(
            f'/api/v2/domains/{domain["id"]}',
            headers={'Authorization': authorization},
            json={'purpose': 'dashboard', 'campaignId': None},
        )

        assert response.status_code == 200, response.text
        snapshot = read_from_db('health_nginx_validation_snapshot')
        available_files = [
            path.relative_to(Path(nginx_workspace_base_dir)).as_posix()
            for path in sorted((Path(nginx_workspace_base_dir) / 'sites-available').rglob('*.conf'))
        ]

        assert snapshot == {
            'id': mock.ANY,
            'created_at': mock.ANY,
            'domain_id': domain['id'],
            'validation_status': 'failed',
            'validation_error': 'nginx: [emerg] invalid configuration',
            'sites_available_files': json.dumps(available_files),
            'sites_enabled_refs': json.dumps([f'sites-enabled/campaign.example.com.conf -> {second_target}']),
        }
        assert first_version.exists()
        assert second_version.exists()

    def test_multiple_successful_publishes_keep_previous_versions_available(
        self, client, authorization, nginx_workspace_base_dir, mock_subprocess_run, read_from_db
    ):
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.stderr = ''

        request_payload = {
            'hostname': 'dashboard.example.com',
            'purpose': 'dashboard',
            'isDisabled': False,
        }

        response = client.post('/api/v2/domains', headers={'Authorization': authorization}, json=request_payload)

        assert response.status_code == 201, response.text
        domain = read_from_db('domain', filters={'hostname': 'dashboard.example.com'})

        response = client.patch(
            f'/api/v2/domains/{domain["id"]}',
            headers={'Authorization': authorization},
            json={'isDisabled': True},
        )

        assert response.status_code == 200, response.text

        available_dir = Path(nginx_workspace_base_dir) / 'sites-available' / 'dashboard.example.com'
        enabled_link = Path(nginx_workspace_base_dir) / 'sites-enabled' / 'dashboard.example.com.conf'
        versioned_configs = sorted(available_dir.glob('*.conf'))

        assert len(versioned_configs) == 2
        assert enabled_link.is_symlink()
        assert (
            enabled_link.readlink().as_posix()
            == f'../sites-available/dashboard.example.com/{versioned_configs[-1].name}'
        )
        assert versioned_configs[0].exists()
        assert versioned_configs[1].exists()

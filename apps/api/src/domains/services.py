import hashlib
import subprocess
import time
from pathlib import Path
from typing import Annotated, Protocol
from uuid import uuid4

from peewee import fn
from wireup import Inject, injectable

from src.core.entities import Campaign
from src.core.enums import SortOrder
from src.core.exceptions import CampaignDoesNotExistError
from src.domains.entities import Domain
from src.domains.enums import DomainPurpose
from src.domains.exceptions import (
    CampaignAlreadyBoundError,
    DashboardDomainCannotAttachCampaignError,
    DomainAlreadyExistsError,
    DomainDoesNotExistError,
)
from src.health.services import HealthService


class WebserverService(Protocol):
    def publish(self, hostname: str):
        pass

    def disable(self, hostname: str) -> None:
        pass


@injectable
class DomainService:
    def __init__(
        self,
        flow_id_cookie_key_length: Annotated[int, Inject(config='FLOW_ID_COOKIE_KEY_LENGTH')],
        webserver_service: WebserverService,
    ):
        self.flow_id_cookie_key_length = flow_id_cookie_key_length
        self.webserver_service = webserver_service

    def get(self, id):
        try:
            return Domain.get_by_id(id)
        except Domain.DoesNotExist as exc:
            raise DomainDoesNotExistError() from exc

    def list(self, page, page_size, sort_by, sort_order):
        order_by = getattr(Domain, sort_by)
        if sort_order == SortOrder.desc:
            order_by = order_by.desc()

        return [
            domain
            for domain in Domain.select()
            .order_by(order_by, Domain.id.asc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        ]

    def count(self):
        return Domain.select(fn.count(Domain.id)).scalar()

    def create(self, hostname, purpose, is_disabled=False):
        if Domain.select(fn.count(Domain.id)).where(Domain.hostname == hostname).scalar():
            raise DomainAlreadyExistsError()

        domain = Domain(
            hostname=hostname,
            purpose=purpose.value,
            is_disabled=is_disabled,
            is_a_record_set=None,
        )
        domain.save()
        self.webserver_service.publish(domain.hostname)
        return domain

    def update(
        self,
        domain_id,
        hostname=None,
        purpose=None,
        campaign_id=None,
        is_disabled=None,
    ):
        domain = self.get(domain_id)
        previous_hostname = domain.hostname

        if hostname is not None and hostname != domain.hostname:
            if (
                Domain.select(fn.count(Domain.id))
                .where((Domain.hostname == hostname) & (Domain.id != domain.id))
                .scalar()
            ):
                raise DomainAlreadyExistsError()
            domain.hostname = hostname
            domain.is_a_record_set = None

        if campaign_id is None:
            domain.campaign = None
        else:
            if domain.purpose == DomainPurpose.dashboard and purpose != DomainPurpose.campaign:
                raise DashboardDomainCannotAttachCampaignError()
            if domain.campaign_id != campaign_id:
                self._ensure_campaign_is_available(campaign_id, domain.id)

            if purpose == DomainPurpose.dashboard:
                raise DashboardDomainCannotAttachCampaignError()

            campaign = self._get_campaign(campaign_id)
            domain.campaign = campaign

        if purpose is not None:
            if purpose == DomainPurpose.dashboard and campaign_id is not None:
                raise DashboardDomainCannotAttachCampaignError()
            domain.purpose = purpose.value

        if is_disabled is not None:
            domain.is_disabled = is_disabled

        domain.save()
        snapshot = self.webserver_service.publish(domain.hostname)
        if previous_hostname != domain.hostname and snapshot.validation_status == 'success':
            self.webserver_service.disable(previous_hostname)
        return domain

    def cookie_name(self, hostname, purpose):
        if purpose != DomainPurpose.campaign:
            return None
        return hashlib.sha256(hostname.encode()).hexdigest()[: self.flow_id_cookie_key_length]

    def _get_campaign(self, campaign_id):
        try:
            return Campaign.get_by_id(campaign_id)
        except Campaign.DoesNotExist as exc:
            raise CampaignDoesNotExistError() from exc

    def _ensure_campaign_is_available(self, campaign_id, domain_id):
        query = Domain.select(fn.count(Domain.id)).where((Domain.campaign == campaign_id) & (Domain.id != domain_id))
        if query.scalar():
            raise CampaignAlreadyBoundError()


class HostCommandExecutionError(RuntimeError):
    pass


@injectable
class HostCommandExecutorService:
    def __init__(
        self,
        host_ops_ssh_user: Annotated[str, Inject(config='BANGI_HOST_OPS_SSH_USER')],
        host_ops_ssh_host: Annotated[str, Inject(config='BANGI_HOST_OPS_SSH_HOST')],
        host_ops_ssh_key_path: Annotated[str, Inject(config='BANGI_HOST_OPS_SSH_KEY_PATH')],
        host_ops_ssh_known_hosts_path: Annotated[str, Inject(config='BANGI_HOST_OPS_SSH_KNOWN_HOSTS_PATH')],
    ):
        self.host_ops_ssh_user = host_ops_ssh_user
        self.host_ops_ssh_host = host_ops_ssh_host
        self.host_ops_ssh_key_path = host_ops_ssh_key_path
        self.host_ops_ssh_known_hosts_path = host_ops_ssh_known_hosts_path

    def run(self, command: str) -> None:
        if not all(
            [
                self.host_ops_ssh_user,
                self.host_ops_ssh_host,
                self.host_ops_ssh_key_path,
                self.host_ops_ssh_known_hosts_path,
            ]
        ):
            raise HostCommandExecutionError('Host operations SSH configuration is missing')

        result = subprocess.run(
            [
                'ssh',
                '-i',
                self.host_ops_ssh_key_path,
                '-o',
                f'UserKnownHostsFile={self.host_ops_ssh_known_hosts_path}',
                '-o',
                'StrictHostKeyChecking=yes',
                f'{self.host_ops_ssh_user}@{self.host_ops_ssh_host}',
                command,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        output = ''.join(part for part in [result.stdout, result.stderr] if part).strip()
        if result.returncode != 0:
            raise HostCommandExecutionError(output or f'Host operation failed: {command}')


@injectable(as_type=WebserverService)
class NginxService:
    def __init__(
        self,
        health_service: HealthService,
        host_command_executor_service: HostCommandExecutorService,
        nginx_workspace_base_dir: Annotated[str, Inject(config='NGINX_WORKSPACE_BASE_DIR')],
    ):
        self.health_service = health_service
        self.host_command_executor_service = host_command_executor_service
        self.nginx_workspace_base_dir = Path(nginx_workspace_base_dir)

    def publish(self, hostname: str):
        domain = Domain.get(Domain.hostname == hostname)
        version = self._next_version()
        available_dir = self._site_available_dir(domain.hostname)
        enabled_link = self._site_enabled_link(domain.hostname)
        versioned_config_path = available_dir / f'{version}.conf'
        previous_active_target = self._current_active_target(enabled_link)

        self._write_versioned_config(versioned_config_path, self._render_domain_config(domain))
        validation_error = self._validate_host_nginx()
        if validation_error is not None:
            return self._record_snapshot(domain, 'failed', validation_error)

        self._activate_version(enabled_link, versioned_config_path)

        reload_error = self._reload_host_nginx()
        if reload_error is not None:
            self._restore_previous_active(enabled_link, previous_active_target)
            return self._record_snapshot(domain, 'failed', reload_error)

        return self._record_snapshot(domain, 'success', None)

    def _next_version(self) -> str:
        timestamp = int(time.time())
        return f'{timestamp}-{uuid4().hex[:8]}'

    def _site_available_dir(self, hostname: str) -> Path:
        return self.nginx_workspace_base_dir / 'sites-available' / hostname

    def _site_enabled_dir(self) -> Path:
        return self.nginx_workspace_base_dir / 'sites-enabled'

    def _site_enabled_link(self, hostname: str) -> Path:
        return self._site_enabled_dir() / f'{hostname}.conf'

    def _write_versioned_config(self, destination_path: Path, config_content: str) -> None:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = destination_path.with_suffix('.conf.tmp')
        temporary_path.write_text(config_content, encoding='utf-8')
        temporary_path.replace(destination_path)

    def _render_domain_config(self, domain: Domain) -> str:
        if (
            domain.is_disabled
            or domain.is_a_record_set is False
            or (domain.purpose == 'campaign' and domain.campaign_id is None)
        ):
            return self._render_disabled_domain_config(domain)

        if domain.purpose == 'dashboard':
            return self._render_dashboard_domain_config(domain)

        return self._render_campaign_domain_config(domain)

    @staticmethod
    def _render_disabled_domain_config(domain: Domain) -> str:
        return (
            '# Managed by Bangi. Disabled or unroutable domain.\n'
            'server {\n'
            '    listen 80;\n'
            '    listen [::]:80;\n'
            f'    server_name {domain.hostname};\n'
            '    return 503;\n'
            '}\n'
        )

    @staticmethod
    def _render_dashboard_domain_config(domain: Domain) -> str:
        return (
            '# Managed by Bangi. Dashboard domain.\n'
            'server {\n'
            '    listen 80;\n'
            '    listen [::]:80;\n'
            f'    server_name {domain.hostname};\n'
            '\n'
            '    location /api/ {\n'
            '        proxy_pass http://127.0.0.1:8000;\n'
            '    }\n'
            '\n'
            '    location / {\n'
            '        proxy_pass http://127.0.0.1:8080;\n'
            '    }\n'
            '}\n'
        )

    @staticmethod
    def _render_campaign_domain_config(domain: Domain) -> str:
        return (
            '# Managed by Bangi. Campaign domain.\n'
            'server {\n'
            '    listen 80;\n'
            '    listen [::]:80;\n'
            f'    server_name {domain.hostname};\n'
            '\n'
            '    location = / {\n'
            f'        proxy_pass http://127.0.0.1:8000/process/{domain.campaign_id};\n'
            '    }\n'
            '\n'
            '    location / {\n'
            '        return 404;\n'
            '    }\n'
            '}\n'
        )

    def _validate_host_nginx(self) -> str | None:
        try:
            self.host_command_executor_service.run('nginx-validate')
        except HostCommandExecutionError as exc:
            return str(exc)
        return None

    def _reload_host_nginx(self) -> str | None:
        try:
            self.host_command_executor_service.run('nginx-reload')
        except HostCommandExecutionError as exc:
            return str(exc)
        return None

    def _activate_version(self, enabled_link: Path, versioned_config_path: Path) -> None:
        enabled_link.parent.mkdir(parents=True, exist_ok=True)
        relative_target = (
            Path('..') / 'sites-available' / versioned_config_path.parent.name / versioned_config_path.name
        )
        temporary_link = enabled_link.with_name(f'{enabled_link.name}.tmp')

        if temporary_link.exists() or temporary_link.is_symlink():
            temporary_link.unlink()
        temporary_link.symlink_to(relative_target)
        temporary_link.replace(enabled_link)

    def _current_active_target(self, enabled_link: Path) -> Path | None:
        if not enabled_link.is_symlink():
            return None
        return Path(enabled_link.readlink())

    def _restore_previous_active(self, enabled_link: Path, previous_active_target: Path | None) -> None:
        if previous_active_target is None:
            if enabled_link.exists() or enabled_link.is_symlink():
                enabled_link.unlink()
            return

        temporary_link = enabled_link.with_name(f'{enabled_link.name}.tmp')
        if temporary_link.exists() or temporary_link.is_symlink():
            temporary_link.unlink()
        temporary_link.symlink_to(previous_active_target)
        temporary_link.replace(enabled_link)

    def disable(self, hostname: str) -> None:
        enabled_link = self._site_enabled_link(hostname)
        if enabled_link.exists() or enabled_link.is_symlink():
            enabled_link.unlink()

    def _record_snapshot(self, domain: Domain, validation_status: str, validation_error: str | None):
        return self.health_service.record_nginx_validation_snapshot(
            domain_id=domain.id,
            validation_status=validation_status,
            validation_error=validation_error,
            sites_available_files=self._list_sites_available_files(),
            sites_enabled_refs=self._list_sites_enabled_refs(),
        )

    def _list_sites_available_files(self) -> list[str]:
        available_root = self.nginx_workspace_base_dir / 'sites-available'
        if not available_root.exists():
            return []
        return sorted(
            path.relative_to(self.nginx_workspace_base_dir).as_posix()
            for path in available_root.rglob('*.conf')
            if path.is_file()
        )

    def _list_sites_enabled_refs(self) -> list[str]:
        enabled_root = self.nginx_workspace_base_dir / 'sites-enabled'
        if not enabled_root.exists():
            return []

        refs = []
        for enabled_link in sorted(enabled_root.glob('*.conf')):
            if not enabled_link.is_symlink():
                continue
            target = enabled_link.readlink()
            refs.append(f'{enabled_link.relative_to(self.nginx_workspace_base_dir).as_posix()} -> {target.as_posix()}')
        return refs

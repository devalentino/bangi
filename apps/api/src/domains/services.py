import logging
import secrets
import string
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Protocol
from uuid import uuid4

import dns.exception
import dns.resolver
from peewee import JOIN, IntegrityError, fn
from wireup import Inject, injectable

from src.core.entities import Campaign
from src.core.enums import SortOrder
from src.core.exceptions import CampaignDoesNotExistError
from src.domains.entities import Domain, DomainCookie
from src.domains.enums import DomainCookieName, DomainPurpose
from src.domains.exceptions import (
    CampaignAlreadyBoundError,
    DashboardDomainCannotAttachCampaignError,
    DomainAlreadyExistsError,
    DomainDoesNotExistError,
)
from src.health.services import HealthService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WebserverPublishResult:
    validation_status: str
    validation_error: str | None
    sites_available_files: list[str]
    sites_enabled_refs: list[str]


@injectable
class DomainCookieService:
    def get_or_create_opaque_name(self, domain_id: int, name: DomainCookieName) -> str:
        cookie_name = name.value
        cookie = DomainCookie.get_or_none((DomainCookie.domain == domain_id) & (DomainCookie.name == cookie_name))
        if cookie is not None:
            return cookie.opaque_name

        while True:
            opaque_name = self._generate_opaque_name()
            try:
                cookie = DomainCookie.create(domain=domain_id, name=cookie_name, opaque_name=opaque_name)
            except IntegrityError:
                # Another request may have created the logical cookie row already.
                # Re-read first; if it still does not exist, the random opaque name likely collided.
                cookie = DomainCookie.get_or_none(
                    (DomainCookie.domain == domain_id) & (DomainCookie.name == cookie_name)
                )
                if cookie is not None:
                    return cookie.opaque_name
                continue

            return cookie.opaque_name

    @staticmethod
    def _generate_opaque_name() -> str:
        alphabet = string.ascii_lowercase + string.digits
        length = secrets.randbelow(6) + 2
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class WebserverService(Protocol):
    def publish(
        self,
        hostname: str,
        purpose: str,
        campaign_id: int | None,
        flow_id_cookie_name: str | None,
        is_disabled: bool,
        is_a_record_set: bool | None,
    ) -> WebserverPublishResult:
        pass

    def disable(self, hostname: str) -> None:
        pass


class DnsService:
    @staticmethod
    def has_a_record(hostname: str, public_host_ip: str) -> bool:
        if not public_host_ip:
            return False

        try:
            answers = dns.resolver.resolve(hostname, 'A', lifetime=5)
        except dns.exception.DNSException:
            logger.error('Failed to resolve A record for managed domain', extra={'hostname': hostname})
            return False

        return any(answer.address == public_host_ip for answer in answers)


@injectable
class DomainService:
    def __init__(
        self,
        webserver_service: WebserverService,
        health_service: HealthService,
        domain_cookie_service: DomainCookieService,
    ):
        self.webserver_service = webserver_service
        self.health_service = health_service
        self.domain_cookie_service = domain_cookie_service

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
            for domain in Domain.select(Domain, Campaign)
            .join(Campaign, JOIN.LEFT_OUTER)
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
        self._publish_domain(domain)
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
        snapshot = self._publish_domain(domain)
        if previous_hostname != domain.hostname and snapshot.validation_status == 'success':
            self.webserver_service.disable(previous_hostname)
        return domain

    def get_by_campaign_id(self, campaign_id):
        domain = Domain.get_or_none(
            (Domain.campaign == campaign_id)
            & (Domain.purpose == DomainPurpose.campaign)
            & (Domain.is_disabled == False)
        )
        if domain is None:
            raise DomainDoesNotExistError()
        return domain

    def _get_campaign(self, campaign_id):
        try:
            return Campaign.get_by_id(campaign_id)
        except Campaign.DoesNotExist as exc:
            raise CampaignDoesNotExistError() from exc

    def _ensure_campaign_is_available(self, campaign_id, domain_id):
        query = Domain.select(fn.count(Domain.id)).where((Domain.campaign == campaign_id) & (Domain.id != domain_id))
        if query.scalar():
            raise CampaignAlreadyBoundError()

    def _publish_domain(self, domain) -> WebserverPublishResult:
        flow_id_cookie_name = None
        if domain.purpose == DomainPurpose.campaign and domain.campaign_id is not None:
            flow_id_cookie_name = self.domain_cookie_service.get_or_create_opaque_name(
                domain.id,
                DomainCookieName.flow_id,
            )

        snapshot = self.webserver_service.publish(
            domain.hostname,
            domain.purpose,
            domain.campaign_id,
            flow_id_cookie_name,
            bool(domain.is_disabled),
            None if domain.is_a_record_set is None else bool(domain.is_a_record_set),
        )
        self.health_service.record_nginx_validation_snapshot(
            domain_id=domain.id,
            validation_status=snapshot.validation_status,
            validation_error=snapshot.validation_error,
            sites_available_files=snapshot.sites_available_files,
            sites_enabled_refs=snapshot.sites_enabled_refs,
        )
        return snapshot


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
            logger.error('Host operations SSH configuration is missing', extra={'command': command})
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
            logger.error(
                'Failed to execute host command',
                extra={
                    'command': command,
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                },
            )
            raise HostCommandExecutionError(output or f'Host operation failed: {command}')


@injectable(as_type=WebserverService)
class NginxService:
    def __init__(
        self,
        host_command_executor_service: HostCommandExecutorService,
        nginx_workspace_base_dir: Annotated[str, Inject(config='NGINX_WORKSPACE_BASE_DIR')],
    ):
        self.host_command_executor_service = host_command_executor_service
        self.nginx_workspace_base_dir = Path(nginx_workspace_base_dir)

    def publish(
        self,
        hostname: str,
        purpose: str,
        campaign_id: int | None,
        flow_id_cookie_name: str | None,
        is_disabled: bool,
        is_a_record_set: bool | None,
    ) -> WebserverPublishResult:
        version = self._next_version()
        available_dir = self._site_available_dir(hostname)
        enabled_link = self._site_enabled_link(hostname)
        versioned_config_path = available_dir / f'{version}.conf'
        previous_active_target = self._current_active_target(enabled_link)

        config_content = self._render_domain_config(
            hostname=hostname,
            purpose=purpose,
            campaign_id=campaign_id,
            flow_id_cookie_name=flow_id_cookie_name,
            is_disabled=is_disabled,
            is_a_record_set=is_a_record_set,
        )
        self._write_versioned_config(versioned_config_path, config_content)
        validation_error = self._validate_host_nginx()
        if validation_error is not None:
            return WebserverPublishResult(
                validation_status='failed',
                validation_error=validation_error,
                sites_available_files=self._list_sites_available_files(),
                sites_enabled_refs=self._list_sites_enabled_refs(),
            )

        self._activate_version(enabled_link, versioned_config_path)

        reload_error = self._reload_host_nginx()
        if reload_error is not None:
            self._restore_previous_active(enabled_link, previous_active_target)
            return WebserverPublishResult(
                validation_status='failed',
                validation_error=reload_error,
                sites_available_files=self._list_sites_available_files(),
                sites_enabled_refs=self._list_sites_enabled_refs(),
            )

        return WebserverPublishResult(
            validation_status='success',
            validation_error=None,
            sites_available_files=self._list_sites_available_files(),
            sites_enabled_refs=self._list_sites_enabled_refs(),
        )

    def _next_version(self) -> str:
        timestamp = time.time_ns()
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

    def _render_domain_config(
        self,
        *,
        hostname: str,
        purpose: str,
        campaign_id: int | None,
        flow_id_cookie_name: str | None,
        is_disabled: bool,
        is_a_record_set: bool | None,
    ) -> str:
        if is_disabled or is_a_record_set is False or (purpose == 'campaign' and campaign_id is None):
            return self.render_disabled_domain_config(hostname)

        if purpose == 'dashboard':
            return self.render_dashboard_domain_config(hostname)

        if flow_id_cookie_name is None:
            raise ValueError('flow_id_cookie_name is required for campaign domains')
        return self.render_campaign_domain_config(hostname, campaign_id, flow_id_cookie_name)

    @staticmethod
    def render_disabled_domain_config(hostname: str) -> str:
        return (
            '# Managed by Bangi. Disabled or unroutable domain.\n'
            'server {\n'
            '    listen 80;\n'
            '    listen [::]:80;\n'
            f'    server_name {hostname};\n'
            '    return 503;\n'
            '}\n'
        )

    @staticmethod
    def render_dashboard_domain_config(hostname: str) -> str:
        return (
            '# Managed by Bangi. Dashboard domain.\n'
            'server {\n'
            '    listen 80;\n'
            '    listen [::]:80;\n'
            f'    server_name {hostname};\n'
            '\n'
            '    location /api/ {\n'
            '        proxy_pass http://127.0.0.1:8000;\n'
            '    }\n'
            '\n'
            '    location /process {\n'
            '        return 404;\n'
            '    }\n'
            '\n'
            '    location / {\n'
            '        proxy_pass http://127.0.0.1:8080;\n'
            '    }\n'
            '}\n'
        )

    @staticmethod
    def render_campaign_domain_config(hostname: str, campaign_id: int, flow_id_cookie_name: str) -> str:
        return (
            '# Managed by Bangi. Campaign domain.\n'
            'server {\n'
            '    listen 80;\n'
            '    listen [::]:80;\n'
            f'    server_name {hostname};\n'
            '\n'
            f'    set $bangi_campaign_upstream "http://127.0.0.1:8000/process/{campaign_id}";\n'
            f'    if ($cookie_{flow_id_cookie_name} != "") {{\n'
            f'        set $bangi_campaign_upstream "http://127.0.0.1:8081/$cookie_{flow_id_cookie_name}/";\n'
            '    }\n'
            '\n'
            '    location = / {\n'
            '        proxy_pass $bangi_campaign_upstream;\n'
            '    }\n'
            '\n'
            '    location / {\n'
            f'        if ($cookie_{flow_id_cookie_name} = "") {{\n'
            '            return 404;\n'
            '        }\n'
            '\n'
            f'        proxy_pass http://127.0.0.1:8081/$cookie_{flow_id_cookie_name}/;\n'
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
